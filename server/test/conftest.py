import pytest
import uuid
import requests
import io

def pytest_addoption(parser):
    parser.addoption(
        "--base-url",
        action="store",
        default="http://localhost:5000",
        help="Base URL for the target API server"
    )

@pytest.fixture
def base_url(request):
    return request.config.getoption("--base-url")

@pytest.fixture(autouse=True)
def test_notifier(request):
    # Runs before test execute
    print(f"\n[STARTING] Running test: {request.node.name}...")
    
    yield
    
    # Runs after test finishes
    print(f"[FINISHED] {request.node.name}")

#Creates a throwaway user and returns its credentials
@pytest.fixture
def created_user(base_url):
    run_id = uuid.uuid4().hex[:8]
    creds = {
        "email": f"test_{run_id}@example.com",
        "login": f"test_{run_id}",
        "password": "TestPassword123!",
        "run_id": run_id,
    }
    resp = requests.post(
        f"{base_url}/api/create-user",
        json={k: creds[k] for k in ("email", "login", "password")},
    )
    assert resp.status_code == 201, resp.text
    return creds

#Logs in as the throwaway user and returns the Authorization header
@pytest.fixture
def auth_headers(base_url, created_user):
    resp = requests.post(
        f"{base_url}/api/login",
        json={"email": created_user["email"], "password": created_user["password"]},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['token']}"}

#Uploads a minimal PDF and returns its document id
@pytest.fixture
def uploaded_document(base_url, auth_headers):
    minimal_pdf = _build_minimal_pdf()
    files = {"file": ("test.pdf", io.BytesIO(minimal_pdf), "application/pdf")}
    resp = requests.post(f"{base_url}/api/upload-document", headers=auth_headers, files=files)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]

#Creates a watermarked version and returns its issued link
@pytest.fixture
def created_link(base_url, auth_headers, created_user, uploaded_document):
    payload = {
        "method": "HMAC-Text-Render",
        "intended_for": f"test-recipient-{created_user['run_id']}",
        "secret": "test-secret",
        "key": "test-key",
    }
    resp = requests.post(
        f"{base_url}/api/create-watermark/{uploaded_document}",
        headers=auth_headers,
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["link"]

#BUILD A PDF ON DEMAND
def _build_minimal_pdf() -> bytes:
    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n",
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]
    content = b"BT /F1 12 Tf 20 100 Td (test) Tj ET"
    objects.append(b"5 0 obj\n<< /Length %d >>\nstream\n%s\nendstream\nendobj\n" % (len(content), content))

    header = b"%PDF-1.4\n"
    body, offsets, pos = b"", [], len(header)
    for obj in objects:
        offsets.append(pos)
        body += obj
        pos += len(obj)

    n = len(objects) + 1
    xref = b"xref\n0 %d\n0000000000 65535 f \n" % n
    for off in offsets:
        xref += b"%010d 00000 n \n" % off

    trailer = b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (n, len(header) + len(body))
    return header + body + xref + trailer