import logging

from apscheduler.schedulers.background import BackgroundScheduler
from telebot import TeleBot

from config import Config
from data.models import SentimentHistory, User, Watchlist
from data.reddit import fetch_reddit_posts
from data.sentiment import analyze_sentiment

logger = logging.getLogger(__name__)


def check_watchlist_sentiment(bot: TeleBot) -> None:
    """Check sentiment for all watched coins and send alerts if significant changes."""
    logger.info("Running scheduled sentiment check")

    # Get all unique coins being watched
    watched_coins = Watchlist.select(Watchlist.coin).distinct()
    coins = [w.coin for w in watched_coins]

    if not coins:
        logger.info("No coins in any watchlist, skipping check")
        return

    for coin in coins:
        try:
            posts = fetch_reddit_posts(coin, limit=Config.DEFAULT_POST_LIMIT)
            if not posts:
                continue

            sentiment = analyze_sentiment(posts)
            current_score = sentiment["average"]

            # Get previous sentiment for comparison
            previous = (
                SentimentHistory.select()
                .where(SentimentHistory.coin == coin)
                .order_by(SentimentHistory.timestamp.desc())
                .first()
            )

            # Save current sentiment
            SentimentHistory.create(
                coin=coin,
                score=current_score,
                positive_pct=sentiment["positive_pct"],
                negative_pct=sentiment["negative_pct"],
                sample_size=sentiment["sample_size"],
            )

            # Check for significant change
            if previous:
                change = abs(current_score - previous.score)
                if change >= Config.ALERT_THRESHOLD_CHANGE:
                    direction = "📈 increased" if current_score > previous.score else "📉 decreased"
                    alert_message = (
                        f"🚨 *Sentiment Alert: {coin.upper()}*\n\n"
                        f"Sentiment has {direction} significantly!\n"
                        f"Previous: {previous.score:.2f} → Current: {current_score:.2f}\n\n"
                        f"Use `/sentiment {coin}` for full analysis."
                    )

                    # Notify all users watching this coin
                    watchers = (
                        Watchlist.select(Watchlist, User)
                        .join(User)
                        .where(Watchlist.coin == coin)
                    )
                    for watch in watchers:
                        try:
                            bot.send_message(
                                watch.user.telegram_id,
                                alert_message,
                                parse_mode="Markdown",
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send alert to user {watch.user.telegram_id}: {e}")

        except Exception as e:
            logger.error(f"Error checking sentiment for {coin}: {e}")


def setup_scheduler(bot: TeleBot) -> BackgroundScheduler:
    """Set up and start the background scheduler."""
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        check_watchlist_sentiment,
        "interval",
        hours=Config.SENTIMENT_CHECK_INTERVAL_HOURS,
        args=[bot],
        id="sentiment_check",
        name="Check watchlist sentiment",
    )

    scheduler.start()
    logger.info(f"Scheduler started. Sentiment checks every {Config.SENTIMENT_CHECK_INTERVAL_HOURS} hours.")

    return scheduler
