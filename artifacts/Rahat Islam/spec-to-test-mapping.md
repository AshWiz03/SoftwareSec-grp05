# Spec-to-Test Mapping — Rahat Islam

Maps the Tatou API specification (API.md Tables 1–3) and the platform rules
(Platform_specifications.md) to the automated tests that cover them. Test names
are from the `server/test/` suite.

Status key: **Covered** = a test asserts this directly · **Partial** = touched but
not fully exercised · **Gap** = no automated test yet (manual or future work).

## Table 1 — Public endpoints

| Requirement | Test file :: test | Status |
|---|---|---|
| `healthz` returns 200 with message + db_connected | test_healthz.py :: test_healthz_route | Covered |
| `create-user` — valid signup | test_auth.py :: test_create_user_success | Covered |
| `create-user` — missing fields rejected | test_auth.py :: test_create_user_missing_fields | Covered |
| `create-user` — invalid email rejected | test_auth.py :: test_create_user_invalid_email_format | Covered |
| `create-user` — weak password rejected | test_auth.py :: test_create_user_invalid_pwd_format | Covered |
| `create-user` — duplicate email → 409 | test_auth.py :: test_create_user_duplicate_email | Covered |
| `create-user` — duplicate login rejected | — | Gap (manual test found login not unique) |
| `login` — valid credentials return token | test_auth.py :: test_login_success | Covered |
| `login` — wrong password → 401 | test_auth.py :: test_login_wrong_password | Covered |
| `login` — nonexistent user → generic 401 (no enumeration) | test_auth.py :: test_login_nonexistent_user | Covered |
| `login` — missing fields → 400 | test_auth.py :: test_login_missing_fields | Covered |
| `get-version/<link>` — valid link returns PDF | test_get_version.py :: test_get_version_valid_link | Covered |
| `get-version/<link>` — garbage link → 404 | test_get_version.py :: test_get_version_fabricated_link | Covered |
| `get-version/<link>` — oversized link handled | test_get_version.py :: test_get_version_oversized_link | Covered |
| `get-watermarking-methods` — count matches list | — | Gap (checked manually) |

## Table 2 — Authenticated endpoints

| Requirement | Test file :: test | Status |
|---|---|---|
| `upload-document` — no token → 401 | test_auth.py :: test_upload_without_token | Covered |
| `upload-document` — fabricated token → 401 | test_auth.py :: test_upload_fabricated_token | Covered |
| `upload-document` — valid upload → 201 | — | Gap (manual test, 17 Sep) |
| `list-documents` — ownership isolation | — | Gap (manual test, 17 Sep) |
| `delete-document` — auth required / ownership | — | Gap (manual test found unauth-delete on VM) |
| `create-watermark` — fields never crash (fuzz) | test_fuzz_watermark.py :: test_fuzz_create_watermark_fields_never_crash | Covered |
| `create-watermark` — unknown method never crashes | test_fuzz_watermark.py :: test_fuzz_create_watermark_unknown_method_never_crashes | Covered |
| `create-watermark` — duplicate → 409 not 503 | test_watermark_conflict.py :: test_duplicate_watermark_returns_conflict_not_service_unavailable | Covered |
| `read-watermark` — wrong key never crashes (fuzz) | test_fuzz_watermark.py :: test_fuzz_read_watermark_wrong_key_never_crashes | Covered |

## Table 3 — RMAP endpoints

| Requirement | Test file :: test | Status |
|---|---|---|
| `rmap-initiate` — missing / empty / invalid body handled | test_rmap.py :: test_rmap_initiate_missing_body, _empty_json, _payload_is_none, _payload_is_empty, _invalid_payload | Covered |
| Full 4-message handshake returns a valid link | test_rmap.py :: test_full_rmap_handshake_flow | Partial (needs test_group_priv.asc present to pass) |

## Watermarking methods (all registered methods, parametrized)

| Requirement | Test file :: test | Status |
|---|---|---|
| Method reports applicability correctly | test_watermarking_all_methods.py :: test_is_watermark_applicable[*] | Covered |
| add_watermark produces valid output | test_watermarking_all_methods.py :: test_add_watermark_and_shape[*] | Covered |
| read_secret round-trips the secret | test_watermarking_all_methods.py :: test_read_secret_roundtrip[*] | Covered |
| metadata-secret wrong-key rejection | test_metadata_watermark.py (round-trip + wrong-key) | Covered |

## Platform rules (Platform_specifications.md)

| Rule | Covered by | Status |
|---|---|---|
| Unwatermarked docs accessible only to owner | auth tests + manual IDOR pass | Partial |
| Watermark allows owner secret retrieval | read_secret round-trip tests | Covered |
| Secret link not guessable by others | — | Gap (manual finding: link is sha1 of a predictable string) |
| Original metadata confidential to owner | auth tests | Partial |
| Documents removable by owner | — | Gap (manual finding: unauth delete on VM) |
| Documents not modifiable by third parties | auth tests | Partial |

## Notes

The "Gap" rows are mostly covered by the manual black-box session on 17 Sep
(see `results/`), not yet folded into the automated suite. The two most
important gaps — the unauthenticated delete and the predictable link — are
documented as security findings in the report.
