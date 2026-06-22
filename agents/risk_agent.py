DIGITAL_ARREST_KEYWORDS = [
    "cbi",
    "ed",
    "police",
    "arrest",
    "investigation",
    "money laundering",
    "customs",
    "court notice"
]

BANKING_FRAUD_KEYWORDS = [
    "kyc",
    "bank account",
    "account blocked",
    "otp",
    "verify account"
]


def calculate_risk(extracted_data):

    score = 0
    reasons = []

    authority_names = [
        x.lower()
        for x in extracted_data.get("authority_names", [])
    ]

    summary = extracted_data.get("summary", "").lower()

    scam_type = extracted_data.get(
        "scam_type",
        ""
    ).lower()

    amounts = extracted_data.get(
        "amounts",
        []
    )

    upi_ids = extracted_data.get(
        "upi_ids",
        []
    )

    # Authority impersonation

    if authority_names:
        score += 30
        reasons.append(
            "Authority impersonation detected"
        )

    # Money request

    if amounts:
        score += 20
        reasons.append(
            "Financial demand detected"
        )

    # UPI present

    if upi_ids:
        score += 20
        reasons.append(
            "Payment destination identified"
        )

    # Digital arrest

    for keyword in DIGITAL_ARREST_KEYWORDS:

        if keyword in summary or keyword in scam_type:
            score += 20

            reasons.append(
                "Digital arrest indicators present"
            )

            break

    score = min(score, 100)

    if score >= 80:
        severity = "CRITICAL"

    elif score >= 60:
        severity = "HIGH"

    elif score >= 40:
        severity = "MEDIUM"

    else:
        severity = "LOW"

    return {
        "risk_score": score,
        "severity": severity,
        "reasons": reasons
    }