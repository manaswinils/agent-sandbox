# Implementation Plan: Add a daily journaling feature using the HOPE framework (Highlights, Obstacles, Progress, Expectations). Users should be able to fill in each section and get a Claude-generated reflection/summary for their day.

## Overview
Add a new `/journal` route and template that presents a HOPE framework journaling form with four textarea fields (Highlights, Obstacles, Progress, Expectations). On submission, the entries are sent to the Claude API which generates a personalized daily reflection/summary. The feature follows the existing app patterns — stateless request/response, module-level Anthropic client, same UI design language, and mocked API in tests.

## Files to Create
| File | Purpose |
|------|---------|
| `templates/journal.html` | Jinja2 template — HOPE form with four textareas + reflection display area |

## Files to Modify
| File | Change Required |
|------|----------------|
| `app.py` | Add `GET/POST /journal` route handler (`journal()`) that processes HOPE form fields and calls Claude for a reflection summary |
| `tests/e2e/test_e2e.js` | Add `testJournalPageStructure` and `testJournalRealAnthropicAPICall` E2E tests for the journal feature |

## Implementation Approach

### 1. Add the `/journal` route in `app.py`

Add a new route function `journal()` decorated with `@app.route("/journal", methods=["GET", "POST"])` following the exact pattern of the existing `index()` route:

- On `GET`: render `journal.html` with empty state (`reflection=None`, `error=None`, all HOPE fields empty).
- On `POST`: read four form fields — `highlights`, `obstacles`, `progress`, `expectations` — each stripped of whitespace.
- **Validation**: Check that at least one of the four fields is non-empty. If all are empty, render the template with no reflection and no API call (matching the `index()` pattern where empty `work` skips the API call).
- **Claude API call**: Use `client.messages.create()` with model `claude-haiku-4-5-20251001`, `max_tokens=1024` (reflections are longer than single quotes). The prompt should be:
  ```
  You are a thoughtful daily journal coach. The user filled out their HOPE framework journal for today. Provide a warm, insightful 3-5 sentence reflection that synthesizes their day, acknowledges their challenges, celebrates their wins, and offers encouragement for tomorrow.

  Highlights: {highlights}
  Obstacles: {obstacles}
  Progress: {progress}
  Expectations: {expectations}

  Reply with just the reflection, nothing else.
  ```
- **Error handling**: Wrap the API call in `try/except Exception as e` and set `error = f"Could not generate reflection: {e}"` (matching the existing error pattern).
- Extract the reflection: `reflection = response.content[0].text.strip()`
- Return `render_template("journal.html", reflection=reflection, error=error, highlights=highlights, obstacles=obstacles, progress=progress, expectations=expectations)`.
- **Docstring**: Must include a docstring per the `route_handlers_have_docstrings` fitness function.
- **Function length**: Keep the handler under 40 lines per the `max_function_lines` fitness constraint. The function will be approximately 25-30 lines.

### 2. Create `templates/journal.html`

Follow the design language and CSS conventions from `templates/index.html`:
- Same gradient background, `.card` container, glassmorphism styling.
- Title: `📓 Daily Journal — HOPE Framework`
- Subtitle explaining the HOPE acronym.
- A `<form method="POST">` containing four `<textarea>` elements:
  - `name="highlights"` with placeholder "What went well today?"
  - `name="obstacles"` with placeholder "What challenges did you face?"
  - `name="progress"` with placeholder "What progress did you make?"
  - `name="expectations"` with placeholder "What do you expect or hope for tomorrow?"
- Each textarea should have a visible label (`<label>`) with the HOPE letter highlighted.
- A submit `<button type="submit">` with text "Get my reflection →".
- Reflection display: `{% if reflection %}<div class="reflection-box">{{ reflection }}</div>{% endif %}` — styled similarly to `.quote-box` but with a distinct color (e.g., a calming blue/teal accent instead of red).
- Error display: `{% if error %}<p class="error">{{ error }}</p>{% endif %}` — same `.error` class.
- Navigation: Add a link back to the main quote page `<a href="/">← Back to Quote Generator</a>`.
- Textareas should preserve submitted values using `{{ highlights or '' }}` etc.
- At least one textarea must be filled (use JavaScript-based validation or server-side; server-side is simpler and consistent with existing approach — no `required` on individual fields, validation handled in the route).

