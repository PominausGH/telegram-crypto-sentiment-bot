"""Tests for bot utility functions."""

import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from bot.utils import (
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW,
    InvalidInput,
    _user_requests,
    check_rate_limit,
    format_uptime,
    get_rate_limit_reset,
    get_user_display_name,
    validate_coin_input,
)


class TestValidateCoinInput:
    """Tests for coin input validation."""

    def test_valid_coin_name(self):
        assert validate_coin_input("bitcoin") == "bitcoin"
        assert validate_coin_input("Bitcoin") == "bitcoin"
        assert validate_coin_input("BITCOIN") == "bitcoin"

    def test_strips_whitespace(self):
        assert validate_coin_input("  bitcoin  ") == "bitcoin"

    def test_normalizes_internal_whitespace(self):
        assert validate_coin_input("shiba  inu") == "shiba inu"

    def test_allows_alphanumeric(self):
        assert validate_coin_input("coin123") == "coin123"

    def test_empty_string_raises(self):
        with pytest.raises(InvalidInput):
            validate_coin_input("")

    def test_whitespace_only_raises(self):
        with pytest.raises(InvalidInput):
            validate_coin_input("   ")

    def test_too_long_raises(self):
        long_name = "a" * 51
        with pytest.raises(InvalidInput) as exc_info:
            validate_coin_input(long_name)
        assert "too long" in str(exc_info.value).lower()

    def test_special_characters_raise(self):
        with pytest.raises(InvalidInput):
            validate_coin_input("bitcoin!")

        with pytest.raises(InvalidInput):
            validate_coin_input("coin@123")

        with pytest.raises(InvalidInput):
            validate_coin_input("<script>")


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def setup_method(self):
        """Clear rate limit data before each test."""
        _user_requests.clear()

    def test_first_request_allowed(self):
        assert check_rate_limit(12345) is True

    def test_multiple_requests_within_limit(self):
        user_id = 12345
        for _ in range(RATE_LIMIT_REQUESTS - 1):
            assert check_rate_limit(user_id) is True

    def test_exceeds_rate_limit(self):
        user_id = 12345
        # Make max requests
        for _ in range(RATE_LIMIT_REQUESTS):
            check_rate_limit(user_id)

        # Next request should be denied
        assert check_rate_limit(user_id) is False

    def test_different_users_independent(self):
        user1, user2 = 12345, 67890

        # Fill up user1's limit
        for _ in range(RATE_LIMIT_REQUESTS):
            check_rate_limit(user1)

        # user2 should still be allowed
        assert check_rate_limit(user2) is True

    def test_rate_limit_resets_after_window(self):
        user_id = 12345

        # Use up all requests
        for _ in range(RATE_LIMIT_REQUESTS):
            check_rate_limit(user_id)

        # Manually expire the requests
        old_time = time.time() - RATE_LIMIT_WINDOW - 1
        _user_requests[user_id] = [old_time] * RATE_LIMIT_REQUESTS

        # Should be allowed again
        assert check_rate_limit(user_id) is True

    def test_get_rate_limit_reset_time(self):
        user_id = 12345

        # No requests yet
        assert get_rate_limit_reset(user_id) == 0

        # Make a request
        check_rate_limit(user_id)

        # Reset time should be approximately RATE_LIMIT_WINDOW seconds
        reset_time = get_rate_limit_reset(user_id)
        assert 0 < reset_time <= RATE_LIMIT_WINDOW


class TestFormatUptime:
    """Tests for uptime formatting."""

    def test_seconds_only(self):
        start = datetime.utcnow() - timedelta(seconds=30)
        result = format_uptime(start)
        assert "30s" in result

    def test_minutes(self):
        start = datetime.utcnow() - timedelta(minutes=5, seconds=30)
        result = format_uptime(start)
        assert "5m" in result

    def test_hours(self):
        start = datetime.utcnow() - timedelta(hours=2, minutes=30)
        result = format_uptime(start)
        assert "2h" in result
        assert "30m" in result

    def test_days(self):
        start = datetime.utcnow() - timedelta(days=3, hours=5)
        result = format_uptime(start)
        assert "3d" in result
        assert "5h" in result

    def test_zero_uptime(self):
        start = datetime.utcnow()
        result = format_uptime(start)
        assert "0s" in result


class TestGetUserDisplayName:
    """Tests for user display name formatting."""

    def test_username_preferred(self):
        message = MagicMock()
        message.from_user.username = "testuser"
        message.from_user.first_name = "Test"
        message.from_user.id = 12345

        assert get_user_display_name(message) == "@testuser"

    def test_first_name_fallback(self):
        message = MagicMock()
        message.from_user.username = None
        message.from_user.first_name = "Test"
        message.from_user.id = 12345

        assert get_user_display_name(message) == "Test"

    def test_user_id_fallback(self):
        message = MagicMock()
        message.from_user.username = None
        message.from_user.first_name = None
        message.from_user.id = 12345

        assert get_user_display_name(message) == "User 12345"
