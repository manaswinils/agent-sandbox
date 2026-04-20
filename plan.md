# Implementation Plan: add a /ping endpoint that returns JSON {"pong": true}

## Overview
The `/ping` endpoint already exists in the codebase. It is defined in `app.py`, returns `{"pong": true}` as JSON, is fully tested in `tests/test_ping.py`, and is documented in `CLAUDE.md`. No changes are required.

## Files to Create
| File | Purpose |
|------|---------|
| *(none)* | All necessary files already exist |

## Files to Modify
| File | Change Required |
|------|----------------|
| *(none)* | All necessary changes are already in place |

## Implementation Approach
1. **Route already defined**: `app.py` contains a `GET /ping` route handler (`def ping()`) that calls `return jsonify(pong=True)`, producing the response `{"pong": true}` with a `200` status code and `application/json` content type.
2. **Tests already exist**: `tests/test_ping.py` contains three tests — `test_ping_status_code` (asserts HTTP 200), `test_ping_content_type` (asserts `application/json`), and `test_ping_json_body` (asserts `{"pong": True}`). These use the shared `client` fixture from `tests/conftest.py`.
3. **Documentation already updated**: `CLAUDE.md` lists `GET /ping` in the routes table under "App structure."
4. **No further action is needed.** Running `pytest tests/test_ping.py` will confirm the endpoint works as expected.

## Test Strategy
- **Unit tests**: Already covered by `tests/test_ping.py` — verifies status code (200), content type (`application/json`), and response body (`{"pong": true}`).
- **Functional test**: Run `flask run` locally and `curl http://localhost:5000/ping` to confirm `{"pong":true}` is returned.
- **End-to-end validation**: The existing E2E test suite (`tests/e2e/test_e2e.js`) does not explicitly test `/ping`, but the unit tests provide sufficient coverage. Optionally, add a Puppeteer test that hits `/ping` and asserts the JSON response.

## Risks and Assumptions
- **No risks**: The endpoint is already fully implemented, tested, and documented.
- **Assumption**: The existing test suite passes. Verify by running `pytest tests/ --cov=app --cov-report=term-missing` locally.