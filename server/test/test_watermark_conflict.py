"""
test_watermark_conflict.py - Regression test for the 503-vs-409 fuzzing
finding: a duplicate watermark version (conflicting link) must return a
clean 409 Conflict, not a misleading 503 Service Unavailable.

Note: this currently relies on identical (document, intended_for) inputs
producing a colliding link under the link-generation scheme in place as
of 2026-10-15. If that scheme changes, this test's setup may need
revisiting to still reliably trigger a conflict.
"""
import uuid

import requests


def test_duplicate_watermark_returns_conflict_not_service_unavailable(
    base_url, auth_headers, uploaded_document
):
    unique_recipient = f"conflict-test-recipient-{uuid.uuid4().hex}"
    payload = {
        "method": "HMAC-Signed",
        "position": "na",
        "key": "conflicttestkey",
        "secret": "conflicttestsecret",
        "intended_for": unique_recipient,
    }

    first = requests.post(
        f"{base_url}/api/create-watermark/{uploaded_document}",
        headers=auth_headers,
        json=payload,
    )
    assert first.status_code == 201, first.text

    second = requests.post(
        f"{base_url}/api/create-watermark/{uploaded_document}",
        headers=auth_headers,
        json=payload,
    )
    assert second.status_code == 409, (
        f"Expected 409 Conflict for a duplicate watermark request, "
        f"got {second.status_code}: {second.text}"
    )