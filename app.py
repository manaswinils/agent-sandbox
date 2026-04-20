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


def _build_journal_prompt(highlights, obstacles, progress, expectations):
    """Build the Claude prompt for generating a HOPE journal reflection."""
    return f"""You are a thoughtful daily reflection coach. A user has completed their daily HOPE journal with the following entries:

**Highlights** (What were today's highlights?):
{highlights if highlights else "(not provided)"}

**Obstacles** (What obstacles did you face?):
{obstacles if obstacles else "(not provided)"}

**Progress** (What progress did you make?):
{progress if progress else "(not provided)"}

**Expectations** (What are your expectations for tomorrow?):
{expectations if expectations else "(not provided)"}

Please provide a personalized daily reflection that:
1. Acknowledges and celebrates their highlights
2. Offers perspective on the obstacles they faced
3. Recognizes the progress they made, no matter how small
4. Connects their expectations for tomorrow with today's experiences
5. Ends with one actionable insight or encouragement for the next day

Keep the reflection warm, supportive, and around 150-200 words."""


@app.route("/", methods=["GET", "POST"])
def index():
    """Render the motivational quote form and handle submissions."""
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
    """Render the HOPE journal form and handle reflection generation."""
    reflection = None
    error = None
    highlights = ""
    obstacles = ""
    progress = ""
    expectations = ""

    if request.method == "POST":
        highlights = request.form.get("highlights", "").strip()
        obstacles = request.form.get("obstacles", "").strip()
        progress = request.form.get("progress", "").strip()
        expectations = request.form.get("expectations", "").strip()

        # Only call API if at least one field is filled
        if highlights or obstacles or progress or expectations:
            try:
                prompt = _build_journal_prompt(highlights, obstacles, progress, expectations)
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                )
                reflection = response.content[0].text.strip()
            except Exception as e:
                error = f"Could not generate reflection: {e}"

    return render_template(
        "journal.html",
        reflection=reflection,
        highlights=highlights,
        obstacles=obstacles,
        progress=progress,
        expectations=expectations,
        error=error,
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
    """Return build information."""
    return jsonify(python_version=platform.python_version(), date=date.today().isoformat())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
