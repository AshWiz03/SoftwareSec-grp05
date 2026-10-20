import pytest
import os
from rmap import RMAPClient
from server import create_app

KEYS_DIR = os.environ.get("KEYS_DIR", "/app/keys")

## RMAP INITIATE ##

def test_rmap_initiate_missing_body(client):
    resp = client.post("/api/rmap-initiate")

    assert resp.status_code == 400
    assert "application/json" in resp.headers.get("Content-Type", "")
    assert resp.get_json()["error"] == "missing payload"


def test_rmap_initiate_empty_json(client):
    resp = client.post("/api/rmap-initiate", json={})

    assert resp.status_code == 400
    assert "application/json" in resp.headers.get("Content-Type", "")
    assert resp.get_json()["error"] == "missing payload"


def test_rmap_initiate_payload_is_none(client):
    resp = client.post("/api/rmap-initiate", json={"payload": None})

    assert resp.status_code == 400
    assert "application/json" in resp.headers.get("Content-Type", "")
    assert resp.get_json()["error"] == "invalid request"


def test_rmap_initiate_payload_is_empty(client):
    resp = client.post("/api/rmap-initiate", json={"payload": ""})

    assert resp.status_code == 400
    assert "application/json" in resp.headers.get("Content-Type", "")
    assert resp.get_json()["error"] == "invalid request"


def test_rmap_initiate_invalid_payload(client):
    resp = client.post(
        "/api/rmap-initiate",
        json={"payload": "this-is-not-a-valid-rmap-message"},
    )

    assert resp.status_code == 400
    assert "application/json" in resp.headers.get("Content-Type", "")
    assert resp.get_json()["error"] == "invalid request"

def test_full_rmap_handshake_flow(client, uploaded_document):

    print("\nStep 1: Initializing RMAP Client")

    rmap_Client = RMAPClient(
        identity=os.environ.get("RMAP_TEST_IDENTITY", "test_group_pub"),
        client_private_key_path=os.path.join(KEYS_DIR, "test_group_priv.asc"),
        server_public_key_path=os.path.join(KEYS_DIR, "server_pub.asc"),
        passphrase=os.environ.get("CLIENT_KEY_PASSPHRASE", "testpassphrase")
    )

    msg1 = rmap_Client.build_msg1()

    resp1 = client.post("/api/rmap-initiate", json=msg1)
    assert resp1.status_code == 200, resp1.get_data(as_text=True)

    resp1_json = resp1.get_json()

    assert "payload" in resp1_json

    nonce_client, nonce_server = rmap_Client.process_resp1(resp1_json)
    assert nonce_client is not None and nonce_server is not None

    msg2 = rmap_Client.build_msg2()

    resp2 = client.post("/api/rmap-get-link", json=msg2)

    assert resp2.status_code == 200, resp2.get_data(as_text=True)
    resp2_json = resp2.get_json()
    assert "payload" in resp2_json

    link_token = rmap_Client.process_resp2(resp2_json)
    
    assert link_token == rmap_Client.expected_link
    print("\nFINISHED ASSERTIONS")
