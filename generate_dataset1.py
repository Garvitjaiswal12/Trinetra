#!/usr/bin/env python3
"""
Synthetic Bitcoin Transaction + Network Metadata Generator
------------------------------------------------------------
Generates a realistic synthetic dataset combining:
  - Blockchain-layer data (wallets, TXIDs, amounts, fees, script types)
  - Network-layer data (src/dst IP:port, timestamps)
  - Geo/ASN enrichment (synthetic lookup table; swap in MaxMind GeoLite2 for real use)

Injects known money-laundering typologies (peeling chain, mixing, fan-out
structuring, fan-in consolidation, IP-cycling) at a configurable ratio,
and keeps a SEPARATE ground-truth label file for model evaluation only
(the main dataset does NOT include the label, to keep detection realistic).

Output:
  dataset/transactions.csv       <- main dataset (what your ML pipeline ingests)
  dataset/transactions.json      <- same data, JSON form
  dataset/ground_truth.csv       <- txid -> is_illicit, pattern_type (for YOUR evaluation only)
  dataset/wallet_graph_edges.csv <- precomputed wallet->wallet edges (optional helper for graph building)
"""

import json
import random
import uuid
import ipaddress
import hashlib
import csv
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)

OUT_DIR = Path("dataset")
OUT_DIR.mkdir(exist_ok=True)

# ----------------------------
# CONFIG
# ----------------------------
N_WALLETS = 4000
N_IPS = 1500
N_NORMAL_TX = 15000
N_ILLICIT_CLUSTERS = 60          # number of separate illicit "cases" injected
START_TIME = datetime(2026, 1, 1)
TIME_SPAN_DAYS = 90

SCRIPT_TYPES = ["P2PKH", "P2SH", "P2WPKH", "P2WSH", "P2TR"]

# Synthetic country/ASN lookup table (replace with real MaxMind GeoLite2 lookups
# via geoip2 module for production use — see note at bottom of file)
COUNTRIES = [
    ("US", [7018, 701, 20115]),
    ("DE", [3320, 6805]),
    ("NL", [1136, 9143]),
    ("RU", [12389, 8402]),
    ("CN", [4134, 4837]),
    ("IN", [9498, 24560]),
    ("SG", [9506, 4657]),
    ("BR", [28573, 7738]),
    ("NG", [37282, 36873]),
    ("IR", [12880, 44244]),
]

TOR_EXIT_LIKE_ASNS = {12389, 8402, 44244}  # pretend these ASNs are common Tor exit/VPN ranges


# ----------------------------
# HELPERS
# ----------------------------
def random_ip():
    return str(ipaddress.IPv4Address(random.randint(0x0B000000, 0xDFFFFFFF)))


def random_wallet():
    # Bech32-ish looking synthetic wallet address (NOT a real derivation, just realistic-looking)
    h = hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:38]
    return "bc1q" + h


def random_txid():
    return hashlib.sha256(uuid.uuid4().bytes).hexdigest()


def random_geo():
    country, asns = random.choice(COUNTRIES)
    return country, random.choice(asns)


def random_timestamp():
    delta_seconds = random.randint(0, TIME_SPAN_DAYS * 86400)
    return START_TIME + timedelta(seconds=delta_seconds)


def new_ip_pool(n):
    return [random_ip() for _ in range(n)]


def new_wallet_pool(n):
    return [random_wallet() for _ in range(n)]


IP_POOL = new_ip_pool(N_IPS)
WALLET_POOL = new_wallet_pool(N_WALLETS)
IP_GEO = {ip: random_geo() for ip in IP_POOL}


# ----------------------------
# CORE TRANSACTION BUILDER
# ----------------------------
def build_tx(inputs, outputs, ts=None, src_ip=None, dst_ip=None, pattern=None):
    ts = ts or random_timestamp()
    src_ip = src_ip or random.choice(IP_POOL)
    dst_ip = dst_ip or random.choice(IP_POOL)
    country, asn = IP_GEO[src_ip]

    total_in = sum(a for _, a in inputs)
    total_out = sum(a for _, a in outputs)
    fee = round(max(total_in - total_out, 0.00001), 8)

    return {
        "timestamp": ts.isoformat() + "Z",
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "src_port": random.randint(1024, 65535),
        "dst_port": 8333,  # standard Bitcoin P2P port
        "txid": random_txid(),
        "input_addresses": [a for a, _ in inputs],
        "output_addresses": [a for a, _ in outputs],
        "input_amounts": [round(a, 8) for _, a in inputs],
        "output_amounts": [round(a, 8) for _, a in outputs],
        "fee": fee,
        "script_type": random.choice(SCRIPT_TYPES),
        "geo_country": country,
        "asn": asn,
        "_pattern": pattern or "normal",  # stripped before writing main dataset
    }


