# TRINETRA (त्रिनेत्र)

### *The third eye — an offline AI system for monitoring, correlating and prioritising suspicious Bitcoin activity.*

---

## 🏆 SIH 2026 — Team & Problem Statement

**Team:** Quantum Minds  
**Problem Statement ID:** 26146  
**Problem Statement Title:** AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic  
**Organization:** National Technical Research Organisation (NTRO)  
**Category:** Software

---

## 🔍 What is Trinetra?

Bitcoin transactions are public, but following suspicious money movement across thousands of transactions is far from simple.

**Trinetra** is an offline investigative pipeline designed to turn raw Bitcoin transaction and network metadata into a clear, ranked set of investigative leads.

It correlates two views of the same activity:

- **Network layer** — who communicated with whom, through which IP/port, and when.
- **Blockchain layer** — which wallets and transactions interacted, including amounts and transaction structure.
- **AI correlation layer** — combines evidence from both views instead of relying on a single detector.

The result is an interactive investigation dashboard where suspicious wallets are not just flagged — they are accompanied by an understandable evidence trail.

> **Trinetra does not claim that a wallet is criminal. It prioritises wallets and transaction patterns that deserve investigation.**

---

# 💡 What Makes Trinetra Different?

Most transaction-monitoring systems stop after finding an anomaly.

**Trinetra goes one step further: it questions its own results and looks beyond the wallet that initially triggered an alert.**

Our two additional innovations are:

### 1. 🛡️ Self-Audit — *"Can we trust our own score?"*

A model can produce impressive precision and recall for the wrong reasons.

During development, we identified a synthetic-data graph artifact that could make graph-based detection appear artificially strong. Instead of hiding that problem, Trinetra turns it into a feature.

The **Self-Audit layer** checks whether the evaluation itself may be misleading.

It performs four sanity checks:

- **Population disconnection check** — detects whether illicit and benign wallets are almost completely separated in the graph.
- **Suspiciously-perfect-score check** — flags unusually high precision/recall for manual review.
- **Base-rate uplift check** — compares the flagged set against the natural illicit rate to determine whether the model is actually concentrating suspicious wallets.
- **Graph density / percolation check** — looks for conditions where address-reuse or connectivity heuristics may create artificial clusters.

This means Trinetra asks:

> **"The model says it is accurate — but is the dataset allowing it to look accurate?"**

That makes the evaluation more honest and the system more useful for real-world deployment.

---

### 2. 🕸️ Suspicion Propagation — *"What happens after the obvious wallet?"*

A laundering chain does not have to make every wallet suspicious.

A wallet several hops downstream from dirty money may deliberately behave normally and never trigger an individual anomaly rule.

Trinetra addresses this using **personalized PageRank-based suspicion propagation**.

High-confidence wallets become propagation seeds. Suspicion then flows through the transaction graph and **decays with distance**.

This allows Trinetra to surface wallets that:

- did not directly trigger a detection rule,
- are structurally close to multiple high-confidence suspicious wallets,
- may represent downstream or **integration-stage** wallets,
- would otherwise remain invisible to a detector that only studies individual wallet behaviour.

The idea is simple:

> **Don't only ask "Which wallet looks suspicious?" — ask "Which other wallets become interesting because of where they sit in the suspicious network?"**

---

# 🧠 Core Detection Architecture

Trinetra uses complementary layers rather than depending on one model.

```text
                 RAW BITCOIN + NETWORK METADATA
                              │
                              ▼
                    ┌──────────────────┐
                    │ Ingestion &      │
                    │ Validation       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Entity Graph     │
                    │ IP ↔ Wallet ↔ TX │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
     ┌─────────────────┐          ┌─────────────────┐
     │ Tabular Anomaly │          │ Graph Pattern   │
     │ Detection       │          │ Detection       │
     │ Isolation Forest│          │ Structural Rules│
     └────────┬────────┘          └────────┬────────┘
              │                            │
              └──────────────┬─────────────┘
                             ▼
                  ┌─────────────────────┐
                  │ Explainable Scoring │
                  │ & Ranked Alerts     │
                  └──────────┬──────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
     ┌─────────────────┐          ┌──────────────────┐
     │ Self-Audit      │          │ Suspicion        │
     │ "Can we trust   │          │ Propagation      │
     │ the evaluation?"│          │ "Where does it   │
     └─────────────────┘          │ spread?"         │
                                  └────────┬─────────┘
                                           │
                                           ▼
                              ┌──────────────────────┐
                              │ Investigator         │
                              │ Dashboard            │
                              └──────────────────────┘
```

---

# ⚙️ Pipeline Stages

