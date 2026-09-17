"""
Simulation data and models for multi-dimensional promotion impact analysis.
Provides deterministic data structures for Stores, SKUs, Suppliers, and Fulfillment Channels.
"""
from typing import Dict, List, Any

# Mock Enterprise Catalog & Network Configuration
STORES_DATA: List[Dict[str, Any]] = [
    {
        "store_id": "STR-101",
        "name": "Manhattan Flagship (NYC)",
        "region": "Northeast",
        "foot_traffic_surge": "+145%",
        "baseline_demand_units": 1200,
        "projected_promo_demand": 3800,
        "current_on_hand": 2100,
        "stockout_risk_pct": 82.5,
        "stockout_day": "Day 2 (14:00)",
        "projected_revenue": "$184,500",
        "store_margin_pct": "34.2%",
        "risk_status": "CRITICAL_STOCKOUT",
        "bottleneck": "Limited backroom floor space for restock staging"
    },
    {
        "store_id": "STR-104",
        "name": "Chicago Downtown (IL)",
        "region": "Midwest",
        "foot_traffic_surge": "+95%",
        "baseline_demand_units": 950,
        "projected_promo_demand": 2400,
        "current_on_hand": 2600,
        "stockout_risk_pct": 14.0,
        "stockout_day": "None (Healthy)",
        "projected_revenue": "$112,000",
        "store_margin_pct": "37.5%",
        "risk_status": "OPTIMAL",
        "bottleneck": "None"
    },
    {
        "store_id": "STR-108",
        "name": "Austin Tech Ridge (TX)",
        "region": "South",
        "foot_traffic_surge": "+110%",
        "baseline_demand_units": 800,
        "projected_promo_demand": 2100,
        "current_on_hand": 1400,
        "stockout_risk_pct": 68.0,
        "stockout_day": "Day 3 (10:30)",
        "projected_revenue": "$98,700",
        "store_margin_pct": "35.8%",
        "risk_status": "HIGH_RISK",
        "bottleneck": "Regional DC transit delay (+24h)"
    },
    {
        "store_id": "STR-112",
        "name": "San Francisco Union Sq (CA)",
        "region": "West",
        "foot_traffic_surge": "+130%",
        "baseline_demand_units": 1100,
        "projected_promo_demand": 3100,
        "current_on_hand": 1950,
        "stockout_risk_pct": 74.2,
        "stockout_day": "Day 2 (18:00)",
        "projected_revenue": "$149,200",
        "store_margin_pct": "33.1%",
        "risk_status": "HIGH_RISK",
        "bottleneck": "BOPIS locker queue capacity maxed"
    },
    {
        "store_id": "STR-119",
        "name": "Miami South Beach (FL)",
        "region": "Southeast",
        "foot_traffic_surge": "+85%",
        "baseline_demand_units": 750,
        "projected_promo_demand": 1850,
        "current_on_hand": 2200,
        "stockout_risk_pct": 8.5,
        "stockout_day": "None (Healthy)",
        "projected_revenue": "$86,400",
        "store_margin_pct": "38.0%",
        "risk_status": "OPTIMAL",
        "bottleneck": "None"
    },
    {
        "store_id": "STR-125",
        "name": "Seattle Pike Place (WA)",
        "region": "Northwest",
        "foot_traffic_surge": "+120%",
        "baseline_demand_units": 900,
        "projected_promo_demand": 2650,
        "current_on_hand": 1800,
        "stockout_risk_pct": 61.5,
        "stockout_day": "Day 3 (16:00)",
        "projected_revenue": "$124,300",
        "store_margin_pct": "36.4%",
        "risk_status": "ELEVATED_RISK",
        "bottleneck": "Ship-from-Store packing station saturation"
    }
]

