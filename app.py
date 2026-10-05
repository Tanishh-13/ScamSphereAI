import os
import tempfile
import streamlit as st
from utils.ocr import extract_text_from_image
from utils.db import (
    init_db,
    save_or_increment_complaint
)
from agents.extraction_agent import extract_entities
from agents.risk_agent import calculate_risk
from agents.cluster_agent import find_connections
from agents.graph_agent import (
    build_graph,
    visualize_graph
)
from agents.copilot_agent import ask_copilot


# ============================================================
# PAGE CONFIGURATION
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
    database_ready = True
except Exception as e:
    database_ready = False
    db_error = str(e)


# ============================================================
# SESSION STATE
# ============================================================

if "analysis" not in st.session_state:
    st.session_state.analysis = None

if "complaint_text" not in st.session_state:
    st.session_state.complaint_text = ""

if "copilot_answer" not in st.session_state:
    st.session_state.copilot_answer = None

if "saved_count" not in st.session_state:
    st.session_state.saved_count = None


# ============================================================
# HEADER
# ============================================================

st.title("🛡️ ScamSphere AI")
st.subheader(
    "Fraud Campaign Intelligence Platform"
)

st.caption(
    "Evidence-driven scam detection using structured evidence, "
    "historical complaint data, and fraud-network analysis."
)


if not database_ready:

    st.error(
        "⚠️ Database connection failed."
    )

    st.code(
        db_error
    )

    st.info(
        "Check your DATABASE_URL and PostgreSQL connection "
        "before continuing."
    )

    st.stop()


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3 = st.tabs(
    [
        "🔎 Complaint Analysis",
        "🕸️ Fraud Network",
        "🤖 AI Copilot"
    ]
)


# ============================================================
# TAB 1 — COMPLAINT ANALYSIS
# ============================================================

