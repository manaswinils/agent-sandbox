# Implementation Plan: add a /version endpoint that returns JSON with the current date and python version

## Overview
Add a new `/version` GET endpoint to the Flask application that returns a JSON response containing the current date and the Python version. This follows the same pattern as the existing `/health` endpoint, using Flask's `jsonify` helper.

## Files to Create
| File | Purpose |
|------|---------|
| tests/test_version.py | Unit tests for the new `/version` endpoint |

## Files to Modify
| File | Change Required |
|------|----------------|
| `app.py` | Add `import sys` and `from datetime import date` at the top; add a new `@app.route("/version")` endpoint that returns `jsonify(python_version=sys.version, date=date.today().isoformat())` |
| `CLAUDE.md` | Update the app structure table to list the new `GET /version` route alongside `GET /health` |

## Implementation Approach
1. **Add imports to `app.py`**: Add `import sys` and `from datetime import date` to the top of `app.py`, alongside the existing standard-library `import os`.
2. **Add the `/version` route**: Define a new function `version()` decorated with `@app.route("/version", methods=["GET"])`. The function returns `jsonify(python_version=sys.version, date=date.today().isoformat())`. This mirrors the pattern of the existing `/health` endpoint.
3. **Update `CLAUDE.md`**: In the "App structure" table, change the `app.py` purpose cell from `GET/POST /` and `GET /health` to also include `GET /version`.
4. **Add tests in `tests/test_version.py`**: Write tests using the existing `client` fixture from `tests/conftest.py`. Tests should verify:
   - The endpoint returns HTTP 200.
   - The response content type is `application/json`.
   - The JSON body contains a `python_version` key whose value matches `sys.version`.
   - The JSON body contains a `date` key whose value matches today's date in ISO format (`YYYY-MM-DD`).

## Test Strategy
- **Unit test (tests/test_version.py)**:
  - `test_version_status_code` — asserts `GET /version` returns 200.
  - `test_version_json_has_python_version` — asserts response JSON key `python_version` equals `sys.version`.
  - `test_version_json_has_date` — asserts response JSON key `date` equals `date.today().isoformat()`.
  - `test_version_content_type` — asserts response `Content-Type` is `application/json`.
- **Functional validation**: Run `pytest tests/ --cov=app --cov-report=term-missing` locally to ensure all tests pass and coverage stays above the 70% threshold.
- **End-to-end validation**: Start the app with `flask run` and `curl http://localhost:5000/version` to confirm valid JSON output with both fields.

## Risks and Assumptions
- The `date` value is computed at request time, so a test that runs exactly at midnight could theoretically see a date mismatch; this is extremely unlikely and acceptable.
- No new dependencies are required — `sys` and `datetime` are Python standard library modules.
- The endpoint is public/unauthenticated, matching the pattern of the existing `/health` endpoint; exposing the full `sys.version` string is assumed acceptable for this application.