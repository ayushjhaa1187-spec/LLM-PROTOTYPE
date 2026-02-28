import pytest
from unittest.mock import patch

def test_run_query_access_denied(client):
    # Register and get token
    reg = client.post("/api/v1/auth/register", json={"email": "test@example.com", "password": "password123", "full_name": "Test User"})
    token = reg.json()["access_token"]
    
    # Send a query asking for a document we don't own/doesn't exist
    response = client.post(
        "/api/v1/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "test query", "document_ids": ["non-existent-id"]}
    )
    
    # Should be 403 denied because document isn't accessible
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]

@patch("app.routes.queries.orchestrator.run_pipeline")
def test_run_query_success(mock_run_pipeline, client):
    # Mocking pipeline to avoid expensive OpenAI calls
    mock_run_pipeline.return_value = {
        "answer": "This is a mock answer",
        "citations": [],
        "confidence": 0.99,
        "tokens_used": 150,
        "processing_time_ms": 100,
        "agent_logs": [],
        "verification": {}
    }
    
    reg = client.post("/api/v1/auth/register", json={"email": "test2@example.com", "password": "password123", "full_name": "Test 2"})
    token = reg.json()["access_token"]
    
    response = client.post(
        "/api/v1/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "What is FAR 19.502-2?", "document_ids": []}
    )
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["answer"] == "This is a mock answer"
    assert "id" in res_data
