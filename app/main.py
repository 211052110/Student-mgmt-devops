"""
Student Management System
A minimal Flask + SQLite CRUD app built to demonstrate an
end-to-end DevOps pipeline (Git -> Jenkins -> Docker -> Deploy -> Monitor).
"""
import os
import sqlite3
from flask import Flask, request, jsonify, render_template, g

DB_PATH = os.environ.get("SMS_DB_PATH", "students.db")

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT NOT NULL,
            branch TEXT,
            semester INTEGER
        )
        """
    )
    db.commit()
    db.close()


# ---------- Views ----------

@app.route("/")
def index():
    return render_template("index.html")


# ---------- Health & Metrics (used by monitoring) ----------

@app.route("/health")
def health():
    return jsonify(status="ok"), 200


REQUEST_COUNT = {"total": 0}


@app.before_request
def count_requests():
    REQUEST_COUNT["total"] += 1


@app.route("/metrics")
def metrics():
    # Minimal Prometheus-style text exposition format.
    body = (
        "# HELP app_requests_total Total HTTP requests received\n"
        "# TYPE app_requests_total counter\n"
        f"app_requests_total {REQUEST_COUNT['total']}\n"
    )
    return body, 200, {"Content-Type": "text/plain; version=0.0.4"}


# ---------- Student CRUD API ----------

@app.route("/students", methods=["GET"])
def list_students():
    db = get_db()
    rows = db.execute("SELECT * FROM students ORDER BY id").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/students", methods=["POST"])
def create_student():
    data = request.get_json(force=True) or {}
    name = data.get("name")
    roll_number = data.get("roll_number")
    branch = data.get("branch", "")
    semester = data.get("semester")

    if not name or not roll_number:
        return jsonify(error="name and roll_number are required"), 400

    db = get_db()
    cur = db.execute(
        "INSERT INTO students (name, roll_number, branch, semester) VALUES (?, ?, ?, ?)",
        (name, roll_number, branch, semester),
    )
    db.commit()
    return jsonify(id=cur.lastrowid), 201


@app.route("/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    db = get_db()
    row = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if row is None:
        return jsonify(error="not found"), 404
    return jsonify(dict(row))


@app.route("/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    data = request.get_json(force=True) or {}
    db = get_db()
    row = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if row is None:
        return jsonify(error="not found"), 404

    name = data.get("name", row["name"])
    roll_number = data.get("roll_number", row["roll_number"])
    branch = data.get("branch", row["branch"])
    semester = data.get("semester", row["semester"])

    db.execute(
        "UPDATE students SET name=?, roll_number=?, branch=?, semester=? WHERE id=?",
        (name, roll_number, branch, semester, student_id),
    )
    db.commit()
    return jsonify(status="updated")


@app.route("/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    db = get_db()
    db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    db.commit()
    return jsonify(status="deleted")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
else:
    # Ensures the table exists when run under gunicorn / tests too.
    init_db()