| Stage | Purpose | Key files |
|---|---|---|
| 1 | Synthetic dataset generation with injected laundering patterns and benign look-alikes | `generate_dataset.py` |
| 2 | CSV/JSON/XML ingestion, validation and canonicalisation | `ingest/parser.py` |
| 3 | IP ↔ wallet ↔ transaction graph construction | `graph/build_graph.py` |
| 4a | Transaction-level statistical anomaly detection | `models/anomaly_detection.py` |
| 4b | Wallet-level structural pattern detection | `models/graph_clustering.py` |
| 4c | Combined confidence scoring + explanations | `models/scoring.py` |
| 4e | Evaluation integrity and model self-audit | `self_audit.py` |
| 4f | Graph-based suspicion propagation | `suspicion_propagation.py` |
| 5 | Ranked investigative outputs | `models/final_alerts.csv` |
| 6 | Interactive investigation dashboard | `dashboard/app.py` |

---

# 🧪 Detection Approach

## Tabular Anomaly Detection

Trinetra uses **Isolation Forest** for transaction-level anomaly detection.

It is useful because it:

- does not require labelled criminal transactions for training,
- works well for bulk tabular metadata,
- identifies unusual transaction behaviour,
- can be paired with feature-level explanations.

Examples of signals include unusual amounts, fees and other transaction-level characteristics.

---

## 🕸️ Graph-Based Pattern Detection

Some suspicious behaviour cannot be understood from one transaction.

For example:

- fan-in consolidation,
- fan-out distribution,
- mixing-like structures,
- unusual wallet connectivity.

Trinetra therefore builds an entity graph and searches for structural patterns.

The graph detector is intentionally explainable: **the pattern that fired is itself part of the explanation.**

---

# 🔗 The Correlation Advantage

The core idea behind Trinetra is that **network evidence and blockchain evidence become more valuable when viewed together**.

```text
Network Layer
IP → Port → Timing
       │
       │ correlation
       ▼
Blockchain Layer
Wallet → Transaction → Wallet
       │
       ▼
   AI Correlation
       │
       ▼
Ranked + Explainable Investigative Lead
```

A suspicious transaction alone may not mean much.

A suspicious graph pattern alone may also be ambiguous.

But when multiple independent signals agree, the investigator gets a much stronger lead.

---

# 🛡️ Explainability by Design

Trinetra is built for investigation, not just prediction.

Every alert is accompanied by evidence such as:

- unusual transaction-level features,
- graph patterns,
- confidence score,
- detector agreement,
- propagated suspicion where applicable.

The system therefore aims to answer:

> **"Why was this wallet flagged?"**

rather than simply:

> **"The model says 94%."**

---

# 🔬 Self-Audit in Detail

The Self-Audit module can be run independently:

```bash
python3 self_audit.py \
    --transactions ../ingest/cleaned_transactions.csv \
    --ground-truth ../dataset/ground_truth.csv \
    --edges ../dataset/wallet_graph_edges.csv \
    --alerts final_alerts.csv
```

The module produces a human-readable report showing which checks are:

- ✅ **OK**
- ⚠️ **FLAGGED for review**

This layer is especially important for synthetic evaluation because a model can exploit accidental properties of a generated dataset rather than learning a genuinely useful signal.

---

# 🌊 Suspicion Propagation in Detail

Run propagation from high-confidence alerts:

```bash
python3 suspicion_propagation.py \
    --graph ../graph/graph.graphml \
    --alerts ../models/final_alerts.csv \
    --seed-threshold 70 \
    --out propagated_suspicion.csv
```

The propagation layer:

1. Takes high-confidence wallets as seeds.
2. Assigns seed weights according to their confidence.
3. Runs personalized PageRank over the transaction graph.
4. Allows suspicion to decay as it moves away from the seeds.
5. Removes already-flagged seed wallets from the final propagated list.
6. Produces a ranked list of previously unflagged wallets worth investigation.

The default damping factor is deliberately conservative so that "propagated suspicion" means **graph proximity to strong evidence**, not guilt by association.

---

# 📊 Evaluation

The current evaluation uses held-out `ground_truth.csv` and tests both transaction-level and wallet-level detection.

Illustrative results from the existing evaluation:

| Detector / Score | Precision | Recall |
|---|---:|---:|
| Tabular anomaly detector | 43.8% | 45.8% |
| Graph detector | 64.8% | 37.2% |
| Combined score ≥ 60 | 95.7% | 31.9% |
| Combined score ≥ 70 | 99.6% | 23.8% |

The important result is not simply the highest number.

The experiments showed that the detectors are **complementary**: for example, the graph detector captured mixing patterns that had very weak single-transaction signals.

Self-Audit was added specifically to prevent such numbers from being accepted blindly.

