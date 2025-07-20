import streamlit as st
import requests
from bs4 import BeautifulSoup
import json

if "memory" not in st.session_state:
    st.session_state.memory = []



TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]


headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

API_URL = "https://api.together.xyz/v1/chat/completions"


def extract_text_from_url(url):
    try:
        response = requests.get(url)
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
                "Summarize news articles clearly and answer user questions precisely using only the article content. Avoid speculation."
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
        return f" API Error {response.status_code}: {response.text}"

# Streamlit App
st.title("🔍 OpenLens – AI Web Article Analyzer (LLaMA 3.1)")

url = st.text_input(" Enter article URL:")
query = st.text_input("Ask a question about the article (optional):")

#  Try to split result into summary and answer using simple keyword logic
if st.button("Analyze"):
    with st.spinner("Extracting article content..."):
        article_text = extract_text_from_url(url)
        st.subheader(" Article Preview")
        st.write(article_text[:1500] + "...")

        with st.spinner("Querying LLaMA 3.1..."):
            result = query_llama_together(article_text, query)
            st.subheader(" LLaMA 3.1 Output")

            # Store result in memory
            st.session_state.memory.append({
                "url": url,
                "question": query,
                "summary_answer": result
            })

            # Display Result
            if "Answer:" in result:
                summary, answer = result.split("Answer:", 1)
                st.markdown(" Summary")
                st.markdown(summary.strip())

                if query:
                    st.markdown(" Question Asked")
                    st.markdown(f"`{query}`")
                    st.markdown("  Answer")
                    st.markdown(answer.strip())
                else:
                    st.markdown("No specific question was asked.")
            else:
                st.markdown("Summary & Answer")
                st.markdown(result.strip())

#  Show previous queries from session memory
with st.sidebar.expander("Session Memory", expanded=False):
    if st.session_state.memory:
        for i, entry in enumerate(st.session_state.memory[::-1]):  # latest first
            st.markdown(f"**{i+1}.** [{entry['url']}]({entry['url']})")
            if entry['question']:
                st.markdown(f"- Q: _{entry['question']}_")
            st.markdown(f"- A: {entry['summary_answer'][:100]}...\n")
            st.markdown("---")
    else:
        st.write("No history yet.")