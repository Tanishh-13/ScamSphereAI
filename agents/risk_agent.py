import re


# ============================================================
# KEYWORD GROUPS
# ============================================================

DIGITAL_ARREST_KEYWORDS = [
    "cbi",
    "ed",
    "police",
    "arrest",
    "investigation",
    "money laundering",
    "customs",
    "court notice",
    "digital arrest",
    "video call",
    "warrant",
    "cyber crime",
    "cybercrime",
]

BANKING_FRAUD_KEYWORDS = [
    "kyc",
    "bank account",
    "account blocked",
    "otp",
    "verify account",
    "account verification",
    "pan card",
    "aadhaar",
    "net banking",
    "bank verification",
]

PAYMENT_KEYWORDS = [
    "upi",
    "transfer",
    "send money",
    "payment",
    "deposit",
    "pay",
    "refund fee",
    "processing fee",
    "security deposit",
]

URGENCY_KEYWORDS = [
    "urgent",
    "immediately",
    "within 24 hours",
    "today",
    "last warning",
    "act now",
    "final notice",
    "immediate action",
]

THREAT_KEYWORDS = [
    "arrest",
    "legal action",
    "account blocked",
    "account freeze",
    "police case",
    "warrant",
    "jail",
    "prosecution",
    "criminal case",
]


# ============================================================
# HELPERS
# ============================================================

def contains_any(text, keywords):

    text = text.lower()

    return any(
        keyword in text
        for keyword in keywords
    )


# ============================================================
# RISK CALCULATION
# ============================================================

def calculate_risk(
    extracted_data,
    raw_text="",
    connections=None
):

    """
    Deterministic evidence-based risk engine.

    The LLM is ONLY responsible for extracting structured
    evidence. It does NOT directly decide the final score.

    Risk is calculated from:

    1. Hard evidence
       - phone
       - UPI
       - URL
       - money amount
       - authority impersonation

    2. Behavioural indicators
       - digital arrest
       - banking/KYC
       - payment requests
       - urgency
       - threats

    3. Historical evidence
       - previous complaints sharing identifiers
       - repeated scam patterns
       - occurrence frequency

    The final score is capped at 100.
    """

    score = 0
    reasons = []

    # ========================================================
    # NORMALIZE INPUT
    # ========================================================

    phones = extracted_data.get(
        "phone_numbers",
        []
    )

    upis = extracted_data.get(
        "upi_ids",
        []
    )

    urls = extracted_data.get(
        "urls",
        []
    )

    amounts = extracted_data.get(
        "amounts",
        []
    )

    authorities = extracted_data.get(
        "authority_names",
        []
    )

    scam_type = extracted_data.get(
        "scam_type",
        ""
    ).lower().strip()

    summary = extracted_data.get(
        "summary",
        ""
    ).lower()

    raw_text = raw_text or ""

    combined_text = (
        f"{raw_text.lower()} "
        f"{scam_type} "
        f"{summary}"
    )


    # ========================================================
    # 1. HARD EVIDENCE
    # ========================================================

    if phones:

        score += 10

        reasons.append(
            "A phone number was identified in the evidence."
        )


    if upis:

        score += 20

        reasons.append(
            "A UPI/payment destination was identified."
        )


    if urls:

        score += 15

        reasons.append(
            "A URL was identified in the suspicious content."
        )


    if amounts:

        score += 15

        reasons.append(
            "A financial amount or payment demand was identified."
        )


    if authorities:

        score += 15

        reasons.append(
            "The message references or impersonates an authority."
        )


    # ========================================================
    # 2. BEHAVIOURAL EVIDENCE
    # ========================================================

    if contains_any(
        combined_text,
        DIGITAL_ARREST_KEYWORDS
    ):

        score += 20

        reasons.append(
            "Digital-arrest or law-enforcement pressure indicators detected."
        )


    if contains_any(
        combined_text,
        BANKING_FRAUD_KEYWORDS
    ):

        score += 15

        reasons.append(
            "Banking/KYC verification indicators detected."
        )


    if contains_any(
        combined_text,
        PAYMENT_KEYWORDS
    ):

        score += 10

        reasons.append(
            "Payment-request language detected."
        )


    if contains_any(
        combined_text,
        URGENCY_KEYWORDS
    ):

        score += 10

        reasons.append(
            "Urgency or time-pressure language detected."
        )


    if contains_any(
        combined_text,
        THREAT_KEYWORDS
    ):

        score += 15

        reasons.append(
            "Threat or coercion language detected."
        )


    # ========================================================
    # 3. HISTORICAL DATABASE EVIDENCE
    # ========================================================

    connections = connections or []

    if connections:

        strongest_connection = max(
            connections,
            key=lambda x: x.get(
                "connection_score",
                0
            )
        )

        strongest_score = strongest_connection.get(
            "connection_score",
            0
        )

        if strongest_score >= 80:

            score += 25

            reasons.append(
                "Strong evidence links this complaint to a previously reported scam pattern."
            )

        elif strongest_score >= 50:

            score += 15

            reasons.append(
                "The complaint shares important identifiers with previous scam reports."
            )

        elif strongest_score >= 20:

            score += 8

            reasons.append(
                "Some evidence overlaps with previously reported complaints."
            )


        # ----------------------------------------------------
        # Repeated occurrence evidence
        # ----------------------------------------------------

        max_occurrences = max(
            (
                c.get(
                    "occurrence_count",
                    1
                )
                for c in connections
            ),
            default=1
        )

        if max_occurrences >= 5:

            score += 15

            reasons.append(
                f"This scam pattern has been reported repeatedly ({max_occurrences} occurrences)."
            )

        elif max_occurrences >= 3:

            score += 10

            reasons.append(
                f"This scam pattern has appeared {max_occurrences} times in the database."
            )


    # ========================================================
    # 4. SCORE CAP
    # ========================================================

    score = min(
        score,
        100
    )


    # ========================================================
    # 5. SEVERITY
    # ========================================================

    if score >= 80:

        severity = "CRITICAL"

    elif score >= 60:

        severity = "HIGH"

    elif score >= 40:

        severity = "MEDIUM"

    else:

        severity = "LOW"


    # ========================================================
    # 6. VERDICT
    # ========================================================

    if score >= 60:

        verdict = "POTENTIALLY A SCAM"

    elif score >= 40:

        verdict = "SUSPICIOUS"

    else:

        verdict = "LOW RISK"


    # ========================================================
    # 7. DATABASE STORAGE DECISION
    # ========================================================

    # Only suspicious/high-risk complaints enter the
    # persistent intelligence database.

    should_store = score >= 40


    return {

        "risk_score": score,

        "severity": severity,

        "verdict": verdict,

        "should_store": should_store,

        "reasons": reasons,

        "evidence_summary": {

            "phones": len(phones),

            "upi_ids": len(upis),

            "urls": len(urls),

            "amounts": len(amounts),

            "authorities": len(authorities),

            "historical_connections": len(
                connections
            )
        }
    }