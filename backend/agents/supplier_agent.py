"""
Supplier & Vendor Capacity Specialist Agent.
Simulates tier-1/tier-2 manufacturing lead times, OTIF reliability, factory utilization, and emergency restock costs.
Consumes upstream `sku_findings` (SKU deficits & depletion days) from `SkuInventoryAgent` and publishes `supplier_findings`.
"""
from typing import Dict, Any, List, Optional
from backend.simulation.data_models import SUPPLIERS_DATA


class SupplierCapacityAgent:
    # Explicit mapping between Tier-1 suppliers and the SKUs they supply
    SUPPLIER_TO_SKU_MAP = {
        "SUP-801": "SKU-9901",
        "SUP-742": "SKU-8820",
        "SUP-619": "SKU-6612",
        "SUP-550": "SKU-7741",
    }

    def __init__(self):
        self.name = "supplier_capacity_agent"
        self.role = "Supplier & Global Manufacturing Specialist"
        self.disallow_transfer_to_parent = True
        self.disallow_transfer_to_peers = True

    def before_agent_callback(self, callback_context: Any = None) -> None:
        """ADK-compliant lifecycle hook before agent execution."""
        return None

    def after_agent_callback(self, callback_context: Any = None) -> None:
        """ADK-compliant lifecycle hook after agent execution."""
        return None

    def run_supplier_network_capacity_audit(
        self,
        promo_parameters: Dict[str, Any],
        upstream_sku_findings: Dict[str, Any],
        applied_interventions: List[str]
    ) -> tuple[List[Dict[str, Any]], float, int]:
        """
        Matches Tier-1 vendor surge capacity and air-freight lead times against
        upstream SKU-level shortages reported by SkuInventoryAgent.
        """
        forecast_multiplier = float(promo_parameters.get("forecast_multiplier", 2.7))
        scale_factor = forecast_multiplier / 2.7
        intv_02_active = "INTV-02" in applied_interventions

        sku_deficits_by_id: Dict[str, Dict[str, Any]] = upstream_sku_findings.get("sku_deficits_by_id", {})

        suppliers: List[Dict[str, Any]] = []
        total_expedited_surcharge = 0.0
        total_required_surge_units = 0

        for sup in SUPPLIERS_DATA:
            s_copy = dict(sup)
            sup_id = s_copy["supplier_id"]
            linked_sku_id = self.SUPPLIER_TO_SKU_MAP.get(sup_id, "")
            sku_info = sku_deficits_by_id.get(linked_sku_id, {})

            # Parse unit surcharge from "$45/unit ($67,500 total)"
            unit_rate_str = str(s_copy["emergency_po_surcharge"]).split("/")[0].replace("$", "").strip()
            unit_surcharge = float(unit_rate_str)

            # Determine required emergency surge units from upstream SKU deficit
            if sku_info:
                sku_deficit = int(sku_info.get("deficit_units", 0))
            else:
                # Standalone fallback scaled by forecast multiplier
                base_deficit = 1350 if sup_id == "SUP-801" else (1200 if sup_id == "SUP-619" else 0)
                sku_deficit = int(round(base_deficit * scale_factor))

            required_surge = min(int(s_copy["max_surge_units"]), max(0, sku_deficit))
            if required_surge == 0 and scale_factor > 1.05:
                required_surge = int(round(s_copy["max_surge_units"] * 0.25 * scale_factor))

            po_cost = required_surge * unit_surcharge
            total_expedited_surcharge += po_cost
            total_required_surge_units += required_surge

            if required_surge > 0:
                s_copy["emergency_po_surcharge"] = (
                    f"${int(unit_surcharge)}/unit (${int(round(po_cost)):,} emergency PO for {required_surge:,} units)"
                )

            # Dynamically adjust factory utilization and vendor status
            base_util = float(str(s_copy["factory_capacity_utilization"]).replace("%", "").strip())
            scaled_util = min(99.5, max(55.0, round(base_util * (0.85 + 0.15 * scale_factor), 1)))
            s_copy["factory_capacity_utilization"] = f"{scaled_util:.1f}%"

            if intv_02_active and sup_id in ("SUP-801", "SUP-619"):
                s_copy["status"] = "EXPEDITED_PO_ACTIVE"
            elif sku_deficit > int(s_copy["max_surge_units"]) or scaled_util >= 95.0:
                s_copy["status"] = "CRITICAL_BOTTLENECK" if sup_id == "SUP-619" else "CONSTRAINED"
            elif sku_deficit > 0 or scaled_util >= 88.0:
                s_copy["status"] = "CONSTRAINED"
            elif scaled_util < 76.0:
                s_copy["status"] = "SECURE"
            else:
                s_copy["status"] = "RESPONSIVE"

            suppliers.append(s_copy)

        return suppliers, total_expedited_surcharge, total_required_surge_units

    def analyze(
        self,
        promo_parameters: Dict[str, Any],
        session_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Simulates vendor capacities, standard vs expedited PO lead times, and upstream supply vulnerabilities,
        consuming `sku_findings` from `session_state` and writing `supplier_findings`.
        """
        upstream_sku_findings = (
            session_state.get("sku_findings", {}) if session_state is not None else {}
        )
        applied_interventions: List[str] = list(
            promo_parameters.get("applied_interventions")
            or (session_state.get("applied_interventions", []) if session_state else [])
        )

        suppliers, total_expedited_surcharge, total_required_surge_units = (
            self.run_supplier_network_capacity_audit(
                promo_parameters, upstream_sku_findings, applied_interventions
            )
        )

        bottleneck_count = 0
        total_max_surge_capacity = 0
        otif_values: List[float] = []

        for s_copy in suppliers:
            total_max_surge_capacity += int(s_copy["max_surge_units"])
            otif_values.append(float(str(s_copy["otif_score"]).replace("%", "").strip()))
            if s_copy["status"] in ("CONSTRAINED", "CRITICAL_BOTTLENECK", "EXPEDITED_PO_ACTIVE"):
                bottleneck_count += 1

        avg_otif = sum(otif_values) / len(otif_values)
        upstream_sku_deficit = int(
            upstream_sku_findings.get("deficit_units_num", total_required_surge_units)
        )

        vulnerabilities: List[str] = []
        for s_copy in suppliers:
            if s_copy["status"] in ("CONSTRAINED", "CRITICAL_BOTTLENECK"):
                vulnerabilities.append(
                    f"{s_copy['name']} ({s_copy['supplier_id']}): {s_copy['factory_capacity_utilization']} utilization; "
                    f"{s_copy['standard_lead_time_days']}-day standard freight requires {s_copy['expedited_lead_time_days']}-day air-lift "
                    f"({s_copy['emergency_po_surcharge']})."
                )
            elif s_copy["status"] == "EXPEDITED_PO_ACTIVE":
                vulnerabilities.append(
                    f"{s_copy['name']} ({s_copy['supplier_id']}): Expedited air-freight PO engaged ({s_copy['expedited_lead_time_days']}-day SLA)."
                )
        if not vulnerabilities:
            vulnerabilities.append("Tier-1 suppliers operating with adequate surge buffer capacity.")

        findings = {
            "agent": self.name,
            "status": "COMPLETED",
            "summary": (
                f"Audited {len(suppliers)} critical Tier-1 component suppliers against {upstream_sku_deficit:,} upstream SKU shortage units. "
                f"Identified {bottleneck_count} constrained/expedited vendor(s). Standard lead times (10 to 28 days) fail mid-promo replenishment; "
                f"expedited air-freight POs (${total_expedited_surcharge:,.0f} surcharge) release up to {total_max_surge_capacity:,} surge units."
            ),
            "metrics": {
                "suppliers_audited": len(suppliers),
                "constrained_suppliers": bottleneck_count,
                "upstream_sku_deficit_units": upstream_sku_deficit,
                "required_emergency_surge_units": total_required_surge_units,
                "total_expedited_surcharge": f"${total_expedited_surcharge:,.0f}",
                "total_available_surge_units": total_max_surge_capacity,
                "average_vendor_otif": f"{avg_otif:.1f}%",
                "expedited_air_freight_window": "3 - 8 Days",
            },
            "supplier_matrix": suppliers,
            "key_vulnerabilities": vulnerabilities[:3],
        }

        if session_state is not None:
            session_state["supplier_findings"] = {
                "suppliers_audited": len(suppliers),
                "constrained_suppliers": bottleneck_count,
                "upstream_sku_deficit_units": upstream_sku_deficit,
                "required_emergency_surge_units": total_required_surge_units,
                "total_expedited_surcharge_num": round(total_expedited_surcharge, 2),
                "total_available_surge_units": total_max_surge_capacity,
                "average_vendor_otif_num": round(avg_otif, 1),
                "supplier_matrix": suppliers,
            }

        return findings
