# This script was originally developed as a manual debugging tool to verify the RMAP 
# handshake implementation during development. It has since been superseded by the 
# formal pytest suite in server/test/test_rmap.py, which covers the same handshake 
# flow alongside error cases and CI integration, making this script redundant.
import requests
import json
from rmap import RMAPClient

BASE = "http://localhost:5000"  
client = RMAPClient(
    identity="Group_05",
    client_private_key_path="server/keys/server_priv.asc",  
    server_public_key_path="server/keys/server_pub.asc",
    passphrase="group05"
)


print("=== Step 1: Sending Message 1 to rmap-initiate ===")
msg1 = client.build_msg1()
r = requests.post(f"{BASE}/api/rmap-initiate",
                  json=msg1)
print("Response:", r.text)

if r.status_code != 200:
    print("FAILED at rmap-initiate")
    exit(1)

resp1 = r.json()


print("\n=== Step 2: Processing Response 1 ===")
nonce_client, nonce_server = client.process_resp1(resp1)
print(f"nonceClient: {nonce_client}")
print(f"nonceServer: {nonce_server}")
print(f"Expected link: {client.expected_link}")
print("\n=== Step 3: Sending Message 2 to rmap-get-link ===")
msg2 = client.build_msg2()
r = requests.post(f"{BASE}/api/rmap-get-link",
                  json=msg2)
print("Status:", r.status_code)
print("Response:", r.text)

if r.status_code != 200:
    print("FAILED at rmap-get-link")
    exit(1)

resp2 = r.json().get("payload")

print("\n=== Step 4: Processing Response 2 ===")
link = client.process_resp2(resp2)
print(f"Received link: {link}")
print(f"Expected link: {client.expected_link}")
print(f"Match: {link == client.expected_link}")

print("\n=== Full RMAP handshake complete ===")
print(f"Download watermarked PDF at: {BASE}/api/get-version/{link}")
