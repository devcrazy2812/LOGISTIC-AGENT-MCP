from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

@dataclass
class Depot:
    id: str
    name: str
    lat: float
    lng: float
    inventory: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Order:
    id: str
    customer: str
    item: str
    quantity: int
    weight_kg: float
    volume_m3: float
    lat: float
    lng: float
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    deadline_minutes: int
    sla_penalty_usd: float
    status: str = "pending"  # pending, assigned, in_transit, delivered, delayed, re_routed
    assigned_vehicle_id: Optional[str] = None
    assigned_depot_id: Optional[str] = None
    estimated_arrival_minutes: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class RouteStop:
    stop_type: str  # 'depot_origin', 'delivery', 'depot_return'
    reference_id: str
    name: str
    lat: float
    lng: float
    order_id: Optional[str] = None
    arrival_time_min: float = 0.0
    cumulative_distance_km: float = 0.0
    payload_weight_kg: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Vehicle:
    id: str
    name: str
    type: str
    capacity_kg: float
    capacity_volume_m3: float
    depot_id: str
    current_lat: float
    current_lng: float
    fuel_type: str  # Electric, Diesel, CNG, Hybrid
    co2_per_km_kg: float
    cost_per_km: float
    avg_speed_kmh: float
    status: str = "idle"  # idle, en_route, disrupted, completed
    assigned_orders: List[str] = field(default_factory=list)
    route_stops: List[RouteStop] = field(default_factory=list)
    total_distance_km: float = 0.0
    total_time_min: float = 0.0
    total_cost_usd: float = 0.0
    total_co2_kg: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['route_stops'] = [s.to_dict() if hasattr(s, 'to_dict') else s for s in self.route_stops]
        return data

@dataclass
class Disruption:
    id: str
    type: str  # 'breakdown', 'severe_weather', 'road_closure', 'urgent_surge'
    title: str
    description: str
    severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM'
    target_vehicle_id: Optional[str] = None
    affected_lat: Optional[float] = None
    affected_lng: Optional[float] = None
    radius_km: Optional[float] = None
    active: bool = True
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AgentThought:
    agent_name: str
    role: str
    phase: str  # 'OBSERVE', 'REASON', 'CONSENSUS', 'ACTION'
    content: str
    timestamp: str
    tools_used: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SwarmMetrics:
    total_orders: int = 0
    delivered_or_scheduled: int = 0
    sla_compliance_rate: float = 100.0
    total_distance_km: float = 0.0
    total_cost_usd: float = 0.0
    total_co2_kg: float = 0.0
    co2_saved_vs_baseline_kg: float = 0.0
    active_disruptions: int = 0
    autonomous_recovery_count: int = 0
    fleet_utilization_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
