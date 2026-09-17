"""
Store Demand & Regional Foot-Traffic Simulation Specialist Agent.
Analyzes store-by-store foot traffic surges, localized sell-through velocity, and stockout probabilities.
"""
from typing import Dict, Any, List
from backend.simulation.data_models import STORES_DATA

class StoreDemandAgent:
    def __init__(self):
        self.name = "store_demand_agent"
        self.role = "Regional Store Demand & Traffic Specialist"
        self.disallow_transfer_to_parent = True
        self.disallow_transfer_to_peers = True

    def analyze(self, promo_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulates foot traffic, demand surge, and store-level stockout hazards.
        """
        stores: List[Dict[str, Any]] = []
        critical_count = 0
        high_risk_count = 0
        total_projected_demand = 0
        total_on_hand = 0

        for store in STORES_DATA:
            s_copy = dict(store)
            total_projected_demand += s_copy["projected_promo_demand"]
            total_on_hand += s_copy["current_on_hand"]
            if s_copy["risk_status"] == "CRITICAL_STOCKOUT":
                critical_count += 1
            elif s_copy["risk_status"] in ("HIGH_RISK", "ELEVATED_RISK"):
                high_risk_count += 1
            stores.append(s_copy)

        national_stockout_risk_avg = sum(s["stockout_risk_pct"] for s in stores) / len(stores)

        findings = {
            "agent": self.name,
            "status": "COMPLETED",
            "summary": (
                f"Simulated {len(stores)} regional store clusters. Identified {critical_count} critical stockout location(s) "
                f"(notably Manhattan NYC at 82.5% risk by Day 2) and {high_risk_count} elevated risk stores. "
                f"Total store demand will spike to {total_projected_demand:,} units against {total_on_hand:,} on-hand stock."
            ),
            "metrics": {
                "total_stores_simulated": len(stores),
                "critical_stockout_stores": critical_count,
                "high_risk_stores": high_risk_count,
                "average_national_stockout_risk": f"{national_stockout_risk_avg:.1f}%",
                "total_projected_store_units": total_projected_demand,
                "total_store_inventory_on_hand": total_on_hand,
            },
            "store_matrix": stores,
            "key_vulnerabilities": [
                "Manhattan Flagship (STR-101) breaches inventory on Day 2 due to +145% foot traffic and small backroom.",
                "San Francisco Union Sq (STR-112) BOPIS locker congestion creates an in-store pickup deadlock.",
                "Austin (STR-108) faces a 24-hour regional transit lag from Dallas DC."
            ]
        }
        return findings
