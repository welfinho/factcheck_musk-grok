import os
import json
import datetime as dt
import requests
import streamlit as st

# ───────────── 1. ENV ────────────────────────────────────────────────────────

X_TOKEN   = st.secrets["X_BEARER_TOKEN"]
GROK_KEY  = st.secrets["GROK_API_KEY"]
MODEL_ID  = st.secrets.get("GROK_MODEL_ID", "grok-3-beta")
ELON_ID   = st.secrets.get("ELON_ID", "44196397")

if not (X_TOKEN and GROK_KEY):
    st.error("❌  X_BEARER_TOKEN or GROK_API_KEY missing. Check .env / Secrets.")
    st.stop()

# ───────────── 2. Helpers ────────────────────────────────────────────────────
def fetch_tweets(max_results=50):
    try:
        url = f"https://api.twitter.com/2/users/{ELON_ID}/tweets"
        headers = {"Authorization": f"Bearer {X_TOKEN}"}
        params = {
            "max_results": max_results,
            "tweet.fields": "created_at,referenced_tweets"
        }
        r = requests.get(url, headers=headers, params=params, timeout=15)
        if r.status_code == 429:
            st.error("📉 Twitter API request limit reached (Free Tier). Please wait 15 minutes and try again.")
            st.stop()
        elif r.status_code != 200:
            st.error(f"❌ Twitter API error ({r.status_code}). Try again later.")
            st.stop()
        return r.json().get("data", [])
    except Exception:
        st.error("⚠️ Could not fetch tweets from Twitter. Please try again later.")
        st.stop()

def looks_empty(tweet):
    txt = tweet["text"].strip()
    return txt.startswith("http") or len(txt) < 10

@st.cache_data(ttl=1800)
def get_checked(n=5):
    tweets = fetch_tweets(50)
    filtered = []
    for t in tweets:
        rt_info = t.get("referenced_tweets")
        if rt_info and any(r["type"] == "retweeted" for r in rt_info) and t["text"].startswith("RT "):
            continue
        if looks_empty(t):
            continue
        filtered.append(t)

    if not filtered:
        return []

    checked = []
    for tw in filtered[:n]:
        body = {
            "model": MODEL_ID,
            "messages": [
                {"role": "system", "content": "Return JSON {conclusion:true|false|uncertain,reason,sources}"},
                {"role": "user", "content": tw["text"]},
            ],
        }
        try:
            r = requests.post(
                GROK_EP,
                headers={"Authorization": f"Bearer {GROK_KEY}", "Content-Type": "application/json"},
                json=body,
                timeout=30,
            )
            r.raise_for_status()
            tw["fact"] = json.loads(r.json()["choices"][0]["message"]["content"])
        except requests.exceptions.HTTPError as e:
            if r.status_code == 429:
                reason = "xAI request limit reached. Try again in 15 minutes."
            else:
                reason = f"xAI API error ({r.status_code})."
            tw["fact"] = {"conclusion": "uncertain", "reason": reason, "sources": []}
        except Exception:
            tw["fact"] = {
                "conclusion": "uncertain",
                "reason": "Unexpected error while contacting xAI.",
                "sources": [],
            }
        checked.append(tw)

    return checked

# ───────────── 3. UI ─────────────────────────────────────────────────────────
st.set_page_config(page_title="Musk Interference Model", page_icon="🤖")
st.markdown("<h1 style='text-align: center;'>🤖 Musk Interference Model</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Live Fact Check</h3>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>Model: <b>{MODEL_ID}</b> • Cache 30 min</p>", unsafe_allow_html=True)

if "show_readme" not in st.session_state:
    st.session_state.show_readme = False
if "tweet_count" not in st.session_state:
    st.session_state.tweet_count = 5

# ───────────── Buttons ───────────────────────────────────────────────────────
col = st.columns([3, 4, 3])
with col[1]:
    if st.button("ℹ️ About this project", use_container_width=True):
        st.session_state.show_readme = not st.session_state.show_readme

if st.session_state.show_readme:
    with open("README.md", "r") as f:
        st.markdown(f.read(), unsafe_allow_html=True)
    st.stop()

col2 = st.columns([3, 4, 3])
with col2[1]:
    if st.button("🔄 Refresh tweets", use_container_width=True):
        st.cache_data.clear()
        st.experimental_rerun()

# ───────────── Tweets anzeigen ───────────────────────────────────────────────
data = get_checked(st.session_state.tweet_count)
if not data:
    st.info("No eligible tweets in the current window.")
    st.stop()

for t in data:
    st.subheader(t["text"])
    verdict = t["fact"]["conclusion"]
    color = {"true": "green", "false": "red", "uncertain": "orange"}.get(verdict, "gray")
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

# ───────────── Show More Button ──────────────────────────────────────────────
col3 = st.columns([3, 4, 3])
with col3[1]:
    if st.button("➕ Show more tweets", use_container_width=True):
        st.session_state.tweet_count += 5
        st.experimental_rerun()