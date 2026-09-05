#!/usr/bin/env python3
"""
Trinetra — Bitcoin Transaction Intelligence Dashboard
--------------------------------------------------------
Interactive Streamlit dashboard combining every stage of the pipeline.

UI redesigned to closely match the supplied Trinetra reference:
- deep ocean-blue background
- blue + cyan accent system
- compact left navigation rail
- rounded bordered cards
- responsive layout
- consistent controls, charts, tables and alert styling

Run with:
    streamlit run app.py
"""

import glob
import os
import html
import importlib.util

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ------------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Trinetra — BTC Intelligence Dashboard",
    page_icon="👁",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ------------------------------------------------------------------
# THEME / STYLE
# ------------------------------------------------------------------
st.markdown(
    """
<style>
/* ================================================================
   TRINETRA — REFERENCE UI (DEEP OCEAN BLUE THEME)
   ================================================================ */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

:root {
    --bg: #020c18;
    --bg-2: #041526;
    --panel: #06192b;
    --panel-2: #0a2338;
    --panel-hover: #0f2c46;
    --gold: #2196f3;
    --gold-2: #4fc3f7;
    --gold-soft: rgba(33,150,243,.13);
    --gold-border: rgba(33,150,243,.30);
    --text: #f2f6fa;
    --muted: #96a6b5;
    --green: #3dde9c;
    --green-soft: rgba(61,222,156,.13);
    --red: #ee5a43;
    --line: rgba(255,255,255,.075);
}

html, body, [class*="css"] {
    font-family: 'Inter', Arial, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 72% 8%, rgba(33,150,243,.06), transparent 28%),
        linear-gradient(180deg, #020a14 0%, #041526 55%, #020c18 100%);
    color: var(--text);
}

.main {
    background: transparent !important;
}

.block-container {
    max-width: 1600px;
    padding: 28px 26px 30px 18px;
}

/* ---------------- SIDEBAR ---------------- */

section[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, #020c18 0%, #041526 70%, #020814 100%) !important;
    border-right: 1px solid rgba(33,150,243,.25);
    width: 252px !important;
    min-width: 252px !important;
}

section[data-testid="stSidebar"] > div {
    padding: 22px 14px 16px 14px;
}

section[data-testid="stSidebar"] .block-container {
    padding: 0 !important;
}

/* Sidebar brand */
.tri-brand {
    padding: 2px 10px 18px 10px;
    border-bottom: 1px solid rgba(33,150,243,.18);
    margin-bottom: 18px;
}

.brand-row {
    display: flex;
    align-items: center;
    gap: 10px;
}

.eye {
    position: relative;
    width: 84px;
    height: 46px;
    flex: 0 0 84px;
}

.eye::before {
    content: "";
    position: absolute;
    left: 5px;
    top: 5px;
    width: 70px;
    height: 35px;
    border: 3px solid var(--gold);
    border-radius: 75% 12%;
    transform: rotate(-1deg);
    box-shadow: 0 0 15px rgba(33,150,243,.10);
}

.eye::after {
    content: "";
    position: absolute;
    left: 30px;
    top: 13px;
    width: 19px;
    height: 19px;
    border: 4px solid var(--gold);
    border-radius: 50%;
    background: #041018;
    box-shadow: inset 0 0 0 5px rgba(33,150,243,.13);
}

.eye-pupil {
    position: absolute;
    left: 30px;
    top: 13px;
    width: 19px;
    height: 19px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--gold-2);
    font-weight: 700;
    font-size: 12px;
    line-height: 1;
    z-index: 2;
}

.brand-name {
    line-height: 1.02;
}

.brand-name .en {
    color: #f6f8fa;
    font-size: 19px;
    font-weight: 600;
    letter-spacing: .6px;
}

.brand-name .hi {
    color: var(--gold);
    font-family: 'Noto Serif Devanagari', Georgia, serif;
    font-size: 23px;
    margin-top: 3px;
}

.brand-caption {
    color: #ccd6e0;
    font-size: 12px;
    margin-top: 12px;
    letter-spacing: .1px;
}

.sidebar-label {
    color: var(--gold);
    text-transform: uppercase;
    letter-spacing: 1.3px;
    font-size: 11px;
    font-weight: 600;
    margin: 13px 4px 9px 4px;
}

/* Data source cards */
.source-card {
    background: linear-gradient(135deg, #0a2338, #06192b);
    border: 1px solid rgba(255,255,255,.11);
    border-radius: 9px;
    padding: 10px 10px;
    margin: 0 0 9px 0;
    transition: .18s ease;
}

.source-card:hover {
    border-color: rgba(33,150,243,.30);
    transform: translateX(2px);
}

.source-top {
    display: flex;
    align-items: center;
    gap: 10px;
}

.source-check {
    width: 21px;
    height: 21px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: rgba(61,222,156,.12);
    color: var(--green);
    font-weight: 700;
    font-size: 14px;
    flex: 0 0 21px;
}

.source-name {
    color: #e9eff5;
    font-size: 12px;
    font-weight: 500;
}

.source-count {
    margin: 4px 0 0 31px;
    color: var(--green);
    font-size: 11px;
}

/* Radio navigation */
section[data-testid="stSidebar"] [data-testid="stRadio"] > label {
    color: var(--gold) !important;
    text-transform: uppercase;
    letter-spacing: 1.3px;
    font-size: 11px;
    font-weight: 600;
    margin: 9px 4px 8px 4px;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    gap: 5px !important;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label {
    position: relative;
    min-height: 40px;
    padding: 9px 10px !important;
    margin: 0 !important;
    border: 1px solid transparent;
    border-radius: 9px;
    background: transparent;
    transition: all .18s ease;
    cursor: pointer;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(33,150,243,.08);
    border-color: rgba(33,150,243,.18);
    transform: translateX(2px);
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(90deg, rgba(33,150,243,.18), rgba(33,150,243,.06));
    border-color: rgba(33,150,243,.62);
    box-shadow: inset 2px 0 0 var(--gold), 0 0 14px rgba(33,150,243,.04);
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label p {
    color: #edf2f7 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p {
    color: #fff !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] input {
    accent-color: var(--gold);
}

.quote-card {
    border: 1px solid rgba(33,150,243,.28);
    border-radius: 11px;
    padding: 15px 15px 13px;
    margin-top: 14px;
    background: linear-gradient(145deg, rgba(33,150,243,.06), rgba(0,0,0,.10));
}

.quote-mark {
    color: var(--gold);
    font-size: 28px;
    line-height: .6;
    font-family: Georgia, serif;
}

.quote-text {
    color: #eef3f8;
    font-family: Georgia, serif;
    font-size: 16px;
    font-weight: 600;
    line-height: 1.65;
    margin-top: 6px;
}

.quote-author {
    color: var(--gold-2);
    font-family: Georgia, serif;
    font-style: italic;
    font-size: 14px;
    margin-top: 8px;
}

.sidebar-footer {
    color: #64707c;
    font-size: 10px;
    text-align: center;
    margin-top: 16px;
}

/* ---------------- GLOBAL TYPOGRAPHY ---------------- */

h1, h2, h3, h4 {
    color: var(--text) !important;
}

h1 {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-size: clamp(30px, 3vw, 43px) !important;
    line-height: 1.1 !important;
    margin: 0 0 22px 0 !important;
    font-weight: 700 !important;
    letter-spacing: -.5px;
}

h2 {
    font-family: 'Playfair Display', Georgia, serif !important;
}

.page-title {
    display: flex;
    align-items: center;
    gap: 13px;
    margin-bottom: 18px;
}

.page-icon {
    width: 56px;
    height: 56px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    background: linear-gradient(145deg, rgba(33,150,243,.20), rgba(33,150,243,.05));
    border: 1px solid rgba(33,150,243,.42);
    color: var(--gold);
    font-size: 27px;
    box-shadow: 0 8px 30px rgba(0,0,0,.22);
}

.title-main {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: clamp(30px, 3vw, 40px);
    color: #f2f6fa;
    font-weight: 700;
}

.title-main span {
    color: var(--gold);
}

.section-title {
    display: flex;
    align-items: center;
    gap: 10px;
    color: #eef3f8;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 17px;
    font-weight: 600;
    margin: 0 0 11px;
}

.section-title::before {
    content: "";
    width: 11px;
    height: 11px;
    border-radius: 50%;
    background: var(--gold);
    box-shadow: 0 0 13px rgba(33,150,243,.28);
    flex: 0 0 11px;
}

.caption, .stCaption, [data-testid="stCaptionContainer"] {
    color: #869aab !important;
}

/* ---------------- CARDS ---------------- */

.metric-card {
    min-height: 123px;
    padding: 20px 19px 16px;
    border: 1px solid rgba(33,150,243,.25);
    border-radius: 12px;
    background:
        radial-gradient(circle at 20% 0%, rgba(33,150,243,.05), transparent 40%),
        linear-gradient(145deg, #0a2338, #06192b);
    box-shadow: 0 10px 30px rgba(0,0,0,.18);
    transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    border-color: rgba(33,150,243,.55);
    box-shadow: 0 13px 35px rgba(0,0,0,.28);
}

.metric-head {
    display: flex;
    align-items: center;
    gap: 11px;
    color: #eef3f8;
    font-size: 14px;
    font-weight: 500;
}

.metric-icon {
    width: 45px;
    height: 45px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(33,150,243,.11);
    border: 1px solid rgba(33,150,243,.30);
    color: var(--gold);
    font-size: 23px;
}

.metric-value {
    color: var(--gold-2);
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 31px;
    line-height: 1;
    margin: 13px 0 8px 56px;
    font-weight: 700;
}

.metric-sub {
    color: #869aab;
    font-size: 11px;
    margin-left: 56px;
}

.metric-sub strong {
    color: var(--green);
    font-weight: 500;
}

.chart-card,
.content-card {
    border: 1px solid rgba(33,150,243,.22);
    border-radius: 12px;
    background:
        radial-gradient(circle at 12% 0%, rgba(33,150,243,.04), transparent 38%),
        linear-gradient(145deg, #06192b, #041526);
    padding: 17px 17px 10px;
    box-shadow: 0 12px 30px rgba(0,0,0,.16);
    overflow: hidden;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: rgba(33,150,243,.22) !important;
    border-radius: 12px !important;
    background: linear-gradient(145deg, #06192b, #041526) !important;
}

/* Footer impact card */
.impact-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    border: 1px solid rgba(33,150,243,.22);
    border-radius: 12px;
    background: linear-gradient(145deg, #0a2338, #041526);
    padding: 12px 16px;
    margin-top: 15px;
}

.impact-copy {
    display: flex;
    align-items: center;
    gap: 12px;
    color: #c6d3de;
    font-size: 14px;
}

.impact-star {
    color: var(--gold);
    font-size: 26px;
}

/* ---------------- STREAMLIT METRIC FALLBACK ---------------- */

[data-testid="stMetric"] {
    background: linear-gradient(145deg, #0a2338, #06192b) !important;
    border: 1px solid rgba(33,150,243,.26) !important;
    border-radius: 12px !important;
    padding: 17px !important;
}

[data-testid="stMetricLabel"] {
    color: #d7e2ec !important;
}

[data-testid="stMetricValue"] {
    color: var(--gold-2) !important;
    font-family: 'Playfair Display', Georgia, serif !important;
}

/* ---------------- CONTROLS ---------------- */

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div {
    background: #06192b !important;
    border-color: rgba(33,150,243,.30) !important;
    border-radius: 8px !important;
    color: #f0f5fa !important;
}

div[data-baseweb="select"] > div:hover,
div[data-baseweb="input"] > div:hover {
    border-color: rgba(33,150,243,.60) !important;
}

label {
    color: #a9b9c6 !important;
    font-size: 12px !important;
}

.stSlider [data-baseweb="slider"] div {
    background-color: var(--gold) !important;
}

.stCheckbox label:hover,
.stMultiSelect label:hover {
    color: #fff !important;
}

button[kind="secondary"],
button[kind="primary"] {
    border-radius: 8px !important;
    transition: .18s ease !important;
}

button[kind="secondary"] {
    background: #0a2338 !important;
    border: 1px solid rgba(33,150,243,.32) !important;
    color: #eef3f8 !important;
}

button[kind="secondary"]:hover {
    border-color: var(--gold) !important;
    color: var(--gold-2) !important;
    transform: translateY(-1px);
}

button[kind="primary"] {
    background: linear-gradient(135deg, #1565c0, #42a5f5) !important;
    color: #041018 !important;
    border: 1px solid #64b5f6 !important;
    font-weight: 700 !important;
}

/* ---------------- EXPANDERS ---------------- */

[data-testid="stExpander"] {
    background: linear-gradient(145deg, #0a2338, #06192b) !important;
    border: 1px solid rgba(33,150,243,.24) !important;
    border-radius: 10px !important;
    margin-bottom: 8px !important;
}

[data-testid="stExpander"]:hover {
    border-color: rgba(33,150,243,.46) !important;
}

[data-testid="stExpander"] summary {
    color: #eef3f8 !important;
}

/* ---------------- TABLES ---------------- */

[data-testid="stDataFrame"] {
    border: 1px solid rgba(33,150,243,.20);
    border-radius: 9px;
    overflow: hidden;
}

[data-testid="stDataFrame"] > div {
    background: #041526 !important;
}

/* ---------------- ALERTS / INFO ---------------- */

div[data-testid="stAlert"] {
    background: #06192b !important;
    border-radius: 9px !important;
    border-color: rgba(33,150,243,.24) !important;
}

.badge-both,
.badge-tabular,
.badge-graph {
    display: inline-block;
    padding: 4px 9px;
    border-radius: 999px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: .4px;
    text-transform: uppercase;
}

.badge-both {
    background: rgba(238,90,67,.14);
    color: #ff8b78;
    border: 1px solid rgba(238,90,67,.35);
}

.badge-tabular {
    background: rgba(33,150,243,.16);
    color: #4fc3f7;
    border: 1px solid rgba(33,150,243,.38);
}

.badge-graph {
    background: rgba(61,222,156,.12);
    color: #66e9b8;
    border: 1px solid rgba(61,222,156,.30);
}

/* ---------------- DOWNLOAD BUTTON ---------------- */

[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, #0a2338, #041018) !important;
    border: 1px solid rgba(33,150,243,.50) !important;
    color: var(--gold-2) !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: .18s ease !important;
}

[data-testid="stDownloadButton"] button:hover {
    background: rgba(33,150,243,.14) !important;
    border-color: var(--gold) !important;
    transform: translateY(-1px);
}

/* Remove excessive Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent !important;}

/* ---------------- RESPONSIVE ---------------- */

@media (max-width: 1100px) {
    section[data-testid="stSidebar"] {
        width: 220px !important;
        min-width: 220px !important;
    }
    .block-container {
        padding: 22px 18px;
    }
    .metric-card {
        min-height: 112px;
        padding: 15px;
    }
    .metric-value {
        font-size: 27px;
    }
}

@media (max-width: 768px) {
    section[data-testid="stSidebar"] {
        width: 100% !important;
        min-width: 100% !important;
    }
    .block-container {
        padding: 16px 12px 24px;
    }
    .title-main {
        font-size: 29px;
    }
    .page-icon {
        width: 46px;
        height: 46px;
        font-size: 22px;
    }
    .impact-card {
        align-items: flex-start;
        flex-direction: column;
    }
}

@media (max-width: 480px) {
    .metric-card {
        min-height: auto;
    }
    .metric-value {
        margin-left: 0;
    }
    .metric-sub {
        margin-left: 0;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------
SEARCH_ROOTS = [
    ".",
    "..",
    "../ingest",
    "../models",
    "../graph",
    "../dataset",
    "../../ingest",
    "../../models",
    "../../graph",
]


def find_file(filename):
    for root in SEARCH_ROOTS:
        candidate = os.path.join(root, filename)
        if os.path.exists(candidate):
            return candidate
    matches = glob.glob(f"../**/{filename}", recursive=True)
    return matches[0] if matches else None


@st.cache_data
def load_csv(filename, **kwargs):
    path = find_file(filename)
    if path is None:
        return None, None
    return pd.read_csv(path, **kwargs), path


def load_local_module(module_name, filename):
    """Import a sibling pipeline script (e.g. self_audit.py) by file path,
    wherever it happens to sit relative to the dashboard."""
    path = find_file(filename)
    if path is None:
        return None
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


def split_list(cell, cast=str):
    if pd.isna(cell) or cell == "":
        return []
    return [cast(x) for x in str(cell).split("|")]


def safe_count(df):
    return len(df) if df is not None else 0


def page_header(icon, title, gold_word=None):
    if gold_word and gold_word in title:
        before, after = title.split(gold_word, 1)
        title_html = f"{html.escape(before)}<span>{html.escape(gold_word)}</span>{html.escape(after)}"
    else:
        title_html = html.escape(title)

    st.markdown(
        f"""
        <div class="page-title">
            <div class="page-icon">{html.escape(icon)}</div>
            <div class="title-main">{title_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(text):
    st.markdown(f'<div class="section-title">{html.escape(text)}</div>', unsafe_allow_html=True)


def metric_card(icon, label, value, subtext="", green_prefix="✓"):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-head">
                <div class="metric-icon">{html.escape(icon)}</div>
                <div>{html.escape(label)}</div>
            </div>
            <div class="metric-value">{html.escape(str(value))}</div>
            <div class="metric-sub"><strong>{html.escape(green_prefix)}</strong> {html.escape(subtext)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def plot_layout(fig, height=320, x_title=None, y_title=None):
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Arial", color="#e8eef4", size=11),
        hoverlabel=dict(
            bgcolor="#06192b",
            bordercolor="#2196f3",
            font=dict(color="#ffffff"),
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#dce6ef"),
        ),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,.10)",
        zeroline=False,
        linecolor="rgba(255,255,255,.10)",
        title_text=x_title,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,.10)",
        zeroline=False,
        linecolor="rgba(255,255,255,.10)",
        title_text=y_title,
    )
    return fig


