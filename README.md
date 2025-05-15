# Musk Interference Model (MIM)

## Overview

The **Musk Interference Model (MIM)** is a web-based prototype that explores the intersection of computational fact-checking, platform discourse, and the performative power of high-profile social media actors. Using Twitter’s API and xAI’s Grok language model, the tool fetches recent tweets from Elon Musk, filters relevant messages, and subjects them to a structured verification routine. The result is a machine-assisted evaluation of the truth value, reasoning, and source attribution of individual tweets in near real time.

---

## Motivation

Elon Musk wields disproportionate influence in public discourse—not only as a tech entrepreneur, but as the owner of a platform that shapes global attention. Under the banner of "free speech," he often spreads questionable claims and unverified information. These messages are not fringe content; they are highly visible, often widely accepted, and have real-world effects.

This prototype was created to expose the irony of Musk's information dominance: by using his own advanced language model—xAI's Grok—to check the factual integrity of his statements on his own platform. In doing so, MIM reflects on the recursive loop of influence, truth, and technological power. It is a small, focused intervention, rooted in a belief that platforms must not be treated as neutral spaces when they actively shape the boundaries of public understanding.

---

## How it works

1. The application uses the Twitter API to retrieve the most recent tweets by Elon Musk.
2. A lightweight filtering algorithm removes retweets, short links, and non-substantive content.
3. Each tweet is submitted to Grok (via xAI’s API), using a custom system prompt requesting structured JSON output including:
    - `conclusion`: true / false / uncertain
    - `reason`: explanation for the assessment
    - `sources`: optional external or factual links
4. The result is visualized in the Streamlit frontend with contextual metadata, highlighting uncertainty and machine limitations.

---

## Technologies

- Python 3.10+
- Streamlit
- Twitter API v2
- xAI Grok API (grok-3-beta)

---

## Disclaimer

This prototype is an artistic and exploratory tool. It is not a fact-checking authority, nor is it affiliated with Twitter, xAI, or Elon Musk. All evaluations are generated via large language models and should be treated as speculative insights—not verified truth.

---

## License

MIT License. Built by Welf Lehmann for academic submission to the Master’s program *Design & Computation* at UdK/TU Berlin.

---

## Live Demo

👉 [https://musk-interference-model.streamlit.app](https://musk-interference-model.streamlit.app)
