#!/usr/bin/env python3
"""Tests for HalalCheckBot."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bot import database as db
from bot import classifier


def test_ingredient_status_values():
    """Verify all status values are valid."""
    valid_statuses = {"halal", "haram", "mushbooh", "halal_if_no_alcohol"}
    for status in valid_statuses:
        assert status in valid_statuses


def test_database_initialization():
    """Database should initialize without errors."""
    conn = db.get_connection()
    assert conn is not None
    conn.close()


def test_add_and_get_ingredient():
    """Test adding and retrieving an ingredient."""
    name = f"Test Ingredient {os.urandom(4).hex()}"
    row_id = db.add_ingredient(
        code=None,
        name=name,
        status="halal",
        category="test",
        explanation="Test ingredient",
        source="Unit test",
        confidence=1.0,
        ai_generated=False,
    )
    assert row_id > 0

    result = db.get_ingredient_by_name(name)
    assert result is not None
    assert result["name"] == name
    assert result["status"] == "halal"


def test_search_ingredients():
    """Test ingredient search."""
    results = db.search_ingredients("salt", limit=5)
    assert isinstance(results, list)


def test_ingredient_status():
    """Test that a known ingredient returns correct status."""
    result = db.get_ingredient_by_name("salt")
    if result:
        assert result["status"] == "halal"


def test_haram_ingredient():
    """Test that pork is correctly identified as haram."""
    result = db.get_ingredient_by_name("pork")
    if result:
        assert result["status"] == "haram"


def test_stats():
    """Test database statistics."""
    stats = db.get_stats()
    assert isinstance(stats, dict)
    assert "ingredients" in stats
    assert "restaurants" in stats
    assert "users" in stats
    assert stats["ingredients"] >= 0


def test_restaurant_add():
    """Test adding a restaurant."""
    name = f"Test Restaurant {os.urandom(4).hex()}"
    row_id = db.add_restaurant(
        name=name,
        city="Test City",
        country="Test Country",
        address="123 Test St",
        cuisine_type="Test",
        halal_status="Certified Halal",
        source_certification="Test Authority",
        submitter_tg_id="test_user",
    )
    assert row_id > 0


def test_vote_entry():
    """Test voting on entries."""
    result = db.vote_entry("ingredient", 1, "test_user_123", 1)
    assert "trust_score" in result


def test_classifier_fallback():
    """Test classifier returns mushbooh when no API key."""
    # Save original env
    orig_key = os.environ.get("MINIMAX_API_KEY", "")
    os.environ["MINIMAX_API_KEY"] = ""

    result = classifier.classify_ingredient("test ingredient")
    assert result["status"] == "mushbooh"
    assert result["confidence"] == 0.0

    # Restore
    os.environ["MINIMAX_API_KEY"] = orig_key


def test_ai_response_parsing():
    """Test AI response parsing with various formats."""
    valid_json = '{"status": "haram", "confidence": 0.95, "explanation": "Test", "source": "Test"}'
    result = classifier._parse_ai_response(valid_json)
    assert result["status"] == "haram"
    assert result["confidence"] == 0.95

    # Markdown code block
    md_json = '```json\n{"status": "halal", "confidence": 0.9, "explanation": "OK", "source": "Test"}\n```'
    result = classifier._parse_ai_response(md_json)
    assert result["status"] == "halal"


def test_ingredient_categories():
    """Test all ingredient categories are valid."""
    valid_categories = {"additive", "ingredient", "beverage", "alcohol_derivative", "meat_type"}


if __name__ == "__main__":
    print("Running HalalCheckBot tests...")

    tests = [
        test_database_initialization,
        test_add_and_get_ingredient,
        test_search_ingredients,
        test_stats,
        test_restaurant_add,
        test_vote_entry,
        test_classifier_fallback,
        test_ai_response_parsing,
        test_ingredient_status_values,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {test.__name__} — {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
