"""Tests for Reddit data fetching module."""

from unittest.mock import MagicMock, patch
import pytest

from data.reddit import (
    extract_post_text,
    fetch_reddit_posts,
    fetch_subreddit_hot,
    get_reddit_client,
)


class TestExtractPostText:
    """Tests for extracting text from Reddit submissions."""

    def test_extracts_title(self):
        submission = MagicMock()
        submission.title = "Bitcoin hits new ATH"
        submission.selftext = ""

        result = extract_post_text(submission)
        assert "Bitcoin hits new ATH" in result

    def test_extracts_selftext(self):
        submission = MagicMock()
        submission.title = "Title"
        submission.selftext = "This is the body text"

        result = extract_post_text(submission)
        assert "This is the body text" in result

    def test_combines_title_and_selftext(self):
        submission = MagicMock()
        submission.title = "Great news"
        submission.selftext = "Bitcoin is mooning"

        result = extract_post_text(submission)
        assert "Great news" in result
        assert "Bitcoin is mooning" in result

    def test_handles_empty_selftext(self):
        submission = MagicMock()
        submission.title = "Just a title"
        submission.selftext = ""

        result = extract_post_text(submission)
        assert result == "Just a title"


class TestFetchRedditPosts:
    """Tests for fetching posts from Reddit."""

    @patch("data.reddit.get_reddit_client")
    def test_returns_list(self, mock_get_client):
        # Setup mock
        mock_reddit = MagicMock()
        mock_get_client.return_value = mock_reddit

        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.search.return_value = []

        result = fetch_reddit_posts("bitcoin", subreddits=["cryptocurrency"])
        assert isinstance(result, list)

    @patch("data.reddit.get_reddit_client")
    def test_extracts_post_data(self, mock_get_client):
        # Setup mock
        mock_reddit = MagicMock()
        mock_get_client.return_value = mock_reddit

        mock_submission = MagicMock()
        mock_submission.title = "Test post"
        mock_submission.selftext = "Test body"
        mock_submission.score = 100
        mock_submission.num_comments = 50
        mock_submission.created_utc = 1234567890
        mock_submission.permalink = "/r/test/comments/abc123"

        mock_subreddit = MagicMock()
        mock_subreddit.search.return_value = [mock_submission]
        mock_reddit.subreddit.return_value = mock_subreddit

        result = fetch_reddit_posts("bitcoin", subreddits=["cryptocurrency"], limit=10)

        assert len(result) == 1
        assert result[0]["score"] == 100
        assert result[0]["num_comments"] == 50
        assert "Test post" in result[0]["text"]
        assert "cryptocurrency" == result[0]["subreddit"]

    @patch("data.reddit.get_reddit_client")
    def test_searches_multiple_subreddits(self, mock_get_client):
        mock_reddit = MagicMock()
        mock_get_client.return_value = mock_reddit

        mock_submission = MagicMock()
        mock_submission.title = "Post"
        mock_submission.selftext = ""
        mock_submission.score = 10
        mock_submission.num_comments = 5
        mock_submission.created_utc = 1234567890
        mock_submission.permalink = "/r/test/comments/abc"

        mock_subreddit = MagicMock()
        mock_subreddit.search.return_value = [mock_submission]
        mock_reddit.subreddit.return_value = mock_subreddit

        subreddits = ["cryptocurrency", "bitcoin", "ethereum"]
        fetch_reddit_posts("eth", subreddits=subreddits)

        # Should call subreddit for each subreddit
        assert mock_reddit.subreddit.call_count == len(subreddits)

    @patch("data.reddit.get_reddit_client")
    def test_handles_api_error_gracefully(self, mock_get_client):
        mock_reddit = MagicMock()
        mock_get_client.return_value = mock_reddit

        mock_subreddit = MagicMock()
        mock_subreddit.search.side_effect = Exception("API Error")
        mock_reddit.subreddit.return_value = mock_subreddit

        # Should not raise, should return empty list
        result = fetch_reddit_posts("bitcoin", subreddits=["cryptocurrency"])
        assert result == []

    @patch("data.reddit.get_reddit_client")
    def test_uses_default_subreddits(self, mock_get_client):
        mock_reddit = MagicMock()
        mock_get_client.return_value = mock_reddit

        mock_subreddit = MagicMock()
        mock_subreddit.search.return_value = []
        mock_reddit.subreddit.return_value = mock_subreddit

        fetch_reddit_posts("bitcoin")

        # Should call subreddit multiple times (default list)
        assert mock_reddit.subreddit.call_count > 1


class TestFetchSubredditHot:
    """Tests for fetching hot posts from a subreddit."""

    @patch("data.reddit.get_reddit_client")
    def test_returns_list(self, mock_get_client):
        mock_reddit = MagicMock()
        mock_get_client.return_value = mock_reddit

        mock_subreddit = MagicMock()
        mock_subreddit.hot.return_value = []
        mock_reddit.subreddit.return_value = mock_subreddit

        result = fetch_subreddit_hot("cryptocurrency")
        assert isinstance(result, list)

    @patch("data.reddit.get_reddit_client")
    def test_skips_stickied_posts(self, mock_get_client):
        mock_reddit = MagicMock()
        mock_get_client.return_value = mock_reddit

        stickied_post = MagicMock()
        stickied_post.stickied = True

        regular_post = MagicMock()
        regular_post.stickied = False
        regular_post.title = "Regular post"
        regular_post.selftext = ""
        regular_post.score = 50
        regular_post.num_comments = 10
        regular_post.created_utc = 1234567890
        regular_post.permalink = "/r/test/comments/abc"

        mock_subreddit = MagicMock()
        mock_subreddit.hot.return_value = [stickied_post, regular_post]
        mock_reddit.subreddit.return_value = mock_subreddit

        result = fetch_subreddit_hot("cryptocurrency")

        assert len(result) == 1
        assert "Regular post" in result[0]["text"]

    @patch("data.reddit.get_reddit_client")
    def test_handles_error_gracefully(self, mock_get_client):
        mock_reddit = MagicMock()
        mock_get_client.return_value = mock_reddit

        mock_subreddit = MagicMock()
        mock_subreddit.hot.side_effect = Exception("API Error")
        mock_reddit.subreddit.return_value = mock_subreddit

        result = fetch_subreddit_hot("cryptocurrency")
        assert result == []
