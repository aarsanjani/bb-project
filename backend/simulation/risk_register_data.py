"""
Data models and simulation fixtures for the Spark Campaign Ops & Risk Register Swarm.
Captures connected enterprise data sources (BigQuery, GCS), risk registers with citation linkages,
3x3 Impact vs Likelihood heat maps, and cross-functional agent execution logs.
"""
from typing import Dict, Any, List

SPARK_CAMPAIGN_INFO = {
    "tenant": "PIC · 7-Eleven",
    "department": "Campaign Ops",
    "campaign_name": "Q4 Chilled RTE Push",
    "manager": "Ploy Siriwan",
    "role": "CAMPAIGN MANAGER",
    "status": "Register ready",
    "verdict": "DO NOT LAUNCH AS BRIEFED",
    "verdict_severity": "HIGH_EXPOSURE",
    "summary_metrics": {
        "risk_factors_count": 6,
        "high_severity_count": 3,
        "unfunded_margin_exposure": "฿18.4M",
        "unfunded_margin_usd": "$525,000",
        "goal_alignment_pct": "12%",
        "goal_alignment_subtext": "as briefed",
        "interventions_count": 15,
        "interventions_timeline": "6 owners · T-14 → T-2"
    },
    "verdict_narrative": (
        "The mechanic is sound but it is pointed at the wrong goal. As briefed, the campaign will deliver "
        "basket uplift and lose margin, while moving new-user rate by roughly +1.2pp, not +15%. "
        "Three changes recover it: re-scope the 42 breaching SKUs, gate the deepest tier behind a first 7-App purchase, "
        "and pre-allocate hero stock to the top-1,142 store cluster. All three are feasible inside the current T-14 window."
    )
}

SPARK_DATA_SOURCES = {
    "local_files": [
        {"name": "promo_sku_list_v3.xlsx", "type": "excel", "size": "420 KB"},
        {"name": "campaign_goals_FY26Q4.docx", "type": "doc", "size": "1.2 MB"},
        {"name": "POS_creative_pack/ (18)", "type": "folder", "items_count": 18}
    ],
    "bigquery": {
        "status": "LINKED",
        "dataset": "pic-7e-prod.retail_core",
        "tables": ["stores", "sku_master", "suppliers", "fulfillment_channels", "pos_txn_daily", "inventory_snapshot"],
        "bytes_scanned": "2.41 TB"
    },
    "cloud_storage": {
        "status": "LINKED",
        "bucket": "gs://pic-7e-knowledge/",
        "docs": ["trade_promo_policy_v4.2", "cold_chain_sop", "post_campaign_reviews/", "supplier_MSA/"],
        "docs_retrieved": 17
    },
    "skill": {
        "name": "Campaign Assistant",
        "description": "Swarms a cross-functional agent team to pressure-test a promotion before launch.",
        "tags": ["risk-manager", "3 agents"]
    }
}

