"""Motivational quote web app powered by Claude."""
import os
import platform
from datetime import date

from anthropic import Anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)
client = Anthropic()

# Maximum allowed length per journal field (chars) to control token costs
MAX_FIELD_LENGTH = 2000

# System prompt for journal coach (separated from user content for prompt injection safety)
JOURNAL_SYSTEM_PROMPT = (
    "You are a thoughtful daily journal coach. The user filled out their HOPE framework "
    "journal for today. Provide a warm, insightful 3-5 sentence reflection that synthesizes "
    "their day, acknowledges their challenges, celebrates their wins, and offers encouragement "
    "for tomorrow. Reply with just the reflection, nothing else."
)


def _truncate_field(value: str) -> str:
    """Truncate field to MAX_FIELD_LENGTH chars."""
    return value[:MAX_FIELD_LENGTH]


def _build_journal_user_message(highlights: str, obstacles: str, progress: str, expectations: str) -> str:
    """Build user message with XML-tagged fields to separate data from instructions."""
    return (
        "Here is my HOPE journal entry for today:\n\n"
        f"<highlights>{highlights}</highlights>\n"
        f"<obstacles>{obstacles}</obstacles>\n"
        f"<progress>{progress}</progress>\n"
        f"<expectations>{expectations}</expectations>"
    )


@app.route("/", methods=["GET", "POST"])
def index():
    """Render main quote generator page and handle form submission."""
    quote = None
    work = None
    error = None

    if request.method == "POST":
        work = request.form.get("work", "").strip()
        if work:
            try:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=256,
                    messages=[{
                        "role": "user",
                        "content": (
                            f"Give me a single short, powerful motivational quote "
                            f"tailored for someone working on: {work}. "
                            "Reply with just the quote and its author (if known), nothing else."
                        ),
                    }],
                )
                quote = response.content[0].text.strip()
            except Exception as e:
                error = f"Could not generate quote: {e}"

    return render_template("index.html", quote=quote, work=work, error=error)


@app.route("/journal", methods=["GET", "POST"])
def journal():
    """Render HOPE framework journal page and generate Claude reflection."""
    reflection = None
    error = None
    highlights = obstacles = progress = expectations = ""

    if request.method == "POST":
        # Extract and sanitize inputs (truncate to limit token costs)
        highlights = _truncate_field(request.form.get("highlights", "").strip())
        obstacles = _truncate_field(request.form.get("obstacles", "").strip())
        progress = _truncate_field(request.form.get("progress", "").strip())
        expectations = _truncate_field(request.form.get("expectations", "").strip())

        if highlights or obstacles or progress or expectations:
            try:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    system=JOURNAL_SYSTEM_PROMPT,
                    messages=[{
                        "role": "user",
                        "content": _build_journal_user_message(highlights, obstacles, progress, expectations),
                    }],
                )
                reflection = response.content[0].text.strip()
            except Exception as e:
                app.logger.error(f"Journal API error: {e}")
                error = f"Could not generate reflection: {e}"

    return render_template(
        "journal.html", reflection=reflection, error=error,
        highlights=highlights, obstacles=obstacles, progress=progress, expectations=expectations,
    )


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify(status="ok")


@app.route("/ping", methods=["GET"])
def ping():
    """Liveness probe endpoint."""
    return jsonify(pong=True)


@app.route("/version", methods=["GET"])
def version():
    """Return build/version info."""
    return jsonify(python_version=platform.python_version(), date=date.today().isoformat())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
