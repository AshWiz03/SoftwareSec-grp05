import pytest
import requests

# TEST get-version

def test_get_version_fabricated_link(base_url):
    fake_link = "023c6e9d1a3f97884039ab1c89b3d3e"
    resp = requests.get(
            f"{base_url}/api/get-version/{fake_link}",
        )
    jsonData = resp.json()
    assert resp.status_code == 404

    assert jsonData.get("error") == "document not found"


def test_get_version_valid_link(base_url, created_link):
    resp = requests.get(f"{base_url}/api/get-version/{created_link}")

    assert resp.status_code == 200
    assert resp.headers.get("Cache-Control") == "private, max-age=0"
    assert resp.headers.get("Content-Type", "").startswith("application/pdf")

def test_get_version_oversized_link(base_url):
    oversized_link = "a" * 50000
    resp = requests.get(f"{base_url}/api/get-version/{oversized_link}")

    assert resp.status_code != 500, "handler crashed on oversized input"

    body_text = resp.text.lower()
    for leak_marker in ("sql", "column", "mysql", "traceback", "data too long"):
        assert leak_marker not in body_text, f"response leaked internal detail: {leak_marker!r}"