"""
Lead Promotion Orchestrator: Multi-Scale Fractal Chain of Thought (FCoT) Synthesis
Coordinates specialized domain agents (store, sku, supplier, fulfillment) via a shared session_state
blackboard, enforces Hub-and-Spoke sequential state transitions, and constructs dynamic A2UI schemas.
"""
import os
import re
import json
import logging
from typing import Generator, Dict, Any, List, Optional
from backend.agents.store_agent import StoreDemandAgent
from backend.agents.sku_agent import SkuInventoryAgent
from backend.agents.supplier_agent import SupplierCapacityAgent
from backend.agents.fulfillment_agent import FulfillmentLogisticsAgent
from backend.simulation.data_models import INTERVENTIONS_DATA

logger = logging.getLogger(__name__)


def _init_vertex_genai_client() -> Any:
    """
    Initializes the unified Google Gen AI SDK client on Vertex AI per GEMINI.md guidelines
    when available in the environment.
    """
    if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() != "true":
        return None
    try:
        from google import genai  # type: ignore
        return genai.Client(
            enterprise=True,
            project=os.environ.get("GOOGLE_CLOUD_PROJECT", "arsanjani-genai"),
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )
    except Exception as exc:
        logger.debug(f"Vertex AI genai.Client initialization skipped/fallback: {exc}")
        return None


