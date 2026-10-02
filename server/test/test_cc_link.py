"""
Task 2 Empirical Test — FCS_COP.1 Link Generation
===================================================
Tests whether a watermark access link can be reconstructed offline
by a party who knows the document name and intended_for value,
without going through the normal issuance flow as the document owner.

T.LINK_GUESS: can an unauthorized party predict/reconstruct a valid link?
"""

import hashlib
import time
import requests
import pytest
from werkzeug.utils import secure_filename

BASE_URL = "http://localhost:5000"

@pytest.fixture(autouse=True)
def _use_base_url(base_url):
    global BASE_URL
    BASE_URL = base_url


@pytest.fixture
def auth_token():
    """Get a valid auth token for testing."""
    requests.post(f"{BASE_URL}/api/create-user", json={
        "login": "sfr_tester",
        "password": "SFRtest123456!",
        "email": "sfr_tester@test.com"
    })
    r = requests.post(f"{BASE_URL}/api/login", json={
        "email": "sfr_tester@test.com",
        "password": "SFRtest123456!"
    })
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["token"]


@pytest.fixture
def uploaded_doc(auth_token, tmp_path):
    """
    Upload a minimal valid PDF with a unique name per test run.
    Timestamp suffix ensures no two test runs share the same document name,
    which prevents SHA1 collisions from causing DB unique constraint errors.
    """
    # Unique name per test run — critical for avoiding SHA1 DB collisions
    unique_name = f"sfr_test_{int(time.time() * 1000)}"

    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
        b"xref\n0 4\n"
        b"0000000000 65535 f\n"
        b"0000000009 00000 n\n"
        b"0000000058 00000 n\n"
        b"0000000115 00000 n\n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n190\n%%EOF"
    )
    pdf_file = tmp_path / f"{unique_name}.pdf"
    pdf_file.write_bytes(pdf_content)

    r = requests.post(
        f"{BASE_URL}/api/upload-document",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": (f"{unique_name}.pdf", pdf_file.read_bytes(), "application/pdf")},
        data={"name": unique_name}
    )
    assert r.status_code == 201, f"Upload failed: {r.text}"
    return r.json()


