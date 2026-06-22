import streamlit as st

from utils.ocr import extract_text_from_image
from agents.extraction_agent import extract_entities
from agents.risk_agent import calculate_risk
from agents.cluster_agent import find_connections
from agents.graph_agent import build_graph, visualize_graph
from agents.copilot_agent import ask_copilot

st.set_page_config(
    page_title="ScamSphere AI",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ ScamSphere AI")
st.subheader("Fraud Campaign Intelligence Platform")

if "extracted" not in st.session_state:
    st.session_state.extracted = None

if "risk" not in st.session_state:
    st.session_state.risk = None

if "connections" not in st.session_state:
    st.session_state.connections = None

tab1, tab2, tab3 = st.tabs([
    "Complaint Analysis",
    "Fraud Network",
    "AI Copilot"
])

# ==========================
# TAB 1 - ANALYSIS
# ==========================

with tab1:

    complaint = st.text_area(
        "Paste suspicious message here"
    )

    uploaded_file = st.file_uploader(
        "Upload Screenshot",
        type=["png", "jpg", "jpeg"]
    )

    if st.button("Analyze"):

        if complaint or uploaded_file:

            if uploaded_file:

                file_extension = uploaded_file.name.split(".")[-1]

                temp_path = f"temp.{file_extension}"

                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                complaint = extract_text_from_image(
                    temp_path
                )

                st.success(
                    "Screenshot processed successfully"
                )

                with st.expander(
                    "View Extracted Text"
                ):
                    st.write(
                        complaint
                    )

            with st.spinner("Analyzing..."):

                extracted = extract_entities(
                    complaint
                )

                risk = calculate_risk(
                    extracted
                )

                connections = find_connections(
                    extracted
                )

                st.session_state.extracted = extracted
                st.session_state.risk = risk
                st.session_state.connections = connections

    if st.session_state.extracted:

        extracted = st.session_state.extracted
        risk = st.session_state.risk
        connections = st.session_state.connections

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Threat Score",
                risk["risk_score"]
            )

        with col2:
            st.metric(
                "Severity",
                risk["severity"]
            )

        with col3:
            st.metric(
                "Campaign Links",
                len(connections)
            )

        st.divider()

        st.subheader(
            "🎯 Threat Intelligence"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                f"**Scam Type:** {extracted['scam_type']}"
            )

            st.write(
                f"**Phone Numbers:** {', '.join(extracted['phone_numbers'])}"
            )

            st.write(
                f"**UPI IDs:** {', '.join(extracted['upi_ids'])}"
            )

        with col2:

            st.write(
                f"**Authorities Mentioned:** {', '.join(extracted['authority_names'])}"
            )

            st.write(
                f"**Amounts:** {', '.join(extracted['amounts'])}"
            )

            st.write(
                f"**Summary:** {extracted['summary']}"
            )

        st.divider()

        st.subheader(
            "🚨 Risk Assessment"
        )

        st.progress(
            risk["risk_score"] / 100
        )

        st.write(
            f"### Risk Score: {risk['risk_score']}%"
        )

        st.write(
            f"### Severity: {risk['severity']}"
        )

        for reason in risk["reasons"]:
            st.success(reason)

        st.divider()

        st.subheader(
            "🕸️ Campaign Intelligence"
        )

        if len(connections) > 0:

            st.error(
                f"Connected to {len(connections)} prior complaints"
            )

        else:

            st.success(
                "No linked complaints found"
            )

# ==========================
# TAB 2 - NETWORK
# ==========================

with tab2:

    st.header(
        "Fraud Network"
    )

    if st.session_state.extracted:

        graph = build_graph(
            st.session_state.extracted,
            st.session_state.connections
        )

        fig = visualize_graph(
            graph
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info(
            "Analyze a complaint first."
        )

# ==========================
# TAB 3 - COPILOT
# ==========================

with tab3:

    st.header(
        "AI Cybercrime Copilot"
    )

    question = st.text_input(
        "Ask a question"
    )

    if st.button(
        "Ask Copilot"
    ):

        if (
            question
            and st.session_state.extracted
        ):

            context = f"""
            Extracted:
            {st.session_state.extracted}

            Risk:
            {st.session_state.risk}

            Connections:
            {st.session_state.connections}
            """

            with st.spinner(
                "Thinking..."
            ):

                answer = ask_copilot(
                    question,
                    context
                )

            st.write(
                answer
            )
