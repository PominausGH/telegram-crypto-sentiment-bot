#!/usr/bin/env python3
"""
Crypto Sentiment Monitor Bot

A Telegram bot that monitors cryptocurrency sentiment from Reddit.
"""

import logging
import sys

from telebot import TeleBot

from config import Config
from bot.handlers import setup_handlers
from bot.scheduler import setup_scheduler
from data.models import init_db


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> None:
    """Main entry point for the bot."""
    setup_logging()
    logger = logging.getLogger(__name__)

    # Validate configuration
    missing = Config.validate()
    if missing:
        logger.error(f"Missing required configuration: {', '.join(missing)}")
        logger.error("Please copy .env.example to .env and fill in the values.")
        sys.exit(1)

    # Initialize database
    init_db()

    # Create bot instance
    bot = TeleBot(Config.TELEGRAM_BOT_TOKEN)
    logger.info("Bot instance created")

    # Register handlers
    setup_handlers(bot)

    # Start scheduler for periodic sentiment checks
    scheduler = setup_scheduler(bot)

    # Start polling
    logger.info("Starting bot polling...")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    main()
