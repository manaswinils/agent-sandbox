"""harness/fitness.py — Architecture Fitness Harness: Computational Sensors

Encodes architectural constraints from docs/DECISIONS.md as executable
fitness functions. Each function returns a list of violation strings.
An empty list means the constraint is satisfied.

Run directly:
    python harness/fitness.py [--path .]

Called by the pipeline Stage 2.5 FITNESS after IMPLEMENT.
"""
import ast
import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
SOURCE_DIRS = [REPO_ROOT]
SKIP = {"__pycache__", ".git", "venv", ".venv", "harness", "tests", "node_modules"}

# Thresholds (match docs/DECISIONS.md)
MAX_FUNCTION_LINES = 40
MAX_FILE_LINES = 300  # more lenient for this app size
MIN_ROUTE_DOCSTRING = True


def _source_files() -> list[Path]:
    files = []
    for d in SOURCE_DIRS:
        for f in d.rglob("*.py"):
            if not any(skip in f.parts for skip in SKIP):
                files.append(f)
    return sorted(files)


def max_function_lines(limit: int = MAX_FUNCTION_LINES) -> list[str]:
    """Flag any function/method exceeding `limit` lines."""
    violations = []
    for fpath in _source_files():
        try:
            tree = ast.parse(fpath.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                if length > limit:
                    rel = fpath.relative_to(REPO_ROOT)
                    violations.append(
                        f"{rel}:{node.lineno} function '{node.name}' is {length} lines (limit {limit})"
                    )
    return violations


def max_file_lines(limit: int = MAX_FILE_LINES) -> list[str]:
    """Flag any source file exceeding `limit` lines."""
    violations = []
    for fpath in _source_files():
        lines = fpath.read_text(encoding="utf-8").count("\n")
        if lines > limit:
            rel = fpath.relative_to(REPO_ROOT)
            violations.append(f"{rel}: {lines} lines (limit {limit})")
    return violations


def route_handlers_have_docstrings() -> list[str]:
    """Flag Flask route handler functions missing a docstring."""
    violations = []
    for fpath in _source_files():
        try:
            source = fpath.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            # Check if decorated with @app.route or @app.<method>
            is_route = any(
                (isinstance(d, ast.Call) and
                 isinstance(d.func, ast.Attribute) and
                 d.func.attr in ("route", "get", "post", "put", "delete", "patch"))
                or
                (isinstance(d, ast.Attribute) and
                 d.attr in ("route", "get", "post", "put", "delete", "patch"))
                for d in node.decorator_list
            )
            if is_route:
                has_doc = (
                    node.body and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)
                )
                if not has_doc:
                    rel = fpath.relative_to(REPO_ROOT)
                    violations.append(
                        f"{rel}:{node.lineno} route handler '{node.name}' missing docstring"
                    )
    return violations


def no_hardcoded_secrets() -> list[str]:
    """Flag obvious hardcoded secrets (api keys, passwords in assignments)."""
    import re
    violations = []
    secret_pattern = re.compile(
        r'(api[_-]?key|secret|password|token|credential)\s*=\s*["\'][^"\']{8,}["\']',
        re.IGNORECASE
    )
    for fpath in _source_files():
        source = fpath.read_text(encoding="utf-8")
        for i, line in enumerate(source.splitlines(), 1):
            if secret_pattern.search(line) and "os.environ" not in line and "getenv" not in line:
                rel = fpath.relative_to(REPO_ROOT)
                violations.append(f"{rel}:{i} possible hardcoded secret: {line.strip()[:80]}")
    return violations


def requirements_match_imports() -> list[str]:
    """Warn if top-level imports reference packages not in requirements.txt."""
    req_file = REPO_ROOT / "requirements.txt"
    if not req_file.exists():
        return ["requirements.txt not found"]

    stdlib_modules = sys.stdlib_module_names if hasattr(sys, "stdlib_module_names") else set()
    # Parse requirements — strip version specifiers
    declared = set()
    for line in req_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            pkg = line.split(">=")[0].split("==")[0].split("<=")[0].split("[")[0].strip().lower()
            # normalize hyphens/underscores
            declared.add(pkg.replace("-", "_"))

    violations = []
    for fpath in _source_files():
        try:
            tree = ast.parse(fpath.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0].lower().replace("-", "_")
                    if top not in stdlib_modules and top not in declared and top != "app":
                        rel = fpath.relative_to(REPO_ROOT)
                        violations.append(f"{rel}:{node.lineno} import '{top}' not in requirements.txt")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0].lower().replace("-", "_")
                    if top not in stdlib_modules and top not in declared and top != "app":
                        rel = fpath.relative_to(REPO_ROOT)
                        violations.append(f"{rel}:{node.lineno} from '{top}' not in requirements.txt")
    return violations


def run_all() -> dict[str, list[str]]:
    checks = {
        "max_function_lines": max_function_lines,
        "max_file_lines": max_file_lines,
        "route_handlers_have_docstrings": route_handlers_have_docstrings,
        "no_hardcoded_secrets": no_hardcoded_secrets,
        "requirements_match_imports": requirements_match_imports,
    }
    return {name: fn() for name, fn in checks.items()}


if __name__ == "__main__":
    results = run_all()
    total_violations = 0
    for check, violations in results.items():
        if violations:
            print(f"\n❌ {check}:")
            for v in violations:
                print(f"   {v}")
            total_violations += len(violations)
        else:
            print(f"✅ {check}: OK")

    print(f"\n{'='*50}")
    if total_violations == 0:
        print("✅ All fitness functions passed.")
        sys.exit(0)
    else:
        print(f"⚠️  {total_violations} total violation(s) found.")
        sys.exit(1)
