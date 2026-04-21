"""Telegram command handlers for HalalCheckBot."""

import os
import io
import logging
import threading
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from . import database as db
from . import classifier
from . import ocr_processor
from . import keyboards as kb


logger = logging.getLogger(__name__)

# Rate limiting: user_id -> (count, window_start) — protected by asyncio.Lock
AI_CHECK_RATELIMIT = {}
RATE_LIMIT_COUNT = 10
RATE_LIMIT_WINDOW = 3600  # 1 hour
_ai_rate_lock = threading.Lock()


def _check_ai_rate_limit(tg_id: str) -> bool:
    """Check if user is within AI check rate limit. Returns True if allowed."""
    import time
    now = time.time()
    key = tg_id
    with _ai_rate_lock:
        if key in AI_CHECK_RATELIMIT:
            count, window_start = AI_CHECK_RATELIMIT[key]
            if now - window_start < RATE_LIMIT_WINDOW:
                if count >= RATE_LIMIT_COUNT:
                    return False
                AI_CHECK_RATELIMIT[key] = (count + 1, window_start)
            else:
                AI_CHECK_RATELIMIT[key] = (1, now)
        else:
            AI_CHECK_RATELIMIT[key] = (1, now)
    return True


STATUS_EMOJI = {
    "halal": "✅",
    "haram": "❌",
    "mushbooh": "⚠️",
    "halal_if_no_alcohol": "🔶",
}

STATUS_TEXT = {
    "halal": "HALAL",
    "haram": "HARAM (forbidden)",
    "mushbooh": "MUSHB OOH (doubtful)",
    "halal_if_no_alcohol": "HALAL (if no alcohol present)",
}


