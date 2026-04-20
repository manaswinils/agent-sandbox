# Test Strategy — Motivational Quote App

> **Living document** — updated automatically by the pipeline after every merged PR.
> Do not edit manually; changes will be overwritten.

## Test Layers

| Layer | Location | Runner | Mocking | When it runs |
|---|---|---|---|---|
| Unit | `tests/test_unit.py` | pytest | `app.client` patched via MagicMock | Every PR (local in pipeline) |
| Functional | `tests/test_functional.py` | pytest | `app.client` patched via MagicMock | Every PR (local in pipeline) |
| E2E (staging) | `tests/e2e/test_e2e.js` | Puppeteer | **None — real Anthropic API calls** | After staging deploy |
| E2E (prod) | `tests/e2e/test_e2e.js` | Puppeteer | **None — real Anthropic API calls** | After prod deploy |

## Unit & Functional Tests (`tests/`)

**Tests are AI-generated** by the pipeline on each PR — do not write or modify them manually.

### Shared fixtures (`tests/conftest.py`)

| Fixture | Purpose |
|---|---|
| `client` | Flask test client with `app.config["TESTING"] = True` |
| `mock_anthropic` | Patches `app.client` with `MagicMock`; sets `return_value.content[0].text = "Test quote"` |

### What is covered

| Scenario | Unit | Functional |
|---|---|---|
| `GET /` returns 200 with empty form | ✅ | ✅ |
| `POST /` with valid `work` → Anthropic called, `.quote-box` rendered | ✅ | ✅ |
| `POST /` with empty `work` → Anthropic NOT called, no `.quote-box` | ✅ | ✅ |
| `POST /` with whitespace-only `work` → treated as empty | ✅ | ✅ |
| `POST /` when Anthropic raises `Exception` → `.error` rendered, no traceback | ✅ | ✅ |
| `/health` returns 200 `{"status": "ok"}` | ✅ | — |
| `/ping` returns 200 `{"pong": true}` | ✅ | — |
| `/version` returns 200 with python_version + date | ✅ | — |

### Coverage target

**70%** minimum — enforced in CI (`--cov-fail-under=70`).

### Mocking pattern

```python
# Standard pattern used across all unit/functional tests:
with patch('app.client') as mock_client:
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Test motivational quote")]
    mock_client.messages.create.return_value = mock_response
    # ... test assertions
```

Never use real Anthropic API in unit or functional tests — always mock `app.client`.

## E2E Tests (`tests/e2e/test_e2e.js`)

Browser-based tests using Puppeteer. Run against live deployed environments (staging first, then prod).
**Make real Anthropic API calls** — validates the complete user journey including Claude response quality.

### Test cases

| Test | What it validates |
|---|---|
| `testHealthEndpoint` | `GET /health` returns 200, body is `{"status": "ok"}` |
| `testMainPageStructure` | Page loads (200), non-empty title, `<form>` present, `input[name="work"]` present, submit button present |
| `testRealAnthropicAPICall` | Types "software engineering", submits (60s timeout), checks: no `.error` element, `.quote-box` present, quote ≥ 30 chars, ≥ 5 real words, `.work-label` shows input |
| `testEmptyFormSubmission` | Empty submit either blocked by HTML5 validation or returns without `.quote-box` and no server error |
| `testNotFoundPage` | Unmatched route returns non-500 status code |

### Running E2E tests locally

```bash
cd tests/e2e
npm install
node test_e2e.js https://motivational-quote-app-staging.delightfulfield-c939fa9a.eastus.azurecontainerapps.io
```

### E2E failure handling (prod)

If prod E2E fails:
1. Container App is rolled back to the previous image tag
2. Main branch is reverted (git revert + new PR auto-merged)
3. A GitHub issue is created with full failure details and next steps

## Known gaps / not tested

- CSS styling and visual layout
- Anthropic API response time under load
- Azure infrastructure behaviour (validated only by HTTP health checks)
- Browser compatibility (Puppeteer uses Chromium only)
