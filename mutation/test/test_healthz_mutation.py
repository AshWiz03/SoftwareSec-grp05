def test_healthz_route(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert "application/json" in resp.headers.get("Content-Type", "")
    assert resp.get_json()["message"] == "The server is up and running."