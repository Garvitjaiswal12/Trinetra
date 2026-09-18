"""
Stage 4b — Graph-Based Structural Pattern Detection
--------------------------------------------------------
Tabular anomaly detection (Stage 4a) catches individual transactions that
LOOK statistically weird. But some laundering typologies -- especially
mixing -- are invisible transaction-by-transaction; they're only visible
as a SHAPE in the graph. This script explicitly searches for five known
typologies using graph structure + timing, and produces a per-wallet
suspicion score with a plain-language reason for each.

Patterns detected (rule-based on graph structure -- explainable by design):
    1. fan_out_structuring : one wallet source-funds many outgoing tx in a short window
    2. fan_in_consolidation: many distinct wallets feed into one wallet in a short window
    3. mixing               : single transaction with many inputs AND many outputs (pooling)
    4. peeling_chain        : a wallet-to-wallet chain of >=4 hops, each hop peeling off a small amount
    5. ip_cycling           : a wallet's transactions are broadcast from many distinct IPs in a short window

Usage:
    python3 graph_clustering.py <cleaned_transactions.csv> [--out wallet_pattern_scores.csv]
"""

import argparse
from collections import defaultdict

import networkx as nx
import pandas as pd


def split_list(cell, cast=str):
    if pd.isna(cell) or cell == "":
        return []
    return [cast(x) for x in str(cell).split("|")]


def load_cleaned(path):
    df = pd.read_csv(path)
    df["input_addresses"] = df["input_addresses"].apply(lambda c: split_list(c, str))
    df["output_addresses"] = df["output_addresses"].apply(lambda c: split_list(c, str))
    df["input_amounts"] = df["input_amounts"].apply(lambda c: split_list(c, float))
    df["output_amounts"] = df["output_amounts"].apply(lambda c: split_list(c, float))
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


# ----------------------------
# PATTERN 1: FAN-OUT STRUCTURING
# One wallet appears as sole input across many transactions in a short window
# ----------------------------
def detect_fanout(df, window_hours=6, min_tx=8):
    flags = defaultdict(list)
    wallet_tx_times = defaultdict(list)

    for _, row in df.iterrows():
        if len(row["input_addresses"]) == 1:
            wallet_tx_times[row["input_addresses"][0]].append(row["timestamp"])

    for wallet, times in wallet_tx_times.items():
        times = sorted(times)
        for i in range(len(times)):
            window_end = times[i] + pd.Timedelta(hours=window_hours)
            count_in_window = sum(1 for t in times[i:] if t <= window_end)
            if count_in_window >= min_tx:
                flags[wallet].append(
                    f"fan_out_structuring: {count_in_window} outgoing transactions within {window_hours}h"
                )
                break
    return flags


# ----------------------------
# PATTERN 2: FAN-IN CONSOLIDATION
# Many distinct wallets send to one wallet within a short window
# ----------------------------
def detect_fanin(df, window_hours=72, min_sources=10, structuring_cv_threshold=0.12):
    flags = defaultdict(list)
    wallet_incoming = defaultdict(list)  # collector -> list of (timestamp, source_wallet, amount)

    for _, row in df.iterrows():
        sources = row["input_addresses"]
        for out_idx, out_addr in enumerate(row["output_addresses"]):
            amt = row["output_amounts"][out_idx] if out_idx < len(row["output_amounts"]) else 0.0
            for src in sources:
                if src != out_addr:
                    wallet_incoming[out_addr].append((row["timestamp"], src, amt))

    for wallet, events in wallet_incoming.items():
        events.sort(key=lambda x: x[0])
        for i in range(len(events)):
            window_end = events[i][0] + pd.Timedelta(hours=window_hours)
            window_events = [(t, src, amt) for t, src, amt in events[i:] if t <= window_end]
            sources_in_window = {src for t, src, amt in window_events}
            if len(sources_in_window) >= min_sources:
                flags[wallet].append(
                    f"fan_in_consolidation: {len(sources_in_window)} distinct wallets funneled in within {window_hours}h"
                )
                # Structuring signal: real laundering funnels often cluster
                # amounts tightly near a threshold (to stay under reporting
                # limits), unlike ordinary collection which has natural,
                # high-variance deposit sizes. Low coefficient of variation
                # here is a genuine, non-labeled distinguishing feature.
                amounts = pd.Series([amt for _, _, amt in window_events if amt])
                if len(amounts) >= 5 and amounts.mean() > 0:
                    cv = amounts.std() / amounts.mean()
                    if cv <= structuring_cv_threshold:
                        flags[wallet].append(
                            f"fan_in_consolidation: incoming amounts unusually uniform "
                            f"(cv={cv:.3f}) -- consistent with structuring"
                        )
                break
    return flags


# ----------------------------
# PATTERN 3: MIXING
# Single transaction with many inputs AND many outputs (pooling/tumbling)
# ----------------------------
def detect_mixing(df, min_inputs=8, min_outputs=8):
    flags = defaultdict(list)
    mixing_txs = df[(df["n_inputs"] >= min_inputs) & (df["n_outputs"] >= min_outputs)]

    for _, row in mixing_txs.iterrows():
        note = f"mixing: involved in a pooled transaction with {row['n_inputs']} inputs / {row['n_outputs']} outputs"
        for addr in row["input_addresses"] + row["output_addresses"]:
            flags[addr].append(note)
    return flags


