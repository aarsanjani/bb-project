"""
Automated Test Suite for ADK 2.x & A2UI Enterprise Promotion Simulation Platform.
Verifies SSE stream compliance, multi-agent FCoT state transitions, and A2UI schema-driven layout payloads.
"""
import json
import pytest
from backend.app import app
from backend.agents.store_agent import StoreDemandAgent
from backend.agents.sku_agent import SkuInventoryAgent
from backend.agents.supplier_agent import SupplierCapacityAgent
from backend.agents.fulfillment_agent import FulfillmentLogisticsAgent
from backend.orchestrator import PromotionOrchestratorEngine

@pytest.fixture
def test_client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_session_endpoint(test_client):
    """Verifies durable session context generation."""
    response = test_client.get('/api/session')
    assert response.status_code == 200
    data = response.get_json()
    assert data["lifecycle_state"] == "ACTIVE"
    assert len(data["active_mesh"]) == 5

def test_promotion_presets_endpoint(test_client):
    """Verifies availability of promotion scenario presets."""
    response = test_client.get('/api/promotions/presets')
    assert response.status_code == 200
    data = response.get_json()
    assert "presets" in data
    assert len(data["presets"]) >= 3

def test_stream_endpoint_schema_compliance(test_client):
    """
    Verifies that the /api/chat/stream SSE endpoint emits valid JSON-RPC 2.0 frames
    and delivers the complete multi-scale A2UI component tree.
    """
    payload = {
        "prompt": "Before I launch this promotion, show me exactly what will happen across every store, SKU, supplier and fulfillment channel and tell me the best intervention if something goes wrong.",
        "session_id": "test-session-suite-1"
    }
    response = test_client.post('/api/chat/stream', json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers['Content-Type']

    raw_text = response.get_data(as_text=True)
    events = [line.replace("data: ", "").strip() for line in raw_text.split("\n\n") if line.startswith("data:")]

    assert len(events) >= 8, f"Expected at least 8 SSE frames, received {len(events)}"

    methods_received = set()
    a2ui_payload = None

    for evt_str in events:
        data = json.loads(evt_str)
        assert data["jsonrpc"] == "2.0"
        assert "method" in data
        assert "params" in data
        method = data["method"]
        methods_received.add(method)

        if method == "onUiComponentDelivery":
            a2ui_payload = data["params"]["payload"]

    assert "onAgentThought" in methods_received
    assert "onAgentDelegation" in methods_received
    assert "onToolCall" in methods_received
    assert "onUiComponentDelivery" in methods_received
    assert "onSimulationComplete" in methods_received

    # Verify A2UI schema structure
    assert a2ui_payload is not None
    assert a2ui_payload["type"] == "Dashboard"
    
    # Locate Tabs component
    tabs_comp = None
    for comp in a2ui_payload["components"]:
        if comp["type"] == "Tabs":
            tabs_comp = comp
            break
            
    assert tabs_comp is not None
    tab_ids = [t["id"] for t in tabs_comp["components"]]
    assert "tab_executive_summary" in tab_ids
    assert "tab_stores" in tab_ids
    assert "tab_skus" in tab_ids
    assert "tab_suppliers" in tab_ids
    assert "tab_fulfillment" in tab_ids
    assert "tab_interventions" in tab_ids

def test_store_agent_analysis():
    """Unit test for StoreDemandAgent."""
    agent = StoreDemandAgent()
    results = agent.analyze({"name": "Test Promo"})
    assert results["status"] == "COMPLETED"
    assert len(results["store_matrix"]) >= 6
    assert results["metrics"]["critical_stockout_stores"] >= 1

def test_sku_agent_analysis():
    """Unit test for SkuInventoryAgent."""
    agent = SkuInventoryAgent()
    results = agent.analyze({"name": "Test Promo"})
    assert results["status"] == "COMPLETED"
    assert len(results["sku_matrix"]) >= 4
    assert results["metrics"]["critical_stockout_skus"] >= 1

def test_supplier_agent_analysis():
    """Unit test for SupplierCapacityAgent."""
    agent = SupplierCapacityAgent()
    results = agent.analyze({"name": "Test Promo"})
    assert results["status"] == "COMPLETED"
    assert len(results["supplier_matrix"]) >= 4
    assert results["metrics"]["constrained_suppliers"] >= 1

def test_fulfillment_agent_analysis():
    """Unit test for FulfillmentLogisticsAgent."""
    agent = FulfillmentLogisticsAgent()
    results = agent.analyze({"name": "Test Promo"})
    assert results["status"] == "COMPLETED"
    assert len(results["channel_matrix"]) >= 4
    assert results["metrics"]["overloaded_channels"] >= 1

def test_apply_intervention_endpoint(test_client):
    """Verifies applying an automated intervention circuit breaker."""
    payload = {"intervention_id": "INTV-01", "action": "EXECUTE"}
    response = test_client.post('/api/interventions/apply', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "SUCCESS"
    assert data["applied_state"] == "ACTIVE_GUARDRAIL_ENGAGED"

def test_apply_invalid_intervention_endpoint(test_client):
    """Verifies error handling for non-existent intervention."""
    payload = {"intervention_id": "INTV-NONEXISTENT"}
    response = test_client.post('/api/interventions/apply', json=payload)
    assert response.status_code == 404

def test_digital_twin_simulation_endpoint(test_client):
    """Verifies digital twin calculation endpoint."""
    payload = {
        "horizon": 23,
        "discount_mult": 0.60,
        "media_mult": 1.00,
        "demand_uncertainty": 12,
        "supplier_slip": 8,
        "wh_capacity": 70,
        "channel_capacity": 100,
        "competitor_response": 25
    }
    response = test_client.post('/api/digital-twin/simulate', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert "campaign_outcome" in data
    assert "headline_risks" in data
    assert "daily_series" in data
    assert "loss_breakdown" in data
    assert "sku_outcomes" in data
    assert len(data["daily_series"]) == 23
    assert len(data["sku_outcomes"]) >= 8

def test_digital_twin_optimize_endpoint(test_client):
    """Verifies digital twin greedy optimizer endpoint."""
    payload = {
        "horizon": 23,
        "discount_mult": 0.60,
        "media_mult": 1.00,
        "greedy_rounds": 4,
        "optimize_for": "Balanced (margin + service)"
    }
    response = test_client.post('/api/digital-twin/optimize', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["optimization_status"] == "RESOLVED"
    assert data["rounds_completed"] == 4

def test_pre_mortem_view(test_client):
    """Verifies rendering of the /twin pre-mortem digital twin view."""
    response = test_client.get('/twin')
    assert response.status_code == 200
    assert "Promo Pre-Mortem" in response.get_data(as_text=True)


def test_cross_agent_state_propagation():
    """
    Verifies that agents interact functionally via shared session_state:
    StoreDemandAgent -> SkuInventoryAgent -> SupplierCapacityAgent -> FulfillmentLogisticsAgent.
    """
    session_state = {}
    promo_params = {
        "name": "Flash 48-Hour Omni-Deals (40% Off Storewide)",
        "duration_days": 2,
        "target_discount_pct": "40%",
        "forecast_multiplier": 3.8,
    }

    store_agent = StoreDemandAgent()
    sku_agent = SkuInventoryAgent()
    supplier_agent = SupplierCapacityAgent()
    fulfillment_agent = FulfillmentLogisticsAgent()

    # 1. Store agent writes store_findings into session_state
    store_res = store_agent.analyze(promo_params, session_state=session_state)
    assert "store_findings" in session_state
    assert session_state["store_findings"]["total_projected_store_units"] == store_res["metrics"]["total_projected_store_units"]

    # 2. SKU agent consumes store_findings from session_state and writes sku_findings
    sku_res = sku_agent.analyze(promo_params, session_state=session_state)
    assert "sku_findings" in session_state
    assert "sku_deficits_by_id" in session_state["sku_findings"]
    assert session_state["sku_findings"]["upstream_store_units"] == store_res["metrics"]["total_projected_store_units"]

    # 3. Supplier agent consumes sku_findings (deficits & depletion timeline) from session_state
    sup_res = supplier_agent.analyze(promo_params, session_state=session_state)
    assert "supplier_findings" in session_state
    assert session_state["supplier_findings"]["total_expedited_surcharge_num"] > 0
    assert sup_res["metrics"]["upstream_sku_deficit_units"] == session_state["sku_findings"]["deficit_units_num"]

    # 4. Fulfillment agent consumes both store_findings and sku_findings from session_state
    ful_res = fulfillment_agent.analyze(promo_params, session_state=session_state)
    assert "fulfillment_findings" in session_state
    assert ful_res["metrics"]["total_omnichannel_orders"] > 0


def test_dynamic_parameter_sensitivity_across_presets():
    """
    Verifies that changing promotional parameters (e.g. Flash 40% Off vs Fall 25% Off)
    dynamically changes subagent outputs and orchestrator A2UI KPIs.
    """
    flash_engine = PromotionOrchestratorEngine(
        session_id="test-flash",
        declarative_intent="Simulate 48-hour flash sale at 40% off",
        promo_parameters={
            "name": "Flash 48-Hour Omni-Deals",
            "duration_days": 2,
            "target_discount_pct": "40%",
            "forecast_multiplier": 3.8,
        }
    )
    gentle_engine = PromotionOrchestratorEngine(
        session_id="test-gentle",
        declarative_intent="Simulate 7-day fall home campaign at 25% off",
        promo_parameters={
            "name": "Fall Home Essentials",
            "duration_days": 7,
            "target_discount_pct": "25%",
            "forecast_multiplier": 1.8,
        }
    )

    flash_frames = [json.loads(f) for f in flash_engine.execute_workflow()]
    gentle_frames = [json.loads(f) for f in gentle_engine.execute_workflow()]

    flash_complete = [f["params"] for f in flash_frames if f["method"] == "onSimulationComplete"][0]
    gentle_complete = [f["params"] for f in gentle_frames if f["method"] == "onSimulationComplete"][0]

    # Flash sale (3.8x multiplier) must generate higher projected demand and risk than Gentle sale (1.8x)
    assert flash_complete["projected_revenue_impact"] != gentle_complete["projected_revenue_impact"]
    assert flash_engine.session_state["store_findings"]["total_projected_store_units"] > (
        gentle_engine.session_state["store_findings"]["total_projected_store_units"]
    )
    assert flash_engine.session_state["sku_findings"]["deficit_units_num"] > (
        gentle_engine.session_state["sku_findings"]["deficit_units_num"]
    )


def test_closed_loop_intervention_effect():
    """
    Verifies that applying interventions (INTV-01, INTV-02, INTV-03, INTV-04)
    measurably mitigates stockouts, SKU deficits, and BOPIS/SFS channel overload when re-simulated.
    """
    base_params = {
        "name": "Summer Electronics & Appliance Blast (30-35% Off)",
        "duration_days": 4,
        "target_discount_pct": "28-35%",
        "forecast_multiplier": 2.7,
        "applied_interventions": []
    }
    mitigated_params = {
        "name": "Summer Electronics & Appliance Blast (30-35% Off)",
        "duration_days": 4,
        "target_discount_pct": "28-35%",
        "forecast_multiplier": 2.7,
        "applied_interventions": ["INTV-01", "INTV-02", "INTV-03", "INTV-04"]
    }

    base_engine = PromotionOrchestratorEngine("sim-base", "Base run", promo_parameters=base_params)
    list(base_engine.execute_workflow())

    mitigated_engine = PromotionOrchestratorEngine("sim-mitigated", "Mitigated run", promo_parameters=mitigated_params)
    list(mitigated_engine.execute_workflow())

    # Net unbridged SKU deficit and BOPIS overload must decrease when interventions are active
    assert mitigated_engine.session_state["sku_findings"]["net_unmitigated_deficit"] < (
        base_engine.session_state["sku_findings"]["net_unmitigated_deficit"]
    )
    assert mitigated_engine.session_state["fulfillment_findings"]["bopis_utilization_num"] < (
        base_engine.session_state["fulfillment_findings"]["bopis_utilization_num"]
    )

