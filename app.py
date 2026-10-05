import os
import tempfile

import streamlit as st

from utils.db import (
    init_db,
    save_or_increment_complaint
)

from utils.ocr import extract_text_from_image

from agents.extraction_agent import extract_entities
from agents.risk_agent import calculate_risk
from agents.cluster_agent import find_connections
from agents.graph_agent import build_graph, visualize_graph
from agents.copilot_agent import ask_copilot


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ScamSphere AI",
    page_icon="🛡️",
    layout="wide"
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

try:
    init_db()
except Exception as e:
    st.error("Could not connect to the ScamSphere database.")
    st.caption(str(e))
    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

if "extracted" not in st.session_state:
    st.session_state.extracted = None

if "risk" not in st.session_state:
    st.session_state.risk = None

if "connections" not in st.session_state:
    st.session_state.connections = []

if "complaint_text" not in st.session_state:
    st.session_state.complaint_text = ""

if "stored" not in st.session_state:
    st.session_state.stored = False

if "occurrence_count" not in st.session_state:
    st.session_state.occurrence_count = None


# ============================================================
# HEADER
# ============================================================

st.title("🛡️ ScamSphere AI")
st.subheader("Fraud Campaign Intelligence Platform")

st.caption(
    "Analyze suspicious messages, identify evidence, "
    "detect links to previous scam campaigns, and visualize "
    "fraud networks."
)


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3 = st.tabs([
    "🔍 Complaint Analysis",
    "🕸️ Fraud Network",
    "🤖 AI Copilot"
])


# ============================================================
# TAB 1 — COMPLAINT ANALYSIS
# ============================================================

