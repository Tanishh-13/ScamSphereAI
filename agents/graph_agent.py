import networkx as nx
import plotly.graph_objects as go


# =========================================================
# BUILD EVIDENCE GRAPH
# =========================================================

def build_graph(
    current_data,
    connected_cases
):

    graph = nx.Graph()

    current_node = "CURRENT COMPLAINT"

    # -----------------------------------------------------
    # Current complaint
    # -----------------------------------------------------

    graph.add_node(
        current_node,
        node_type="complaint",
        label="Current Complaint",
        occurrence_count=1
    )

    # -----------------------------------------------------
    # Helper: add evidence node
    # -----------------------------------------------------

    def add_evidence(
        value,
        evidence_type,
        parent
    ):

        graph.add_node(
            value,
            node_type=evidence_type,
            label=str(value)
        )

        graph.add_edge(
            parent,
            value,
            relationship=evidence_type,
            weight=1
        )

    # -----------------------------------------------------
    # Current evidence
    # -----------------------------------------------------

    for phone in current_data.get(
        "phone_numbers",
        []
    ):

        add_evidence(
            phone,
            "phone",
            current_node
        )

    for upi in current_data.get(
        "upi_ids",
        []
    ):

        add_evidence(
            upi,
            "upi",
            current_node
        )

    for url in current_data.get(
        "urls",
        []
    ):

        add_evidence(
            url,
            "url",
            current_node
        )

    # -----------------------------------------------------
    # Previous connected complaints
    # -----------------------------------------------------

    for case in connected_cases:

        case_id = case.get(
            "complaint_id",
            "UNKNOWN"
        )

        occurrence_count = case.get(
            "occurrence_count",
            1
        )

        connection_score = case.get(
            "connection_score",
            0
        )

        matching_entities = case.get(
            "matching_entities",
            []
        )

        # -------------------------------------------------
        # Case node
        # -------------------------------------------------

        graph.add_node(
            case_id,
            node_type="case",
            label=case_id,
            occurrence_count=occurrence_count,
            risk_score=case.get(
                "risk_score",
                0
            ),
            severity=case.get(
                "severity",
                "UNKNOWN"
            )
        )

        # -------------------------------------------------
        # Connection to current complaint
        # -------------------------------------------------

        graph.add_edge(
            current_node,
            case_id,
            relationship=", ".join(
                matching_entities
            ),
            weight=connection_score
        )

        # -------------------------------------------------
        # Case evidence
        # -------------------------------------------------

        for phone in case.get(
            "phone_numbers",
            []
        ):

            add_evidence(
                phone,
                "phone",
                case_id
            )

        for upi in case.get(
            "upi_ids",
            []
        ):

            add_evidence(
                upi,
                "upi",
                case_id
            )

        for url in case.get(
            "urls",
            []
        ):

            add_evidence(
                url,
                "url",
                case_id
            )

    return graph


# =========================================================
# VISUALIZE GRAPH
# =========================================================

def visualize_graph(graph):

    if len(graph.nodes) == 0:

        return go.Figure()

    # -----------------------------------------------------
    # NetworkX force-directed layout
    # -----------------------------------------------------

    positions = nx.spring_layout(
        graph,
        seed=42,
        k=1.8,
        iterations=100
    )

    # =====================================================
    # EDGES
    # =====================================================

    edge_x = []
    edge_y = []
    edge_hover = []

    for u, v, data in graph.edges(
        data=True
    ):

        x0, y0 = positions[u]
        x1, y1 = positions[v]

        edge_x.extend(
            [x0, x1, None]
        )

        edge_y.extend(
            [y0, y1, None]
        )

        relationship = data.get(
            "relationship",
            "connected"
        )

        weight = data.get(
            "weight",
            1
        )

        edge_hover.append(
            f"{u} → {v}<br>"
            f"Relationship: {relationship}<br>"
            f"Strength: {weight}"
        )

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(
            width=1
        ),
        hoverinfo="none"
    )

    # =====================================================
    # NODES
    # =====================================================

    node_x = []
    node_y = []
    node_text = []
    node_hover = []
    node_sizes = []

    for node, data in graph.nodes(
        data=True
    ):

        x, y = positions[node]

        node_x.append(x)
        node_y.append(y)

        node_type = data.get(
            "node_type",
            "unknown"
        )

        occurrence_count = data.get(
            "occurrence_count",
            1
        )

        risk_score = data.get(
            "risk_score",
            None
        )

        # -------------------------------------------------
        # Display label
        # -------------------------------------------------

        label = data.get(
            "label",
            str(node)
        )

        # Keep long URLs from destroying the graph
        if len(str(label)) > 25:

            label = (
                str(label)[:22]
                + "..."
            )

        node_text.append(
            str(label)
        )

        # -------------------------------------------------
        # Hover information
        # -------------------------------------------------

        hover = (
            f"<b>{node}</b><br>"
            f"Type: {node_type}"
        )

        if occurrence_count:

            hover += (
                f"<br>Occurrences: "
                f"{occurrence_count}"
            )

        if risk_score is not None:

            hover += (
                f"<br>Risk Score: "
                f"{risk_score}"
            )

        node_hover.append(
            hover
        )

        # -------------------------------------------------
        # Node size
        # -------------------------------------------------

        if node_type == "complaint":

            size = 35

        elif node_type == "case":

            size = min(
                25 + occurrence_count * 3,
                50
            )

        else:

            size = 22

        node_sizes.append(size)

    # =====================================================
    # NODE TRACE
    # =====================================================

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",

        text=node_text,

        textposition="top center",

        hovertext=node_hover,

        hoverinfo="text",

        marker=dict(
            size=node_sizes,
            line=dict(
                width=1
            )
        )
    )

    # =====================================================
    # FIGURE
    # =====================================================

    fig = go.Figure(
        data=[
            edge_trace,
            node_trace
        ]
    )

    fig.update_layout(

        title="Live Fraud Evidence Network",

        showlegend=False,

        hovermode="closest",

        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20
        ),

        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),

        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),

        plot_bgcolor="white"
    )

    return fig