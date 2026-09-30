"""
Task 2 Empirical Test — FCS_COP.1 Link Generation
===================================================
Tests whether a watermark access link can be reconstructed offline
by a party who knows the document name and intended_for value,
without going through the normal issuance flow as the document owner.

T.LINK_GUESS: can an unauthorized party predict/reconstruct a valid link?
"""

import hashlib
import requests
import pytest

BASE_URL = "http://localhost:5000"


@pytest.fixture
def auth_token():
    """Get a valid auth token for testing."""
    # Register (ignore if already exists)
    requests.post(f"{BASE_URL}/api/create-user", json={
        "login": "sfr_tester",
        "password": "SFRtest123456!",
        "email": "sfr_tester@test.com"
    })
    # Login
    r = requests.post(f"{BASE_URL}/api/login", json={
        "email": "sfr_tester@test.com",
        "password": "SFRtest123456!"
    })
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["token"]


@pytest.fixture
def uploaded_doc(auth_token, tmp_path):
    """Upload a minimal valid PDF and return its doc_id and name."""
    # Minimal valid PDF
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
    pdf_file = tmp_path / "sfr_test_document.pdf"
    pdf_file.write_bytes(pdf_content)

    r = requests.post(
        f"{BASE_URL}/api/upload-document",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": ("sfr_test_document.pdf", pdf_file.read_bytes(), "application/pdf")},
        data={"name": "sfr_test_document"}
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
        intended_for = "sfr_test_recipient"

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
        print(f"\nServer-issued link:   {real_link}")

        # Step 2: Attempt to reconstruct the link offline using the
        # KNOWN VULNERABLE pattern: SHA1(document_name__intended_for.pdf)
        from werkzeug.utils import secure_filename
        intended_slug = secure_filename(intended_for)
        base_name = doc_name  # document name is observable by the owner
        candidate = f"{base_name}__{intended_slug}.pdf"
        predicted_link = hashlib.sha1(candidate.encode("utf-8")).hexdigest()
        print(f"Predicted link (SHA1): {predicted_link}")
        print(f"Match: {real_link == predicted_link}")

        # Step 3: Assert the prediction FAILS — if it matches, the
        # vulnerability is still present and T.LINK_GUESS is exploitable
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
        for identical inputs, which would trivially confirm predictability.
        A CSPRNG produces different links every time.
        """
        doc_id = uploaded_doc["id"]

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
                    "intended_for": "same_recipient"  # identical inputs
                }
            )
            assert r.status_code == 201
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

        secrets.token_hex(32) produces 64 hex characters = 256 bits of entropy.
        SHA1 produces 40 hex characters = 160 bits — less entropy AND predictable.
        Minimum acceptable: 128 bits (32 hex chars) per NIST SP 800-63B.
        """
        doc_id = uploaded_doc["id"]

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
                "intended_for": "entropy_test"
            }
        )
        assert r.status_code == 201
        link = r.json()["link"]

        print(f"\nLink: {link}")
        print(f"Length: {len(link)} hex chars = {len(link) * 4} bits")

        # Must be at least 32 hex chars (128 bits)
        assert len(link) >= 32, (
            f"Link too short: {len(link)} hex chars ({len(link) * 4} bits). "
            f"Minimum 32 chars (128 bits) required."
        )
        # Must be hex only
        assert all(c in '0123456789abcdef' for c in link.lower()), (
            f"Link contains non-hex characters: {link}"
        )

        print(f"FCS_COP.1 PASS: Link has {len(link) * 4} bits of entropy.")

    def test_predicted_link_does_not_grant_access(self, auth_token, uploaded_doc):
        """
        End-to-end test — even if an attacker computes the old SHA1 prediction,
        it must NOT grant access to get-version.

        This tests the full T.LINK_GUESS threat: can a predicted link
        actually be used to download a document?
        """
        doc_id = uploaded_doc["id"]
        doc_name = uploaded_doc["name"]
        intended_for = "access_test_recipient"

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
        assert r.status_code == 201
        real_link = r.json()["link"]

        # Compute the old SHA1-based predicted link
        from werkzeug.utils import secure_filename
        intended_slug = secure_filename(intended_for)
        predicted_link = hashlib.sha1(
            f"{doc_name}__{intended_slug}.pdf".encode()
        ).hexdigest()

        # Confirm the real link works
        r_real = requests.get(f"{BASE_URL}/api/get-version/{real_link}")
        assert r_real.status_code == 200, "Real link should grant access"
        print(f"\nReal link grants access: {r_real.status_code == 200}")

        # Confirm the predicted link does NOT work
        r_predicted = requests.get(f"{BASE_URL}/api/get-version/{predicted_link}")
        assert r_predicted.status_code == 404, (
            f"SECURITY VIOLATION — predicted link granted access! "
            f"T.LINK_GUESS is exploitable. Status: {r_predicted.status_code}"
        )
        print(f"Predicted link denied: {r_predicted.status_code == 404}")
        print("FCS_COP.1 PASS: Predicted link does not grant access.")