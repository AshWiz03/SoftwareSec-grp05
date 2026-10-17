import requests
from rmap import RMAPClient
import os
import re
os.makedirs("/home/softsec/rmap_pdfs", exist_ok=True)


GROUPS = [f"{i:02d}" for i in range(1, 35)]

for GROUP in GROUPS:
    BASE = f"http://softsec-group-{GROUP}.dsv.local.su.se:5000"
    print(f"\n=== Group {GROUP} ===")
    
    try:
        r = requests.get(f"{BASE}/healthz", timeout=3)
        if r.status_code != 200:
            print(f"  Not healthy, skipping")
            continue

      
        key_path = f"/home/softsec/SoftwareSec-grp05/server/keys/Group_{GROUP}.asc"
        if not os.path.exists(key_path):
            print(f"  No public key, skipping")
            continue

        client = RMAPClient(
            identity="Group_05",
            client_private_key_path="/home/softsec/SoftwareSec-grp05/server/keys/server_priv.asc",
            server_public_key_path=key_path,
            passphrase="group05"
        )

        msg1 = client.build_msg1()
        r = requests.post(f"{BASE}/api/rmap-initiate", json=msg1, timeout=10)
        print(f"  rmap-initiate: {r.status_code}")
        if r.status_code != 200:
            print(f"  Failed: {r.text[:80]}")
            continue

        client.process_resp1(r.json())

        msg2 = client.build_msg2()
        r = requests.post(f"{BASE}/api/rmap-get-link", json=msg2, timeout=10)
        print(f"  rmap-get-link: {r.status_code}")
        if r.status_code != 200:
            print(f"  Failed: {r.text[:80]}")
            continue

        link = client.process_resp2(r.json())
        print(f"  Link: {link}")

        if link.startswith("/api/"):
            download_url = f"{BASE}{link}"
        elif link.startswith("http"):
            
        
            download_url = re.sub(
                r'(softsec-group-\d+\.dsv\.local\.su\.se)(:\d+)?',
                rf'softsec-group-{GROUP}.dsv.local.su.se:5000',
                link
            )
        else:
            download_url = f"{BASE}/api/get-version/{link}"

        r = requests.get(download_url, timeout=15)
        print(f"  Download: {r.status_code}, {len(r.content)} bytes")

        if r.status_code == 200 and r.content[:4] == b'%PDF':
            fname = f"/home/softsec/rmap_pdfs/group_{GROUP}_watermarked.pdf"
            with open(fname, "wb") as f:
                f.write(r.content)
            print(f"  Saved ✓")
        else:
            print(f"  Not a valid PDF")

    except Exception as e:
        print(f"  Error: {e}")

print("\n=== Done ===")
for f in sorted(os.listdir("/home/softsec/rmap_pdfs")):
    size = os.path.getsize(f"/home/softsec/rmap_pdfs/{f}")
    print(f"  {f} ({size:,} bytes)")