# ----------------------------
# PATTERN 4: PEELING CHAIN
# A chain of wallet -> wallet hops, each peeling off a small amount, length >= min_hops
# ----------------------------
def detect_peeling_chain(df, min_hops=4):
    flags = defaultdict(list)

    # Build a simple directed wallet->wallet graph where an edge exists if
    # a wallet's tx output largely funds the next wallet (the "remainder" leg)
    G = nx.DiGraph()
    for _, row in df.iterrows():
        if len(row["input_addresses"]) == 1 and len(row["output_addresses"]) == 2:
            src = row["input_addresses"][0]
            # The larger output is treated as the "remainder" continuing the chain
            outs = list(zip(row["output_addresses"], row["output_amounts"]))
            outs.sort(key=lambda x: x[1], reverse=True)
            remainder_wallet = outs[0][0]
            if remainder_wallet != src:
                G.add_edge(src, remainder_wallet, timestamp=row["timestamp"])

    # Find long simple paths (chains) — walk from each node with in-degree 0 (chain start)
    visited_in_chain = set()
    for node in G.nodes():
        if G.in_degree(node) == 0 and G.out_degree(node) >= 1:
            path = [node]
            current = node
            while True:
                successors = list(G.successors(current))
                if len(successors) != 1:
                    break
                nxt = successors[0]
                if nxt in path:  # avoid cycles
                    break
                path.append(nxt)
                current = nxt
            if len(path) >= min_hops:
                for w in path:
                    if w not in visited_in_chain:
                        flags[w].append(f"peeling_chain: part of a {len(path)}-hop wallet chain")
                        visited_in_chain.add(w)
    return flags


# ----------------------------
# PATTERN 5: IP CYCLING
# A wallet's transactions are broadcast from many distinct IPs in a short window
# ----------------------------
def detect_ip_cycling(df, window_hours=2, min_ips=4):
    flags = defaultdict(list)
    wallet_ip_events = defaultdict(list)  # wallet -> list of (timestamp, ip)

    for _, row in df.iterrows():
        for addr in row["input_addresses"]:
            wallet_ip_events[addr].append((row["timestamp"], row["src_ip"]))

    for wallet, events in wallet_ip_events.items():
        events.sort(key=lambda x: x[0])
        for i in range(len(events)):
            window_end = events[i][0] + pd.Timedelta(hours=window_hours)
            ips_in_window = {ip for t, ip in events[i:] if t <= window_end}
            if len(ips_in_window) >= min_ips:
                flags[wallet].append(
                    f"ip_cycling: broadcast from {len(ips_in_window)} distinct IPs within {window_hours}h"
                )
                break
    return flags


# ----------------------------
# COMBINE ALL PATTERNS INTO A WALLET-LEVEL SCORE
# ----------------------------
def combine_flags(*flag_dicts):
    all_wallets = set()
    for fd in flag_dicts:
        all_wallets.update(fd.keys())

    rows = []
    for wallet in all_wallets:
        reasons = []
        pattern_types = set()
        for fd in flag_dicts:
            for reason in fd.get(wallet, []):
                reasons.append(reason)
                pattern_types.add(reason.split(":")[0])

        # Simple explainable scoring: more distinct pattern types + more total flags = higher score
        score = min(100, len(pattern_types) * 35 + len(reasons) * 5)

        rows.append({
            "wallet": wallet,
            "graph_suspicion_score": score,
            "n_patterns_matched": len(pattern_types),
            "matched_patterns": ", ".join(sorted(pattern_types)),
            "reasons": "; ".join(sorted(set(reasons))[:5]),  # cap for readability
        })

    return pd.DataFrame(rows).sort_values("graph_suspicion_score", ascending=False)


def main():
    parser = argparse.ArgumentParser(description="Detect structural laundering patterns in the wallet graph.")
    parser.add_argument("input_file", help="Path to cleaned_transactions.csv (Stage 2 output)")
    parser.add_argument("--out", default="wallet_pattern_scores.csv", help="Output CSV path")
    args = parser.parse_args()

    print(f"Loading: {args.input_file}")
    df = load_cleaned(args.input_file)
    print(f"  Transactions loaded: {len(df)}")

    print("Detecting fan-out structuring...")
    fanout_flags = detect_fanout(df)
    print(f"  Wallets flagged: {len(fanout_flags)}")

    print("Detecting fan-in consolidation...")
    fanin_flags = detect_fanin(df)
    print(f"  Wallets flagged: {len(fanin_flags)}")

    print("Detecting mixing...")
    mixing_flags = detect_mixing(df)
    print(f"  Wallets flagged: {len(mixing_flags)}")

    print("Detecting peeling chains...")
    peeling_flags = detect_peeling_chain(df)
    print(f"  Wallets flagged: {len(peeling_flags)}")

    print("Detecting IP cycling...")
    ip_flags = detect_ip_cycling(df)
    print(f"  Wallets flagged: {len(ip_flags)}")

    print("\nCombining pattern flags into wallet-level scores...")
    result = combine_flags(fanout_flags, fanin_flags, mixing_flags, peeling_flags, ip_flags)
    result.to_csv(args.out, index=False)

    print(f"\nTotal unique wallets flagged by at least one pattern: {len(result)}")
    print(f"\nTop 10 most suspicious wallets:")
    for _, row in result.head(10).iterrows():
        print(f"  {row['wallet'][:16]}...  score={row['graph_suspicion_score']}  patterns=[{row['matched_patterns']}]")

    print(f"\nScores written to: {args.out}")


if __name__ == "__main__":
    main()
