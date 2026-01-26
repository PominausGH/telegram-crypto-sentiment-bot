"""Tests for the scheduler module."""

from unittest.mock import MagicMock, patch


class TestSetupScheduler:
    """Tests for scheduler setup."""

    @patch("bot.scheduler.BackgroundScheduler")
    def test_creates_scheduler(self, mock_scheduler_class):
        from bot.scheduler import setup_scheduler

        mock_bot = MagicMock()
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler

        result = setup_scheduler(mock_bot)

        mock_scheduler_class.assert_called_once()
        mock_scheduler.start.assert_called_once()
        assert result == mock_scheduler

    @patch("bot.scheduler.BackgroundScheduler")
    def test_adds_sentiment_check_job(self, mock_scheduler_class):
        from bot.scheduler import setup_scheduler
        from config import Config

        mock_bot = MagicMock()
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler

        setup_scheduler(mock_bot)

        # Verify job was added
        mock_scheduler.add_job.assert_called_once()
        call_kwargs = mock_scheduler.add_job.call_args[1]

        assert call_kwargs["id"] == "sentiment_check"
        assert call_kwargs["hours"] == Config.SENTIMENT_CHECK_INTERVAL_HOURS


class TestCheckWatchlistSentiment:
    """Tests for the sentiment checking job."""

    @patch("bot.scheduler.Watchlist")
    def test_skips_when_no_watched_coins(self, mock_watchlist):
        from bot.scheduler import check_watchlist_sentiment

        mock_bot = MagicMock()
        mock_watchlist.select.return_value.distinct.return_value = []

        # Should not raise and should return early
        check_watchlist_sentiment(mock_bot)

        mock_bot.send_message.assert_not_called()

    @patch("bot.scheduler.SentimentHistory")
    @patch("bot.scheduler.analyze_sentiment")
    @patch("bot.scheduler.fetch_reddit_posts")
    @patch("bot.scheduler.Watchlist")
    def test_fetches_posts_for_watched_coins(
        self, mock_watchlist, mock_fetch, mock_analyze, mock_history
    ):
        from bot.scheduler import check_watchlist_sentiment

        mock_bot = MagicMock()

        # Setup watched coin
        mock_coin = MagicMock()
        mock_coin.coin = "bitcoin"
        mock_watchlist.select.return_value.distinct.return_value = [mock_coin]

        # Setup fetch to return posts
        mock_fetch.return_value = [{"text": "test", "score": 10}]

        # Setup sentiment analysis
        mock_analyze.return_value = {
            "average": 0.5,
            "positive_pct": 60.0,
            "negative_pct": 20.0,
            "sample_size": 10,
        }

        # Setup history query (no previous)
        mock_history.select.return_value.where.return_value.order_by.return_value.first.return_value = (
            None
        )

        check_watchlist_sentiment(mock_bot)

        # Verify posts were fetched
        mock_fetch.assert_called_once()

        # Verify history was saved
        mock_history.create.assert_called_once()

    @patch("bot.scheduler.SentimentHistory")
    @patch("bot.scheduler.analyze_sentiment")
    @patch("bot.scheduler.fetch_reddit_posts")
    @patch("bot.scheduler.Watchlist")
    def test_sends_alert_on_significant_change(
        self, mock_watchlist, mock_fetch, mock_analyze, mock_history
    ):
        from bot.scheduler import check_watchlist_sentiment

        mock_bot = MagicMock()

        # Setup watched coin
        mock_coin = MagicMock()
        mock_coin.coin = "bitcoin"
        mock_watchlist.select.return_value.distinct.return_value = [mock_coin]

        # Setup fetch
        mock_fetch.return_value = [{"text": "test", "score": 10}]

        # Current sentiment is very different from previous
        mock_analyze.return_value = {
            "average": 0.5,  # Very bullish
            "positive_pct": 60.0,
            "negative_pct": 20.0,
            "sample_size": 10,
        }

        # Previous was bearish - big change!
        mock_previous = MagicMock()
        mock_previous.score = -0.2
        mock_history.select.return_value.where.return_value.order_by.return_value.first.return_value = (
            mock_previous
        )

        # Setup watchers
        mock_watcher = MagicMock()
        mock_watcher.user.telegram_id = 12345
        mock_watchlist.select.return_value.join.return_value.where.return_value = [mock_watcher]

        check_watchlist_sentiment(mock_bot)

        # Verify alert was sent
        mock_bot.send_message.assert_called()

    @patch("bot.scheduler.SentimentHistory")
    @patch("bot.scheduler.analyze_sentiment")
    @patch("bot.scheduler.fetch_reddit_posts")
    @patch("bot.scheduler.Watchlist")
    def test_no_alert_on_small_change(
        self, mock_watchlist, mock_fetch, mock_analyze, mock_history
    ):
        from bot.scheduler import check_watchlist_sentiment

        mock_bot = MagicMock()

        # Setup watched coin
        mock_coin = MagicMock()
        mock_coin.coin = "bitcoin"
        mock_watchlist.select.return_value.distinct.return_value = [mock_coin]

        # Setup fetch
        mock_fetch.return_value = [{"text": "test", "score": 10}]

        # Small change in sentiment
        mock_analyze.return_value = {
            "average": 0.12,
            "positive_pct": 55.0,
            "negative_pct": 25.0,
            "sample_size": 10,
        }

        mock_previous = MagicMock()
        mock_previous.score = 0.1  # Very small change
        mock_history.select.return_value.where.return_value.order_by.return_value.first.return_value = (
            mock_previous
        )

        check_watchlist_sentiment(mock_bot)

        # No alert should be sent
        mock_bot.send_message.assert_not_called()

    @patch("bot.scheduler.fetch_reddit_posts")
    @patch("bot.scheduler.Watchlist")
    def test_handles_fetch_error_gracefully(self, mock_watchlist, mock_fetch):
        from bot.scheduler import check_watchlist_sentiment

        mock_bot = MagicMock()

        # Setup watched coin
        mock_coin = MagicMock()
        mock_coin.coin = "bitcoin"
        mock_watchlist.select.return_value.distinct.return_value = [mock_coin]

        # Fetch raises an error
        mock_fetch.side_effect = Exception("API Error")

        # Should not raise
        check_watchlist_sentiment(mock_bot)

        # No messages sent
        mock_bot.send_message.assert_not_called()
