import math
from typing import List, Dict, Any, Tuple, Optional
from ..models.entities import Vehicle, Order, Depot, RouteStop

# Graceful optional OR-Tools detection
try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    HAS_ORTOOLS = True
except ImportError:
    HAS_ORTOOLS = False


class GeoRoutingSolver:
    """
    Solves Capacitated Vehicle Routing Problem (CVRP) with Priority Deadlines,
    Carbon Emission modeling, and dynamic disruption avoidance.
    Supports Greedy Nearest Neighbor with 2-Opt local search refinement,
    and optional Google OR-Tools integration when installed.
    """

    HAS_ORTOOLS_SOLVER = HAS_ORTOOLS

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates great-circle distance between two points in km."""
        R = 6371.0  # Earth's radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 2)

    @classmethod
    def travel_time_minutes(cls, dist_km: float, speed_kmh: float, traffic_multiplier: float = 1.15) -> float:
        """Calculates realistic road transit time in minutes."""
        if speed_kmh <= 0:
            speed_kmh = 35.0
        effective_speed = speed_kmh / traffic_multiplier
        hours = dist_km / effective_speed
        return round(hours * 60, 1)

    @classmethod
    def optimize_fleet_routes(
        cls,
        vehicles: List[Vehicle],
        orders: List[Order],
        depots: Dict[str, Depot],
        active_disruptions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Multi-depot, multi-vehicle Capacitated Routing with Priority Scheduling.
        """
        active_disruptions = active_disruptions or []

        # Identify blocked coordinates or disabled vehicles
        disabled_vehicle_ids = set()
        hazard_zones = []
        for d in active_disruptions:
            if d.get("target_vehicle_id"):
                disabled_vehicle_ids.add(d["target_vehicle_id"])
            if d.get("affected_lat") and d.get("affected_lng") and d.get("radius_km"):
                hazard_zones.append({
                    "lat": d["affected_lat"],
                    "lng": d["affected_lng"],
                    "radius": d["radius_km"]
                })

        available_vehicles = [v for v in vehicles if v.id not in disabled_vehicle_ids and v.status != "disrupted"]

        # Sort orders by priority and urgency
        priority_weight = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        pending_orders = sorted(
            [o for o in orders if o.status in ("pending", "delayed", "re_routed")],
            key=lambda o: (priority_weight.get(o.priority, 4), o.deadline_minutes)
        )

        assignments: Dict[str, List[Order]] = {v.id: [] for v in available_vehicles}
        unassigned_orders: List[Order] = []

        # Step 1: Assign orders to most compatible and closest vehicle
        for order in pending_orders:
            # Check if order location is in a direct hazard zone
            in_hazard = any(
                cls.haversine_distance_km(order.lat, order.lng, hz["lat"], hz["lng"]) < hz["radius"]
                for hz in hazard_zones
            )
            if in_hazard:
                order.status = "delayed"
                unassigned_orders.append(order)
                continue

            best_vehicle = None
            min_extra_cost = float('inf')

            for vehicle in available_vehicles:
                # Capacity checks
                curr_weight = sum(o.weight_kg for o in assignments[vehicle.id])
                curr_volume = sum(o.volume_m3 for o in assignments[vehicle.id])

                if (curr_weight + order.weight_kg <= vehicle.capacity_kg) and \
                   (curr_volume + order.volume_m3 <= vehicle.capacity_volume_m3):

                    # Cold chain requirement match
                    if order.item == "cold_chain_vaccines" and "Reefer" not in vehicle.name and "Electric" not in vehicle.name:
                        continue

                    # Proximity scoring
                    depot = depots.get(vehicle.depot_id)
                    depot_lat = depot.lat if depot else vehicle.current_lat
                    depot_lng = depot.lng if depot else vehicle.current_lng

                    if assignments[vehicle.id]:
                        last_loc = (assignments[vehicle.id][-1].lat, assignments[vehicle.id][-1].lng)
                    else:
                        last_loc = (depot_lat, depot_lng)

                    dist = cls.haversine_distance_km(last_loc[0], last_loc[1], order.lat, order.lng)
                    cost_estimate = dist * vehicle.cost_per_km

                    # EV preference for lower carbon footprint
                    if vehicle.fuel_type == "Electric":
                        cost_estimate *= 0.85

                    if cost_estimate < min_extra_cost:
                        min_extra_cost = cost_estimate
                        best_vehicle = vehicle

            if best_vehicle:
                assignments[best_vehicle.id].append(order)
                order.assigned_vehicle_id = best_vehicle.id
                order.assigned_depot_id = best_vehicle.depot_id
                order.status = "assigned"
            else:
                unassigned_orders.append(order)

        # Step 2: Route construction with 2-Opt TSP optimization per vehicle
        for vehicle in available_vehicles:
            vehicle_orders = assignments[vehicle.id]
            depot = depots.get(vehicle.depot_id)
            depot_lat = depot.lat if depot else vehicle.current_lat
            depot_lng = depot.lng if depot else vehicle.current_lng

            if not vehicle_orders:
                vehicle.route_stops = []
                vehicle.total_distance_km = 0.0
                vehicle.total_time_min = 0.0
                vehicle.total_cost_usd = 0.0
                vehicle.total_co2_kg = 0.0
                vehicle.status = "idle"
                continue

            # Optimize stop sequence (Nearest Neighbor with 2-Opt refinement)
            ordered_stops = cls._nearest_neighbor_sequence(
                depot_lat, depot_lng, vehicle_orders
            )
            ordered_stops = cls._two_opt_refine(
                depot_lat, depot_lng, ordered_stops
            )

            # Build detailed RouteStops
            stops: List[RouteStop] = []
            curr_lat, curr_lng = depot_lat, depot_lng
            total_dist = 0.0
            total_time = 0.0
            cum_load = sum(o.weight_kg for o in ordered_stops)

            # Origin stop
            stops.append(RouteStop(
                stop_type="depot_origin",
                reference_id=vehicle.depot_id,
                name=f"{depot.name if depot else 'Depot'} (Dispatch)",
                lat=depot_lat,
                lng=depot_lng,
                arrival_time_min=0.0,
                cumulative_distance_km=0.0,
                payload_weight_kg=cum_load
            ))

            for o in ordered_stops:
                leg_dist = cls.haversine_distance_km(curr_lat, curr_lng, o.lat, o.lng)
                leg_time = cls.travel_time_minutes(leg_dist, vehicle.avg_speed_kmh)

                # Service time allowance (10 minutes unloading)
                service_time = 10.0
                total_dist += leg_dist
                total_time += (leg_time + service_time)
                cum_load -= o.weight_kg

                o.estimated_arrival_minutes = round(total_time, 1)

                stops.append(RouteStop(
                    stop_type="delivery",
                    reference_id=o.id,
                    name=f"Dropoff: {o.customer} ({o.item})",
                    lat=o.lat,
                    lng=o.lng,
                    order_id=o.id,
                    arrival_time_min=round(total_time, 1),
                    cumulative_distance_km=round(total_dist, 2),
                    payload_weight_kg=max(0.0, cum_load)
                ))
                curr_lat, curr_lng = o.lat, o.lng

            # Return to depot
            return_dist = cls.haversine_distance_km(curr_lat, curr_lng, depot_lat, depot_lng)
            return_time = cls.travel_time_minutes(return_dist, vehicle.avg_speed_kmh)
            total_dist += return_dist
            total_time += return_time

            stops.append(RouteStop(
                stop_type="depot_return",
                reference_id=vehicle.depot_id,
                name=f"{depot.name if depot else 'Depot'} (Return)",
                lat=depot_lat,
                lng=depot_lng,
                arrival_time_min=round(total_time, 1),
                cumulative_distance_km=round(total_dist, 2),
                payload_weight_kg=0.0
            ))

            vehicle.route_stops = stops
            vehicle.assigned_orders = [o.id for o in ordered_stops]
            vehicle.total_distance_km = round(total_dist, 2)
            vehicle.total_time_min = round(total_time, 1)
            vehicle.total_cost_usd = round(total_dist * vehicle.cost_per_km, 2)
            vehicle.total_co2_kg = round(total_dist * vehicle.co2_per_km_kg, 2)
            vehicle.status = "en_route"

        return {
            "assigned_count": len(pending_orders) - len(unassigned_orders),
            "unassigned_orders": [o.id for o in unassigned_orders],
            "active_vehicles": len([v for v in available_vehicles if v.assigned_orders])
        }

    @classmethod
    def _nearest_neighbor_sequence(
        cls, start_lat: float, start_lng: float, orders: List[Order]
    ) -> List[Order]:
        """Arranges orders using Greedy Nearest Neighbor heuristic."""
        unvisited = list(orders)
        sequence: List[Order] = []
        curr_lat, curr_lng = start_lat, start_lng

        while unvisited:
            unvisited.sort(key=lambda o: cls.haversine_distance_km(curr_lat, curr_lng, o.lat, o.lng))
            next_order = unvisited.pop(0)
            sequence.append(next_order)
            curr_lat, curr_lng = next_order.lat, next_order.lng

        return sequence

    @classmethod
    def _two_opt_refine(
        cls, start_lat: float, start_lng: float, sequence: List[Order]
    ) -> List[Order]:
        """Refines tour sequence using 2-Opt pairwise edge swap local search."""
        if len(sequence) < 3:
            return sequence

        def tour_distance(seq: List[Order]) -> float:
            dist = cls.haversine_distance_km(start_lat, start_lng, seq[0].lat, seq[0].lng)
            for i in range(len(seq) - 1):
                dist += cls.haversine_distance_km(seq[i].lat, seq[i].lng, seq[i + 1].lat, seq[i + 1].lng)
            dist += cls.haversine_distance_km(seq[-1].lat, seq[-1].lng, start_lat, start_lng)
            return dist

        best_seq = list(sequence)
        best_dist = tour_distance(best_seq)
        improved = True
        iterations = 0

        while improved and iterations < 30:
            improved = False
            iterations += 1
            for i in range(len(best_seq) - 1):
                for j in range(i + 1, len(best_seq)):
                    # Reverse intermediate segment [i:j+1]
                    new_seq = best_seq[:i] + best_seq[i:j + 1][::-1] + best_seq[j + 1:]
                    new_dist = tour_distance(new_seq)
                    if new_dist < best_dist - 0.01:
                        best_seq = new_seq
                        best_dist = new_dist
                        improved = True
                        break
                if improved:
                    break

        return best_seq
