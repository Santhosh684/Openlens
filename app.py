import streamlit as st
import requests
from bs4 import BeautifulSoup
import json

from web_fetcher import (
    get_top_news,
    get_stock_blog_rss,
    get_reddit_posts
)

# session state initialization
if "memory" not in st.session_state:
    st.session_state.memory = []
if "mode" not in st.session_state:
    st.session_state.mode = "URL Summarizer"
if "auto_url" not in st.session_state:
    st.session_state.auto_url = ""
if "auto_url_triggered" not in st.session_state:
    st.session_state.auto_url_triggered = False

# query parameters handling
query_params = st.query_params
if "auto_url" in query_params and not st.session_state.auto_url_triggered:
    st.session_state.auto_url = query_params["auto_url"]
    st.session_state.auto_url_triggered = True
    st.session_state.mode = "URL Summarizer"
    st.rerun()

# API keys
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
news_key = st.secrets["newsapi"]
reddit_id = st.secrets["reddit"]["client_id"]
reddit_secret = st.secrets["reddit"]["client_secret"]
reddit_agent = st.secrets["reddit"]["user_agent"]

# LLaMA REQUEST 
headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}
API_URL = "https://api.together.xyz/v1/chat/completions"

def extract_text_from_url(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            return f"Failed to fetch article: {response.status_code}"

        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all(["p", "h1", "h2", "h3"])
        article_text = "\n".join(
            [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
        )

        return article_text if article_text else "No meaningful content found on the page."
    except Exception as e:
        return f"Error fetching content: {e}"

def query_llama_together(article_text, query):
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert research assistant. "
                "Summarize news articles clearly and answer user questions precisely using only the article content. Avoid speculation. "
                "Have a sarcastic tone when appropriate, but always be helpful. "
                "If the user asks for your opinion, make it funny and engaging."
            )
        },
        {
            "role": "user",
            "content": f"""Here's an article I want you to analyze:

{article_text}

Now, follow these steps:
1. Give a concise **summary** of the article.
2. If the following question is provided, answer it using only the article content:

**Question**: {query if query.strip() else 'No question was asked'}

Begin your response below:
"""
        }
    ]

    payload = {
        "model": "meta-llama/Llama-3-70b-chat-hf", 
        "messages": messages,
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 1024
    }

    response = requests.post(API_URL, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"API Error {response.status_code}: {response.text}"

# ----------------- FRONTEND LOGIC -----------------
st.title(" OpenLens – Unified AI Web Analyzer")

mode = st.radio("Choose Mode:", ["URL Summarizer", "Web Data Explorer"])
st.session_state.mode = mode

# URL SUMMARIZER
if st.session_state.mode == "URL Summarizer":
    url_default = st.session_state.get("auto_url", "")
    url = st.text_input("Enter article URL", value=url_default, key="url_input")
    query = st.text_input("Ask a question about the article (optional):", key="url_question")
    query = st.session_state.get("url_question", "").strip()

    auto_trigger = st.session_state.auto_url_triggered
    trigger_clicked = st.button("Analyze", key="analyze_button")

    if auto_trigger or trigger_clicked:
        st.session_state.auto_url = ""
        st.session_state.auto_url_triggered = False

        with st.spinner("Extracting article content..."):
            article_text = extract_text_from_url(url)
            st.subheader(" Article Preview")
            st.write(article_text[:500] + "...")

        if (
            not article_text
            or "Failed" in article_text
            or "Error" in article_text
            or "No meaningful content" in article_text
        ):
            st.error(" Could not extract meaningful article content. Try a different link.")
        else:
            with st.spinner("Querying LLaMA 3.1..."):
                result = query_llama_together(article_text, query)
                st.subheader("Here's what I found:")

                st.session_state.memory.append({
                    "url": url,
                    "question": query,
                    "summary_answer": result
                })

                if "Answer:" in result:
                    summary, answer = result.split("Answer:", 1)
                    st.markdown("###  Summary")
                    st.markdown(summary.strip())

                    if query:
                        st.markdown("###  Question Asked")
                        st.markdown(f"`{query}`")
                        st.markdown("###  Answer")
                        st.markdown(answer.strip())
                    else:
                        st.markdown("No specific question was asked.")
                else:
                    st.markdown("###  Summary & Answer")
                    st.markdown(result.strip())

#  WEB DATA EXPLORER 
elif st.session_state.mode == "Web Data Explorer":
    if st.button(" Fetch Real-Time Data"):
        news = get_top_news(news_key)
        stocks = get_stock_blog_rss()
        reddit = get_reddit_posts(reddit_id, reddit_secret, reddit_agent)

        st.markdown("###  Top News")
        for i, article in enumerate(news[:10]):
            if isinstance(article, dict) and "title" in article and "url" in article:
                st.markdown(f"{i+1}. [{article['title']}](/?auto_url={article['url']})")
            else:
                st.markdown(f"{i+1}.  {article}")

        st.markdown("###  Stock Blogs")
        for i, post in enumerate(stocks[:10]):
            if isinstance(post, dict):
                st.markdown(f"{i+1}. [{post['title']}](/?auto_url={post['link']})")
            else:
                st.markdown(f"{i+1}.  {post}")

        st.markdown("###  Reddit Posts")
        for i, post in enumerate(reddit[:10]):
            if isinstance(post, dict):
                st.markdown(f"{i+1}. [{post['title']}](/?auto_url={post['url']})")
            else:
                st.markdown(f"{i+1}. {post}")

#  SESSION MEMORY 
with st.sidebar.expander("Session Memory", expanded=False):
    if st.session_state.memory:
        selected = st.radio(
            "Select a memory to display:",
            [f"{i+1}. {item['url']}" for i, item in enumerate(st.session_state.memory[::-1])],
            index=0,
            key="memory_select"
        )
        idx = int(selected.split(". ")[0]) - 1
        mem_item = st.session_state.memory[::-1][idx]

        st.markdown(f"**Query:** {mem_item['question'] if mem_item['question'] else 'N/A'}")
        st.markdown(f"**Summary/Answer:**\n{mem_item['summary_answer']}")
    else:
        st.write("No memory yet.")