SKUS_DATA: List[Dict[str, Any]] = [
    {
        "sku_id": "SKU-9901",
        "name": "UltraVision 65' 4K OLED Smart TV",
        "category": "Consumer Electronics",
        "base_price": "$899.99",
        "promo_price": "$649.99 (-28%)",
        "elasticity_coefficient": 2.85,
        "projected_unit_demand": 4200,
        "total_available_stock": 2850,
        "depletion_day": "Day 2",
        "projected_revenue": "$2,729,958",
        "promo_margin_pct": "21.4% (vs 38.5% reg)",
        "gmroi": 3.42,
        "cannibalization_target": "SKU-9903 (55' OLED -32% demand)",
        "stockout_severity": "CRITICAL"
    },
    {
        "sku_id": "SKU-8820",
        "name": "AcousticPro ANC Wireless Headphones",
        "category": "Audio & Accessories",
        "base_price": "$249.99",
        "promo_price": "$179.99 (-28%)",
        "elasticity_coefficient": 2.15,
        "projected_unit_demand": 7500,
        "total_available_stock": 6100,
        "depletion_day": "Day 3",
        "projected_revenue": "$1,349,925",
        "promo_margin_pct": "42.1%",
        "gmroi": 4.88,
        "cannibalization_target": "None (Complementary attach item)",
        "stockout_severity": "MODERATE"
    },
    {
        "sku_id": "SKU-7741",
        "name": "NeoSmart Home Hub & Sensor Bundle",
        "category": "Smart Home",
        "base_price": "$199.99",
        "promo_price": "$129.99 (-35%)",
        "elasticity_coefficient": 3.10,
        "projected_unit_demand": 5800,
        "total_available_stock": 6500,
        "depletion_day": "Day 4 (Buffer OK)",
        "projected_revenue": "$753,942",
        "promo_margin_pct": "31.0%",
        "gmroi": 4.12,
        "cannibalization_target": "SKU-7738 (Legacy Hub -48%)",
        "stockout_severity": "HEALTHY"
    },
    {
        "sku_id": "SKU-6612",
        "name": "Apex Pro Robotic Vacuum & Mop",
        "category": "Home Appliances",
        "base_price": "$549.99",
        "promo_price": "$399.99 (-27%)",
        "elasticity_coefficient": 2.40,
        "projected_unit_demand": 3100,
        "total_available_stock": 1900,
        "depletion_day": "Day 2 (11:00)",
        "projected_revenue": "$1,239,969",
        "promo_margin_pct": "26.8%",
        "gmroi": 3.15,
        "cannibalization_target": "Manual Vacuums (-15%)",
        "stockout_severity": "CRITICAL"
    }
]

SUPPLIERS_DATA: List[Dict[str, Any]] = [
    {
        "supplier_id": "SUP-801",
        "name": "Apex Display Technologies Ltd",
        "key_component": "65-inch OLED Display Panels (SKU-9901)",
        "country": "South Korea / Vietnam",
        "standard_lead_time_days": 28,
        "expedited_lead_time_days": 8,
        "factory_capacity_utilization": "96.4%",
        "otif_score": "89.2%",
        "max_surge_units": 1500,
        "emergency_po_surcharge": "$45/unit ($67,500 total)",
        "raw_material_risk": "HIGH (Glass substrate shortage)",
        "status": "CONSTRAINED"
    },
    {
        "supplier_id": "SUP-742",
        "name": "Sonics MicroAcoustics Corp",
        "key_component": "DSP Chipsets & Drivers (SKU-8820)",
        "country": "Taiwan / Austin TX",
        "standard_lead_time_days": 14,
        "expedited_lead_time_days": 4,
        "factory_capacity_utilization": "78.0%",
        "otif_score": "96.5%",
        "max_surge_units": 4000,
        "emergency_po_surcharge": "$12/unit ($24,000 total)",
        "raw_material_risk": "LOW (Silicon supply secured)",
        "status": "RESPONSIVE"
    },
    {
        "supplier_id": "SUP-619",
        "name": "RoboMotion Mechatronics",
        "key_component": "LiDAR Modules & Brushless Motors (SKU-6612)",
        "country": "Germany / Mexico",
        "standard_lead_time_days": 21,
        "expedited_lead_time_days": 6,
        "factory_capacity_utilization": "94.0%",
        "otif_score": "84.0%",
        "max_surge_units": 1200,
        "emergency_po_surcharge": "$38/unit ($45,600 total)",
        "raw_material_risk": "MEDIUM (Rare earth magnet lead time)",
        "status": "CRITICAL_BOTTLENECK"
    },
    {
        "supplier_id": "SUP-550",
        "name": "IoT Gateway Devices Group",
        "key_component": "Zigbee/Matter Connectivity Radios (SKU-7741)",
        "country": "USA / Japan",
        "standard_lead_time_days": 10,
        "expedited_lead_time_days": 3,
        "factory_capacity_utilization": "72.0%",
        "otif_score": "98.1%",
        "max_surge_units": 5000,
        "emergency_po_surcharge": "$5/unit ($10,000 total)",
        "raw_material_risk": "LOW",
        "status": "SECURE"
    }
]

