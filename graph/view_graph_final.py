#!/usr/bin/env python3
"""
Graph Viewer — Deep Ocean edition (Stage 3 output visual)
--------------------------------------------------------------------------------
Full graphs (tens of thousands of nodes) are unreadable rendered directly, so
this script samples a manageable, meaningful subgraph and renders it as an
interactive HTML file you can open in any browser (fully offline).

Sampling strategy: takes the top N highest-degree wallets (the most
interesting entities — likely hubs, collectors, mixers) plus everything
directly connected to them (their transactions), then explicitly attaches
the IP addresses that broadcast those transactions (see note below on why
that's a separate step).

Features:
  - "Deep Ocean" color theme (navy background, cyan wallets, amber txns, teal IPs)
  - Node size scaled by degree (bigger = more connected = visually stands out)
  - Edge colors differentiated by relationship type (input / output / broadcast)
  - Floating glass legend + live stats panel
  - Search box to find and focus a specific wallet/txid/IP by (partial) id
  - Click-to-highlight: clicking a node dims everything except its neighborhood
  - Soft glow/shadow on nodes for a more polished look

Fixed in this version:
  - IPs were showing up as 0 in every sample. The graph shape is
    wallet --input_to--> transaction --output_to--> wallet, and separately
    ip --broadcasts--> transaction. An IP is never adjacent to a wallet, so
    a 1-hop expansion seeded from wallets can only ever reach transactions
    and stops one hop short of any IP. On top of that, the old trim step
    gave wallets a reserve equal to the *entire* node budget and processed
    them first, so even a --hops 2 run would have its IPs squeezed out
    during trimming. Sampling now explicitly attaches the IPs that
    broadcast the sampled transactions, with their own reserved quota that
    survives trimming, controlled by --ip-share.
  - The search button ("Go", bottom right) previously never worked: pyvis
    wraps `nodes`/`edges`/`network` inside a local drawGraph() function, so
    the overlay script threw a ReferenceError on `network` before it ever
    reached the `trinetraSearch` definition. Those objects are now
    published onto `window`, and the overlay polls for them before wiring
    up handlers. Dimming also now recolors nodes instead of relying on
    per-node `opacity`, which some vis-network builds ignore.

Usage:
    python3 view_graph.py graph.graphml --top-wallets 15 --hops 1 --out graph_view.html

Then open graph_view.html in your Windows browser:
    explorer.exe graph_view.html      (run this from WSL)
"""

import argparse
import json

import networkx as nx
from pyvis.network import Network

# ---------------------------------------------------------------------------
# Deep Ocean theme
# ---------------------------------------------------------------------------
BG_COLOR = "#071021"          # near-black navy
PANEL_BG = "rgba(9, 22, 43, 0.88)"
PANEL_BORDER = "rgba(79, 209, 197, 0.35)"
TEXT_COLOR = "#DCEFF2"
ACCENT = "#4FD1C5"            # teal accent for headings/glow

COLOR_MAP = {
    "wallet": "#4FC3F7",       # electric cyan-blue
    "transaction": "#FFB300",  # amber/gold
    "ip": "#2ED9A0",           # sea-green / teal
}
GLOW_MAP = {
    "wallet": "rgba(79,195,247,0.55)",
    "transaction": "rgba(255,179,0,0.5)",
    "ip": "rgba(46,217,160,0.5)",
}
BASE_SIZE = {
    "wallet": 16,
    "transaction": 9,
    "ip": 14,   # bumped up slightly — IPs are usually degree-1 leaves and
                # were getting lost visually against the amber transactions
}
EDGE_COLOR = {
    "input_to": "#6FA8DC",     # cool blue — money flowing into a tx
    "output_to": "#FFD37A",    # warm amber — money flowing out of a tx
    "broadcasts": "#3FE0C0",   # teal — IP broadcast link
}
HUB_BORDER = "#FF5F5F"         # coral-red ring for flagged hub wallets
DIM_BG = "#16233a"             # color used to fade out non-neighbors


