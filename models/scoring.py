#!/usr/bin/env python3
"""
Stage 4c — Score Combiner
--------------------------------
Merges the two independent detection signals into ONE final, explainable
confidence score per wallet:

    1. Tabular anomaly score  (Stage 4a) -- individual transactions that
       look statistically weird (unusual amounts, fees, timing)
    2. Graph pattern score    (Stage 4b) -- structural laundering typologies
       (fan-out, fan-in, mixing, peeling chains, IP cycling)

These two signals are complementary (see evaluation notes below), so
combining them catches more true positives than either alone, while the
combined "reasons" field keeps every flag fully explainable.

Combination logic (simple, transparent -- not a black box):
    wallet_tabular_score = MAX suspicion_score across all transactions
                            the wallet participated in (as input or output)
    combined_score        = 0.5 * wallet_tabular_score + 0.5 * graph_suspicion_score
    (wallets with signal from only one detector still get a fair score --
     see WEIGHT NOTE below)

Usage:
    python3 scoring.py \\
        --transactions ../ingest/cleaned_transactions.csv \\
        --tx-scores tx_anomaly_scores.csv \\
        --wallet-patterns wallet_pattern_scores.csv \\
        --out final_alerts.csv
"""

import argparse

import pandas as pd


def split_list(cell, cast=str):
    if pd.isna(cell) or cell == "":
        return []
    return [cast(x) for x in str(cell).split("|")]


def load_cleaned(path):
    df = pd.read_csv(path)
    df["input_addresses"] = df["input_addresses"].apply(lambda c: split_list(c, str))
    df["output_addresses"] = df["output_addresses"].apply(lambda c: split_list(c, str))
    return df


def build_wallet_tx_map(df):
    """wallet -> list of txids it participated in (as input or output)."""
    wallet_txids = {}
    for _, row in df.iterrows():
        for addr in row["input_addresses"] + row["output_addresses"]:
            wallet_txids.setdefault(addr, []).append(row["txid"])
    return wallet_txids


def aggregate_tabular_score_per_wallet(wallet_txids, tx_scores_df):
    """For each wallet, take the MAX suspicion score among its transactions,
    plus collect the single most informative reason (from its worst transaction)."""
    tx_score_map = tx_scores_df.set_index("txid")["suspicion_score"].to_dict()
    tx_reason_map = tx_scores_df.set_index("txid")["reason"].to_dict()

    rows = []
    for wallet, txids in wallet_txids.items():
        scores = [tx_score_map.get(t, 0.0) for t in txids]
        if not scores:
            continue
        max_score = max(scores)
        worst_txid = txids[scores.index(max_score)]
        reason = tx_reason_map.get(worst_txid, "")
        rows.append({
            "wallet": wallet,
            "tabular_score": max_score,
            "tabular_reason": f"transaction {worst_txid[:12]}...: {reason}" if reason else "",
            "n_tx_touched": len(txids),
        })
    return pd.DataFrame(rows)


def combine(tabular_df, graph_df, w_tabular=0.5, w_graph=0.5):
    merged = tabular_df.merge(graph_df, on="wallet", how="outer")

    merged["tabular_score"] = merged["tabular_score"].fillna(0.0)
    merged["graph_suspicion_score"] = merged["graph_suspicion_score"].fillna(0.0)
    merged["tabular_reason"] = merged["tabular_reason"].fillna("")
    merged["reasons"] = merged["reasons"].fillna("")
    merged["matched_patterns"] = merged["matched_patterns"].fillna("")
    merged["n_patterns_matched"] = merged["n_patterns_matched"].fillna(0)

    # WEIGHT NOTE: a wallet flagged by BOTH detectors is more credible than one
    # flagged by only one. We apply a small "agreement bonus" on top of the
    # weighted average to reflect that, capped at 100.
    base_score = w_tabular * merged["tabular_score"] + w_graph * merged["graph_suspicion_score"]
    both_flagged = (merged["tabular_score"] > 0) & (merged["graph_suspicion_score"] > 0)
    agreement_bonus = both_flagged.astype(float) * 10
    merged["combined_confidence"] = (base_score + agreement_bonus).clip(upper=100).round(1)

    def build_reason(row):
        parts = []
        if row["tabular_reason"]:
            parts.append(f"[Tabular] {row['tabular_reason']}")
        if row["reasons"]:
            parts.append(f"[Graph] {row['reasons']}")
        return " || ".join(parts)

    merged["combined_reason"] = merged.apply(build_reason, axis=1)
    merged["detected_by"] = merged.apply(
        lambda r: ("both" if r["tabular_score"] > 0 and r["graph_suspicion_score"] > 0
                    else "tabular_only" if r["tabular_score"] > 0
                    else "graph_only"),
        axis=1,
    )

    result = merged[[
        "wallet", "combined_confidence", "detected_by",
        "tabular_score", "graph_suspicion_score", "n_patterns_matched", "matched_patterns",
        "combined_reason",
    ]].sort_values("combined_confidence", ascending=False).reset_index(drop=True)

    result.insert(0, "rank", result.index + 1)
    return result


def main():
    parser = argparse.ArgumentParser(description="Combine tabular + graph detection signals into final ranked alerts.")
    parser.add_argument("--transactions", required=True, help="Path to cleaned_transactions.csv")
    parser.add_argument("--tx-scores", required=True, help="Path to tx_anomaly_scores.csv (Stage 4a output)")
    parser.add_argument("--wallet-patterns", required=True, help="Path to wallet_pattern_scores.csv (Stage 4b output)")
    parser.add_argument("--out", default="final_alerts.csv", help="Output ranked alerts CSV")
    parser.add_argument("--w-tabular", type=float, default=0.5, help="Weight for tabular score")
    parser.add_argument("--w-graph", type=float, default=0.5, help="Weight for graph score")
    args = parser.parse_args()

    print("Loading inputs...")
    df = load_cleaned(args.transactions)
    tx_scores_df = pd.read_csv(args.tx_scores)
    graph_df = pd.read_csv(args.wallet_patterns)
    print(f"  Transactions: {len(df)}  |  Tx scores: {len(tx_scores_df)}  |  Graph-flagged wallets: {len(graph_df)}")

    print("Mapping wallets to their transactions...")
    wallet_txids = build_wallet_tx_map(df)
    print(f"  Unique wallets: {len(wallet_txids)}")

    print("Aggregating tabular scores to wallet level...")
    tabular_df = aggregate_tabular_score_per_wallet(wallet_txids, tx_scores_df)

    print(f"Combining scores (weights: tabular={args.w_tabular}, graph={args.w_graph})...")
    final = combine(tabular_df, graph_df, args.w_tabular, args.w_graph)
    final.to_csv(args.out, index=False)

    print(f"\n=== Final Alert Summary ===")
    print(f"Total wallets scored: {len(final)}")
    print(final["detected_by"].value_counts().to_string())

    print(f"\nTop 10 ranked alerts:")
    for _, row in final.head(10).iterrows():
        print(f"  #{row['rank']}  {row['wallet'][:16]}...  confidence={row['combined_confidence']}  "
              f"(detected_by={row['detected_by']}, patterns=[{row['matched_patterns']}])")

    print(f"\nFinal ranked alerts written to: {args.out}")


if __name__ == "__main__":
    main()
