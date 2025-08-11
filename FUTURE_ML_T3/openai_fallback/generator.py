# openai_fallback/generator.py
import os
import openai

openai.api_key = os.getenv('OPENAI_API_KEY')
MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

PROMPT = (
    "You are a helpful customer support assistant. Use only the provided FAQ and context to answer. "
    "If the answer is not present, apologize and offer to create a support ticket. Do not invent personal data.\n\n"
    "FAQ:\n{faq}\n\nContext:\n{context}\n\nUser:\n{user}\n\nAnswer:"
)


def generate_fallback(user_text: str, faq_text: str, context_text: str) -> str:
    if not openai.api_key:
        return "Fallback unavailable (OPENAI_API_KEY not set). I can create a support ticket instead."
    prompt = PROMPT.format(faq=faq_text or 'None', context=context_text or 'None', user=user_text)
    try:
        resp = openai.ChatCompletion.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.15,
        )
        return resp['choices'][0]['message']['content'].strip()
    except Exception as e:
        return "Sorry, I couldn't generate an answer right now. I can create a ticket for you."