import time
from typing import Dict, List, Any, Optional
from ..models.entities import Disruption, Vehicle, Order

class DisruptionEngine:
    """
    Simulates dynamic logistics chaos and disruption injection (Chaos Monkey for Supply Chains).
    """

    PRESETS = {
        "breakdown": {
            "title": "Engine Telematics Failure - Titan Heavy Cargo",
            "type": "breakdown",
            "description": "Vehicle FLEET-TRK-02 experienced critical coolant leak. Transmission stalled on Eastern Expressway.",
            "severity": "CRITICAL",
            "target_vehicle_id": "FLEET-TRK-02"
        },
        "severe_weather": {
            "title": "Severe Flash Flooding & Cyclone Alert",
            "type": "severe_weather",
            "description": "Torrential monsoon rains inundated low-lying arterial transit corridor. Road access blocked within 4.5km radius.",
            "severity": "HIGH",
            "affected_lat": 19.1450,
            "affected_lng": 72.9350,
            "radius_km": 4.5
        },
        "road_closure": {
            "title": "Major Highway Collision & Hazardous Spill",
            "type": "road_closure",
            "description": "Multi-car pileup blocked Western Express Highway. Emergency hazmat crews on site.",
            "severity": "HIGH",
            "affected_lat": 19.0950,
            "affected_lng": 72.8550,
            "radius_km": 3.0
        },
        "urgent_surge": {
            "title": "Emergency Vaccine Demand Surge",
            "type": "urgent_surge",
            "description": "Hospital trauma unit issued priority code-red requisition for emergency trauma supplies and cold vaccines.",
            "severity": "CRITICAL",
            "new_order": {
                "id": "ORD-SURGE-99",
                "customer": "Memorial Emergency Trauma Center",
                "item": "cold_chain_vaccines",
                "quantity": 30,
                "weight_kg": 90,
                "volume_m3": 1.2,
                "lat": 19.0600,
                "lng": 72.8350,
                "priority": "CRITICAL",
                "deadline_minutes": 45,
                "sla_penalty_usd": 2500
            }
        }
    }

    @classmethod
    def create_disruption(cls, disruption_type: str, custom_params: Optional[Dict[str, Any]] = None) -> Disruption:
        preset = cls.PRESETS.get(disruption_type, cls.PRESETS["breakdown"]).copy()
        if custom_params:
            preset.update(custom_params)

        disruption_id = f"DISRUPT-{int(time.time())}"
        return Disruption(
            id=disruption_id,
            type=preset.get("type", "unknown"),
            title=preset.get("title", "Logistics Disruption"),
            description=preset.get("description", ""),
            severity=preset.get("severity", "HIGH"),
            target_vehicle_id=preset.get("target_vehicle_id"),
            affected_lat=preset.get("affected_lat"),
            affected_lng=preset.get("affected_lng"),
            radius_km=preset.get("radius_km"),
            active=True,
            timestamp=time.strftime("%H:%M:%S")
        )
