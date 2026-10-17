from typing import Dict, List, Any
from .base_agent import BaseAgent
from ..models.entities import Depot, Order
from ..tools.inventory_engine import InventoryEngine

class WarehouseAgent(BaseAgent):
    """
    Warehouse & Inventory Allocation Agent:
    Tracks inventory across multi-regional distribution hubs and manages cross-dock logistics.
    """

    def __init__(self):
        super().__init__(
            name="StockMaster",
            role="Warehouse & Inventory Specialist",
            color="#8b5cf6"
        )

    def verify_and_allocate(self, depots: Dict[str, Depot], orders: List[Order]) -> Dict[str, Any]:
        self.record_thought(
            phase="OBSERVE",
            content=f"Auditing stock availability across {len(depots)} regional distribution hubs for {len(orders)} active order requisitions.",
            tools_used=["ERPInventoryDatabase"]
        )

        results = InventoryEngine.allocate_order_inventory(depots, orders)
        fulfilled_count = len(results["fulfilled_orders"])
        backorder_count = len(results["backordered_orders"])

        self.record_thought(
            phase="REASON",
            content=(
                f"Inventory allocation results: {fulfilled_count} orders successfully backed by regional stocks. "
                f"{backorder_count} requisitions require inter-hub transfers or emergency warehouse prioritization."
            ),
            tools_used=["CrossDockingOptimizer"]
        )

        # Check safety stock
        alerts = InventoryEngine.check_safety_stock(depots)
        if alerts:
            self.record_thought(
                phase="ACTION",
                content=f"Safety stock alert: {len(alerts)} item categories flagged below minimum replenishment threshold. Auto-generating supply POs.",
                tools_used=["AutoReplenishmentEngine"]
            )

        return results
