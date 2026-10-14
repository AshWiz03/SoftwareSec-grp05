import uuid
import pytest
import requests
from hypothesis import given, settings, strategies as st, HealthCheck


"""
test_fuzz_watermark.py - Property-based fuzzing of the watermark endpoints.

Uses Hypothesis to generate a wide range of malformed/edge-case string
inputs for create-watermark and read-watermark, checking the server never
crashes with an unhandled 500. A 500 means the input reached code that
crashed instead of being validated and rejected cleanly (4xx) or accepted
(2xx). Fixtures (base_url, auth_headers, uploaded_document) come from
conftest.py.
"""
import pytest
import requests
from hypothesis import given, settings, strategies as st, HealthCheck

FUZZ_TEXT = st.text(min_size=0, max_size=300)

FAST_SETTINGS = dict(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)


@settings(**FAST_SETTINGS)
@given(secret=FUZZ_TEXT, key=FUZZ_TEXT, intended_for=FUZZ_TEXT)
def test_fuzz_create_watermark_fields_never_crash(
    base_url, auth_headers, uploaded_document, secret, key, intended_for
):
    resp = requests.post(
        f"{base_url}/api/create-watermark/{uploaded_document}",
        headers=auth_headers,
        json={
            "method": "HMAC-Signed",
            "position": "na",
            "key": key,
            "secret": secret,
            "intended_for": intended_for,
        },
    )
    assert resp.status_code != 500, (
        f"Unhandled server error (500) with "
        f"secret={secret!r} key={key!r} intended_for={intended_for!r}: {resp.text}"
    )


@settings(**FAST_SETTINGS)
@given(method=st.text(min_size=0, max_size=100))
def test_fuzz_create_watermark_unknown_method_never_crashes(
    base_url, auth_headers, uploaded_document, method
):
    resp = requests.post(
        f"{base_url}/api/create-watermark/{uploaded_document}",
        headers=auth_headers,
        json={
            "method": method,
            "position": "na",
            "key": "fuzzkey",
            "secret": "fuzzsecret",
            "intended_for": "fuzz-recipient",
        },
    )
    assert resp.status_code != 500, (
        f"Unhandled server error (500) with method={method!r}: {resp.text}"
    )


@settings(**FAST_SETTINGS)
@given(key=FUZZ_TEXT)
def test_fuzz_read_watermark_wrong_key_never_crashes(
    base_url, auth_headers, uploaded_document, key
):
    create_resp = requests.post(
        f"{base_url}/api/create-watermark/{uploaded_document}",
        headers=auth_headers,
        json={
            "method": "HMAC-Signed",
            "position": "na",
            "key": "realkey",
            "secret": "realsecret",
            "intended_for": f"fuzz-read-recipient-{uuid.uuid4().hex}",
        },
    )
    assert create_resp.status_code == 201

    resp = requests.post(
        f"{base_url}/api/read-watermark/{uploaded_document}",
        headers=auth_headers,
        json={"method": "HMAC-Signed", "position": "na", "key": key},
    )
    assert resp.status_code != 500, (
        f"Unhandled server error (500) with key={key!r}: {resp.text}"
    )

@pytest.mark.manual
@settings(
    max_examples=500,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(secret=FUZZ_TEXT, key=FUZZ_TEXT, intended_for=FUZZ_TEXT)
def test_fuzz_create_watermark_deep_campaign(
    base_url, auth_headers, uploaded_document, secret, key, intended_for
):
    """Deeper campaign for the specialization deliverable.
    Run manually: pytest test/test_fuzz_watermark.py -m manual -v
    """
    resp = requests.post(
        f"{base_url}/api/create-watermark/{uploaded_document}",
        headers=auth_headers,
        json={
            "method": "HMAC-Signed",
            "position": "na",
            "key": key,
            "secret": secret,
            "intended_for": intended_for,
        },
    )
    assert resp.status_code != 500, (
        f"Unhandled server error (500) with "
        f"secret={secret!r} key={key!r} intended_for={intended_for!r}: {resp.text}"
    )