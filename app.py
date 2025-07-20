import streamlit as st
import requests
from bs4 import BeautifulSoup
import json

from web_fetcher import (
    get_top_news,
    get_stock_blog_rss,
    get_reddit_posts
)

# Session Memory
if "memory" not in st.session_state:
    st.session_state.memory = []

# Secrets
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
news_key = st.secrets["newsapi"]
reddit_id = st.secrets["reddit"]["client_id"]
reddit_secret = st.secrets["reddit"]["client_secret"]
reddit_agent = st.secrets["reddit"]["user_agent"]

headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}
API_URL = "https://api.together.xyz/v1/chat/completions"

# Functions
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
                "Summarize news articles clearly and answer user questions precisely using only the article content. Avoid speculation. Have a sarcastic tone when appropriate, but always be helpful, and if the user asks for your opinion, do it in a funny and engaging way."
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


# Streamlit UI
st.set_page_config(page_title="OpenLens", layout="wide")
st.title("🔍 OpenLens – Unified AI Web Assistant")

option = st.radio("Choose an Option:", ["🔗 URL Summarizer", "🌐 Real-time Web Data"])

if option == "🔗 URL Summarizer":
    url = st.text_input("Enter article URL")
    query = st.text_input("Ask a question about the article (optional):")

    if st.button("Analyze Article"):
        with st.spinner("Extracting article content..."):
            article_text = extract_text_from_url(url)
            st.subheader("📝 Article Preview")
            st.write(article_text[:1500] + "...")

        with st.spinner("Querying LLaMA 3.1..."):
            result = query_llama_together(article_text, query)
            st.subheader("🤖 LLaMA 3.1 Output")

            st.session_state.memory.append({
                "url": url,
                "question": query,
                "summary_answer": result
            })

            if "Answer:" in result:
                summary, answer = result.split("Answer:", 1)
                st.markdown("**Summary:**")
                st.markdown(summary.strip())

                if query:
                    st.markdown(f"**Question Asked:** `{query}`")
                    st.markdown("**Answer:**")
                    st.markdown(answer.strip())
                else:
                    st.markdown("No specific question was asked.")
            else:
                st.markdown("**Summary & Answer**")
                st.markdown(result.strip())

elif option == "🌐 Real-time Web Data":
    if st.button("Fetch Web Data"):
        with st.spinner("Fetching..."):
            news = get_top_news(news_key)
            stocks = get_stock_blog_rss()
            reddit = get_reddit_posts(reddit_id, reddit_secret, reddit_agent)

        st.subheader("🗞️ Top News")
        st.write(news)

        st.subheader("📈 Stock Blogs")
        st.write(stocks)

        st.subheader("👽 Reddit Posts")
        st.write(reddit)

# Sidebar: Session Memory
with st.sidebar.expander("🧠 Session Memory", expanded=False):
    if st.session_state.memory:
        for i, entry in enumerate(reversed(st.session_state.memory)):
            st.markdown(f"**{i+1}.** [{entry['url']}]({entry['url']})")
            if entry['question']:
                st.markdown(f"- Q: _{entry['question']}_")
            st.markdown(f"- A: {entry['summary_answer'][:100]}...\n---")
    else:
        st.write("No history yet.")