def sample_subgraph(G, top_n_wallets, hops=1, max_nodes=450, ip_share=0.15):
    """
    Samples around the top-degree wallets, then explicitly attaches the IPs
    that broadcast the sampled transactions.

    IPs are never adjacent to a wallet -- they hang off transactions via
    `broadcasts` edges -- so a wallet-seeded 1-hop expansion can only ever
    reach transactions, never IPs. The attachment step below is what puts
    IPs in the picture without needing an expensive full 2-hop expansion
    (which would also balloon in wallets/transactions long before it
    reliably surfaced IPs).

    ip_share is the fraction of max_nodes reserved for IP nodes, both when
    initially attaching them and when trimming down to max_nodes.
    """
    wallet_degrees = [(n, G.degree(n)) for n, d in G.nodes(data=True)
                      if d.get("node_type") == "wallet"]
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

    # --- attach broadcasting IPs -------------------------------------
    ip_budget = max(1, int(max_nodes * ip_share))
    txns = [n for n in nodes_to_keep
            if G.nodes[n].get("node_type") == "transaction"]
    # Prefer transactions that are already well connected, so the IPs we
    # surface hang off the visually prominent part of the sample rather
    # than an arbitrary corner of it.
    txns.sort(key=lambda n: G.degree(n), reverse=True)

    attached_ips = set()
    for t in txns:
        if len(attached_ips) >= ip_budget:
            break
        for nb in nx.all_neighbors(G, t):
            if G.nodes[nb].get("node_type") == "ip":
                attached_ips.add(nb)
                if len(attached_ips) >= ip_budget:
                    break
    nodes_to_keep.update(attached_ips)
    # -----------------------------------------------------------------

    if len(nodes_to_keep) > max_nodes:
        # Stratified trim with real quotas per node type. The previous
        # version gave "wallet" a reserve equal to the entire max_nodes
        # budget and processed it first, which meant transactions and IPs
        # only ever got whatever scraps were left -- often zero.
        by_type = {}
        for n in nodes_to_keep:
            t = G.nodes[n].get("node_type", "unknown")
            by_type.setdefault(t, []).append(n)
        for t in by_type:
            by_type[t].sort(key=lambda n: G.degree(n), reverse=True)

        # Never lose the hub wallets themselves or the IPs we just went
        # out of our way to find.
        kept = set(top_wallets) | attached_ips

        quota = {
            "ip": int(max_nodes * ip_share),
            "transaction": int(max_nodes * 0.55),
            "wallet": int(max_nodes * 0.30),
        }
        ordered_types = ["ip", "transaction", "wallet"] + \
            [k for k in by_type if k not in ("ip", "transaction", "wallet")]
        for t in ordered_types:
            reserve = quota.get(t, int(max_nodes * 0.05))
            for n in by_type.get(t, []):
                if reserve <= 0 or len(kept) >= max_nodes:
                    break
                if n in kept:
                    continue
                kept.add(n)
                reserve -= 1

        # top up with whatever highest-degree nodes remain, if under budget
        if len(kept) < max_nodes:
            remainder = sorted(nodes_to_keep - kept,
                               key=lambda n: G.degree(n), reverse=True)
            kept.update(remainder[: max_nodes - len(kept)])

        nodes_to_keep = kept

    return G.subgraph(nodes_to_keep).copy(), set(top_wallets)


def expose_pyvis_globals(html):
    """
    pyvis emits its graph setup inside `function drawGraph() { ... }`, so
    `nodes`, `edges` and `network` are function-local and invisible to any
    script we append afterwards. Publish them onto `window` so the overlay
    can reach them. Falls back to a couple of alternative anchors in case a
    different pyvis version formats the return statement differently.
    """
    injection = ("window.network = network; window.nodes = nodes; "
                 "window.edges = edges; ")

    for anchor in ("return network;", "return network ;", "return network"):
        if anchor in html:
            return html.replace(anchor, injection + anchor, 1)

    marker = "network = new vis.Network(container, data, options);"
    if marker in html:
        return html.replace(marker, marker + " " + injection, 1)

    print("WARNING: could not locate pyvis drawGraph() return — "
          "search/highlight may not initialise. Check the browser console.")
    return html


