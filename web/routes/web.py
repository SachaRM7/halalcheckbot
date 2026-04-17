"""Web page routes for HalalCheckBot."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from bot import database as db

web_bp = Blueprint("web", __name__)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me-in-production")


@web_bp.route("/")
def index():
    """Landing page with search."""
    stats = db.get_stats()
    return render_template(
        "index.html",
        stats=stats,
        search_query=request.args.get("q", ""),
    )


@web_bp.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    """Community contribution dashboard."""
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["admin_authenticated"] = True
            flash("Logged in as admin.", "success")
        else:
            flash("Invalid password.", "error")
        return redirect(url_for("web.dashboard"))

    authenticated = session.get("admin_authenticated", False)

    conn = db.get_connection()
    cur = conn.execute("SELECT COUNT(*) as cnt FROM ingredients")
    ingredient_count = cur.fetchone()["cnt"]
    cur = conn.execute("SELECT COUNT(*) as cnt FROM restaurants")
    restaurant_count = cur.fetchone()["cnt"]
    cur = conn.execute("SELECT COUNT(*) as cnt FROM users")
    user_count = cur.fetchone()["cnt"]
    conn.close()

    return render_template(
        "dashboard.html",
        authenticated=authenticated,
        ingredient_count=ingredient_count,
        restaurant_count=restaurant_count,
        user_count=user_count,
    )


@web_bp.route("/admin")
def admin():
    """Admin panel (requires auth)."""
    if not session.get("admin_authenticated"):
        flash("Please log in first.", "error")
        return redirect(url_for("web.dashboard"))

    conn = db.get_connection()
    cur = conn.execute("SELECT * FROM ingredients ORDER BY id DESC LIMIT 100")
    ingredients = [dict(r) for r in cur.fetchall()]
    cur = conn.execute("SELECT * FROM restaurants ORDER BY id DESC LIMIT 100")
    restaurants = [dict(r) for r in cur.fetchall()]
    conn.close()

    return render_template(
        "dashboard.html",
        authenticated=True,
        ingredients=ingredients,
        restaurants=restaurants,
    )


@web_bp.route("/logout")
def logout():
    """Log out admin."""
    session.pop("admin_authenticated", None)
    flash("Logged out.", "info")
    return redirect(url_for("web.dashboard"))
