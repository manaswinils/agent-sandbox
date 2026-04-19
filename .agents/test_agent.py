"""AI test generation agent using Claude claude-sonnet-4-6.

Reads changed source files in a PR, generates pytest unit + functional tests,
runs them with coverage, and posts a coverage report as a PR comment.

Required env vars (set by GitHub Actions):
    ANTHROPIC_API_KEY
    GITHUB_TOKEN
    GITHUB_REPOSITORY   e.g. manaswinils/agent-sandbox
    PR_NUMBER           pull request number (integer)
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from github import Github

load_dotenv()

TEST_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are an expert Python test engineer.
You write thorough pytest test suites that always mock external API calls so tests never touch the network.
Your response contains EXACTLY two fenced Python code blocks and nothing else — no prose, no explanation."""

USER_PROMPT_TEMPLATE = """Generate a complete pytest test suite for the Flask app below.

=== SOURCE FILES ===
{source_files}

=== APP BEHAVIOUR ===
- Flask app in app.py with `client = Anthropic()` at module level.
- GET  /  → renders empty form (templates/index.html).
- POST /  → reads form field "work" (stripped); if non-empty calls client.messages.create()
            and passes the quote to the template; on exception renders error message.

=== OUTPUT FORMAT ===
Produce exactly two Python code blocks:

```python
# tests/test_unit.py
\"\"\"Unit tests for app.py — mock app.client so no real API calls are made.\"\"\"
import pytest
from unittest.mock import MagicMock, patch
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

# Tests required:
# 1. GET / returns 200
# 2. POST / with valid "work" → mocked client returns a quote → quote appears in response body
# 3. POST / with empty "work" → client.messages.create NOT called → no quote in body
# 4. POST / with whitespace-only "work" → treated as empty (stripped)
# 5. POST / when Anthropic raises Exception → error message shown in body

... complete unit test code here ...
```

```python
# tests/test_functional.py
\"\"\"Functional tests using Flask test client — mock app.client to avoid real API calls.\"\"\"
import pytest
from unittest.mock import MagicMock, patch
from app import app as flask_app

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c

# Tests required:
# 1. GET / returns 200, response contains <form and name="work"
# 2. Full flow: POST / with valid input → 200, quote text in body, work label in body
# 3. Full flow: POST / with API failure → 200, error text in body
# 4. POST / with empty work → 200, no quote rendered

... complete functional test code here ...
```

Write real, complete test code with docstrings. Every test must have an assert."""

SKIP_PATTERNS = {"tests/", ".agents/", "__pycache__", ".git", "venv/", ".venv/"}


# ── source file collection ────────────────────────────────────────────────────

def should_test_file(filename: str) -> bool:
    if not filename.endswith(".py"):
        return False
    return not any(skip in filename for skip in SKIP_PATTERNS)


def collect_source_content(changed_files) -> str:
    repo_root = Path(os.getcwd())
    parts: list[str] = []
    for f in changed_files:
        if not should_test_file(f.filename):
            continue
        local_path = repo_root / f.filename
        if not local_path.exists():
            print(f"[test] skipping {f.filename} (not found locally)")
            continue
        try:
            content = local_path.read_text(encoding="utf-8")
            parts.append(f"=== {f.filename} ===\n{content}")
            print(f"[test] collected {f.filename} ({len(content)} chars)")
        except OSError as e:
            print(f"[test] could not read {f.filename}: {e}")
    return "\n\n".join(parts)


# ── Claude interaction ────────────────────────────────────────────────────────

def generate_tests(source_content: str) -> tuple[str, str]:
    """Call Claude to generate test code. Returns (unit_code, functional_code)."""
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = USER_PROMPT_TEMPLATE.format(source_files=source_content)

    print(f"[test] calling Claude {TEST_MODEL} ...")
    response = client.messages.create(
        model=TEST_MODEL,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text
    print(f"[test] received response ({len(raw)} chars)")
    return parse_test_blocks(raw)


def parse_test_blocks(text: str) -> tuple[str, str]:
    blocks = re.findall(r"```python\n(.*?)```", text, re.DOTALL)
    print(f"[test] found {len(blocks)} python code block(s)")

    unit_code = ""
    functional_code = ""

    for block in blocks:
        stripped = block.strip()
        first_line = stripped.split("\n")[0].lower()
        if "test_unit" in first_line or ("unit" in first_line and "functional" not in first_line):
            unit_code = stripped
        elif "test_functional" in first_line or "functional" in first_line:
            functional_code = stripped

    # positional fallback
    if not unit_code and not functional_code and len(blocks) >= 2:
        print("[test] classification fell back to positional assignment")
        unit_code, functional_code = blocks[0].strip(), blocks[1].strip()
    elif not unit_code and len(blocks) >= 1:
        print("[test] WARNING: only one block found; assigning as unit tests")
        unit_code = blocks[0].strip()

    if not unit_code:
        raise ValueError("Could not extract unit test code from Claude response")
    if not functional_code:
        raise ValueError("Could not extract functional test code from Claude response")

    return unit_code, functional_code


# ── test execution ────────────────────────────────────────────────────────────

def write_tests(unit_code: str, functional_code: str) -> None:
    tests_dir = Path("tests")
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "__init__.py").touch()
    (tests_dir / "test_unit.py").write_text(unit_code, encoding="utf-8")
    (tests_dir / "test_functional.py").write_text(functional_code, encoding="utf-8")
    print(f"[test] wrote tests/test_unit.py ({len(unit_code)} chars)")
    print(f"[test] wrote tests/test_functional.py ({len(functional_code)} chars)")


