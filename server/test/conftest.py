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

@pytest.fixture
def created_link(base_url):
    # Create a throwaway user
    run_id = uuid.uuid4().hex[:8]
    creds = {
        "email": f"test_{run_id}@example.com",
        "login": f"test_{run_id}",
        "password": "TestPassword123!", 
    }
    respCreateUser = requests.post(f"{base_url}/api/create-user", json=creds)
    assert respCreateUser.status_code == 201, respCreateUser.text

    #Log in
    respLogin = requests.post(f"{base_url}/api/login",
                       json={"email": creds["email"], "password": creds["password"]})
    assert respLogin.status_code == 200, respLogin.text
    headers = {"Authorization": f"Bearer {respLogin.json()['token']}"}

    #Upload a PDF
    minimal_pdf = _build_minimal_pdf()
    files = {"file": ("test.pdf", io.BytesIO(minimal_pdf), "application/pdf")}
    respUpload = requests.post(f"{base_url}/api/upload-document", headers=headers, files=files)
    assert respUpload.status_code == 201, respUpload.text
    doc_id = respUpload.json()["id"]

    #Create a watermark to get a real, issued link
    payload = {
        "method": "HMAC-Text-Render",  
        "intended_for": f"test-recipient-{run_id}",
        "secret": "test-secret",
        "key": "test-key",
    }
    respWatermark = requests.post(f"{base_url}/api/create-watermark/{doc_id}", headers=headers, json=payload)
    assert respWatermark.status_code == 201, respWatermark.text
    return respWatermark.json()["link"]

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