class TestFCSCOP1LinkGeneration:
    """
    FCS_COP.1 — Link Generation Security

    Tests that watermark links cannot be reconstructed from observable inputs.
    Before fix: links were SHA1(document_name__intended_for) — fully predictable.
    After fix: links use secrets.token_hex(32) — cryptographically unpredictable.
    """

    def test_link_is_not_predictable_from_document_name_and_intended_for(
        self, auth_token, uploaded_doc
    ):
        """
        CORE TEST — directly addresses T.LINK_GUESS.

        Prior to fix, link = SHA1(f"{doc_name}__{intended_for}.pdf")
        This test proves that the current implementation does NOT use
        this predictable scheme — the computed SHA1 must NOT match
        the server-issued link.

        If this test FAILS (SHA1 matches), T.LINK_GUESS is exploitable.
        If this test PASSES (SHA1 doesn't match), the predictable scheme
        is no longer in use.
        """
        doc_id = uploaded_doc["id"]
        doc_name = uploaded_doc["name"]

        # Unique intended_for per test run — avoids SHA1 DB collision
        intended_for = f"sfr_test_recipient_{int(time.time() * 1000)}"

        # Step 1: Create a watermark legitimately
        r = requests.post(
            f"{BASE_URL}/api/create-watermark/{doc_id}",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "method": "HMAC-Signed",
                "key": "testkey",
                "secret": "testsecret",
                "intended_for": intended_for
            }
        )
        assert r.status_code == 201, f"Watermark creation failed: {r.text}"
        real_link = r.json()["link"]
        print(f"\nServer-issued link:    {real_link}")

        # Step 2: Attempt to reconstruct the link offline using the
        # KNOWN VULNERABLE pattern: SHA1(document_name__intended_for.pdf)
        intended_slug = secure_filename(intended_for)
        candidate = f"{doc_name}__{intended_slug}.pdf"
        predicted_link = hashlib.sha1(candidate.encode("utf-8")).hexdigest()
        print(f"Predicted link (SHA1): {predicted_link}")
        print(f"Match: {real_link == predicted_link}")

        # Step 3: Assert the prediction FAILS — if it matches,
        # T.LINK_GUESS is exploitable
        assert real_link != predicted_link, (
            f"SECURITY VIOLATION — FCS_COP.1 FAILS: "
            f"Link was reconstructed offline using SHA1(name__intended_for). "
            f"T.LINK_GUESS is exploitable. "
            f"Predicted: {predicted_link}, Actual: {real_link}"
        )
        print("FCS_COP.1 PASS: Link is not predictable from observable inputs.")

    def test_two_watermarks_same_inputs_produce_different_links(
        self, auth_token, uploaded_doc
    ):
        """
        Tests that creating two watermarks with identical inputs produces
        different links — confirming randomness in link generation.

        A deterministic scheme (like SHA1) would produce identical links
        for identical inputs. A CSPRNG produces different links every time.

        Note: if SHA1 is still in use, the second call will return 503
        (DB unique constraint violation) — itself evidence of determinism.
        """
        doc_id = uploaded_doc["id"]

        # Unique intended_for so first call doesn't collide with previous tests
        intended_for = f"same_recipient_{int(time.time() * 1000)}"

        links = []
        for i in range(2):
            r = requests.post(
                f"{BASE_URL}/api/create-watermark/{doc_id}",
                headers={
                    "Authorization": f"Bearer {auth_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "method": "HMAC-Signed",
                    "key": "testkey",
                    "secret": "testsecret",
                    "intended_for": intended_for  # identical inputs both times
                }
            )
            if r.status_code == 503 and "Duplicate entry" in r.text:
                pytest.fail(
                    "SECURITY VIOLATION — FCS_COP.1 FAILS: "
                    "Identical inputs produced a DB collision, confirming "
                    "deterministic (SHA1) link generation. T.LINK_GUESS exploitable."
                )
            assert r.status_code == 201, f"Watermark creation failed: {r.text}"
            links.append(r.json()["link"])

        print(f"\nLink 1: {links[0]}")
        print(f"Link 2: {links[1]}")

        assert links[0] != links[1], (
            "SECURITY VIOLATION — FCS_COP.1 FAILS: "
            "Identical inputs produced identical links, confirming deterministic "
            "and therefore predictable link generation."
        )
        print("FCS_COP.1 PASS: Different links generated for identical inputs.")

    def test_link_has_sufficient_entropy(self, auth_token, uploaded_doc):
        """
        Tests that the link token has sufficient length to resist brute-force.

        secrets.token_hex(32) produces 64 hex chars = 256 bits of entropy.
        SHA1 produces 40 hex chars = 160 bits — less entropy AND predictable.
        Minimum acceptable: 64 hex chars (256 bits) for a CSPRNG-based token.

        Note: a 40-char link passing this test does NOT mean it is secure —
        SHA1 of predictable inputs has effectively zero real entropy regardless
        of output length. Length alone is not a security guarantee.
        """
        doc_id = uploaded_doc["id"]
        intended_for = f"entropy_test_{int(time.time() * 1000)}"

        r = requests.post(
            f"{BASE_URL}/api/create-watermark/{doc_id}",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "method": "HMAC-Signed",
                "key": "testkey",
                "secret": "testsecret",
                "intended_for": intended_for
            }
        )
        assert r.status_code == 201, f"Watermark creation failed: {r.text}"
        link = r.json()["link"]

        print(f"\nLink: {link}")
        print(f"Length: {len(link)} hex chars = {len(link) * 4} bits")

        # Must be hex only
        assert all(c in '0123456789abcdef' for c in link.lower()), (
            f"Link contains non-hex characters: {link}"
        )

        # Must be at least 64 hex chars (256 bits) — SHA1 only produces 40
        assert len(link) >= 64, (
            f"SECURITY VIOLATION — FCS_COP.1 FAILS: "
            f"Link is only {len(link)} hex chars ({len(link) * 4} bits). "
            f"secrets.token_hex(32) produces 64 chars (256 bits). "
            f"SHA1 produces 40 chars — this suggests SHA1 is still in use."
        )
        print(f"FCS_COP.1 PASS: Link has {len(link) * 4} bits of entropy.")

    def test_predicted_link_does_not_grant_access(self, auth_token, uploaded_doc):
        """
        End-to-end test — even if an attacker computes the old SHA1 prediction,
        it must NOT grant access to get-version.

        This tests the full T.LINK_GUESS threat end-to-end:
        can a predicted link actually be used to download a document?
        """
        doc_id = uploaded_doc["id"]
        doc_name = uploaded_doc["name"]
        intended_for = f"access_test_{int(time.time() * 1000)}"

        # Create a real watermark
        r = requests.post(
            f"{BASE_URL}/api/create-watermark/{doc_id}",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "method": "HMAC-Signed",
                "key": "testkey",
                "secret": "testsecret",
                "intended_for": intended_for
            }
        )
        assert r.status_code == 201, f"Watermark creation failed: {r.text}"
        real_link = r.json()["link"]

        # Compute the old SHA1-based predicted link
        intended_slug = secure_filename(intended_for)
        predicted_link = hashlib.sha1(
            f"{doc_name}__{intended_slug}.pdf".encode()
        ).hexdigest()

        print(f"\nReal link:      {real_link}")
        print(f"Predicted link: {predicted_link}")

        # Confirm the real link works
        r_real = requests.get(f"{BASE_URL}/api/get-version/{real_link}")
        assert r_real.status_code == 200, "Real link should grant access"
        print(f"Real link grants access: True")

        # Confirm the predicted link does NOT work
        r_predicted = requests.get(f"{BASE_URL}/api/get-version/{predicted_link}")
        assert r_predicted.status_code == 404, (
            f"SECURITY VIOLATION — FCS_COP.1 FAILS: "
            f"Predicted link granted access (status {r_predicted.status_code})! "
            f"T.LINK_GUESS is fully exploitable end-to-end."
        )
        print(f"Predicted link denied: True")
        print("FCS_COP.1 PASS: Predicted link does not grant access.")