def render(G_full, G_sub, highlighted, out_path):
    net = Network(height="880px", width="100%", directed=True,
                  bgcolor=BG_COLOR, font_color=TEXT_COLOR)

    # forceAtlas2Based tends to produce tighter, more organic hub-and-spoke
    # clusters than barnesHut, which reads as "denser" and more deliberate
    # for a demo audience, while still settling quickly.
    net.force_atlas_2based(gravity=-45, central_gravity=0.012,
                           spring_length=95, spring_strength=0.06,
                           damping=0.75, overlap=0.3)

    degrees = dict(G_sub.degree())
    max_deg = max(degrees.values()) if degrees else 1

    type_counts = {"wallet": 0, "transaction": 0, "ip": 0}

    for node, data in G_sub.nodes(data=True):
        ntype = data.get("node_type", "unknown")
        type_counts[ntype] = type_counts.get(ntype, 0) + 1
        color = COLOR_MAP.get(ntype, "#CCCCCC")
        glow = GLOW_MAP.get(ntype, "rgba(200,200,200,0.4)")
        is_hub = node in highlighted

        # size scales gently with degree so hubs visually pop without
        # dwarfing everything else
        deg_boost = (degrees.get(node, 0) / max_deg) * 14
        size = BASE_SIZE.get(ntype, 10) + deg_boost

        border = HUB_BORDER if is_hub else color
        label = str(node)[:10] + "…" if ntype != "ip" else str(node)
        title_lines = [f"type: {ntype}", f"degree (in sample): {degrees.get(node, 0)}"]
        for k, v in data.items():
            if k != "node_type":
                title_lines.append(f"{k}: {v}")
        title = "\n".join(title_lines)

        # NOTE: deliberately no "group" kwarg here. vis-network can assign
        # its own auto-palette colors to grouped nodes in some situations,
        # which is what caused wallets/transactions to render with swapped
        # colors previously. Every node's color is set explicitly instead,
        # so there's no ambiguity about which type gets which color.
        net.add_node(
            node, label=label, title=title, shape="dot", color={
                "background": color, "border": border,
                "highlight": {"background": color, "border": HUB_BORDER},
                "hover": {"background": color, "border": ACCENT},
            },
            size=size,
            borderWidth=4 if is_hub else 1.5,
            borderWidthSelected=6,
            shadow={"enabled": True, "color": glow, "size": 18 if is_hub else 10, "x": 0, "y": 0},
        )

    for u, v, data in G_sub.edges(data=True):
        etype = data.get("edge_type", "")
        edge_label = f"{data['amount']:.4f} BTC" if "amount" in data else ""
        e_color = EDGE_COLOR.get(etype, "#5A6B85")
        net.add_edge(u, v, title=etype, label=edge_label, arrows="to",
                     color={"color": e_color, "highlight": ACCENT, "opacity": 0.55},
                     smooth={"type": "continuous", "roundness": 0.25})

    net.set_options("""
    {
      "nodes": {"font": {"size": 12, "face": "Segoe UI, sans-serif"}},
      "edges": {"font": {"size": 8, "align": "middle", "color": "#9FB3C8", "strokeWidth": 0},
                "color": {"inherit": false}, "smooth": true},
      "interaction": {"hover": true, "tooltipDelay": 120, "hideEdgesOnDrag": true},
      "physics": {
        "stabilization": {"iterations": 120, "fit": true},
        "forceAtlas2Based": {"avoidOverlap": 0.3}
      },
      "layout": {"improvedLayout": true}
    }
    """)

    net.write_html(out_path, notebook=False)

    with open(out_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = expose_pyvis_globals(html)

    stats_json = json.dumps({
        "full_nodes": G_full.number_of_nodes(),
        "full_edges": G_full.number_of_edges(),
        "sample_nodes": G_sub.number_of_nodes(),
        "sample_edges": G_sub.number_of_edges(),
        "wallets": type_counts.get("wallet", 0),
        "transactions": type_counts.get("transaction", 0),
        "ips": type_counts.get("ip", 0),
        "hubs": len(highlighted),
    })

    overlay = f"""
    <style>
      body {{ margin: 0; background: {BG_COLOR}; }}
      #mynetwork {{ background: radial-gradient(circle at 50% 30%, #0d1c33 0%, {BG_COLOR} 70%); }}

      .trinetra-panel {{
        position: fixed; z-index: 999; background: {PANEL_BG};
        border: 1px solid {PANEL_BORDER}; border-radius: 12px;
        color: {TEXT_COLOR}; font-family: 'Segoe UI', sans-serif;
        backdrop-filter: blur(6px); box-shadow: 0 8px 32px rgba(0,0,0,0.45);
      }}

      #trinetra-title {{
        top: 18px; left: 18px; padding: 10px 20px; display: flex; align-items: center; gap: 12px;
      }}
      #trinetra-eye-logo {{ flex-shrink: 0; filter: drop-shadow(0 0 6px rgba(79,209,197,0.55)); }}
      #trinetra-title h1 {{
        margin: 0; font-size: 18px; font-weight: 600;
        background: linear-gradient(90deg, {ACCENT}, #4FC3F7);
        -webkit-background-clip: text; background-clip: text; color: transparent;
        letter-spacing: 0.5px;
      }}
      #trinetra-title p {{ margin: 2px 0 0; font-size: 11px; color: #8FA5BC; letter-spacing: 0.5px; }}

      #trinetra-legend {{
        bottom: 18px; left: 18px; padding: 14px 18px; min-width: 210px;
      }}
      #trinetra-legend h3 {{ margin: 0 0 8px; font-size: 12px; color: {ACCENT}; text-transform: uppercase; letter-spacing: 1px; }}
      .legend-row {{ display: flex; align-items: center; gap: 8px; font-size: 13px; margin: 5px 0; }}
      .legend-dot {{ width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }}
      .legend-dot.hub {{ border: 2px solid {HUB_BORDER}; width: 8px; height: 8px; background: transparent; }}

      #trinetra-stats {{
        top: 18px; right: 18px; padding: 14px 18px; min-width: 190px; font-size: 12px;
      }}
      #trinetra-stats h3 {{ margin: 0 0 8px; font-size: 12px; color: {ACCENT}; text-transform: uppercase; letter-spacing: 1px; }}
      .stat-row {{ display: flex; justify-content: space-between; margin: 3px 0; color: #B9CBDC; }}
      .stat-row b {{ color: {TEXT_COLOR}; }}

      #trinetra-search {{
        bottom: 18px; right: 18px; padding: 12px 16px; display: flex; gap: 8px; align-items: center;
      }}
      #trinetra-search input {{
        background: #0c1c33; border: 1px solid {PANEL_BORDER}; border-radius: 6px;
        color: {TEXT_COLOR}; padding: 6px 10px; font-size: 12px; width: 170px; outline: none;
      }}
      #trinetra-search button {{
        background: {ACCENT}; border: none; border-radius: 6px; color: #06131F;
        font-weight: 600; padding: 6px 12px; font-size: 12px; cursor: pointer;
      }}
      #trinetra-search button:hover {{ filter: brightness(1.1); }}
      #trinetra-search button:disabled {{ opacity: 0.5; cursor: default; }}
      #trinetra-hint {{ font-size: 10px; color: #708196; margin-top: 4px; }}
    </style>

    <div class="trinetra-panel" id="trinetra-title">
      <svg id="trinetra-eye-logo" width="36" height="36" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
        <path d="M4 32 C 14 12, 50 12, 60 32 C 50 52, 14 52, 4 32 Z"
              fill="none" stroke="{ACCENT}" stroke-width="3" stroke-linejoin="round"/>
        <circle cx="32" cy="32" r="15" fill="#06131F" stroke="{ACCENT}" stroke-width="2"/>
        <circle cx="32" cy="32" r="15" fill="none" stroke="{COLOR_MAP['transaction']}" stroke-width="1" opacity="0.6"/>
        <text x="32" y="38" font-size="17" text-anchor="middle" font-family="Segoe UI, sans-serif"
              font-weight="700" fill="{COLOR_MAP['transaction']}">&#8383;</text>
      </svg>
      <div>
        <h1>Trinetra &mdash; Entity Graph</h1>
        <p>Team = Quantum Minds</p>
      </div>
    </div>

    <div class="trinetra-panel" id="trinetra-legend">
      <h3>Legend</h3>
      <div class="legend-row"><span class="legend-dot" style="background:{COLOR_MAP['wallet']}"></span> Wallets (Bitcoin addresses)</div>
      <div class="legend-row"><span class="legend-dot" style="background:{COLOR_MAP['transaction']}"></span> Transactions (single TXID)</div>
      <div class="legend-row"><span class="legend-dot" style="background:{COLOR_MAP['ip']}"></span> IP addresses (who broadcast it)</div>
      <div class="legend-row"><span class="legend-dot hub"></span> Coral ring = flagged hub wallet</div>
    </div>

    <div class="trinetra-panel" id="trinetra-stats">
      <h3>Sample Stats</h3>
      <div class="stat-row"><span>Wallets</span><b id="st-wallets">-</b></div>
      <div class="stat-row"><span>Transactions</span><b id="st-txns">-</b></div>
      <div class="stat-row"><span>IPs</span><b id="st-ips">-</b></div>
      <div class="stat-row"><span>Hub wallets</span><b id="st-hubs">-</b></div>
      <div class="stat-row"><span>Sampled nodes</span><b id="st-sn">-</b></div>
      <div class="stat-row"><span>Full graph nodes</span><b id="st-fn">-</b></div>
    </div>

    <div class="trinetra-panel" id="trinetra-search">
      <div>
        <input id="trinetra-search-input" type="text" placeholder="Find wallet / txid / IP..." />
        <div id="trinetra-hint">Loading graph...</div>
      </div>
      <button id="trinetra-search-btn" disabled>Go</button>
    </div>

    <script type="text/javascript">
      var TRINETRA_STATS = {stats_json};
      var TRINETRA_DIM = {{ background: "{DIM_BG}", border: "{DIM_BG}" }};

      (function fillStats() {{
        var s = TRINETRA_STATS;
        document.getElementById('st-wallets').innerText = s.wallets;
        document.getElementById('st-txns').innerText = s.transactions;
        document.getElementById('st-ips').innerText = s.ips;
        document.getElementById('st-hubs').innerText = s.hubs;
        document.getElementById('st-sn').innerText = s.sample_nodes + ' / ' + s.sample_edges + ' edges';
        document.getElementById('st-fn').innerText = s.full_nodes + ' / ' + s.full_edges + ' edges';
      }})();

      // pyvis builds the graph inside drawGraph(); we injected window.network /
      // window.nodes above, but the script may not have run yet, so poll for it.
      var TRINETRA_TRIES = 0;
      function trinetraInit() {{
        var network = window.network;
        var nodes = window.nodes;

        if (!network || !nodes) {{
          if (++TRINETRA_TRIES > 100) {{
            document.getElementById('trinetra-hint').innerText = 'Graph objects not found';
            return;
          }}
          return setTimeout(trinetraInit, 100);
        }}

        var allNodeIds = nodes.getIds();
        var ORIGINAL = {{}};
        nodes.get().forEach(function (n) {{ ORIGINAL[n.id] = n.color; }});

        var hint = document.getElementById('trinetra-hint');
        var input = document.getElementById('trinetra-search-input');
        var btn = document.getElementById('trinetra-search-btn');

        function setHint(msg) {{ hint.innerText = msg; }}

        network.once("stabilizationIterationsDone", function () {{
          network.setOptions({{ physics: false }});
        }});

        // Dim by recoloring rather than by opacity -- several vis-network
        // builds silently ignore per-node opacity.
        function resetHighlight() {{
          nodes.update(allNodeIds.map(function (id) {{
            return {{ id: id, color: ORIGINAL[id], opacity: 1 }};
          }}));
        }}

        function highlightNeighborhood(nodeId) {{
          var connected = new Set(network.getConnectedNodes(nodeId));
          connected.add(nodeId);
          nodes.update(allNodeIds.map(function (id) {{
            var on = connected.has(id);
            return {{ id: id, color: on ? ORIGINAL[id] : TRINETRA_DIM, opacity: on ? 1 : 0.15 }};
          }}));
        }}

        function search() {{
          var q = input.value.trim().toLowerCase();
          if (!q) {{ resetHighlight(); setHint('Enter = focus & highlight'); return; }}
          var match = null;
          for (var i = 0; i < allNodeIds.length; i++) {{
            if (String(allNodeIds[i]).toLowerCase().indexOf(q) !== -1) {{
              match = allNodeIds[i];
              break;
            }}
          }}
          if (match === null) {{
            setHint('No match for "' + q + '"');
            return;
          }}
          setHint('Focused: ' + String(match).slice(0, 22));
          highlightNeighborhood(match);
          network.selectNodes([match]);
          network.focus(match, {{
            scale: 1.6,
            animation: {{ duration: 600, easingFunction: "easeInOutQuad" }}
          }});
        }}

        network.on("click", function (params) {{
          if (params.nodes.length > 0) {{
            highlightNeighborhood(params.nodes[0]);
          }} else {{
            resetHighlight();
            setHint('Enter = focus & highlight');
          }}
        }});

        btn.addEventListener('click', search);
        input.addEventListener('keydown', function (e) {{
          if (e.key === 'Enter') {{ e.preventDefault(); search(); }}
        }});

        // Expose for console debugging / inline handlers.
        window.trinetraSearch = search;
        window.trinetraResetHighlight = resetHighlight;
        window.trinetraHighlightNeighborhood = highlightNeighborhood;

        btn.disabled = false;
        setHint('Enter = focus & highlight');
      }}

      if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', trinetraInit);
      }} else {{
        trinetraInit();
      }}
    </script>
    """

    html = html.replace("</body>", overlay + "</body>", 1)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Interactive graph written to: {out_path}")
    print(f"  Sample composition: {type_counts.get('wallet',0)} wallets, "
          f"{type_counts.get('transaction',0)} transactions, "
          f"{type_counts.get('ip',0)} IPs")
    print("Node colors: cyan=wallet, amber=transaction, teal=IP")
    print("Coral-ring nodes = the top-degree 'hub' wallets used for sampling")
    print("Search box (bottom right): type a partial id, press Enter or click Go")


def main():
    parser = argparse.ArgumentParser(description="Render a Deep Ocean-themed interactive view of the entity graph.")
    parser.add_argument("graphml_file", help="Path to graph.graphml (Stage 3 output)")
    parser.add_argument("--top-wallets", type=int, default=15, help="Number of top-degree wallets to sample around")
    parser.add_argument("--hops", type=int, default=1, help="Neighbor expansion depth from wallets (1 = fast/presentable, 2 = denser)")
    parser.add_argument("--max-nodes", type=int, default=450, help="Hard cap on total rendered nodes")
    parser.add_argument("--ip-share", type=float, default=0.15,
                        help="Fraction of --max-nodes reserved for IP nodes (default 0.15)")
    parser.add_argument("--out", default="graph_view.html", help="Output HTML path")
    args = parser.parse_args()

    print(f"Loading: {args.graphml_file}")
    G = nx.read_graphml(args.graphml_file)
    print(f"  Full graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    print(f"Sampling subgraph around top {args.top_wallets} highest-degree wallets...")
    G_sub, highlighted = sample_subgraph(G, args.top_wallets, hops=args.hops,
                                         max_nodes=args.max_nodes,
                                         ip_share=args.ip_share)
    print(f"  Sampled subgraph: {G_sub.number_of_nodes()} nodes, {G_sub.number_of_edges()} edges")

    render(G, G_sub, highlighted, args.out)


if __name__ == "__main__":
    main()