with tab1:

    st.header("Analyze Suspicious Content")

    st.write(
        "Paste a suspicious message or upload a screenshot. "
        "ScamSphere extracts structured evidence and checks it "
        "against previously identified scam patterns."
    )

    complaint_input = st.text_area(
        "Suspicious message",
        height=150,
        placeholder=(
            "Example: Your bank account will be blocked. "
            "Contact this officer immediately and transfer ₹50,000..."
        )
    )

    uploaded_file = st.file_uploader(
        "Or upload a screenshot",
        type=["png", "jpg", "jpeg"]
    )

    analyze_button = st.button(
        "🔎 Analyze Complaint",
        type="primary",
        use_container_width=True
    )


    # ========================================================
    # ANALYSIS PIPELINE
    # ========================================================

    if analyze_button:

        if not complaint_input.strip() and not uploaded_file:

            st.warning(
                "Please enter a suspicious message or upload a screenshot."
            )

        else:

            complaint_text = complaint_input.strip()


            # ------------------------------------------------
            # OCR
            # ------------------------------------------------

            if uploaded_file:

                file_extension = (
                    uploaded_file.name.split(".")[-1]
                )

                temp_path = None

                try:

                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=f".{file_extension}"
                    ) as temp_file:

                        temp_file.write(
                            uploaded_file.getbuffer()
                        )

                        temp_path = temp_file.name


                    with st.spinner(
                        "Extracting text from screenshot..."
                    ):

                        complaint_text = extract_text_from_image(
                            temp_path
                        )

                    st.success(
                        "Screenshot processed successfully."
                    )

                finally:

                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)


            if not complaint_text.strip():

                st.error(
                    "No readable text was found in the input."
                )
                st.stop()


            # ------------------------------------------------
            # SAVE RAW TEXT IN SESSION
            # ------------------------------------------------

            st.session_state.complaint_text = complaint_text


            # ------------------------------------------------
            # ENTITY EXTRACTION
            # ------------------------------------------------

            with st.spinner(
                "Extracting threat intelligence..."
            ):

                extracted = extract_entities(
                    complaint_text
                )


            # ------------------------------------------------
            # DETERMINISTIC RISK ANALYSIS
            # ------------------------------------------------
            #
            # IMPORTANT:
            # The risk score is NOT generated by the LLM.
            #
            # The LLM only extracts structured evidence.
            #
            # risk_agent.py calculates the score using:
            # phones, UPI IDs, URLs, amounts, authorities,
            # scam language, urgency, threats, etc.
            # ------------------------------------------------

            with st.spinner(
                "Calculating evidence-based risk..."
            ):

                risk = calculate_risk(
                    extracted,
                    complaint_text
                )


            # ------------------------------------------------
            # DATABASE / CAMPAIGN LOOKUP
            # ------------------------------------------------
            #
            # IMPORTANT:
            # We check the existing database BEFORE inserting
            # the current complaint.
            #
            # Therefore connections represent links to
            # previously stored high-risk scam patterns.
            # ------------------------------------------------

            with st.spinner(
                "Checking previous scam campaigns..."
            ):

                connections = find_connections(
                    extracted
                )


            # ------------------------------------------------
            # SAVE ONLY HIGH-RISK CASES
            # ------------------------------------------------
            #
            # Low-risk / ordinary messages are NOT added to
            # the fraud intelligence database.
            #
            # HIGH + CRITICAL cases become intelligence.
            # ------------------------------------------------

            should_store = risk["severity"] in [
                "HIGH",
                "CRITICAL"
            ]

            occurrence_count = None

            if should_store:

                with st.spinner(
                    "Updating fraud intelligence database..."
                ):

                    occurrence_count = (
                        save_or_increment_complaint(
                            extracted,
                            risk,
                            complaint_text
                        )
                    )

                st.session_state.stored = True
                st.session_state.occurrence_count = (
                    occurrence_count
                )

            else:

                st.session_state.stored = False
                st.session_state.occurrence_count = None


            # ------------------------------------------------
            # UPDATE SESSION STATE
            # ------------------------------------------------

            st.session_state.extracted = extracted
            st.session_state.risk = risk
            st.session_state.connections = connections


    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    if st.session_state.extracted:

        extracted = st.session_state.extracted
        risk = st.session_state.risk
        connections = st.session_state.connections


        # ====================================================
        # VERDICT
        # ====================================================

        st.divider()

        st.header("🚨 Threat Assessment")


        score = risk["risk_score"]
        severity = risk["severity"]


        # Friendly verdict for everyone
        if severity == "CRITICAL":

            verdict = "🚨 HIGHLY LIKELY SCAM"
            verdict_help = (
                "Strong evidence indicates that this message "
                "is associated with fraudulent activity."
            )

        elif severity == "HIGH":

            verdict = "⚠️ POTENTIAL SCAM"
            verdict_help = (
                "Multiple scam indicators were detected. "
                "Treat this message as suspicious."
            )

        elif severity == "MEDIUM":

            verdict = "🟠 SUSPICIOUS"
            verdict_help = (
                "Some suspicious characteristics were found, "
                "but the evidence is not strong enough to "
                "classify it as a likely scam."
            )

        else:

            verdict = "🟢 LOW RISK"
            verdict_help = (
                "Few known scam indicators were detected. "
                "Still remain cautious with unexpected requests."
            )


        st.subheader(verdict)

        st.write(verdict_help)


        # ====================================================
        # SCORE DISPLAY
        # ====================================================

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Risk Score",
                f"{score}/100"
            )

        with col2:

            st.metric(
                "Severity",
                severity
            )

        with col3:

            st.metric(
                "Campaign Links",
                len(connections)
            )


        st.progress(
            score / 100
        )


        # ====================================================
        # WHAT SHOULD THE USER DO?
        # ====================================================

        if severity in ["HIGH", "CRITICAL"]:

            st.error(
                "🛑 Recommended action: "
                "Do not send money, share OTPs/passwords, "
                "or follow payment instructions."
            )

            st.info(
                "If this appears to be a real scam, preserve "
                "the original message/screenshot and report it "
                "to the appropriate cybercrime authorities."
            )

        elif severity == "MEDIUM":

            st.warning(
                "⚠️ Be cautious. Verify the sender independently "
                "before taking any action."
            )

        else:

            st.success(
                "No strong scam indicators were detected. "
                "However, never share sensitive information "
                "with unknown senders."
            )


        # ====================================================
        # DATABASE STATUS
        # ====================================================

        if st.session_state.stored:

            count = st.session_state.occurrence_count

            st.success(
                f"📊 This scam pattern is now in the "
                f"fraud intelligence database. "
                f"Observed {count} time(s)."
            )

            if count and count > 1:

                st.warning(
                    f"🔁 This evidence pattern has appeared "
                    f"{count} times. Repeated targeting may "
                    f"indicate an active scam campaign."
                )

        else:

            st.caption(
                "This case was not added to the campaign database "
                "because its risk level did not meet the intelligence "
                "storage threshold."
            )


        # ====================================================
        # EXTRACTED TEXT
        # ====================================================

        with st.expander(
            "📄 View analyzed message"
        ):

            st.write(
                st.session_state.complaint_text
            )


        # ====================================================
        # THREAT INTELLIGENCE
        # ====================================================

        st.divider()

        st.header("🎯 Extracted Threat Intelligence")


        col1, col2 = st.columns(2)


        with col1:

            st.write(
                f"**Scam Type:** "
                f"{extracted.get('scam_type', 'Unknown')}"
            )

            st.write(
                "**Phone Numbers:**"
            )

            phones = extracted.get(
                "phone_numbers",
                []
            )

            if phones:
                for phone in phones:
                    st.code(phone)
            else:
                st.caption("None detected")


            st.write(
                "**UPI IDs:**"
            )

            upis = extracted.get(
                "upi_ids",
                []
            )

            if upis:
                for upi in upis:
                    st.code(upi)
            else:
                st.caption("None detected")


            st.write(
                "**URLs:**"
            )

            urls = extracted.get(
                "urls",
                []
            )

            if urls:
                for url in urls:
                    st.code(url)
            else:
                st.caption("None detected")


        with col2:

            st.write(
                "**Authorities Mentioned:**"
            )

            authorities = extracted.get(
                "authority_names",
                []
            )

            if authorities:
                for authority in authorities:
                    st.write(f"• {authority}")
            else:
                st.caption("None detected")


            st.write(
                "**Amounts:**"
            )

            amounts = extracted.get(
                "amounts",
                []
            )

            if amounts:
                for amount in amounts:
                    st.write(f"• {amount}")
            else:
                st.caption("None detected")


            st.write(
                "**Summary:**"
            )

            st.write(
                extracted.get(
                    "summary",
                    "No summary available."
                )
            )


        # ====================================================
        # RISK REASONS
        # ====================================================

        st.divider()

        st.header("🧠 Why was this score given?")


        st.write(
            "The score is calculated from observable evidence "
            "and predefined fraud indicators — not directly "
            "generated by the language model."
        )


        for reason in risk.get(
            "reasons",
            []
        ):

            st.success(
                f"✓ {reason}"
            )


        # ====================================================
        # CAMPAIGN CONNECTIONS
        # ====================================================

        st.divider()

        st.header("🕸️ Campaign Intelligence")


        if connections:

            st.error(
                f"Found {len(connections)} connection(s) "
                "to previously identified scam patterns."
            )


            for connection in connections[:10]:

                with st.expander(
                    f"{connection['complaint_id']} — "
                    f"{connection['connection_score']}% connection"
                ):

                    st.write(
                        f"**Scam Type:** "
                        f"{connection.get('scam_type', 'Unknown')}"
                    )

                    st.write(
                        f"**Previous Risk:** "
                        f"{connection.get('risk_score', 0)}/100"
                    )

                    st.write(
                        f"**Severity:** "
                        f"{connection.get('severity', 'Unknown')}"
                    )

                    st.write(
                        f"**Observed:** "
                        f"{connection.get('occurrence_count', 1)} time(s)"
                    )

                    st.write(
                        "**Shared evidence:**"
                    )

                    for entity in connection.get(
                        "matching_entities",
                        []
                    ):

                        st.write(
                            f"• {entity}"
                        )

                    st.write(
                        f"**First seen:** "
                        f"{connection.get('first_seen', 'Unknown')}"
                    )

                    st.write(
                        f"**Last seen:** "
                        f"{connection.get('last_seen', 'Unknown')}"
                    )

        else:

            st.success(
                "No meaningful links to previously stored "
                "high-risk scam patterns were found."
            )


