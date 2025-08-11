# Chatbot for Customer Support — End-to-End Project

**Task 3 — Smart Customer Support Chatbot (End-to-end)**

> Complete, runnable project to build, train, and deploy a customer-support chatbot using Rasa (NLU + dialogue), OpenAI fallback, Streamlit web UI, and Telegram integration. Includes dataset preprocessing, Docker deployment, CI, and example code.

---

## Table of contents

1. Project Overview
2. Architecture
3. Repo Layout (what you'll find)
4. Quickstart (run locally)
5. Dataset & Preprocessing
6. Rasa: NLU, Domain, Stories, Actions
7. OpenAI Fallback (Generative)
8. Frontend: Streamlit chat UI
9. Telegram Bot Integration
10. Docker & Deployment
11. Testing & CI
12. Environment variables
13. Security & Privacy
14. Roadmap & Improvements
15. License & Contact

---

## 1) Project overview

This repository implements a hybrid customer-support chatbot:

* **Deterministic NLU & Dialogue** using **Rasa** for intent detection, entity extraction, and rule-based flows (greetings, FAQs, ticket creation).
* **Generative fallback** using **OpenAI** (or another LLM) to answer queries that the NLU can't confidently match.
* **Frontend**: Streamlit web UI for demo & quick testing.
* **Messaging**: Telegram bot integration for real chat experience.
* **Persistence**: Simple SQLite ticketing DB and logs for analytics.

Goal: deliver a production-like pipeline that you can run locally, test, and deploy.

---

## 2) Architecture (high level)

```
User (Streamlit / Telegram)
        |
Frontend -> Router -> Rasa HTTP API
                      |      \
                matched intent  fallback (confidence < threshold)
                      |              |
                 Rasa responses   OpenAI fallback generator
                      |              |
                 Actions server -> ticket DB / logs
```

---

## 3) Repo layout

```
/ (root)
├─ README.md
├─ requirements.txt
├─ data/
│  ├─ raw/                        # put kaggle CSV here
│  ├─ preprocess.py               # converts raw CSV -> rasa nlu + faq
│  └─ faqs.json                   # generated FAQ file
├─ rasa/
│  ├─ config.yml
│  ├─ domain.yml
│  ├─ data/
│  │  ├─ nlu.yml
│  │  ├─ stories.yml
│  │  └─ rules.yml
│  ├─ actions.py
│  └─ credentials.yml
├─ openai_fallback/
│  └─ generator.py
├─ frontend/
│  └─ streamlit_app.py
├─ bots/
│  └─ telegram_bot.py
├─ db/
│  └─ tickets.sqlite3             # created at runtime
├─ docker/
│  └─ docker-compose.yml
├─ .github/workflows/ci.yml
└─ LICENSE
```

---

## 4) Quickstart (run locally)

Prereqs:

* Python 3.10+
* pip
* (Optional) Docker & docker-compose

Steps:

1. Clone repository

```bash
git clone <your-repo-url>
cd chatbot-customer-support
python -m venv .venv
source .venv/bin/activate   # windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Place dataset

* Download the **Customer Support Conversations** Kaggle CSV and place it into `data/raw/customer_support.csv`.

3. Preprocess dataset to generate Rasa training data and FAQs

```bash
python data/preprocess.py --input data/raw/customer_support.csv --out_dir rasa/data --faq_out data/faqs.json
```

4. Train Rasa

```bash
cd rasa
rasa train
# run actions server in one terminal
rasa run actions &
# run core in another
rasa run --enable-api
```

5. Start Streamlit UI

```bash
streamlit run frontend/streamlit_app.py
```

6. (Optional) Start Telegram bot

```bash
python bots/telegram_bot.py
```

Open Streamlit URL and test. The UI sends messages to Rasa HTTP API, and Rasa will either reply or call OpenAI fallback when confidence is low.

---

## 5) Dataset & Preprocessing

`data/preprocess.py` does the following:

* Loads the Kaggle CSV
* Normalizes text (lowercase, remove strange whitespace)
* Masks PII (emails, phone numbers)
* Converts multi-turn conversation examples to Rasa `nlu.yml` format: `intent` with multiple `- text:` examples
* Extracts top-k FAQs into `data/faqs.json` (question -> canonical answer)

**Usage**:

```
python data/preprocess.py --input data/raw/customer_support.csv --out_dir rasa/data --faq_out data/faqs.json
```

**Notes**: The script uses heuristics for mapping messages to intents. You should iterate on the label mapping if you know common intents (e.g., `greet`, `goodbye`, `ask_refund`, `order_status`).

---

## 6) Rasa: NLU, Domain, Stories, Actions

Key Rasa files (already included as templates):

* `rasa/data/nlu.yml` — intents and example utterances
* `rasa/domain.yml` — intents, entities, slots, responses, actions
* `rasa/data/stories.yml` — example conversational flows
* `rasa/data/rules.yml` — rules like FAQ handling and fallback
* `rasa/actions.py` — custom actions (ticket creation, search faqs)

### Example `domain.yml` snippet

```yaml
intents:
  - greet
  - goodbye
  - ask_refund
  - order_status

responses:
  utter_greet:
    - text: "Hello! How can I help you today?"
  utter_goodbye:
    - text: "Thanks for reaching out — have a great day!"

actions:
  - action_create_ticket
  - action_fallback_response
```

### Example `actions.py` (essential parts)

```python
# rasa/actions.py
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import sqlite3

DB_PATH = "../db/tickets.sqlite3"

class ActionCreateTicket(Action):
    def name(self) -> Text:
        return "action_create_ticket"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user = tracker.get_slot("user_name") or "anonymous"
        issue = tracker.latest_message.get('text')

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY, user TEXT, issue TEXT)")
        cur.execute("INSERT INTO tickets (user, issue) VALUES (?, ?)", (user, issue))
        conn.commit()
        ticket_id = cur.lastrowid
        conn.close()

        dispatcher.utter_message(text=f"I've created a ticket for you. Ticket ID: {ticket_id}")
        return []