class PromotionOrchestratorEngine:
    """
    Lead Promotion Simulation Synthesizer Orchestrator.
    Executes sequential hub-and-spoke multi-agent analysis over a shared session_state
    where each specialist agent's output constrains downstream agents and drives dynamic A2UI synthesis.
    """

    def __init__(
        self,
        session_id: str,
        declarative_intent: str,
        promo_parameters: Optional[Dict[str, Any]] = None
    ):
        self.session_id = session_id
        self.intent = declarative_intent
        self.genai_client = _init_vertex_genai_client()
        self.promo_params = self._disambiguate_intent_parameters(declarative_intent, promo_parameters)

        # Shared multi-agent blackboard state
        self.session_state: Dict[str, Any] = {
            "session_id": self.session_id,
            "declarative_intent": self.intent,
            "promo_parameters": self.promo_params,
            "applied_interventions": list(self.promo_params.get("applied_interventions", [])),
        }

        # Epistemic state tracking for strict sequential isolation
        self.state_tracker: Dict[str, bool] = {
            "store_invoked": False,
            "sku_invoked": False,
            "supplier_invoked": False,
            "fulfillment_invoked": False,
            "synthesis_unlocked": False,
        }

        # Initialize isolated specialist worker mesh
        self.store_agent = StoreDemandAgent()
        self.sku_agent = SkuInventoryAgent()
        self.supplier_agent = SupplierCapacityAgent()
        self.fulfillment_agent = FulfillmentLogisticsAgent()

    def _disambiguate_intent_parameters(
        self,
        intent: str,
        explicit_params: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Disambiguates natural language intent and merges with explicit preset parameters
        so each subagent receives structured simulation boundaries.
        """
        default_params: Dict[str, Any] = {
            "name": "Summer Electronics & Appliance Blast (30-35% Off)",
            "duration_days": 4,
            "target_discount_pct": "28-35%",
            "forecast_multiplier": 2.7,
            "applied_interventions": [],
        }
        if explicit_params:
            merged = dict(default_params)
            merged.update(explicit_params)
            return merged

        lower_intent = (intent or "").lower()
        if "48-hour" in lower_intent or "flash" in lower_intent or "40%" in lower_intent:
            return {
                "name": "Flash 48-Hour Omni-Deals (40% Off Storewide)",
                "duration_days": 2,
                "target_discount_pct": "40%",
                "forecast_multiplier": 3.8,
                "applied_interventions": [],
            }
        if "multi-week" in lower_intent or "home essentials" in lower_intent or "25%" in lower_intent:
            return {
                "name": "Fall Home Essentials & Lifestyle Upgrade (25% Off)",
                "duration_days": 7,
                "target_discount_pct": "25%",
                "forecast_multiplier": 1.8,
                "applied_interventions": [],
            }

        # Parse custom percentage discount or day duration from arbitrary natural language prompt
        pct_match = re.search(r"(\d{1,2})\s*%", lower_intent)
        if pct_match:
            pct_val = int(pct_match.group(1))
            mult = round(max(1.2, min(4.5, 1.0 + (pct_val / 18.0))), 2)
            default_params["target_discount_pct"] = f"{pct_val}%"
            default_params["forecast_multiplier"] = mult
            default_params["name"] = f"Custom Promotion Scenario ({pct_val}% Off)"

        return default_params

    def _run_agent_turn(self, agent: Any) -> Dict[str, Any]:
        """
        Executes a single subagent turn with ADK-compliant lifecycle callbacks
        and shared session_state propagation.
        """
        ctx = {"agent_name": agent.name, "session_id": self.session_id, "state": self.session_state}
        agent.before_agent_callback(callback_context=ctx)
        results = agent.analyze(self.promo_params, session_state=self.session_state)
        agent.after_agent_callback(callback_context=ctx)
        return results

    def execute_workflow(self) -> Generator[str, None, None]:
        """
        Executes the sequential Hub-and-Spoke multi-agent orchestration loop over shared session_state
        and streams standardized JSON-RPC 2.0 frames.
        """
        logger.info(f"Session {self.session_id}: Starting Promotion Multi-Scale Simulation.")

        # Step 1: Pre-Execution Scope Declaration & Intent Disambiguation
        yield self._encode_rpc_frame("onAgentThought", {
            "author": "LeadPromotionOrchestrator",
            "message": (
                f"Decomposing promotion pre-flight analysis for '{self.promo_params.get('name')}' "
                f"(Discount: {self.promo_params.get('target_discount_pct')}, "
                f"Duration: {self.promo_params.get('duration_days')}d, "
                f"Demand Multiplier: {self.promo_params.get('forecast_multiplier')}x). "
                f"Initiating state-coupled 4-pillar recursive descent."
            )
        })

        # Step 2: Turn 1 — Store Demand Simulation (Writes session_state['store_findings'])
        if not self.state_tracker["store_invoked"]:
            yield self._encode_rpc_frame("onAgentDelegation", {
                "author": "LeadPromotionOrchestrator",
                "target": self.store_agent.name,
                "message": "Turn 1: Dispatching regional store foot-traffic and shelf depletion model."
            })
            yield self._encode_rpc_frame("onToolCall", {
                "author": self.store_agent.name,
                "tool": "run_store_network_demand_model",
                "arguments": {
                    "promo_campaign": self.promo_params.get("name"),
                    "forecast_multiplier": self.promo_params.get("forecast_multiplier"),
                    "duration_days": self.promo_params.get("duration_days"),
                    "active_guardrails": self.session_state["applied_interventions"],
                }
            })
            store_results = self._run_agent_turn(self.store_agent)
            self.state_tracker["store_invoked"] = True
            yield self._encode_rpc_frame("onAgentThought", {
                "author": self.store_agent.name,
                "message": store_results["summary"]
            })

        # Step 3: Turn 2 — SKU & Unit Economics Simulation (Consumes store_findings -> Writes sku_findings)
        if self.state_tracker["store_invoked"] and not self.state_tracker["sku_invoked"]:
            store_state = self.session_state["store_findings"]
            yield self._encode_rpc_frame("onAgentDelegation", {
                "author": "LeadPromotionOrchestrator",
                "target": self.sku_agent.name,
                "message": (
                    f"Turn 2: Passing {store_state['total_projected_store_units']:,} projected store units "
                    f"({store_state['demand_uplift_ratio']:.2f}x uplift) to SKU Elasticity & GMROI model."
                )
            })
            yield self._encode_rpc_frame("onToolCall", {
                "author": self.sku_agent.name,
                "tool": "run_merchandising_elasticity_model",
                "arguments": {
                    "discount_tier": self.promo_params.get("target_discount_pct"),
                    "upstream_store_units": store_state["total_projected_store_units"],
                    "store_demand_uplift_ratio": round(store_state["demand_uplift_ratio"], 2),
                }
            })
            sku_results = self._run_agent_turn(self.sku_agent)
            self.state_tracker["sku_invoked"] = True
            yield self._encode_rpc_frame("onAgentThought", {
                "author": self.sku_agent.name,
                "message": sku_results["summary"]
            })

        # Step 4: Turn 3 — Supplier Capacity Audit (Consumes sku_findings -> Writes supplier_findings)
        if self.state_tracker["sku_invoked"] and not self.state_tracker["supplier_invoked"]:
            sku_state = self.session_state["sku_findings"]
            shortage_map = {
                k: v["deficit_units"]
                for k, v in sku_state["sku_deficits_by_id"].items()
                if v["deficit_units"] > 0
            }
            yield self._encode_rpc_frame("onAgentDelegation", {
                "author": "LeadPromotionOrchestrator",
                "target": self.supplier_agent.name,
                "message": (
                    f"Turn 3: Passing SKU shortages ({shortage_map or 'None'}) to Tier-1 Supplier "
                    f"Capacity & Air-Freight Lead-Time Audit."
                )
            })
            yield self._encode_rpc_frame("onToolCall", {
                "author": self.supplier_agent.name,
                "tool": "run_supplier_network_capacity_audit",
                "arguments": {
                    "upstream_sku_shortages": shortage_map,
                    "national_deficit_units": sku_state["deficit_units_num"],
                }
            })
            supplier_results = self._run_agent_turn(self.supplier_agent)
            self.state_tracker["supplier_invoked"] = True
            yield self._encode_rpc_frame("onAgentThought", {
                "author": self.supplier_agent.name,
                "message": supplier_results["summary"]
            })

        # Step 5: Turn 4 — Fulfillment & Logistics Stress-Test (Consumes store_findings + sku_findings)
        if self.state_tracker["supplier_invoked"] and not self.state_tracker["fulfillment_invoked"]:
            store_state = self.session_state["store_findings"]
            sku_state = self.session_state["sku_findings"]
            yield self._encode_rpc_frame("onAgentDelegation", {
                "author": "LeadPromotionOrchestrator",
                "target": self.fulfillment_agent.name,
                "message": (
                    f"Turn 4: Stress-testing BOPIS, SFS, Central DC, and POS channels for "
                    f"{sku_state['total_units_demanded']:,} total SKU units and "
                    f"{len(store_state['critical_store_ids'])} high-risk stores."
                )
            })
            yield self._encode_rpc_frame("onToolCall", {
                "author": self.fulfillment_agent.name,
                "tool": "run_omnichannel_fulfillment_stress_test",
                "arguments": {
                    "upstream_sku_units_demanded": sku_state["total_units_demanded"],
                    "congested_stores": store_state["critical_store_ids"],
                }
            })
            fulfillment_results = self._run_agent_turn(self.fulfillment_agent)
            self.state_tracker["fulfillment_invoked"] = True
            yield self._encode_rpc_frame("onAgentThought", {
                "author": self.fulfillment_agent.name,
                "message": fulfillment_results["summary"]
            })

        # Step 6: Verify all 4 pillars completed before unlocking Step E Multi-Scale Synthesis
        all_pillars_complete = all(
            self.state_tracker[k]
            for k in ("store_invoked", "sku_invoked", "supplier_invoked", "fulfillment_invoked")
        )
        if all_pillars_complete:
            self.state_tracker["synthesis_unlocked"] = True

        synthesized_interventions, margin_protected_num, combined_roi = self._synthesize_interventions()
        total_rev_num = self.session_state["sku_findings"]["total_promo_revenue_num"]

        yield self._encode_rpc_frame("onAgentThought", {
            "author": "LeadPromotionOrchestrator",
            "message": (
                f"Step E Multi-Scale Synthesis Unlocked: Reconciled ${total_rev_num:,.0f} projected revenue across "
                f"{self.session_state['store_findings']['total_projected_store_units']:,} store units and "
                f"{self.session_state['fulfillment_findings']['total_omnichannel_orders']:,} omnichannel orders. "
                f"Synthesized {len(synthesized_interventions)} prescriptive interventions protecting "
                f"${margin_protected_num:,.0f} in gross margin ({combined_roi:.1f}x ROI)."
            )
        })

        # Step 7: Emit Schema-Driven A2UI Delivery Frame
        a2ui_payload = self._build_a2ui_schema(
            store_results,
            sku_results,
            supplier_results,
            fulfillment_results,
            synthesized_interventions,
            margin_protected_num,
            combined_roi,
        )
        yield self._encode_rpc_frame("onUiComponentDelivery", {
            "author": "LeadPromotionOrchestrator",
            "ui_specification": "2.0",
            "payload": a2ui_payload
        })

        # Step 8: Final Simulation Complete
        decision_state = (
            "GUARDRAILS_ACTIVE_READY_FOR_LAUNCH"
            if len(self.session_state["applied_interventions"]) >= 2
            else "ACTION_REQUIRED_BEFORE_LAUNCH"
        )
        yield self._encode_rpc_frame("onSimulationComplete", {
            "author": "LeadPromotionOrchestrator",
            "status": "SUCCESS",
            "session_id": self.session_id,
            "executive_decision": decision_state,
            "interventions_count": len(synthesized_interventions),
            "projected_revenue_impact": f"${total_rev_num:,.0f}",
            "margin_protected": f"${margin_protected_num:,.0f}",
        })

    def _synthesize_interventions(self) -> tuple[List[Dict[str, Any]], int, float]:
        """
        Cross-correlates findings from all 4 specialist agents in `self.session_state`
        to dynamically parameterize prescriptive interventions, costs, and ROI.
        """
        store_f = self.session_state["store_findings"]
        sku_f = self.session_state["sku_findings"]
        sup_f = self.session_state["supplier_findings"]
        ful_f = self.session_state["fulfillment_findings"]
        applied = set(self.session_state.get("applied_interventions", []))

        # Quantify cross-domain exposures from actual subagent state
        bopis_mitigated_loss = int(round(max(120000, store_f["peak_store_risk_pct"] * 3400)))
        sku_shortage_revenue_at_risk = int(
            round(max(350000, sku_f["net_unmitigated_deficit"] * 455))
        )
        po_cost = int(round(max(24000, sup_f["total_expedited_surcharge_num"])))
        intv_02_roi = round(sku_shortage_revenue_at_risk / max(1, po_cost), 1)

        margin_protected_num = bopis_mitigated_loss + sku_shortage_revenue_at_risk + 60000
        total_impl_cost = 8200 + po_cost + 3500
        combined_roi = round(margin_protected_num / max(1, total_impl_cost), 1)

        dynamic_interventions: List[Dict[str, Any]] = []
        for base_inv in INTERVENTIONS_DATA:
            inv = dict(base_inv)
            inv_id = inv["intervention_id"]

            if inv_id == "INTV-01":
                inv["action_description"] = (
                    f"Cap BOPIS order intake at 90% store capacity (currently {ful_f['bopis_utilization_num']:.0f}% load) "
                    f"and dynamically reroute excess online demand to Central DC DTC ({ful_f['dc_headroom_pct']:.1f}% headroom). "
                    f"Pre-allocate 400 reserve units to high-risk stores ({', '.join(store_f['critical_store_ids'][:2]) or 'STR-101'})."
                )
                inv["risk_mitigation"] = (
                    f"Protects ${bopis_mitigated_loss:,} in at-risk store sales; reduces BOPIS SLA breach "
                    f"from {ful_f['bopis_peak_sla_breach_rate']} to < 4.5%."
                )
            elif inv_id == "INTV-02":
                inv["action_description"] = (
                    f"Authorize expedited air-freight Purchase Orders for {sup_f['required_emergency_surge_units']:,} surge units "
                    f"across constrained Tier-1 suppliers (SUP-801 & SUP-619) to cover the {sku_f['net_unmitigated_deficit']:,}-unit SKU deficit."
                )
                inv["risk_mitigation"] = (
                    f"Prevents mid-promo stockouts across {sku_f['critical_stockout_skus']} hero SKU(s); "
                    f"protects ${sku_shortage_revenue_at_risk:,} in back-half promo revenue."
                )
                inv["implementation_cost"] = f"${po_cost:,} (Emergency air-freight surcharges)"
                inv["net_roi"] = f"{intv_02_roi:.1f}x ROI"
            elif inv_id == "INTV-03":
                inv["action_description"] = (
                    f"Automatically disable Ship-from-Store orders ({ful_f['sfs_utilization_num']:.0f}% load) in "
                    f"{len(store_f['critical_store_ids'])} constrained store(s) when on-hand falls below 3 days of walk-in demand."
                )

            if inv_id in applied:
                inv["status"] = "ACTIVE_GUARDRAIL_ENGAGED"

            dynamic_interventions.append(inv)

        return dynamic_interventions, margin_protected_num, combined_roi

    def _build_a2ui_schema(
        self,
        store_res: Dict[str, Any],
        sku_res: Dict[str, Any],
        supplier_res: Dict[str, Any],
        fulfillment_res: Dict[str, Any],
        synthesized_interventions: List[Dict[str, Any]],
        margin_protected_num: int,
        combined_roi: float,
    ) -> Dict[str, Any]:
        """
        Constructs a dynamic, schema-compliant A2UI payload synthesized from all 4 subagent findings.
        """
        store_f = self.session_state["store_findings"]
        sku_f = self.session_state["sku_findings"]
        sup_f = self.session_state["supplier_findings"]
        ful_f = self.session_state["fulfillment_findings"]

        rev_millions = sku_f["total_promo_revenue_num"] / 1_000_000.0
        uplift_pct = int(round((store_f["demand_uplift_ratio"] * 2.7 - 1.0) * 100))

        return {
            "type": "Dashboard",
            "id": "promotion_preflight_simulator",
            "title": "Promotion Pre-Flight Impact Simulation & Prescriptive Interventions",
            "subtitle": (
                f"Cross-Domain Diagnostic for '{self.promo_params.get('name')}' "
                f"({self.promo_params.get('target_discount_pct')} Discount | {self.promo_params.get('duration_days')} Days)"
            ),
            "components": [
                {
                    "type": "MetricGrid",
                    "id": "executive_kpi_grid",
                    "title": "Executive KPI Telemetry (Live Multi-Agent Synthesis)",
                    "metrics": [
                        {
                            "label": "Projected Promo Revenue",
                            "value": f"${rev_millions:.2f}M",
                            "trend": f"+{uplift_pct}% vs Baseline",
                            "status": "positive"
                        },
                        {
                            "label": "Store Stockout Risk",
                            "value": f"{store_f['peak_store_risk_pct']}% Peak",
                            "subtext": f"{store_f['peak_store_name']} ({store_f['peak_store_breach_day']})",
                            "status": "critical" if store_f["peak_store_risk_pct"] >= 70 else "warning"
                        },
                        {
                            "label": "Hero SKU Unit Deficit",
                            "value": f"-{sku_f['net_unmitigated_deficit']:,} units",
                            "subtext": f"{sku_f['critical_stockout_skus']} Critical SKU(s) Exposed",
                            "status": "critical" if sku_f["net_unmitigated_deficit"] > 1000 else "positive"
                        },
                        {
                            "label": "BOPIS Channel Load",
                            "value": f"{ful_f['bopis_utilization_num']:.0f}% Labor Cap",
                            "subtext": f"{ful_f['bopis_peak_sla_breach_rate']} SLA Breach Risk",
                            "status": "warning" if ful_f["bopis_utilization_num"] > 95 else "positive"
                        },
                        {
                            "label": "Interventions ROI",
                            "value": f"{combined_roi:.1f}x",
                            "subtext": f"Protects ${margin_protected_num / 1_000_000:.2f}M Margin",
                            "status": "positive"
                        }
                    ]
                },
                {
                    "type": "Tabs",
                    "id": "simulation_dimension_tabs",
                    "components": [
                        # Tab 1: Executive Overview & Synthesis
                        {
                            "id": "tab_executive_summary",
                            "title": "Executive Synthesis",
                            "type": "TabContent",
                            "components": [
                                {
                                    "type": "AlertBanner",
                                    "severity": "critical" if store_f["critical_stockout_stores"] > 0 else "info",
                                    "title": (
                                        f"Pre-Launch Cross-Agent Diagnostic: {store_f['critical_stockout_stores']} Critical Store(s) "
                                        f"& {sku_f['net_unmitigated_deficit']:,} Unit SKU Shortage"
                                    ),
                                    "message": (
                                        f"Cross-domain synthesis across {store_f['total_projected_store_units']:,} store units and "
                                        f"{ful_f['total_omnichannel_orders']:,} omnichannel orders indicates "
                                        f"${margin_protected_num:,} in revenue/margin exposure unless prescriptive guardrails are engaged."
                                    )
                                },
                                {
                                    "type": "Card",
                                    "title": "Lead Orchestrator Multi-Scale Diagnostic (State-Coupled FCoT)",
                                    "badge": "FCoT Hillclimbing Complete",
                                    "content": (
                                        f"### 1. Macro Analysis (Demand & Revenue)\n"
                                        f"The `{self.promo_params.get('target_discount_pct')}` promotional structure drives a "
                                        f"**{self.promo_params.get('forecast_multiplier')}x** demand multiplier, projecting "
                                        f"**${sku_f['total_promo_revenue_num']:,.0f}** in gross revenue across **{sku_f['total_units_demanded']:,}** total units "
                                        f"(blended GMROI of **{sku_f['average_gmroi_num']}x**).\n\n"
                                        f"### 2. Meso Analysis (Regional & Channel Bottlenecks)\n"
                                        f"- **Store Network (`store_demand_agent`)**: {store_res['summary']}\n"
                                        f"- **Omnichannel Fulfillment (`fulfillment_logistics_agent`)**: {fulfillment_res['summary']}\n\n"
                                        f"### 3. Micro Analysis (Line-Item Exposures)\n"
                                        f"- **SKU Deficits (`sku_inventory_agent`)**: {sku_res['summary']}\n"
                                        f"- **Tier-1 Suppliers (`supplier_capacity_agent`)**: {supplier_res['summary']}"
                                    )
                                }
                            ]
                        },
                        # Tab 2: Store Impact Matrix
                        {
                            "id": "tab_stores",
                            "title": f"Stores Matrix ({len(store_res['store_matrix'])})",
                            "type": "TabContent",
                            "components": [
                                {
                                    "type": "Table",
                                    "id": "stores_simulation_table",
                                    "title": "Store-by-Store Traffic, Demand & Stockout Probability",
                                    "headers": ["Store ID", "Location", "Region", "Traffic Surge", "Projected Demand", "On-Hand Stock", "Stockout Risk", "Breach Day", "Risk Status"],
                                    "rows": [
                                        [
                                            s["store_id"],
                                            s["name"],
                                            s["region"],
                                            s["foot_traffic_surge"],
                                            f"{s['projected_promo_demand']:,} units",
                                            f"{s['current_on_hand']:,} units",
                                            f"{s['stockout_risk_pct']}%",
                                            s["stockout_day"],
                                            s["risk_status"]
                                        ]
                                        for s in store_res["store_matrix"]
                                    ]
                                }
                            ]
                        },
                        # Tab 3: SKU & Merchandising Matrix
                        {
                            "id": "tab_skus",
                            "title": f"SKU & Unit Economics ({len(sku_res['sku_matrix'])})",
                            "type": "TabContent",
                            "components": [
                                {
                                    "type": "Table",
                                    "id": "skus_simulation_table",
                                    "title": "SKU Promotional Elasticity, Inventory Depletion & Margin Breakdown",
                                    "headers": ["SKU ID", "Product Name", "Category", "Promo Price", "Elasticity", "Demand Forecast", "National Stock", "Depletion Day", "GMROI", "Severity"],
                                    "rows": [
                                        [
                                            k["sku_id"],
                                            k["name"],
                                            k["category"],
                                            k["promo_price"],
                                            str(k["elasticity_coefficient"]),
                                            f"{k['projected_unit_demand']:,}",
                                            f"{k['total_available_stock']:,}",
                                            k["depletion_day"],
                                            f"{k['gmroi']}x",
                                            k["stockout_severity"]
                                        ]
                                        for k in sku_res["sku_matrix"]
                                    ]
                                }
                            ]
                        },
                        # Tab 4: Supplier & Vendor Matrix
                        {
                            "id": "tab_suppliers",
                            "title": f"Supplier Capacity ({len(supplier_res['supplier_matrix'])})",
                            "type": "TabContent",
                            "components": [
                                {
                                    "type": "Table",
                                    "id": "suppliers_simulation_table",
                                    "title": "Tier-1 Vendor Lead Times, OTIF Reliability & Restock Readiness",
                                    "headers": ["Supplier ID", "Vendor Name", "Key Component", "Std Lead Time", "Expedited Lead Time", "Capacity Load", "OTIF %", "Max Surge", "Status"],
                                    "rows": [
                                        [
                                            sup["supplier_id"],
                                            sup["name"],
                                            sup["key_component"],
                                            f"{sup['standard_lead_time_days']} days",
                                            f"{sup['expedited_lead_time_days']} days",
                                            sup["factory_capacity_utilization"],
                                            sup["otif_score"],
                                            f"{sup['max_surge_units']:,} units",
                                            sup["status"]
                                        ]
                                        for sup in supplier_res["supplier_matrix"]
                                    ]
                                }
                            ]
                        },
                        # Tab 5: Fulfillment Channels
                        {
                            "id": "tab_fulfillment",
                            "title": f"Fulfillment Channels ({len(fulfillment_res['channel_matrix'])})",
                            "type": "TabContent",
                            "components": [
                                {
                                    "type": "Table",
                                    "id": "fulfillment_simulation_table",
                                    "title": "Omnichannel Capacity Utilization & SLA Breach Vulnerabilities",
                                    "headers": ["Fulfillment Channel", "Demand Share", "Projected Orders", "Peak Surge", "Labor Capacity", "SLA Breach Rate", "Bottleneck Factor", "Health Status"],
                                    "rows": [
                                        [
                                            ch["channel_name"],
                                            ch["demand_share_pct"],
                                            ch["projected_order_volume"],
                                            ch["peak_hour_surge"],
                                            ch["labor_capacity_utilization"],
                                            ch["projected_sla_breach_rate"],
                                            ch["bottleneck_factor"],
                                            ch["health"]
                                        ]
                                        for ch in fulfillment_res["channel_matrix"]
                                    ]
                                }
                            ]
                        },
                        # Tab 6: Prescriptive Interventions & Circuit Breakers
                        {
                            "id": "tab_interventions",
                            "title": f"Interventions & Actions ({len(synthesized_interventions)})",
                            "type": "TabContent",
                            "components": [
                                {
                                    "type": "InterventionList",
                                    "id": "prescriptive_interventions_list",
                                    "title": "Prescriptive Cross-Domain Interventions & Automated Circuit Breakers",
                                    "items": synthesized_interventions
                                }
                            ]
                        }
                    ]
                }
            ]
        }

    def _encode_rpc_frame(self, method: str, params: Dict[str, Any]) -> str:
        """Standardizes streaming frames into valid JSON-RPC 2.0 payloads."""
        return json.dumps({"jsonrpc": "2.0", "method": method, "params": params})