def chart_card_start(title):
    st.markdown(
        f"""
        <div class="chart-card">
            <div class="section-title">{html.escape(title)}</div>
        """,
        unsafe_allow_html=True,
    )


def chart_card_end():
    st.markdown("</div>", unsafe_allow_html=True)


def source_card(label, df):
    if df is not None:
        st.markdown(
            f"""
            <div class="source-card">
                <div class="source-top">
                    <span class="source-check">✓</span>
                    <span class="source-name">{html.escape(label)}</span>
                </div>
                <div class="source-count">({len(df):,} rows)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="source-card">
                <div class="source-top">
                    <span class="source-check" style="color:#ee5a43;background:rgba(238,90,67,.10)">!</span>
                    <span class="source-name">{html.escape(label)}</span>
                </div>
                <div class="source-count" style="color:#ee8a78">(not found)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ------------------------------------------------------------------
# DATA LOADING
# ------------------------------------------------------------------
with st.spinner("Loading pipeline data..."):
    cleaned_df, cleaned_path = load_csv("cleaned_transactions.csv")
    wallet_stats_df, wallet_stats_path = load_csv("wallet_stats.csv")
    tx_anomaly_df, tx_anomaly_path = load_csv("tx_anomaly_scores.csv")
    wallet_pattern_df, wallet_pattern_path = load_csv("wallet_pattern_scores.csv")
    final_alerts_df, final_alerts_path = load_csv("final_alerts.csv")
    propagated_df, propagated_path = load_csv("propagated_suspicion.csv")
    ground_truth_df, ground_truth_path = load_csv("ground_truth.csv")
    wallet_edges_df, wallet_edges_path = load_csv("wallet_graph_edges.csv")

if cleaned_df is not None and "timestamp" in cleaned_df.columns:
    cleaned_df["timestamp"] = pd.to_datetime(
        cleaned_df["timestamp"], utc=True, errors="coerce"
    )

if tx_anomaly_df is not None and "timestamp" in tx_anomaly_df.columns:
    tx_anomaly_df["timestamp"] = pd.to_datetime(
        tx_anomaly_df["timestamp"], utc=True, errors="coerce"
    )


# ------------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="tri-brand">
            <div class="brand-row">
                <div class="eye"><span class="eye-pupil">₿</span></div>
                <div class="brand-name">
                    <div class="en">TRINETRA</div>
                    <div class="hi">नेत्र</div>
                </div>
            </div>
            <div class="brand-caption">Bitcoin Transaction Intelligence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-label">Data Sources</div>', unsafe_allow_html=True)

    for label, df in [
        ("Cleaned transactions", cleaned_df),
        ("Wallet stats", wallet_stats_df),
        ("Tx anomaly scores", tx_anomaly_df),
        ("Wallet pattern scores", wallet_pattern_df),
        ("Final alerts", final_alerts_df),
        ("Propagated suspicion", propagated_df),
    ]:
        source_card(label, df)

    nav_options = [
        "▦  Overview",
        "〽  Transaction Anomalies",
        "▣  Wallet Patterns",
        "↝  Suspicion Propagation",
        "♟  Final Alerts",
        "☑  Self-Audit",
        "⌕  Wallet Lookup",
    ]

    st.markdown('<div class="sidebar-label">Navigation</div>', unsafe_allow_html=True)

    selected_nav = st.radio(
        "Navigate",
        nav_options,
        index=0,
        label_visibility="collapsed",
    )

    page = selected_nav.split("  ", 1)[-1]

    st.markdown(
        """
        <div class="quote-card">
            <div class="quote-mark">◆</div>
            <div class="quote-text">Team Name</div>
            <div class="quote-author">Quantum Minds</div>
        </div>
        <div class="sidebar-footer">Trinetra Pipeline · Stages 2–4f</div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------
# PAGE: OVERVIEW
# ------------------------------------------------------------------
if page == "Overview":
    page_header("▥", "Transactions Overview", "Overview")

    total_tx = safe_count(cleaned_df)
    n_anomalies = (
        int(tx_anomaly_df["is_anomaly"].sum())
        if tx_anomaly_df is not None and "is_anomaly" in tx_anomaly_df.columns
        else 0
    )
    n_wallets_flagged = safe_count(wallet_pattern_df)
    n_alerts = safe_count(final_alerts_df)

    anomaly_rate = (n_anomalies / total_tx * 100) if total_tx else 0
    wallet_rate = (n_wallets_flagged / safe_count(wallet_stats_df) * 100) if safe_count(wallet_stats_df) else 0

    m1, m2, m3, m4 = st.columns(4, gap="small")
    with m1:
        metric_card("▥", "Total Transactions", f"{total_tx:,}", "loaded from cleaned pipeline")
    with m2:
        metric_card("〽", "Anomalous Transactions", f"{n_anomalies:,}", f"{anomaly_rate:.1f}% of transactions", "↗")
    with m3:
        metric_card("▣", "Wallets w/ Graph Patterns", f"{n_wallets_flagged:,}", f"{wallet_rate:.1f}% of wallet stats", "↗")
    with m4:
        metric_card("♟", "Final Ranked Alerts", f"{n_alerts:,}", "combined ranked alerts", "↗")

    st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1.04, 0.96], gap="small")

    with c1:
        chart_card_start("Transaction volume over time")

        if cleaned_df is not None and "timestamp" in cleaned_df.columns:
            daily = (
                cleaned_df.dropna(subset=["timestamp"])
                .set_index("timestamp")
                .resample("D")
                .size()
                .reset_index(name="count")
            )

            fig = px.area(daily, x="timestamp", y="count")
            fig.update_traces(
                line=dict(color="#2196f3", width=2),
                fillcolor="rgba(33,150,243,.18)",
                hovertemplate="%{x|%b %d, %Y}<br>Count: %{y:,}<extra></extra>",
            )
            fig = plot_layout(fig, 285, x_title="timestamp", y_title="count")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("cleaned_transactions.csv not found")

        chart_card_end()

    with c2:
        chart_card_start("Suspicion score distribution")

        if tx_anomaly_df is not None and "suspicion_score" in tx_anomaly_df.columns:
            fig = px.histogram(
                tx_anomaly_df,
                x="suspicion_score",
                nbins=40,
            )
            fig.update_traces(
                marker_color="#2196f3",
                marker_line_color="#4fc3f7",
                marker_line_width=.35,
                hovertemplate="Score: %{x}<br>Count: %{y:,}<extra></extra>",
            )
            fig = plot_layout(fig, 285, x_title="suspicion_score", y_title="count")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("tx_anomaly_scores.csv not found")

        chart_card_end()

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    c3, c4 = st.columns([1.04, 0.96], gap="small")

    with c3:
        chart_card_start("Detection method breakdown")

        if final_alerts_df is not None and "detected_by" in final_alerts_df.columns:
            counts = final_alerts_df["detected_by"].value_counts().reset_index()
            counts.columns = ["method", "count"]

            fig = px.pie(
                counts,
                names="method",
                values="count",
                hole=.56,
            )

            fig.update_traces(
                marker=dict(
                    colors=["#2196f3", "#ee5a43", "#3dde9c"],
                    line=dict(color="#06192b", width=2),
                ),
                textfont=dict(color="#041018", size=12),
                hovertemplate="%{label}<br>%{value:,}<extra></extra>",
            )

            fig.update_layout(
                showlegend=True,
                legend=dict(
                    orientation="v",
                    x=.78,
                    y=.5,
                    font=dict(size=11, color="#dce6ef"),
                ),
                annotations=[
                    dict(
                        text=f"<b>{total_tx:,}</b><br><span style='font-size:11px'>Total</span>",
                        x=.5,
                        y=.5,
                        showarrow=False,
                        font=dict(size=16, color="#eef3f8"),
                    )
                ],
            )
            fig = plot_layout(fig, 285)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("final_alerts.csv not found or missing 'detected_by' column")

        chart_card_end()

    with c4:
        chart_card_start("Top flagged graph patterns")

        if wallet_pattern_df is not None and "matched_patterns" in wallet_pattern_df.columns:
            all_patterns = (
                wallet_pattern_df["matched_patterns"]
                .dropna()
                .astype(str)
                .str.split(", ")
                .explode()
            )
            pattern_counts = (
                all_patterns[all_patterns != ""]
                .value_counts()
                .head(8)
                .reset_index()
            )
            pattern_counts.columns = ["pattern", "count"]

            fig = px.bar(
                pattern_counts,
                x="count",
                y="pattern",
                orientation="h",
            )
            fig.update_traces(
                marker_color="#3dde9c",
                hovertemplate="%{y}<br>Count: %{x:,}<extra></extra>",
            )
            fig = plot_layout(fig, 285, x_title="count", y_title="pattern")
            fig.update_layout(yaxis=dict(categoryorder="total ascending"))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("wallet_pattern_scores.csv not found")

        chart_card_end()

    st.markdown(
        """
        <div class="impact-card">
            <div class="impact-copy">
                <span class="impact-star">☆</span>
                <span>Turning insights into impact — building smarter, safer, and more efficient systems.</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if final_alerts_df is not None:
        csv = final_alerts_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⇩  Download Report",
            csv,
            "trinetra_report.csv",
            "text/csv",
            use_container_width=False,
        )


# ------------------------------------------------------------------
# PAGE: TRANSACTION ANOMALIES
# ------------------------------------------------------------------
elif page == "Transaction Anomalies":
    page_header("〽", "Transaction Anomaly Explorer", "Anomaly")

    if tx_anomaly_df is None:
        st.error("tx_anomaly_scores.csv not found.")
    else:
        with st.container(border=True):
            section_title("Filters")
            col1, col2, col3 = st.columns(3)

            with col1:
                min_score = st.slider(
                    "Minimum suspicion score",
                    0, 100, 50,
                    key="tx_min_score",
                )

            with col2:
                only_flagged = st.checkbox(
                    "Only show flagged anomalies (is_anomaly=True)",
                    value=True,
                    key="tx_only_flagged",
                )

            with col3:
                countries = (
                    sorted(tx_anomaly_df["geo_country"].dropna().unique().tolist())
                    if "geo_country" in tx_anomaly_df.columns
                    else []
                )
                selected_countries = st.multiselect(
                    "Filter by country",
                    countries,
                    default=[],
                    key="tx_countries",
                )

        filtered = tx_anomaly_df[
            tx_anomaly_df["suspicion_score"] >= min_score
        ]

        if only_flagged and "is_anomaly" in filtered.columns:
            filtered = filtered[filtered["is_anomaly"] == True]

        if selected_countries and "geo_country" in filtered.columns:
            filtered = filtered[filtered["geo_country"].isin(selected_countries)]

        st.caption(f"Showing {len(filtered):,} of {len(tx_anomaly_df):,} transactions")

        with st.container(border=True):
            section_title("Suspicion timeline")

            hover_cols = [
                c for c in
                ["txid", "geo_country", "total_in", "total_out", "fee", "reason"]
                if c in filtered.columns
            ]

            fig = px.scatter(
                filtered,
                x="timestamp",
                y="suspicion_score",
                color="suspicion_score",
                color_continuous_scale=["#2d6d8b", "#2196f3", "#ee5a43"],
                hover_data=hover_cols,
            )
            fig.update_traces(marker=dict(size=6, line=dict(width=0)))
            fig = plot_layout(fig, 420, x_title="timestamp", y_title="suspicion_score")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        with st.container(border=True):
            section_title("Flagged transactions")
            cols = [
                c for c in
                ["txid", "timestamp", "geo_country", "total_in", "total_out",
                 "fee", "suspicion_score", "is_anomaly", "reason"]
                if c in filtered.columns
            ]
            st.dataframe(
                filtered.sort_values("suspicion_score", ascending=False)[cols],
                use_container_width=True,
                height=420,
                hide_index=True,
            )


# ------------------------------------------------------------------
# PAGE: WALLET PATTERNS
# ------------------------------------------------------------------
elif page == "Wallet Patterns":
    page_header("▣", "Graph-Based Structural Patterns", "Structural")

    if wallet_pattern_df is None:
        st.error("wallet_pattern_scores.csv not found.")
    else:
        with st.container(border=True):
            section_title("Pattern filters")
            col1, col2 = st.columns(2)

            with col1:
                min_score = st.slider(
                    "Minimum graph suspicion score",
                    0, 100, 35,
                    key="wallet_min_score",
                )

            with col2:
                all_patterns = sorted(
                    set(
                        p
                        for plist in wallet_pattern_df["matched_patterns"]
                        .dropna()
                        .astype(str)
                        .str.split(", ")
                        for p in plist if p
                    )
                )
                selected_patterns = st.multiselect(
                    "Filter by pattern type",
                    all_patterns,
                    default=[],
                    key="wallet_patterns",
                )

        filtered = wallet_pattern_df[
            wallet_pattern_df["graph_suspicion_score"] >= min_score
        ]

        if selected_patterns:
            filtered = filtered[
                filtered["matched_patterns"].apply(
                    lambda x: any(p in str(x) for p in selected_patterns)
                )
            ]

        st.caption(
            f"Showing {len(filtered):,} of {len(wallet_pattern_df):,} flagged wallets"
        )

        with st.container(border=True):
            section_title("Highest-risk wallets")

            top = (
                filtered
                .sort_values("graph_suspicion_score", ascending=False)
                .head(30)
            )

            fig = px.bar(
                top,
                x="graph_suspicion_score",
                y="wallet",
                orientation="h",
                color="n_patterns_matched" if "n_patterns_matched" in top.columns else None,
                color_continuous_scale=["#2d6d8b", "#2196f3", "#ee5a43"],
                hover_data=[
                    c for c in ["matched_patterns", "reasons"]
                    if c in top.columns
                ],
            )
            fig = plot_layout(
                fig, 600,
                x_title="graph_suspicion_score",
                y_title="wallet",
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        with st.container(border=True):
            section_title("All flagged wallets")
            st.dataframe(
                filtered.sort_values("graph_suspicion_score", ascending=False),
                use_container_width=True,
                height=430,
                hide_index=True,
            )


# ------------------------------------------------------------------
# PAGE: SUSPICION PROPAGATION
# ------------------------------------------------------------------
elif page == "Suspicion Propagation":
    page_header("↝", "Suspicion Propagation", "Propagation")

    if propagated_df is None:
        st.error(
            "propagated_suspicion.csv not found. Run "
            "`python3 suspicion_propagation.py --graph ../graph/graph.graphml "
            "--alerts ../models/final_alerts.csv --out propagated_suspicion.csv` "
            "from the models/ directory first."
        )
    else:
        st.caption(
            "These wallets never matched a rule directly, but sit close in the "
            "transaction graph to high-confidence flags — personalized PageRank "
            "seeded at confirmed alerts, decaying with graph distance. Worth "
            "review as possible 'integration stage' wallets (laundering's final, "
            "deliberately clean-looking hop)."
        )

        score_col = (
            "propagated_suspicion_0_100"
            if "propagated_suspicion_0_100" in propagated_df.columns
            else propagated_df.columns[-1]
        )

        n_scored = safe_count(propagated_df)
        top_score = propagated_df[score_col].max() if n_scored else 0
        n_above_50 = int((propagated_df[score_col] >= 50).sum()) if n_scored else 0
        pct_above_50 = (n_above_50 / n_scored * 100) if n_scored else 0

        m1, m2, m3 = st.columns(3, gap="small")
        with m1:
            metric_card("↝", "Non-Seed Wallets Scored", f"{n_scored:,}", "scored via PageRank diffusion")
        with m2:
            metric_card("◉", "Highest Propagated Score", f"{top_score:.1f}", "0–100 scale", "↗")
        with m3:
            metric_card("⚠", "Wallets ≥ 50 Propagated", f"{n_above_50:,}", f"{pct_above_50:.1f}% of scored wallets", "↗")

        st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            section_title("Top wallets by propagated suspicion")
            top = propagated_df.sort_values(score_col, ascending=False).head(25)
            fig = px.bar(
                top,
                x=score_col,
                y="wallet",
                orientation="h",
                color=score_col,
                color_continuous_scale=["#2d6d8b", "#2196f3", "#ee5a43"],
            )
            fig = plot_layout(fig, 600, x_title=score_col, y_title="wallet")
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        with st.container(border=True):
            section_title("All propagated-suspicion wallets")
            st.dataframe(
                propagated_df.sort_values(score_col, ascending=False),
                use_container_width=True,
                height=430,
                hide_index=True,
            )

        csv = propagated_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⇩  Download Propagated Suspicion as CSV",
            csv,
            "propagated_suspicion.csv",
            "text/csv",
        )


# ------------------------------------------------------------------
# PAGE: FINAL ALERTS
# ------------------------------------------------------------------
elif page == "Final Alerts":
    page_header("♟", "Final Ranked Alerts", "Alerts")

    if final_alerts_df is None:
        st.error("final_alerts.csv not found.")
    else:
        with st.container(border=True):
            section_title("Alert filters")
            col1, col2, col3 = st.columns(3)

            with col1:
                min_conf = st.slider(
                    "Minimum confidence",
                    0, 100, 0,
                    key="alert_min_conf",
                )

            with col2:
                methods = (
                    final_alerts_df["detected_by"].dropna().unique().tolist()
                    if "detected_by" in final_alerts_df.columns
                    else []
                )
                selected_methods = st.multiselect(
                    "Detection method",
                    methods,
                    default=methods,
                    key="alert_methods",
                )

            with col3:
                top_n = st.number_input(
                    "Show top N",
                    min_value=5,
                    max_value=500,
                    value=25,
                    step=5,
                    key="alert_top_n",
                )

        conf_col = (
            "combined_confidence"
            if "combined_confidence" in final_alerts_df.columns
            else "final_risk_score"
        )

        filtered = final_alerts_df[
            final_alerts_df[conf_col] >= min_conf
        ]

        if selected_methods and "detected_by" in filtered.columns:
            filtered = filtered[
                filtered["detected_by"].isin(selected_methods)
            ]

        filtered = filtered.sort_values(conf_col, ascending=False).head(int(top_n))

        st.caption(f"Showing top {len(filtered):,} alerts")

        for _, row in filtered.iterrows():
            wallet_id = row.get("wallet", row.get("txid", "unknown"))
            conf = row.get(conf_col, 0)

            try:
                conf_display = f"{float(conf):.1f}"
            except (TypeError, ValueError):
                conf_display = str(conf)

            badge_class = {
                "both": "badge-both",
                "tabular_only": "badge-tabular",
                "graph_only": "badge-graph",
            }.get(row.get("detected_by", ""), "badge-graph")

            rank = row.get("rank", "-")

            with st.expander(
                f"#{rank}   {str(wallet_id)[:26]}...   —   confidence {conf_display}"
            ):
                c1, c2 = st.columns([1, 3])

                with c1:
                    st.metric("Confidence", conf_display)

                    if "detected_by" in row:
                        st.markdown(
                            f'<span class="{badge_class}">{html.escape(str(row["detected_by"]))}</span>',
                            unsafe_allow_html=True,
                        )

                    if "matched_patterns" in row and pd.notna(row["matched_patterns"]):
                        st.caption(
                            f"Patterns: {row['matched_patterns']}"
                        )

                with c2:
                    reason_col = (
                        "combined_reason"
                        if "combined_reason" in row
                        else "reason"
                    )
                    st.write(
                        row.get(reason_col, "No details available")
                    )

        with st.container(border=True):
            section_title("Full alert table")
            st.dataframe(
                filtered,
                use_container_width=True,
                height=430,
                hide_index=True,
            )

        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⇩  Download Filtered Alerts as CSV",
            csv,
            "filtered_alerts.csv",
            "text/csv",
        )


# ------------------------------------------------------------------
# PAGE: SELF-AUDIT
# ------------------------------------------------------------------
elif page == "Self-Audit":
    page_header("☑", "Self-Audit Report", "Self-Audit")

    st.caption(
        "Sanity checks run against held-out ground truth to catch metrics "
        "that look strong because of a dataset artifact (e.g. graph "
        "percolation) rather than genuine detection power."
    )

    missing = [
        label for label, df in [
            ("cleaned_transactions.csv", cleaned_df),
            ("ground_truth.csv", ground_truth_df),
            ("wallet_graph_edges.csv", wallet_edges_df),
            ("final_alerts.csv", final_alerts_df),
        ] if df is None
    ]

    if missing:
        st.error(f"Missing required file(s) for self-audit: {', '.join(missing)}")
    else:
        self_audit_module = load_local_module("self_audit", "self_audit.py")

        if self_audit_module is None:
            st.error(
                "self_audit.py not found alongside the pipeline — copy it into "
                "the project root or models/ directory."
            )
        else:
            with st.spinner("Running self-audit checks..."):
                audit_results = self_audit_module.run_self_audit(
                    cleaned_df, ground_truth_df, wallet_edges_df, final_alerts_df
                )

            n_flags = sum(1 for r in audit_results if r["is_suspicious"])

            m1, m2 = st.columns(2, gap="small")
            with m1:
                metric_card("☑", "Checks Run", f"{len(audit_results)}", "sanity checks against ground truth")
            with m2:
                metric_card(
                    "⚠" if n_flags else "✓",
                    "Checks Flagged",
                    f"{n_flags}",
                    "review before reporting these metrics" if n_flags else "no red flags raised",
                    "↗" if n_flags else "✓",
                )

            st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

            for r in audit_results:
                flagged = r["is_suspicious"]
                badge_class = "badge-both" if flagged else "badge-graph"
                badge_text = "FLAGGED" if flagged else "OK"

                with st.container(border=True):
                    st.markdown(
                        f'<div class="section-title">{html.escape(r["check"])} '
                        f'<span class="{badge_class}" style="margin-left:10px;">{html.escape(badge_text)}</span></div>',
                        unsafe_allow_html=True,
                    )

                    detail_items = {
                        k: v for k, v in r.items()
                        if k not in ("check", "verdict", "is_suspicious")
                    }
                    if detail_items:
                        cols = st.columns(len(detail_items))
                        for col, (k, v) in zip(cols, detail_items.items()):
                            with col:
                                st.metric(k.replace("_", " ").title(), v)

                    st.write(r["verdict"])

            if n_flags > 0:
                st.warning(
                    "One or more checks were flagged above. Treat the "
                    "corresponding metrics with the noted caveat rather than "
                    "presenting them as unqualified evidence of detection power."
                )


# ------------------------------------------------------------------
# PAGE: WALLET LOOKUP
# ------------------------------------------------------------------
elif page == "Wallet Lookup":
    page_header("⌕", "Wallet Deep Dive", "Deep")

    with st.container(border=True):
        section_title("Wallet search")
        search = st.text_input(
            "Enter a wallet address (or partial match)",
            placeholder="Paste a wallet address or partial address...",
            key="wallet_search",
        )

    if search:
        results_found = False

        if wallet_stats_df is not None and "wallet" in wallet_stats_df.columns:
            matches = wallet_stats_df[
                wallet_stats_df["wallet"].astype(str).str.contains(
                    search, case=False, na=False
                )
            ]
            if len(matches) > 0:
                results_found = True
                with st.container(border=True):
                    section_title("Graph stats")
                    st.dataframe(
                        matches,
                        use_container_width=True,
                        hide_index=True,
                    )

        if wallet_pattern_df is not None and "wallet" in wallet_pattern_df.columns:
            matches = wallet_pattern_df[
                wallet_pattern_df["wallet"].astype(str).str.contains(
                    search, case=False, na=False
                )
            ]
            if len(matches) > 0:
                results_found = True
                with st.container(border=True):
                    section_title("Structural pattern flags")

                    for _, row in matches.iterrows():
                        score = row.get("graph_suspicion_score", "—")
                        reasons = row.get("reasons", "No reason available")
                        st.markdown(
                            f"""
                            <div class="content-card" style="margin-bottom:9px;">
                                <div style="color:#2196f3;font-weight:600;font-size:13px;">
                                    {html.escape(str(row.get("wallet", "unknown")))}
                                </div>
                                <div style="color:#d3dde6;margin-top:7px;font-size:12px;">
                                    Graph suspicion score: <strong style="color:#4fc3f7">{html.escape(str(score))}</strong>
                                </div>
                                <div style="color:#869aab;margin-top:6px;font-size:12px;">
                                    {html.escape(str(reasons))}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

        if final_alerts_df is not None and "wallet" in final_alerts_df.columns:
            matches = final_alerts_df[
                final_alerts_df["wallet"].astype(str).str.contains(
                    search, case=False, na=False
                )
            ]
            if len(matches) > 0:
                results_found = True
                with st.container(border=True):
                    section_title("Final alert record")
                    st.dataframe(
                        matches,
                        use_container_width=True,
                        hide_index=True,
                    )

        if propagated_df is not None and "wallet" in propagated_df.columns:
            matches = propagated_df[
                propagated_df["wallet"].astype(str).str.contains(
                    search, case=False, na=False
                )
            ]
            if len(matches) > 0:
                results_found = True
                score_col = (
                    "propagated_suspicion_0_100"
                    if "propagated_suspicion_0_100" in propagated_df.columns
                    else propagated_df.columns[-1]
                )
                with st.container(border=True):
                    section_title("Propagated suspicion (no direct rule match)")
                    for _, row in matches.iterrows():
                        st.markdown(
                            f"""
                            <div class="content-card" style="margin-bottom:9px;">
                                <div style="color:#2196f3;font-weight:600;font-size:13px;">
                                    {html.escape(str(row.get("wallet", "unknown")))}
                                </div>
                                <div style="color:#d3dde6;margin-top:7px;font-size:12px;">
                                    Propagated suspicion score: <strong style="color:#4fc3f7">{html.escape(str(row.get(score_col, "—")))}</strong>
                                </div>
                                <div style="color:#869aab;margin-top:6px;font-size:12px;">
                                    Graph-close to a confirmed high-confidence alert, but never matched a rule itself — possible integration-stage wallet.
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

        if cleaned_df is not None:
            cleaned_df["input_str"] = cleaned_df.get(
                "input_addresses", pd.Series(index=cleaned_df.index, dtype=str)
            ).astype(str)
            cleaned_df["output_str"] = cleaned_df.get(
                "output_addresses", pd.Series(index=cleaned_df.index, dtype=str)
            ).astype(str)

            tx_matches = cleaned_df[
                cleaned_df["input_str"].str.contains(
                    search, case=False, na=False
                )
                | cleaned_df["output_str"].str.contains(
                    search, case=False, na=False
                )
            ]

            if len(tx_matches) > 0:
                results_found = True
                with st.container(border=True):
                    section_title(
                        f"Transactions involving this wallet ({len(tx_matches)})"
                    )

                    cols = [
                        c for c in
                        ["txid", "timestamp", "src_ip", "geo_country",
                         "total_in", "total_out", "fee"]
                        if c in tx_matches.columns
                    ]

                    st.dataframe(
                        tx_matches[cols],
                        use_container_width=True,
                        height=320,
                        hide_index=True,
                    )

        if not results_found:
            st.info("No records found for this wallet across any data source.")
    else:
        st.info("Enter a wallet address above to see everything known about it.")