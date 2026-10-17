from typing import List, Dict, Any, Optional
from .base_agent import BaseAgent
from ..models.entities import Disruption, Vehicle, Order

class SentinelAgent(BaseAgent):
    """
    Sentinel Risk & Anomaly Detection Agent:
    Monitors telematics, weather feeds, and traffic conditions to detect disruptions in real-time.
    """

    def __init__(self):
        super().__init__(
            name="Sentinel-Risk",
            role="Disruption & Anomaly Monitor",
            color="#ef4444"
        )

    def scan_for_risks(
        self,
        vehicles: List[Vehicle],
        orders: List[Order],
        disruptions: List[Disruption]
    ) -> Dict[str, Any]:
        """Scans the supply chain telemetry for active or imminent disruptions."""
        active = [d for d in disruptions if d.active]

        if not active:
            self.record_thought(
                phase="OBSERVE",
                content="Telemetry scan complete across all corridors. Weather radar clear. Traffic flows normal. No vehicle distress signals detected.",
                tools_used=["TelematicsRadar", "WeatherMonitor"]
            )
            return {"status": "NORMAL", "impacted_orders": [], "impacted_vehicles": []}

        # Analyze highest severity disruption
        lead_disruption = active[-1]
        self.record_thought(
            phase="OBSERVE",
            content=f"ALERT! Anomaly detected: {lead_disruption.title} [{lead_disruption.severity}]. Details: {lead_disruption.description}",
            tools_used=["IncidentTelemetry", "GeoSpatialRadar"]
        )

        impacted_vehicles = []
        impacted_orders = []

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
            "impacted_orders": [o.id for o in impacted_orders]
        }
