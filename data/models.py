import os
import logging
from datetime import datetime
from peewee import (
    SqliteDatabase,
    Model,
    IntegerField,
    CharField,
    FloatField,
    DateTimeField,
    ForeignKeyField,
)

from config import Config

logger = logging.getLogger(__name__)

# Initialize database (deferred connection)
db = SqliteDatabase(None)


class BaseModel(Model):
    """Base model with database binding."""

    class Meta:
        database = db


class User(BaseModel):
    """Telegram user who interacts with the bot."""

    telegram_id = IntegerField(unique=True, index=True)
    username = CharField(null=True)
    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = "users"


class Watchlist(BaseModel):
    """Coins a user is tracking for sentiment alerts."""

    user = ForeignKeyField(User, backref="watchlist")
    coin = CharField(index=True)
    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = "watchlist"
        indexes = ((("user", "coin"), True),)  # Unique together


class SentimentHistory(BaseModel):
    """Historical sentiment data for tracked coins."""

    coin = CharField(index=True)
    score = FloatField()
    positive_pct = FloatField()
    negative_pct = FloatField()
    sample_size = IntegerField()
    timestamp = DateTimeField(default=datetime.utcnow, index=True)

    class Meta:
        table_name = "sentiment_history"


def init_db() -> None:
    """Initialize the database connection and create tables."""
    db_path = Config.DATABASE_PATH

    # Ensure directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # Connect to database
    db.init(db_path)
    db.connect()

    # Create tables if they don't exist
    db.create_tables([User, Watchlist, SentimentHistory], safe=True)

    logger.info(f"Database initialized at {db_path}")


def get_or_create_user(telegram_id: int, username: str = None) -> User:
    """Get existing user or create new one."""
    user, created = User.get_or_create(
        telegram_id=telegram_id,
        defaults={"username": username},
    )
    if not created and username and user.username != username:
        user.username = username
        user.save()
    return user
