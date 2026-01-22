"""Tests for sentiment analysis module."""

import pytest
from data.sentiment import (
    preprocess_text,
    analyze_text,
    analyze_sentiment,
    apply_crypto_modifiers,
    get_sentiment_emoji,
    get_sentiment_label,
    format_sentiment_report,
)


class TestPreprocessText:
    """Tests for text preprocessing."""

    def test_lowercases_text(self):
        assert preprocess_text("BITCOIN MOON") == "bitcoin moon"

    def test_removes_urls(self):
        text = "Check this out https://example.com and http://test.org"
        result = preprocess_text(text)
        assert "https://" not in result
        assert "http://" not in result

    def test_removes_markdown_links(self):
        text = "Check [this link](https://example.com) out"
        result = preprocess_text(text)
        # Keeps link text, removes URL and brackets
        assert "this link" in result
        assert "https://" not in result
        assert "[" not in result

    def test_removes_formatting_chars(self):
        text = "This is **bold** and *italic* and `code`"
        result = preprocess_text(text)
        assert "*" not in result
        assert "`" not in result

    def test_normalizes_whitespace(self):
        text = "too    many     spaces"
        assert preprocess_text(text) == "too many spaces"

    def test_handles_empty_string(self):
        assert preprocess_text("") == ""


class TestApplyCryptoModifiers:
    """Tests for crypto-specific sentiment adjustments."""

    def test_bullish_terms_increase_score(self):
        text = "hodl moon diamond hands"
        base_score = 0.0
        result = apply_crypto_modifiers(text, base_score)
        assert result > base_score

    def test_bearish_terms_decrease_score(self):
        text = "rugpull scam dump bearish"
        base_score = 0.0
        result = apply_crypto_modifiers(text, base_score)
        assert result < base_score

    def test_mixed_terms_balance(self):
        text = "moon but also rug"
        base_score = 0.0
        result = apply_crypto_modifiers(text, base_score)
        # Should be close to neutral with one bullish and one bearish
        assert -0.2 <= result <= 0.2

    def test_clamps_to_max(self):
        text = "moon hodl bullish pump rocket lambo diamond hands ath breakout rally"
        result = apply_crypto_modifiers(text, 0.5)
        assert result <= 1.0

    def test_clamps_to_min(self):
        text = "scam rugpull dump crash bearish dead rekt"
        result = apply_crypto_modifiers(text, -0.5)
        assert result >= -1.0


class TestAnalyzeText:
    """Tests for single text sentiment analysis."""

    def test_positive_text(self):
        score = analyze_text("This is amazing and wonderful!")
        assert score > 0

    def test_negative_text(self):
        score = analyze_text("This is terrible and awful!")
        assert score < 0

    def test_neutral_text(self):
        score = analyze_text("The price is 100 dollars")
        assert -0.3 <= score <= 0.3

    def test_empty_text(self):
        assert analyze_text("") == 0.0

    def test_crypto_bullish_boost(self):
        # "hodl" should boost sentiment
        without_crypto = analyze_text("I am holding my position")
        with_crypto = analyze_text("I am hodl my position")
        assert with_crypto > without_crypto

    def test_crypto_bearish_penalty(self):
        # "rugpull" should decrease sentiment
        without_crypto = analyze_text("The project ended")
        with_crypto = analyze_text("The project is a rugpull")
        assert with_crypto < without_crypto


class TestAnalyzeSentiment:
    """Tests for batch sentiment analysis."""

    def test_empty_posts_returns_zeros(self):
        result = analyze_sentiment([])
        assert result["average"] == 0.0
        assert result["sample_size"] == 0

    def test_returns_correct_structure(self, sample_posts):
        result = analyze_sentiment(sample_posts)
        assert "average" in result
        assert "weighted_average" in result
        assert "positive_pct" in result
        assert "negative_pct" in result
        assert "neutral_pct" in result
        assert "sample_size" in result
        assert "scores" in result

    def test_sample_size_matches_input(self, sample_posts):
        result = analyze_sentiment(sample_posts)
        assert result["sample_size"] == len(sample_posts)

    def test_percentages_sum_to_100(self, sample_posts):
        result = analyze_sentiment(sample_posts)
        total = result["positive_pct"] + result["negative_pct"] + result["neutral_pct"]
        assert abs(total - 100.0) < 0.1  # Allow small floating point error

    def test_bullish_posts_positive_average(self, bullish_posts):
        result = analyze_sentiment(bullish_posts)
        assert result["average"] > 0
        assert result["positive_pct"] > result["negative_pct"]

    def test_bearish_posts_negative_average(self, bearish_posts):
        result = analyze_sentiment(bearish_posts)
        assert result["average"] < 0
        assert result["negative_pct"] > result["positive_pct"]

    def test_weighted_average_considers_score(self):
        # High-score post should have more influence
        posts = [
            {"text": "This is amazing!", "score": 1000},
            {"text": "This is bad", "score": 1},
        ]
        result = analyze_sentiment(posts)
        # Weighted average should be closer to the high-score post's sentiment
        assert result["weighted_average"] > 0


class TestGetSentimentEmoji:
    """Tests for sentiment emoji mapping."""

    def test_very_positive(self):
        assert get_sentiment_emoji(0.5) == "🟢"

    def test_slightly_positive(self):
        assert get_sentiment_emoji(0.15) == "🟡"

    def test_neutral(self):
        assert get_sentiment_emoji(0.0) == "⚪"

    def test_slightly_negative(self):
        assert get_sentiment_emoji(-0.15) == "🟠"

    def test_very_negative(self):
        assert get_sentiment_emoji(-0.5) == "🔴"


class TestGetSentimentLabel:
    """Tests for sentiment label mapping."""

    def test_very_bullish(self):
        assert get_sentiment_label(0.5) == "Very Bullish"

    def test_bullish(self):
        assert get_sentiment_label(0.15) == "Bullish"

    def test_neutral(self):
        assert get_sentiment_label(0.0) == "Neutral"

    def test_bearish(self):
        assert get_sentiment_label(-0.15) == "Bearish"

    def test_very_bearish(self):
        assert get_sentiment_label(-0.5) == "Very Bearish"


class TestFormatSentimentReport:
    """Tests for report formatting."""

    def test_contains_coin_name(self):
        sentiment = {
            "average": 0.5,
            "weighted_average": 0.4,
            "positive_pct": 60.0,
            "negative_pct": 20.0,
            "neutral_pct": 20.0,
            "sample_size": 50,
        }
        report = format_sentiment_report("bitcoin", sentiment)
        assert "BITCOIN" in report

    def test_contains_sentiment_label(self):
        sentiment = {
            "average": 0.5,
            "weighted_average": 0.4,
            "positive_pct": 60.0,
            "negative_pct": 20.0,
            "neutral_pct": 20.0,
            "sample_size": 50,
        }
        report = format_sentiment_report("bitcoin", sentiment)
        assert "Very Bullish" in report

    def test_contains_percentages(self):
        sentiment = {
            "average": 0.0,
            "weighted_average": 0.0,
            "positive_pct": 33.3,
            "negative_pct": 33.3,
            "neutral_pct": 33.4,
            "sample_size": 30,
        }
        report = format_sentiment_report("eth", sentiment)
        assert "33.3%" in report

    def test_contains_sample_size(self):
        sentiment = {
            "average": 0.0,
            "weighted_average": 0.0,
            "positive_pct": 50.0,
            "negative_pct": 50.0,
            "neutral_pct": 0.0,
            "sample_size": 42,
        }
        report = format_sentiment_report("sol", sentiment)
        assert "42" in report
