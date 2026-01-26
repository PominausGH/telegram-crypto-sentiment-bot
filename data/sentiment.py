import logging
import re

from textblob import TextBlob

logger = logging.getLogger(__name__)

# Crypto-specific sentiment modifiers
BULLISH_TERMS = {
    "hodl", "moon", "mooning", "bullish", "pump", "rocket", "lambo",
    "diamond hands", "buy the dip", "btd", "ath", "all time high",
    "breakout", "rally", "surge", "accumulate", "undervalued",
}

BEARISH_TERMS = {
    "bearish", "dump", "crash", "rug", "rugpull", "scam", "ponzi",
    "paper hands", "sell", "short", "correction", "bubble", "overvalued",
    "dead", "rekt", "liquidated", "capitulation",
}


def preprocess_text(text: str) -> str:
    """Clean and normalize text for sentiment analysis."""
    # Lowercase
    text = text.lower()
    # Remove Reddit formatting (before URLs to preserve link structure)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # Markdown links -> keep text
    text = re.sub(r"[*_~`]", "", text)  # Formatting chars
    # Remove URLs
    text = re.sub(r"http\S+|www\.\S+", "", text)
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def apply_crypto_modifiers(text: str, base_polarity: float) -> float:
    """Adjust sentiment based on crypto-specific terminology."""
    text_lower = text.lower()
    modifier = 0.0

    # Check for bullish terms
    bullish_count = sum(1 for term in BULLISH_TERMS if term in text_lower)
    # Check for bearish terms
    bearish_count = sum(1 for term in BEARISH_TERMS if term in text_lower)

    # Apply modifiers (each term shifts sentiment by 0.1)
    modifier += bullish_count * 0.1
    modifier -= bearish_count * 0.1

    # Clamp result to [-1, 1]
    adjusted = max(-1.0, min(1.0, base_polarity + modifier))
    return adjusted


def analyze_text(text: str) -> float:
    """Analyze sentiment of a single text, returning polarity [-1, 1]."""
    cleaned = preprocess_text(text)
    if not cleaned:
        return 0.0

    blob = TextBlob(cleaned)
    base_polarity = blob.sentiment.polarity

    # Apply crypto-specific adjustments
    adjusted_polarity = apply_crypto_modifiers(cleaned, base_polarity)

    return adjusted_polarity


def analyze_sentiment(posts: list[dict]) -> dict:
    """
    Analyze sentiment across multiple posts.

    Args:
        posts: List of post dicts with 'text' and optionally 'score' keys

    Returns:
        Dict with sentiment metrics:
        - average: Mean polarity [-1, 1]
        - weighted_average: Score-weighted mean polarity
        - positive_pct: Percentage of positive posts
        - negative_pct: Percentage of negative posts
        - neutral_pct: Percentage of neutral posts
        - sample_size: Number of posts analyzed
        - scores: List of individual scores (for debugging)
    """
    if not posts:
        return {
            "average": 0.0,
            "weighted_average": 0.0,
            "positive_pct": 0.0,
            "negative_pct": 0.0,
            "neutral_pct": 0.0,
            "sample_size": 0,
            "scores": [],
        }

    scores = []
    weighted_scores = []
    total_weight = 0

    for post in posts:
        text = post.get("text", "")
        weight = max(1, post.get("score", 1))  # Use Reddit score as weight

        polarity = analyze_text(text)
        scores.append(polarity)
        weighted_scores.append(polarity * weight)
        total_weight += weight

    # Calculate metrics
    average = sum(scores) / len(scores)
    weighted_average = sum(weighted_scores) / total_weight if total_weight > 0 else 0

    # Threshold for positive/negative classification
    threshold = 0.05
    positive_count = sum(1 for s in scores if s > threshold)
    negative_count = sum(1 for s in scores if s < -threshold)
    neutral_count = len(scores) - positive_count - negative_count

    return {
        "average": round(average, 3),
        "weighted_average": round(weighted_average, 3),
        "positive_pct": round(positive_count / len(scores) * 100, 1),
        "negative_pct": round(negative_count / len(scores) * 100, 1),
        "neutral_pct": round(neutral_count / len(scores) * 100, 1),
        "sample_size": len(scores),
        "scores": scores,
    }


def get_sentiment_emoji(score: float) -> str:
    """Get emoji representation of sentiment score."""
    if score >= 0.3:
        return "🟢"  # Very positive
    elif score >= 0.1:
        return "🟡"  # Slightly positive
    elif score >= -0.1:
        return "⚪"  # Neutral
    elif score >= -0.3:
        return "🟠"  # Slightly negative
    else:
        return "🔴"  # Very negative


def get_sentiment_label(score: float) -> str:
    """Get text label for sentiment score."""
    if score >= 0.3:
        return "Very Bullish"
    elif score >= 0.1:
        return "Bullish"
    elif score >= -0.1:
        return "Neutral"
    elif score >= -0.3:
        return "Bearish"
    else:
        return "Very Bearish"


def format_sentiment_report(coin: str, sentiment: dict) -> str:
    """Format sentiment data as a readable Telegram message."""
    emoji = get_sentiment_emoji(sentiment["average"])
    label = get_sentiment_label(sentiment["average"])

    report = f"""
{emoji} *Sentiment Report: {coin.upper()}*

*Overall:* {label} ({sentiment['average']:+.2f})
*Weighted Score:* {sentiment['weighted_average']:+.2f}

*Breakdown:*
• 🟢 Positive: {sentiment['positive_pct']}%
• ⚪ Neutral: {sentiment['neutral_pct']}%
• 🔴 Negative: {sentiment['negative_pct']}%

_Based on {sentiment['sample_size']} Reddit posts from the last 24h_
    """.strip()

    return report
