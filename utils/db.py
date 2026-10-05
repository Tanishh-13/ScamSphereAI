import os
import hashlib
import psycopg2

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# DATABASE URL
# ============================================================

def get_database_url():
    """
    Get DATABASE_URL in a way that works both locally
    and on Streamlit Cloud.

    Priority:
        1. Streamlit secrets
        2. Environment variable / .env
    """

    # Streamlit Cloud
    try:
        import streamlit as st

        database_url = st.secrets.get("DATABASE_URL")

        if database_url:
            return str(database_url).strip()

    except Exception:
        # Streamlit is unavailable when running outside Streamlit
        pass

    # Local development / .env
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return database_url.strip()

    raise RuntimeError(
        "DATABASE_URL is not configured. "
        "Add DATABASE_URL to Streamlit Secrets or your local .env file."
    )


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    database_url = get_database_url()

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is empty."
        )

    # Prevent the confusing localhost PostgreSQL fallback.
    if database_url.startswith("postgresql://") or \
       database_url.startswith("postgres://"):

        return psycopg2.connect(
            database_url,
            sslmode="require",
            connect_timeout=15
        )

    raise RuntimeError(
        "DATABASE_URL does not appear to be a valid PostgreSQL URL."
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    conn = get_connection()
    cur = conn.cursor()

    # Create the complete complaints table if it does not exist.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS complaints (

            id SERIAL PRIMARY KEY,

            complaint_text TEXT NOT NULL,

            scam_type TEXT,
            risk_score INTEGER,
            severity TEXT,

            phone_numbers TEXT[],
            upi_ids TEXT[],
            urls TEXT[],
            authority_names TEXT[],
            amounts TEXT[],

            summary TEXT,

            fingerprint TEXT UNIQUE,

            occurrence_count INTEGER DEFAULT 1,

            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ========================================================
    # MIGRATION SAFETY
    # ========================================================

    cur.execute("""
        ALTER TABLE complaints
        ADD COLUMN IF NOT EXISTS complaint_text TEXT
    """)

    cur.execute("""
        ALTER TABLE complaints
        ADD COLUMN IF NOT EXISTS scam_type TEXT
    """)

    cur.execute("""
        ALTER TABLE complaints
        ADD COLUMN IF NOT EXISTS risk_score INTEGER
    """)

    cur.execute("""
        ALTER TABLE complaints
        ADD COLUMN IF NOT EXISTS severity TEXT
    """)

    cur.execute("""
        ALTER TABLE complaints
        ADD COLUMN IF NOT EXISTS phone_numbers TEXT[]
    """)

    cur.execute("""
        ALTER TABLE complaints
        ADD COLUMN IF NOT EXISTS upi_ids TEXT[]
    """)

    cur.execute("""
        ALTER TABLE complaints
        ADD COLUMN IF NOT EXISTS urls TEXT[]
    """)

    cur.execute("""
        ALTER TABLE complaints
        ADD COLUMN IF NOT EXISTS authority_names TEXT[]
    """)

    cur.execute("""
        ALTER TABLE complaints
        ADD COLUMN IF NOT EXISTS amounts TEXT[]
    """)

    cur.execute("""
        ALTER TABLE complaints
        ADD COLUMN IF NOT EXISTS summary TEXT
    """)

    cur.execute("""
        ALTER TABLE complaints
        ADD COLUMN IF NOT EXISTS fingerprint TEXT
    """)

    cur.execute("""
        ALTER TABLE complaints
        ADD COLUMN IF NOT EXISTS occurrence_count INTEGER
        DEFAULT 1
    """)

    cur.execute("""
        ALTER TABLE complaints
        ADD COLUMN IF NOT EXISTS first_seen TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP
    """)

    cur.execute("""
        ALTER TABLE complaints
        ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP
    """)

    cur.execute("""
        ALTER TABLE complaints
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP
    """)

    # ========================================================
    # FIX NULL VALUES FROM OLD SCHEMA
    # ========================================================

    cur.execute("""
        UPDATE complaints
        SET occurrence_count = 1
        WHERE occurrence_count IS NULL
    """)

    cur.execute("""
        UPDATE complaints
        SET first_seen = CURRENT_TIMESTAMP
        WHERE first_seen IS NULL
    """)

    cur.execute("""
        UPDATE complaints
        SET last_seen = CURRENT_TIMESTAMP
        WHERE last_seen IS NULL
    """)

    cur.execute("""
        UPDATE complaints
        SET created_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL
    """)

    # ========================================================
    # INDEXES
    # ========================================================

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_complaints_last_seen
        ON complaints(last_seen)
    """)

    conn.commit()

    cur.close()
    conn.close()


# ============================================================
# EVIDENCE FINGERPRINT
# ============================================================

def generate_fingerprint(extracted):

    """
    Creates a deterministic fingerprint from structured evidence.

    Raw complaint text is intentionally NOT used.

    Therefore differently worded complaints containing the same
    core evidence can be recognized as the same scam pattern.
    """

    phones = sorted(
        set(
            extracted.get(
                "phone_numbers",
                []
            )
        )
    )

    upis = sorted(
        set(
            extracted.get(
                "upi_ids",
                []
            )
        )
    )

    urls = sorted(
        set(
            extracted.get(
                "urls",
                []
            )
        )
    )

    authorities = sorted(
        set(
            x.lower().strip()
            for x in extracted.get(
                "authority_names",
                []
            )
        )
    )

    scam_type = (
        extracted.get(
            "scam_type",
            ""
        )
        .lower()
        .strip()
    )

    evidence = "|".join([
        "phones:" + ",".join(phones),
        "upis:" + ",".join(upis),
        "urls:" + ",".join(urls),
        "authorities:" + ",".join(authorities),
        "scam_type:" + scam_type
    ])

    return hashlib.sha256(
        evidence.encode("utf-8")
    ).hexdigest()


# ============================================================
# SAVE OR INCREMENT COMPLAINT
# ============================================================

def save_or_increment_complaint(
    extracted,
    risk,
    complaint_text
):

    fingerprint = generate_fingerprint(
        extracted
    )

    conn = get_connection()
    cur = conn.cursor()

    # ========================================================
    # CHECK FOR EXISTING EVIDENCE PATTERN
    # ========================================================

    cur.execute("""
        SELECT
            id,
            occurrence_count
        FROM complaints
        WHERE fingerprint = %s
    """, (
        fingerprint,
    ))

    existing = cur.fetchone()

    # ========================================================
    # EXISTING PATTERN
    # ========================================================

    if existing:

        complaint_id = existing[0]
        occurrence_count = existing[1] or 1

        occurrence_count += 1

        cur.execute("""
            UPDATE complaints

            SET
                occurrence_count = %s,
                last_seen = CURRENT_TIMESTAMP,
                risk_score = %s,
                severity = %s

            WHERE id = %s

            RETURNING occurrence_count
        """, (
            occurrence_count,
            risk.get("risk_score", 0),
            risk.get("severity", "LOW"),
            complaint_id
        ))

        result = cur.fetchone()

        conn.commit()

        cur.close()
        conn.close()

        return result[0] if result else occurrence_count

    # ========================================================
    # NEW PATTERN
    # ========================================================

    cur.execute("""
        INSERT INTO complaints (

            complaint_text,
            scam_type,
            risk_score,
            severity,

            phone_numbers,
            upi_ids,
            urls,
            authority_names,
            amounts,

            summary,
            fingerprint,

            occurrence_count,
            first_seen,
            last_seen

        )

        VALUES (

            %s,
            %s,
            %s,
            %s,

            %s,
            %s,
            %s,
            %s,
            %s,

            %s,
            %s,

            1,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP

        )

        RETURNING occurrence_count
    """, (

        complaint_text,

        extracted.get(
            "scam_type",
            ""
        ),

        risk.get(
            "risk_score",
            0
        ),

        risk.get(
            "severity",
            "LOW"
        ),

        extracted.get(
            "phone_numbers",
            []
        ),

        extracted.get(
            "upi_ids",
            []
        ),

        extracted.get(
            "urls",
            []
        ),

        extracted.get(
            "authority_names",
            []
        ),

        extracted.get(
            "amounts",
            []
        ),

        extracted.get(
            "summary",
            ""
        ),

        fingerprint
    ))

    result = cur.fetchone()

    conn.commit()

    cur.close()
    conn.close()

    return result[0] if result else 1


# ============================================================
# GET ALL COMPLAINTS
# ============================================================

def get_all_complaints():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            complaint_text,
            scam_type,
            risk_score,
            severity,
            phone_numbers,
            upi_ids,
            urls,
            authority_names,
            amounts,
            summary,
            fingerprint,
            occurrence_count,
            first_seen,
            last_seen,
            created_at

        FROM complaints

        ORDER BY last_seen DESC
    """)

    complaints = cur.fetchall()

    cur.close()
    conn.close()

    return complaints