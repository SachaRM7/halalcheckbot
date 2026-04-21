"""Telegram /stats command handler for HalalCheckBot."""

from telegram import Update
from telegram.ext import ContextTypes

from . import database as db


def build_stats_message() -> str:
    """Build the /stats response message."""
    stats = db.get_stats()
    return (
        "📊 *HalalCheckBot Statistics*\n\n"
        f"🧪 Ingredients in database: {stats.get('ingredients', 0)}\n"
        f"🍽️ Restaurants: {stats.get('restaurants', 0)}\n"
        f"👤 Active users: {stats.get('users', 0)}\n\n"
        "_Help grow the database by contributing!_"
    )


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command."""
    del context
    message = update.effective_message
    if message is None:
        return
    await message.reply_text(build_stats_message(), parse_mode="Markdown")
