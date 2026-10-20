import hashlib
import io

from conftest import _build_minimal_pdf

VERSION_KEYS = {"id", "documentid", "link", "intended_for", "secret", "method"}
ALL_VERSION_KEYS = {"id", "documentid", "link", "intended_for", "method"}
DOCUMENT_KEYS = {"id", "name", "creation", "sha256", "size"}

def _upload(client, headers, filename, name=None):
    # Extra uploads beyond the uploaded_document fixture
    data = {"file": (io.BytesIO(_build_minimal_pdf()), filename)}
    if name is not None:
        data["name"] = name
    resp = client.post(
        "/api/upload-document",
        headers=headers,
        data=data,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201, resp.get_data(as_text=True)
    return resp.get_json()["id"]

#LIST DOCUMENTS
def test_list_documents_without_token(client):
    resp = client.get("/api/list-documents")
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "Missing or invalid Authorization header"

def test_list_documents_returns_uploaded_document(client, auth_headers, uploaded_document):
    pdf = _build_minimal_pdf()
 
    resp = client.get("/api/list-documents", headers=auth_headers)
    assert resp.status_code == 200
    docs = resp.get_json()["documents"]
    assert len(docs) == 1
 
    doc = docs[0]
    assert set(doc) == DOCUMENT_KEYS
    assert doc["id"] == uploaded_document
    assert doc["name"] == "test.pdf"
    assert doc["size"] == len(pdf)
    assert doc["sha256"].lower() == hashlib.sha256(pdf).hexdigest()
    assert doc["creation"]

def test_list_documents_returns_all_own_documents(client, auth_headers, uploaded_document):
    second = _upload(client, auth_headers, "second.pdf")
 
    docs = client.get("/api/list-documents", headers=auth_headers).get_json()["documents"]
    assert {d["id"] for d in docs} == {uploaded_document, second}

#LIST VERSIONS
 
def test_list_versions_without_token(client):
    resp = client.get("/api/list-versions/1")
    assert resp.status_code == 401

def test_list_documents_empty_for_new_user(client, auth_headers):
    resp = client.get("/api/list-documents", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json() == {"documents": []}

def test_list_versions_returns_created_version(client, auth_headers, created_user, uploaded_document, created_link):
    resp = client.get(f"/api/list-versions/{uploaded_document}", headers=auth_headers)
    assert resp.status_code == 200
    versions = resp.get_json()["versions"]
    assert len(versions) == 1
 
    v = versions[0]
    assert set(v) == VERSION_KEYS
    assert v["documentid"] == uploaded_document
    assert v["link"] == created_link
    assert v["intended_for"] == f"test-recipient-{created_user['run_id']}"
    assert v["secret"] == "test-secret"
    assert v["method"] == "HMAC-Text-Render"


#LIST ALL VERSIONS
def test_list_all_versions_without_token(client):
    resp = client.get("/api/list-all-versions")
    assert resp.status_code == 401

def test_list_all_versions_returns_created_version(client, auth_headers, uploaded_document, created_link):
    resp = client.get("/api/list-all-versions", headers=auth_headers)
    assert resp.status_code == 200
    versions = resp.get_json()["versions"]
    assert len(versions) == 1
 
    v = versions[0]
    assert set(v) == ALL_VERSION_KEYS  # the secret is not included in this listing
    assert v["documentid"] == uploaded_document
    assert v["link"] == created_link
    assert v["method"] == "HMAC-Text-Render"