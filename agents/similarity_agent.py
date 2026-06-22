import json
from utils.groq_client import client


def compare_complaints(text1, text2):

    prompt = f"""
You are a cybercrime analyst.

Determine if these two complaints belong to the same scam campaign.

Return ONLY JSON.

Schema:

{{
    "same_campaign": true,
    "confidence": 0,
    "reason": ""
}}

Complaint 1:
{text1}

Complaint 2:
{text2}
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