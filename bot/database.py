"""SQLite database operations for HalalCheckBot."""

import sqlite3
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "halalcheck.db")
SCHEMA = """
CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    name TEXT NOT NULL,
    status TEXT CHECK(status IN ('halal','haram','mushbooh','halal_if_no_alcohol')),
    category TEXT,
    explanation TEXT,
    source TEXT,
    confidence REAL DEFAULT 1.0,
    ai_generated INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    country TEXT,
    address TEXT,
    cuisine_type TEXT,
    halal_status TEXT,
    source_certification TEXT,
    trust_score REAL DEFAULT 0.0,
    total_votes INTEGER DEFAULT 0,
    submitter_tg_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_type TEXT CHECK(entry_type IN ('ingredient','restaurant')),
    entry_id INTEGER,
    tg_id TEXT,
    vote INTEGER CHECK(vote IN (-1, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entry_type, entry_id, tg_id)
);

CREATE TABLE IF NOT EXISTS users (
    tg_id TEXT PRIMARY KEY,
    username TEXT,
    checks_count INTEGER DEFAULT 0,
    contributions_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ingredients_name ON ingredients(name);
CREATE INDEX IF NOT EXISTS idx_ingredients_code ON ingredients(code);
CREATE INDEX IF NOT EXISTS idx_restaurants_city ON restaurants(city);
"""


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def get_ingredient_by_name(name: str) -> Optional[sqlite3.Row]:
    """Look up an ingredient by name (case-insensitive partial match)."""
    conn = get_connection()
    cur = conn.execute(
        "SELECT * FROM ingredients WHERE LOWER(name) = LOWER(?) LIMIT 1",
        (name.strip(),),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def search_ingredients(query: str, limit: int = 20) -> list[dict]:
    """Search ingredients by name (partial, case-insensitive)."""
    conn = get_connection()
    cur = conn.execute(
        "SELECT * FROM ingredients WHERE LOWER(name) LIKE LOWER(?) ORDER BY confidence DESC LIMIT ?",
        (f"%{query}%", limit),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_ingredient(
    code: Optional[str],
    name: str,
    status: str,
    category: str = "ingredient",
    explanation: str = "",
    source: str = "",
    confidence: float = 1.0,
    ai_generated: bool = False,
) -> int:
    """Insert or update an ingredient. Returns row ID."""
    conn = get_connection()
    if code is not None:
        # Normal case: upsert by code
        cur = conn.execute(
            """
            INSERT INTO ingredients (code, name, status, category, explanation, source, confidence, ai_generated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                name=excluded.name,
                status=excluded.status,
                category=excluded.category,
                explanation=excluded.explanation,
                source=excluded.source,
                confidence=excluded.confidence,
                ai_generated=excluded.ai_generated
            """,
            (code, name, status, category, explanation, source, confidence, int(ai_generated)),
        )
    else:
        # NULL code: check if ingredient with same name exists, otherwise insert
        cur = conn.execute(
            "SELECT id FROM ingredients WHERE name=? AND code IS NULL LIMIT 1",
            (name,),
        )
        existing = cur.fetchone()
        if existing:
            conn.execute(
                "UPDATE ingredients SET status=?, category=?, explanation=?, source=?, confidence=?, ai_generated=? WHERE id=?",
                (status, category, explanation, source, confidence, int(ai_generated), existing["id"]),
            )
            cur = conn.execute("SELECT ?", (existing["id"],))
        else:
            cur = conn.execute(
                "INSERT INTO ingredients (code, name, status, category, explanation, source, confidence, ai_generated) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (None, name, status, category, explanation, source, confidence, int(ai_generated)),
            )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def get_restaurants_by_city(city: str, limit: int = 10) -> list[dict]:
    """Search halal restaurants by city."""
    conn = get_connection()
    cur = conn.execute(
        "SELECT * FROM restaurants WHERE LOWER(city) LIKE LOWER(?) AND total_votes >= 5 ORDER BY trust_score DESC LIMIT ?",
        (f"%{city}%", limit),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_restaurant(
    name: str,
    city: str,
    country: str = "",
    address: str = "",
    cuisine_type: str = "",
    halal_status: str = "",
    source_certification: str = "",
    submitter_tg_id: str = "",
) -> int:
    """Add a new restaurant entry."""
    conn = get_connection()
    cur = conn.execute(
        """
        INSERT INTO restaurants (name, city, country, address, cuisine_type, halal_status, source_certification, submitter_tg_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, city, country, address, cuisine_type, halal_status, source_certification, submitter_tg_id),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def vote_entry(entry_type: str, entry_id: int, tg_id: str, vote: int) -> dict:
    """Cast or update a vote on an entry. Returns updated trust score."""
    conn = get_connection()

    # Check existing vote
    cur = conn.execute(
        "SELECT vote FROM votes WHERE entry_type=? AND entry_id=? AND tg_id=?",
        (entry_type, entry_id, tg_id),
    )
    existing = cur.fetchone()

    if existing:
        old_vote = existing["vote"]
        if old_vote == vote:
            # Remove vote (toggle off)
            conn.execute(
                "DELETE FROM votes WHERE entry_type=? AND entry_id=? AND tg_id=?",
                (entry_type, entry_id, tg_id),
            )
            delta = -vote
        else:
            # Change vote
            conn.execute(
                "UPDATE votes SET vote=? WHERE entry_type=? AND entry_id=? AND tg_id=?",
                (vote, entry_type, entry_id, tg_id),
            )
            delta = vote * 2
    else:
        # New vote
        conn.execute(
            "INSERT INTO votes (entry_type, entry_id, tg_id, vote) VALUES (?, ?, ?, ?)",
            (entry_type, entry_id, tg_id, vote),
        )
        delta = vote

    # Update trust score
    if entry_type == "restaurant":
        cur = conn.execute(
            "SELECT SUM(vote) as net, COUNT(*) as total FROM votes WHERE entry_type='restaurant' AND entry_id=?",
            (entry_id,),
        )
        row = cur.fetchone()
        net = row["net"] or 0
        total = row["total"] or 0
        trust_score = net / total if total > 0 else 0.0
        conn.execute(
            "UPDATE restaurants SET trust_score=?, total_votes=? WHERE id=?",
            (trust_score, total, entry_id),
        )
    elif entry_type == "ingredient":
        cur = conn.execute(
            "SELECT SUM(vote) as net, COUNT(*) as total FROM votes WHERE entry_type='ingredient' AND entry_id=?",
            (entry_id,),
        )
        row = cur.fetchone()
        net = row["net"] or 0
        total = row["total"] or 0
        confidence = max(0.0, min(1.0, (total + net) / (total * 2))) if total > 0 else 0.5
        conn.execute(
            "UPDATE ingredients SET confidence=? WHERE id=?",
            (confidence, entry_id),
        )
        trust_score = confidence

    conn.commit()
    conn.close()
    return {"trust_score": trust_score, "total_votes": total if entry_type == "restaurant" else None}


def get_or_create_user(tg_id: str, username: str = "") -> dict:
    """Get or create a user record."""
    conn = get_connection()
    cur = conn.execute(
        "SELECT * FROM users WHERE tg_id=?", (tg_id,)
    )
    row = cur.fetchone()
    if not row:
        conn.execute(
            "INSERT INTO users (tg_id, username) VALUES (?, ?)",
            (tg_id, username),
        )
        conn.commit()
        cur = conn.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,))
        row = cur.fetchone()
    conn.close()
    return dict(row)


def increment_user_checks(tg_id: str):
    """Increment the checks count for a user."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET checks_count = checks_count + 1 WHERE tg_id=?",
        (tg_id,),
    )
    conn.commit()
    conn.close()


def get_stats() -> dict:
    """Return database statistics."""
    conn = get_connection()
    stats = {}
    allowed_tables = {"ingredients", "restaurants", "users"}
    for table in ["ingredients", "restaurants", "users"]:
        if table not in allowed_tables:
            raise ValueError(f"Invalid table name: {table}")
        cur = conn.execute(f"SELECT COUNT(*) as cnt FROM {table}")
        stats[table] = cur.fetchone()["cnt"]
    conn.close()
    return stats
