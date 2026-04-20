# Implementation Plan: Add a daily journaling feature using the HOPE framework (Highlights, Obstacles, Progress, Expectations). Users should be able to fill in each section and get a Claude-generated reflection/summary for their day.

## Overview
Add a new `/journal` route that presents a HOPE framework journaling form with four textarea fields (Highlights, Obstacles, Progress, Expectations). On submission, the entries are sent to Claude to generate a personalized daily reflection/summary. This follows the existing pattern of a form-based page that calls the Anthropic API and renders the result, implemented as a new route and template alongside the existing motivational quote feature.

## Files to Create
| File | Purpose |
|------|---------|
| `templates/journal.html` | Jinja2 template with the HOPE journal form (4 textareas) and reflection display area |

## Files to Modify
| File | Change Required |
|------|----------------|
| `app.py` | Add `GET/POST /journal` route handler with HOPE form processing, Claude API call for reflection generation, and a helper function to build the journal prompt |
| `templates/index.html` | Add a navigation link to the journal page (and from journal back to quotes) for discoverability |
| `tests/e2e/test_e2e.js` | Add E2E test for the journal page: structure check, form submission with real Anthropic API call, and reflection validation |

## Implementation Approach

### 1. Add the journal route to `app.py`

Add a helper function `_build_journal_prompt(highlights, obstacles, progress, expectations)` that constructs the Claude prompt from the four HOPE sections. This keeps the route handler under the 40-line limit enforced by `harness/fitness.py`.

Add the `GET/POST /journal` route handler following existing conventions:
- Route handler has a docstring (required by fitness function `route_handlers_have_docstrings`)
- Read form fields via `request.form.get("highlights", "").strip()` (same pattern for obstacles, progress, expectations)
- Validate that at least one field is non-empty before calling the API
- Wrap `client.messages.create(...)` in `try/except Exception as e` — on error, set `error = f"Could not generate reflection: {e}"`
- Use the module-level `client` (ADR-001) — do not instantiate a new `Anthropic()`
- Use model `claude-haiku-4-5-20251001` and `max_tokens=1024` (longer output needed for a reflection summary)
- Pass `reflection`, `highlights`, `obstacles`, `progress`, `expectations`, and `error` to `render_template("journal.html", ...)`
- The prompt should instruct Claude to provide a thoughtful daily reflection that synthesizes the four HOPE sections, identifies patterns, offers encouragement, and suggests one actionable insight

### 2. Create `templates/journal.html`

Structure the template following the same visual design as `index.html` (dark gradient background, card layout, glassmorphism style). Include:

- `<title>Daily Journal — HOPE Framework</title>`
- Navigation link back to `/` (motivational quote page)
- Four `<textarea>` elements inside a `<form method="post" action="/journal">`:
  - `name="highlights"` `id="highlights"` with `<label for="highlights">` — "What were today's highlights?"
  - `name="obstacles"` `id="obstacles"` with `<label for="obstacles">` — "What obstacles did you face?"
  - `name="progress"` `id="progress"` with `<label for="progress">` — "What progress did you make?"
  - `name="expectations"` `id="expectations"` with `<label for="expectations">` — "What are your expectations for tomorrow?"
- Submit button inside the form
- Conditional `{% if reflection %}` block with CSS class `.reflection-box` to display the Claude-generated reflection
- Conditional `{% if error %}` block with CSS class `.error` (reuse existing error styling pattern)
- Echo back submitted values in the textareas via `{{ highlights or '' }}` etc. for UX continuity
- All user-supplied data auto-escaped by Jinja2 (no `| safe` filter)
- Semantic HTML: `<main>`, `<section>`, proper `<label>` elements for accessibility

**Stable CSS selectors for E2E tests:**
- `.reflection-box` — container for the generated reflection
- `.error` — error message container (matches existing convention)
- `form[method="post"]` — the journal form
- `#highlights`, `#obstacles`, `#progress`, `#expectations` — the four textarea fields

### 3. Add navigation link to `templates/index.html`

