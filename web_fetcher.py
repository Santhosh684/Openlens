import requests
import feedparser

import praw
import streamlit as st
from newsapi import NewsApiClient
import tweepy


def get_top_news(api_key, query="technology", language="en"):
    try:
        newsapi = NewsApiClient(api_key=api_key)
        top_headlines = newsapi.get_top_headlines(q=query, language=language)
        # return [{"title": top_headline.title, "url": top_headline.url} for top_headline in top_headlines.articles]
        return [{"title": article["title"], "url": article["url"]} for article in top_headlines["articles"]]
    except Exception as e:
        return [f"Error fetching news: {e}"]


def get_stock_blog_rss(rss_url="https://finance.yahoo.com/news/rssindex"):
    try:
        feed = feedparser.parse(rss_url)
        return [{"title": entry.title, "link": entry.link} for entry in feed.entries]
    except Exception as e:
        return [{"title": f"Error fetching RSS: {e}", "link": "#"}]


# --- Twitter (via tweepy) ---
# def get_twitter_posts(query, count=5):
#     try:
#         api_key = st.secrets["twitter"]["api_key"]
#         api_secret = st.secrets["twitter"]["api_secret"]
#         access_token = st.secrets["twitter"]["access_token"]
#         access_token_secret = st.secrets["twitter"]["access_token_secret"]

#         auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
#         api = tweepy.API(auth)
#         tweets = api.search_tweets(q=query, count=count, lang="en", tweet_mode="extended")

#         return [tweet.full_text for tweet in tweets]
#     except Exception as e:
#         return [f"Error fetching tweets: {e}"]

# --- Reddit (via praw) ---

def get_reddit_posts(client_id, client_secret, user_agent, subreddit="technology", limit=5):
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        posts = reddit.subreddit(subreddit).hot(limit=limit)
        return [{"title": post.title, "url": post.url} for post in posts]
    except Exception as e:
        return [{"title": f"Error fetching Reddit posts: {e}", "url": "#"}]
