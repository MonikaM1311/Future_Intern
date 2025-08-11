"""Simple preprocessing to convert Kaggle Customer Support Conversations CSV
into Rasa nlu.yml examples and an FAQ JSON.
Usage:
python data/preprocess.py --input data/raw/customer_support.csv --out_dir rasa/data --faq_out data/faqs.json
"""
import argparse
import pandas as pd
import re
import json
from collections import Counter

EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+")
PHONE_RE = re.compile(r"\+?\d[\d \-]{5,}\d")

INTENT_MAP = {
    'hi': 'greet',
    'hello': 'greet',
    'refund': 'ask_refund',
    'return': 'ask_refund',
    'order status': 'order_status',
    'where is my order': 'order_status',
    'thanks': 'thanks',
}


def mask_pii(text: str) -> str:
    text = EMAIL_RE.sub('<email>', text)
    text = PHONE_RE.sub('<phone>', text)
    return text


def guess_intent(text: str) -> str:
    txt = text.lower()
    for k, v in INTENT_MAP.items():
        if k in txt:
            return v
    return 'other'


def build_nlu_examples(df: pd.DataFrame, out_path: str):
    intents = {}
    for _, row in df.iterrows():
        user = str(row.get('message', '')).strip()
        if not user:
            continue
        user = mask_pii(user)
        intent = guess_intent(user)
        intents.setdefault(intent, []).append(user)

    nlu = {'version': '3.1', 'nlu': []}
    for intent, examples in intents.items():
        unique = list(dict.fromkeys(examples))[:200]
        ex_yaml = '\n'.join([f"- {e.replace('\n',' ')}" for e in unique])
        nlu['nlu'].append({'intent': intent, 'examples': '\n'.join([f"- {e}" for e in unique])})

    # write simple nlu.yml
    with open(out_path.rstrip('/') + '/nlu.yml', 'w', encoding='utf-8') as f:
        f.write('version: "3.1"\n')
        f.write('nlu:\n')
        for item in nlu['nlu']:
            f.write(f"- intent: {item['intent']}\n  examples: |\n")
            for ex in item['examples'].split('\n'):
                f.write(f"    {ex}\n")


def extract_faqs(df: pd.DataFrame, faq_out: str, top_k: int = 20):
    # Heuristic: Questions are messages containing '?' or starting with wh- words
    candidates = []
    for _, row in df.iterrows():
        text = str(row.get('message', '')).strip()
        if not text:
            continue
        if '?' in text or text.lower().split()[0] in ('what', 'when', 'where', 'how', 'why', 'which'):
            candidates.append(mask_pii(text))

    most = Counter(candidates).most_common(top_k)
    faqs = []
    for q, _ in most:
        faqs.append({'question': q, 'answer': 'Answer to this question should be filled manually or pulled from support docs.'})

    with open(faq_out, 'w', encoding='utf-8') as f:
        json.dump(faqs, f, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--out_dir', required=True)
    parser.add_argument('--faq_out', required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    # Expecting a column 'message' — adapt if dataset differs
    build_nlu_examples(df, args.out_dir)
    extract_faqs(df, args.faq_out)
    print('Generated rasa/data/nlu.yml and', args.faq_out)