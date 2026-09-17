"""
Supplier & Vendor Capacity Specialist Agent.
Simulates tier-1/tier-2 manufacturing lead times, OTIF reliability, factory utilization, and emergency restock costs.
"""
from typing import Dict, Any, List
from backend.simulation.data_models import SUPPLIERS_DATA

class SupplierCapacityAgent:
    def __init__(self):
        self.name = "supplier_capacity_agent"
        self.role = "Supplier & Global Manufacturing Specialist"
        self.disallow_transfer_to_parent = True
        self.disallow_transfer_to_peers = True

    def analyze(self, promo_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulates vendor capacities, standard vs expedited PO lead times, and upstream supply vulnerabilities.
        """
        suppliers: List[Dict[str, Any]] = []
        bottleneck_count = 0
        total_expedited_surcharge = 0
        total_max_surge_capacity = 0

        for sup in SUPPLIERS_DATA:
            s_copy = dict(sup)
            total_max_surge_capacity += s_copy["max_surge_units"]
            if s_copy["status"] in ("CONSTRAINED", "CRITICAL_BOTTLENECK"):
                bottleneck_count += 1
            suppliers.append(s_copy)

        findings = {
            "agent": self.name,
            "status": "COMPLETED",
            "summary": (
                f"Audited {len(suppliers)} critical Tier-1 component suppliers. Identified {bottleneck_count} severely constrained "
                f"suppliers. Standard reorder lead times (14 to 28 days) will NOT support in-flight promo replenishment. "
                f"Expedited air-freight POs (3 to 8 days) are required immediately to release {total_max_surge_capacity:,} surge units."
            ),
            "metrics": {
                "suppliers_audited": len(suppliers),
                "constrained_suppliers": bottleneck_count,
                "total_available_surge_units": total_max_surge_capacity,
                "average_vendor_otif": "91.9%",
                "expedited_air_freight_window": "3 - 8 Days",
            },
            "supplier_matrix": suppliers,
            "key_vulnerabilities": [
                "Apex Display (SUP-801): 96.4% factory utilization; 28-day standard sea freight means zero replenishment without expedited air-lift.",
                "RoboMotion Mechatronics (SUP-619): 84.0% OTIF reliability with rare earth magnet shortages in Germany.",
                "Sonics MicroAcoustics (SUP-742) and IoT Gateway (SUP-550) have healthy capacity and low risk."
            ]
        }
        return findings
