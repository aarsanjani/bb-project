"""
Digital Twin Simulation Engine for Retail Campaign Promotions.
Calculates dynamic outcomes across SKUs, DCs, suppliers, and fulfillment channels based on real-time levers.
"""
from typing import Dict, Any, List
import copy

BASE_SKUS = [
    {"sku": "Aurora Headphones", "disc": 15, "media": 120000, "base_demand": 22780, "base_stock": 23000, "price": 154.50, "cost": 93.50, "lead_time": 14, "so_days": 0},
    {"sku": "Aurora Earbuds Pro", "disc": 21, "media": 260000, "base_demand": 49638, "base_stock": 35500, "price": 93.10, "cost": 53.80, "lead_time": 39, "so_days": 5},
    {"sku": "Nimbus Smart Speaker", "disc": 12, "media": 45000, "base_demand": 23132, "base_stock": 24000, "price": 71.60, "cost": 40.70, "lead_time": 10, "so_days": 0},
    {"sku": "Vertex 14 Laptop Stand", "disc": 9, "media": 20000, "base_demand": 14715, "base_stock": 15000, "price": 49.00, "cost": 25.70, "lead_time": 12, "so_days": 0},
    {"sku": "Vertex Mech Keyboard", "disc": 18, "media": 90000, "base_demand": 13417, "base_stock": 13800, "price": 111.70, "cost": 62.70, "lead_time": 18, "so_days": 0},
    {"sku": "Vertex 4K Webcam", "disc": 12, "media": 30000, "base_demand": 9279, "base_stock": 9500, "price": 87.70, "cost": 48.00, "lead_time": 15, "so_days": 0},
    {"sku": "Pulse Fitness Band", "disc": 25, "media": 180000, "base_demand": 38400, "base_stock": 20500, "price": 68.00, "cost": 34.00, "lead_time": 28, "so_days": 12},
    {"sku": "Pulse Watch 2", "disc": 20, "media": 210000, "base_demand": 21500, "base_stock": 19200, "price": 199.00, "cost": 115.00, "lead_time": 24, "so_days": 4},
    {"sku": "Terra Power Bank 20k", "disc": 22, "media": 95000, "base_demand": 24500, "base_stock": 14500, "price": 45.00, "cost": 22.00, "lead_time": 21, "so_days": 10}
]

BASE_WAREHOUSES = [
    {"name": "Amsterdam DC", "limit_daily": 3220, "base_outbound": 4679, "region": "EMEA"},
    {"name": "Singapore DC", "limit_daily": 2660, "base_outbound": 3664, "region": "APAC"},
    {"name": "Chicago Central DC", "limit_daily": 6500, "base_outbound": 5800, "region": "North America"},
    {"name": "Dallas Regional DC", "limit_daily": 4200, "base_outbound": 3900, "region": "North America"}
]

BASE_SUPPLIERS = [
    {"name": "Hanoi Components", "capacity_limit": 101857, "base_demand": 103015, "lead_days": 39, "otif_pct": 88},
    {"name": "Taipei MicroSilicon", "capacity_limit": 85000, "base_demand": 72000, "lead_days": 18, "otif_pct": 96},
    {"name": "Shenzhen Precision Audio", "capacity_limit": 95000, "base_demand": 88000, "lead_days": 24, "otif_pct": 91}
]