def run_pytest() -> tuple[int, str]:
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=app",
        "--cov-report=json",
        "--cov-report=term-missing",
        "--cov-fail-under=70",
        "-v",
    ]
    print(f"[test] running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout + ("\n" + result.stderr if result.stderr else "")
    print(f"[test] pytest exit code: {result.returncode}")
    print(output[-3000:])
    return result.returncode, output


def parse_coverage_json() -> dict | None:
    cov_path = Path("coverage.json")
    if not cov_path.exists():
        return None
    try:
        return json.loads(cov_path.read_text()).get("totals", {})
    except (json.JSONDecodeError, OSError):
        return None


# ── PR comment ────────────────────────────────────────────────────────────────

def format_coverage_comment(exit_code: int, pytest_output: str, totals: dict | None) -> str:
    icon = "✅" if exit_code == 0 else "❌"
    status = "PASSED" if exit_code == 0 else "FAILED"
    lines = [f"## {icon} AI Test Agent — {status}", ""]

    if totals:
        pct = totals.get("percent_covered", 0)
        covered = totals.get("covered_lines", 0)
        total_stmts = totals.get("num_statements", 0)
        missing = totals.get("missing_lines", 0)
        lines += [
            "### Coverage Summary",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Covered lines | {covered} / {total_stmts} |",
            f"| Coverage | **{pct:.1f}%** |",
            f"| Missing lines | {missing} |",
            "| Threshold | 70% |",
            "",
            f"{'Coverage threshold met' if pct >= 70 else '⚠️ Coverage below threshold'} "
            f"({pct:.1f}% {'≥' if pct >= 70 else '<'} 70%).",
            "",
        ]

    lines += [
        "<details>",
        "<summary>pytest output</summary>",
        "",
        "```",
        pytest_output[-4000:],
        "```",
        "</details>",
        "",
        "_Generated by AI test agent (claude-sonnet-4-6)_",
    ]
    return "\n".join(lines)


def post_pr_comment(token: str, repo_full_name: str, pr_number: int, body: str) -> None:
    gh = Github(token)
    gh.get_repo(repo_full_name).get_pull(pr_number).create_issue_comment(body)
    print(f"[test] comment posted to PR #{pr_number}")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    token = os.environ["GITHUB_TOKEN"]
    repo_full_name = os.environ["GITHUB_REPOSITORY"]
    pr_number = int(os.environ["PR_NUMBER"])

    print(f"[test] repo: {repo_full_name}, PR: #{pr_number}")

    gh = Github(token)
    pr = gh.get_repo(repo_full_name).get_pull(pr_number)
    changed_files = list(pr.get_files())
    print(f"[test] {len(changed_files)} changed file(s) in PR")

    source_content = collect_source_content(changed_files)
    if not source_content:
        print("[test] no testable Python source files changed; skipping")
        post_pr_comment(token, repo_full_name, pr_number,
                        "## ℹ️ AI Test Agent\n\nNo testable Python source files changed in this PR.")
        return 0

    try:
        unit_code, functional_code = generate_tests(source_content)
    except (ValueError, Exception) as e:
        post_pr_comment(token, repo_full_name, pr_number,
                        f"## ❌ AI Test Agent\n\nFailed to generate tests: {e}")
        return 1

    write_tests(unit_code, functional_code)

    exit_code, pytest_output = run_pytest()
    totals = parse_coverage_json()

    comment = format_coverage_comment(exit_code, pytest_output, totals)
    post_pr_comment(token, repo_full_name, pr_number, comment)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
