import pytest
import requests
import uuid

# User credentials
def _creds():
    run_id = uuid.uuid4().hex[:8]
    return {
        "email": f"test_{run_id}@example.com",
        "login": f"test_{run_id}",
        "password": "TestPassword123!",
    }

#AUTH TOKEN TEST
def test_upload_without_token(base_url):
    resp = requests.post(f"{base_url}/api/upload-document", files={"file": ("x.pdf", b"%PDF-1.4", "application/pdf")})
    assert resp.status_code == 401, resp.text
    
def test_upload_fabricated_token(base_url):
    resp = requests.post(
        f"{base_url}/api/upload-document",
        headers={"Authorization": "Bearer not.a.real.token"},
        files={"file": ("x.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert resp.status_code == 401, resp.text


#CREATE USER

def test_create_user_success(base_url):
    resp = requests.post(f"{base_url}/api/create-user", json=_creds())
    assert resp.status_code == 201, resp.text

def test_create_user_invalid_email_format(base_url):
    creds = _creds()
    creds["email"] = "not-an-email"
    resp = requests.post(f"{base_url}/api/create-user", json=creds)
    assert resp.status_code == 400, resp.text

def test_create_user_invalid_pwd_format(base_url):
    creds = _creds()
    creds["password"] = "no1"
    resp = requests.post(f"{base_url}/api/create-user", json=creds)
    assert resp.status_code == 400, resp.text

def test_create_user_missing_fields(base_url):
    resp = requests.post(f"{base_url}/api/create-user", json={"email": "x@example.com"})
    assert resp.status_code == 400, resp.text

def test_create_user_duplicate_email(base_url, created_user):
    resp = requests.post(f"{base_url}/api/create-user", json={
        "email": created_user["email"],
        "login": f"different_{uuid.uuid4().hex[:8]}",
        "password": "TestPassword123!",
    })
    assert resp.status_code in (400, 409), resp.text

## LOGIN ##

def test_login_success(base_url, created_user):
    resp = requests.post(f"{base_url}/api/login", json={
        "email": created_user["email"], "password": created_user["password"],
    })
    assert resp.status_code == 200, resp.text
    assert "token" in resp.json()

def test_login_nonexistent_user(base_url):
    resp = requests.post(f"{base_url}/api/login", json={
        "email": "nobody@example.com", "password": "iamcrazy",
    })
    assert resp.status_code == 401, resp.text

def test_login_wrong_password(base_url, created_user):
    resp = requests.post(f"{base_url}/api/login", json={
        "email": created_user["email"], "password": "WrongPassword1234!",
    })
    assert resp.status_code == 401, resp.text

def test_login_missing_fields(base_url):
    resp = requests.post(f"{base_url}/api/login", json={"email": "x@example.com"})
    assert resp.status_code == 400, resp.text