import json
import re

from utils.groq_client import client


# =========================================================
# VALIDATION PATTERNS
# =========================================================

PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)"
)

UPI_PATTERN = re.compile(
    r"\b[a-zA-Z0-9._-]{2,}@[a-zA-Z]{2,}\b"
)

URL_PATTERN = re.compile(
    r'(?:https?://|www\.)[^\s<>"\']+',
    re.IGNORECASE
)


# =========================================================
# NORMALIZATION HELPERS
# =========================================================

def normalize_phone(phone):
    digits = re.sub(r"\D", "", phone)

    # Remove Indian country code
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]

    if len(digits) == 10:
        return digits

    return None


def normalize_upi(upi):
    upi = upi.strip().lower()

    if "@" not in upi:
        return None

    username, provider = upi.split("@", 1)

    if len(username) < 2:
        return None

    if len(provider) < 2:
        return None

    return f"{username}@{provider}"


def normalize_url(url):
    url = url.strip()

    # Remove punctuation accidentally captured at the end
    url = url.rstrip(".,!?;:)]}")

    return url


# =========================================================
# REGEX EXTRACTION
# =========================================================

def extract_verified_phones(text):
    matches = re.findall(PHONE_PATTERN, text)

    phones = []

    for match in matches:
        normalized = normalize_phone(match)

        if normalized and normalized not in phones:
            phones.append(normalized)

    return phones


def extract_verified_upis(text):
    matches = re.findall(UPI_PATTERN, text)

    upis = []

    for match in matches:
        normalized = normalize_upi(match)

        if normalized and normalized not in upis:
            upis.append(normalized)

    return upis


def extract_verified_urls(text):
    matches = re.findall(URL_PATTERN, text)

    urls = []

    for match in matches:
        normalized = normalize_url(match)

        if normalized and normalized not in urls:
            urls.append(normalized)

    return urls


# =========================================================
# LLM EXTRACTION
# =========================================================

def extract_entities(text):

    prompt = f"""
You are an expert cybercrime analyst.

Analyze the following suspicious message.

Extract information into the exact JSON schema below.

IMPORTANT:
- Do NOT invent information.
- Only include entities explicitly present in the text.
- If a field is not present, return an empty list.
- Keep scam_type concise.
- Keep summary factual and short.
- Do not infer phone numbers, UPI IDs or URLs.

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

    # =====================================================
    # GROQ REQUEST
    # =====================================================

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

    content = response.choices[0].message.content

    if not content:
        content = ""

    content = content.strip()

    # Remove Markdown JSON fences if the model adds them
    if content.startswith("```json"):
        content = content[7:]

    elif content.startswith("```"):
        content = content[3:]

    if content.endswith("```"):
        content = content[:-3]

    content = content.strip()

    # =====================================================
    # PARSE LLM JSON
    # =====================================================

    try:
        extracted = json.loads(content)

    except (json.JSONDecodeError, TypeError):
        extracted = {}

    # Make absolutely sure we have a dictionary
    if not isinstance(extracted, dict):
        extracted = {}

    # =====================================================
    # REGEX-VERIFIED ENTITIES
    # =====================================================

    verified_phones = extract_verified_phones(text)
    verified_upis = extract_verified_upis(text)
    verified_urls = extract_verified_urls(text)

    # =====================================================
    # IMPORTANT:
    #
    # Concrete identifiers come from the actual text,
    # NOT from the LLM.
    #
    # This prevents the LLM from hallucinating:
    # - phone numbers
    # - UPI IDs
    # - URLs
    # =====================================================

    extracted["phone_numbers"] = verified_phones
    extracted["upi_ids"] = verified_upis
    extracted["urls"] = verified_urls

    # =====================================================
    # SAFETY DEFAULTS
    # =====================================================

    extracted.setdefault("authority_names", [])
    extracted.setdefault("amounts", [])
    extracted.setdefault("scam_type", "")
    extracted.setdefault("summary", "")

    # =====================================================
    # TYPE VALIDATION
    # =====================================================

    if not isinstance(
        extracted.get("authority_names"),
        list
    ):
        extracted["authority_names"] = []

    if not isinstance(
        extracted.get("amounts"),
        list
    ):
        extracted["amounts"] = []

    if not isinstance(
        extracted.get("phone_numbers"),
        list
    ):
        extracted["phone_numbers"] = verified_phones

    if not isinstance(
        extracted.get("upi_ids"),
        list
    ):
        extracted["upi_ids"] = verified_upis

    if not isinstance(
        extracted.get("urls"),
        list
    ):
        extracted["urls"] = verified_urls

    if not isinstance(
        extracted.get("scam_type"),
        str
    ):
        extracted["scam_type"] = ""

    if not isinstance(
        extracted.get("summary"),
        str
    ):
        extracted["summary"] = ""

    return extracted