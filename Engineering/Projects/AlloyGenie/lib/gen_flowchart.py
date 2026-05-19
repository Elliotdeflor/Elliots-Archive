import matplotlib.pyplot as plt
import networkx as nx

def create_light_fill_flowchart():
    # Create a directed graph
    G = nx.DiGraph()

    # Define nodes and edges
    nodes = {
        "start": "Start",
        "input": "Input Parameters",
        "preprocess": "Preprocess Image",
        "detect_edges": "Detect Edges",
        "identify_regions": "Identify Fillable Regions",
        "apply_fill": "Apply Light Fill Algorithm",
        "postprocess": "Postprocess Image",
        "output": "Output Image",
        "end": "End"
    }

    edges = [
        ("start", "input"),
        ("input", "preprocess"),
        ("preprocess", "detect_edges"),
        ("detect_edges", "identify_regions"),
        ("identify_regions", "apply_fill"),
        ("apply_fill", "postprocess"),
        ("postprocess", "output"),
        ("output", "end")
    ]

    # Add nodes and edges to the graph
    for key, label in nodes.items():
        G.add_node(key, label=label)
    G.add_edges_from(edges)

    # Draw the flowchart
    pos = nx.spring_layout(G, seed=42)  # Layout for positioning nodes
    labels = nx.get_node_attributes(G, 'label')

    plt.figure(figsize=(10, 6))
    nx.draw(G, pos, with_labels=True, labels=labels, node_size=3000, node_color="lightblue", font_size=9, edge_color="gray", font_weight="bold", arrows=True)
    plt.title("Light Fill Algorithm Flowchart")
    plt.show()

# Run the function
create_light_fill_flowchart()
