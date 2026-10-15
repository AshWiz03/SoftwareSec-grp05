import io
import uuid


#AUTH TOKEN

def test_upload_without_token(client):
    resp = client.post(
        "/api/upload-document",
        data={"file": (io.BytesIO(b"%PDF-1.4"), "x.pdf")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 401, resp.get_data(as_text=True)


def test_upload_fabricated_token(client):
    resp = client.post(
        "/api/upload-document",
        headers={"Authorization": "Bearer not.a.real.token"},
        data={"file": (io.BytesIO(b"%PDF-1.4"), "x.pdf")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 401, resp.get_data(as_text=True)


#CREATE USER

def test_create_user_success(client, new_creds):
    #payload = {var: new_creds[var] for var in ("email", "login", "password")},
    resp = client.post("/api/create-user", json=new_creds)
    assert resp.status_code == 201, resp.get_data(as_text=True)


def test_create_user_invalid_email_format(client, new_creds):
    #payload = {var: new_creds[var] for var in ("email", "login", "password")},
    #payload["email"] = "not-an-email.se"
    new_creds["email"] = "not-an-email.se"
    resp = client.post("/api/create-user", json=new_creds)
    assert resp.status_code == 400, resp.get_data(as_text=True)


def test_create_user_invalid_pwd_format(client, new_creds):
    #creds["password"] = "no1"
    new_creds["password"] = "no1"
    resp = client.post("/api/create-user", json=new_creds)
    assert resp.status_code == 400, resp.get_data(as_text=True)


def test_create_user_missing_fields(client):
    resp = client.post("/api/create-user", json={"email": "x@example.com"})
    assert resp.status_code == 400, resp.get_data(as_text=True)


def test_create_user_duplicate_email(client, created_user):
    resp = client.post("/api/create-user", json={
        "email": created_user["email"],
        "login": f"different_{uuid.uuid4().hex[:8]}",
        "password": "TestPassword123!",
    })
    assert resp.status_code in (400, 409), resp.get_data(as_text=True)


#LOGIN

def test_login_success(client, created_user):
    resp = client.post("/api/login", json={
        "email": created_user["email"], "password": created_user["password"],
    })
    assert resp.status_code == 200, resp.get_data(as_text=True)
    assert "token" in resp.get_json()


def test_login_nonexistent_user(client):
    resp = client.post("/api/login", json={
        "email": "nobody@example.com", "password": "iamcrazy",
    })
    assert resp.status_code == 401, resp.get_data(as_text=True)


def test_login_wrong_password(client, created_user):
    resp = client.post("/api/login", json={
        "email": created_user["email"], "password": "WrongPassword1234!",
    })
    assert resp.status_code == 401, resp.get_data(as_text=True)


def test_login_missing_fields(client):
    resp = client.post("/api/login", json={"email": "x@example.com"})
    assert resp.status_code == 400, resp.get_data(as_text=True)