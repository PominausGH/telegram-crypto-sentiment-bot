import logging
from telebot import TeleBot
from telebot.types import Message

from config import Config
from data.reddit import fetch_reddit_posts
from data.sentiment import analyze_sentiment, format_sentiment_report
from data.models import Watchlist, get_or_create_user

logger = logging.getLogger(__name__)


def setup_handlers(bot: TeleBot) -> None:
    """Register all bot command handlers."""

    @bot.message_handler(commands=["start", "help"])
    def handle_help(message: Message):
        help_text = """
🔍 *Crypto Sentiment Bot*

Monitor cryptocurrency sentiment from Reddit discussions.

*Commands:*
`/sentiment <coin>` - Get current sentiment analysis
`/track <coin>` - Add coin to your watchlist
`/untrack <coin>` - Remove coin from watchlist
`/watchlist` - View your tracked coins
`/help` - Show this message

*Examples:*
`/sentiment bitcoin`
`/sentiment eth`
`/track solana`

_Sentiment data sourced from Reddit cryptocurrency communities._
        """
        bot.reply_to(message, help_text, parse_mode="Markdown")

    @bot.message_handler(commands=["sentiment"])
    def handle_sentiment(message: Message):
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            bot.reply_to(message, "Usage: `/sentiment <coin>`\nExample: `/sentiment bitcoin`", parse_mode="Markdown")
            return

        coin = args[1].strip().lower()
        # Resolve aliases
        coin = Config.COIN_ALIASES.get(coin, coin)

        bot.reply_to(message, f"⏳ Analyzing sentiment for *{coin}*...", parse_mode="Markdown")

        try:
            posts = fetch_reddit_posts(coin, limit=Config.DEFAULT_POST_LIMIT)

            if not posts:
                bot.send_message(
                    message.chat.id,
                    f"❌ No recent posts found for *{coin}*. Try a different coin or check the spelling.",
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
                "❌ An error occurred while fetching sentiment data. Please try again later.",
            )

    @bot.message_handler(commands=["track"])
    def handle_track(message: Message):
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            bot.reply_to(message, "Usage: `/track <coin>`\nExample: `/track ethereum`", parse_mode="Markdown")
            return

        coin = args[1].strip().lower()
        coin = Config.COIN_ALIASES.get(coin, coin)

        user = get_or_create_user(message.from_user.id, message.from_user.username)
        watchlist_item, created = Watchlist.get_or_create(user=user, coin=coin)

        if created:
            bot.reply_to(
                message,
                f"✅ Added *{coin}* to your watchlist. You'll receive sentiment alerts.",
                parse_mode="Markdown",
            )
        else:
            bot.reply_to(message, f"ℹ️ *{coin}* is already on your watchlist.", parse_mode="Markdown")

    @bot.message_handler(commands=["untrack"])
    def handle_untrack(message: Message):
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            bot.reply_to(message, "Usage: `/untrack <coin>`\nExample: `/untrack ethereum`", parse_mode="Markdown")
            return

        coin = args[1].strip().lower()
        coin = Config.COIN_ALIASES.get(coin, coin)

        user = get_or_create_user(message.from_user.id, message.from_user.username)
        deleted = Watchlist.delete().where(Watchlist.user == user, Watchlist.coin == coin).execute()

        if deleted:
            bot.reply_to(message, f"✅ Removed *{coin}* from your watchlist.", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"ℹ️ *{coin}* was not on your watchlist.", parse_mode="Markdown")

    @bot.message_handler(commands=["watchlist"])
    def handle_watchlist(message: Message):
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
        watchlist_text = "📋 *Your Watchlist:*\n\n" + "\n".join(f"• {coin}" for coin in coins)
        watchlist_text += "\n\n_Use `/sentiment <coin>` to check any coin._"
        bot.reply_to(message, watchlist_text, parse_mode="Markdown")

    @bot.message_handler(func=lambda m: True)
    def handle_unknown(message: Message):
        bot.reply_to(
            message,
            "I don't understand that command. Use `/help` to see available commands.",
            parse_mode="Markdown",
        )

    logger.info("Bot handlers registered")
