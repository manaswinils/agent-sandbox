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
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    messages=[{
                        "role": "user",
                        "content": (
                            "You are a thoughtful daily journal coach. The user filled out "
                            "their HOPE framework journal for today. Provide a warm, insightful "
                            "3-5 sentence reflection that synthesizes their day, acknowledges "
                            "their challenges, celebrates their wins, and offers encouragement "
                            "for tomorrow.\n\n"
                            f"Highlights: {highlights}\n"
                            f"Obstacles: {obstacles}\n"
                            f"Progress: {progress}\n"
                            f"Expectations: {expectations}\n\n"
                            "Reply with just the reflection, nothing else."
                        ),
                    }],
                )
                reflection = response.content[0].text.strip()
            except Exception as e:
                error = f"Could not generate reflection: {e}"

    return render_template(
        "journal.html",
        reflection=reflection,
        error=error,
        highlights=highlights,
        obstacles=obstacles,
        progress=progress,
        expectations=expectations,
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
