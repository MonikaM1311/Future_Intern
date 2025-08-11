# rasa/actions.py
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'tickets.sqlite3')
FALLBACK_MODULE = os.path.join(os.path.dirname(__file__), '..', 'openai_fallback', 'generator.py')

class ActionCreateTicket(Action):
    def name(self) -> Text:
        return "action_create_ticket"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user = tracker.get_slot('user_name') or 'anonymous'
        issue = tracker.latest_message.get('text')

        os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'db'), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY, user TEXT, issue TEXT)")
        cur.execute("INSERT INTO tickets (user, issue) VALUES (?, ?)", (user, issue))
        conn.commit()
        ticket_id = cur.lastrowid
        conn.close()

        dispatcher.utter_message(text=f"I've created a ticket for you. Ticket ID: {ticket_id}")
        return []


class ActionFallbackResponse(Action):
    def name(self) -> Text:
        return "action_fallback_response"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Load fallback generator dynamically to avoid heavy deps at rasa start
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location('fallback', FALLBACK_MODULE)
            fallback = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fallback)
            # prepare context
            last_user = tracker.latest_message.get('text')
            faqs_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'faqs.json')
            faq_text = ''
            if os.path.exists(faqs_path):
                with open(faqs_path, 'r', encoding='utf-8') as f:
                    faqs = json.load(f)
                    faq_text = '\n'.join([f"Q: {q['question']} A: {q['answer']}" for q in faqs[:5]])

            resp = fallback.generate_fallback(last_user, faq_text, '')
            dispatcher.utter_message(text=resp)
            return []
        except Exception as e:
            dispatcher.utter_message(text="Sorry, I'm having trouble reaching the fallback service. I can create a ticket for you.")
            return []