class DigitalTwinEngine:
    """
    Simulates real-time supply chain digital twin behavior under campaign levers and world stress.
    """
    @staticmethod
    def simulate(levers: Dict[str, Any]) -> Dict[str, Any]:
        horizon = int(levers.get("horizon", 23))
        discount_mult = float(levers.get("discount_mult", 0.60))
        media_mult = float(levers.get("media_mult", 1.00))
        demand_uncertainty = float(levers.get("demand_uncertainty", 12)) / 100.0
        supplier_slip = int(levers.get("supplier_slip", 8))
        wh_capacity_pct = float(levers.get("wh_capacity", 70)) / 100.0
        channel_capacity_pct = float(levers.get("channel_capacity", 100)) / 100.0
        competitor_resp = float(levers.get("competitor_response", 25)) / 100.0
        interventions_applied = levers.get("interventions_applied", [])

        # Calculate demand multiplier
        elasticity_factor = 1.0 + (1.0 - discount_mult) * 1.8
        marketing_factor = (media_mult ** 0.6)
        comp_drag = 1.0 - (competitor_resp * 0.15)
        demand_scale = (horizon / 23.0) * elasticity_factor * marketing_factor * comp_drag

        # Process SKUs
        sku_outcomes = []
        total_demand = 0
        total_sold = 0
        total_revenue = 0.0
        total_margin = 0.0
        total_media_spend = 0.0
        out_of_stock_units = 0

        for b_sku in BASE_SKUS:
            sku_demand = int(b_sku["base_demand"] * demand_scale * (1.0 + (demand_uncertainty * 0.2)))
            # Effective stock calculation taking into account supplier slip
            available_stock = b_sku["base_stock"]
            
            # If intervention applied for SKU stock rebalance
            if "INTV-STOCK-REALLOC" in interventions_applied or "INTV-01" in interventions_applied:
                available_stock = int(available_stock * 1.25)
            if "INTV-AIR-PO" in interventions_applied or "INTV-02" in interventions_applied:
                available_stock = int(available_stock * 1.35)

            # Supplier slip effect
            effective_stock = int(available_stock * max(0.4, 1.0 - (supplier_slip * 0.025)))
            sold_units = min(sku_demand, effective_stock)
            unserved = max(0, sku_demand - sold_units)
            fill_rate = (sold_units / sku_demand * 100.0) if sku_demand > 0 else 100.0

            eff_price = b_sku["price"] * (1.0 - (b_sku["disc"] / 100.0))
            rev = sold_units * eff_price
            margin = sold_units * (eff_price - b_sku["cost"])
            media_spend = b_sku["media"] * media_mult

            # Stockout days
            so_days = 0
            if fill_rate < 95.0:
                so_days = int((1.0 - (fill_rate / 100.0)) * horizon * 0.7)
            if "INTV-02" in interventions_applied or "INTV-AIR-PO" in interventions_applied:
                so_days = max(0, so_days - 4)

            total_demand += sku_demand
            total_sold += sold_units
            total_revenue += rev
            total_margin += margin
            total_media_spend += media_spend
            out_of_stock_units += unserved

            sku_outcomes.append({
                "sku": b_sku["sku"],
                "disc": f"{b_sku['disc']}%",
                "media": f"${int(media_spend):,}",
                "demand": sku_demand,
                "sold": sold_units,
                "fill": f"{fill_rate:.1f}%",
                "fill_num": fill_rate,
                "unserved": unserved,
                "revenue": f"${int(rev):,}",
                "margin": f"${int(margin):,}",
                "so_days": so_days if so_days > 0 else "-"
            })

        # Calculate DC and Warehouse Breaches
        dc_shed_units = 0
        headline_risks = []
        hard_breaches_count = 0
        tight_constraints_count = 0

        for wh in BASE_WAREHOUSES:
            eff_limit = int(wh["limit_daily"] * wh_capacity_pct)
            projected_outbound = int(wh["base_outbound"] * demand_scale)
            
            if "INTV-WH-THROTTLE" in interventions_applied or "INTV-03" in interventions_applied:
                projected_outbound = min(projected_outbound, int(eff_limit * 1.05))

            if projected_outbound > eff_limit:
                hard_breaches_count += 1
                shed = int((projected_outbound - eff_limit) * (horizon * 0.4))
                dc_shed_units += shed
                headline_risks.append({
                    "type": "BREACH",
                    "category": "Warehouse",
                    "title": f"Warehouse - {wh['name']} - outbound units/day - {projected_outbound:,} vs limit {eff_limit:,}",
                    "details": f"{shed:,} units shed after overtime"
                })
            elif projected_outbound > int(eff_limit * 0.9):
                tight_constraints_count += 1

        # Supplier Breaches
        for sup in BASE_SUPPLIERS:
            projected_sup_demand = int(sup["base_demand"] * demand_scale)
            if "INTV-AIR-PO" in interventions_applied or "INTV-02" in interventions_applied:
                projected_sup_demand = min(projected_sup_demand, sup["capacity_limit"])

            if projected_sup_demand > sup["capacity_limit"]:
                hard_breaches_count += 1
                headline_risks.append({
                    "type": "BREACH",
                    "category": "Supplier",
                    "title": f"Supplier - {sup['name']} - capacity over horizon - {projected_sup_demand:,} vs limit {sup['capacity_limit']:,}",
                    "details": f"lead {sup['lead_days'] + supplier_slip}d, on-time {sup['otif_pct']}%"
                })
            else:
                tight_constraints_count += 1

        # SKU Breaches
        for s in sku_outcomes:
            if s["fill_num"] < 90.0:
                hard_breaches_count += 1
                headline_risks.append({
                    "type": "BREACH",
                    "category": "SKU",
                    "title": f"SKU - {s['sku']} - fill rate - {int(s['fill_num'])} vs limit 100",
                    "details": f"{s['so_days']} stockout days" if s['so_days'] != '-' else f"{s['unserved']:,} units unserved"
                })
            elif s["fill_num"] < 98.0:
                tight_constraints_count += 1

        # Service level
        service_level_pct = (total_sold / total_demand * 100.0) if total_demand > 0 else 100.0
        if service_level_pct < 90.0:
            hard_breaches_count += 1
            headline_risks.append({
                "type": "BREACH",
                "category": "Campaign",
                "title": f"Campaign - Blended service level - {int(service_level_pct)} vs limit 97",
                "details": f"Total {total_demand - total_sold:,} unserved units"
            })

        unserved_total = max(0, total_demand - total_sold)
        unserved_dollars = (unserved_total / total_demand * total_revenue) if total_demand > 0 else 0

        # Generate Time Series Daily Demand vs Fulfilled
        daily_series = []
        for d in range(1, horizon + 1):
            day_shape = 1.0 + (0.35 if d in (1, 2, 3, 14, 15) else (-0.25 if d in (7, 8, 9) else 0.05))
            daily_d = int((total_demand / horizon) * day_shape)
            fulfillment_drop = 1.0 if d < 4 else max(0.55, 1.0 - ((d - 3) * 0.04))
            daily_f = int(daily_d * fulfillment_drop)
            daily_series.append({
                "day": f"day {d}",
                "demand": daily_d,
                "fulfilled": daily_f
            })

        return {
            "campaign_outcome": {
                "units_sold": f"{total_sold:,}",
                "revenue": f"${total_revenue / 1_000_000:.2f}M",
                "gross_margin": f"${total_margin / 1_000_000:.2f}M",
                "service_level": f"{service_level_pct:.1f}%",
                "unserved_demand": f"{unserved_total:,} u",
                "unserved_demand_dollars": f"${unserved_dollars / 1_000_000:.2f}M at risk",
                "promo_logistics_spend": f"${(total_media_spend * 1.08) / 1_000_000:.2f}M",
                "media_spend_subtext": f"media ${total_media_spend / 1_000_000:.2f}M"
            },
            "headline_summary": f"{hard_breaches_count} hard breaches, {tight_constraints_count} tight constraints.",
            "headline_risks": headline_risks,
            "daily_series": daily_series,
            "loss_breakdown": {
                "out_of_stock": out_of_stock_units,
                "channel_order_cap": 0,
                "dc_throughput": dc_shed_units
            },
            "sku_outcomes": sku_outcomes,
            "interventions_available": [
                {
                    "id": "INTV-AIR-PO",
                    "title": "Air Freight Expedited PO for Hanoi Components & Audio SKUs",
                    "benefit": "+14,200 units recovered, eliminates 5 stockout days on Earbuds Pro",
                    "cost": "$88,000",
                    "applied": "INTV-AIR-PO" in interventions_applied or "INTV-02" in interventions_applied
                },
                {
                    "id": "INTV-WH-THROTTLE",
                    "title": "Amsterdam & Singapore DC Dynamic Order Throttling",
                    "benefit": "Eliminates 6,096 units overtime shed by routing overflow to Chicago DC",
                    "cost": "$14,500",
                    "applied": "INTV-WH-THROTTLE" in interventions_applied or "INTV-03" in interventions_applied
                },
                {
                    "id": "INTV-STOCK-REALLOC",
                    "title": "Digital Omnichannel Buffer Pre-Allocation",
                    "benefit": "Protects $2.1M high-margin in-store walk-in demand",
                    "cost": "$6,200",
                    "applied": "INTV-STOCK-REALLOC" in interventions_applied or "INTV-01" in interventions_applied
                }
            ]
        }
