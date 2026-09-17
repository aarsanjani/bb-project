"""
Store Demand & Regional Foot-Traffic Simulation Specialist Agent.
Analyzes store-by-store foot traffic surges, localized sell-through velocity, and stockout probabilities.
Participates in the Hub-and-Spoke multi-agent mesh by publishing `store_findings` to shared `session_state`.
"""
from typing import Dict, Any, List, Optional
from backend.simulation.data_models import STORES_DATA


class StoreDemandAgent:
    def __init__(self):
        self.name = "store_demand_agent"
        self.role = "Regional Store Demand & Traffic Specialist"
        self.disallow_transfer_to_parent = True
        self.disallow_transfer_to_peers = True

    def before_agent_callback(self, callback_context: Any = None) -> None:
        """ADK-compliant lifecycle hook before agent execution."""
        return None

    def after_agent_callback(self, callback_context: Any = None) -> None:
        """ADK-compliant lifecycle hook after agent execution."""
        return None

    def run_store_network_demand_model(
        self,
        promo_parameters: Dict[str, Any],
        applied_interventions: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Executes dynamic regional foot-traffic and store-level inventory depletion simulation.
        """
        forecast_multiplier = float(promo_parameters.get("forecast_multiplier", 2.7))
        duration_days = max(1, int(promo_parameters.get("duration_days", 4)))
        scale_factor = forecast_multiplier / 2.7

        intv_01_active = "INTV-01" in applied_interventions
        intv_03_active = "INTV-03" in applied_interventions

        stores: List[Dict[str, Any]] = []
        for store in STORES_DATA:
            s_copy = dict(store)
            store_id = s_copy["store_id"]

            # Parse baseline surge percentage
            base_surge_num = int(
                str(s_copy["foot_traffic_surge"]).replace("+", "").replace("%", "").strip()
            )
            scaled_surge_num = max(15, int(round(base_surge_num * scale_factor)))
            s_copy["foot_traffic_surge"] = f"+{scaled_surge_num}%"

            # Calculate demand relief from active omnichannel interventions
            demand_relief = 1.0
            on_hand_boost = 0
            if intv_01_active and store_id in ("STR-101", "STR-112"):
                on_hand_boost += 200  # Pre-allocated reserve units from INTV-01
                demand_relief *= 0.90  # BOPIS intake capped at 90%
            if intv_03_active and store_id in ("STR-101", "STR-108", "STR-112", "STR-125"):
                demand_relief *= 0.88  # SFS rerouted to Central DC when cover < 3 days

            projected_demand = int(round(s_copy["projected_promo_demand"] * scale_factor * demand_relief))
            current_on_hand = int(s_copy["current_on_hand"]) + on_hand_boost

            s_copy["projected_promo_demand"] = projected_demand
            s_copy["current_on_hand"] = current_on_hand

            # Compute stockout probability & breach timeline dynamically
            if abs(scale_factor - 1.0) < 1e-3 and not intv_01_active and not intv_03_active:
                risk_pct = float(s_copy["stockout_risk_pct"])
            else:
                coverage_ratio = current_on_hand / max(1.0, float(projected_demand))
                raw_risk = max(3.0, min(98.5, (1.18 - coverage_ratio) * 125.0))
                risk_pct = round(raw_risk, 1)

            s_copy["stockout_risk_pct"] = risk_pct

            # Classify risk status & breach day
            daily_burn = projected_demand / float(duration_days)
            days_until_stockout = current_on_hand / max(1.0, daily_burn)

            if risk_pct >= 75.0:
                s_copy["risk_status"] = "CRITICAL_STOCKOUT"
                breach_day_num = max(1, min(duration_days, int(days_until_stockout) + 1))
                s_copy["stockout_day"] = f"Day {breach_day_num} (14:00)"
            elif risk_pct >= 65.0:
                s_copy["risk_status"] = "HIGH_RISK"
                breach_day_num = max(2, min(duration_days, int(days_until_stockout) + 1))
                s_copy["stockout_day"] = f"Day {breach_day_num} (18:00)"
            elif risk_pct >= 50.0:
                s_copy["risk_status"] = "ELEVATED_RISK"
                breach_day_num = max(2, min(duration_days, int(days_until_stockout) + 1))
                s_copy["stockout_day"] = f"Day {breach_day_num} (16:00)"
            else:
                s_copy["risk_status"] = "OPTIMAL"
                s_copy["stockout_day"] = "None (Healthy)"
                if intv_01_active or intv_03_active:
                    s_copy["bottleneck"] = "Mitigated via Omnichannel Guardrail"

            # Scale projected store revenue proportionally
            base_rev = float(str(store["projected_revenue"]).replace("$", "").replace(",", ""))
            demand_ratio = projected_demand / max(1.0, float(store["projected_promo_demand"]))
            s_copy["projected_revenue"] = f"${int(round(base_rev * demand_ratio)):,}"

            stores.append(s_copy)

        return stores

    def analyze(
        self,
        promo_parameters: Dict[str, Any],
        session_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Simulates foot traffic, demand surge, and store-level stockout hazards,
        publishing `store_findings` into `session_state` for downstream agents.
        """
        applied_interventions: List[str] = list(
            promo_parameters.get("applied_interventions")
            or (session_state.get("applied_interventions", []) if session_state else [])
        )

        stores = self.run_store_network_demand_model(promo_parameters, applied_interventions)

        critical_count = 0
        high_risk_count = 0
        total_projected_demand = 0
        total_on_hand = 0
        critical_store_ids: List[str] = []

        for s_copy in stores:
            total_projected_demand += s_copy["projected_promo_demand"]
            total_on_hand += s_copy["current_on_hand"]
            if s_copy["risk_status"] == "CRITICAL_STOCKOUT":
                critical_count += 1
                critical_store_ids.append(s_copy["store_id"])
            elif s_copy["risk_status"] in ("HIGH_RISK", "ELEVATED_RISK"):
                high_risk_count += 1
                critical_store_ids.append(s_copy["store_id"])

        national_stockout_risk_avg = sum(s["stockout_risk_pct"] for s in stores) / len(stores)
        peak_store = max(stores, key=lambda x: x["stockout_risk_pct"])
        demand_uplift_ratio = total_projected_demand / 15900.0

        vulnerabilities: List[str] = []
        for s in stores:
            if s["risk_status"] in ("CRITICAL_STOCKOUT", "HIGH_RISK", "ELEVATED_RISK"):
                vulnerabilities.append(
                    f"{s['name']} ({s['store_id']}) at {s['stockout_risk_pct']}% stockout risk "
                    f"({s['stockout_day']}) due to {s['foot_traffic_surge']} traffic — {s['bottleneck']}."
                )
        if not vulnerabilities:
            vulnerabilities.append("All regional store clusters operating within safe inventory buffer thresholds.")

        findings = {
            "agent": self.name,
            "status": "COMPLETED",
            "summary": (
                f"Simulated {len(stores)} regional store clusters. Identified {critical_count} critical stockout location(s) "
                f"(peak: {peak_store['name']} at {peak_store['stockout_risk_pct']}% risk, {peak_store['stockout_day']}) "
                f"and {high_risk_count} elevated risk stores. "
                f"Total store demand will reach {total_projected_demand:,} units against {total_on_hand:,} on-hand stock."
            ),
            "metrics": {
                "total_stores_simulated": len(stores),
                "critical_stockout_stores": critical_count,
                "high_risk_stores": high_risk_count,
                "average_national_stockout_risk": f"{national_stockout_risk_avg:.1f}%",
                "peak_store_risk_pct": peak_store["stockout_risk_pct"],
                "peak_store_name": peak_store["name"],
                "peak_store_breach_day": peak_store["stockout_day"],
                "total_projected_store_units": total_projected_demand,
                "total_store_inventory_on_hand": total_on_hand,
            },
            "store_matrix": stores,
            "key_vulnerabilities": vulnerabilities[:3],
        }

        if session_state is not None:
            session_state["store_findings"] = {
                "total_projected_store_units": total_projected_demand,
                "total_store_inventory_on_hand": total_on_hand,
                "demand_uplift_ratio": demand_uplift_ratio,
                "critical_stockout_stores": critical_count,
                "high_risk_stores": high_risk_count,
                "average_national_stockout_risk_num": round(national_stockout_risk_avg, 1),
                "peak_store_risk_pct": peak_store["stockout_risk_pct"],
                "peak_store_name": peak_store["name"],
                "peak_store_breach_day": peak_store["stockout_day"],
                "critical_store_ids": critical_store_ids,
                "store_matrix": stores,
            }

        return findings
