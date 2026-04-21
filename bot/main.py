#!/usr/bin/env python3
"""HalalCheckBot — Telegram bot entry point."""

import os
import sys
import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# Ensure project root is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bot import handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    """Build and run the Telegram bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment")
        sys.exit(1)

    app = ApplicationBuilder().token(token).build()

    # Command handlers
    app.add_handler(CommandHandler("start", handlers.cmd_start))
    app.add_handler(CommandHandler("check", handlers.cmd_check))
    app.add_handler(CommandHandler("scan", handlers.cmd_scan))
    app.add_handler(CommandHandler("restaurant", handlers.cmd_restaurant))
    app.add_handler(CommandHandler("vote", handlers.cmd_vote))
    app.add_handler(CommandHandler("stats", handlers.cmd_stats))
    app.add_handler(CommandHandler("about", handlers.cmd_about))
    app.add_handler(CommandHandler("donate", handlers.cmd_donate))
    app.add_handler(CommandHandler("help", handlers.cmd_help))

    # Callback queries (inline keyboard)
    app.add_handler(CallbackQueryHandler(handlers.handle_callback))

    # Message handler for restaurant details submission
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handlers.handle_restaurant_details,
        )
    )

    logger.info("HalalCheckBot starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
