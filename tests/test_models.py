"""Tests for database models."""

import pytest

from data.models import (
    SentimentHistory,
    User,
    Watchlist,
    db,
    get_or_create_user,
)


@pytest.fixture
def test_db(temp_db):
    """Initialize test database."""
    # Configure database to use temp file
    db.init(temp_db)
    db.connect(reuse_if_open=True)
    db.create_tables([User, Watchlist, SentimentHistory], safe=True)

    yield db

    # Cleanup
    db.close()


class TestUser:
    """Tests for User model."""

    def test_create_user(self, test_db):
        user = User.create(telegram_id=12345, username="testuser")
        assert user.telegram_id == 12345
        assert user.username == "testuser"
        assert user.created_at is not None

    def test_telegram_id_unique(self, test_db):
        from peewee import IntegrityError

        User.create(telegram_id=12345, username="user1")
        with pytest.raises(IntegrityError):
            User.create(telegram_id=12345, username="user2")

    def test_username_nullable(self, test_db):
        user = User.create(telegram_id=99999)
        assert user.username is None


class TestWatchlist:
    """Tests for Watchlist model."""

    def test_create_watchlist_item(self, test_db):
        user = User.create(telegram_id=12345)
        item = Watchlist.create(user=user, coin="bitcoin")

        assert item.user.telegram_id == 12345
        assert item.coin == "bitcoin"

    def test_user_can_watch_multiple_coins(self, test_db):
        user = User.create(telegram_id=12345)
        Watchlist.create(user=user, coin="bitcoin")
        Watchlist.create(user=user, coin="ethereum")
        Watchlist.create(user=user, coin="solana")

        items = Watchlist.select().where(Watchlist.user == user)
        assert len(list(items)) == 3

    def test_unique_user_coin_pair(self, test_db):
        from peewee import IntegrityError

        user = User.create(telegram_id=12345)
        Watchlist.create(user=user, coin="bitcoin")

        with pytest.raises(IntegrityError):
            Watchlist.create(user=user, coin="bitcoin")

    def test_different_users_same_coin(self, test_db):
        user1 = User.create(telegram_id=11111)
        user2 = User.create(telegram_id=22222)

        Watchlist.create(user=user1, coin="bitcoin")
        Watchlist.create(user=user2, coin="bitcoin")

        items = Watchlist.select().where(Watchlist.coin == "bitcoin")
        assert len(list(items)) == 2

    def test_delete_removes_watchlist(self, test_db):
        user = User.create(telegram_id=12345)
        Watchlist.create(user=user, coin="bitcoin")

        deleted = (
            Watchlist.delete()
            .where(Watchlist.user == user, Watchlist.coin == "bitcoin")
            .execute()
        )

        assert deleted == 1
        items = Watchlist.select().where(Watchlist.user == user)
        assert len(list(items)) == 0


class TestSentimentHistory:
    """Tests for SentimentHistory model."""

    def test_create_history_entry(self, test_db):
        entry = SentimentHistory.create(
            coin="bitcoin",
            score=0.5,
            positive_pct=60.0,
            negative_pct=20.0,
            sample_size=100,
        )

        assert entry.coin == "bitcoin"
        assert entry.score == 0.5
        assert entry.sample_size == 100
        assert entry.timestamp is not None

    def test_query_by_coin(self, test_db):
        SentimentHistory.create(coin="bitcoin", score=0.5, positive_pct=60, negative_pct=20, sample_size=50)
        SentimentHistory.create(coin="bitcoin", score=0.6, positive_pct=65, negative_pct=15, sample_size=60)
        SentimentHistory.create(coin="ethereum", score=0.3, positive_pct=50, negative_pct=30, sample_size=40)

        btc_entries = SentimentHistory.select().where(SentimentHistory.coin == "bitcoin")
        assert len(list(btc_entries)) == 2

    def test_order_by_timestamp(self, test_db):
        SentimentHistory.create(coin="bitcoin", score=0.1, positive_pct=50, negative_pct=30, sample_size=10)
        SentimentHistory.create(coin="bitcoin", score=0.2, positive_pct=55, negative_pct=25, sample_size=20)
        SentimentHistory.create(coin="bitcoin", score=0.3, positive_pct=60, negative_pct=20, sample_size=30)

        latest = (
            SentimentHistory.select()
            .where(SentimentHistory.coin == "bitcoin")
            .order_by(SentimentHistory.timestamp.desc())
            .first()
        )

        assert latest.score == 0.3  # Most recently created


class TestGetOrCreateUser:
    """Tests for get_or_create_user helper."""

    def test_creates_new_user(self, test_db):
        user = get_or_create_user(12345, "newuser")

        assert user.telegram_id == 12345
        assert user.username == "newuser"

    def test_returns_existing_user(self, test_db):
        User.create(telegram_id=12345, username="existing")

        get_or_create_user(12345, "existing")

        # Should return existing, not create new
        all_users = User.select().where(User.telegram_id == 12345)
        assert len(list(all_users)) == 1

    def test_updates_username_if_changed(self, test_db):
        User.create(telegram_id=12345, username="oldname")

        user = get_or_create_user(12345, "newname")

        assert user.username == "newname"

    def test_handles_none_username(self, test_db):
        user = get_or_create_user(12345, None)
        assert user.telegram_id == 12345
        assert user.username is None
