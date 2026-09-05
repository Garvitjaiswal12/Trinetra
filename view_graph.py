#!/usr/bin/env python3
"""
Graph Viewer — quick visual sanity check of the entity graph (Stage 3 output)
--------------------------------------------------------------------------------
Full graphs (tens of thousands of nodes) are unreadable rendered directly, so
this script samples a manageable, meaningful subgraph and renders it as an
interactive HTML file you can open in any browser (fully offline).

Sampling strategy: takes the top N highest-degree wallets (the most
interesting entities — likely hubs, collectors, mixers) plus everything
directly connected to them (their transactions and counterparty IPs/wallets).

Usage:
    python3 view_graph.py graph.graphml --top-wallets 15 --out graph_view.html

Then open graph_view.html in your Windows browser:
    explorer.exe graph_view.html      (run this from WSL)
"""

import argparse

import networkx as nx
from pyvis.network import Network

COLOR_MAP = {
    "wallet": "#4C9AFF",       # blue
    "transaction": "#FFAB00",  # amber
    "ip": "#36B37E",           # green
}
SIZE_MAP = {
    "wallet": 18,
    "transaction": 10,
    "ip": 14,
}


def sample_subgraph(G, top_n_wallets, hops=1, max_nodes=400):
    """
    Samples around the top-degree wallets. Defaults to 1-hop expansion and a
    hard node cap -- a 2-hop expansion on a real-sized graph can balloon into
    thousands of nodes, which makes the browser's physics simulation crawl
    and looks messy rather than presentable in a live demo.
    """
    wallet_degrees = [(n, G.degree(n)) for n, d in G.nodes(data=True) if d.get("node_type") == "wallet"]
    wallet_degrees.sort(key=lambda x: x[1], reverse=True)
    top_wallets = [w for w, _ in wallet_degrees[:top_n_wallets]]

    nodes_to_keep = set(top_wallets)
    frontier = set(top_wallets)
    for _ in range(hops):
        next_frontier = set()
        for w in frontier:
            next_frontier.update(nx.all_neighbors(G, w))
        nodes_to_keep.update(next_frontier)
        frontier = next_frontier
        if len(nodes_to_keep) >= max_nodes:
            break

    # Hard safety cap: if still oversized, trim down to the highest-degree
    # nodes within the sample so rendering always stays fast.
    if len(nodes_to_keep) > max_nodes:
        ranked = sorted(nodes_to_keep, key=lambda n: G.degree(n), reverse=True)
        nodes_to_keep = set(ranked[:max_nodes]) | set(top_wallets)

    return G.subgraph(nodes_to_keep).copy(), set(top_wallets)


def render(G_sub, highlighted, out_path):
    net = Network(height="850px", width="100%", directed=True, bgcolor="#111111", font_color="white")
    # Faster solver + short stabilization window, then physics turns itself
    # off once settled -- loads quickly and stays still for a clean demo
    # instead of endlessly jittering while judges are watching.
    net.barnes_hut(gravity=-2000, central_gravity=0.3, spring_length=90, spring_strength=0.02)

    for node, data in G_sub.nodes(data=True):
        ntype = data.get("node_type", "unknown")
        color = COLOR_MAP.get(ntype, "#CCCCCC")
        size = SIZE_MAP.get(ntype, 10)
        border = "#FF5630" if node in highlighted else color  # red border = flagged hub wallet

        label = str(node)[:10] + "…" if ntype != "ip" else str(node)
        title_lines = [f"type: {ntype}"]
        for k, v in data.items():
            if k != "node_type":
                title_lines.append(f"{k}: {v}")
        title = "\n".join(title_lines)

        net.add_node(
            node, label=label, title=title, color=color, size=size,
            borderWidth=4 if node in highlighted else 1,
            borderWidthSelected=6,
        )

    for u, v, data in G_sub.edges(data=True):
        etype = data.get("edge_type", "")
        edge_label = ""
        if "amount" in data:
            edge_label = f"{data['amount']:.4f} BTC"
        net.add_edge(u, v, title=etype, label=edge_label, arrows="to")

    net.set_options("""
    {
      "nodes": {"font": {"size": 12}},
      "edges": {"font": {"size": 8, "align": "middle"}, "color": {"inherit": false, "color": "#666666"}},
      "physics": {
        "stabilization": {"iterations": 80, "fit": true},
        "barnesHut": {"avoidOverlap": 0.2}
      },
      "layout": {"improvedLayout": false}
    }
    """)

    net.write_html(out_path, notebook=False)
    # Freeze physics right after stabilization finishes so the layout holds
    # still for a clean demo instead of drifting/jittering continuously.
    with open(out_path, "r") as f:
        html = f.read()
    freeze_script = """
    <script type="text/javascript">
      network.once("stabilizationIterationsDone", function () {
        network.setOptions({ physics: false });
      });
    </script>
    """
    html = html.replace("</body>", freeze_script + "</body>")
    with open(out_path, "w") as f:
        f.write(html)
    print(f"Interactive graph written to: {out_path}")
    print("Node colors: blue=wallet, amber=transaction, green=IP")
    print("Red-bordered nodes = the top-degree 'hub' wallets used for sampling")


def main():
    parser = argparse.ArgumentParser(description="Render an interactive HTML view of the entity graph.")
    parser.add_argument("graphml_file", help="Path to graph.graphml (Stage 3 output)")
    parser.add_argument("--top-wallets", type=int, default=10, help="Number of top-degree wallets to sample around")
    parser.add_argument("--hops", type=int, default=1, help="Neighbor expansion depth (1 = fast/presentable, 2 = denser)")
    parser.add_argument("--max-nodes", type=int, default=400, help="Hard cap on total rendered nodes")
    parser.add_argument("--out", default="graph_view.html", help="Output HTML path")
    args = parser.parse_args()

    print(f"Loading: {args.graphml_file}")
    G = nx.read_graphml(args.graphml_file)
    print(f"  Full graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    print(f"Sampling subgraph around top {args.top_wallets} highest-degree wallets...")
    G_sub, highlighted = sample_subgraph(G, args.top_wallets, hops=args.hops, max_nodes=args.max_nodes)
    print(f"  Sampled subgraph: {G_sub.number_of_nodes()} nodes, {G_sub.number_of_edges()} edges")

    render(G_sub, highlighted, args.out)


if __name__ == "__main__":
    main()
