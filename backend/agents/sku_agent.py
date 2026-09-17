"""
SKU & Merchandising Unit Economics Specialist Agent.
Simulates promotional price elasticity, GMROI, unit margin dilution, and inventory depletion velocity.
Consumes upstream `store_findings` from `StoreDemandAgent` and publishes `sku_findings` to `session_state`.
"""
from typing import Dict, Any, List, Optional
from backend.simulation.data_models import SKUS_DATA


class SkuInventoryAgent:
    def __init__(self):
        self.name = "sku_inventory_agent"
        self.role = "Merchandising & SKU Elasticity Specialist"
        self.disallow_transfer_to_parent = True
        self.disallow_transfer_to_peers = True

    def before_agent_callback(self, callback_context: Any = None) -> None:
        """ADK-compliant lifecycle hook before agent execution."""
        return None

    def after_agent_callback(self, callback_context: Any = None) -> None:
        """ADK-compliant lifecycle hook after agent execution."""
        return None

    def run_merchandising_elasticity_model(
        self,
        promo_parameters: Dict[str, Any],
        upstream_store_findings: Dict[str, Any],
        applied_interventions: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Reconciles national SKU elasticity demand with upstream regional store demand
        and evaluates active pricing/supply interventions.
        """
        forecast_multiplier = float(promo_parameters.get("forecast_multiplier", 2.7))
        duration_days = max(1, int(promo_parameters.get("duration_days", 4)))

        # Couple SKU demand scaling to upstream StoreDemandAgent's demand uplift ratio if present
        store_uplift_ratio = float(
            upstream_store_findings.get("demand_uplift_ratio", forecast_multiplier / 2.7)
        )
        raw_multiplier_ratio = forecast_multiplier / 2.7
        blended_scale = (0.65 * store_uplift_ratio) + (0.35 * raw_multiplier_ratio)

        intv_02_active = "INTV-02" in applied_interventions
        intv_04_active = "INTV-04" in applied_interventions

        skus: List[Dict[str, Any]] = []
        for sku in SKUS_DATA:
            s_copy = dict(sku)
            sku_id = s_copy["sku_id"]

            # Parse unit promo price from "$649.99 (-28%)"
            price_token = str(s_copy["promo_price"]).split()[0].replace("$", "").replace(",", "")
            unit_promo_price = float(price_token)

            sku_demand_factor = blended_scale
            stock_boost = 0

            # Apply INTV-04: Micro-Elasticity Margin Circuit Breaker on SKU-9901
            if intv_04_active and sku_id == "SKU-9901":
                unit_promo_price = 699.99
                s_copy["promo_price"] = "$699.99 (-22% Circuit Breaker)"
                s_copy["promo_margin_pct"] = "26.2% (+4.8% Margin Protected)"
                s_copy["elasticity_coefficient"] = 2.25
                sku_demand_factor *= 0.76  # 24% demand velocity moderation

            # Apply INTV-02: Expedited Tier-1 Supplier Pre-PO Dispatch
            if intv_02_active:
                if sku_id == "SKU-9901":
                    stock_boost += 1200
                elif sku_id == "SKU-6612":
                    stock_boost += 800

            projected_demand = int(round(s_copy["projected_unit_demand"] * sku_demand_factor))
            available_stock = int(s_copy["total_available_stock"]) + stock_boost
            projected_rev_num = round(projected_demand * unit_promo_price, 2)

            s_copy["projected_unit_demand"] = projected_demand
            s_copy["total_available_stock"] = available_stock
            s_copy["projected_revenue"] = f"${projected_rev_num:,.0f}"

            # Compute depletion day & severity dynamically
            if abs(sku_demand_factor - 1.0) < 1e-3 and stock_boost == 0:
                pass  # Preserve exact baseline formatting
            else:
                daily_velocity = projected_demand / float(duration_days)
                days_cover = available_stock / max(1.0, daily_velocity)
                if available_stock >= projected_demand:
                    s_copy["depletion_day"] = f"Day {duration_days} (Buffer OK)"
                    s_copy["stockout_severity"] = "HEALTHY"
                elif days_cover <= 2.2:
                    dep_day = max(1, int(days_cover) + 1)
                    s_copy["depletion_day"] = f"Day {dep_day}"
                    s_copy["stockout_severity"] = "CRITICAL"
                else:
                    dep_day = max(2, min(duration_days, int(days_cover) + 1))
                    s_copy["depletion_day"] = f"Day {dep_day}"
                    s_copy["stockout_severity"] = "MODERATE"

            skus.append(s_copy)

        return skus

    def analyze(
        self,
        promo_parameters: Dict[str, Any],
        session_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Simulates SKU demand elasticity, unit margins, and inventory depletion timeline,
        reading `store_findings` from `session_state` and publishing `sku_findings`.
        """
        upstream_store_findings = (
            session_state.get("store_findings", {}) if session_state is not None else {}
        )
        applied_interventions: List[str] = list(
            promo_parameters.get("applied_interventions")
            or (session_state.get("applied_interventions", []) if session_state else [])
        )

        skus = self.run_merchandising_elasticity_model(
            promo_parameters, upstream_store_findings, applied_interventions
        )

        critical_skus = 0
        total_promo_revenue = 0.0
        total_units_demanded = 0
        total_units_available = 0
        sku_deficits_by_id: Dict[str, Dict[str, Any]] = {}
        per_sku_deficit_sum = 0

        for s_copy in skus:
            demanded = int(s_copy["projected_unit_demand"])
            available = int(s_copy["total_available_stock"])
            total_units_demanded += demanded
            total_units_available += available

            rev_numeric = float(str(s_copy["projected_revenue"]).replace("$", "").replace(",", ""))
            total_promo_revenue += rev_numeric

            sku_deficit = max(0, demanded - available)
            per_sku_deficit_sum += sku_deficit

            if s_copy["stockout_severity"] == "CRITICAL":
                critical_skus += 1

            # Extract numeric depletion day for downstream SupplierCapacityAgent
            dep_str = str(s_copy["depletion_day"])
            dep_day_num = 4
            for token in dep_str.replace("(", " ").split():
                if token.isdigit():
                    dep_day_num = int(token)
                    break

            sku_deficits_by_id[s_copy["sku_id"]] = {
                "sku_id": s_copy["sku_id"],
                "product_name": s_copy["name"],
                "demanded_units": demanded,
                "available_units": available,
                "deficit_units": sku_deficit,
                "depletion_day": dep_str,
                "depletion_day_num": dep_day_num,
                "severity": s_copy["stockout_severity"],
            }

        deficit_units = max(0, total_units_demanded - total_units_available)
        avg_gmroi = sum(float(s["gmroi"]) for s in skus) / len(skus)
        upstream_store_units = upstream_store_findings.get(
            "total_projected_store_units", int(round(total_units_demanded * 0.77))
        )

        vulnerabilities: List[str] = []
        for s_copy in skus:
            info = sku_deficits_by_id[s_copy["sku_id"]]
            if info["deficit_units"] > 0:
                vulnerabilities.append(
                    f"{s_copy['sku_id']} ({s_copy['name']}): Elasticity {s_copy['elasticity_coefficient']} "
                    f"drives {info['demanded_units']:,} unit demand vs {info['available_units']:,} stock "
                    f"({info['deficit_units']:,} unit shortage by {info['depletion_day']})."
                )
        if not vulnerabilities:
            vulnerabilities.append("All promotional SKUs have sufficient national stock and active circuit breakers.")

        findings = {
            "agent": self.name,
            "status": "COMPLETED",
            "summary": (
                f"Evaluated {len(skus)} featured promotional SKUs coupled with {upstream_store_units:,} store-channel units. "
                f"Total projected demand of {total_units_demanded:,} units against {total_units_available:,} available stock "
                f"(net deficit of {deficit_units:,} units; {per_sku_deficit_sum:,} SKU-level shortage units). "
                f"{critical_skus} hero SKU(s) face critical stockout exposure."
            ),
            "metrics": {
                "skus_evaluated": len(skus),
                "critical_stockout_skus": critical_skus,
                "projected_promo_revenue": f"${total_promo_revenue:,.2f}",
                "national_unit_deficit": f"-{deficit_units:,} units",
                "sku_level_shortage_units": f"-{per_sku_deficit_sum:,} units",
                "average_gmroi": f"{avg_gmroi:.2f}x",
            },
            "sku_matrix": skus,
            "key_vulnerabilities": vulnerabilities[:3],
        }

        if session_state is not None:
            session_state["sku_findings"] = {
                "upstream_store_units": upstream_store_units,
                "total_units_demanded": total_units_demanded,
                "total_units_available": total_units_available,
                "deficit_units_num": deficit_units,
                "net_unmitigated_deficit": per_sku_deficit_sum,
                "total_promo_revenue_num": total_promo_revenue,
                "critical_stockout_skus": critical_skus,
                "average_gmroi_num": round(avg_gmroi, 2),
                "sku_deficits_by_id": sku_deficits_by_id,
                "sku_matrix": skus,
            }

        return findings
