import json
from utils.groq_client import client


def extract_entities(text):

    prompt = f"""
You are an expert cybercrime analyst.

Extract the following information from the text.

Return ONLY valid JSON.

Schema:

{{
    "phone_numbers": [],
    "upi_ids": [],
    "urls": [],
    "authority_names": [],
    "amounts": [],
    "scam_type": "",
    "summary": ""
}}

Text:
{text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    content = response.choices[0].message.content
    content = content.replace("```json", "")
    content = content.replace("```", "")
    content = content.strip()

    return json.loads(content)