def _format_ingredient_result(ingredient: dict) -> str:
    """Format a single ingredient result as a Telegram message."""
    status = ingredient["status"]
    emoji = STATUS_EMOJI.get(status, "❓")
    status_label = STATUS_TEXT.get(status, status.upper())

    msg = f"{emoji} *{ingredient['name']}* — *{status_label}*\n\n"
    if ingredient.get("explanation"):
        msg += f"📝 {ingredient['explanation']}\n"
    if ingredient.get("source"):
        msg += f"📖 Source: {ingredient['source']}\n"
    if ingredient.get("category"):
        msg += f"🏷️ Category: {ingredient['category']}\n"
    if ingredient.get("code"):
        msg += f"🔢 Code: {ingredient['code']}\n"
    msg += f"📊 Confidence: {ingredient.get('confidence', 1.0):.0%}"
    return msg


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    db.get_or_create_user(str(user.id), user.username or "")

    welcome = (
        "🕌 *Assalamu Alaikum!* Welcome to *HalalCheckBot*\n\n"
        "This bot helps you verify if food ingredients and restaurants are halal (permissible) "
        "according to Islamic guidelines.\n\n"
        "*Available commands:*\n"
        "• /check \<ingredient\> — Verify an ingredient\n"
        "• /scan — Upload a product photo for OCR\n"
        "• /restaurant \<city\> — Find halal restaurants\n"
        "• /restaurant add — Add a new restaurant\n"
        "• /vote \<id\> \<up/down\> — Vote on community entries\n"
        "• /stats — View database statistics\n"
        "• /about — About this project\n\n"
        "🔒 *Note:* Always verify critical decisions with trusted scholars. "
        "This tool assists but does not replace Islamic authority.\n\n"
        "*JAK!* (Thank you — Malay)"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown", reply_markup=kb.main_menu_keyboard())


async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /check command."""
    if not context.args:
        await update.message.reply_text(
            "Usage: /check \<ingredient name\>\n"
            "Example: /check gelatin\n"
            "You can also check multiple ingredients:\n"
            "/check sugar, salt, gelatin"
        )
        return

    user = update.effective_user
    db.get_or_create_user(str(user.id), user.username or "")
    db.increment_user_checks(str(user.id))

    raw_input = " ".join(context.args)
    ingredients_raw = [i.strip() for i in raw_input.split(",")]

    for ingredient_name in ingredients_raw:
        if not ingredient_name:
            continue

        # Look up in database
        result = db.get_ingredient_by_name(ingredient_name)

        if result:
            msg = _format_ingredient_result(result)
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            # Not in DB — try AI classification
            if not _check_ai_rate_limit(str(user.id)):
                await update.message.reply_text(
                    "⚠️ You've reached the AI check limit (10/hour). "
                    "Try again later or submit this ingredient to the community."
                )
                return

            await update.message.reply_text(f"🔍 '{ingredient_name}' not found in database. Consulting AI scholar...")
            ai_result = classifier.classify_ingredient(ingredient_name)

            ai_result["name"] = ingredient_name
            ai_result["ai_generated"] = 1
            row_id = db.add_ingredient(
                code=None,
                name=ingredient_name,
                status=ai_result["status"],
                category="ingredient",
                explanation=ai_result.get("explanation", ""),
                source=ai_result.get("source", "MiniMax AI"),
                confidence=ai_result.get("confidence", 0.5),
                ai_generated=True,
            )
            ai_result["id"] = row_id

            msg = _format_ingredient_result(ai_result)
            msg += "\n\n_(This result was generated by AI and cached for future use)_"
            await update.message.reply_text(msg, parse_mode="Markdown")

        db.increment_user_checks(str(user.id))


async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /scan command — receive photo and perform OCR."""
    if not update.message.photo:
        await update.message.reply_text(
            "📷 Please send a photo of the product's ingredient list with the /scan command.\n"
            "Example: send a photo, then type /scan"
        )
        return

    user = update.effective_user
    db.get_or_create_user(str(user.id), user.username or "")

    await update.message.reply_text("📷 Processing image...")

    try:
        # Get largest photo
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        image_bytes = await photo_file.download_as_bytearray()

        ingredients = ocr_processor.extract_ingredients_from_image(bytes(image_bytes))

        if not ingredients:
            await update.message.reply_text(
                "❌ Could not extract ingredients from this image. "
                "Please try with a clearer photo of the ingredient list."
            )
            return

        await update.message.reply_text(
            f"🔍 Found {len(ingredients)} ingredient(s). Checking each..."
        )

        for ingredient_name in ingredients[:20]:  # Limit to 20 per scan
            result = db.get_ingredient_by_name(ingredient_name)
            if result:
                msg = _format_ingredient_result(result)
            else:
                if not _check_ai_rate_limit(str(user.id)):
                    msg = f"⚠️ Rate limited for {ingredient_name}"
                else:
                    ai_result = classifier.classify_ingredient(ingredient_name)
                    db.add_ingredient(
                        code=None,
                        name=ingredient_name,
                        status=ai_result["status"],
                        explanation=ai_result.get("explanation", ""),
                        source=ai_result.get("source", "MiniMax AI"),
                        confidence=ai_result.get("confidence", 0.5),
                        ai_generated=True,
                    )
                    ai_result["name"] = ingredient_name
                    msg = _format_ingredient_result(ai_result)
                    msg += "\n_(AI-generated)_"

            await update.message.reply_text(msg, parse_mode="Markdown")

    except RuntimeError as e:
        await update.message.reply_text(f"OCR Error: {e}")
    except Exception as e:
        logger.error(f"OCR error: {e}")
        await update.message.reply_text("❌ Error processing image. Please try again.")


async def cmd_restaurant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /restaurant command — search or add restaurants."""
    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/restaurant \<city\> — Search halal restaurants\n"
            "/restaurant add — Add a new restaurant (interactive)"
        )
        return

    subcommand = context.args[0].lower()
    if subcommand == "add":
        await cmd_restaurant_add(update, context)
    else:
        city = " ".join(context.args)
        await cmd_restaurant_search(update, city)


async def cmd_restaurant_search(update: Update, city: str):
    """Search for halal restaurants in a city."""
    restaurants = db.get_restaurants_by_city(city)

    if not restaurants:
        await update.message.reply_text(
            f"🍽️ No restaurants found for *{city}*.\n"
            f"Be the first to add one: /restaurant add",
            parse_mode="Markdown",
        )
        return

    msg = f"🍽️ *Halal Restaurants in {city}*\n\n"
    for r in restaurants:
        trust = r.get("trust_score", 0)
        stars = "⭐" * max(1, int(trust * 5))
        msg += (
            f"*{r['name']}* {stars}\n"
            f"📍 {r.get('address', 'N/A')}\n"
            f"🏷️ {r.get('cuisine_type', 'N/A')}\n"
            f"🕌 Status: {r.get('halal_status', 'Unknown')}\n"
            f"📊 Trust: {trust:.0%} ({r.get('total_votes', 0)} votes)\n\n"
        )

    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_restaurant_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Interactive restaurant addition via conversation."""
    await update.message.reply_text(
        "🏨 *Add Restaurant*\n\n"
        "Please reply with restaurant details in this format:\n"
        "`name | city | country | address | cuisine_type | halal_status | certification`\n\n"
        "Example:\n"
        "`Al-Madina Restaurant | Paris | France | 12 Rue de Rivoli | Middle Eastern | Certified Halal | AFIA France`"
    )
    # Store context for next message handler
    context.user_data["awaiting_restaurant"] = True


async def handle_restaurant_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming restaurant details from user."""
    if not context.user_data.get("awaiting_restaurant"):
        return None

    parts = update.message.text.split("|")
    if len(parts) < 4:
        await update.message.reply_text(
            "❌ Invalid format. Please use:\n"
            "`name | city | country | address | cuisine_type | halal_status | certification`"
        )
        return

    name, city, country = [p.strip() for p in parts[:3]]
    address = parts[3].strip() if len(parts) > 3 else ""
    cuisine = parts[4].strip() if len(parts) > 4 else ""
    halal_status = parts[5].strip() if len(parts) > 5 else ""
    certification = parts[6].strip() if len(parts) > 6 else ""

    user = update.effective_user
    row_id = db.add_restaurant(
        name=name,
        city=city,
        country=country,
        address=address,
        cuisine_type=cuisine,
        halal_status=halal_status,
        source_certification=certification,
        submitter_tg_id=str(user.id),
    )

    context.user_data["awaiting_restaurant"] = False

    await update.message.reply_text(
        f"✅ Restaurant added! ID: `{row_id}`\n"
        f"Help others find it: /vote restaurant_{row_id} up",
        parse_mode="Markdown",
    )
    return True


async def cmd_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /vote command."""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /vote \<entry_id\> \<up|down\>\n"
            "Example: /vote restaurant_42 up\n"
            "Example: /vote ingredient_15 down"
        )
        return

    user = update.effective_user
    entry_ref = context.args[0]  # e.g. "restaurant_42" or "ingredient_15"
    vote_str = context.args[1].lower()

    if vote_str not in ("up", "down"):
        await update.message.reply_text("Vote must be 'up' or 'down'")
        return

    vote = 1 if vote_str == "up" else -1

    # Parse entry type and ID
    parts = entry_ref.split("_")
    if len(parts) < 2:
        await update.message.reply_text("Invalid entry format. Use: restaurant_N or ingredient_N")
        return

    entry_type = parts[0]
    try:
        entry_id = int(parts[1])
    except ValueError:
        await update.message.reply_text("Invalid entry ID")
        return

    if entry_type not in ("restaurant", "ingredient"):
        await update.message.reply_text("Entry type must be 'restaurant' or 'ingredient'")
        return

    result = db.vote_entry(entry_type, entry_id, str(user.id), vote)

    await update.message.reply_text(
        f"✅ Vote recorded!\n"
        f"Trust score: {result['trust_score']:.0%}\n"
        f"Total votes: {result.get('total_votes', 'N/A')}",
        parse_mode="Markdown",
    )


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command."""
    stats = db.get_stats()
    await update.message.reply_text(
        "📊 *HalalCheckBot Statistics*\n\n"
        f"🧪 Ingredients in database: {stats.get('ingredients', 0)}\n"
        f"🍽️ Restaurants: {stats.get('restaurants', 0)}\n"
        f"👤 Active users: {stats.get('users', 0)}\n\n"
        "_Help grow the database by contributing!_",
        parse_mode="Markdown",
    )


async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command."""
    about = (
        "🕌 *HalalCheckBot*\n\n"
        "An *open-source*, community-driven halal verification tool.\n\n"
        "*What we do:*\n"
        "• Verify ingredients against Islamic guidelines\n"
        "• Help find halal restaurants worldwide\n"
        "• Community voting to ensure transparency\n"
        "• AI-assisted classification with scholarly sources\n\n"
        "*Legal disclaimer:*\n"
        "This bot provides informational assistance only. "
        "Always consult qualified Islamic scholars for definitive rulings. "
        "The developers accept no liability for food choices made based on this bot's output.\n\n"
        "*Open source:*\n"
        "github.com/oummah/halalcheckbot\n\n"
        "_Built with ❤️ for the Oummah (Muslim community)_"
    )
    await update.message.reply_text(about, parse_mode="Markdown")


