from utils.db import get_all_complaints


def find_connections(extracted_data):

    complaints = get_all_complaints()

    connections = []

    # =========================================================
    # CURRENT COMPLAINT EVIDENCE
    # =========================================================

    current_phones = set(
        extracted_data.get(
            "phone_numbers",
            []
        )
    )

    current_upis = set(
        extracted_data.get(
            "upi_ids",
            []
        )
    )

    current_urls = set(
        extracted_data.get(
            "urls",
            []
        )
    )

    current_authorities = set(
        x.lower().strip()
        for x in extracted_data.get(
            "authority_names",
            []
        )
    )

    current_scam_type = (
        extracted_data.get(
            "scam_type",
            ""
        )
        .lower()
        .strip()
    )

    # =========================================================
    # COMPARE AGAINST DATABASE
    # =========================================================

    for complaint in complaints:

        (
            complaint_id,
            complaint_text,
            scam_type,
            risk_score,
            severity,
            phones,
            upis,
            urls,
            authorities,
            amounts,
            summary,
            fingerprint,
            occurrence_count,
            first_seen,
            last_seen,
            created_at
        ) = complaint

        complaint_phones = set(
            phones or []
        )

        complaint_upis = set(
            upis or []
        )

        complaint_urls = set(
            urls or []
        )

        complaint_authorities = set(
            x.lower().strip()
            for x in (authorities or [])
        )

        # =====================================================
        # SHARED EVIDENCE
        # =====================================================

        shared_phones = (
            current_phones &
            complaint_phones
        )

        shared_upis = (
            current_upis &
            complaint_upis
        )

        shared_urls = (
            current_urls &
            complaint_urls
        )

        shared_authorities = (
            current_authorities &
            complaint_authorities
        )

        matching_entities = []

        if shared_phones:
            matching_entities.append("phone")

        if shared_upis:
            matching_entities.append("upi")

        if shared_urls:
            matching_entities.append("url")

        if shared_authorities:
            matching_entities.append("authority")

        # =====================================================
        # CONNECTION SCORE
        # =====================================================

        connection_score = 0

        # Strong identifiers
        if shared_phones:
            connection_score += 50

        if shared_upis:
            connection_score += 50

        if shared_urls:
            connection_score += 40

        # Supporting evidence
        if shared_authorities:
            connection_score += 10

        # Same scam category
        if (
            current_scam_type
            and scam_type
            and current_scam_type
            == scam_type.lower().strip()
        ):
            connection_score += 15

            if "scam_type" not in matching_entities:
                matching_entities.append(
                    "scam_type"
                )

        # =====================================================
        # CAMPAIGN STRENGTH
        # =====================================================

        occurrence_count = (
            occurrence_count or 1
        )

        # Repeated reports strengthen the significance
        # of the connected campaign, but only slightly.
        repetition_bonus = min(
            occurrence_count * 2,
            10
        )

        connection_score += repetition_bonus

        connection_score = min(
            connection_score,
            100
        )

        # =====================================================
        # KEEP ONLY REAL CONNECTIONS
        # =====================================================

        if connection_score < 20:
            continue

        # =====================================================
        # CONNECTION TYPE
        # =====================================================

        if (
            shared_phones
            or shared_upis
            or shared_urls
        ):
            connection_type = "STRONG"

        elif (
            shared_authorities
            or "scam_type" in matching_entities
        ):
            connection_type = "SUPPORTING"

        else:
            connection_type = "WEAK"

        # =====================================================
        # HUMAN-READABLE EXPLANATION
        # =====================================================

        evidence_parts = []

        if shared_phones:
            evidence_parts.append(
                f"{len(shared_phones)} shared phone number(s)"
            )

        if shared_upis:
            evidence_parts.append(
                f"{len(shared_upis)} shared UPI ID(s)"
            )

        if shared_urls:
            evidence_parts.append(
                f"{len(shared_urls)} shared URL(s)"
            )

        if shared_authorities:
            evidence_parts.append(
                f"{len(shared_authorities)} shared authority indicator(s)"
            )

        if "scam_type" in matching_entities:
            evidence_parts.append(
                "same scam category"
            )

        evidence_explanation = ", ".join(
            evidence_parts
        )

        # =====================================================
        # STORE CONNECTION
        # =====================================================

        connections.append({

            "complaint_id":
                f"Case #{complaint_id}",

            "db_id":
                complaint_id,

            "complaint_text":
                complaint_text,

            "scam_type":
                scam_type,

            "risk_score":
                risk_score,

            "severity":
                severity,

            "phone_numbers":
                phones or [],

            "upi_ids":
                upis or [],

            "urls":
                urls or [],

            "authority_names":
                authorities or [],

            "amounts":
                amounts or [],

            "summary":
                summary,

            "occurrence_count":
                occurrence_count,

            "fingerprint":
                fingerprint,

            "first_seen":
                str(first_seen),

            "last_seen":
                str(last_seen),

            "created_at":
                str(created_at),

            "matching_entities":
                matching_entities,

            "connection_score":
                connection_score,

            "connection_type":
                connection_type,

            "evidence_explanation":
                evidence_explanation
        })

    # =========================================================
    # STRONGEST CONNECTIONS FIRST
    # =========================================================

    connections.sort(
        key=lambda x:
            (
                x["connection_score"],
                x["occurrence_count"]
            ),
        reverse=True
    )

    return connections