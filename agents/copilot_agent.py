from utils.groq_client import client


def ask_copilot(question, context):

    prompt = f"""
You are a cybercrime investigation assistant.

Context:
{context}

Question:
{question}

Give practical advice in under 150 words.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content