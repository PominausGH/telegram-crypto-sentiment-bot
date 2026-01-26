import logging

import praw
from praw.models import Submission

from config import Config

logger = logging.getLogger(__name__)

_reddit_client: praw.Reddit | None = None


def get_reddit_client() -> praw.Reddit:
    """Get or create Reddit API client (singleton)."""
    global _reddit_client

    if _reddit_client is None:
        _reddit_client = praw.Reddit(
            client_id=Config.REDDIT_CLIENT_ID,
            client_secret=Config.REDDIT_CLIENT_SECRET,
            user_agent=Config.REDDIT_USER_AGENT,
        )
        logger.info("Reddit client initialized")

    return _reddit_client


def extract_post_text(submission: Submission) -> str:
    """Extract relevant text from a Reddit submission."""
    parts = [submission.title]
    if submission.selftext:
        parts.append(submission.selftext)
    return " ".join(parts)


def fetch_reddit_posts(
    coin: str,
    subreddits: list[str] | None = None,
    limit: int = 50,
    time_filter: str = "day",
) -> list[dict]:
    """
    Fetch Reddit posts mentioning a cryptocurrency.

    Args:
        coin: Name of the cryptocurrency to search for
        subreddits: List of subreddits to search (defaults to Config.CRYPTO_SUBREDDITS)
        limit: Maximum posts per subreddit
        time_filter: Time range (hour, day, week, month, year, all)

    Returns:
        List of dicts with post data: {text, score, num_comments, created_utc, url}
    """
    if subreddits is None:
        subreddits = Config.CRYPTO_SUBREDDITS

    reddit = get_reddit_client()
    posts = []

    for subreddit_name in subreddits:
        try:
            subreddit = reddit.subreddit(subreddit_name)

            # Search for posts mentioning the coin
            for submission in subreddit.search(
                coin,
                limit=limit,
                time_filter=time_filter,
                sort="relevance",
            ):
                post_data = {
                    "text": extract_post_text(submission),
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "created_utc": submission.created_utc,
                    "url": f"https://reddit.com{submission.permalink}",
                    "subreddit": subreddit_name,
                }
                posts.append(post_data)

        except Exception as e:
            logger.warning(f"Error fetching from r/{subreddit_name}: {e}")
            continue

    logger.info(f"Fetched {len(posts)} posts for '{coin}'")
    return posts


def fetch_subreddit_hot(subreddit_name: str, limit: int = 25) -> list[dict]:
    """Fetch hot posts from a specific subreddit (useful for general crypto sentiment)."""
    reddit = get_reddit_client()
    posts = []

    try:
        subreddit = reddit.subreddit(subreddit_name)
        for submission in subreddit.hot(limit=limit):
            if submission.stickied:
                continue  # Skip pinned posts
            posts.append({
                "text": extract_post_text(submission),
                "score": submission.score,
                "num_comments": submission.num_comments,
                "created_utc": submission.created_utc,
                "url": f"https://reddit.com{submission.permalink}",
                "subreddit": subreddit_name,
            })
    except Exception as e:
        logger.error(f"Error fetching hot posts from r/{subreddit_name}: {e}")

    return posts
