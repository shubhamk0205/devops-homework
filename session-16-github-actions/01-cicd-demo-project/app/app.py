"""Session 16 - small Flask app used for the CI/CD demo."""
import os

from flask import Flask, jsonify, request

from app.calculator import add, subtract, multiply, divide

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "dev")

OPERATIONS = {
    "add": add,
    "subtract": subtract,
    "multiply": multiply,
    "divide": divide,
}


@app.route("/")
def home():
    return jsonify({
        "app": "Session 16 CI/CD Demo",
        "version": APP_VERSION,
        "endpoints": ["/health", "/api/calc?op=add&a=1&b=2", "/api/message"],
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/api/calc")
def calc():
    op = request.args.get("op", "add")
    if op not in OPERATIONS:
        return jsonify({"error": f"unknown operation '{op}'"}), 400
    try:
        a = float(request.args.get("a", ""))
        b = float(request.args.get("b", ""))
        result = OPERATIONS[op](a, b)
    except ValueError as err:
        return jsonify({"error": str(err)}), 400
    return jsonify({"op": op, "a": a, "b": b, "result": result})


@app.route("/api/message")
def message():
    # APP_MESSAGE comes from a GitHub Actions secret during the CD job
    return jsonify({"message": os.getenv("APP_MESSAGE", "no message set")})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "127.0.0.1")
    app.run(host=host, port=port)
