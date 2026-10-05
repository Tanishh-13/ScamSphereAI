import os
import hashlib
import psycopg2

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return psycopg2.connect(DATABASE_URL)


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
    #
    # CREATE TABLE IF NOT EXISTS does not modify an existing
    # table. These ALTER statements make older databases
    # compatible with the final schema.
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

    Therefore, differently worded complaints containing the same
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

    """
    Store a suspicious complaint.

    If the exact evidence fingerprint already exists,
    increment occurrence_count instead of creating
    another duplicate row.

    Returns:
        occurrence_count
    """

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
        current_count = existing[1] or 1

        new_count = current_count + 1

        cur.execute("""
            UPDATE complaints
            SET
                occurrence_count = %s,
                last_seen = CURRENT_TIMESTAMP,
                risk_score = %s,
                severity = %s
            WHERE id = %s
        """, (
            new_count,

            risk.get(
                "risk_score",
                0
            ),

            risk.get(
                "severity",
                "LOW"
            ),

            complaint_id
        ))

        conn.commit()

        cur.close()
        conn.close()

        # IMPORTANT:
        # Return ONLY the count because app.py expects
        # saved_count to be an integer.
        return new_count

    # ========================================================
    # NEW EVIDENCE PATTERN
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
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )

        RETURNING id
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

    cur.fetchone()

    conn.commit()

    cur.close()
    conn.close()

    # IMPORTANT:
    # First occurrence = 1.
    return 1


# ============================================================
# FETCH ALL COMPLAINTS
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

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows