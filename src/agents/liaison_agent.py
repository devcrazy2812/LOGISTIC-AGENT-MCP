from typing import List, Dict, Any, Optional
from .base_agent import BaseAgent
from ..models.entities import Order, Vehicle

class LiaisonAgent(BaseAgent):
    """
    Customer SLA & Carrier Liaison Agent:
    Handles automated stakeholder communications, ETA updates, SLA penalty mitigation,
    and spot carrier spot-market negotiation for overflow cargo.
    """

    def __init__(self):
        super().__init__(
            name="CommLiaison",
            role="SLA & Carrier Negotiator",
            color="#f59e0b"
        )

    def handle_stakeholder_communications(
        self,
        orders: List[Order],
        vehicles: List[Vehicle],
        disruption_event: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        notifications = []

        if not disruption_event:
            self.record_thought(
                phase="OBSERVE",
                content="Reviewing all scheduled customer delivery windows against agreed SLAs.",
                tools_used=["SLAPenaltyCalculator"]
            )
            for o in orders:
                if o.status == "assigned" and o.estimated_arrival_minutes:
                    if o.estimated_arrival_minutes > o.deadline_minutes:
                        msg = (
                            f"Proactive Alert to {o.customer}: Estimated arrival ({o.estimated_arrival_minutes} min) "
                            f"may exceed standard deadline ({o.deadline_minutes} min). Expedited priority granted."
                        )
                        notifications.append({"order_id": o.id, "type": "warning", "message": msg})
            
            self.record_thought(
                phase="ACTION",
                content=f"Dispatched {len(orders)} live tracking links and digital consignment notes to clients.",
                tools_used=["AutomatedNotificationDispatcher"]
            )
            return notifications

        # Disruption handling communications
        self.record_thought(
            phase="OBSERVE",
            content=f"Assessing stakeholder impact of crisis event: {disruption_event.get('title')}",
            tools_used=["CustomerImpactMatrix"]
        )

        delayed_orders = [o for o in orders if o.status in ("delayed", "re_routed")]
        saved_penalties = sum(o.sla_penalty_usd for o in delayed_orders)

        self.record_thought(
            phase="REASON",
            content=(
                f"Autonomous re-routing protected ${saved_penalties:,.2f} in contractual SLA delay penalties. "
                f"Generating personalized transparency notices with courtesy discount credits."
            ),
            tools_used=["ContractPenaltyMitigator", "B2BCommunicationSynthesizer"]
        )

        for o in delayed_orders:
            notice = (
                f"[DISPATCH DIRECTIVE TO {o.customer.upper()}] Our autonomous logistics radar detected an en-route transit hazard. "
                f"Shipment #{o.id} ({o.item}) has been autonomously rerouted to an alternate verified corridor. "
                f"Updated ETA: {o.estimated_arrival_minutes or 'Recalculating'} mins. A 10% courtesy credit has been issued."
            )
            notifications.append({"order_id": o.id, "type": "crisis_update", "message": notice})

        self.record_thought(
            phase="ACTION",
            content=f"Transmitted {len(delayed_orders)} high-priority emergency transparency bulletins to impacted recipients.",
            tools_used=["DirectMessagingGateway", "CarrierDispatchChannel"]
        )

        return notifications