SPARK_RISK_REGISTER: List[Dict[str, Any]] = [
    {
        "risk_id": "RISK-01",
        "score": 8.7,
        "severity": "HIGH",
        "impact_likelihood": {"impact": "HIGH", "likelihood": "HIGH", "grid_pos": [0, 2]},
        "title": "Cold-chain temperature excursion at high-velocity store staging",
        "description": "Chilled RTE products (sandwich packs & bento) risk exceeding 4°C safety threshold during peak 11:30-13:30 replenishment waves in 412 non-walk-in cooler stores.",
        "citations": ["GCS · cold_chain_sop", "BQ · store_asset", "BQ · waste_daily"],
        "interventions_count": 3,
        "plays_count": 3
    },
    {
        "risk_id": "RISK-02",
        "score": 8.1,
        "severity": "HIGH",
        "impact_likelihood": {"impact": "HIGH", "likelihood": "MED", "grid_pos": [0, 1]},
        "title": "Hero SKU inventory draw velocity depletes Central DC buffer by Day 2",
        "description": "Promotional discount elasticity (+32%) causes 8 hero bento SKUs to breach safety stock levels across Bangkok Metro regional stores within 36 hours of launch.",
        "citations": ["BQ · inventory_snapshot", "BQ · pos_txn_daily"],
        "interventions_count": 3,
        "plays_count": 3
    },
    {
        "risk_id": "RISK-03",
        "score": 7.9,
        "severity": "HIGH",
        "impact_likelihood": {"impact": "HIGH", "likelihood": "MED", "grid_pos": [0, 1]},
        "title": "7-App exclusive coupon margin leakage without basket hurdle",
        "description": "Discount coupon lacks minimum spend threshold (฿150), allowing single-item discount redemptions that erode gross margin without achieving targeted cross-sell basket expansion.",
        "citations": ["GCS · trade_promo_policy_v4.2", "BQ · category_hierarchy"],
        "interventions_count": 3,
        "plays_count": 3
    },
    {
        "risk_id": "RISK-04",
        "score": 6.4,
        "severity": "MED",
        "impact_likelihood": {"impact": "MED", "likelihood": "HIGH", "grid_pos": [1, 2]},
        "title": "BOPIS locker thermal capacity limit in high-density office zones",
        "description": "Store pick-up staging lockers exceed chilled physical capacity, creating order fulfillment queue delays (> 15 mins) during peak lunch hours.",
        "citations": ["BQ · fulfillment_channels", "GCS · cold_chain_sop"],
        "interventions_count": 2,
        "plays_count": 2
    },
    {
        "risk_id": "RISK-05",
        "score": 5.8,
        "severity": "MED",
        "impact_likelihood": {"impact": "MED", "likelihood": "MED", "grid_pos": [1, 1]},
        "title": "Cannibalisation of the full-price hot-food counter",
        "description": "Chilled RTE and hot-food counter share 61% basket overlap in the 11:00-14:00 daypart. Hot food carries 9pp higher margin. Modelled substitution says 23% of promo volume is transferred, not incremental — turning a revenue win into a mix loss.",
        "citations": ["BQ · pos_txn_daily", "BQ · category_hierarchy"],
        "interventions_count": 2,
        "plays_count": 2
    },
    {
        "risk_id": "RISK-06",
        "score": 4.2,
        "severity": "LOW",
        "impact_likelihood": {"impact": "LOW", "likelihood": "MED", "grid_pos": [2, 1]},
        "title": "Supplier concentration — 3 vendors cover 61% of promo volume",
        "description": "Three suppliers account for 61% of promo SKU units. Two share a single chilled production site in Bang Na. A single line stoppage takes out over a third of the campaign, and neither MSA carries a promotional volume-commitment clause.",
        "citations": ["BQ · suppliers", "GCS · supplier_MSA/"],
        "interventions_count": 2,
        "plays_count": 2
    }
]

SPARK_SWARM_ACTIVITY_LOG = [
    {"time": "00:23", "event": "Risk register delivered", "type": "system"},
    {"time": "00:22", "event": "RISK-06 scored 4.2 · 2 plays", "type": "risk"},
    {"time": "00:22", "event": "RISK-05 scored 5.8 · 2 plays", "type": "risk"},
    {"time": "00:21", "event": "RISK-04 scored 6.4 · 2 plays", "type": "risk"},
    {"time": "00:21", "event": "RISK-03 scored 7.9 · 3 plays", "type": "risk"},
    {"time": "00:20", "event": "RISK-02 scored 8.1 · 3 plays", "type": "risk"},
    {"time": "00:20", "event": "RISK-01 scored 8.7 · 3 plays", "type": "risk"},
    {"time": "00:18", "event": "Swarm converged", "type": "swarm"},
    {"time": "00:18", "event": "Risk Agent finished", "type": "agent"},
    {"time": "00:17", "event": "Marketing Agent finished", "type": "agent"},
    {"time": "00:16", "event": "Data Agent finished", "type": "agent"},
    {"time": "00:12", "event": "Risk Agent spawned", "type": "agent"},
    {"time": "00:11", "event": "Marketing Agent spawned", "type": "agent"},
    {"time": "00:10", "event": "Data Agent spawned", "type": "agent"}
]
