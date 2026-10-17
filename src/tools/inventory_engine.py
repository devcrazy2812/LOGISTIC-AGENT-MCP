from typing import Dict, List, Any, Tuple
from ..models.entities import Depot, Order

class InventoryEngine:
    """
    Handles Multi-Depot Inventory Allocation, Safety Stock Tracking,
    and Inter-Hub Rebalancing.
    """

    @classmethod
    def allocate_order_inventory(
        cls, depots: Dict[str, Depot], orders: List[Order]
    ) -> Dict[str, Any]:
        """
        Validates inventory across regional hubs for all requested orders.
        Returns fulfillment status and any cross-depot transfer recommendations.
        """
        results = {
            "fulfilled_orders": [],
            "backordered_orders": [],
            "transfers_needed": []
        }

        # Work on a copy of inventory so we can simulate allocations
        temp_inventory = {d_id: dict(d.inventory) for d_id, d in depots.items()}

        for order in orders:
            item = order.item
            qty = order.quantity
            assigned = False

            # Check assigned depot first if available
            preferred_depots = list(depots.keys())
            if order.assigned_depot_id and order.assigned_depot_id in preferred_depots:
                preferred_depots.remove(order.assigned_depot_id)
                preferred_depots.insert(0, order.assigned_depot_id)

            for d_id in preferred_depots:
                available = temp_inventory[d_id].get(item, 0)
                if available >= qty:
                    temp_inventory[d_id][item] -= qty
                    order.assigned_depot_id = d_id
                    assigned = True
                    results["fulfilled_orders"].append(order.id)
                    break

            if not assigned:
                # Need inter-hub rebalance or partial fulfillment
                results["backordered_orders"].append({
                    "order_id": order.id,
                    "item": item,
                    "required": qty,
                    "reason": "Insufficient stock in nearest regional depot"
                })

        return results

    @classmethod
    def check_safety_stock(cls, depots: Dict[str, Depot], threshold: int = 50) -> List[Dict[str, Any]]:
        """Identifies SKUs that have fallen below safety thresholds."""
        alerts = []
        for d_id, depot in depots.items():
            for item, qty in depot.inventory.items():
                if qty < threshold:
                    alerts.append({
                        "depot_id": d_id,
                        "depot_name": depot.name,
                        "item": item,
                        "quantity": qty,
                        "warning": f"CRITICAL: Stock below safety threshold ({threshold} units)"
                    })
        return alerts
