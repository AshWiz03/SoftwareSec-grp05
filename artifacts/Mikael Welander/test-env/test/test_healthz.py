import pytest
import requests

def test_healthz_route(base_url):
    resp = requests.get(f"{base_url}/healthz")

    assert resp.status_code == 200
    assert "application/json" in resp.headers.get("Content-Type", "") # IS JSON
    assert resp.json()["message"] == "The server is up and running."