---

# 🚀 Quick Start — Linux / WSL2

### 1. Clone the repository

```bash
git clone <repository-url>
cd Trinetra
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the pipeline

```bash
chmod +x run_pipeline.sh
./run_pipeline.sh
```

### 5. Launch the dashboard

```bash
cd dashboard
streamlit run app.py
```

For WSL2, if the browser does not open automatically:

```bash
explorer.exe "http://localhost:8501"
```

---

# 📁 Repository Structure

```text
Trinetra/
├── README.md
├── run_pipeline.sh
├── generate_dataset.py
│
├── dataset/
│   ├── transactions.csv
│   ├── transactions.json
│   ├── ground_truth.csv
│   └── wallet_graph_edges.csv
│
├── ingest/
│   ├── parser.py
│   └── cleaned_transactions.csv
│
├── graph/
│   ├── build_graph.py
│   ├── view_graph.py
│   ├── graph.graphml
│   └── wallet_stats.csv
│
├── models/
│   ├── anomaly_detection.py
│   ├── graph_clustering.py
│   ├── scoring.py
│   ├── tx_anomaly_scores.csv
│   ├── wallet_pattern_scores.csv
│   └── final_alerts.csv
│
├── self_audit.py
├── suspicion_propagation.py
│
├── dashboard/
│   └── app.py
│
├── docs/
│   ├── Trinetra_Technical_Writeup.docx
│   └── Trinetra_Project_Guide_and_QA.docx
│
└── requirements.txt
```

---

# 🌟 Why Trinetra is Innovative

### **1. Multi-layer visibility**
It connects network-layer and blockchain-layer evidence in one investigative view.

### **2. Two independent detection philosophies**
Statistical anomalies and graph structures are analysed separately before being combined.

### **3. Explainability is part of the pipeline**
The system gives reasons behind alerts rather than treating the model as a black box.

### **4. Self-auditing evaluation**
Trinetra does something unusual for an ML prototype: it actively searches for reasons why its own evaluation might be misleading.

### **5. Suspicion propagation**
It does not stop at directly suspicious wallets. It searches the graph for nearby wallets that may represent later stages of a laundering chain.

### **6. Offline-first architecture**
The core pipeline can operate without sending sensitive investigative data to external cloud AI services.

### **7. Investigator-first output**
Instead of overwhelming an investigator with thousands of raw transactions, Trinetra produces a ranked shortlist with evidence and graph context.

---

# 🎯 Our Core Innovation

> **Detect → Explain → Audit → Propagate**

Most systems focus on:

**Detect suspicious activity.**

Trinetra extends that workflow:

```text
DETECT
  ↓
Why was it flagged?
  ↓
EXPLAIN
  ↓
Can we trust the evaluation?
  ↓
SELF-AUDIT
  ↓
Where could the suspicious trail continue?
  ↓
PROPAGATE
  ↓
INVESTIGATOR-READY LEADS
```

This is the central idea behind Trinetra:

### **A system that not only watches suspicious activity — but also watches its own blind spots.**

---

# ⚠️ Limitations & Responsible Use

- Current evaluation data is synthetic and contains algorithmically injected patterns.
- Real Bitcoin traffic contains legitimate edge cases, noise and adversarial behaviour that synthetic data cannot fully reproduce.
- Graph thresholds require recalibration against real-world case data.
- GeoIP attribution should use a production-grade database in deployment.
- Wallet-to-real-world identity attribution requires off-chain investigation and appropriate legal authority.
- Trinetra is an **investigative lead-generation system**, not an automated system for declaring guilt.

---

# 🔮 Future Scope

- Integration with larger real-world Bitcoin datasets.
- Temporal graph analysis and multi-hop investigation.
- Adaptive thresholds learned from validated case data.
- Graph embeddings and GNN-based detection once suitable labelled data is available.
- More advanced cross-chain analysis.
- Analyst feedback loops for continuous improvement.
- Stronger provenance and audit trails for investigation workflows.
- Additional explainability and case-management features.

---

# 👥 Team

## **Quantum Minds**

Built for **Smart India Hackathon 2026**

**Problem Statement:** 26146  
**Title:** AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic  
**Organization:** National Technical Research Organisation (NTRO)

---

## 📌 Final Note

Trinetra was built around a simple question:

> **If suspicious money can hide inside a huge network, can an investigator get a clearer view without losing the context?**

Our answer is **Trinetra** — an offline, explainable system that connects transactions, wallets and network activity, challenges the reliability of its own evaluation, and follows suspicion beyond the first obvious flag.

### **Trinetra — See the transaction. Understand the network. Question the result. Follow the trail.**
