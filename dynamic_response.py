import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Maintain conversation state (list of messages)
conversation_history = [
    {"role": "system", "content": "You are a fun educational assistant for kids. Respond helpfully and kindly."}
]

def generate_response(user_message):
    # Add user message to the conversation
    conversation_history.append({"role": "user", "content": user_message})

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation_history
    )

    assistant_message = completion.choices[0].message.content.strip()

    # Add assistant's reply to the history
    conversation_history.append({"role": "assistant", "content": assistant_message})

    return assistant_message
