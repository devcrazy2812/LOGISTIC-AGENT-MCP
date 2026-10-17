from typing import List, Dict, Any, Optional
from .base_agent import BaseAgent
from ..models.entities import Vehicle, Order, Depot
from ..tools.geo_solver import GeoRoutingSolver

class RouterAgent(BaseAgent):
    """
    Fleet Routing & Optimization Agent:
    Solves Capacitated Vehicle Routing (CVRP), prioritizes EV fleets for low carbon emissions,
    and dynamically recalculates paths during disruptions.
    """

    def __init__(self):
        super().__init__(
            name="RouteOptima",
            role="Fleet & Routing Specialist",
            color="#10b981"
        )

    def optimize_routes(
        self,
        vehicles: List[Vehicle],
        orders: List[Order],
        depots: Dict[str, Depot],
        active_disruptions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        self.record_thought(
            phase="OBSERVE",
            content=f"Initiating routing synthesis for {len(vehicles)} vehicles across {len(orders)} destination waypoints.",
            tools_used=["CVRPSolver", "HaversineDistanceMatrix"]
        )

        optimization_result = GeoRoutingSolver.optimize_fleet_routes(
            vehicles=vehicles,
            orders=orders,
            depots=depots,
            active_disruptions=active_disruptions
        )

        active_vehicles = [v for v in vehicles if v.assigned_orders]
        total_dist = sum(v.total_distance_km for v in active_vehicles)
        total_cost = sum(v.total_cost_usd for v in active_vehicles)
        total_co2 = sum(v.total_co2_kg for v in active_vehicles)

        self.record_thought(
            phase="REASON",
            content=(
                f"Generated optimal routing plan: {len(active_vehicles)} active trucks dispatched. "
                f"Total route distance: {round(total_dist, 1)} km. Estimated logistics cost: ${round(total_cost, 2)}. "
                f"Projected fleet CO2 emissions: {round(total_co2, 2)} kg."
            ),
            tools_used=["MultiModalPathOptimizer", "CarbonEmissionModel"]
        )

        if optimization_result["unassigned_orders"]:
            self.record_thought(
                phase="ACTION",
                content=(
                    f"Warning: {len(optimization_result['unassigned_orders'])} orders could not be accommodated "
                    "due to vehicle weight/volume boundaries or active hazard zones. Recommending spot-carrier bidding to Liaison."
                ),
                tools_used=["OverflowCapacityAlert"]
            )

        return optimization_result
