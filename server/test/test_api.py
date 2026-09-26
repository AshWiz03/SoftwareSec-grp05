import pytest
import requests


#CLIENT
@pytest.fixture
#def client():
    #app.config["TESTING"] = True
    #return app.test_client()

def test_healthz_route(base_url):
    resp = requests.get(f"{base_url}/healthz")
    #client = app.test_client()
    #resp = client.get("/healthz")

    assert resp.status_code == 200
    assert "application/json" in resp.headers.get("Content-Type", "") # IS JSON
    assert resp.json()["message"] == "The server is up and running."
    

## RMAP INITIATE ##

#TEST EMPTY BODY
def test_rmap_initiate_missing_body(base_url):
    resp = requests.post(f"{base_url}/api/rmap-initiate")

    assert resp.status_code == 400
    assert "application/json" in resp.headers.get("Content-Type", "")
    assert resp.json()["error"] == "missing payload"

##TEST EMPTY JSON
def test_rmap_initiate_empty_json(base_url):
    resp = requests.post(f"{base_url}/api/rmap-initiate", json={})

    assert resp.status_code == 400
    assert "application/json" in resp.headers.get("Content-Type", "")
    assert resp.json()["error"] == "missing payload"
#TEST PAYLOAD IS NONE
def test_rmap_initiate_payload_is_none(base_url):
    resp = requests.post(
        f"{base_url}/api/rmap-initiate",
        json={"payload": None}
    )

    assert resp.status_code == 400
    assert "application/json" in resp.headers.get("Content-Type", "")
    assert resp.json()["error"] == "invalid request"
#TEST EMPTY PAYLOAD
def test_rmap_initiate_payload_is_empty(base_url):
    resp = resp = requests.post(
        f"{base_url}/api/rmap-initiate",
        json={"payload": ""}
    )

    assert resp.status_code == 400
    assert "application/json" in resp.headers.get("Content-Type", "")
    assert resp.json()["error"] == "invalid request"
#TEST INVALID PAYLOAD
def test_rmap_initiate_invalid_payload(base_url):
    resp = requests.post(
        f"{base_url}/api/rmap-initiate",
        json={"payload": "this-is-not-a-valid-rmap-message"}
    )

    assert resp.status_code == 400
    assert "application/json" in resp.headers.get("Content-Type", "")
    assert resp.json()["error"] == "invalid request"



#TEST CALL
#def test_all_rmap_invalid_requests(client):
 #   test_rmap_initiate_missing_body(client)
   # test_rmap_initiate_empty_json(client)
   # test_rmap_initiate_payload_is_none(client)
   # test_rmap_initiate_payload_is_empty(client)
   # test_rmap_initiate_invalid_payload(client)