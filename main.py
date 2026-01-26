#!/usr/bin/env python3
"""
Crypto Sentiment Monitor Bot

A Telegram bot that monitors cryptocurrency sentiment from Reddit.
"""

import logging
import signal
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from telebot import TeleBot
from telebot.apihelper import ApiTelegramException

from bot.handlers import set_start_time, setup_handlers
from bot.scheduler import setup_scheduler
from config import Config
from data.models import init_db

# Global references for graceful shutdown
_bot: TeleBot | None = None
_scheduler = None
_shutdown_requested = False


def setup_logging() -> None:
    """Configure logging for the application with file rotation."""
    log_level = getattr(logging, Config.LOG_LEVEL, logging.INFO)

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Create formatters
    console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_format = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

    console_formatter = logging.Formatter(console_format)
    file_formatter = logging.Formatter(file_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)

    # File handler with rotation (10MB max, keep 5 backups)
    file_handler = RotatingFileHandler(
        logs_dir / "bot.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("prawcore").setLevel(logging.WARNING)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    logger = logging.getLogger(__name__)

    signal_name = signal.Signals(signum).name
    logger.info(f"Received {signal_name}, initiating graceful shutdown...")

    _shutdown_requested = True

    if _bot:
        try:
            _bot.stop_polling()
        except Exception as e:
            logger.warning(f"Error stopping bot polling: {e}")

    if _scheduler:
        try:
            _scheduler.shutdown(wait=False)
        except Exception as e:
            logger.warning(f"Error stopping scheduler: {e}")


def run_bot_with_retry(bot: TeleBot, max_retries: int = 5, base_delay: int = 5) -> None:
    """
    Run the bot with exponential backoff retry logic.

    Args:
        bot: TeleBot instance
        max_retries: Maximum number of consecutive retry attempts
        base_delay: Base delay in seconds between retries
    """
    logger = logging.getLogger(__name__)
    retry_count = 0

    while not _shutdown_requested:
        try:
            logger.info("Starting bot polling...")
            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=30,
                allowed_updates=["message"],
            )

            # If we get here normally, reset retry count
            retry_count = 0

        except ApiTelegramException as e:
            logger.error(f"Telegram API error: {e}")

            if e.error_code == 401:
                logger.critical("Invalid bot token. Please check TELEGRAM_BOT_TOKEN.")
                sys.exit(1)

            retry_count += 1

        except KeyboardInterrupt:
            logger.info("Bot stopped by keyboard interrupt")
            break

        except Exception as e:
            logger.error(f"Unexpected error in bot polling: {e}", exc_info=True)
            retry_count += 1

        # Handle retries
        if _shutdown_requested:
            break

        if retry_count > 0:
            if retry_count > max_retries:
                logger.critical(f"Max retries ({max_retries}) exceeded. Exiting.")
                sys.exit(1)

            # Exponential backoff: 5, 10, 20, 40, 80 seconds
            delay = base_delay * (2 ** (retry_count - 1))
            logger.warning(f"Retry {retry_count}/{max_retries} in {delay} seconds...")
            time.sleep(delay)


def main() -> None:
    """Main entry point for the bot."""
    global _bot, _scheduler

    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("Crypto Sentiment Monitor Bot Starting")
    logger.info("=" * 50)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Validate configuration
    missing = Config.validate()
    if missing:
        logger.error(f"Missing required configuration: {', '.join(missing)}")
        logger.error("Please copy .env.example to .env and fill in the values.")
        sys.exit(1)

    # Initialize database
    try:
        init_db()
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}")
        sys.exit(1)

    # Create bot instance
    token = Config.TELEGRAM_BOT_TOKEN
    if not token:
        logger.critical("TELEGRAM_BOT_TOKEN is not set")
        sys.exit(1)

    _bot = TeleBot(token)
    logger.info("Bot instance created")

    # Set start time for uptime tracking
    start_time = datetime.utcnow()
    set_start_time(start_time)

    # Register handlers
    setup_handlers(_bot)

    # Start scheduler for periodic sentiment checks
    _scheduler = setup_scheduler(_bot)

    # Run with retry logic
    try:
        run_bot_with_retry(_bot)
    finally:
        logger.info("Shutting down...")

        if _scheduler:
            try:
                _scheduler.shutdown(wait=True)
                logger.info("Scheduler stopped")
            except Exception as e:
                logger.warning(f"Error during scheduler shutdown: {e}")

        logger.info("Bot stopped")


if __name__ == "__main__":
    main()
