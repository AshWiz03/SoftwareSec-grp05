import pytest
import requests
import os
from rmap import RMAPClient

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

# TEST FULL RMAP HANSHAKE
def test_full_rmap_handshake_flow(base_url):
    print("\nStep 1: Initializing RMAP Client")
 
    # Locate the keys directory relative to this test file (server/keys)
    test_dir = os.path.dirname(os.path.abspath(__file__))
    keys_dir = os.path.abspath(os.path.join(test_dir, "..", "keys"))
 
    client_priv_key = os.path.join(keys_dir, "test_group_priv.asc") # test client priv key 
    server_pub_key = os.path.join(keys_dir, "server_pub.asc") 

    identity = os.environ.get("RMAP_TEST_IDENTITY", "test_group_pub")
    passphrase = os.environ.get("CLIENT_KEY_PASSPHRASE", "testpassphrase")
 
    client = RMAPClient(
        identity=identity,
        client_private_key_path=client_priv_key,
        server_public_key_path=server_pub_key,
        passphrase=passphrase,
    )
 
    print(f"Using identity: '{identity}'")
 
    #Step 2 & 3: Initiate Handshake (/api/rmap-initiate)
    print("Step 2: Building Message 1")
    msg1 = client.build_msg1()
 
    print("Step 3: Sending POST /api/rmap-initiate")
    resp1 = requests.post(f"{base_url}/api/rmap-initiate", json=msg1)
 
    assert (resp1.status_code == 200), f"Initiate failed [{resp1.status_code}]: {resp1.text}"
    resp1_json = resp1.json()
    assert "payload" in resp1_json, "Response 1 missing 'payload' key"
 
    #Step 4 & 5: Process Response 1, build & send Message 2
    print("Step 4: Processing Response 1 & Building Message 2")
    nonce_client, nonce_server = client.process_resp1(resp1_json)
    print(f"nonceClient: {nonce_client}")
    print(f"nonceServer: {nonce_server}")
    print(f"Expected link: {client.expected_link}")
 
    msg2 = client.build_msg2()
 
    print("Step 5: Sending POST /api/rmap-get-link")
    resp2 = requests.post(f"{base_url}/api/rmap-get-link", json=msg2)
 
    assert (resp2.status_code == 200), f"Get Link failed [{resp2.status_code}]: {resp2.text}"
    resp2_json = resp2.json()
    assert "payload" in resp2_json, "Response 2 missing 'payload' key"
 
    #Step 6: Decrypt Final Response
    print("Step 6: Decrypting Final Link Response")
    link_token = client.process_resp2(resp2_json.get("payload"))
 
    assert link_token is not None, "Failed to extract link token from response"
    assert link_token == client.expected_link, (f"Link mismatch: got {link_token}, expected {client.expected_link}")

    print(f"\n[SUCCESS] RMAP Full Handshake completed! Obtained link: {link_token}")
