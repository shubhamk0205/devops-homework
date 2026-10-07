"""Session 17 - DevSecOps demo app (adapted from the instructor's demo)."""
import datetime
import os
import platform
import sys

from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

APP_VERSION = "1.0.0"
_start_time = datetime.datetime.now(datetime.timezone.utc)


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


@app.route("/")
def home():
    return render_template("index.html", version=APP_VERSION)


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/api/status")
def status():
    uptime = int((_now() - _start_time).total_seconds())
    return jsonify({
        "app": "DevSecOps Demo",
        "version": APP_VERSION,
        "status": "running",
        "python_version": sys.version.split()[0],
        "platform": platform.system(),
        "uptime_seconds": uptime,
    })


@app.route("/api/greet/<name>")
def greet(name):
    return jsonify({"message": f"Hello, {name}! May your pipelines always pass.", "name": name})


@app.route("/api/add", methods=["POST"])
def add_numbers():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    number1 = data.get("number1")
    number2 = data.get("number2")
    if number1 is None or number2 is None:
        return jsonify({"error": "Both number1 and number2 are required"}), 400

    try:
        n1, n2 = float(number1), float(number2)
    except (TypeError, ValueError):
        return jsonify({"error": "Values must be numbers"}), 400

    return jsonify({"number1": n1, "number2": n2, "operation": "addition", "result": n1 + n2})


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found", "code": 404}), 404


if __name__ == "__main__":
    # debug=True was removed - CodeQL (py/flask-debug) flagged it because the
    # Werkzeug debugger lets anyone run code on the server.
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5001"))
    app.run(host=host, port=port)
