#!/usr/bin/env python3
"""
Stage 4d — Common-Input-Ownership Entity Clustering
---------------------------------------------------------
Real-world Bitcoin forensics heuristic (used by firms like Chainalysis):
if multiple wallet addresses appear together as INPUTS to the same
transaction, they were spent together by one private key holder, meaning
they very likely belong to the SAME real-world entity (person/organization),
even though they look like separate addresses on-chain.

This lets Trinetra score ENTITIES instead of raw addresses -- a more
realistic unit of analysis, since a launderer commonly spreads funds
across many addresses precisely to look like separate actors.

Method: Union-Find (disjoint set) over wallets that co-occur as inputs
in the same transaction. Each resulting set = one inferred entity.

Usage:
    python3 entity_clustering.py <cleaned_transactions.csv> --out wallet_entity_map.csv
"""
import argparse
from collections import defaultdict

import pandas as pd


def split_list(cell, cast=str):
    if pd.isna(cell) or cell == "":
        return []
    return [cast(x) for x in str(cell).split("|")]


def load_cleaned(path):
    df = pd.read_csv(path)
    df["input_addresses"] = df["input_addresses"].apply(lambda c: split_list(c, str))
    return df


class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path compression
            x = self.parent[x]
        return x

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx != ry:
            self.parent[rx] = ry


def build_entities(df, mixing_txids=None, hub_wallets=None):
    """
    mixing_txids: TXIDs flagged as mixing/CoinJoin-like -- excluded because they
    deliberately combine unrelated owners' inputs.

    hub_wallets: wallets that appear as an input across an unusually large number
    of DISTINCT transactions. In real Bitcoin data, this is the signature of a
    custodial service or exchange hot wallet, not a single individual owner --
    real forensics tools exclude these from common-input clustering for the same
    reason. Without this exclusion, one reused wallet can transitively chain
    together many unrelated real-world entities into a false "super-cluster".
    """
    mixing_txids = mixing_txids or set()
    hub_wallets = hub_wallets or set()
    uf = UnionFind()
    multi_input_tx_count = 0
    excluded_mixing = 0
    excluded_hub_links = 0

    for _, row in df.iterrows():
        inputs = [a for a in row["input_addresses"] if a not in hub_wallets]
        if row["txid"] in mixing_txids:
            excluded_mixing += 1
            continue
        if len(row["input_addresses"]) > len(inputs):
            excluded_hub_links += 1
        if len(inputs) > 1:
            multi_input_tx_count += 1
            first = inputs[0]
            for addr in inputs[1:]:
                uf.union(first, addr)

    entity_map = defaultdict(list)
    for wallet in uf.parent:
        root = uf.find(wallet)
        entity_map[root].append(wallet)

    return entity_map, multi_input_tx_count, excluded_mixing, excluded_hub_links


def identify_hub_wallets(df, max_distinct_tx=10):
    """A wallet used as input across more than `max_distinct_tx` different
    transactions is treated as a likely custodial/exchange wallet, not an
    individual owner, and excluded from the clustering step."""
    freq = defaultdict(int)
    for _, row in df.iterrows():
        for addr in set(row["input_addresses"]):
            freq[addr] += 1
    return {w for w, c in freq.items() if c > max_distinct_tx}


def expand_entity_local(df, seed_wallet, mixing_txids=None, hub_wallets=None, max_hops=3):
    """
    Practical, artifact-free version of entity clustering: instead of clustering
    the ENTIRE graph (which on a small synthetic wallet pool collapses into one
    giant false super-cluster via random-graph percolation -- see README notes),
    expand OUTWARD from one seed wallet only as far as genuine common-input links
    reach, capped at max_hops. This mirrors the real investigative workflow --
    "what else does THIS flagged wallet's owner likely control?" -- and is what
    the dashboard's per-wallet drill-down calls, rather than a global pre-computed map.
    """
    mixing_txids = mixing_txids or set()
    hub_wallets = hub_wallets or set()

    frontier = {seed_wallet}
    visited = {seed_wallet}
    for _ in range(max_hops):
        next_frontier = set()
        for _, row in df.iterrows():
            if row["txid"] in mixing_txids:
                continue
            inputs = [a for a in row["input_addresses"] if a not in hub_wallets]
            if len(inputs) > 1 and any(a in frontier for a in inputs):
                next_frontier.update(a for a in inputs if a not in visited)
        if not next_frontier:
            break
        visited.update(next_frontier)
        frontier = next_frontier

    return visited


