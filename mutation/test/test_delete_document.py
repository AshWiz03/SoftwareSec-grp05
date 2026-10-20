def test_delete_document_success(client, auth_headers, uploaded_document):
    resp = client.delete(
        f"/api/delete-document/{uploaded_document}",
        headers=auth_headers,
    )
    assert resp.status_code == 200


def test_delete_document_no_auth(client, uploaded_document, auth_headers):
    resp = client.delete(f"/api/delete-document/{uploaded_document}")
    assert resp.status_code == 401


def test_delete_document_wrong_user(client, uploaded_document, auth_headers):
    import uuid
    run_id = uuid.uuid4().hex[:8]
    other_creds = {
        "email": f"other_{run_id}@example.com",
        "login": f"other_{run_id}",
        "password": "TestPassword123!",
    }
    client.post("/api/create-user", json=other_creds)
    login_resp = client.post("/api/login", json={
        "email": other_creds["email"],
        "password": other_creds["password"],
    })
    assert login_resp.status_code == 200
    other_headers = {"Authorization": f"Bearer {login_resp.get_json()['token']}"}
    resp = client.delete(f"/api/delete-document/{uploaded_document}", headers=other_headers)
    assert resp.status_code in (403, 404)


def test_delete_document_gone_after_deletion(client, auth_headers, uploaded_document):
    client.delete(f"/api/delete-document/{uploaded_document}", headers=auth_headers)
    resp = client.get(f"/api/get-document/{uploaded_document}", headers=auth_headers)
    assert resp.status_code == 404
