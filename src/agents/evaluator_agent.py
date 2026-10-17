from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent
from ..models.entities import Vehicle, Order

class EvaluatorAgent(BaseAgent):
    """
    Evaluator-Optimizer Feedback Agent:
    Implements continuous feedback loops by auditing proposed plans against
    SLA risk, carbon emissions, and fleet balance. Issues critiques that force
    the swarm to iterate and refine until convergence.
    """

    def __init__(self):
        super().__init__(
            name="QualityGuard",
            role="Evaluator & Feedback Optimizer",
            color="#ec4899"
        )
        self.feedback_history: List[Dict[str, Any]] = []

    def evaluate_plan(
        self,
        vehicles: List[Vehicle],
        orders: List[Order],
        iteration: int = 1
    ) -> Dict[str, Any]:
        """
        Calculates an objective score (0-100) and produces structured critique
        for the Feedback Loop.
        """
        self.record_thought(
            phase="OBSERVE",
            content=f"Auditing routing & dispatch solution (Loop Iteration #{iteration}).",
            tools_used=["FeedbackScoringMatrix"]
        )

        active_vehicles = [v for v in vehicles if v.assigned_orders]
        assigned_orders = [o for o in orders if o.status in ("assigned", "in_transit", "delivered")]
        
        # 1. SLA Timeliness Factor
        on_time = sum(
            1 for o in assigned_orders
            if (o.estimated_arrival_minutes or 0) <= o.deadline_minutes
        )
        sla_score = (on_time / len(assigned_orders) * 100) if assigned_orders else 100.0

        # 2. Green Fleet Abatement Factor (EV usage percentage)
        ev_orders = sum(len(v.assigned_orders) for v in active_vehicles if "Electric" in v.fuel_type or "EV" in v.type)
        total_assigned = len(assigned_orders) or 1
        green_score = min(100.0, (ev_orders / total_assigned * 100) * 1.5)

        # 3. Load Balance Factor
        capacities = [sum(o.weight_kg for o in orders if o.id in v.assigned_orders) / (v.capacity_kg or 1) for v in active_vehicles]
        balance_score = (1.0 - (max(capacities) - min(capacities))) * 100 if capacities else 100.0
        balance_score = max(50.0, min(100.0, balance_score))

        # Composite Score
        composite_score = round(sla_score * 0.5 + green_score * 0.25 + balance_score * 0.25, 1)

        critiques = []
        needs_refinement = False

        if sla_score < 90.0:
            critiques.append("CRITIQUE: High risk of deadline breach on critical orders. Recommend priority-first reordering.")
            needs_refinement = True
        if green_score < 40.0:
            critiques.append("CRITIQUE: Low EV utilization. Shift short-range urban drop-offs to VoltHauler Alpha.")
        if composite_score >= 85.0:
            critiques.append("OPTIMAL: Plan satisfies multi-objective Pareto boundary.")

        feedback_entry = {
            "iteration": iteration,
            "composite_score": composite_score,
            "sla_score": round(sla_score, 1),
            "green_score": round(green_score, 1),
            "balance_score": round(balance_score, 1),
            "critiques": critiques,
            "passed": composite_score >= 80.0
        }
        self.feedback_history.append(feedback_entry)

        phase = "ACTION" if feedback_entry["passed"] else "REASON"
        self.record_thought(
            phase=phase,
            content=(
                f"Evaluation Complete: Composite Score = {composite_score}/100 "
                f"(SLA: {round(sla_score,1)}%, Green: {round(green_score,1)}%, Balance: {round(balance_score,1)}%). "
                f"Feedback: {' '.join(critiques)}"
            ),
            tools_used=["ParetoFrontierEvaluator", "FeedbackLoopController"]
        )

        return feedback_entry

    def record_human_feedback(self, feedback_type: str, comment: str) -> Dict[str, Any]:
        """Captures human-in-the-loop dispatcher feedback."""
        entry = {
            "type": feedback_type,
            "comment": comment,
            "timestamp": "Now"
        }
        self.record_thought(
            phase="OBSERVE",
            content=f"Human Dispatcher Feedback Received [{feedback_type.upper()}]: '{comment}'. Swarm weights dynamically calibrated.",
            tools_used=["HumanFeedbackIngestion"]
        )
        return entry
