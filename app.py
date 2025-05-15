import os
import json
import datetime as dt
import requests
import streamlit as st
from dotenv import load_dotenv

# ───────────── 1. ENV ────────────────────────────────────────────────────────
load_dotenv(".env", override=False)

X_TOKEN   = os.getenv("X_BEARER_TOKEN")          # Twitter/X Bearer token
GROK_KEY  = os.getenv("GROK_API_KEY")            # xAI server key
MODEL_ID  = os.getenv("GROK_MODEL_ID", "grok-3-beta")
ELON_ID   = os.getenv("ELON_ID", "44196397")     # @elonmusk
GROK_EP   = "https://api.x.ai/v1/chat/completions"

if not (X_TOKEN and GROK_KEY):
    st.error("❌  X_BEARER_TOKEN or GROK_API_KEY missing. Check .env / Secrets.")
    st.stop()

# ───────────── 2. Helpers ────────────────────────────────────────────────────
def fetch_tweets(max_results=50):
    url = f"https://api.twitter.com/2/users/{ELON_ID}/tweets"
    headers = {"Authorization": f"Bearer {X_TOKEN}"}
    params  = {
        "max_results": max_results,
        "tweet.fields": "created_at,referenced_tweets"
    }
    r = requests.get(url, headers=headers, params=params, timeout=15)
    if r.status_code != 200:
        raise RuntimeError(f"{r.status_code}: {r.text[:120]}")
    return r.json().get("data", [])

def looks_empty(tweet):
    """True if tweet is only a link or very short/emoji."""
    txt = tweet["text"].strip()
    return txt.startswith("http") or len(txt) < 10

@st.cache_data(ttl=1800)      # 30‑min cache
def get_checked(n=5):
    tweets = fetch_tweets(50)

    # ---- keep: originals + quotes/replies with comment; skip pure retweets/empty
    filtered = []
    for t in tweets:
        rt_info = t.get("referenced_tweets")
        if rt_info and any(r["type"] == "retweeted" for r in rt_info) \
                and t["text"].startswith("RT "):
            continue                       # pure retweet
        if looks_empty(t):
            continue                       # link-only or emoji
        filtered.append(t)

    if not filtered:
        return []

    # ---- Grok fact‑check
    checked = []
    for tw in filtered[:n]:
        body = {
            "model": MODEL_ID,
            "messages": [
                {"role": "system",
                 "content": ("Return JSON {conclusion:true|false|uncertain,"
                             "reason,sources}")},
                {"role": "user", "content": tw["text"]},
            ],
        }
        try:
            r = requests.post(
                GROK_EP,
                headers={"Authorization": f"Bearer {GROK_KEY}",
                         "Content-Type": "application/json"},
                json=body,
                timeout=30,
            )
            r.raise_for_status()
            tw["fact"] = json.loads(r.json()["choices"][0]["message"]["content"])
        except Exception as e:
            tw["fact"] = {
                "conclusion": "uncertain",
                "reason": f"Grok error: {e}",
                "sources": [],
            }
        checked.append(tw)

    return checked

# ───────────── 3. UI ─────────────────────────────────────────────────────────
st.set_page_config(page_title="Musk Interference Model", page_icon="🤖")
st.title("🤖 Musk Interference Model — Live Fact Check")
st.caption(f"Model: **{MODEL_ID}** • Cache 30 min")

# About Button (zentral platziert)
if st.button("ℹ️ About this project"):
    with open("README.md", "r") as f:
        st.markdown(f.read(), unsafe_allow_html=True)
    st.stop()

if st.button("🔄 Refresh tweets", use_container_width=True):
    st.cache_data.clear()
    st.experimental_rerun()

data = get_checked()
if not data:
    st.info("No eligible tweets in the current window.")
    st.stop()

for t in data:
    st.subheader(t["text"])
    verdict = t["fact"]["conclusion"]
    color   = {"true": "green", "false": "red",
               "uncertain": "orange"}.get(verdict, "gray")
    st.markdown(
        f"**Result:** <span style='color:{color};font-weight:600'>{verdict}</span>",
        unsafe_allow_html=True,
    )
    st.markdown(f"**Reason:** {t['fact']['reason']}")

    sources = t["fact"].get("sources", [])
    if isinstance(sources, str):
        sources = [sources]
    if sources:
        st.markdown("**Sources**")
        for s in sources:
            st.write("•", s)

    ts = dt.datetime.fromisoformat(t["created_at"].replace("Z", ""))
    st.caption(ts.strftime("%d %b %Y %H:%M UTC"))
    st.divider()