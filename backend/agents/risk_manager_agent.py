"""
Risk Manager Swarm Specialist Agent.
Orchestrates cross-functional pressure-testing (Data Agent, Marketing Agent, Risk Agent)
and builds a prioritized Risk Register with connected BigQuery and GCS citations.
"""
from typing import Dict, Any, List
from backend.simulation.risk_register_data import (
    SPARK_CAMPAIGN_INFO,
    SPARK_DATA_SOURCES,
    SPARK_RISK_REGISTER,
    SPARK_SWARM_ACTIVITY_LOG
)

class RiskManagerSwarmAgent:
    def __init__(self):
        self.name = "risk_manager_agent"
        self.role = "Cross-Functional Swarm Risk Manager"
        self.disallow_transfer_to_parent = True
        self.disallow_transfer_to_peers = True

    def run_swarm_assessment(self, campaign_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executes swarm convergence across Data, Marketing, and Risk dimensions.
        """
        params = campaign_params or {}
        custom_query = params.get("query", "").strip()

        # Compute dynamic risk stats
        risks = list(SPARK_RISK_REGISTER)
        high_severity = [r for r in risks if r["severity"] == "HIGH"]
        med_severity = [r for r in risks if r["severity"] == "MED"]
        low_severity = [r for r in risks if r["severity"] == "LOW"]

        # Build 3x3 Heatmap Grid Counts: [Impact (0: High, 1: Med, 2: Low), Likelihood (0: Low, 1: Med, 2: High)]
        heatmap_matrix = [
            [[], [{"id": "02", "risk": "RISK-02"}, {"id": "03", "risk": "RISK-03"}], [{"id": "01", "risk": "RISK-01"}]], # High Impact
            [[], [{"id": "05", "risk": "RISK-05"}], [{"id": "04", "risk": "RISK-04"}]],                                     # Med Impact
            [[], [{"id": "06", "risk": "RISK-06"}], []]                                                                      # Low Impact
        ]

        return {
            "status": "SUCCESS",
            "campaign": SPARK_CAMPAIGN_INFO,
            "data_sources": SPARK_DATA_SOURCES,
            "risk_register": risks,
            "heatmap_matrix": heatmap_matrix,
            "activity_log": SPARK_SWARM_ACTIVITY_LOG,
            "run_ledger": {
                "bq_bytes_scanned": "2.41 TB",
                "gcs_docs_retrieved": "17 docs",
                "agents_spawned": 3
            },
            "user_query_response": (
                f"Swarm evaluated query: '{custom_query}'. Found 6 risk factors across cold-chain, inventory draw, and cannibalisation."
                if custom_query else None
            )
        }
