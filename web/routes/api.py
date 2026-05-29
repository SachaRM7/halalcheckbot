"""REST API routes for HalalCheckBot."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from flask import Blueprint, request, jsonify, g
from bot import database as db

api_bp = Blueprint("api", __name__, url_prefix="/api")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me-in-production")


def require_auth():
    """Basic auth check for admin routes."""
    import secrets
    from flask import make_response
    auth = request.authorization
    if not auth or not secrets.compare_digest(auth.password or "", ADMIN_PASSWORD):
        return make_response("Unauthorized", 401)
    return None


@api_bp.route("/search", methods=["GET"])
def search_ingredients():
    """Search ingredients by name. GET /api/search?q=<query>"""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Missing query parameter 'q'"}), 400

    results = db.search_ingredients(q, limit=20)
    return jsonify({
        "query": q,
        "count": len(results),
        "results": results,
    })


@api_bp.route("/restaurants", methods=["GET"])
def search_restaurants():
    """Search restaurants by city. GET /api/restaurants?city=<city>"""
    city = request.args.get("city", "").strip()
    if not city:
        return jsonify({"error": "Missing query parameter 'city'"}), 400

    results = db.get_restaurants_by_city(city, limit=10)
    return jsonify({
        "city": city,
        "count": len(results),
        "restaurants": results,
    })


@api_bp.route("/stats", methods=["GET"])
def get_stats():
    """Return database statistics."""
    stats = db.get_stats()
    return jsonify(stats)


@api_bp.route("/contribute", methods=["POST"])
def contribute():
    """Submit a new ingredient or restaurant. POST /api/contribute"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    entry_type = data.get("type")
    if entry_type == "ingredient":
        row_id = db.add_ingredient(
            code=data.get("code"),
            name=data.get("name"),
            status=data.get("status", "mushbooh"),
            category=data.get("category", "ingredient"),
            explanation=data.get("explanation", ""),
            source=data.get("source", "Community contribution"),
            confidence=data.get("confidence", 0.5),
            ai_generated=False,
        )
        return jsonify({"success": True, "id": row_id, "type": "ingredient"})

    elif entry_type == "restaurant":
        row_id = db.add_restaurant(
            name=data.get("name"),
            city=data.get("city"),
            country=data.get("country", ""),
            address=data.get("address", ""),
            cuisine_type=data.get("cuisine_type", ""),
            halal_status=data.get("halal_status", ""),
            source_certification=data.get("source_certification", ""),
            submitter_tg_id=data.get("submitter_tg_id", ""),
        )
        return jsonify({"success": True, "id": row_id, "type": "restaurant"})

    return jsonify({"error": "Invalid type. Use 'ingredient' or 'restaurant'"}), 400


@api_bp.route("/vote", methods=["POST"])
def vote():
    """Submit a vote on an entry. POST /api/vote"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    entry_type = data.get("entry_type")
    entry_id = data.get("entry_id")
    tg_id = data.get("tg_id", "anonymous")
    vote_val = data.get("vote")

    if entry_type not in ("ingredient", "restaurant"):
        return jsonify({"error": "Invalid entry_type"}), 400
    if entry_id is None:
        return jsonify({"error": "Missing entry_id"}), 400
    if vote_val not in (-1, 1):
        return jsonify({"error": "Vote must be -1 or 1"}), 400

    result = db.vote_entry(entry_type, int(entry_id), str(tg_id), int(vote_val))
    return jsonify({"success": True, **result})


@api_bp.route("/admin/entries", methods=["GET"])
def admin_entries():
    """List all entries (requires admin auth)."""
    err = require_auth()
    if err:
        return err

    entry_type = request.args.get("type", "ingredients")
    limit = min(int(request.args.get("limit", 50)), 200)

    conn = db.get_connection()
    if entry_type == "restaurants":
        cur = conn.execute(
            "SELECT * FROM restaurants ORDER BY trust_score DESC LIMIT ?",
            (limit,),
        )
    else:
        cur = conn.execute(
            "SELECT * FROM ingredients ORDER BY confidence DESC LIMIT ?",
            (limit,),
        )
    rows = cur.fetchall()
    conn.close()

    return jsonify({
        "type": entry_type,
        "count": len(rows),
        "entries": [dict(r) for r in rows],
    })


@api_bp.route("/admin/export", methods=["GET"])
def admin_export():
    """Export entries as CSV (requires admin auth)."""
    err = require_auth()
    if err:
        return err

    import csv
    import io

    entry_type = request.args.get("type", "ingredients")

    conn = db.get_connection()
    if entry_type == "restaurants":
        cur = conn.execute("SELECT * FROM restaurants ORDER BY id")
    else:
        cur = conn.execute("SELECT * FROM ingredients ORDER BY id")
    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))

    from flask import Response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={entry_type}.csv"},
    )
