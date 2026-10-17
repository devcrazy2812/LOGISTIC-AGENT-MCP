from typing import List, Dict, Any, Optional, Tuple
from .base_agent import BaseAgent
from ..models.entities import Disruption, Vehicle, Order


class SentinelAgent(BaseAgent):
    """
    Sentinel Risk & Anomaly Detection Agent:
    Monitors telematics, weather feeds, and traffic conditions to detect disruptions in real-time.
    Includes cold-chain thermal excursion tracking and corridor weather alerts.
    """

    def __init__(self):
        super().__init__(
            name="Sentinel-Risk",
            role="Disruption & Anomaly Monitor",
            color="#ef4444"
        )
        self.cold_chain_threshold_celsius = 8.0

    def scan_for_risks(
        self,
        vehicles: List[Vehicle],
        orders: List[Order],
        disruptions: List[Disruption]
    ) -> Dict[str, Any]:
        """Scans the supply chain telemetry for active disruptions, weather alerts, or thermal excursions."""
        active = [d for d in disruptions if d.active]

        # Scan for cold-chain excursions
        cold_chain_alerts = self.scan_cold_chain_telematics(vehicles, orders)

        if not active and not cold_chain_alerts:
            self.record_thought(
                phase="OBSERVE",
                content="Telemetry scan complete across all corridors. Weather radar clear. Traffic flows normal. No vehicle distress or thermal excursions detected.",
                tools_used=["TelematicsRadar", "WeatherMonitor", "ColdChainSensors"]
            )
            return {"status": "NORMAL", "impacted_orders": [], "impacted_vehicles": [], "alerts": []}

        impacted_vehicles = []
        impacted_orders = []
        alerts = list(cold_chain_alerts)

        if active:
            lead_disruption = active[-1]
            self.record_thought(
                phase="OBSERVE",
                content=f"ALERT! Anomaly detected: {lead_disruption.title} [{lead_disruption.severity}]. Details: {lead_disruption.description}",
                tools_used=["IncidentTelemetry", "GeoSpatialRadar"]
            )

            if lead_disruption.target_vehicle_id:
                impacted_vehicles = [v for v in vehicles if v.id == lead_disruption.target_vehicle_id]
                for v in impacted_vehicles:
                    v.status = "disrupted"
                    impacted_orders.extend([o for o in orders if o.id in v.assigned_orders])

            if lead_disruption.affected_lat and lead_disruption.radius_km:
                from ..tools.geo_solver import GeoRoutingSolver
                for o in orders:
                    dist = GeoRoutingSolver.haversine_distance_km(
                        lead_disruption.affected_lat, lead_disruption.affected_lng, o.lat, o.lng
                    )
                    if dist <= lead_disruption.radius_km:
                        impacted_orders.append(o)

            self.record_thought(
                phase="REASON",
                content=(
                    f"Impact assessment: {len(impacted_vehicles)} vehicle(s) disabled, "
                    f"{len(impacted_orders)} customer shipment(s) at immediate risk of SLA breach. "
                    "Triggering autonomous swarm emergency protocol."
                ),
                tools_used=["ImpactAnalysisModel"]
            )

            return {
                "status": "DISRUPTED",
                "disruption": lead_disruption,
                "impacted_vehicles": [v.id for v in impacted_vehicles],
                "impacted_orders": [o.id for o in impacted_orders],
                "alerts": alerts
            }

        return {
            "status": "ALERT",
            "impacted_vehicles": [],
            "impacted_orders": [],
            "alerts": alerts
        }

    def scan_cold_chain_telematics(
        self,
        vehicles: List[Vehicle],
        orders: List[Order]
    ) -> List[Dict[str, Any]]:
        """Audits real-time thermal telematics on cold-chain pharmaceutical cargo."""
        alerts = []
        for v in vehicles:
            if not v.assigned_orders:
                continue
            has_cold_chain = any(
                o.item == "cold_chain_vaccines"
                for o in orders if o.id in v.assigned_orders
            )
            if has_cold_chain:
                # Simulated telematics sensor read: normal is 3.5C, excursion above 8.0C
                sensor_temp = 4.2  # Normal nominal operating temperature
                if v.status == "disrupted":
                    # Reefer failure simulation
                    sensor_temp = 9.8
                    alerts.append({
                        "vehicle_id": v.id,
                        "type": "COLD_CHAIN_EXCURSION",
                        "severity": "CRITICAL",
                        "temperature_celsius": sensor_temp,
                        "threshold_celsius": self.cold_chain_threshold_celsius,
                        "message": f"Critical thermal excursion on {v.name}: {sensor_temp}°C exceeds {self.cold_chain_threshold_celsius}°C limit"
                    })
                    self.record_thought(
                        phase="OBSERVE",
                        content=f"THERMAL EXCURSION WARNING: Reefer temperature on {v.name} breached {self.cold_chain_threshold_celsius}°C (reading {sensor_temp}°C).",
                        tools_used=["ReeferIoTTelemetry"]
                    )
        return alerts

    def check_weather_signals(self, coords: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
        """Audits weather radar signals along planned routing coordinates."""
        weather_alerts = []
        for lat, lng in coords:
            # Check regional weather anomaly zone near lat 37.77, lng -122.42
            if abs(lat - 37.77) < 0.05 and abs(lng - (-122.42)) < 0.05:
                weather_alerts.append({
                    "lat": lat,
                    "lng": lng,
                    "type": "STORM_FRONT",
                    "severity": "HIGH",
                    "precipitation_mm": 45.0,
                    "wind_gust_kmh": 68.0,
                    "advisory": "Flash flood risk on I-80 low-lying underpass"
                })
        return weather_alerts
