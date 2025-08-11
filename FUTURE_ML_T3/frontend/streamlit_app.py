import streamlit as st
import requests
import os
from dotenv import load_dotenv
load_dotenv()

RASA_URL = os.getenv('RASA_URL', 'http://localhost:5005')

st.set_page_config(page_title='SupportBot', layout='centered')
st.title('SupportBot — Demo')

if 'messages' not in st.session_state:
    st.session_state.messages = []

with st.form('msg'):
    user_input = st.text_input('You:', '')
    submitted = st.form_submit_button('Send')

if submitted and user_input:
    st.session_state.messages.append({'role': 'user', 'text': user_input})
    # send to Rasa REST webhook
    try:
        resp = requests.post(f"{RASA_URL}/webhooks/rest/webhook", json={"sender": "user1", "message": user_input}, timeout=6)
        data = resp.json()
        for item in data:
            text = item.get('text')
            if text:
                st.session_state.messages.append({'role': 'bot', 'text': text})
    except Exception as e:
        st.session_state.messages.append({'role': 'bot', 'text': 'Error connecting to Rasa. Is it running?'})

for m in st.session_state.messages:
    if m['role'] == 'user':
        st.write(f"**You**: {m['text']}")
    else:
        st.write(f"**Bot**: {m['text']}")

if st.button('Create Ticket (demo)'):
    # call action via Rasa's /conversations/<sender>/trigger_intent or simply ask the user
    st.info('To create a ticket, send a message 