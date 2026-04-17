"""MiniMax AI classification for unknown halal/haram ingredients."""

import os
import json
import httpx
from typing import Optional

MINIMAX_API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")

ISLAMIC_CONTEXT = (
    "You are an Islamic scholar assistant specializing in halal/haram food classification. "
    "You classify ingredients based on Quran, Sahih Hadith, and established fiqh opinions "
    "(Hanafi, Maliki, Shafi'i, Hanbali). "
    "Classify ONLY as: halal, haram, mushbooh (doubtful), halal_if_no_alcohol. "
    "Key rules:\n"
    "- Pork in any form = haram\n"
    "- Alcohol (ethanol, wine, beer, etc.) = haram\n"
    "- Blood of any animal = haram\n"
    "- Carnivorous animals/birds of prey = haram\n"
    "- Animals not slaughtered properly = haram\n"
    "- Insects (except locusts) = disputed/haram in most schools\n"
    "- Gelatin (porcine source) = haram\n"
    "- L-cysteine (human hair) = haram\n"
    "- Carmine/cochineal (insect) = haram in many opinions\n"
    "- Vanilla extract (alcohol-based) = haram unless alcohol evaporates\n"
    "- Natural flavors labeled 'alcohol' = haram\n"
    "- Enzymes from animal sources = requires verification\n"
    "Return ONLY valid JSON: {\"status\": \"...\", \"confidence\": 0.0-1.0, \"explanation\": \"...\", \"source\": \"...\"}"
)


def classify_ingredient(ingredient_name: str) -> dict:
    """Classify an ingredient using MiniMax AI.

    Returns dict with: status, confidence, explanation, source.
    Falls back to 'mushbooh' if API unavailable.
    """
    if not MINIMAX_API_KEY:
        return {
            "status": "mushbooh",
            "confidence": 0.0,
            "explanation": "AI classification unavailable — no API key configured.",
            "source": "System",
        }

    prompt = (
        f"{ISLAMIC_CONTEXT}\n\n"
        f'Classify this ingredient: "{ingredient_name}"\n\n'
        f"Return ONLY valid JSON."
    )

    payload = {
        "model": "MiniMax-Text-01",
        "messages": [
            {"role": "system", "content": "You are a helpful Islamic halal classification assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }

    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(MINIMAX_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        # Try to extract JSON from response
        return _parse_ai_response(content)
    except Exception as e:
        return {
            "status": "mushbooh",
            "confidence": 0.0,
            "explanation": f"AI classification failed: {str(e)}",
            "source": "System",
        }


def _parse_ai_response(content: str) -> dict:
    """Parse JSON from AI response, handling markdown code blocks."""
    text = content.strip()
    # Remove markdown code block delimiters
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    try:
        result = json.loads(text)
        # Validate required fields
        if "status" in result and "confidence" in result:
            if result["status"] not in ("halal", "haram", "mushbooh", "halal_if_no_alcohol"):
                result["status"] = "mushbooh"
            if not (0.0 <= result.get("confidence", 0.0) <= 1.0):
                result["confidence"] = 0.5
            return {
                "status": result["status"],
                "confidence": float(result["confidence"]),
                "explanation": result.get("explanation", ""),
                "source": result.get("source", "MiniMax AI"),
            }
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from within text
    import re
    match = re.search(r'\{[^{}]*"status"\s*:\s*"(?:halal|haram|mushbooh|halal_if_no_alcohol)"[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            return {
                "status": result.get("status", "mushbooh"),
                "confidence": float(result.get("confidence", 0.5)),
                "explanation": result.get("explanation", ""),
                "source": result.get("source", "MiniMax AI"),
            }
        except Exception:
            pass

    return {
        "status": "mushbooh",
        "confidence": 0.0,
        "explanation": f"Could not parse AI response: {text[:200]}",
        "source": "MiniMax AI",
    }
