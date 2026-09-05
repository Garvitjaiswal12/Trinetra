#!/usr/bin/env python3
"""
Stage 4e — Self-Auditing Evaluation Layer
-----------------------------------------------
Most teams report precision/recall and stop. Almost none check whether their
OWN evaluation is trustworthy in the first place. This module runs a set of
sanity checks against any evaluation result and flags when a score is likely
inflated by a dataset artifact rather than genuine detection power -- exactly
the failure mode this project found twice during development (a graph
percolation artifact that made both community detection and common-input
clustering look artificially perfect on the synthetic dataset).

Checks performed:
    1. Population disconnection check -- are illicit and benign wallets
       graph-disconnected from each other? If so, ANY graph-based method
       will look artificially perfect, regardless of whether it's genuinely
       good at finding structure.
    2. Suspiciously-perfect-score check -- flags any precision or recall
       >= 98% as needing manual review before being reported.
    3. Base-rate sanity check -- compares flagged-set precision to the
       dataset's natural illicit ratio to make sure the model is doing
       better than a trivial "flag everyone" or "flag nobody" baseline.
    4. Graph density check -- estimates whether the wallet pool is large
       enough relative to transaction volume to avoid random-graph
       percolation artifacts (the root cause behind checks 1 and 2).

Usage (CLI):
    python3 self_audit.py \\
        --transactions ../ingest/cleaned_transactions.csv \\
        --ground-truth ../dataset/ground_truth.csv \\
        --edges ../dataset/wallet_graph_edges.csv \\
        --alerts final_alerts.csv

Usage (importable, e.g. from the dashboard):
    from self_audit import run_self_audit
    results = run_self_audit(transactions_df, ground_truth_df, edges_df, alerts_df)
    # each result is a dict with keys: check, is_suspicious, verdict, + check-specific fields
"""
import argparse

import networkx as nx
import pandas as pd


def check_population_disconnection(edges_df, wallet_illicit):
    """If illicit and benign wallets fall into entirely separate connected
    components, ANY graph-based clustering will look artificially perfect."""
    WG = nx.Graph()
    for _, row in edges_df.iterrows():
        WG.add_edge(row["src_wallet"], row["dst_wallet"])

    components = list(nx.connected_components(WG))
    pure_components = 0
    mixed_components = 0
    for comp in components:
        labels = {wallet_illicit.get(w, 0) for w in comp}
        if len(labels) == 1:
            pure_components += 1
        else:
            mixed_components += 1

    pure_fraction = pure_components / len(components) if components else 0
    is_suspicious = pure_fraction > 0.9

    return {
        "check": "Population disconnection",
        "total_components": len(components),
        "pure_components": pure_components,
        "mixed_components": mixed_components,
        "pure_fraction": round(pure_fraction, 3),
        "verdict": "SUSPICIOUS -- illicit/benign wallets are nearly graph-disconnected. "
                   "Any graph method will look artificially strong; treat high scores "
                   "on this dataset as unproven until tested on data where populations "
                   "genuinely overlap (as real Bitcoin traffic does)."
                   if is_suspicious else
                   "OK -- illicit and benign wallets are meaningfully interconnected, "
                   "so graph-based results are less likely to be a pure connectivity artifact.",
        "is_suspicious": is_suspicious,
    }


def check_suspiciously_perfect(name, precision, recall, threshold=0.98):
    flagged = precision >= threshold or recall >= threshold
    return {
        "check": f"Suspiciously-perfect-score check ({name})",
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "verdict": f"FLAGGED -- {name} precision/recall >= {threshold*100:.0f}% is unusual enough "
                   "to warrant manual review before reporting; verify against the population "
                   "disconnection check above before trusting this number."
                   if flagged else
                   f"OK -- {name} precision/recall are within a normal range, not flagged for review.",
        "is_suspicious": flagged,
    }


def check_base_rate_uplift(name, flagged_precision, base_rate):
    uplift = flagged_precision / base_rate if base_rate > 0 else float("inf")
    return {
        "check": f"Base-rate uplift check ({name})",
        "base_illicit_rate": round(base_rate, 4),
        "flagged_set_precision": round(flagged_precision, 4),
        "uplift_factor": round(uplift, 2),
        "verdict": f"{name} concentrates illicit wallets at {uplift:.1f}x the dataset's natural rate. "
                   + ("This is a meaningful, non-trivial uplift." if uplift >= 1.5 else
                      "This is only a marginal uplift over guessing at random -- weak signal."),
        "is_suspicious": uplift < 1.5,
    }