def main():
    parser = argparse.ArgumentParser(description="Cluster wallets into entities via common-input-ownership.")
    parser.add_argument("input_file", help="Path to cleaned_transactions.csv")
    parser.add_argument("--seed-wallet", default=None,
                         help="If given, run LOCAL expansion from this one wallet only (recommended -- "
                              "see notes about global clustering on small synthetic wallet pools)")
    parser.add_argument("--max-hops", type=int, default=1,
                         help="Max hops for local expansion (default 1 = direct co-spend only, the "
                              "defensible standard reading of this heuristic). Values >1 risk the same "
                              "'closure problem' super-cluster explosion documented in real Bitcoin "
                              "forensics literature -- increase with caution and inspect the result size.")
    parser.add_argument("--out", default="wallet_entity_map.csv", help="Output wallet->entity mapping CSV")
    args = parser.parse_args()

    print(f"Loading: {args.input_file}")
    df = load_cleaned(args.input_file)
    print(f"  Transactions loaded: {len(df)}")

    mixing_txids = set(df[(df["n_inputs"] >= 8) & (df["n_outputs"] >= 8)]["txid"])
    print(f"  Transactions identified as mixing-like (excluded from clustering): {len(mixing_txids)}")

    hub_wallets = identify_hub_wallets(df, max_distinct_tx=10)
    print(f"  Wallets identified as likely custodial/exchange hubs (excluded from clustering): {len(hub_wallets)}")

    if args.seed_wallet:
        print(f"\nRunning LOCAL entity expansion from seed wallet: {args.seed_wallet}")
        entity = expand_entity_local(df, args.seed_wallet, mixing_txids, hub_wallets, args.max_hops)
        print(f"Inferred entity size: {len(entity)} wallet(s) likely controlled by the same real-world owner")
        result = pd.DataFrame({"wallet": sorted(entity), "entity_id": "seed_" + args.seed_wallet[:12]})
        result.to_csv(args.out, index=False)
        print(f"Entity map written to: {args.out}")
        return

    print("\nBuilding entity clusters via common-input-ownership (GLOBAL mode)...")
    print("NOTE: on a small synthetic wallet pool this commonly collapses into one giant")
    print("      component due to random-graph percolation -- use --seed-wallet for a")
    print("      practical, artifact-free result scoped to one investigation instead.")
    entity_map, multi_input_count, excluded_mixing, excluded_hub_links = build_entities(df, mixing_txids, hub_wallets)
    print(f"  Multi-input transactions used for clustering: {multi_input_count}")
    print(f"  Transactions excluded (mixing-like): {excluded_mixing}")
    print(f"  Transactions where a hub wallet was excluded from its input list: {excluded_hub_links}")

    sorted_entities = sorted(entity_map.items(), key=lambda x: -len(x[1]))
    rows = []
    for i, (root, wallets) in enumerate(sorted_entities):
        entity_id = f"entity_{i:05d}"
        for w in wallets:
            rows.append({"wallet": w, "entity_id": entity_id, "entity_size": len(wallets)})
    result = pd.DataFrame(rows)
    result.to_csv(args.out, index=False)

    print(f"\nTotal wallets clustered: {len(result)}")
    print(f"Total entities found: {len(sorted_entities)}")
    print(f"\nEntity map written to: {args.out}")


if __name__ == "__main__":
    main()
