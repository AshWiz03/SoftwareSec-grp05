import pytest
import io
import uuid
from server import create_app


@pytest.fixture
def app():
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    yield flask_app
    engine = flask_app.config.get("_ENGINE")
    if engine is not None:
        engine.dispose()

@pytest.fixture
def new_creds():
    return _creds()

@pytest.fixture
def client(app):
    return app.test_client()


def _creds():
    run_id = uuid.uuid4().hex[:8]
    return {
        "email": f"test_{run_id}@example.com",
        "login": f"test_{run_id}",
        "password": "TestPassword123!",
        "run_id": run_id,
    }


@pytest.fixture
def created_user(client, new_creds):
    resp = client.post(
        "/api/create-user",
        json={k: new_creds[k] for k in ("email", "login", "password")},
    )
    assert resp.status_code == 201, resp.get_data(as_text=True)
    return new_creds


@pytest.fixture
def auth_headers(client, created_user):
    resp = client.post(
        "/api/login",
        json={"email": created_user["email"], "password": created_user["password"]},
    )
    assert resp.status_code == 200, resp.get_data(as_text=True)
    return {"Authorization": f"Bearer {resp.get_json()['token']}"}

@pytest.fixture
def uploaded_document(client, auth_headers):
    minimal_pdf = _build_minimal_pdf()
    resp = client.post(
        "/api/upload-document",
        headers=auth_headers,
        data={"file": (io.BytesIO(minimal_pdf), "test.pdf")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201, resp.get_data(as_text=True)
    return resp.get_json()["id"]

@pytest.fixture
def created_link(client, auth_headers, created_user, uploaded_document):
    payload = {
        "method": "HMAC-Text-Render",
        "intended_for": f"test-recipient-{created_user['run_id']}",
        "secret": "test-secret",
        "key": "test-key",
    }
    resp = client.post(
        f"/api/create-watermark/{uploaded_document}",
        headers=auth_headers,
        json=payload,
    )
    assert resp.status_code == 201, resp.get_data(as_text=True)
    return resp.get_json()["link"]

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