with tab1:

    st.header(
        "🔎 Analyze Suspicious Content"
    )

    st.write(
        "Paste a suspicious message or upload a screenshot. "
        "ScamSphere extracts evidence, checks it against "
        "previously reported cases, and calculates a "
        "deterministic risk score."
    )

    complaint_input = st.text_area(
        "Suspicious message",
        height=180,
        placeholder=(
            "Example:\n"
            "This is a message from CBI. Your bank account "
            "will be blocked unless you pay ₹25,000 immediately..."
        )
    )

    uploaded_file = st.file_uploader(
        "Or upload a screenshot",
        type=[
            "png",
            "jpg",
            "jpeg"
        ]
    )

    analyze_button = st.button(
        "🔍 Analyze Complaint",
        type="primary",
        use_container_width=True
    )


    # ========================================================
    # ANALYSIS PIPELINE
    # ========================================================

    if analyze_button:

        complaint = complaint_input.strip()


        # ----------------------------------------------------
        # OCR
        # ----------------------------------------------------

        if uploaded_file:

            try:

                file_extension = (
                    uploaded_file.name
                    .split(".")[-1]
                    .lower()
                )

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=f".{file_extension}"
                ) as temp_file:

                    temp_file.write(
                        uploaded_file.getbuffer()
                    )

                    temp_path = temp_file.name


                with st.spinner(
                    "Reading screenshot..."
                ):

                    complaint = extract_text_from_image(
                        temp_path
                    )


                try:
                    os.remove(temp_path)
                except OSError:
                    pass


                if complaint:

                    st.success(
                        "Screenshot processed successfully."
                    )

                    with st.expander(
                        "📄 View extracted text"
                    ):

                        st.write(
                            complaint
                        )

                else:

                    st.error(
                        "Could not extract readable text "
                        "from the screenshot."
                    )

                    st.stop()


            except Exception as e:

                st.error(
                    "OCR processing failed."
                )

                st.exception(e)

                st.stop()


        # ----------------------------------------------------
        # Validate input
        # ----------------------------------------------------

        if not complaint:

            st.warning(
                "Please enter a suspicious message "
                "or upload a screenshot."
            )

            st.stop()


        # ----------------------------------------------------
        # COMPLETE INTELLIGENCE PIPELINE
        # ----------------------------------------------------

        try:

            with st.spinner(
                "Analyzing evidence and historical cases..."
            ):

                # ============================================
                # STEP 1 — LLM EXTRACTION
                # ============================================

                extracted = extract_entities(
                    complaint
                )


                # ============================================
                # STEP 2 — DATABASE / HISTORICAL EVIDENCE
                # ============================================

                connections = find_connections(
                    extracted
                )


                # ============================================
                # STEP 3 — DETERMINISTIC RISK ENGINE
                #
                # IMPORTANT:
                # The LLM does NOT generate the risk score.
                #
                # Risk is calculated from:
                # - extracted evidence
                # - raw complaint text
                # - historical DB connections
                # - occurrence frequency
                # ============================================

                risk = calculate_risk(
                    extracted_data=extracted,
                    raw_text=complaint,
                    connections=connections
                )


                # ============================================
                # STEP 4 — PERSISTENCE
                #
                # Only meaningful/suspicious complaints are
                # stored in the intelligence database.
                #
                # Existing evidence fingerprints increment
                # occurrence_count rather than creating
                # duplicate records.
                # ============================================

                saved_count = None

                if risk.get(
                    "should_store",
                    False
                ):

                    saved_count = (
                        save_or_increment_complaint(
                            extracted=extracted,
                            risk=risk,
                            complaint_text=complaint
                        )
                    )


                # ============================================
                # STEP 5 — STORE RESULT IN SESSION
                # ============================================

                st.session_state.analysis = {

                    "complaint": complaint,

                    "extracted": extracted,

                    "connections": connections,

                    "risk": risk,

                    "saved_count": saved_count

                }

                st.session_state.complaint_text = complaint

                st.session_state.saved_count = saved_count

                st.session_state.copilot_answer = None


        except Exception as e:

            st.error(
                "❌ Analysis pipeline failed."
            )

            st.exception(e)

            st.stop()


    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    analysis = st.session_state.analysis


    if analysis:

        extracted = analysis["extracted"]

        connections = analysis["connections"]

        risk = analysis["risk"]

        saved_count = analysis["saved_count"]


        # ====================================================
        # TOP VERDICT
        # ====================================================

        st.divider()

        st.subheader(
            "🚨 Scam Assessment"
        )


        score = risk.get(
            "risk_score",
            0
        )

        severity = risk.get(
            "severity",
            "LOW"
        )

        verdict = risk.get(
            "verdict",
            "LOW RISK"
        )


        if score >= 80:

            st.error(
                f"🚨 {verdict}"
            )

            st.error(
                "This complaint contains strong scam indicators "
                "and/or strong historical links to known patterns."
            )

        elif score >= 60:

            st.warning(
                f"⚠️ {verdict}"
            )

            st.warning(
                "Multiple indicators suggest that this "
                "message may be part of a fraudulent activity."
            )

        elif score >= 40:

            st.warning(
                f"⚠️ {verdict}"
            )

            st.info(
                "Some suspicious indicators were detected. "
                "Treat the message carefully and verify the "
                "sender independently."
            )

        else:

            st.success(
                f"✅ {verdict}"
            )

            st.info(
                "The current evidence does not strongly indicate "
                "a scam. Continue to exercise normal caution."
            )


        # ====================================================
        # SCORE METRICS
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
                "Historical Connections",
                len(connections)
            )


        st.progress(
            score / 100
        )


        # ====================================================
        # WHAT SHOULD THE USER DO?
        # ====================================================

        st.subheader(
            "🧭 What should you do?"
        )


        if score >= 60:

            st.error(
                """
                **Do not send money or share sensitive information.**

                • Do not share OTPs, passwords, PINs or banking details.  
                • Do not click suspicious links.  
                • Do not install software requested by the caller.  
                • Independently contact your bank or the relevant authority.  
                • Preserve screenshots, phone numbers, UPI IDs and URLs as evidence.
                """
            )

        elif score >= 40:

            st.warning(
                """
                **Be cautious before taking any action.**

                • Verify who contacted you.  
                • Do not make payments based only on the message.  
                • Avoid clicking unknown links.  
                • Keep the original message/screenshot as evidence.
                """
            )

        else:

            st.success(
                """
                **No strong scam indicators were detected.**

                Still avoid sharing sensitive information unless you
                independently trust and verify the sender.
                """
            )


        # ====================================================
        # THREAT INTELLIGENCE
        # ====================================================

        st.divider()

        st.subheader(
            "🎯 Extracted Threat Intelligence"
        )


        col1, col2 = st.columns(2)


        with col1:

            st.markdown(
                f"**Scam Type:** "
                f"{extracted.get('scam_type', 'Unknown')}"
            )

            phones = extracted.get(
                "phone_numbers",
                []
            )

            if phones:

                st.markdown(
                    "**📞 Phone Numbers:**"
                )

                for phone in phones:

                    st.code(
                        str(phone)
                    )

            else:

                st.markdown(
                    "**📞 Phone Numbers:** None identified"
                )


            upis = extracted.get(
                "upi_ids",
                []
            )

            if upis:

                st.markdown(
                    "**💳 UPI IDs:**"
                )

                for upi in upis:

                    st.code(
                        str(upi)
                    )

            else:

                st.markdown(
                    "**💳 UPI IDs:** None identified"
                )


            urls = extracted.get(
                "urls",
                []
            )

            if urls:

                st.markdown(
                    "**🔗 URLs:**"
                )

                for url in urls:

                    st.code(
                        str(url)
                    )

            else:

                st.markdown(
                    "**🔗 URLs:** None identified"
                )


        with col2:

            authorities = extracted.get(
                "authority_names",
                []
            )

            if authorities:

                st.markdown(
                    "**🏛️ Authorities Mentioned:**"
                )

                for authority in authorities:

                    st.write(
                        f"• {authority}"
                    )

            else:

                st.markdown(
                    "**🏛️ Authorities Mentioned:** None"
                )


            amounts = extracted.get(
                "amounts",
                []
            )

            if amounts:

                st.markdown(
                    "**💰 Amounts:**"
                )

                for amount in amounts:

                    st.write(
                        f"• {amount}"
                    )

            else:

                st.markdown(
                    "**💰 Amounts:** None identified"
                )


            st.markdown(
                "**📝 Summary:**"
            )

            st.write(
                extracted.get(
                    "summary",
                    "No summary available."
                )
            )


        # ====================================================
        # WHY THIS SCORE?
        # ====================================================

        st.divider()

        st.subheader(
            "🧠 Why did ScamSphere give this score?"
        )

        reasons = risk.get(
            "reasons",
            []
        )


        if reasons:

            for reason in reasons:

                st.info(
                    f"• {reason}"
                )

        else:

            st.info(
                "No specific risk indicators were triggered."
            )


        # ====================================================
        # EVIDENCE SUMMARY
        # ====================================================

        evidence_summary = risk.get(
            "evidence_summary",
            {}
        )


        if evidence_summary:

            with st.expander(
                "🔬 Evidence used by the risk engine"
            ):

                e1, e2, e3 = st.columns(3)

                with e1:

                    st.metric(
                        "Phones",
                        evidence_summary.get(
                            "phones",
                            0
                        )
                    )

                    st.metric(
                        "UPI IDs",
                        evidence_summary.get(
                            "upi_ids",
                            0
                        )
                    )

                    st.metric(
                        "URLs",
                        evidence_summary.get(
                            "urls",
                            0
                        )
                    )

                with e2:

                    st.metric(
                        "Amounts",
                        evidence_summary.get(
                            "amounts",
                            0
                        )
                    )

                    st.metric(
                        "Authorities",
                        evidence_summary.get(
                            "authorities",
                            0
                        )
                    )

                with e3:

                    st.metric(
                        "Historical Connections",
                        evidence_summary.get(
                            "historical_connections",
                            0
                        )
                    )


        # ====================================================
        # HISTORICAL INTELLIGENCE
        # ====================================================

        st.divider()

        st.subheader(
            "🗄️ Historical Intelligence"
        )


        if connections:

            st.success(
                f"Found {len(connections)} historical "
                f"connection(s) in the database."
            )


            for index, connection in enumerate(
                connections,
                start=1
            ):

                with st.expander(
                    f"Case #{connection.get('db_id')} — "
                    f"Connection strength "
                    f"{connection.get('connection_score', 0)}/100"
                ):

                    st.write(
                        f"**Scam Type:** "
                        f"{connection.get('scam_type', 'Unknown')}"
                    )

                    st.write(
                        f"**Severity:** "
                        f"{connection.get('severity', 'Unknown')}"
                    )

                    st.write(
                        f"**Historical Occurrences:** "
                        f"{connection.get('occurrence_count', 1)}"
                    )

                    st.write(
                        f"**Matching Evidence:** "
                        f"{', '.join(connection.get('matching_entities', []))}"
                    )

                    st.write(
                        f"**First Seen:** "
                        f"{connection.get('first_seen', 'Unknown')}"
                    )

                    st.write(
                        f"**Last Seen:** "
                        f"{connection.get('last_seen', 'Unknown')}"
                    )

                    st.write(
                        "**Summary:**"
                    )

                    st.write(
                        connection.get(
                            "summary",
                            ""
                        )
                    )

        else:

            st.info(
                "No matching historical complaints were found "
                "in the database."
            )


        # ====================================================
        # DATABASE STORAGE
        # ====================================================

        st.divider()

        st.subheader(
            "📊 Intelligence Database"
        )


        if risk.get(
            "should_store",
            False
        ):

            if saved_count is not None:

                st.success(
                    f"This evidence pattern is stored in the "
                    f"intelligence database. "
                    f"Current occurrence count: **{saved_count}**."
                )

                if saved_count > 1:

                    st.info(
                        "This pattern has now been reported "
                        f"{saved_count} times. ScamSphere keeps "
                        "it as one evidence pattern rather than "
                        "creating duplicate records."
                    )

        else:

            st.info(
                "This complaint did not meet the persistence "
                "threshold and was not added to the historical "
                "intelligence database."
            )


