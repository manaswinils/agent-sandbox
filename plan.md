# Implementation Plan: add a /health endpoint to app.py that returns JSON {status: ok}

## Overview
The repository currently contains no application code — only documentation files. We need to create an `app.py` file with a minimal web application that exposes a `/health` endpoint returning `{"status": "ok"}` as JSON. Based on the deploy.md context (Docker-based Python app on Azure Container Apps), Flask is a natural and lightweight choice.

## Files to Create
| File | Purpose |
|------|---------|
| `app.py` | Flask application with a `/health` endpoint that returns `{"status": "ok"}` (HTTP 200) |
| `requirements.txt` | Python dependency list, pinning `flask` |
| `tests/test_app.py` | Unit/integration tests for the `/health` endpoint |

## Files to Modify
| File | Change Required |
|------|----------------|
| (none) | No existing files need modification |

## Implementation Approach
1. **Create `requirements.txt`** containing `flask` (e.g., `flask>=3.0,<4.0`) so dependencies are explicit and reproducible.
2. **Create `app.py`** with the following structure:
   - Import `Flask` and `jsonify` from `flask`.
   - Instantiate the app: `app = Flask(__name__)`.
   - Define a route `@app.route("/health")` mapped to a function `health()` that returns `jsonify({"status": "ok"})` with an implicit 200 status code.
   - Add an `if __name__ == "__main__":` block that calls `app.run(host="0.0.0.0", port=8000)` for local development and container execution.
3. **Create `tests/test_app.py`**:
   - Import `app` from `app`.
   - Use Flask's built-in test client (`app.test_client()`) to send a `GET /health` request.
   - Assert the response status code is `200`.
   - Assert the response JSON body equals `{"status": "ok"}`.
   - Assert the `Content-Type` header is `application/json`.

## Test Strategy
- **Unit test**: Use Flask's `test_client` in `tests/test_app.py` to call `GET /health` and verify: HTTP 200 status, `Content-Type: application/json`, and body `{"status": "ok"}`.
- **Functional test**: Run `python app.py` locally, then `curl http://localhost:8000/health` and confirm the JSON response.
- **End-to-end validation**: After deployment (per `deploy.md`), hit the live URL at `/health` and verify HTTP 200 with the expected JSON payload.

## Risks and Assumptions
- **Assumption**: Flask is an acceptable framework. The repo has no existing code or framework constraints; Flask is the simplest choice consistent with the Python/Docker deployment described in `deploy.md`.
- **Assumption**: Port 8000 is appropriate for the container runtime. This may need to align with a `Dockerfile` or Azure Container App ingress configuration not yet present in the repo.
- **Risk**: No `Dockerfile` exists in the repo yet. The `/health` endpoint will work locally and in tests, but full container deployment will require a `Dockerfile` (out of scope for this goal but noted).
- **Risk**: If a different web framework or async runtime is later preferred, this Flask-based implementation would need to be refactored.