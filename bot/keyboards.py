"""Inline keyboards for HalalCheckBot Telegram responses."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def status_keyboard(status: str, entry_type: str, entry_id: int) -> InlineKeyboardMarkup:
    """Voting keyboard for ingredient/restaurant entries."""
    keyboard = [
        [
            InlineKeyboardButton("👍 upvote", callback_data=f"vote_{entry_type}_{entry_id}_1"),
            InlineKeyboardButton("👎 downvote", callback_data=f"vote_{entry_type}_{entry_id}_-1"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def check_result_keyboard(ingredient_name: str) -> InlineKeyboardMarkup:
    """Keyboard shown after ingredient check."""
    keyboard = [
        [InlineKeyboardButton("🔍 Check another", callback_data="check_another")],
        [InlineKeyboardButton("📍 Find halal restaurant", callback_data="search_restaurant")],
        [InlineKeyboardButton("🏠 Main menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def restaurant_keyboard(restaurant_id: int) -> InlineKeyboardMarkup:
    """Keyboard for restaurant entries."""
    keyboard = [
        [
            InlineKeyboardButton("👍 upvote", callback_data=f"vote_restaurant_{restaurant_id}_1"),
            InlineKeyboardButton("👎 downvote", callback_data=f"vote_restaurant_{restaurant_id}_-1"),
        ],
        [InlineKeyboardButton("🏠 Main menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("🔍 Check ingredient", callback_data="cmd_check")],
        [InlineKeyboardButton("📷 OCR scan", callback_data="cmd_scan")],
        [InlineKeyboardButton("🍽️ Find restaurant", callback_data="cmd_restaurant")],
        [InlineKeyboardButton("📊 Statistics", callback_data="cmd_stats")],
        [InlineKeyboardButton("💬 Feedback", callback_data="cmd_feedback")],
    ]
    return InlineKeyboardMarkup(keyboard)
