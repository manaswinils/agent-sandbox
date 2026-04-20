# Architectural Decisions — Motivational Quote App

> **Living document** — updated automatically by the pipeline after every merged PR.
> New entries are prepended (newest first). Do not edit manually.

---

## ADR-005: HOPE journaling feature with structured prompt builder

**Date:** 2026-04
**Decision:** Added a `/journal` route implementing the HOPE framework (Highlights,
Obstacles, Progress, Expectations). A dedicated `_build_journal_prompt()` helper
constructs the Claude prompt from four form fields. Claude (claude-haiku-4-5-20251001)
generates a 150-200 word personalized daily reflection.
**Rationale:** Separating prompt construction into `_build_journal_prompt()` keeps
the route handler focused on HTTP concerns and makes the prompt logic independently
testable. Using the same model and module-level client as the quote feature avoids
additional configuration and maintains consistency.
**Tradeoffs:** All four HOPE fields are optional — if a user submits an empty journal,
Claude still generates a response based on "(not provided)" placeholders. No
server-side validation enforces at least one non-empty field.
**Alternative considered:** A separate microservice or dedicated endpoint per HOPE
field — rejected as unnecessary complexity for a single-app deployment.

---

## ADR-004: Living documents maintained by pipeline

**Date:** 2026-04
**Decision:** ARCHITECTURE.md, TEST.md, DECISIONS.md, and CLAUDE.md are updated
automatically by `docs_agent.py` after every successful pipeline run (Stage 11).
**Rationale:** Keeps documentation in sync with code without requiring manual updates.
AI agents (plan, implement, review) read these docs as context before acting, so
they must reflect the current state to be useful.
**Tradeoffs:** Docs may lag one pipeline run behind reality if a run fails. The doc
update stage is non-fatal — a failure never blocks deployment.

---

## ADR-003: Puppeteer E2E tests with real Anthropic API calls

**Date:** 2026-04
**Decision:** E2E tests in `tests/e2e/test_e2e.js` make real calls to the deployed
app which in turn calls the real Anthropic API. No mocking at the E2E layer.
**Rationale:** The core value proposition is the Anthropic integration. Mocking it
at E2E level would validate only routing/rendering, not the actual user experience.
A 60-second timeout accommodates real Claude response latency (typically 3-15s).
**Tradeoffs:** Tests consume API credits and are non-deterministic. Mitigated by
validating response structure (≥30 chars, ≥5 words) rather than exact content.
**Alternative considered:** Mock the Anthropic endpoint at the HTTP layer using a
proxy — rejected as overly complex and not matching actual production behaviour.

---

## ADR-002: Staging always-on (min-replicas=1)

**Date:** 2026-04
**Decision:** Staging Container App is configured with `min-replicas=1`.
**Rationale:** Azure Container Apps with `min-replicas=0` (scale-to-zero) take
60-90 seconds to cold-start after a deploy. This caused Puppeteer E2E tests to
time out before the app became ready. Always-on staging eliminates this.
**Tradeoffs:** Small additional Azure cost for one permanently running replica.
**Alternative considered:** Increase E2E timeout to 3+ minutes — rejected as it
makes the pipeline slow and masks genuine startup failures.

---

## ADR-001: Module-level Anthropic client

**Date:** 2026-04
**Decision:** `client = Anthropic()` is instantiated once at module level in
`app.py`, not per request.
**Rationale:** Avoids connection overhead on every request. The Anthropic SDK client
is thread-safe. Flask's development server and gunicorn both use a shared module
state per worker process.
**Tradeoffs:** Requires `unittest.mock.patch('app.client', ...)` in tests rather
than constructor injection. This is the established pattern — see `tests/conftest.py`.
**Alternative considered:** Dependency injection via Flask's `g` or `current_app` —
rejected as unnecessary complexity for a single-client app.
