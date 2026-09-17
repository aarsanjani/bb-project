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
