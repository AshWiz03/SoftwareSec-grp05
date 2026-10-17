# Fuzzing Evidence — Rahat Islam (Phase II, Specialization A)

API fuzzing of Tatou's watermark endpoints, 14–15 Oct 2026.

## Files in this folder

- `README.md` — this write-up
- `test_fuzz_watermark.py` — the four Hypothesis fuzz tests
- `test_watermark_conflict.py` — the regression test for the bug found
- `fuzz_deep_campaign_results.txt` — raw output of the 500-example deep campaign

## Tool and target

Tool: **Hypothesis**, a property-based testing library for Python. I chose it
because it plugs into the project's existing pytest + `requests` setup (the
`tests` Docker service and its `conftest.py` fixtures) rather than needing a
separate framework.

Target: `POST /api/create-watermark` and `POST /api/read-watermark`. They take
several free-form string fields (`secret`, `key`, `intended_for`, `method`)
straight from the caller, and Phase I had already turned up two real bugs on this
path, so it was the part I trusted least.

## Tests

| Test | Fuzzes | Examples | Auto-run |
|---|---|---|---|
| test_fuzz_create_watermark_fields_never_crash | secret, key, intended_for (0–300 chars) | 30 | Yes |
| test_fuzz_create_watermark_unknown_method_never_crashes | method (0–100 chars) | 30 | Yes |
| test_fuzz_read_watermark_wrong_key_never_crashes | key on read-watermark | 30 | Yes |
| test_fuzz_create_watermark_deep_campaign | secret, key, intended_for | 500 | No — `@pytest.mark.manual` |

The invariant in every test: **the server must never return an unhandled 500**. A
500 means fuzzed input reached code that crashed instead of being validated and
rejected cleanly (4xx) or accepted (2xx). The 500-example campaign is kept out of
CI (`pytest -m "not manual"`) so it doesn't slow every run; it's invoked on demand.

## What I expected vs. what I found

Expected: to find out whether the string handling and validation around watermark
create and read held up against arbitrary input, since this exact path had already
crashed once in Phase I (the zero-page bug).

Found — a test-harness bug of my own, caught twice. My first two "never crashes"
attempts for read-watermark failed with 503 — not a server crash, but because the
test reused the same `intended_for` across calls, colliding on the deterministic
link. A second attempt deriving it from `hash(key)` still collided, because
Hypothesis deliberately re-tries simple edge values (e.g. `key=''`) during its
generate and shrink phases, producing the same derived value. The fix was a fresh
UUID per call, independent of the fuzzed input. Lesson specific to property-based
testing: setup code must be collision-free across repeated calls with *identical*
inputs, not only distinct ones.

Found — one real application bug. On a database conflict (a duplicate recipient),
`create-watermark` returned `503 Service Unavailable`, which conventionally means
"retry later." It's really a predictable client-side conflict and should be
`409 Conflict`. Fixed: the route now catches `IntegrityError` specifically and
returns 409, falling back to 503 only for genuine database errors.
`test_watermark_conflict.py` locks this in.

No crashes: across 90 light examples (30 × 3) plus a 500-example deep campaign
(500 passing, 0 failing, 0 invalid, stopped at max_examples=500), the string fields
and unknown-method handling held up cleanly.

## Limits of the approach

This campaign fuzzed the string fields that reach validated business logic. That's
a fair test of input validation, but it does **not** reach the lower-level
PDF-parsing code inside each watermarking method, which is where the Phase I
zero-page bug lived, because every call used the same valid PDF. The obvious next
step, not yet done, is to fuzz the PDF *bytes* directly against each
`WatermarkingMethod.add_watermark` / `read_secret`, skipping the HTTP and auth
layer to get there faster.

## What I changed as a result

- Added `hypothesis` as a dev dependency (`pyproject.toml`) and to the test image
  (`Dockerfile.test`).
- Added `server/test/test_fuzz_watermark.py`, merged to main from
  `fuzzing/rahat-api-fuzzing`.
- Fixed the 503-for-conflict status in `server.py` (now 409) with a dedicated
  regression test — the full find → triage → fix → regression-test loop.