### 3. Add navigation link from `index.html` to journal

Add a small link/button below the existing card content in `templates/index.html`:
- `<a href="/journal" class="nav-link">📓 Daily Journal</a>` with subtle styling that fits the existing design.

### 4. Keep `app.py` under 300 lines (fitness constraint)

The current `app.py` is approximately 55 lines. Adding the journal route (~25-30 lines) will bring it to approximately 80-85 lines — well within the 300-line limit.

### 5. Update E2E tests in `tests/e2e/test_e2e.js`

Add two new test functions to the E2E suite:

**`testJournalPageStructure(page)`**:
- Navigate to `${BASE_URL}/journal`
- Assert HTTP 200
- Assert `<form>` present
- Assert four textareas exist: `textarea[name="highlights"]`, `textarea[name="obstacles"]`, `textarea[name="progress"]`, `textarea[name="expectations"]`
- Assert submit button present

**`testJournalRealAnthropicAPICall(page)`**:
- Navigate to `/journal`
- Type sample content into each textarea
- Submit the form (60s timeout for real API call, matching existing pattern)
- Assert no `.error` element
- Assert `.reflection-box` is present and non-empty
- Assert reflection text is ≥50 chars and ≥10 real words (reflections are longer than quotes)
- Assert no server error phrases in body

Register both new tests in the runner `try` block alongside existing tests.

## Test Strategy

### Unit tests (AI-generated — guidance for the test agent)
Tests will mock `app.client` using the existing `mock_anthropic` fixture pattern from `tests/conftest.py`:

- **`GET /journal` returns 200** with empty form, no `.reflection-box`
- **`POST /journal` with all four fields filled** → Anthropic `messages.create` called once, `.reflection-box` rendered with reflection text
- **`POST /journal` with only some fields filled** (e.g., just highlights) → Anthropic called, reflection rendered
- **`POST /journal` with all fields empty/whitespace** → Anthropic NOT called, no `.reflection-box`
- **`POST /journal` when Anthropic raises Exception** → `.error` rendered, no `.reflection-box`, no traceback
- **Verify the prompt sent to Claude** includes all four field values

Mocking pattern (extends existing `conftest.py`):
```python
with patch('app.client') as mock_client:
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Great day of progress! ...")]
    mock_client.messages.create.return_value = mock_response
```

### Functional tests via Flask test client
- Submit the journal form via `client.post("/journal", data={...})` and assert response HTML contains `.reflection-box` with content
- Verify that submitted field values are preserved in the response HTML (textarea values repopulated)
- Test navigation links exist between index and journal pages

### E2E validation (Puppeteer against live staging/prod)
- **Selectors**: `textarea[name="highlights"]`, `textarea[name="obstacles"]`, `textarea[name="progress"]`, `textarea[name="expectations"]`, `.reflection-box`, `.error`, `button[type="submit"]`
- **User flows**: Load journal page → fill all four fields → submit → verify reflection appears with substantial content

## Risks and Assumptions

- **New route is a feature addition, not a design change**: The `/journal` route follows the identical stateless request→Claude→render pattern as `/`. No new architectural decisions are introduced — this uses the same module-level client (ADR-001), same mocking strategy, same error handling pattern.
- **Fitness constraints**: The journal route handler must stay ≤40 lines and `app.py` must stay ≤300 lines total. With the current ~55-line file and a ~25-line handler, this is achievable. If needed, the prompt string can be extracted to a module-level constant.
- **`max_tokens=1024`**: Reflections need more space than quotes (which use 256). 1024 tokens is sufficient for a 3-5 sentence reflection without being wasteful. This is not a new architectural decision — it's a per-call parameter matching content needs.
- **No state persistence**: Consistent with existing stateless design. Journal entries are not saved between requests. If persistence is desired in the future, that would be a separate ADR.
- **Tests are AI-generated**: Per CLAUDE.md, tests in `tests/` are generated by the AI test agent. The test strategy section above provides guidance for what the test agent should generate, but we do not manually create test files. The E2E additions in `tests/e2e/test_e2e.js` are an exception — E2E tests are manually maintained.
- **Template escaping**: Jinja2 auto-escapes by default. User-submitted HOPE field values rendered in textareas via `{{ field or '' }}` are safe. The reflection from Claude is also auto-escaped, which is correct behavior.