def check_graph_density(n_wallets_pool, n_transactions):
    """Rough heuristic: if transactions-per-wallet ratio is high, address-reuse
    based heuristics are likely to hit random-graph percolation and produce
    a single giant connected component, regardless of any real structure."""
    ratio = n_transactions / max(n_wallets_pool, 1)
    is_suspicious = ratio > 2.0
    return {
        "check": "Graph density / percolation risk",
        "wallet_pool_size": n_wallets_pool,
        "transaction_count": n_transactions,
        "tx_per_wallet_ratio": round(ratio, 2),
        "verdict": "SUSPICIOUS -- transaction volume is high relative to wallet pool size; "
                   "address-reuse-based graph heuristics (common-input clustering, connected "
                   "components) are at real risk of collapsing into one giant false cluster."
                   if is_suspicious else
                   "OK -- wallet pool is large enough relative to transaction volume that "
                   "percolation-driven false clustering is less likely.",
        "is_suspicious": is_suspicious,
    }


def _build_wallet_illicit_map(ground_truth_df, edges_df):
    tx_illicit = ground_truth_df.set_index("txid")["is_illicit"].to_dict()
    wallet_illicit = {}
    for _, row in edges_df.iterrows():
        illicit = tx_illicit.get(row["txid"], 0)
        for w in [row["src_wallet"], row["dst_wallet"]]:
            wallet_illicit[w] = wallet_illicit.get(w, 0) or illicit
    return wallet_illicit


def run_self_audit(transactions_df, ground_truth_df, edges_df, alerts_df, thresholds=(70, 80)):
    """
    Run every self-audit check and return a list of result dicts. Pure
    function -- no printing, no side effects -- so it can be called from
    the CLI entrypoint below, or imported directly (e.g. by the dashboard)
    and rendered as UI elements instead of console output.
    """
    wallet_illicit = _build_wallet_illicit_map(ground_truth_df, edges_df)
    n_wallets = len(wallet_illicit)
    base_rate = sum(wallet_illicit.values()) / n_wallets if n_wallets else 0

    results = []
    results.append(check_population_disconnection(edges_df, wallet_illicit))
    results.append(check_graph_density(n_wallets, len(transactions_df)))

    for threshold in thresholds:
        flagged = alerts_df[alerts_df["combined_confidence"] >= threshold].copy()
        if len(flagged) == 0:
            continue
        flagged["is_illicit"] = flagged["wallet"].map(wallet_illicit).fillna(0)
        precision = flagged["is_illicit"].mean()
        recall = flagged["is_illicit"].sum() / max(sum(wallet_illicit.values()), 1)
        results.append(check_suspiciously_perfect(f"combined@{threshold}", precision, recall))
        results.append(check_base_rate_uplift(f"combined@{threshold}", precision, base_rate))

    return results


def print_report(results):
    """Render a list of check results (from run_self_audit) to the terminal."""
    print("=" * 70)
    print("TRINETRA SELF-AUDIT REPORT")
    print("=" * 70)
    n_flags = 0
    for r in results:
        marker = "⚠️  FLAGGED" if r["is_suspicious"] else "✅ OK"
        print(f"\n[{marker}] {r['check']}")
        for k, v in r.items():
            if k not in ("check", "verdict", "is_suspicious"):
                print(f"    {k}: {v}")
        print(f"    -> {r['verdict']}")
        if r["is_suspicious"]:
            n_flags += 1

    print("\n" + "=" * 70)
    print(f"SUMMARY: {n_flags} / {len(results)} checks flagged for review.")
    print("=" * 70)
    return n_flags


def main():
    parser = argparse.ArgumentParser(description="Self-audit Trinetra's own evaluation results.")
    parser.add_argument("--transactions", required=True)
    parser.add_argument("--ground-truth", required=True)
    parser.add_argument("--edges", required=True)
    parser.add_argument("--alerts", required=True, help="final_alerts.csv from Stage 4c")
    args = parser.parse_args()

    df = pd.read_csv(args.transactions)
    truth = pd.read_csv(args.ground_truth)
    edges_df = pd.read_csv(args.edges)
    alerts = pd.read_csv(args.alerts)

    results = run_self_audit(df, truth, edges_df, alerts)
    print_report(results)


if __name__ == "__main__":
    main()