# ============================================================
# TAB 2 — FRAUD NETWORK
# ============================================================

with tab2:

    st.header("🕸️ Fraud Evidence Network")

    st.write(
        "This graph shows how the current complaint is connected "
        "to previously identified scam cases through shared "
        "evidence such as phone numbers, UPI IDs and URLs."
    )


    if st.session_state.extracted:

        graph = build_graph(
            st.session_state.extracted,
            st.session_state.connections
        )


        if len(graph.nodes) > 1:

            fig = visualize_graph(
                graph
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


            st.caption(
                "Connections are based on shared structured evidence "
                "retrieved from the fraud intelligence database."
            )

        else:

            st.info(
                "Not enough linked evidence exists yet to build "
                "a meaningful network."
            )

    else:

        st.info(
            "Analyze a complaint first to generate its evidence network."
        )


# ============================================================
# TAB 3 — AI COPILOT
# ============================================================

with tab3:

    st.header("🤖 AI Cybercrime Copilot")

    st.write(
        "Ask questions about the currently analyzed complaint, "
        "its evidence, risk assessment and campaign connections."
    )


    if not st.session_state.extracted:

        st.info(
            "Analyze a complaint first, then ask the Copilot "
            "about the investigation."
        )

    else:

        question = st.text_area(
            "Ask the Copilot",
            placeholder=(
                "Example: Why is this complaint considered high risk?"
            ),
            height=100
        )


        if st.button(
            "💬 Ask Copilot",
            type="primary"
        ):

            if not question.strip():

                st.warning(
                    "Please enter a question."
                )

            else:

                # --------------------------------------------
                # Give Copilot ONLY actual application evidence
                # --------------------------------------------

                context = f"""
CURRENT COMPLAINT
-----------------
{st.session_state.complaint_text}


EXTRACTED EVIDENCE
------------------
{st.session_state.extracted}


DETERMINISTIC RISK ASSESSMENT
-----------------------------
{st.session_state.risk}


DATABASE CAMPAIGN CONNECTIONS
-----------------------------
{st.session_state.connections}
"""


                with st.spinner(
                    "Analyzing investigation evidence..."
                ):

                    answer = ask_copilot(
                        question,
                        context
                    )


                st.subheader(
                    "Copilot Response"
                )

                st.write(
                    answer
                )