Add a small navigation link (e.g., `<a href="/journal" class="nav-link">📓 Daily Journal</a>`) below the subtitle or near the bottom of the card. Style it to match the existing design. Do **not** rename or remove any existing CSS selectors (`.quote-box`, `.error`, `.work-label`, `#work`, `form[method="post"]`).

### 4. Update E2E tests in `tests/e2e/test_e2e.js`

Add two new test functions following the existing pattern:

**`testJournalPageStructure(page)`** — Navigate to `/journal`, verify HTTP 200, check for form presence, verify all four textarea fields exist, verify submit button exists, verify navigation link back to `/`.

**`testJournalRealAnthropicAPICall(page)`** — Navigate to `/journal`, fill in all four textareas with sample text, submit the form (60s timeout for real API call), verify no `.error` element, verify `.reflection-box` is present and contains substantial text (≥ 50 chars, ≥ 10 words).

Register both tests in the main runner `try` block alongside existing tests.

### 5. Keep `app.py` under file and function limits

- The file must stay under 300 lines (fitness: `max_file_lines`)
- Each function must stay under 40 lines (fitness: `max_function_lines`)
- Extract the prompt-building logic into `_build_journal_prompt()` to keep the route handler concise
- Every route handler must have a docstring

## Test Strategy

**Note:** Per CLAUDE.md, tests in `tests/` are AI-generated by the pipeline — we should not manually create test files. The test agent will generate unit and functional tests for the new `/journal` route. However, the plan defines what those tests should cover for completeness.

### What unit tests should cover (generated by AI test agent, mocking `app.client`):
- `GET /journal` returns 200 with empty form, no `.reflection-box`
- `POST /journal` with all four fields filled → `client.messages.create` called once, `.reflection-box` rendered
- `POST /journal` with only some fields filled → still calls API, renders reflection
- `POST /journal` with all fields empty/whitespace → API NOT called, no `.reflection-box`
- `POST /journal` when Anthropic raises `Exception` → `.error` rendered, no traceback leaked
- Verify the prompt sent to Claude contains all four HOPE section values

### Mocking pattern (same as existing):
```python
with patch("app.client") as mock_client:
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Great day of progress...")]
    mock_client.messages.create.return_value = mock_response
```

### E2E validation (manual addition to `tests/e2e/test_e2e.js`):
- `testJournalPageStructure`: `/journal` loads, form present, 4 textareas present, submit button present
- `testJournalRealAnthropicAPICall`: fill all 4 fields, submit, verify `.reflection-box` has ≥50 chars and ≥10 real words, no `.error` element

## Risks and Assumptions

1. **New route added to a single-route app**: The existing app serves only `GET/POST /`. Adding `/journal` is the first feature expansion. This is consistent with the Flask architecture and does not require any new dependencies or infrastructure changes. The stateless design (ADR-001 key constraint) is preserved — no database or session storage needed.

2. **File size constraints**: Adding the journal route and helper function to `app.py` will increase it from ~58 lines to approximately 100-110 lines, well within the 300-line limit. The route handler will be ~25 lines with the prompt helper extracted, within the 40-line function limit.

3. **No new dependencies**: The feature uses only the existing Anthropic SDK and Flask — no additions to `requirements.txt` needed.

4. **E2E test modification**: Manually editing `tests/e2e/test_e2e.js` is acceptable since E2E tests are not AI-generated (only `tests/` unit/functional tests are). The E2E file is maintained by developers.

5. **Template conventions**: The new `journal.html` introduces new CSS selectors (`.reflection-box`, `#highlights`, `#obstacles`, `#progress`, `#expectations`). These become part of the stable E2E contract and must not be renamed once established. This is consistent with the existing selector stability pattern documented in `docs/rules/templates.md`.

6. **Token budget**: Journal reflections require more output tokens than a single motivational quote. Using `max_tokens=1024` (vs. 256 for quotes) accommodates a meaningful multi-paragraph reflection while keeping costs reasonable.

7. **Navigation between features**: Adding cross-links between `/` and `/journal` changes the existing `index.html` template. The change is minimal (adding one link) and does not alter any existing selectors or form structure, so existing E2E tests remain unaffected.