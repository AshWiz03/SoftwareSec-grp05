def test_get_version_fabricated_link(client):
    resp = client.get("/api/get-version/023c6e9d1a3f97884039ab1c89b3d3e")
    assert resp.status_code == 404
    assert resp.get_json().get("error") == "document not found"


def test_get_version_valid_link(client, created_link):
    resp = client.get(f"/api/get-version/{created_link}")
    assert resp.status_code == 200
    assert resp.headers.get("Cache-Control") == "private, max-age=0"
    assert resp.headers.get("Content-Type", "").startswith("application/pdf")


def test_get_version_oversized_link(client):
    resp = client.get(f"/api/get-version/{'a' * 50000}")
    assert resp.status_code != 500, "handler crashed on oversized input"
    body_text = resp.get_data(as_text=True).lower()
    for leak_marker in ("sql", "column", "mysql", "traceback", "data too long"):
        assert leak_marker not in body_text, f"response leaked internal detail: {leak_marker!r}"