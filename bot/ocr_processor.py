"""OCR processing for HalalCheckBot — extracts ingredient lists from product photos."""

import io
import os
import re
from typing import Optional

try:
    from PIL import Image
    import pytesseract

    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


def preprocess_image(image_bytes: bytes) -> Image.Image:
    """Convert image bytes to a PIL Image, preprocessed for OCR."""
    if not PYTESSERACT_AVAILABLE:
        raise RuntimeError("pytesseract or Pillow not installed")

    img = Image.open(io.BytesIO(image_bytes))

    # Convert to grayscale
    img = img.convert("L")

    # Auto-rotate if needed (pytesseract can detect orientation)
    try:
        osd = pytesseract.image_to_osd(img)
        rotation = int(re.search(r"Rotate: (\d+)", osd).group(1)) if re.search(r"Rotate: (\d+)", osd) else 0
        img = img.rotate(-rotation, expand=True)
    except Exception:
        pass  # Orientation detection failed, continue

    # Apply threshold to increase contrast
    img = img.point(lambda x: 0 if x < 128 else 255)
    return img


def extract_ingredients_from_image(image_bytes: bytes) -> list[str]:
    """Extract ingredient list from a product label image.

    Returns a list of individual ingredient names.
    """
    if not PYTESSERACT_AVAILABLE:
        raise RuntimeError("pytesseract or Pillow not installed. Run: pip install pytesseract Pillow")

    img = preprocess_image(image_bytes)
    raw_text = pytesseract.image_to_string(img)

    ingredients = parse_ingredients_text(raw_text)
    return ingredients


def parse_ingredients_text(text: str) -> list[str]:
    """Parse raw OCR text and extract individual ingredient names.

    Handles common formats:
    - "Ingredients: water, sugar, salt, ..."
    - "Water, Sugar, Salt, ..."
    - "Contains: ..."
    """
    # Normalize whitespace
    text = text.replace("\n", " ").replace("\r", " ")

    # Find the ingredients section
    patterns = [
        r"(?:ingredients|substances|mengandungi)[\s:]+(.+?)(?:\.|$)",
        r"^(.+?)(?:ingredients|substances|$)",
    ]

    section = text
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            section = match.group(1)
            break

    # Split by common delimiters: comma, semicolon, bullet points
    items = re.split(r"[,;•·\-\–\—]+", section)

    results = []
    for item in items:
        # Clean up each ingredient
        name = item.strip()
        # Remove leading numbers, asterisks, parentheses content that are just quantities
        name = re.sub(r"^\d+\.?\s*", "", name)
        name = re.sub(r"\s*\(\s*\d+[a-zA-Z]*\s*\)\s*$", "", name)
        name = re.sub(r"^\*\s*", "", name)
        name = name.strip(" .*")

        # Skip very short or empty items
        if len(name) < 2:
            continue
        # Skip items that look like quantities (e.g. "12g", "100ml")
        if re.match(r"^\d+\s*(g|ml|mg|kg|%|mcg)", name, re.IGNORECASE):
            continue

        results.append(name)

    return results
