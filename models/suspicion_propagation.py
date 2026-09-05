#!/usr/bin/env python3
"""
Stage 4f — Suspicion Propagation
--------------------------------------
Every detector so far only flags a wallet based on ITS OWN behavior or
structure. This misses a real laundering technique: the "integration" stage
is specifically designed to look clean -- a wallet several hops downstream
of confirmed dirty money can show zero anomalous behavior of its own while
still being part of the laundering chain.

This module runs a personalized PageRank diffusion seeded at high-confidence
wallets from final_alerts.csv, letting "suspicion" flow outward through the
transaction graph and decay with distance. A wallet that is graph-close to
many high-confidence flags accumulates propagated suspicion even if it never
matched a single rule itself -- catching exactly the blind spot above.

Usage:
    python3 suspicion_propagation.py \\
        --graph ../graph/graph.graphml \\
        --alerts ../models/final_alerts.csv \\
        --seed-threshold 70 \\
        --out propagated_suspicion.csv
"""
import argparse

import networkx as nx
import pandas as pd


def build_seed_weights(alerts_df, threshold):
    """High-confidence wallets become PageRank's personalization seeds,
    weighted by their own confidence score."""
    seeds = alerts_df[alerts_df["combined_confidence"] >= threshold]
    if len(seeds) == 0:
        return {}
    total = seeds["combined_confidence"].sum()
    return {row["wallet"]: row["combined_confidence"] / total for _, row in seeds.iterrows()}


def propagate(G, seed_weights, alpha=0.6):
    """
    alpha = damping factor. Lower alpha = suspicion decays FASTER with graph
    distance (stays more local to the seeds); higher alpha = spreads further.
    0.6 is deliberately conservative -- we want propagated suspicion to mean
    "close to confirmed dirty money", not "anywhere in a huge component".
    """
    # personalized PageRank needs every node represented in the dict (0 for non-seeds)
    personalization = {n: seed_weights.get(n, 0.0) for n in G.nodes()}
    scores = nx.pagerank(G, alpha=alpha, personalization=personalization, weight=None)
    return scores


def main():
    parser = argparse.ArgumentParser(description="Propagate suspicion outward from high-confidence wallets.")
    parser.add_argument("--graph", required=True, help="Path to graph.graphml (Stage 3 output)")
    parser.add_argument("--alerts", required=True, help="Path to final_alerts.csv (Stage 4c output)")
    parser.add_argument("--seed-threshold", type=float, default=70,
                         help="Confidence threshold above which a wallet becomes a propagation seed")
    parser.add_argument("--alpha", type=float, default=0.6, help="Damping factor (lower = more local decay)")
    parser.add_argument("--out", default="propagated_suspicion.csv")
    args = parser.parse_args()

    print(f"Loading graph: {args.graph}")
    G = nx.read_graphml(args.graph)
    print(f"  {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    print(f"Loading alerts: {args.alerts}")
    alerts = pd.read_csv(args.alerts)

    seed_weights = build_seed_weights(alerts, args.seed_threshold)
    print(f"Seed wallets (confidence >= {args.seed_threshold}): {len(seed_weights)}")
    if not seed_weights:
        print("No seeds found at this threshold -- lower --seed-threshold and retry.")
        return

    print(f"Running personalized PageRank (alpha={args.alpha})...")
    scores = propagate(G, seed_weights, args.alpha)

    # Only report on WALLET nodes, excluding the seeds themselves (we already know about those)
    wallet_nodes = {n for n, d in G.nodes(data=True) if d.get("node_type") == "wallet"}
    already_flagged = set(alerts[alerts["combined_confidence"] >= args.seed_threshold]["wallet"])

    rows = []
    for wallet in wallet_nodes:
        if wallet in already_flagged:
            continue
        rows.append({"wallet": wallet, "propagated_suspicion_raw": scores.get(wallet, 0.0)})

    result = pd.DataFrame(rows)
    if len(result) == 0:
        print("No non-seed wallets found in graph.")
        return

    # Rescale to 0-100 for consistency with the rest of the pipeline's scoring
    max_score = result["propagated_suspicion_raw"].max()
    result["propagated_suspicion_0_100"] = (result["propagated_suspicion_raw"] / max_score * 100).round(2)
    result = result.sort_values("propagated_suspicion_0_100", ascending=False)

    result[["wallet", "propagated_suspicion_0_100"]].to_csv(args.out, index=False)

    print(f"\nTop 10 wallets by propagated suspicion (none of these matched a rule directly):")
    for _, row in result.head(10).iterrows():
        print(f"  {row['wallet'][:20]}...  propagated_score={row['propagated_suspicion_0_100']:.2f}")

    print(f"\nWritten to: {args.out}")
    print("\nThese wallets carry no direct rule match but sit close in the graph to")
    print("confirmed high-confidence flags -- worth investigator review as potential")
    print("'integration stage' wallets (laundering's final, deliberately-clean-looking hop).")


if __name__ == "__main__":
    main()