CHANNELS_DATA: List[Dict[str, Any]] = [
    {
        "channel_name": "Buy Online, Pick Up In Store (BOPIS)",
        "demand_share_pct": "34.0%",
        "projected_order_volume": "18,400 orders",
        "peak_hour_surge": "285% vs baseline",
        "labor_capacity_utilization": "112% (OVER CAPACITY)",
        "projected_sla_breach_rate": "18.4% (> 2 hr hold delay)",
        "bottleneck_factor": "Store associate staging & locker density limit",
        "health": "CRITICAL"
    },
    {
        "channel_name": "Ship-From-Store (Omnichannel SFS)",
        "demand_share_pct": "22.0%",
        "projected_order_volume": "11,900 orders",
        "peak_hour_surge": "190% vs baseline",
        "labor_capacity_utilization": "104% (OVER CAPACITY)",
        "projected_sla_breach_rate": "14.2% (Carrier cutoff missed)",
        "bottleneck_factor": "Single pack station per store; carton box stockout",
        "health": "HIGH_RISK"
    },
    {
        "channel_name": "Central DC Direct-to-Consumer (DTC)",
        "demand_share_pct": "30.0%",
        "projected_order_volume": "16,200 orders",
        "peak_hour_surge": "165% vs baseline",
        "labor_capacity_utilization": "88.0% (WITHIN SAFE THRESHOLD)",
        "projected_sla_breach_rate": "3.1% (Standard ground delivery)",
        "bottleneck_factor": "Secondary sorting conveyor speed",
        "health": "HEALTHY"
    },
    {
        "channel_name": "In-Store POS / Walk-in Register",
        "demand_share_pct": "14.0%",
        "projected_order_volume": "7,600 transactions",
        "peak_hour_surge": "130% vs baseline",
        "labor_capacity_utilization": "82.0%",
        "projected_sla_breach_rate": "5.0% (Checkout queue > 7 mins)",
        "bottleneck_factor": "Peak hours 12pm-2pm and 5pm-8pm cashier staffing",
        "health": "STABLE"
    }
]

INTERVENTIONS_DATA: List[Dict[str, Any]] = [
    {
        "intervention_id": "INTV-01",
        "title": "Dynamic Digital Allocation & Dynamic Buffer Lock",
        "category": "Channel & Store Allocation",
        "priority": "P0 - IMMEDIATE",
        "trigger_condition": "Store stockout probability > 60% OR BOPIS capacity > 100%",
        "action_description": "Cap BOPIS order intake at 90% store capacity and dynamically reroute excess online demand to Central DC DTC fulfillment. Pre-allocate 400 reserve units of SKU-9901 and SKU-6612 to Manhattan (STR-101) & SF (STR-112).",
        "risk_mitigation": "Eliminates $280K in lost store sales; reduces BOPIS SLA breach from 18.4% to < 4.5%.",
        "implementation_cost": "$8,200 (Software throttling + freight adjustment)",
        "net_roi": "34.1x ROI",
        "status": "RECOMMENDED"
    },
    {
        "intervention_id": "INTV-02",
        "title": "Expedited Tier-1 Supplier Pre-PO Dispatch",
        "category": "Supply Chain & Manufacturing",
        "priority": "P0 - CRITICAL",
        "trigger_condition": "Projected SKU stockout before Day 3 of promotion",
        "action_description": "Authorize expedited air freight Purchase Orders for 1,200 OLED panels with Apex Display (SUP-801) and 800 LiDAR assemblies with RoboMotion (SUP-619) with 6-8 day SLA.",
        "risk_mitigation": "Prevents catastrophic mid-promo stockouts on SKU-9901 and SKU-6612; protects $1.15M in back-half promo revenue.",
        "implementation_cost": "$113,100 (Emergency surcharges)",
        "net_roi": "10.2x ROI",
        "status": "RECOMMENDED"
    },
    {
        "intervention_id": "INTV-03",
        "title": "Smart SFS-to-DC Fulfillment Reroute Guardrail",
        "category": "Fulfillment Logistics",
        "priority": "P1 - HIGH",
        "trigger_condition": "Ship-from-Store backlog > 120 orders per store",
        "action_description": "Automatically disable Ship-from-Store orders in NYC, SF, and Austin when store on-hand falls below 3 days of walk-in demand, preserving inventory for high-margin in-store shoppers.",
        "risk_mitigation": "Prevents local walk-in customer stockout dissatisfaction while shifting volume to high-throughput Central DC automated pick-lines.",
        "implementation_cost": "$3,500 (Omnichannel routing rule config)",
        "net_roi": "45.0x ROI",
        "status": "RECOMMENDED"
    },
    {
        "intervention_id": "INTV-04",
        "title": "Micro-Elasticity Margin Circuit Breaker",
        "category": "Pricing & Merchandising",
        "priority": "P2 - CONTINGENCY",
        "trigger_condition": "National inventory level for SKU-9901 drops below 15% before 48 hours",
        "action_description": "Automatically step up promotional price from $649.99 to $699.99 (-22% discount instead of -28%), slowing demand velocity by 24% while capturing an additional +$50 margin per unit on remaining 1,200 units.",
        "risk_mitigation": "Extends stock availability through promotional weekend; generates +$60,000 pure margin capture.",
        "implementation_cost": "$0 (Automated pricing feed)",
        "net_roi": "Infinite",
        "status": "AUTOMATED_TRIGGER"
    }
]
