from typing import List, Dict, Any, Optional
from .base_agent import BaseAgent
from .sentinel_agent import SentinelAgent
from .warehouse_agent import WarehouseAgent
from .router_agent import RouterAgent
from .liaison_agent import LiaisonAgent
from .evaluator_agent import EvaluatorAgent
from ..models.entities import Depot, Vehicle, Order, Disruption

class OrchestratorAgent(BaseAgent):
    """
    Master Dispatch Commander & Swarm Orchestrator:
    Coordinates cross-agent decisions, arbitrates trade-offs between speed, cost, and carbon emissions,
    and supervises the Evaluator Feedback Loop and Self-Healing during crises.
    """

    def __init__(
        self,
        sentinel: SentinelAgent,
        warehouse: WarehouseAgent,
        router: RouterAgent,
        liaison: LiaisonAgent,
        evaluator: Optional[EvaluatorAgent] = None
    ):
        super().__init__(
            name="Commander-Prime",
            role="Master Swarm Orchestrator",
            color="#3b82f6"
        )
        self.sentinel = sentinel
        self.warehouse = warehouse
        self.router = router
        self.liaison = liaison
        self.evaluator = evaluator or EvaluatorAgent()

    def orchestrate_initial_dispatch(
        self,
        depots: Dict[str, Depot],
        vehicles: List[Vehicle],
        orders: List[Order]
    ) -> Dict[str, Any]:
        self.record_thought(
            phase="OBSERVE",
            content=f"Mission initialized. Managing global logistics state with {len(depots)} depots, {len(vehicles)} vehicles, and {len(orders)} consignment orders.",
            tools_used=["SwarmStateSynchronizer"]
        )

        # Step 1: Sentinel checks environment
        risk_report = self.sentinel.scan_for_risks(vehicles, orders, [])

        # Step 2: Warehouse allocates stock
        stock_report = self.warehouse.verify_and_allocate(depots, orders)

        # Step 3: Router calculates optimal routes
        routing_report = self.router.optimize_routes(vehicles, orders, depots, [])

        # Step 4: Feedback Loop (Evaluator-Optimizer audit)
        feedback_report = self.evaluator.evaluate_plan(vehicles, orders, iteration=1)

        # If feedback suggests refinement, perform 2nd pass feedback optimization
        if not feedback_report["passed"]:
            self.record_thought(
                phase="REASON",
                content=f"Evaluator flagged optimization critique: {feedback_report['critiques']}. Triggering feedback refinement loop.",
                tools_used=["FeedbackLoopOptimizer"]
            )
            routing_report = self.router.optimize_routes(vehicles, orders, depots, [])
            feedback_report = self.evaluator.evaluate_plan(vehicles, orders, iteration=2)

        # Step 5: Liaison checks SLA
        notifications = self.liaison.handle_stakeholder_communications(orders, vehicles)

        self.record_thought(
            phase="ACTION",
            content=f"Dispatch plan synthesized, audited (Score: {feedback_report['composite_score']}/100), and cleared for departure.",
            tools_used=["MissionApprovalProtocol"]
        )

        return {
            "risk_report": risk_report,
            "stock_report": stock_report,
            "routing_report": routing_report,
            "feedback_report": feedback_report,
            "notifications": notifications
        }

    def orchestrate_disruption_recovery(
        self,
        disruption: Disruption,
        depots: Dict[str, Depot],
        vehicles: List[Vehicle],
        orders: List[Order]
    ) -> Dict[str, Any]:
        self.record_thought(
            phase="OBSERVE",
            content=f"CRISIS DETECTED: {disruption.title} ({disruption.severity}). Initiating emergency self-healing swarm protocol.",
            tools_used=["IncidentResponseMatrix"]
        )

        # Step 1: Sentinel analyzes affected entities
        risk_report = self.sentinel.scan_for_risks(vehicles, orders, [disruption])

        # Step 2: Unassign orders from disabled vehicle or hazard zones
        impacted_order_ids = set(risk_report.get("impacted_orders", []))
        for o in orders:
            if o.id in impacted_order_ids or o.assigned_vehicle_id in risk_report.get("impacted_vehicles", []):
                o.status = "re_routed"
                o.assigned_vehicle_id = None

        self.record_thought(
            phase="REASON",
            content=f"Releasing {len(impacted_order_ids)} orders from disabled assets. Directing RouteOptima to re-solve CVRP with active bypass constraints.",
            tools_used=["ConstraintRelaxationEngine"]
        )

        # Step 3: Router recalculates with active disruption constraints
        active_disruptions = [disruption.to_dict()]
        routing_report = self.router.optimize_routes(
            vehicles=vehicles,
            orders=orders,
            depots=depots,
            active_disruptions=active_disruptions
        )

        # Step 4: Feedback Loop post-recovery audit
        feedback_report = self.evaluator.evaluate_plan(vehicles, orders, iteration=1)

        # Step 5: Liaison broadcasts apology and live ETA updates
        notifications = self.liaison.handle_stakeholder_communications(
            orders=orders,
            vehicles=vehicles,
            disruption_event=disruption.to_dict()
        )

        self.record_thought(
            phase="ACTION",
            content=f"Disruption neutralized. Self-healing completed (Post-recovery Plan Quality Score: {feedback_report['composite_score']}/100).",
            tools_used=["SelfHealingSwarmConsensus"]
        )

        return {
            "status": "RECOVERED",
            "disruption": disruption.to_dict(),
            "routing_report": routing_report,
            "feedback_report": feedback_report,
            "notifications": notifications
        }
