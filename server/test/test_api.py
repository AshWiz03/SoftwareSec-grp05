from server import app
import pytest

BASE_URL = "http://localhost:5000"
rmap_initiate_endpoint = "/api/rmap-initiate"
rmap_getLink_endpoint = "/api/rmap-get-link"
#CLIENT
@pytest.fixture
def client():
    app.config["TESTING"] = True
    return test_all_rmap_invalid_requests(app.test_client())

def test_healthz_route():
    client = app.test_client()
    resp = client.get("/healthz")

    assert resp.status_code == 200
    assert resp.is_json
    

## RMAP INITIATE ##

#TEST EMPTY BODY
def test_rmap_initiate_missing_body(client):
    resp = client.post("/api/rmap-initiate")

    assert resp.status_code == 400
    assert resp.is_json
    assert resp.get_json()["error"] == "missing payload"

##TEST EMPTY JSON
def test_rmap_initiate_empty_json(client):
    resp = client.post("/api/rmap-initiate", json={})

    assert resp.status_code == 400
    assert resp.get_json()["error"] == "missing payload"
#TEST PAYLOAD IS NONE
def test_rmap_initiate_payload_is_none(client):
    resp = client.post(
        "/api/rmap-initiate",
        json={"payload": None}
    )

    assert resp.status_code == 400
    assert resp.is_json
    assert resp.get_json()["error"] == "invalid request"
#TEST EMPTY PAYLOAD
def test_rmap_initiate_payload_is_empty(client):
    resp = client.post(
        "/api/rmap-initiate",
        json={"payload": ""}
    )

    assert resp.status_code == 400
    assert resp.is_json
    assert resp.get_json()["error"] == "invalid request"
#TEST INVALID PAYLOAD
def test_rmap_initiate_invalid_payload(client):
    resp = client.post(
        "/api/rmap-initiate",
        json={"payload": "this-is-not-a-valid-rmap-message"}
    )

    assert resp.status_code == 400
    assert resp.is_json
    assert resp.get_json()["error"] == "invalid request"



#TEST CALL
def test_all_rmap_invalid_requests(client):
    test_rmap_initiate_missing_body(client)
    test_rmap_initiate_empty_json(client)
    test_rmap_initiate_payload_is_none(client)
    test_rmap_initiate_payload_is_empty(client)
    test_rmap_initiate_invalid_payload(client)