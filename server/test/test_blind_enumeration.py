"""
FCS_COP.1 Empirical Test — Blind Link Enumeration
===================================================
Simulates an attacker with NO knowledge of any document, its name,
its recipient, or its existence. Tests whether valid links can be
discovered purely by enumeration — without any underlying document data.
"""

import hashlib
import secrets
import requests
import time
import pytest

BASE_URL = "http://localhost:5000"

@pytest.fixture(autouse=True)
def _use_base_url(base_url):
    global BASE_URL
    BASE_URL = base_url



@pytest.fixture
def auth_token():
    # Unique credentials per test run — avoids conflicts with previous runs
    unique_id = int(time.time() * 1000)
    email = f"fcs_tester_{unique_id}@test.com"
    login = f"fcs_tester_{unique_id}"
    password = "FCStest123456!"

    r = requests.post(f"{BASE_URL}/api/create-user", json={
        "login": login,
        "password": password,
        "email": email
    })
    assert r.status_code == 201, f"Registration failed: {r.text}"

    r = requests.post(f"{BASE_URL}/api/login", json={
        "email": email,
        "password": password
    })
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["token"]


@pytest.fixture
def issued_link(auth_token, tmp_path):
    """
    Create a real watermark and return its link.
    The attacker does NOT know the document name or intended_for —
    only that some link exists somewhere in the 40-hex-char space.
    """
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
    unique_name = f"fcs_doc_{int(time.time() * 1000)}"
    pdf_file = tmp_path / f"{unique_name}.pdf"
    pdf_file.write_bytes(pdf_content)

    r = requests.post(
        f"{BASE_URL}/api/upload-document",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": (f"{unique_name}.pdf", pdf_file.read_bytes(), "application/pdf")},
        data={"name": unique_name}
    )
    assert r.status_code == 201

    doc_id = r.json()["id"]
    intended_for = f"fcs_recipient_{int(time.time() * 1000)}"

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
    return r.json()["link"]


class TestFCSCOP1BlindEnumeration:
    """
    FCS_COP.1 — Blind Link Enumeration
    
    Attacker has NO knowledge of document name, intended_for, or
    document existence. Tests whether the link space is large enough
    to prevent practical blind enumeration.
    """

    def test_link_space_is_practically_unenumerable(self, issued_link):
        """
        CORE TEST — measures the size of the link space and calculates
        how long blind enumeration would take.

        A 40-char SHA1 hex link has 16^40 = 2^160 possible values.
        A 64-char CSPRNG hex link has 16^64 = 2^256 possible values.

        Even at 1 billion requests/second, exhausting 2^160 values
        would take longer than the age of the universe.

        This test confirms the link is long enough to prevent blind
        enumeration — regardless of HOW it was generated.
        """
        link = issued_link
        link_bits = len(link) * 4  # each hex char = 4 bits

        print(f"\nLink: {link}")
        print(f"Link length: {len(link)} hex chars = {link_bits} bits")
        print(f"Link space size: 2^{link_bits}")

        # Calculate time to enumerate at 1 billion requests/second
        requests_per_second = 1_000_000_000
        total_values = 2 ** link_bits
        seconds_to_exhaust = total_values / requests_per_second
        years_to_exhaust = seconds_to_exhaust / (365.25 * 24 * 3600)

        print(f"At 1B requests/sec, exhaustion takes: {years_to_exhaust:.2e} years")
        print(f"Age of universe: ~1.38 × 10^10 years")

        # Must be at least 128 bits to resist blind enumeration
        assert link_bits >= 128, (
            f"FCS_COP.1 FAILS: Link space too small ({link_bits} bits). "
            f"Blind enumeration may be practical."
        )
        print(f"FCS_COP.1 PASS: Link space is 2^{link_bits} — "
              f"blind enumeration takes {years_to_exhaust:.2e} years at 1B req/s.")

    def test_random_guesses_do_not_find_valid_links(self, issued_link):
        """
        Practical confirmation — generate 1000 random 40-char hex strings
        and verify none of them happen to be valid links.

        This directly tests whether an attacker can stumble upon a valid
        link by random guessing. 1000 attempts against a 2^160 space
        has effectively zero probability of success.

        Note: this test passes trivially for a correctly-sized link space.
        Its value is as a concrete, reproducible demonstration that
        random guessing does not work — not as a statistical proof.
        """
        hits = 0
        attempts = 1000

        for _ in range(attempts):
            # Generate a random 40-char hex string (same length as SHA1)
            random_link = secrets.token_hex(20)  # 20 bytes = 40 hex chars
            r = requests.get(f"{BASE_URL}/api/get-version/{random_link}")
            if r.status_code == 200:
                hits += 1

        print(f"\nRandom guesses tried: {attempts}")
        print(f"Valid links found: {hits}")
        print(f"Success rate: {hits}/{attempts} = {hits/attempts:.6f}")

        assert hits == 0, (
            f"FCS_COP.1 FAILS: {hits} random guesses returned valid links. "
            f"Link space may be smaller than expected."
        )
        print("FCS_COP.1 PASS: 0 valid links found in 1000 random guesses.")

    def test_link_is_not_sequential_or_predictable_from_id(self, auth_token, tmp_path):
        """
        Tests that links issued for sequential documents are not sequential
        or arithmetically related — ruling out ID-based enumeration.

        An attacker who notices that document IDs are sequential integers
        might try to predict links from IDs. This test confirms that
        sequential document IDs produce unrelated link values.
        """
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

        links = []
        for i in range(3):
            unique_name = f"seq_doc_{i}_{int(time.time() * 1000)}"
            pdf_file = tmp_path / f"{unique_name}.pdf"
            pdf_file.write_bytes(pdf_content)

            r = requests.post(
                f"{BASE_URL}/api/upload-document",
                headers={"Authorization": f"Bearer {auth_token}"},
                files={"file": (f"{unique_name}.pdf",
                                pdf_file.read_bytes(), "application/pdf")},
                data={"name": unique_name}
            )
            assert r.status_code == 201
            doc_id = r.json()["id"]

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
                    "intended_for": f"recipient_{i}_{int(time.time() * 1000)}"
                }
            )
            assert r.status_code == 201
            links.append(r.json()["link"])

        print(f"\nLink 1: {links[0]}")
        print(f"Link 2: {links[1]}")
        print(f"Link 3: {links[2]}")

        # Check no two links share a common prefix longer than chance
        # (would indicate sequential/ID-based generation)
        for i in range(len(links)):
            for j in range(i + 1, len(links)):
                common_prefix = 0
                for a, b in zip(links[i], links[j]):
                    if a == b:
                        common_prefix += 1
                    else:
                        break
                print(f"Common prefix between link {i+1} and {j+1}: "
                      f"{common_prefix} chars")
                # More than 4 chars in common would be suspicious for random links
                assert common_prefix < 5, (
                    f"FCS_COP.1 FAILS: Links {i+1} and {j+1} share a "
                    f"{common_prefix}-char prefix — suggests sequential generation."
                )

        # Also confirm all three are distinct
        assert len(set(links)) == 3, (
            "FCS_COP.1 FAILS: Duplicate links generated for different documents."
        )
        print("FCS_COP.1 PASS: Sequential documents produce unrelated links.")