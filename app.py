import streamlit as st
import requests
from bs4 import BeautifulSoup
import json

from web_fetcher import (
    get_top_news,
    get_stock_blog_rss,
    get_reddit_posts
)



# Initialize memory
if "memory" not in st.session_state:
    st.session_state.memory = []
if "mode" not in st.session_state:
    st.session_state.mode = "URL Summarizer"
if "auto_url" not in st.session_state:
    st.session_state.auto_url = ""

query_params = st.experimental_get_query_params()
if "auto_url" in query_params:
    st.session_state.auto_url = query_params["auto_url"][0]

# API Keys
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
news_key = st.secrets["newsapi"]
reddit_id = st.secrets["reddit"]["client_id"]
reddit_secret = st.secrets["reddit"]["client_secret"]
reddit_agent = st.secrets["reddit"]["user_agent"]



# LLaMA Request Setup
headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}
API_URL = "https://api.together.xyz/v1/chat/completions"

def extract_text_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return f"Failed to fetch article: {response.status_code}"
        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all("p")
        return "\n".join([p.get_text() for p in paragraphs])
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

**Question**: {query if query else 'No question was asked'}

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

# --- FRONTEND LOGIC ---
st.title("🧠 OpenLens – Unified AI Web Analyzer")

mode = st.radio("Choose Mode:", ["URL Summarizer", "Web Data Explorer"])
st.session_state.mode = mode

# Handle Auto-Summarize from Web Data
if st.session_state.auto_url:
    mode = "URL Summarizer"
    st.session_state.mode = "URL Summarizer"
    auto_url = st.session_state.auto_url
    st.session_state.auto_url = ""
    st.experimental_rerun()

# ------------------------ URL SUMMARIZER ------------------------
if st.session_state.mode == "URL Summarizer":
    url = st.text_input("Enter article URL", value=st.session_state.get("auto_url", ""), key="url_input")
    query = st.text_input("Ask a question about the article (optional):", key="url_question")

    if st.button("Analyze", key="analyze_button"):
        with st.spinner("Extracting article content..."):
            article_text = extract_text_from_url(url)
            st.subheader("📰 Article Preview")
            st.write(article_text[:1500] + "...")

            with st.spinner("Querying LLaMA 3.1..."):
                result = query_llama_together(article_text, query)
                st.subheader("🧾 LLaMA 3.1 Output")

                # Store in session
                st.session_state.memory.append({
                    "url": url,
                    "question": query,
                    "summary_answer": result
                })

                # Display smart split
                if "Answer:" in result:
                    summary, answer = result.split("Answer:", 1)
                    st.markdown("### 📌 Summary")
                    st.markdown(summary.strip())

                    if query:
                        st.markdown("### ❓ Question Asked")
                        st.markdown(f"`{query}`")
                        st.markdown("### ✅ Answer")
                        st.markdown(answer.strip())
                    else:
                        st.markdown("No specific question was asked.")
                else:
                    st.markdown("### 📌 Summary & Answer")
                    st.markdown(result.strip())

# ------------------------ WEB DATA FETCH ------------------------
elif st.session_state.mode == "Web Data Explorer":
    if st.button("🔄 Fetch Real-Time Data"):
        news = get_top_news(news_key)
        stocks = get_stock_blog_rss()
        reddit = get_reddit_posts(reddit_id, reddit_secret, reddit_agent)

        st.markdown("### 🗞️ Top News")
        for i, article in enumerate(news[:10]):
            st.markdown(f"{i+1}. [{article['title']}](/?auto_url={article['url']})")

        st.markdown("### 📈 Stock Blogs")
        for i, post in enumerate(stocks[:10]):
            st.markdown(f"{i+1}. [{post['title']}](/?auto_url={post['link']})")

        st.markdown("### 👽 Reddit Posts")
        for i, post in enumerate(reddit[:10]):
            st.markdown(f"{i+1}. [{post['title']}](/?auto_url={post['url']})")

# ------------------------ SESSION MEMORY ------------------------
with st.sidebar.expander("🧠 Session Memory", expanded=False):
    if st.session_state.memory:
        for i, entry in enumerate(st.session_state.memory[::-1]):
            st.markdown(f"**{i+1}.** [{entry['url']}]({entry['url']})")
            if entry['question']:
                st.markdown(f"- Q: _{entry['question']}_")
            st.markdown(f"- A: {entry['summary_answer'][:100]}...\n")
            st.markdown("---")
    else:
        st.write("No memory yet.")
