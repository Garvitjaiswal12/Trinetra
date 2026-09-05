#!/usr/bin/env python3
"""
Stage 3 — Entity/Transaction Graph Construction
-------------------------------------------------
Builds a heterogeneous graph linking three entity types:
    IP        -- an IP address that broadcast a transaction
    Wallet     -- a Bitcoin address (input or output of a transaction)
    Transaction -- a single Bitcoin transaction (TXID)

Edges:
    IP        --broadcasts-->     Transaction
    Wallet     --input_to-->      Transaction
    Transaction --output_to-->    Wallet

This graph view is what makes structural laundering patterns visible
(peeling chains, fan-in/fan-out, mixing) that a flat table hides.

Usage:
    python3 build_graph.py <cleaned_transactions.csv> [--out graph.graphml]

Output:
    - <out>            : the full graph in GraphML format (readable by Gephi, etc.)
    - wallet_stats.csv  : per-wallet summary features (useful directly as ML features in Stage 4)
"""

import argparse
import ast
from pathlib import Path

import networkx as nx
import pandas as pd


def split_list(cell, cast=str):
    """Cleaned CSV stores list fields as pipe-separated strings."""
    if pd.isna(cell) or cell == "":
        return []
    return [cast(x) for x in str(cell).split("|")]


def load_cleaned(path):
    df = pd.read_csv(path)
    df["input_addresses"] = df["input_addresses"].apply(lambda c: split_list(c, str))
    df["output_addresses"] = df["output_addresses"].apply(lambda c: split_list(c, str))
    df["input_amounts"] = df["input_amounts"].apply(lambda c: split_list(c, float))
    df["output_amounts"] = df["output_amounts"].apply(lambda c: split_list(c, float))
    return df


def build_graph(df):
    G = nx.MultiDiGraph()

    for _, row in df.iterrows():
        txid = row["txid"]
        ts = row["timestamp"]

        # Transaction node
        G.add_node(
            txid, node_type="transaction", timestamp=ts,
            fee=row["fee"], script_type=row["script_type"],
            geo_country=row["geo_country"], asn=row["asn"],
            n_inputs=row["n_inputs"], n_outputs=row["n_outputs"],
        )

        # IP node + broadcast edge
        src_ip = row["src_ip"]
        G.add_node(src_ip, node_type="ip")
        G.add_edge(src_ip, txid, edge_type="broadcasts", timestamp=ts)

        # Wallet input edges: wallet -> transaction
        for addr, amt in zip(row["input_addresses"], row["input_amounts"]):
            G.add_node(addr, node_type="wallet")
            G.add_edge(addr, txid, edge_type="input_to", amount=amt, timestamp=ts)

        # Wallet output edges: transaction -> wallet
        for addr, amt in zip(row["output_addresses"], row["output_amounts"]):
            G.add_node(addr, node_type="wallet")
            G.add_edge(txid, addr, edge_type="output_to", amount=amt, timestamp=ts)

    return G


def compute_wallet_stats(G, df):
    """
    Per-wallet features useful directly for Stage 4 ML:
        - n_tx_in / n_tx_out : how many transactions this wallet appears as input/output of
        - total_received / total_sent
        - n_unique_counterparty_ips : how many distinct source IPs are linked to this wallet's txs
        - degree : total graph connections
    """
    wallet_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "wallet"]
    stats = []

    for wallet in wallet_nodes:
        out_edges = list(G.out_edges(wallet, data=True))   # wallet -> tx (wallet as input)
        in_edges = list(G.in_edges(wallet, data=True))      # tx -> wallet (wallet as output)

        total_sent = sum(d.get("amount", 0) for _, _, d in out_edges if d.get("edge_type") == "input_to")
        total_received = sum(d.get("amount", 0) for _, _, d in in_edges if d.get("edge_type") == "output_to")

        # Find transactions this wallet touched, then find the source IPs of those transactions
        touched_txids = {t for _, t, d in out_edges if d.get("edge_type") == "input_to"} | \
                         {t for t, _, d in in_edges if d.get("edge_type") == "output_to"}
        counterparty_ips = set()
        for txid in touched_txids:
            for ip, _, d in G.in_edges(txid, data=True):
                if d.get("edge_type") == "broadcasts":
                    counterparty_ips.add(ip)

        stats.append({
            "wallet": wallet,
            "n_tx_as_input": len(out_edges),
            "n_tx_as_output": len(in_edges),
            "total_sent": total_sent,
            "total_received": total_received,
            "n_unique_counterparty_ips": len(counterparty_ips),
            "degree": G.degree(wallet),
        })

    return pd.DataFrame(stats)


def print_summary(G):
    node_types = pd.Series([d.get("node_type") for _, d in G.nodes(data=True)]).value_counts()
    edge_types = pd.Series([d.get("edge_type") for _, _, d in G.edges(data=True)]).value_counts()

    print("\n=== Graph Summary ===")
    print(f"Total nodes: {G.number_of_nodes()}")
    for t, c in node_types.items():
        print(f"  {t}: {c}")
    print(f"Total edges: {G.number_of_edges()}")
    for t, c in edge_types.items():
        print(f"  {t}: {c}")

    # Top wallets by degree — a quick sanity view of the busiest entities
    wallet_degrees = [(n, G.degree(n)) for n, d in G.nodes(data=True) if d.get("node_type") == "wallet"]
    wallet_degrees.sort(key=lambda x: x[1], reverse=True)
    print("\nTop 5 most-connected wallets (possible hubs — mixers, collectors, exchanges):")
    for wallet, deg in wallet_degrees[:5]:
        print(f"  {wallet}  (degree={deg})")


def main():
    parser = argparse.ArgumentParser(description="Build IP-Wallet-Transaction graph from cleaned data.")
    parser.add_argument("input_file", help="Path to cleaned_transactions.csv (Stage 2 output)")
    parser.add_argument("--out", default="graph.graphml", help="Output GraphML path")
    parser.add_argument("--wallet-stats-out", default="wallet_stats.csv", help="Output wallet features CSV")
    args = parser.parse_args()

    print(f"Loading cleaned data: {args.input_file}")
    df = load_cleaned(args.input_file)
    print(f"  Transactions loaded: {len(df)}")

    print("Building graph...")
    G = build_graph(df)
    print_summary(G)

    print(f"\nComputing per-wallet statistics...")
    wallet_stats = compute_wallet_stats(G, df)
    wallet_stats.to_csv(args.wallet_stats_out, index=False)
    print(f"Wallet stats written to: {args.wallet_stats_out} ({len(wallet_stats)} wallets)")

    # GraphML requires simple attribute types; drop non-serializable ones (Timestamps -> str)
    G_export = G.copy()
    for _, d in G_export.nodes(data=True):
        if "timestamp" in d:
            d["timestamp"] = str(d["timestamp"])
    for _, _, d in G_export.edges(data=True):
        if "timestamp" in d:
            d["timestamp"] = str(d["timestamp"])

    nx.write_graphml(G_export, args.out)
    print(f"Graph written to: {args.out}")


if __name__ == "__main__":
    main()