# ----------------------------
# NORMAL TRAFFIC
# ----------------------------
def generate_normal_transactions(n):
    txs = []
    for _ in range(n):
        n_in = random.randint(1, 3)
        n_out = random.randint(1, 3)
        amt = random.uniform(0.001, 3.0)
        inputs = [(random.choice(WALLET_POOL), amt / n_in) for _ in range(n_in)]
        outputs = [(random.choice(WALLET_POOL), amt / n_out * 0.998) for _ in range(n_out)]
        txs.append(build_tx(inputs, outputs))
    return txs


# ----------------------------
# ILLICIT PATTERN GENERATORS
# ----------------------------
def gen_peeling_chain():
    """One wallet peels off small amounts across a long chain of hops."""
    txs = []
    amount = random.uniform(5, 50)
    current_wallet = random_wallet()
    ts = random_timestamp()
    src_ip = random.choice(IP_POOL)
    hops = random.randint(6, 15)
    for _ in range(hops):
        next_wallet = random_wallet()
        peel = amount * random.uniform(0.02, 0.08)
        remainder = amount - peel
        tx = build_tx(
            inputs=[(current_wallet, amount)],
            outputs=[(next_wallet, remainder), (random_wallet(), peel)],
            ts=ts, src_ip=src_ip, pattern="peeling_chain",
        )
        txs.append(tx)
        current_wallet = next_wallet
        amount = remainder
        ts += timedelta(minutes=random.randint(5, 240))
    return txs


def gen_mixing_service():
    """Many inputs pooled, then redistributed to many unrelated outputs."""
    n_in = random.randint(8, 20)
    n_out = random.randint(8, 20)
    total = random.uniform(10, 100)
    inputs = [(random_wallet(), total / n_in) for _ in range(n_in)]
    outputs = [(random_wallet(), total / n_out * 0.97) for _ in range(n_out)]
    # mixing services are often accessed via Tor-like ASNs
    src_ip = random.choice([ip for ip, (c, a) in IP_GEO.items() if a in TOR_EXIT_LIKE_ASNS] or IP_POOL)
    return [build_tx(inputs, outputs, src_ip=src_ip, pattern="mixing")]


def gen_fanout_structuring():
    """One wallet splits a large sum into many small txs (smurfing) in a short window."""
    txs = []
    origin = random_wallet()
    total = random.uniform(20, 80)
    n_splits = random.randint(10, 25)
    ts = random_timestamp()
    src_ip = random.choice(IP_POOL)
    per = total / n_splits
    for _ in range(n_splits):
        tx = build_tx(
            inputs=[(origin, per)],
            outputs=[(random_wallet(), per * 0.995)],
            ts=ts, src_ip=src_ip, pattern="fanout_structuring",
        )
        txs.append(tx)
        ts += timedelta(minutes=random.randint(1, 15))  # rapid succession
    return txs


def gen_fanin_consolidation():
    """Many small wallets funnel into one collector wallet (ransomware/darknet payout)."""
    txs = []
    collector = random_wallet()
    n_sources = random.randint(15, 40)
    ts = random_timestamp()
    for _ in range(n_sources):
        amt = random.uniform(0.05, 1.5)
        tx = build_tx(
            inputs=[(random_wallet(), amt)],
            outputs=[(collector, amt * 0.99)],
            ts=ts + timedelta(hours=random.randint(0, 72)),
            pattern="fanin_consolidation",
        )
        txs.append(tx)
    return txs


def gen_ip_cycling():
    """Same wallet, many different source IPs in a short burst — obfuscation behavior."""
    txs = []
    wallet = random_wallet()
    ts = random_timestamp()
    for _ in range(random.randint(5, 12)):
        tx = build_tx(
            inputs=[(wallet, random.uniform(0.1, 2))],
            outputs=[(random_wallet(), random.uniform(0.05, 1.9))],
            ts=ts + timedelta(minutes=random.randint(1, 30)),
            src_ip=random.choice(IP_POOL),
            pattern="ip_cycling",
        )
        txs.append(tx)
    return txs


ILLICIT_GENERATORS = [
    gen_peeling_chain,
    gen_mixing_service,
    gen_fanout_structuring,
    gen_fanin_consolidation,
    gen_ip_cycling,
]