```

### Fallback handling

Use Rasa's `ResponseSelector` / rules for low-confidence detection. If `confidence` < threshold (e.g., 0.4) then call `action_fallback_response` which invokes the OpenAI fallback generator (see next section).

---

## 7) OpenAI Fallback (Generative)

File: `openai_fallback/generator.py`

Purpose: Provide a context-aware answer when Rasa can't confidently match an intent.

Key ideas:

* Use a short context window: last 4 user messages + matched FAQ if any.
* Provide grounding: load `data/faqs.json` and pass top relevant FAQ text in prompt.
* Use a safety prompt to avoid hallucination and to refuse handling PII.

**Example usage**:

```python
import os
import openai
openai.api_key = os.getenv('OPENAI_API_KEY')

PROMPT = (
    "You are a helpful customer support assistant. Answer concisely using only the provided FAQ and context. "
    "If the answer is not in the FAQ, offer a short apology and propose to create a support ticket.\n\n"
    "FAQ:\n{faq}\n\nContext:\n{context}\n\nUser:\n{user}\n\nAnswer:"
)


def generate_fallback(user_text, faq_text, context_text):
    prompt = PROMPT.format(faq=faq_text, context=context_text, user=user_text)
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        max_tokens=200,
        temperature=0.2,
    )
    return resp['choices'][0]['message']['content'].strip()
```

**Important**: Do **not** send PII to OpenAI. Mask or prompt the model to refuse PII content.

---

## 8) Frontend: Streamlit chat UI

File: `frontend/streamlit_app.py`

Features:

* Chat interface (messages from user and bot)
* Quick-reply FAQ buttons
* Escalation button to create a ticket
* Toggle to use OpenAI fallback or not

The Streamlit app uses Rasa HTTP API endpoints:

* POST `/webhooks/rest/webhook` to send user message
* Read responses (and actions) and render them

**Minimal flow**:

1. User types message
2. App calls Rasa REST webhook
3. If Rasa replies normally → show reply
4. If Rasa triggers fallback action → UI shows model-generated response

The repo includes a ready-to-run Streamlit app template. Customize the UI colors / quick replies to your liking.

---

## 9) Telegram Bot Integration

File: `bots/telegram_bot.py`

Two modes supported:

* Polling (easy for local testing)
* Webhook (recommended for production — requires publicly reachable URL)

Bot behaviour:

* Forward messages to Rasa HTTP API
* Send responses back to the user
* Provide `/create_ticket` command that triggers `action_create_ticket`

**Notes**: Keep your `TELEGRAM_BOT_TOKEN` in env vars.

---

## 10) Docker & Deployment

A `docker/docker-compose.yml` file is included to run the stack locally. Services:

* `rasa` (Rasa server)
* `actions` (Rasa actions server)
* `streamlit` (frontend)
* `postgres` or `sqlite` for persistence (SQLite used by default for simplicity)

**Run**:

```bash
cd docker
docker-compose up --build
```

**Deploying tips**:

* For staging: use Railway / DigitalOcean / Render to run Rasa + actions. Deploy Streamlit separately (Streamlit Cloud) or use a lightweight web server.
* For production: consider using a managed DB (Postgres), set up HTTPS, use a message broker if scaling actions, and implement rate limiting.

---

## 11) Testing & CI

* Unit tests: `tests/test_preprocess.py`, `tests/test_actions.py` (mock DB)
* Integration tests: small script that sends messages to Rasa REST and verifies replies
* GitHub Actions: `.github/workflows/ci.yml` runs linting and unit tests on push

---

## 12) Environment variables (important)

Store these in `.env` (do not commit) or in your deployment secret store:

```
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=...
RASA_URL=http://rasa:5005
FALLBACK_CONFIDENCE_THRESHOLD=0.4
DATABASE_URL=sqlite:///db/tickets.sqlite3
```

---

## 13) Security & Privacy

* **PII**: Mask or remove PII (emails, phone numbers, payment info) before sending anything to external services.
* **Logging**: Redact sensitive fields in logs.
* **Rate-limiting**: Add per-IP rate limits to any public webhooks.
* **Secrets**: Use env vars and secret managers.

---

## 14) Roadmap & improvements

* Add more intents and collect labeling feedback from real chats
* Integrate knowledge base (vector DB + retrieval-augmented generation) to reduce hallucinations
* Human-in-the-loop dashboard for escalations
* Multi-language support
* Add analytics dashboards (Power BI / Superset) for ticket & intent metrics

---

## 15) License & Contact

MIT License — see `LICENSE` file.

Maintainer: \[Your Name] — update `README` with your contact info.

---

## Ready-made deliverables in this repo

* Working Rasa project skeleton and training data generator
* OpenAI fallback module with grounding using `data/faqs.json`
* Streamlit frontend that connects to Rasa
* Telegram bot adapter
* Docker compose for local end-to-end testing
* CI pipeline to run tests and linting

---

If you'd like, I can now:

* (A) generate the actual files (preprocess.py, rasa/\*, frontend/streamlit\_app.py, openai\_fallback/generator.py, bots/telegram\_bot.py, docker-compose.yml) and add them to the repo canvas, OR
* (B) create one single ready-to-run ZIP with everything pre-filled (I can produce the files here so you can copy them), OR
* (C) implement the Streamlit front-end first so you can demo quickly.

Tell me which option you prefer and I’ll create the code files next.
