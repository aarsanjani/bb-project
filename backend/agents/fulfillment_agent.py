"""
Fulfillment & Logistics Channel Specialist Agent.
Simulates BOPIS, Ship-from-Store, Central DC, and in-store cashier channels, warehouse labor limits, and SLA breaches.
Consumes upstream `store_findings` and `sku_findings` from `session_state` and publishes `fulfillment_findings`.
"""
from typing import Dict, Any, List, Optional
from backend.simulation.data_models import CHANNELS_DATA


class FulfillmentLogisticsAgent:
    def __init__(self):
        self.name = "fulfillment_logistics_agent"
        self.role = "Omnichannel Fulfillment & Logistics Specialist"
        self.disallow_transfer_to_parent = True
        self.disallow_transfer_to_peers = True

    def before_agent_callback(self, callback_context: Any = None) -> None:
        """ADK-compliant lifecycle hook before agent execution."""
        return None

    def after_agent_callback(self, callback_context: Any = None) -> None:
        """ADK-compliant lifecycle hook after agent execution."""
        return None

    def run_omnichannel_fulfillment_stress_test(
        self,
        promo_parameters: Dict[str, Any],
        upstream_store_findings: Dict[str, Any],
        upstream_sku_findings: Dict[str, Any],
        applied_interventions: List[str]
    ) -> tuple[List[Dict[str, Any]], int, float, float, float]:
        """
        Stress-tests omnichannel fulfillment pipelines based on upstream store congestion
        and total SKU order volume, dynamically rerouting volume when INTV-01 or INTV-03 are active.
        """
        forecast_multiplier = float(promo_parameters.get("forecast_multiplier", 2.7))
        scale_factor = forecast_multiplier / 2.7

        # Couple order volume to upstream SKU & Store findings if available
        total_sku_units = int(upstream_sku_findings.get("total_units_demanded", int(round(20600 * scale_factor))))
        order_scale = total_sku_units / 20600.0

        intv_01_active = "INTV-01" in applied_interventions
        intv_03_active = "INTV-03" in applied_interventions

        channels: List[Dict[str, Any]] = []
        total_orders = 0
        bopis_util_num = 112.0
        sfs_util_num = 104.0
        dc_util_num = 88.0

        for ch in CHANNELS_DATA:
            c_copy = dict(ch)
            ch_name = c_copy["channel_name"]

            # Parse baseline order count ("18,400 orders")
            base_orders = int(str(c_copy["projected_order_volume"]).split()[0].replace(",", ""))
            unit_label = str(c_copy["projected_order_volume"]).split()[-1]

            if "BOPIS" in ch_name:
                share_adj = 0.78 if intv_01_active else 1.0
                ch_orders = int(round(base_orders * order_scale * share_adj))
                bopis_util_num = round(112.0 * (order_scale ** 0.65) * (0.78 if intv_01_active else 1.0), 1)
                sla_breach = round(max(1.8, (bopis_util_num - 75.0) * 0.49), 1) if bopis_util_num > 80 else 2.4
                c_copy["demand_share_pct"] = "26.5%" if intv_01_active else "34.0%"
                c_copy["projected_order_volume"] = f"{ch_orders:,} {unit_label}"
                c_copy["labor_capacity_utilization"] = (
                    f"{bopis_util_num:.0f}% (OVER CAPACITY)"
                    if bopis_util_num > 100.0
                    else f"{bopis_util_num:.0f}% (GUARDRAIL CAPPED)"
                )
                c_copy["projected_sla_breach_rate"] = f"{sla_breach:.1f}% (> 2 hr hold delay)"
                c_copy["health"] = (
                    "CRITICAL" if bopis_util_num >= 105.0 else ("HIGH_RISK" if bopis_util_num > 95.0 else "HEALTHY")
                )

            elif "Ship-From-Store" in ch_name:
                share_adj = 0.74 if intv_03_active else 1.0
                ch_orders = int(round(base_orders * order_scale * share_adj))
                sfs_util_num = round(104.0 * (order_scale ** 0.65) * (0.80 if intv_03_active else 1.0), 1)
                sla_breach = round(max(2.1, (sfs_util_num - 72.0) * 0.44), 1)
                c_copy["demand_share_pct"] = "16.5%" if intv_03_active else "22.0%"
                c_copy["projected_order_volume"] = f"{ch_orders:,} {unit_label}"
                c_copy["labor_capacity_utilization"] = (
                    f"{sfs_util_num:.0f}% (OVER CAPACITY)"
                    if sfs_util_num > 100.0
                    else f"{sfs_util_num:.0f}% (REROUTED TO DC)"
                )
                c_copy["projected_sla_breach_rate"] = f"{sla_breach:.1f}% (Carrier cutoff risk)"
                c_copy["health"] = (
                    "CRITICAL" if sfs_util_num >= 108.0 else ("HIGH_RISK" if sfs_util_num > 95.0 else "HEALTHY")
                )

            elif "Central DC" in ch_name:
                reroute_boost = (1.18 if intv_01_active else 1.0) * (1.14 if intv_03_active else 1.0)
                ch_orders = int(round(base_orders * order_scale * reroute_boost))
                dc_util_num = min(98.0, round(88.0 * (order_scale ** 0.45) * (1.06 if (intv_01_active or intv_03_active) else 1.0), 1))
                c_copy["demand_share_pct"] = "43.0%" if (intv_01_active or intv_03_active) else "30.0%"
                c_copy["projected_order_volume"] = f"{ch_orders:,} {unit_label}"
                c_copy["labor_capacity_utilization"] = f"{dc_util_num:.1f}% (WITHIN SAFE THRESHOLD)"
                c_copy["health"] = "HEALTHY" if dc_util_num <= 95.0 else "HIGH_RISK"

            else:
                ch_orders = int(round(base_orders * order_scale))
                pos_util = min(99.0, round(82.0 * (order_scale ** 0.5), 1))
                c_copy["projected_order_volume"] = f"{ch_orders:,} {unit_label}"
                c_copy["labor_capacity_utilization"] = f"{pos_util:.1f}%"
                c_copy["health"] = "STABLE" if pos_util < 92.0 else "HIGH_RISK"

            total_orders += ch_orders
            channels.append(c_copy)

        return channels, total_orders, bopis_util_num, sfs_util_num, dc_util_num

    def analyze(
        self,
        promo_parameters: Dict[str, Any],
        session_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Simulates channel capacity, labor bottlenecking, packaging throughput, and SLA risk,
        consuming `store_findings` and `sku_findings` from `session_state` and writing `fulfillment_findings`.
        """
        upstream_store_findings = (
            session_state.get("store_findings", {}) if session_state is not None else {}
        )
        upstream_sku_findings = (
            session_state.get("sku_findings", {}) if session_state is not None else {}
        )
        applied_interventions: List[str] = list(
            promo_parameters.get("applied_interventions")
            or (session_state.get("applied_interventions", []) if session_state else [])
        )

        channels, total_orders, bopis_util_num, sfs_util_num, dc_util_num = (
            self.run_omnichannel_fulfillment_stress_test(
                promo_parameters, upstream_store_findings, upstream_sku_findings, applied_interventions
            )
        )

        critical_channels = sum(1 for c in channels if c["health"] in ("CRITICAL", "HIGH_RISK"))
        dc_headroom = max(0.0, round(100.0 - dc_util_num, 1))
        bopis_sla_str = channels[0]["projected_sla_breach_rate"].split()[0]

        vulnerabilities: List[str] = []
        if bopis_util_num > 100.0:
            vulnerabilities.append(
                f"BOPIS Locker Bottleneck: {bopis_util_num:.0f}% labor utilization drives {bopis_sla_str} SLA breach rate across urban stores."
            )
        if sfs_util_num > 100.0:
            vulnerabilities.append(
                f"Ship-From-Store Saturation: {sfs_util_num:.0f}% packing station load threatens 4:30 PM carrier ground cutoffs."
            )
        vulnerabilities.append(
            f"Central DC DTC Pipeline: Operating at {dc_util_num:.1f}% utilization ({dc_headroom:.1f}% headroom available to absorb overflow)."
        )

        findings = {
            "agent": self.name,
            "status": "COMPLETED",
            "summary": (
                f"Stress-tested {len(channels)} omnichannel fulfillment pipelines across {total_orders:,} total orders. "
                f"{critical_channels} out of {len(channels)} channels exceed safe labor thresholds: "
                f"BOPIS at {bopis_util_num:.0f}% utilization ({bopis_sla_str} SLA risk) and Ship-from-Store at {sfs_util_num:.0f}%. "
                f"Central DC DTC line at {dc_util_num:.1f}% utilization ({dc_headroom:.1f}% headroom)."
            ),
            "metrics": {
                "channels_monitored": len(channels),
                "overloaded_channels": critical_channels,
                "total_omnichannel_orders": total_orders,
                "bopis_peak_sla_breach_rate": bopis_sla_str,
                "ship_from_store_labor_load": f"{sfs_util_num:.0f}%",
                "central_dc_headroom": f"{dc_headroom:.1f}% buffer remaining",
            },
            "channel_matrix": channels,
            "key_vulnerabilities": vulnerabilities[:3],
        }

        if session_state is not None:
            session_state["fulfillment_findings"] = {
                "channels_monitored": len(channels),
                "overloaded_channels": critical_channels,
                "total_omnichannel_orders": total_orders,
                "bopis_utilization_num": bopis_util_num,
                "sfs_utilization_num": sfs_util_num,
                "dc_utilization_num": dc_util_num,
                "dc_headroom_pct": dc_headroom,
                "bopis_peak_sla_breach_rate": bopis_sla_str,
                "channel_matrix": channels,
            }

        return findings
