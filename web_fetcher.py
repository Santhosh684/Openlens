# web_fetcher.py

import requests
import feedparser
import snscrape.modules.twitter as sntwitter
import praw
from newsapi import NewsApiClient

# --- NewsAPI (Top Headlines) ---
def get_top_news(api_key, query="technology", language="en"):
    newsapi = NewsApiClient(api_key=api_key)
    top_headlines = newsapi.get_top_headlines(q=query, language=language)
    return [article['title'] for article in top_headlines['articles']]

# --- RSS Feed (e.g., Yahoo Finance) ---
def get_stock_blog_rss(rss_url="https://finance.yahoo.com/news/rssindex"):
    feed = feedparser.parse(rss_url)
    return [entry.title for entry in feed.entries]

# --- Twitter (via snscrape) ---
def get_twitter_posts(query="AI", limit=5):
    tweets = []
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
        if i >= limit:
            break
        tweets.append(tweet.content)
    return tweets

# --- Reddit (via praw) ---
def get_reddit_posts(client_id, client_secret, user_agent, subreddit="technology", limit=5):
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )
    posts = reddit.subreddit(subreddit).hot(limit=limit)
    return [post.title for post in posts]