# ============================================================
# TAB 2 — FRAUD NETWORK
# ============================================================

with tab2:

    st.header(
        "🕸️ Fraud Intelligence Network"
    )

    st.write(
        "This graph shows relationships between the current "
        "complaint and evidence found in historical reports."
    )


    analysis = st.session_state.analysis


    if analysis:

        current_data = analysis["extracted"]

        connections = analysis["connections"]


        graph = build_graph(
            current_data,
            connections
        )


        fig = visualize_graph(
            graph
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


        st.divider()

        st.subheader(
            "How to read this graph"
        )

        st.markdown(
            """
            **CURRENT COMPLAINT**  
            The complaint currently being investigated.

            **Phone / UPI / URL nodes**  
            Digital identifiers extracted from the complaint.

            **Case nodes**  
            Previously reported complaints from the database.

            **Connections**  
            Shared evidence such as the same phone number,
            UPI ID, URL or other identifiers.

            A cluster of multiple cases around the same identifier
            can indicate a repeated fraud campaign.
            """
        )

    else:

        st.info(
            "Analyze a complaint first to generate "
            "the fraud intelligence network."
        )


# ============================================================
# TAB 3 — AI COPILOT
# ============================================================

with tab3:

    st.header(
        "🤖 AI Cybercrime Copilot"
    )

    st.write(
        "Ask questions about the currently analyzed case. "
        "The Copilot receives the extracted evidence, risk "
        "assessment and historical connections."
    )


    analysis = st.session_state.analysis


    if not analysis:

        st.info(
            "Analyze a complaint first."
        )

    else:

        question = st.text_input(
            "Ask the Copilot",
            placeholder=(
                "Example: Why is this complaint considered high risk?"
            )
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

                context = f"""
CURRENT COMPLAINT
{analysis["complaint"]}


EXTRACTED EVIDENCE
{analysis["extracted"]}


DETERMINISTIC RISK ASSESSMENT
{analysis["risk"]}


HISTORICAL DATABASE CONNECTIONS
{analysis["connections"]}


IMPORTANT INSTRUCTION:
Answer using only the evidence provided above.
Do not invent phone numbers, UPI IDs, URLs, cases,
risk scores, historical connections or other facts.
If the available evidence does not answer the question,
clearly say that the information is not available.
"""


                with st.spinner(
                    "Copilot is analyzing the case..."
                ):

                    try:

                        answer = ask_copilot(
                            question,
                            context
                        )

                        st.session_state.copilot_answer = answer

                    except Exception as e:

                        st.error(
                            "Copilot request failed."
                        )

                        st.exception(e)


        if st.session_state.copilot_answer:

            st.divider()

            st.subheader(
                "💡 Copilot Response"
            )

            st.write(
                st.session_state.copilot_answer
            )