from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import os
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.secret_key = "smartspend-secret-key-change-in-production"
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")

# ─── Database Setup ───────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                amount    REAL    NOT NULL,
                category  TEXT    NOT NULL,
                note      TEXT    DEFAULT '',
                date      TEXT    NOT NULL,
                created_at TEXT   DEFAULT (datetime('now'))
            )
        """)
        # ── NEW: users table ──────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL,
                email      TEXT    NOT NULL UNIQUE,
                password   TEXT    NOT NULL,
                created_at TEXT    DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

init_db()

# ─── Helpers ──────────────────────────────────────────────────────────────────

CATEGORIES = ["Food", "Travel", "Shopping", "Entertainment",
              "Healthcare", "Utilities", "Education", "Other"]

CATEGORY_TIPS = {
    "Food":          ("🍽️", "Cook at home more often to cut food costs by up to 60%."),
    "Travel":        ("✈️", "Use public transport or carpool to reduce travel spend."),
    "Shopping":      ("🛍️", "Try a 24-hour rule — wait a day before buying non-essentials."),
    "Entertainment": ("🎬", "Look for free or discounted events in your area."),
    "Healthcare":    ("💊", "Schedule preventive check-ups to avoid bigger costs later."),
    "Utilities":     ("⚡", "Unplug devices when not in use to lower your utility bill."),
    "Education":     ("📚", "Explore free resources like Coursera audits or YouTube."),
    "Other":         ("📦", "Track what's in 'Other' — you might find hidden patterns."),
}

def rows_to_list(rows):
    return [dict(r) for r in rows]

# ─── AI / Analytics Engine ────────────────────────────────────────────────────

def generate_insights(expenses):
    if not expenses:
        return {
            "top_category": None,
            "trend": "neutral",
            "trend_label": "No data yet",
            "suggestions": ["Start adding expenses to get personalised insights!"],
            "category_totals": {},
            "monthly_totals": {},
            "avg_daily": 0,
        }

    # Category totals
    cat_totals = {}
    for e in expenses:
        cat = e["category"]
        cat_totals[cat] = cat_totals.get(cat, 0) + e["amount"]

    top_cat = max(cat_totals, key=cat_totals.get)

    # Monthly totals (last 6 months)
    monthly = {}
    for e in expenses:
        month = e["date"][:7]  # YYYY-MM
        monthly[month] = monthly.get(month, 0) + e["amount"]

    sorted_months = sorted(monthly.keys())

    # Trend detection (compare last 2 months)
    trend = "neutral"
    trend_label = "Steady spending"
    if len(sorted_months) >= 2:
        prev = monthly[sorted_months[-2]]
        curr = monthly[sorted_months[-1]]
        pct = ((curr - prev) / prev * 100) if prev else 0
        if pct > 10:
            trend = "up"
            trend_label = f"↑ {pct:.0f}% vs last month"
        elif pct < -10:
            trend = "down"
            trend_label = f"↓ {abs(pct):.0f}% vs last month"
        else:
            trend_label = f"~{pct:+.0f}% vs last month"

    # Average daily spend (last 30 days)
    thirty_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    recent = [e["amount"] for e in expenses if e["date"] >= thirty_ago]
    avg_daily = sum(recent) / 30 if recent else 0

    # Suggestions
    suggestions = []
    if top_cat:
        _, tip = CATEGORY_TIPS.get(top_cat, ("💡", "Review your top spending category."))
        suggestions.append(f"Your top spend is <strong>{top_cat}</strong> (₹{cat_totals[top_cat]:,.0f}). {tip}")

    if avg_daily > 500:
        suggestions.append(f"You're averaging <strong>₹{avg_daily:.0f}/day</strong>. Setting a daily budget of ₹400 could save ₹{(avg_daily - 400) * 30:,.0f}/month.")

    if trend == "up":
        suggestions.append("Your spending is <strong>rising</strong> this month. Review recent transactions to find quick wins.")

    if len(cat_totals) == 1:
        suggestions.append("Try categorising expenses more granularly to spot saving opportunities.")

    if not suggestions:
        suggestions.append("Great job! Your spending looks balanced across categories. 🎉")

    return {
        "top_category": top_cat,
        "top_category_icon": CATEGORY_TIPS.get(top_cat, ("📊", ""))[0] if top_cat else "📊",
        "trend": trend,
        "trend_label": trend_label,
        "suggestions": suggestions,
        "category_totals": cat_totals,
        "monthly_totals": {m: round(monthly[m], 2) for m in sorted(monthly)},
        "avg_daily": round(avg_daily, 2),
    }

# ─── Routes ───────────────────────────────────────────────────────────────────

# ── NEW: login_required decorator ────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ── NEW: Register ─────────────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            error = "All fields are required."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        else:
            hashed = generate_password_hash(password)
            try:
                with get_db() as conn:
                    conn.execute(
                        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                        (name, email, hashed)
                    )
                    conn.commit()
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                error = "An account with this email already exists."

    return render_template("register.html", error=error)

# ── NEW: Login ────────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"]   = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("index"))
        else:
            error = "Invalid email or password."

    return render_template("login.html", error=error)

# ── NEW: Logout ───────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required                          # ← only change to existing route
def index():
    return render_template("index.html", categories=CATEGORIES, user_name=session.get("user_name", ""))

# GET all expenses (with optional filters)
@app.route("/api/expenses", methods=["GET"])
def get_expenses():
    month   = request.args.get("month")   # YYYY-MM
    category = request.args.get("category")
    with get_db() as conn:
        q = "SELECT * FROM expenses WHERE 1=1"
        params = []
        if month:
            q += " AND date LIKE ?"
            params.append(f"{month}%")
        if category:
            q += " AND category = ?"
            params.append(category)
        q += " ORDER BY date DESC, id DESC"
        rows = conn.execute(q, params).fetchall()
    return jsonify(rows_to_list(rows))

# POST add expense
@app.route("/api/expenses", methods=["POST"])
def add_expense():
    data = request.get_json()
    amount   = float(data.get("amount", 0))
    category = data.get("category", "Other")
    note     = data.get("note", "")
    date     = data.get("date", datetime.now().strftime("%Y-%m-%d"))

    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400
    if category not in CATEGORIES:
        return jsonify({"error": "Invalid category"}), 400

    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO expenses (amount, category, note, date) VALUES (?, ?, ?, ?)",
            (amount, category, note, date)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM expenses WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

# DELETE expense
@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    with get_db() as conn:
        affected = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,)).rowcount
        conn.commit()
    if affected == 0:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"deleted": expense_id})

# GET insights / analytics
@app.route("/api/insights", methods=["GET"])
def get_insights():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM expenses ORDER BY date").fetchall()
    insights = generate_insights(rows_to_list(rows))
    return jsonify(insights)

# GET summary stats
@app.route("/api/summary", methods=["GET"])
def get_summary():
    with get_db() as conn:
        total     = conn.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0]
        this_month = datetime.now().strftime("%Y-%m")
        monthly   = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE date LIKE ?",
            (f"{this_month}%",)
        ).fetchone()[0]
        count     = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    return jsonify({"total": round(total, 2), "this_month": round(monthly, 2), "count": count})

# GET categories list
@app.route("/api/categories", methods=["GET"])
def get_categories():
    return jsonify(CATEGORIES)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
