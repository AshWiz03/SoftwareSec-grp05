# Specification to test mapping

Maps each platform specification to the tests that verify it. Only for tests created by Mikael Welander, thus watermarking methods and tests created by other members are not included

## Test suites

- **API suite**: HTTP tests in `server/test/`, run against the running server container (`docker compose up --build tests`).
- **In-process suite**: Flask `test_client()` tests in `mutation/test/`, also used for coverage and mutation testing.

The fixtures in `conftest.py` are chained (`created_user` → `auth_headers` → `uploaded_document` → `created_link`). A test that uses a fixture therefore also exercises the endpoints behind it.

## Legend

| Status | Meaning |
|---|---|
| Covered | The requirement is verified by at least one test, including the relevant failure case |
| Partly | Only some aspects are tested, e.g. only the happy path or only unauthenticated access |
| Not tested | No test verifies the requirement |

## Mapping

| # | Specification | Tests | Status |
|---|---|---|---|
| 1 | Users SHOULD be able to upload documents on the platform. | `test_auth.py::test_upload_without_token`, `test_auth.py::test_upload_fabricated_token`, fixture `uploaded_document` | Partly (implicitly covered): rejection without a valid token is tested; a successful upload only runs as a fixture, without a dedicated pytest |
| 2 | Documents without watermarks MUST be accessible only to their owner (and the platform). | – | Not tested: no test tries to fetch another user's document |
| 3 | Users SHOULD be able to generate watermarked versions of their documents. | fixture `created_link` | Partly |
| 4 | Watermarks SHOULD be hard to remove. | – | Not tested|
| 5 | Watermarks MUST allow secret retrieval by the owner, identifying the document's version. | – | Not tested: is tested in `test_watermarkling_all_methods.py` |
| 6 | The platform SHOULD be able to create a secret link to each watermarked document; the link SHOULD not be guessable. | `test_get_version.py::test_get_version_fabricated_link`, `test_get_version.py::test_get_version_oversized_link`, `test_rmap.py::test_full_rmap_handshake_flow` (both suites) | Partly: link creation and rejection of fabricated links are tested % rmap covers creation; the randomness of links is not tested|
| 7 | A watermarked document MAY be downloaded by anyone having knowledge of the link. | `test_get_version.py::test_get_version_valid_link`  | Covered |
| 8 | Original document metadata SHOULD be confidential (known only by the owner and the platform). | – | Not tested: no cross-user tests on the list endpoints |
| 9 | Documents SHOULD be available to their owner. | – | Not tested: `get-document` and `list-documents` have no tests |
| 10 | Documents SHOULD be removable by their owner. | – | Not tested: `delete-document` has no tests |
| 11 | Documents SHOULD not be modifiable by third parties. | `test_auth.py::test_upload_without_token`, `test_auth.py::test_upload_fabricated_token` | Partly: only unauthenticated requests are tested, not an authenticated user acting on someone else's document |

## Summary

- 1 of 11 specifications is fully covered, 4 are partly covered and 6 are not tested.
- Two of the untested specifications are MUST requirements (2 and 5).
- The largest gap is authorisation between users (specifications 2, 8, 10 and 11): every access-control test uses a missing or fabricated token, never a valid token belonging to a different user.