"""Telegram /feedback command handler for HalalCheckBot."""

from __future__ import annotations

import logging
import os
from html import escape
from urllib.parse import quote_plus

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

DEFAULT_FEEDBACK_URL = "https://github.com/SachaRM7/halalcheckbot/issues/new"


def _build_feedback_url(update: Update, message: str | None = None) -> str:
    """Build a feedback URL with optional prefilled content."""
    base_url = os.getenv("HALALCHECKBOT_FEEDBACK_URL", DEFAULT_FEEDBACK_URL).strip() or DEFAULT_FEEDBACK_URL

    user = update.effective_user
    username = f"@{user.username}" if user and user.username else "(no username)"

    if not message:
        return base_url

    title = quote_plus(f"Bot feedback from {username}")
    body = quote_plus(
        "## Feedback\n"
        f"{message}\n\n"
        "## Submitted from Telegram\n"
        f"- User ID: {user.id if user else 'unknown'}\n"
        f"- Username: {username}\n"
    )
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}title={title}&body={body}"


async def cmd_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /feedback command."""
    user = update.effective_user
    message = " ".join(context.args).strip() if context.args else ""
    feedback_url = _build_feedback_url(update, message or None)

    if message:
        logger.info(
            "Feedback shortcut requested by user_id=%s username=%s",
            user.id if user else "unknown",
            user.username if user else None,
        )
        response = (
            "💬 <b>Feedback</b>\n\n"
            "JAK! Tap the link below to send this feedback to the maintainers:\n"
            f"<a href=\"{escape(feedback_url)}\">Open feedback form</a>\n\n"
            "<b>Preview:</b>\n"
            f"<i>{escape(message)}</i>"
        )
    else:
        response = (
            "💬 <b>Send feedback</b>\n\n"
            "Share bugs, feature ideas, or corrections with the maintainers.\n\n"
            "Usage:\n"
            "<code>/feedback your message here</code>\n\n"
            f"Direct link: <a href=\"{escape(feedback_url)}\">Open feedback form</a>"
        )

    if update.message:
        await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True)
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.edit_message_text(response, parse_mode="HTML", disable_web_page_preview=True)
