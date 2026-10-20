import watermarking_utils as WMUtils

READ_PAYLOAD = {"method": "HMAC-Text-Render", "key": "test-key"}

#GET WATERMARKING METHODS
def test_get_watermarking_methods_lists_all_methods(client):
    resp = client.get("/api/get-watermarking-methods")
    assert resp.status_code == 200
    body = resp.get_json()
 
    names = [m["name"] for m in body["methods"]]
    assert names == list(WMUtils.METHODS)


#READ WATERMARK

def test_read_watermark_without_token(client):
    resp = client.post("/api/read-watermark/1", json=READ_PAYLOAD)
    assert resp.status_code == 401

def test_read_watermark_returns_secret(client, auth_headers, uploaded_document, created_link):
    resp = client.post(f"/api/read-watermark/{uploaded_document}", headers=auth_headers, json=READ_PAYLOAD)
    assert resp.status_code == 201, resp.get_data(as_text=True)
    assert resp.get_json() == {
        "documentid": uploaded_document,
        "secret": "test-secret",
        "method": "HMAC-Text-Render",
        "position": None,
    }
