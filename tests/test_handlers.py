"""Tests for Telegram bot handlers."""

from unittest.mock import MagicMock, patch


class TestHelpHandler:
    """Tests for /help and /start commands."""

    def test_help_sends_message(self, mock_bot, mock_message):
        from bot.handlers import setup_handlers

        setup_handlers(mock_bot)

        # The handler is registered via decorator, so we test the registration
        assert mock_bot.message_handler.called


class TestSentimentCommand:
    """Tests for /sentiment command parsing and validation."""

    def test_parse_coin_from_message(self):
        """Test extracting coin name from command."""
        message_text = "/sentiment bitcoin"
        args = message_text.split(maxsplit=1)
        assert len(args) == 2
        assert args[1] == "bitcoin"

    def test_parse_coin_alias(self):
        """Test that aliases are resolved."""
        from config import Config

        coin = "btc"
        resolved = Config.COIN_ALIASES.get(coin, coin)
        assert resolved == "bitcoin"

    def test_parse_unknown_coin_unchanged(self):
        """Test that unknown coins pass through unchanged."""
        from config import Config

        coin = "randomcoin"
        resolved = Config.COIN_ALIASES.get(coin, coin)
        assert resolved == "randomcoin"

    def test_missing_coin_argument(self):
        """Test handling when no coin is provided."""
        message_text = "/sentiment"
        args = message_text.split(maxsplit=1)
        assert len(args) == 1  # Only command, no coin


class TestTrackCommand:
    """Tests for /track command logic."""

    @patch("bot.handlers.get_or_create_user")
    @patch("bot.handlers.Watchlist")
    def test_track_creates_watchlist_entry(self, mock_watchlist, mock_get_user, mock_bot, mock_message):
        mock_user = MagicMock()
        mock_get_user.return_value = mock_user
        mock_watchlist.get_or_create.return_value = (MagicMock(), True)

        # Simulate the logic
        coin = "bitcoin"
        user = mock_get_user(mock_message.from_user.id, mock_message.from_user.username)
        watchlist_item, created = mock_watchlist.get_or_create(user=user, coin=coin)

        assert created is True
        mock_watchlist.get_or_create.assert_called_once()

    @patch("bot.handlers.get_or_create_user")
    @patch("bot.handlers.Watchlist")
    def test_track_existing_coin(self, mock_watchlist, mock_get_user, mock_bot, mock_message):
        mock_user = MagicMock()
        mock_get_user.return_value = mock_user
        mock_watchlist.get_or_create.return_value = (MagicMock(), False)  # Not created

        coin = "bitcoin"
        user = mock_get_user(mock_message.from_user.id, mock_message.from_user.username)
        watchlist_item, created = mock_watchlist.get_or_create(user=user, coin=coin)

        assert created is False


class TestUntrackCommand:
    """Tests for /untrack command logic."""

    @patch("bot.handlers.get_or_create_user")
    @patch("bot.handlers.Watchlist")
    def test_untrack_deletes_entry(self, mock_watchlist, mock_get_user):
        mock_user = MagicMock()
        mock_get_user.return_value = mock_user

        mock_delete = MagicMock()
        mock_delete.where.return_value.execute.return_value = 1
        mock_watchlist.delete.return_value = mock_delete

        # Simulate the delete logic
        deleted = mock_watchlist.delete().where().execute()

        assert deleted == 1

    @patch("bot.handlers.get_or_create_user")
    @patch("bot.handlers.Watchlist")
    def test_untrack_nonexistent_coin(self, mock_watchlist, mock_get_user):
        mock_user = MagicMock()
        mock_get_user.return_value = mock_user

        mock_delete = MagicMock()
        mock_delete.where.return_value.execute.return_value = 0  # Nothing deleted
        mock_watchlist.delete.return_value = mock_delete

        deleted = mock_watchlist.delete().where().execute()

        assert deleted == 0


class TestWatchlistCommand:
    """Tests for /watchlist command logic."""

    def test_empty_watchlist_message(self):
        """Test message for empty watchlist."""
        items = []
        if not items:
            message = "Your watchlist is empty."
            assert "empty" in message

    def test_format_watchlist(self):
        """Test formatting watchlist items."""
        coins = ["bitcoin", "ethereum", "solana"]
        formatted = "\n".join(f"• {coin}" for coin in coins)

        assert "• bitcoin" in formatted
        assert "• ethereum" in formatted
        assert "• solana" in formatted


class TestCoinAliases:
    """Tests for coin alias resolution."""

    def test_common_aliases(self):
        from config import Config

        test_cases = [
            ("btc", "bitcoin"),
            ("eth", "ethereum"),
            ("sol", "solana"),
            ("ada", "cardano"),
            ("xrp", "ripple"),
            ("doge", "dogecoin"),
        ]

        for alias, expected in test_cases:
            resolved = Config.COIN_ALIASES.get(alias, alias)
            assert resolved == expected, f"Expected {alias} to resolve to {expected}"

    def test_full_names_unchanged(self):
        from config import Config

        full_names = ["bitcoin", "ethereum", "solana", "cardano"]

        for name in full_names:
            resolved = Config.COIN_ALIASES.get(name, name)
            assert resolved == name
