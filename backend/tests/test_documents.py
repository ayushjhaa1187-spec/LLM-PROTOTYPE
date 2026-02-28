import pytest
from unittest.mock import patch

def test_upload_document(client):
    # Register and get token
    reg = client.post("/api/v1/auth/register", json={"email": "test@example.com", "password": "password123", "full_name": "Test User"})
    token = reg.json()["access_token"]
    
    # Mock the background process and document writing
    with patch("app.routes.documents._process_in_background"), patch("builtins.open", create=True):
        files = {"file": ("test.txt", b"This is a test document.", "text/plain")}
        data = {"tags": "test,doc", "access_level": "public"}
        
        response = client.post(
            "/api/v1/documents/upload",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )
        
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["filename"] == "test.txt"
    assert res_data["file_type"] == "txt"
    assert "test" in res_data["tags"]

def test_list_documents(client):
    reg = client.post("/api/v1/auth/register", json={"email": "test@example.com", "password": "password123", "full_name": "Test User"})
    token = reg.json()["access_token"]
    
    with patch("app.routes.documents._process_in_background"), patch("builtins.open", create=True):
        files = {"file": ("test.txt", b"This is a test document.", "text/plain")}
        client.post(
            "/api/v1/documents/upload",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data={"tags": "test", "access_level": "public"}
        )
        
    response = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 1
    assert docs[0]["filename"] == "test.txt"
