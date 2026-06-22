import networkx as nx
import plotly.graph_objects as go


def build_graph(current_data, connected_cases):

    graph = nx.Graph()

    # Current complaint node
    graph.add_node(
        "Current Complaint",
        node_type="complaint"
    )

    # Current complaint phones
    for phone in current_data.get(
        "phone_numbers",
        []
    ):

        graph.add_node(
            phone,
            node_type="phone"
        )

        graph.add_edge(
            "Current Complaint",
            phone
        )

    # Current complaint UPI IDs
    for upi in current_data.get(
        "upi_ids",
        []
    ):

        graph.add_node(
            upi,
            node_type="upi"
        )

        graph.add_edge(
            "Current Complaint",
            upi
        )

    # Connected cases
    for case in connected_cases:

        case_id = case.get(
            "complaint_id",
            "UNKNOWN"
        )

        graph.add_node(
            case_id,
            node_type="case"
        )

        graph.add_edge(
            "Current Complaint",
            case_id
        )

        # Case phones
        for phone in case.get(
            "phone_numbers",
            []
        ):

            graph.add_node(
                phone,
                node_type="phone"
            )

            graph.add_edge(
                case_id,
                phone
            )

        # Case UPI IDs
        for upi in case.get(
            "upi_ids",
            []
        ):

            graph.add_node(
                upi,
                node_type="upi"
            )

            graph.add_edge(
                case_id,
                upi
            )

    return graph


def visualize_graph(graph):

    nodes = list(graph.nodes())

    node_positions = {}

    # Manual layout
    for index, node in enumerate(nodes):

        node_positions[node] = (
            index * 2,
            0
        )

    edge_x = []
    edge_y = []

    for edge in graph.edges():

        x0, y0 = node_positions[
            edge[0]
        ]

        x1, y1 = node_positions[
            edge[1]
        ]

        edge_x.extend(
            [x0, x1, None]
        )

        edge_y.extend(
            [y0, y1, None]
        )

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        hoverinfo="none"
    )

    node_x = []
    node_y = []
    node_text = []

    for node in nodes:

        x, y = node_positions[node]

        node_x.append(x)
        node_y.append(y)

        node_text.append(
            str(node)
        )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        hoverinfo="text",
        marker=dict(
            size=25
        )
    )

    fig = go.Figure(
        data=[
            edge_trace,
            node_trace
        ]
    )

    fig.update_layout(
        title="Fraud Intelligence Network",
        showlegend=False,
        hovermode="closest"
    )

    return fig