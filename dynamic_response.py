from groq import Groq

# dynamic_response.py
import os
import requests
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def _chat(messages, model="llama-3.1-8b-instant"):
    """
    Minimal Groq Chat Completions call.
    """
    if not GROQ_API_KEY:
        # Fallback so app still works without a key
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

def generate_response(object_label: str, question: str = "", history=None) -> str:
    """
    If question provided, answer it using the image context (object_label).
    Otherwise, provide an educational, kid-friendly explanation of the object.
    history: optional list of {"role": "user"|"assistant", "content": "..."}
    """
    sys = (
        "You are a friendly, educational tutor for kids. "
        "Explain concepts simply and accurately. Keep answers concise."
    )

    base = [
        {"role": "system", "content": sys},
        {"role": "user", "content": f"The image contains: {object_label}."},
    ]

    if history and isinstance(history, list):
        base.extend(history)

    if question:
        base.append(
            {"role": "user", "content": f"Question about this image: {question}"}
        )
        prompt = base
    else:
        base.append(
            {"role": "user", "content": "Teach me something interesting about it."}
        )
        prompt = base

    try:
        return _chat(prompt)
    except Exception as e:
        return f"(AI error) {e}"
