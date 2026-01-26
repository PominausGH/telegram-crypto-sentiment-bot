"""Tests for configuration module."""

import os
import sys
from unittest.mock import patch


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_missing_all_required(self):
        """Test that validation catches all missing required config."""
        # Remove config module if already imported
        if "config" in sys.modules:
            del sys.modules["config"]

        # Patch environment before importing config
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("dotenv.load_dotenv", return_value=True),
        ):
            # Force reload to pick up patched environment
            import importlib

            import config

            importlib.reload(config)

            # Manually clear the class attributes since they were set at import time
            config.Config.TELEGRAM_BOT_TOKEN = None
            config.Config.REDDIT_CLIENT_ID = None
            config.Config.REDDIT_CLIENT_SECRET = None

            missing = config.Config.validate()

            assert "TELEGRAM_BOT_TOKEN" in missing
            assert "REDDIT_CLIENT_ID" in missing
            assert "REDDIT_CLIENT_SECRET" in missing

    def test_all_required_present(self):
        """Test validation passes when all required config present."""
        if "config" in sys.modules:
            del sys.modules["config"]

        env_vars = {
            "TELEGRAM_BOT_TOKEN": "test_token",
            "REDDIT_CLIENT_ID": "test_id",
            "REDDIT_CLIENT_SECRET": "test_secret",
        }

        with (
            patch.dict(os.environ, env_vars, clear=True),
            patch("dotenv.load_dotenv", return_value=True),
        ):
            import importlib

            import config

            importlib.reload(config)

            # Set the values manually
            config.Config.TELEGRAM_BOT_TOKEN = "test_token"
            config.Config.REDDIT_CLIENT_ID = "test_id"
            config.Config.REDDIT_CLIENT_SECRET = "test_secret"

            missing = config.Config.validate()

            assert len(missing) == 0

    def test_partial_config(self):
        """Test validation catches partial config."""
        if "config" in sys.modules:
            del sys.modules["config"]

        env_vars = {
            "TELEGRAM_BOT_TOKEN": "test_token",
        }

        with (
            patch.dict(os.environ, env_vars, clear=True),
            patch("dotenv.load_dotenv", return_value=True),
        ):
            import importlib

            import config

            importlib.reload(config)

            # Set only telegram token
            config.Config.TELEGRAM_BOT_TOKEN = "test_token"
            config.Config.REDDIT_CLIENT_ID = None
            config.Config.REDDIT_CLIENT_SECRET = None

            missing = config.Config.validate()

            assert "TELEGRAM_BOT_TOKEN" not in missing
            assert "REDDIT_CLIENT_ID" in missing
            assert "REDDIT_CLIENT_SECRET" in missing


class TestConfigDefaults:
    """Tests for configuration defaults."""

    def test_default_post_limit(self):
        from config import Config

        assert Config.DEFAULT_POST_LIMIT == 50

    def test_default_time_filter(self):
        from config import Config

        assert Config.DEFAULT_TIME_FILTER == "day"

    def test_crypto_subreddits_list(self):
        from config import Config

        assert isinstance(Config.CRYPTO_SUBREDDITS, list)
        assert len(Config.CRYPTO_SUBREDDITS) > 0
        assert "cryptocurrency" in Config.CRYPTO_SUBREDDITS

    def test_coin_aliases_dict(self):
        from config import Config

        assert isinstance(Config.COIN_ALIASES, dict)
        assert "btc" in Config.COIN_ALIASES
        assert "eth" in Config.COIN_ALIASES


class TestSchedulerConfig:
    """Tests for scheduler configuration."""

    def test_check_interval_reasonable(self):
        from config import Config

        # Should be between 1 and 24 hours
        assert 1 <= Config.SENTIMENT_CHECK_INTERVAL_HOURS <= 24

    def test_alert_threshold_reasonable(self):
        from config import Config

        # Should be between 0 and 1
        assert 0 < Config.ALERT_THRESHOLD_CHANGE < 1
