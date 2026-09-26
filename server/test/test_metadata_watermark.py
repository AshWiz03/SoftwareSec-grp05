import io
import uuid

import fitz

from server import app


def _make_test_pdf() -> bytes:
    doc = fitz.open()
    doc.new_page()
    return doc.write()


def _register_and_login(client):
    suffix = uuid.uuid4().hex[:8]
    email = f"pytest_{suffix}@example.com"
    password = "TestPass123!"

    resp = client.post("/api/create-user", json={
        "login": f"pytest_{suffix}",
        "password": password,
        "email": email,
    })
    assert resp.status_code == 201

    resp = client.post("/api/login", json={
        "email": email,
        "password": password,
    })
    assert resp.status_code == 200
    token = resp.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}, suffix


def _upload_test_document(client, headers):
    data = {
        "file": (io.BytesIO(_make_test_pdf()), "pytest_test.pdf"),
        "name": "pytest_test.pdf",
    }
    resp = client.post(
        "/api/upload-document",
        data=data,
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201
    return resp.get_json()["id"]


def test_metadata_secret_roundtrip():
    client = app.test_client()
    headers, suffix = _register_and_login(client)
    doc_id = _upload_test_document(client, headers)

    create_resp = client.post(
        f"/api/create-watermark/{doc_id}",
        json={
            "method": "metadata-secret",
            "position": "na",
            "key": "pytestkey123",
            "secret": "pytest-secret",
            "intended_for": f"pytest-run-{suffix}",
        },
        headers=headers,
    )
    assert create_resp.status_code == 201

    read_resp = client.post(
        f"/api/read-watermark/{doc_id}",
        json={
            "method": "metadata-secret",
            "position": "na",
            "key": "pytestkey123",
        },
        headers=headers,
    )
    assert read_resp.status_code == 201
    assert read_resp.get_json()["secret"] == "pytest-secret"


def test_metadata_secret_wrong_key_rejected():
    client = app.test_client()
    headers, suffix = _register_and_login(client)
    doc_id = _upload_test_document(client, headers)

    client.post(
        f"/api/create-watermark/{doc_id}",
        json={
            "method": "metadata-secret",
            "position": "na",
            "key": "correct-key",
            "secret": "pytest-secret",
            "intended_for": f"pytest-run-2-{suffix}",
        },
        headers=headers,
    )

    bad_resp = client.post(
        f"/api/read-watermark/{doc_id}",
        json={
            "method": "metadata-secret",
            "position": "na",
            "key": "wrong-key",
        },
        headers=headers,
    )
    assert bad_resp.status_code == 400