async def cmd_donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /donate command."""
    await update.message.reply_text(
        "💚 *Support HalalCheckBot*\n\n"
        "This project is free and open-source. "
        "Help us maintain the servers and expand the database.\n\n"
        "🔗 Donation link: [coming soon]\n\n"
        "_JAK for your generosity!_",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "🕌 *HalalCheckBot — Available Commands*\n\n"
        "*Ingredient Verification*\n"
        "• /check <ingredient> — Verify if an ingredient is halal\n"
        "• /scan — Upload a photo of a product for OCR analysis\n\n"
        "*Restaurant Search*\n"
        "• /restaurant <city> — Find halal restaurants in a city\n"
        "• /restaurant add — Add a new restaurant to the database\n\n"
        "*Community*\n"
        "• /vote <id> <up/down> — Vote on community submissions\n\n"
        "*Information*\n"
        "• /stats — View bot statistics\n"
        "• /about — About HalalCheckBot\n"
        "• /help — Show this help message\n\n"
        "_Use /start to see the main menu_"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callbacks."""
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = query.data

    if data == "main_menu":
        await cmd_start(update, context)
    elif data == "cmd_check":
        await query.edit_message_text("🔍 Send me an ingredient name using /check \<name\>")
    elif data == "cmd_scan":
        await query.edit_message_text("📷 Send me a product photo, then type /scan")
    elif data == "cmd_restaurant":
        await query.edit_message_text("🍽️ Send me a city name: /restaurant \<city\>")
    elif data == "cmd_stats":
        await cmd_stats(update, context)
    elif data.startswith("vote_"):
        # Parse vote callback: vote_restaurant_42_1
        parts = data.split("_")
        if len(parts) == 4:
            entry_type, entry_id, vote_str = parts[1], parts[2], parts[3]
            vote = int(vote_str)
            result = db.vote_entry(entry_type, int(entry_id), str(query.from_user.id), vote)
            await query.edit_message_text(
                f"✅ Vote recorded!\nTrust score: {result['trust_score']:.0%}"
            )
