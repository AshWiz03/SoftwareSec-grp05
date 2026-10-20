def test_get_document_success(client, auth_headers, uploaded_document):
    resp = client.get(
        f"/api/get-document/{uploaded_document}",
        headers=auth_headers,
    )
    assert resp.status_code == 200


    assert resp.data[:4] == b"%PDF"


def test_get_document_no_auth(client, uploaded_document, auth_headers):
    resp = client.get(f"/api/get-document/{uploaded_document}")

    assert resp.status_code == 401


def test_get_document_wrong_user(client, new_creds, uploaded_document):
    
    client.post("/api/create-user", json={k: new_creds[k] for k in ("email", "login", "password")})

    login_resp = client.post("/api/login", json={"email": new_creds["email"], "password": new_creds["password"]})
    
    other_headers = {"Authorization": f"Bearer {login_resp.get_json()['token']}"}
    resp = client.get(f"/api/get-document/{uploaded_document}", headers=other_headers)

    assert resp.status_code == 404
