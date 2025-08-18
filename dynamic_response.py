# dynamic_response.py
import os
import requests
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def _chat(messages, model="llama-3.1-8b-instant"):
    if not GROQ_API_KEY:
        return "I couldn't reach the AI service. Please set GROQ_API_KEY."
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 512,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=45)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()

def generate_response(object_label: str,
                      question: str = "",
                      history=None,
                      visual_facts: dict | None = None) -> str:
    vf_txt = ""
    if visual_facts:
        parts = [f"{k.replace('_',' ')}: {v}" for k, v in visual_facts.items() if v]
        if parts:
            vf_txt = "Visual facts (precomputed): " + "; ".join(parts)

    sys = (
        "You are a friendly educational tutor for kids. "
        "Explain simply and accurately. Prefer short, clear sentences. "
        "Use any provided visual facts; do NOT ask the user to describe the image."
    )

    base = [
        {"role": "system", "content": sys},
        {"role": "user", "content": f"The image contains: {object_label}."},
    ]
    if vf_txt:
        base.append({"role": "user", "content": vf_txt})
    if history and isinstance(history, list):
        base.extend(history)

    if question:
        base.append({"role": "user", "content": f"Question about this image: {question}"})
    else:
        base.append({"role": "user", "content": "Teach me something interesting about it."})

    try:
        return _chat(base)
    except Exception as e:
        return f"(AI error) {e}"
