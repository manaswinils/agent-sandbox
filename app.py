"""Motivational quote web app powered by Claude."""
import os

from anthropic import Anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)
client = Anthropic()


@app.route("/", methods=["GET", "POST"])
def index():
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


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
