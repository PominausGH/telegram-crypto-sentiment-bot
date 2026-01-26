"""Telegram bot command handlers."""

import logging
from datetime import datetime

from telebot import TeleBot
from telebot.types import Message

from bot.utils import (
    InvalidInput,
    check_rate_limit,
    format_uptime,
    get_rate_limit_reset,
    validate_coin_input,
)
from config import Config
from data.models import SentimentHistory, User, Watchlist, get_or_create_user
from data.reddit import fetch_reddit_posts
from data.sentiment import analyze_sentiment, format_sentiment_report

logger = logging.getLogger(__name__)

# Track bot start time for status command
_bot_start_time: datetime | None = None


def set_start_time(start_time: datetime) -> None:
    """Set the bot start time for uptime tracking."""
    global _bot_start_time
    _bot_start_time = start_time


def setup_handlers(bot: TeleBot) -> None:
    """Register all bot command handlers."""

    @bot.message_handler(commands=["start", "help"])
    def handle_help(message: Message):
        help_text = """
*Crypto Sentiment Bot*

Monitor cryptocurrency sentiment from Reddit discussions.

*Commands:*
`/sentiment <coin>` - Get current sentiment analysis
`/track <coin>` - Add coin to your watchlist
`/untrack <coin>` - Remove coin from watchlist
`/watchlist` - View your tracked coins
`/status` - Check bot status
`/help` - Show this message

*Examples:*
`/sentiment bitcoin`
`/sentiment eth`
`/track solana`

_Sentiment data sourced from Reddit cryptocurrency communities._
        """
        bot.reply_to(message, help_text, parse_mode="Markdown")

    @bot.message_handler(commands=["status"])
    def handle_status(message: Message):
        """Handle /status command - show bot health and statistics."""
        try:
            # Get statistics
            total_users = User.select().count()
            total_watchlist = Watchlist.select().count()
            total_history = SentimentHistory.select().count()

            # Get unique coins being tracked
            unique_coins = (
                Watchlist.select(Watchlist.coin).distinct().count()
            )

            # Calculate uptime
            uptime_str = "Unknown"
            if _bot_start_time:
                uptime_str = format_uptime(_bot_start_time)

            status_text = f"""
*Bot Status*

*Health:* Online
*Uptime:* {uptime_str}

*Statistics:*
- Users: {total_users}
- Watchlist entries: {total_watchlist}
- Unique coins tracked: {unique_coins}
- Sentiment history records: {total_history}

*Configuration:*
- Check interval: {Config.SENTIMENT_CHECK_INTERVAL_HOURS}h
- Alert threshold: {int(Config.ALERT_THRESHOLD_CHANGE * 100)}%
- Rate limit: 10 req/min

_Bot is running normally._
            """
            bot.reply_to(message, status_text, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in status command: {e}")
            bot.reply_to(message, "Error retrieving bot status.")

    @bot.message_handler(commands=["sentiment"])
    def handle_sentiment(message: Message):
        user_id = message.from_user.id

        # Rate limit check
        if not check_rate_limit(user_id):
            reset_seconds = get_rate_limit_reset(user_id)
            bot.reply_to(
                message,
                f"Rate limit exceeded. Please wait {reset_seconds} seconds.",
            )
            return

        # Parse arguments
        if message.text is None:
            bot.reply_to(
                message,
                "Usage: `/sentiment <coin>`\nExample: `/sentiment bitcoin`",
                parse_mode="Markdown",
            )
            return

        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            bot.reply_to(
                message,
                "Usage: `/sentiment <coin>`\nExample: `/sentiment bitcoin`",
                parse_mode="Markdown",
            )
            return

        # Validate input
        try:
            coin = validate_coin_input(args[1])
        except InvalidInput as e:
            bot.reply_to(message, f"Invalid input: {e}")
            return

        # Resolve aliases
        coin = Config.COIN_ALIASES.get(coin, coin)

        bot.reply_to(message, f"Analyzing sentiment for *{coin}*...", parse_mode="Markdown")

        try:
            posts = fetch_reddit_posts(coin, limit=Config.DEFAULT_POST_LIMIT)

            if not posts:
                bot.send_message(
                    message.chat.id,
                    f"No recent posts found for *{coin}*. Try a different coin or check the spelling.",
                    parse_mode="Markdown",
                )
                return

            sentiment = analyze_sentiment(posts)
            report = format_sentiment_report(coin, sentiment)
            bot.send_message(message.chat.id, report, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error analyzing sentiment for {coin}: {e}")
            bot.send_message(
                message.chat.id,
                "An error occurred while fetching sentiment data. Please try again later.",
            )

    @bot.message_handler(commands=["track"])
    def handle_track(message: Message):
        user_id = message.from_user.id

        # Rate limit check
        if not check_rate_limit(user_id):
            reset_seconds = get_rate_limit_reset(user_id)
            bot.reply_to(
                message,
                f"Rate limit exceeded. Please wait {reset_seconds} seconds.",
            )
            return

        # Parse arguments
        if message.text is None:
            bot.reply_to(
                message,
                "Usage: `/track <coin>`\nExample: `/track ethereum`",
                parse_mode="Markdown",
            )
            return

        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            bot.reply_to(
                message,
                "Usage: `/track <coin>`\nExample: `/track ethereum`",
                parse_mode="Markdown",
            )
            return

        # Validate input
        try:
            coin = validate_coin_input(args[1])
        except InvalidInput as e:
            bot.reply_to(message, f"Invalid input: {e}")
            return

        coin = Config.COIN_ALIASES.get(coin, coin)

        user = get_or_create_user(message.from_user.id, message.from_user.username)
        watchlist_item, created = Watchlist.get_or_create(user=user, coin=coin)

        if created:
            bot.reply_to(
                message,
                f"Added *{coin}* to your watchlist. You'll receive sentiment alerts.",
                parse_mode="Markdown",
            )
        else:
            bot.reply_to(message, f"*{coin}* is already on your watchlist.", parse_mode="Markdown")

    @bot.message_handler(commands=["untrack"])
    def handle_untrack(message: Message):
        user_id = message.from_user.id

        # Rate limit check
        if not check_rate_limit(user_id):
            reset_seconds = get_rate_limit_reset(user_id)
            bot.reply_to(
                message,
                f"Rate limit exceeded. Please wait {reset_seconds} seconds.",
            )
            return

        # Parse arguments
        if message.text is None:
            bot.reply_to(
                message,
                "Usage: `/untrack <coin>`\nExample: `/untrack ethereum`",
                parse_mode="Markdown",
            )
            return

        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            bot.reply_to(
                message,
                "Usage: `/untrack <coin>`\nExample: `/untrack ethereum`",
                parse_mode="Markdown",
            )
            return

        # Validate input
        try:
            coin = validate_coin_input(args[1])
        except InvalidInput as e:
            bot.reply_to(message, f"Invalid input: {e}")
            return

        coin = Config.COIN_ALIASES.get(coin, coin)

        user = get_or_create_user(message.from_user.id, message.from_user.username)
        deleted = (
            Watchlist.delete().where(Watchlist.user == user, Watchlist.coin == coin).execute()
        )

        if deleted:
            bot.reply_to(message, f"Removed *{coin}* from your watchlist.", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"*{coin}* was not on your watchlist.", parse_mode="Markdown")

    @bot.message_handler(commands=["watchlist"])
    def handle_watchlist(message: Message):
        user_id = message.from_user.id

        # Rate limit check
        if not check_rate_limit(user_id):
            reset_seconds = get_rate_limit_reset(user_id)
            bot.reply_to(
                message,
                f"Rate limit exceeded. Please wait {reset_seconds} seconds.",
            )
            return

        user = get_or_create_user(message.from_user.id, message.from_user.username)
        items = Watchlist.select().where(Watchlist.user == user)

        if not items:
            bot.reply_to(
                message,
                "Your watchlist is empty.\nUse `/track <coin>` to add coins.",
                parse_mode="Markdown",
            )
            return

        coins = [item.coin for item in items]
        watchlist_text = "*Your Watchlist:*\n\n" + "\n".join(f"- {coin}" for coin in coins)
        watchlist_text += "\n\n_Use `/sentiment <coin>` to check any coin._"
        bot.reply_to(message, watchlist_text, parse_mode="Markdown")

    @bot.message_handler(func=lambda _: True)
    def handle_unknown(message: Message):
        bot.reply_to(
            message,
            "I don't understand that command. Use `/help` to see available commands.",
            parse_mode="Markdown",
        )

    logger.info("Bot handlers registered")