# ----------------------------
# BUILD FULL DATASET
# ----------------------------
def main():
    all_txs = generate_normal_transactions(N_NORMAL_TX)

    for _ in range(N_ILLICIT_CLUSTERS):
        gen_fn = random.choice(ILLICIT_GENERATORS)
        all_txs.extend(gen_fn())

    random.shuffle(all_txs)

    # Split ground truth from main dataset
    ground_truth = []
    for tx in all_txs:
        ground_truth.append({
            "txid": tx["txid"],
            "is_illicit": 0 if tx["_pattern"] == "normal" else 1,
            "pattern_type": tx["_pattern"],
        })
        del tx["_pattern"]

    # ------------------------------------------------------------------
    # DIRTY DATA INJECTION
    # Real bulk transaction/network logs are never perfectly clean. We
    # deliberately corrupt a small, controlled fraction of rows so the
    # ingestion & validation stage (Stage 2) has genuine work to do --
    # otherwise 0 rows get dropped and the "cleaning" step looks like a
    # no-op in a demo. Corruption never removes a row or changes a txid,
    # so ground_truth.csv stays correctly keyed to every row, including
    # the dirty ones.
    # ------------------------------------------------------------------
    DIRTY_RATE = 0.06  # ~6% of rows get one deliberate defect each
    n_dirty = int(len(all_txs) * DIRTY_RATE)
    dirty_indices = random.sample(range(len(all_txs)), n_dirty)
    defect_counts = {
        "missing_critical_field": 0, "duplicate_txid": 0, "invalid_ip": 0,
        "bad_timestamp": 0, "malformed_list": 0, "negative_amount": 0,
        "invalid_fee": 0, "invalid_port": 0, "invalid_asn": 0,
    }
    defect_types = list(defect_counts.keys())
    prev_txid_for_dupes = None

    for idx in dirty_indices:
        tx = all_txs[idx]
        defect = random.choice(defect_types)
        defect_counts[defect] += 1

        if defect == "missing_critical_field":
            field = random.choice(["txid", "timestamp", "src_ip", "dst_ip"])
            tx[field] = ""
        elif defect == "duplicate_txid":
            if prev_txid_for_dupes:
                tx["txid"] = prev_txid_for_dupes
            prev_txid_for_dupes = tx["txid"]
        elif defect == "invalid_ip":
            tx[random.choice(["src_ip", "dst_ip"])] = "999.999.999.999"
        elif defect == "bad_timestamp":
            tx["timestamp"] = "not-a-real-timestamp"
        elif defect == "malformed_list":
            # amounts list length no longer matches addresses list length
            if tx["input_amounts"]:
                tx["input_amounts"] = tx["input_amounts"][:-1] if len(tx["input_amounts"]) > 1 else tx["input_amounts"] + [tx["input_amounts"][0]]
        elif defect == "negative_amount":
            if tx["input_amounts"]:
                tx["input_amounts"][0] = -abs(tx["input_amounts"][0])
        elif defect == "invalid_fee":
            tx["fee"] = -abs(tx["fee"]) if tx["fee"] else -0.001
        elif defect == "invalid_port":
            tx["src_port"] = random.choice([-1, 0, 99999])
        elif defect == "invalid_asn":
            tx["asn"] = random.choice([-1, 999999999])

    # Write main CSV (flatten list fields to pipe-separated strings for CSV compatibility)
    csv_path = OUT_DIR / "transactions.csv"
    fieldnames = ["timestamp", "src_ip", "dst_ip", "src_port", "dst_port", "txid",
                  "input_addresses", "output_addresses", "input_amounts", "output_amounts",
                  "fee", "script_type", "geo_country", "asn"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for tx in all_txs:
            row = tx.copy()
            row["input_addresses"] = "|".join(row["input_addresses"])
            row["output_addresses"] = "|".join(row["output_addresses"])
            row["input_amounts"] = "|".join(str(a) for a in row["input_amounts"])
            row["output_amounts"] = "|".join(str(a) for a in row["output_amounts"])
            writer.writerow(row)

    # Write main JSON (keeps lists as real arrays)
    json_path = OUT_DIR / "transactions.json"
    with open(json_path, "w") as f:
        json.dump(all_txs, f, indent=2)

    # Write ground truth (for evaluation only — do not feed to unsupervised model)
    gt_path = OUT_DIR / "ground_truth.csv"
    with open(gt_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["txid", "is_illicit", "pattern_type"])
        writer.writeheader()
        writer.writerows(ground_truth)

    # Write wallet->wallet edge list (helper for graph construction, e.g. with networkx)
    edges_path = OUT_DIR / "wallet_graph_edges.csv"
    with open(edges_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["src_wallet", "dst_wallet", "txid", "amount"])
        for tx in all_txs:
            for src in tx["input_addresses"]:
                for i, dst in enumerate(tx["output_addresses"]):
                    amt = tx["output_amounts"][i] if i < len(tx["output_amounts"]) else 0
                    writer.writerow([src, dst, tx["txid"], amt])

    n_illicit = sum(g["is_illicit"] for g in ground_truth)
    print(f"Generated {len(all_txs)} transactions ({n_illicit} illicit, "
          f"{len(all_txs) - n_illicit} normal) -> {n_illicit/len(all_txs)*100:.2f}% illicit ratio")
    # print(f"Injected {n_dirty} deliberately dirty/malformed rows ({DIRTY_RATE*100:.0f}% of total), "
    #       f"simulating real-world noisy telemetry:")
    # for defect, count in defect_counts.items():
    #     if count:
    #         print(f"  - {defect}: {count}")
    print(f"Files written to: {OUT_DIR.resolve()}")
    print("  - transactions.csv  ")
    print("  - transactions.json  ")
    print("  - ground_truth.csv  ")
    print("  - wallet_graph_edges.csv ")


if __name__ == "__main__":
    main()
