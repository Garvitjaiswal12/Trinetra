#!/usr/bin/env python3
"""
Trinetra — Bitcoin Transaction Intelligence Dashboard
--------------------------------------------------------
Interactive Streamlit dashboard combining every stage of the pipeline.

UI theme: Slate + Teal/Cyan
- deep navy-slate background (#0F1729 / #111827-family), teal/cyan accents (#2DD4BF / #22D3EE)
- top brand bar with notification bell + Deploy button
- system status strip
- full-width horizontal tab navigation
- rounded bordered cards
- Risk Summary donut gauge
- auto-animating horizontal "Key Features" carousel (right rail)
- responsive layout

Run with:
    streamlit run app.py
"""

import glob
import os
import html
from datetime import timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components


# ------------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Trinetra — BTC Intelligence Dashboard",
    page_icon="👁",
    layout="wide",
)

# ------------------------------------------------------------------
# THEME / STYLE  (slate / teal / cyan)
# ------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap');

:root {
    --navy: #E2E8F0;
    --navy-2: #94A3B8;
    --orange: #2DD4BF;
    --orange-2: #22D3EE;
    --orange-soft: rgba(45, 212, 191, .12);
    --bg: #0F1729;
    --card: #131C2E;
    --border: #1E293B;
    --text: #CBD5E1;
    --muted: #94A3B8;
    --green: #34D399;
    --green-soft: rgba(52, 211, 153, .12);
    --red: #F87171;
    --red-soft: rgba(248, 113, 113, .14);
}

html, body, [class*="css"] {
    font-family: 'Inter', Arial, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 75% 0%, rgba(45,212,191,.05), transparent 30%),
        radial-gradient(circle at 0% 80%, rgba(34,211,238,.04), transparent 35%),
        linear-gradient(180deg, #0B1220 0%, #0F1729 45%, #0D1524 100%);
    color: var(--text);
}

.main { background: transparent !important; }

.block-container {
    max-width: 1650px;
    padding: 20px 26px 34px 18px;
}

/* ================================================================
   TOP BRAND BAR
   ================================================================ */

.top-header {
    width: 100%;
    padding: 4px 0 16px 0;
    margin-bottom: 10px;
}

.top-brand-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    width: 100%;
}

.top-brand {
    display: flex;
    align-items: center;
    gap: 14px;
}

.top-eye {
    position: relative;
    width: 46px;
    height: 30px;
    flex: 0 0 46px;
}

.top-eye::before {
    content: "";
    position: absolute;
    left: 1px;
    top: 3px;
    width: 40px;
    height: 22px;
    border: 3px solid var(--orange);
    border-radius: 75% 12%;
    transform: rotate(-2deg);
}

.top-eye::after {
    content: "";
    position: absolute;
    left: 15px;
    top: 7px;
    width: 12px;
    height: 12px;
    border: 3px solid var(--orange);
    border-radius: 50%;
    background: #0B1220;
}

.top-eye-pupil {
    position: absolute;
    left: 20px;
    top: 12px;
    width: 5px;
    height: 5px;
    background: var(--navy);
    border-radius: 50%;
    z-index: 2;
}

.top-en {
    color: var(--navy);
    font-size: 22px;
    font-weight: 800;
    letter-spacing: .5px;
    line-height: 1;
}

.top-hi {
    color: var(--orange);
    font-family: 'Noto Serif Devanagari', Georgia, serif;
    font-size: 15px;
    margin-top: 2px;
    line-height: 1;
}

.top-brand-caption {
    color: var(--muted);
    font-size: 12.5px;
    font-weight: 500;
    padding: 6px 12px;
    background: #182238;
    border-radius: 7px;
    margin-left: 6px;
}

.top-actions {
    display: flex;
    align-items: center;
    gap: 14px;
}

.bell-wrap {
    position: relative;
    width: 38px;
    height: 38px;
    border-radius: 9px;
    border: 1px solid var(--border);
    background: var(--card);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    color: var(--navy);
}

.bell-badge {
    position: absolute;
    top: -6px;
    right: -6px;
    background: var(--orange);
    color: #0B1220;
    font-size: 10px;
    font-weight: 700;
    border-radius: 999px;
    padding: 1px 5px;
    line-height: 1.4;
}

/* ---------------- HORIZONTAL NAV ---------------- */

div[data-testid="stRadio"] { width: 100%; }
div[data-testid="stRadio"] > label { display: none !important; }

div[data-testid="stRadio"] > div {
    display: flex !important;
    flex-direction: row !important;
    align-items: stretch !important;
    justify-content: flex-start !important;
    gap: 4px !important;
    width: 100% !important;
    padding: 4px !important;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    border-bottom: 2px solid var(--border);
}

div[data-testid="stRadio"] > div > label {
    flex: 0 0 auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 40px !important;
    padding: 8px 18px !important;
    margin: 0 !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 6px 6px 0 0 !important;
    background: transparent !important;
    cursor: pointer;
    transition: background .15s ease, border-color .15s ease;
}

div[data-testid="stRadio"] > div > label:hover {
    background: #182238 !important;
}

div[data-testid="stRadio"] > div > label:has(input:checked) {
    background: transparent !important;
    border-bottom: 2px solid var(--orange) !important;
}

div[data-testid="stRadio"] > div > label p {
    color: var(--muted) !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    white-space: nowrap;
    margin: 0 !important;
}

div[data-testid="stRadio"] > div > label:has(input:checked) p {
    color: var(--orange) !important;
    font-weight: 700 !important;
}

div[data-testid="stRadio"] input { display: none !important; }

/* ---------------- SYSTEM STATUS STRIP ---------------- */

.status-strip {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 18px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 22px;
    margin: 14px 0 18px 0;
}

.status-block {
    display: flex;
    align-items: center;
    gap: 12px;
}

.status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 0 4px var(--green-soft);
    flex: 0 0 10px;
}

.status-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .5px;
    color: var(--muted);
    text-transform: uppercase;
}

.status-title { font-size: 14px; font-weight: 700; color: var(--navy); }
.status-sub { font-size: 11.5px; color: var(--muted); }

.status-icon-circ {
    width: 34px;
    height: 34px;
    border-radius: 9px;
    background: var(--orange-soft);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--orange);
    font-size: 16px;
    flex: 0 0 34px;
}

.status-num { font-size: 17px; font-weight: 700; color: var(--navy); line-height: 1.1; }
.status-num-label { font-size: 11.5px; color: var(--muted); }
.status-trend-up { color: var(--red); font-weight: 600; }
.status-trend-up.good { color: var(--green); }

/* ---------------- GLOBAL TYPOGRAPHY ---------------- */

h1, h2, h3, h4 { color: var(--navy) !important; }

.page-title {
    display: flex;
    align-items: center;
    gap: 13px;
    margin-bottom: 4px;
}

.page-icon {
    width: 50px;
    height: 50px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 11px;
    background: var(--orange-soft);
    color: var(--orange);
    font-size: 24px;
    flex: 0 0 50px;
}

.title-main {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: clamp(26px, 2.6vw, 34px);
    color: var(--navy);
    font-weight: 700;
}

.title-main span { color: var(--orange); }

.title-sub {
    color: var(--muted);
    font-size: 13px;
    margin: 2px 0 0 63px;
}

.section-title {
    display: flex;
    align-items: center;
    gap: 9px;
    color: var(--navy);
    font-size: 15px;
    font-weight: 700;
    margin: 0 0 11px;
}

.section-title::before {
    content: "";
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: var(--orange);
    flex: 0 0 9px;
}

.caption, .stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }

/* ---------------- CARDS ---------------- */

.metric-card {
    min-height: 118px;
    padding: 18px 18px 15px;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--card);
    transition: transform .15s ease, box-shadow .15s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 24px rgba(0,0,0,.35), 0 0 0 1px rgba(45,212,191,.15);
}

.metric-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 11px;
}

.metric-head-left { display: flex; align-items: center; gap: 11px; }

.metric-icon {
    width: 40px;
    height: 40px;
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--orange-soft);
    color: var(--orange);
    font-size: 19px;
}

.metric-label { color: var(--text); font-size: 13.5px; font-weight: 600; }

.metric-trend {
    width: 30px; height: 30px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px;
}
.metric-trend.up-bad { background: var(--red-soft); color: var(--red); }
.metric-trend.up-good { background: var(--green-soft); color: var(--green); }

.metric-value {
    color: var(--navy);
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 28px;
    line-height: 1;
    margin: 12px 0 6px 0;
    font-weight: 700;
}

.metric-sub { color: var(--muted); font-size: 11.5px; }
.metric-sub strong.good { color: var(--green); font-weight: 700; }
.metric-sub strong.bad { color: var(--red); font-weight: 700; }

.chart-card, .content-card {
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--card);
    padding: 16px 17px 10px;
    overflow: hidden;
}

.chart-card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 6px;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--border) !important;
    border-radius: 12px !important;
    background: var(--card) !important;
}

.impact-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: linear-gradient(135deg, #0F2A2C, #101A2E);
    padding: 14px 18px;
    margin-top: 15px;
}

.impact-copy { display: flex; align-items: center; gap: 12px; color: var(--navy); font-size: 14px; font-weight: 500; }
.impact-star { color: var(--orange); font-size: 24px; }

/* ---------------- RISK SUMMARY CARD ---------------- */

.risk-legend-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 9px 0;
    border-top: 1px solid var(--border);
    font-size: 13px;
}
.risk-legend-row:first-of-type { border-top: none; }
.risk-legend-left { display: flex; align-items: center; gap: 9px; color: var(--text); font-weight: 500; }
.risk-dot { width: 9px; height: 9px; border-radius: 50%; flex: 0 0 9px; }
.risk-pct { font-weight: 700; color: var(--navy); }

.risk-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .3px;
}
.risk-badge.elevated { background: var(--red-soft); color: var(--red); }
.risk-badge.moderate { background: rgba(251,191,36,.14); color: #FBBF24; }
.risk-badge.low { background: var(--green-soft); color: var(--green); }

/* ---------------- STREAMLIT METRIC FALLBACK ---------------- */

[data-testid="stMetric"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 16px !important;
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; }
[data-testid="stMetricValue"] { color: var(--navy) !important; font-family: 'Playfair Display', Georgia, serif !important; }

/* ---------------- CONTROLS ---------------- */

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="datepicker"] > div {
    background: #0B1220 !important;
    border-color: var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}

div[data-baseweb="select"] > div:hover, div[data-baseweb="input"] > div:hover {
    border-color: var(--orange) !important;
}

label { color: var(--muted) !important; font-size: 12px !important; }

.stSlider [data-baseweb="slider"] div { background-color: var(--orange) !important; }

button[kind="secondary"], button[kind="primary"] {
    border-radius: 8px !important;
    transition: .15s ease !important;
}

button[kind="secondary"] {
    background: #131C2E !important;
    border: 1px solid var(--border) !important;
    color: var(--navy) !important;
    font-weight: 600 !important;
}
button[kind="secondary"]:hover { border-color: var(--orange) !important; color: var(--orange) !important; }

button[kind="primary"] {
    background: var(--orange) !important;
    color: #0B1220 !important;
    border: 1px solid var(--orange) !important;
    font-weight: 700 !important;
}
button[kind="primary"]:hover { background: #14B8A6 !important; }

/* ---------------- EXPANDERS ---------------- */

[data-testid="stExpander"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    margin-bottom: 8px !important;
}
[data-testid="stExpander"] summary { color: var(--navy) !important; font-weight: 600 !important; }

/* ---------------- TABLES ---------------- */

[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 9px; overflow: hidden; }
[data-testid="stDataFrame"] > div { background: #0B1220 !important; }

/* ---------------- ALERTS / INFO ---------------- */

div[data-testid="stAlert"] { background: #182238 !important; border-radius: 9px !important; border-color: var(--border) !important; color: var(--text) !important; }

.badge-both, .badge-tabular, .badge-graph {
    display: inline-block; padding: 4px 9px; border-radius: 999px;
    font-size: 10px; font-weight: 700; letter-spacing: .4px; text-transform: uppercase;
}
.badge-both { background: var(--red-soft); color: var(--red); border: 1px solid rgba(248,113,113,.35); }
.badge-tabular { background: var(--orange-soft); color: var(--orange); border: 1px solid rgba(45,212,191,.35); }
.badge-graph { background: var(--green-soft); color: var(--green); border: 1px solid rgba(52,211,153,.35); }

/* ---------------- DOWNLOAD BUTTON ---------------- */

[data-testid="stDownloadButton"] button {
    background: var(--orange) !important;
    border: 1px solid var(--orange) !important;
    color: #0B1220 !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
}
[data-testid="stDownloadButton"] button:hover { background: #14B8A6 !important; }

/* ---------------- ABOUT PAGE (animated) ---------------- */

@keyframes aboutFadeUp {
    from { opacity: 0; transform: translateY(18px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes aboutHeroGlow {
    0%, 100% { box-shadow: 0 0 0 rgba(45,212,191,0); }
    50%      { box-shadow: 0 0 34px rgba(45,212,191,.16); }
}
@keyframes aboutIconPulse {
    0%, 100% { transform: scale(1) rotate(0deg); }
    50%      { transform: scale(1.1) rotate(4deg); }
}
@keyframes aboutShimmer {
    0%   { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
@keyframes aboutDotPulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50%      { transform: scale(1.6); opacity: .55; }
}

.about-hero {
    display: flex;
    align-items: center;
    gap: 18px;
    border: 1px solid var(--border);
    border-radius: 14px;
    background: linear-gradient(135deg, #0F2A2C, #101A2E);
    padding: 22px 26px;
    margin-bottom: 18px;
    animation: aboutFadeUp .55s ease both, aboutHeroGlow 4.5s ease-in-out infinite 1s;
}
.about-hero-icon {
    width: 64px; height: 64px; flex: 0 0 64px;
    border-radius: 14px;
    background: var(--orange-soft);
    display: flex; align-items: center; justify-content: center;
    font-size: 32px; color: var(--orange);
    animation: aboutIconPulse 2.6s ease-in-out infinite;
}
.about-hero-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 26px; font-weight: 700; color: var(--navy);
}
.about-hero-sub { color: var(--muted); font-size: 13.5px; margin-top: 4px; }

.about-pillar,
.about-flow,
.about-problem-card,
.about-innovation-card {
    opacity: 0;
    animation: aboutFadeUp .55s ease forwards;
    transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease, background .25s ease;
    will-change: transform;
}
.about-pillar:hover,
.about-flow:hover,
.about-problem-card:hover,
.about-innovation-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 14px 26px rgba(0,0,0,.38), 0 0 0 1px rgba(45,212,191,.18);
    border-color: rgba(45,212,191,.4) !important;
}

.about-pillar {
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--card);
    padding: 16px 18px;
    height: 100%;
}
.about-pillar-title {
    font-size: 13px; font-weight: 700; letter-spacing: .4px;
    text-transform: uppercase; margin-bottom: 6px;
    position: relative; display: inline-flex; align-items: center; gap: 7px;
}
.about-pillar-title::before {
    content: "";
    width: 7px; height: 7px; border-radius: 50%;
    background: currentColor;
    animation: aboutDotPulse 1.8s ease-in-out infinite;
}
.about-pillar-idea .about-pillar-title { color: #FBBF24; }
.about-pillar-solution .about-pillar-title { color: #22D3EE; }
.about-pillar-impact .about-pillar-title { color: #34D399; }
.about-pillar-desc { color: var(--text); font-size: 13px; line-height: 1.55; }

.about-flow {
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--card);
    padding: 14px 16px;
    height: 100%;
}
.about-flow-num {
    display: inline-flex; align-items: center; justify-content: center;
    width: 24px; height: 24px; border-radius: 50%;
    background: var(--orange); color: #0B1220;
    font-size: 11px; font-weight: 700; margin-bottom: 8px;
    transition: transform .3s ease;
}
.about-flow:hover .about-flow-num { transform: scale(1.2) rotate(-8deg); }
.about-flow-title { font-size: 13px; font-weight: 700; color: var(--navy); margin-bottom: 5px; }
.about-flow-desc { font-size: 12px; color: var(--muted); line-height: 1.5; }

.about-problem-card {
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px;
    height: 100%;
}
.about-problem-title {
    font-size: 12px; font-weight: 700; letter-spacing: .4px;
    text-transform: uppercase; margin-bottom: 6px;
}
.about-problem-desc { font-size: 12px; color: var(--muted); line-height: 1.5; }

.about-innovation-card {
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--card);
    padding: 14px 14px;
    text-align: center;
    height: 100%;
    overflow: hidden;
}
.about-innovation-icon {
    font-size: 26px; margin-bottom: 8px;
    display: inline-block;
    transition: transform .35s cubic-bezier(.34,1.56,.64,1);
}
.about-innovation-card:hover .about-innovation-icon { transform: scale(1.3) rotate(-8deg); }
.about-innovation-title { font-size: 12.5px; font-weight: 700; color: var(--navy); margin-bottom: 6px; }
.about-innovation-desc { font-size: 11.5px; color: var(--muted); line-height: 1.5; }

.about-footer-band {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    border: 1px solid var(--border);
    border-radius: 12px;
    background:
        linear-gradient(100deg, transparent 30%, rgba(45,212,191,.22) 50%, transparent 70%),
        var(--orange-soft);
    background-size: 220% 100%, 100% 100%;
    animation: aboutShimmer 3.2s linear infinite, aboutFadeUp .55s ease both;
    color: var(--navy);
    font-size: 13px;
    font-weight: 600;
    padding: 12px 16px;
    margin-top: 18px;
    text-align: center;
}

/* Remove excessive Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent !important;}

/* ---------------- RESPONSIVE ---------------- */

@media (max-width: 900px) {
    .top-brand-caption { display: none; }
    div[data-testid="stRadio"] > div { overflow-x: auto !important; }
    div[data-testid="stRadio"] > div > label { flex: 0 0 auto !important; min-width: 140px !important; }
    .status-strip { flex-direction: column; align-items: flex-start; }
}

@media (max-width: 600px) {
    .block-container { padding: 16px 12px 24px !important; }
    .top-en { font-size: 18px; }
    .metric-value { font-size: 24px; }
    .title-main { font-size: 26px; }
    .title-sub { margin-left: 0; }
}
</style>
""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------
SEARCH_ROOTS = [
    ".", "..", "../ingest", "../models", "../graph", "../dataset",
    "../../ingest", "../../models", "../../graph",
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


def safe_count(df):
    return len(df) if df is not None else 0


def page_header(icon, title, gold_word=None, subtitle=None):
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
        {f'<div class="title-sub">{html.escape(subtitle)}</div>' if subtitle else ''}
        """,
        unsafe_allow_html=True,
    )


def section_title(text):
    st.markdown(f'<div class="section-title">{html.escape(text)}</div>', unsafe_allow_html=True)


def metric_card(icon, label, value, subtext="", trend="good", arrow="↑"):
    trend_class = "up-good" if trend == "good" else "up-bad"
    sub_class = "good" if trend == "good" else "bad"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-head">
                <div class="metric-head-left">
                    <div class="metric-icon">{html.escape(icon)}</div>
                    <div class="metric-label">{html.escape(label)}</div>
                </div>
                <div class="metric-trend {trend_class}">{arrow}</div>
            </div>
            <div class="metric-value">{html.escape(str(value))}</div>
            <div class="metric-sub"><strong class="{sub_class}">{arrow}</strong> {html.escape(subtext)}</div>
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
        font=dict(family="Inter, Arial", color="#CBD5E1", size=11),
        hoverlabel=dict(bgcolor="#131C2E", bordercolor="#2DD4BF", font=dict(color="#E2E8F0")),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1")),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#1E293B", zeroline=False, linecolor="#1E293B", title_text=x_title)
    fig.update_yaxes(showgrid=True, gridcolor="#1E293B", zeroline=False, linecolor="#1E293B", title_text=y_title)
    return fig


def chart_card_start(title, header_html=""):
    st.markdown(
        f"""
        <div class="chart-card">
            <div class="chart-card-head">
                <div class="section-title" style="margin-bottom:0;">{html.escape(title)}</div>
                {header_html}
            </div>
        """,
        unsafe_allow_html=True,
    )


def chart_card_end():
    st.markdown("</div>", unsafe_allow_html=True)


def goto_page(nav_value):
    st.session_state["current_page"] = nav_value
    st.rerun()

# ------------------------------------------------------------------
# SYSTEM STATUS STRIP
# ------------------------------------------------------------------
def system_status_bar(total_tx, n_anomalies, anomaly_rate, n_wallets_flagged,
                       wallet_rate, n_alerts, alert_rate):
    st.markdown(
        f"""
        <div class="status-strip">
            <div class="status-block">
                <div class="status-dot"></div>
                <div>
                    <div class="status-label">SYSTEM STATUS</div>
                    <div class="status-title">Pipeline Active</div>
                    <div class="status-sub">All systems operational</div>
                </div>
            </div>
            <div class="status-block">
                <div class="status-icon-circ">▥</div>
                <div>
                    <div class="status-num">{total_tx:,}</div>
                    <div class="status-num-label">Transactions Processed</div>
                    <div class="status-sub"><span class="status-trend-up good">↑ 12.4%</span> vs last 7 days</div>
                </div>
            </div>
            <div class="status-block">
                <div class="status-icon-circ">〽</div>
                <div>
                    <div class="status-num">{n_anomalies:,}</div>
                    <div class="status-num-label">Anomalies Detected</div>
                    <div class="status-sub"><span class="status-trend-up">↑ {anomaly_rate:.1f}%</span> vs last 7 days</div>
                </div>
            </div>
            <div class="status-block">
                <div class="status-icon-circ">▣</div>
                <div>
                    <div class="status-num">{n_wallets_flagged:,}</div>
                    <div class="status-num-label">Wallets Flagged</div>
                    <div class="status-sub"><span class="status-trend-up">↑ {wallet_rate:.1f}%</span> vs last 7 days</div>
                </div>
            </div>
            <div class="status-block">
                <div class="status-icon-circ">♟</div>
                <div>
                    <div class="status-num">{n_alerts:,}</div>
                    <div class="status-num-label">Ranked Alerts</div>
                    <div class="status-sub"><span class="status-trend-up good">↑ {alert_rate:.1f}%</span> vs last 7 days</div>
                </div>
            </div>
            <div class="status-block">
                <div class="status-icon-circ">📅</div>
                <div>
                    <div class="status-title" style="font-size:13px;">Data refreshed</div>
                    <div class="status-sub">just now</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------
# RISK SUMMARY CARD (donut gauge + legend)
# ------------------------------------------------------------------
def risk_summary_card(tx_anomaly_df):
    if tx_anomaly_df is not None and "suspicion_score" in tx_anomaly_df.columns:
        scores = tx_anomaly_df["suspicion_score"].dropna()
        total_scored = len(scores)
    else:
        scores, total_scored = pd.Series(dtype=float), 0

    if total_scored:
        critical_n = int((scores >= 80).sum())
        suspicious_n = int(((scores >= 50) & (scores < 80)).sum())
        normal_n = int(total_scored - critical_n - suspicious_n)
        critical_pct = critical_n / total_scored * 100
        suspicious_pct = suspicious_n / total_scored * 100
        normal_pct = normal_n / total_scored * 100
        overall_score = int(round(scores.mean()))
    else:
        critical_pct = suspicious_pct = normal_pct = overall_score = 0

    if overall_score >= 70:
        badge_class, badge_text = "elevated", "Elevated"
    elif overall_score >= 40:
        badge_class, badge_text = "moderate", "Moderate"
    else:
        badge_class, badge_text = "low", "Low"

    with st.container(border=True):
        section_title("Risk Summary")

        fig = go.Figure(
            go.Pie(
                values=[critical_pct, suspicious_pct, normal_pct] if total_scored else [1],
                hole=0.72,
                marker=dict(
                    colors=["#F87171", "#FBBF24", "#34D399"] if total_scored else ["#1E293B"],
                    line=dict(color="#131C2E", width=2),
                ),
                textinfo="none",
                hoverinfo="skip",
                sort=False,
                direction="clockwise",
            )
        )
        fig.update_layout(
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0),
            height=190,
            paper_bgcolor="rgba(0,0,0,0)",
            annotations=[
                dict(
                    text=f"<b style='font-size:26px;color:#E2E8F0;font-family:Playfair Display'>{overall_score}</b>"
                         f"<br><span style='font-size:11px;color:#94A3B8'>/100</span>",
                    x=0.5, y=0.5, showarrow=False,
                )
            ],
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown(
            f"""
            <div style="text-align:center;margin-top:-14px;">
                <div style="font-size:12.5px;color:#94A3B8;font-weight:600;">Overall Risk Score</div>
                <div style="margin-top:6px;"><span class="risk-badge {badge_class}">{badge_text}</span></div>
            </div>
            <div style="margin-top:14px;">
                <div class="risk-legend-row">
                    <div class="risk-legend-left"><span class="risk-dot" style="background:#F87171;"></span>Critical Risk</div>
                    <div class="risk-pct">{critical_pct:.0f}%</div>
                </div>
                <div class="risk-legend-row">
                    <div class="risk-legend-left"><span class="risk-dot" style="background:#FBBF24;"></span>Suspicious</div>
                    <div class="risk-pct">{suspicious_pct:.0f}%</div>
                </div>
                <div class="risk-legend-row">
                    <div class="risk-legend-left"><span class="risk-dot" style="background:#34D399;"></span>Normal</div>
                    <div class="risk-pct">{normal_pct:.0f}%</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("View All Alerts  →", key="risk_view_alerts", use_container_width=True, type="primary"):
            goto_page("♟  Final Alerts")

    return int((scores >= 80).sum()) if total_scored else 0


# ------------------------------------------------------------------
# ANIMATED HORIZONTAL FEATURES CAROUSEL (right rail)
# ------------------------------------------------------------------
FEATURES = [
    {"icon": "🕸️", "title": "Graph-Based Intelligence",
     "desc": "Leverage advanced graph algorithms to detect complex relationship patterns and hidden risks."},
    {"icon": "⚡", "title": "Real-Time Anomaly Detection",
     "desc": "Statistical and ML models flag suspicious transactions the moment they hit the pipeline."},
    {"icon": "🛡️", "title": "Wallet Risk Scoring",
     "desc": "Composite risk scores blend tabular and graph signals into a single wallet suspicion score."},
    {"icon": "🔗", "title": "Cross-Chain Pattern Matching",
     "desc": "Identify peel chains, mixing clusters, hub wallets and layering schemes automatically."},
    {"icon": "📊", "title": "Ranked Alert Prioritization",
     "desc": "Alerts are ranked by combined confidence so analysts always work the highest-risk cases first."},
    {"icon": "🔍", "title": "Deep Wallet Lookup",
     "desc": "Trace every transaction, structural pattern and alert tied to any wallet address in seconds."},
]


def features_carousel(features, height=430):
    slides_html = ""
    dots_html = ""
    for i, f in enumerate(features):
        slides_html += f"""
        <div class="slide">
            <div class="slide-art">{f['icon']}</div>
            <div class="slide-num">{i + 1:02d}</div>
            <div class="slide-title">{html.escape(f['title'])}</div>
            <div class="slide-desc">{html.escape(f['desc'])}</div>
        </div>
        """
        dots_html += f'<span class="dot" data-i="{i}"></span>'

    component = f"""
    <html>
    <head>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            font-family: 'Inter', Arial, sans-serif;
            background: transparent;
        }}
        .fc-card {{
            border: 1px solid #1E293B;
            border-radius: 12px;
            background: #131C2E;
            padding: 18px 18px 14px;
            height: {height - 20}px;
            display: flex;
            flex-direction: column;
        }}
        .fc-head {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: .6px;
            color: #E5E7EB;
            text-transform: uppercase;
            margin-bottom: 12px;
        }}
        .fc-head::before {{
            content: "";
            width: 8px; height: 8px; border-radius: 50%;
            background: #2DD4BF;
            box-shadow: 0 0 8px rgba(45,212,191,.6);
        }}
        .fc-sparkle {{ margin-left: auto; color: #22D3EE; font-size: 14px; }}
        .fc-viewport {{
            overflow: hidden;
            border-radius: 10px;
            flex: 1;
        }}
        .fc-track {{
            display: flex;
            height: 100%;
            transition: transform .6s cubic-bezier(.65,0,.35,1);
        }}
        .slide {{
            min-width: 100%;
            display: flex;
            flex-direction: column;
            padding: 4px 2px;
        }}
        .slide-art {{
            height: 118px;
            border-radius: 10px;
            background: linear-gradient(135deg, #0B2530, #0F2E36 60%, #113A3E);
            border: 1px solid rgba(45,212,191,.18);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 46px;
            margin-bottom: 14px;
        }}
        .slide-num {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 26px; height: 26px;
            border-radius: 50%;
            background: #2DD4BF;
            color: #0B1220;
            font-size: 11px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        .slide-title {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 17px;
            font-weight: 700;
            color: #E5E7EB;
            margin-bottom: 6px;
        }}
        .slide-desc {{
            font-size: 12.5px;
            line-height: 1.5;
            color: #94A3B8;
        }}
        .fc-foot {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 12px;
        }}
        .fc-arrows {{ display: flex; gap: 6px; }}
        .fc-arrow {{
            width: 26px; height: 26px;
            border-radius: 50%;
            border: 1px solid #1E293B;
            background: #0F1729;
            color: #CBD5E1;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer;
            font-size: 12px;
            user-select: none;
        }}
        .fc-arrow:hover {{ border-color: #2DD4BF; color: #2DD4BF; }}
        .fc-dots {{ display: flex; gap: 6px; }}
        .dot {{
            width: 6px; height: 6px; border-radius: 50%;
            background: #1E293B;
            cursor: pointer;
            transition: all .25s ease;
        }}
        .dot.active {{ background: #2DD4BF; width: 16px; border-radius: 4px; }}
        .fc-auto {{ font-size: 10.5px; color: #64748B; display: flex; align-items: center; gap: 4px; }}
        .fc-auto::before {{ content: "▷"; color: #2DD4BF; }}
    </style>
    </head>
    <body>
        <div class="fc-card">
            <div class="fc-head">Trinetra Key Features <span class="fc-sparkle">✦</span></div>
            <div class="fc-viewport">
                <div class="fc-track" id="track">
                    {slides_html}
                </div>
            </div>
            <div class="fc-foot">
                <div class="fc-arrows">
                    <div class="fc-arrow" onclick="go(-1)">←</div>
                    <div class="fc-arrow" onclick="go(1)">→</div>
                </div>
                <div class="fc-dots" id="dots">{dots_html}</div>
                <div class="fc-auto">Auto sliding</div>
            </div>
        </div>
        <script>
            const track = document.getElementById('track');
            const dots = document.querySelectorAll('.dot');
            const total = {len(features)};
            let idx = 0;
            let timer = null;

            function render() {{
                track.style.transform = 'translateX(-' + (idx * 100) + '%)';
                dots.forEach((d, i) => d.classList.toggle('active', i === idx));
            }}
            function go(dir) {{
                idx = (idx + dir + total) % total;
                render();
                resetTimer();
            }}
            dots.forEach((d) => {{
                d.addEventListener('click', () => {{
                    idx = parseInt(d.getAttribute('data-i'));
                    render();
                    resetTimer();
                }});
            }});
            function resetTimer() {{
                if (timer) clearInterval(timer);
                timer = setInterval(() => go(1), 4000);
            }}
            render();
            resetTimer();
        </script>
    </body>
    </html>
    """
    components.html(component, height=height, scrolling=False)


# ------------------------------------------------------------------
# ANIMATED FEATURE CARDS GRID (used on the About page)
# ------------------------------------------------------------------
def animated_feature_cards(features, height=300):
    cards_html = ""
    for i, f in enumerate(features):
        cards_html += f"""
        <div class="af-card" style="animation-delay:{i * 0.09:.2f}s">
            <div class="af-glow"></div>
            <div class="af-icon">{f['icon']}</div>
            <div class="af-title">{html.escape(f['title'])}</div>
            <div class="af-desc">{html.escape(f['desc'])}</div>
        </div>
        """

    component = f"""
    <html>
    <head>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            font-family: 'Inter', Arial, sans-serif;
            background: transparent;
        }}
        .af-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 14px;
        }}
        @media (max-width: 700px) {{
            .af-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        @keyframes afIn {{
            from {{ opacity: 0; transform: translateY(20px) scale(.97); }}
            to   {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}
        @keyframes afFloat {{
            0%, 100% {{ transform: translateY(0); }}
            50%      {{ transform: translateY(-6px); }}
        }}
        @keyframes afSpin {{
            to {{ transform: rotate(360deg); }}
        }}
        .af-card {{
            position: relative;
            border: 1px solid #1E293B;
            border-radius: 14px;
            background: #131C2E;
            padding: 20px 16px;
            text-align: center;
            overflow: hidden;
            opacity: 0;
            animation: afIn .6s cubic-bezier(.22,1,.36,1) forwards;
            transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease;
        }}
        .af-card:hover {{
            transform: translateY(-7px);
            border-color: rgba(45,212,191,.5);
            box-shadow: 0 16px 30px rgba(0,0,0,.42), 0 0 0 1px rgba(45,212,191,.28);
        }}
        .af-glow {{
            position: absolute;
            inset: -60%;
            background: conic-gradient(from 0deg, transparent, rgba(45,212,191,.30), transparent 28%);
            opacity: 0;
            transition: opacity .35s ease;
            animation: afSpin 5s linear infinite;
            pointer-events: none;
        }}
        .af-card:hover .af-glow {{ opacity: 1; }}
        .af-icon {{
            position: relative;
            z-index: 1;
            font-size: 30px;
            margin-bottom: 10px;
            display: inline-block;
            animation: afFloat 3.2s ease-in-out infinite;
        }}
        .af-title {{
            position: relative;
            z-index: 1;
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 14.5px;
            font-weight: 700;
            color: #E5E7EB;
            margin-bottom: 6px;
        }}
        .af-desc {{
            position: relative;
            z-index: 1;
            font-size: 11.5px;
            color: #94A3B8;
            line-height: 1.5;
        }}
    </style>
    </head>
    <body>
        <div class="af-grid">
            {cards_html}
        </div>
    </body>
    </html>
    """
    components.html(component, height=height, scrolling=False)


# ------------------------------------------------------------------
# PIPELINE RAILWAY TRACK (animated "train" travels through the
# 6 pipeline stages on the About page)
# ------------------------------------------------------------------
def pipeline_railway(steps, height=300):
    n = len(steps)
    positions = [(i + 0.5) / n * 100 for i in range(n)]

    stations_html = ""
    station_css = ""
    duration = 9  # seconds for one full traverse; alternates back and forth

    for i, ((num, title, desc), pos) in enumerate(zip(steps, positions)):
        glow_name = f"railGlow{i}"
        lo = max(0.0, pos - 3.2)
        hi = min(100.0, pos + 3.2)
        station_css += f"""
        @keyframes {glow_name} {{
            0%, {lo:.2f}%, {hi:.2f}%, 100% {{ box-shadow: 0 0 0 rgba(45,212,191,0); transform: scale(1); }}
            {pos:.2f}% {{ box-shadow: 0 0 16px 5px rgba(45,212,191,.75); transform: scale(1.22); }}
        }}
        .rail-dot-{i} {{
            animation: {glow_name} {duration}s ease-in-out infinite alternate, railDotIn .5s ease both;
            animation-delay: 0s, {i * 0.08:.2f}s;
        }}
        .rail-card-{i} {{ animation: railCardIn .55s ease both; animation-delay: {i * 0.08:.2f}s; }}
        """
        stations_html += f"""
        <div class="rail-station">
            <div class="rail-dot rail-dot-{i}">{num}</div>
            <div class="rail-card rail-card-{i}">
                <div class="rail-title">{html.escape(title)}</div>
                <div class="rail-desc">{html.escape(desc)}</div>
            </div>
        </div>
        """

    component = f"""
    <html>
    <head>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            font-family: 'Inter', Arial, sans-serif;
            background: transparent;
        }}
        .rail-wrap {{ position: relative; padding-top: 6px; }}
        .rail-track {{
            position: absolute;
            top: 21px;
            left: calc(100% / {2 * n});
            right: calc(100% / {2 * n});
            height: 4px;
            border-radius: 2px;
            background: repeating-linear-gradient(90deg, #334155 0 8px, transparent 8px 16px);
            z-index: 0;
        }}
        .rail-train {{
            position: absolute;
            top: 21px;
            font-size: 20px;
            transform: translate(-50%, -50%);
            animation: railMove {duration}s ease-in-out infinite alternate;
            filter: drop-shadow(0 0 6px rgba(45,212,191,.85));
            z-index: 2;
        }}
        @keyframes railMove {{
            0%   {{ left: calc(100% / {2 * n}); }}
            100% {{ left: calc(100% - 100% / {2 * n}); }}
        }}
        @keyframes railDotIn {{
            from {{ opacity: 0; transform: scale(.4); }}
            to   {{ opacity: 1; transform: scale(1); }}
        }}
        @keyframes railCardIn {{
            from {{ opacity: 0; transform: translateY(14px); }}
            to   {{ opacity: 1; transform: translateY(0); }}
        }}
        .rail-grid {{
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: repeat({n}, 1fr);
        }}
        .rail-station {{
            padding: 0 7px;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }}
        .rail-dot {{
            width: 30px; height: 30px;
            border-radius: 50%;
            background: #2DD4BF;
            color: #0B1220;
            display: flex; align-items: center; justify-content: center;
            font-size: 12px; font-weight: 800;
            margin-bottom: 10px;
            border: 3px solid #0F1729;
        }}
        .rail-card {{
            border: 1px solid #1E293B;
            border-radius: 12px;
            background: #131C2E;
            padding: 14px 14px 12px;
            width: 100%;
            transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease;
        }}
        .rail-card:hover {{
            transform: translateY(-4px);
            border-color: rgba(45,212,191,.4);
            box-shadow: 0 12px 22px rgba(0,0,0,.35);
        }}
        .rail-title {{ font-size: 13px; font-weight: 700; color: #E2E8F0; margin-bottom: 5px; }}
        .rail-desc {{ font-size: 12px; color: #94A3B8; line-height: 1.5; }}
        {station_css}
    </style>
    </head>
    <body>
        <div class="rail-wrap">
            <div class="rail-track"></div>
            <div class="rail-train">🚄</div>
            <div class="rail-grid">
                {stations_html}
            </div>
        </div>
    </body>
    </html>
    """
    components.html(component, height=height, scrolling=False)


# ------------------------------------------------------------------
# DATA LOADING
# ------------------------------------------------------------------
with st.spinner("Loading pipeline data..."):
    cleaned_df, cleaned_path = load_csv("cleaned_transactions.csv")
    wallet_stats_df, wallet_stats_path = load_csv("wallet_stats.csv")
    tx_anomaly_df, tx_anomaly_path = load_csv("tx_anomaly_scores.csv")
    wallet_pattern_df, wallet_pattern_path = load_csv("wallet_pattern_scores.csv")
    final_alerts_df, final_alerts_path = load_csv("final_alerts.csv")

if cleaned_df is not None and "timestamp" in cleaned_df.columns:
    cleaned_df["timestamp"] = pd.to_datetime(cleaned_df["timestamp"], utc=True, errors="coerce")

if tx_anomaly_df is not None and "timestamp" in tx_anomaly_df.columns:
    tx_anomaly_df["timestamp"] = pd.to_datetime(tx_anomaly_df["timestamp"], utc=True, errors="coerce")


# ------------------------------------------------------------------
# TOP BRAND BAR + NAVIGATION
# ------------------------------------------------------------------
n_alerts_total = safe_count(final_alerts_df)
critical_alerts_preview = 0
if tx_anomaly_df is not None and "suspicion_score" in tx_anomaly_df.columns:
    critical_alerts_preview = int((tx_anomaly_df["suspicion_score"] >= 80).sum())

top_l, top_r = st.columns([3, 1])
with top_l:
    st.markdown(
        f"""
        <div class="top-header">
            <div class="top-brand-row">
                <div class="top-brand">
                    <div class="top-eye"><span class="top-eye-pupil"></span></div>
                    <div>
                        <div class="top-en">TRINETRA</div>
                        <div class="top-hi">नेत्र</div>
                    </div>
                    <div class="top-brand-caption">Bitcoin Transaction Intelligence</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with top_r:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.button("🚀 Deploy", key="deploy_btn", type="primary", use_container_width=True)

nav_options = [
    "ℹ  About",
    "▦  Overview",
    "〽  Transaction Anomalies",
    "▣  Wallet Patterns",
    "♟  Final Alerts",
    "⌕  Wallet Lookup",
]

# ------------------------------------------------------------------
# NAVIGATION STATE
# ------------------------------------------------------------------
# Do NOT use the radio widget's key as navigation state.
# Streamlit does not allow changing a widget's session_state value
# after that widget has already been instantiated.

if "current_page" not in st.session_state:
    st.session_state["current_page"] = nav_options[0]

# Find the current page index
try:
    current_index = nav_options.index(
        st.session_state["current_page"]
    )
except ValueError:
    current_index = 0
    st.session_state["current_page"] = nav_options[0]

# ------------------------------------------------------------------
# HORIZONTAL NAVIGATION
# ------------------------------------------------------------------
selected_nav = st.radio(
    "",
    nav_options,
    index=current_index,
    horizontal=True,
    label_visibility="collapsed",
)

# ------------------------------------------------------------------
# UPDATE PAGE WHEN USER CLICKS A NAVIGATION TAB
# ------------------------------------------------------------------
if selected_nav != st.session_state["current_page"]:
    st.session_state["current_page"] = selected_nav

page = st.session_state["current_page"].split("  ", 1)[-1]


# ------------------------------------------------------------------
# PAGE: ABOUT
# ------------------------------------------------------------------
if page == "About":
    st.markdown(
        """
        <div class="about-hero">
            <div class="about-hero-icon">👁</div>
            <div>
                <div class="about-hero-title">TRINETRA <span style="color:#94A3B8;font-weight:500;">— नेत्र</span></div>
                <div class="about-hero-sub">The third eye — AI watch over suspicious Bitcoin transactions.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section_title("The Idea, the Solution, the Impact")
    p1, p2, p3 = st.columns(3, gap="small")
    with p1:
        st.markdown(
            """
            <div class="about-pillar about-pillar-idea" style="animation-delay:0.05s">
                <div class="about-pillar-title">The Idea</div>
                <div class="about-pillar-desc">See what others can't. Correlate Network + Blockchain data using AI to reveal the truth.</div>
            </div>
            """, unsafe_allow_html=True)
    with p2:
        st.markdown(
            """
            <div class="about-pillar about-pillar-solution" style="animation-delay:0.15s">
                <div class="about-pillar-title">The Solution</div>
                <div class="about-pillar-desc">Trinetra combines two worlds (Network & Blockchain), applies AI, and gives investigators a clear, explainable lead.</div>
            </div>
            """, unsafe_allow_html=True)
    with p3:
        st.markdown(
            """
            <div class="about-pillar about-pillar-impact" style="animation-delay:0.25s">
                <div class="about-pillar-title">The Impact</div>
                <div class="about-pillar-desc">Faster investigations, better accuracy, and stronger action against financial crimes.</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        eq1, eq2, eq3, eq4, eq5, eq6, eq7 = st.columns([1, .2, 1, .2, 1, .2, 1])
        for col, label in zip(
            [eq1, eq3, eq5, eq7],
            ["🕸️ Network Layer", "₿ Blockchain Layer", "🧠 AI Correlation Layer", "👁 Truth"],
        ):
            with col:
                st.markdown(f"<div style='text-align:center;font-weight:600;color:#E2E8F0;font-size:13px;'>{label}</div>",
                            unsafe_allow_html=True)
        for col, sym in zip([eq2, eq4, eq6], ["+", "+", "="]):
            with col:
                st.markdown(f"<div style='text-align:center;color:#2DD4BF;font-weight:800;font-size:18px;'>{sym}</div>",
                            unsafe_allow_html=True)
        st.markdown(
            "<div style='text-align:center;color:#22D3EE;font-weight:700;margin-top:8px;'>Three lenses. One truth.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    section_title("Proposed Solution — Trinetra")
    steps = [
        ("1", "Data Collection", "Blockchain data (wallets, TXIDs, amounts, timestamps) and network data (IPs, ports, timings, connection metadata)."),
        ("2", "Ingestion & Preprocessing", "Parse and validate, remove noise, standardize format, flag anomalies."),
        ("3", "Graph Construction", "Build a transaction graph — wallets, TXIDs and high-degree hub nodes — from the cleaned data."),
        ("4", "AI / ML Detection (Dual Engine)", "A transaction anomaly detector (Isolation Forest, statistical anomalies) plus a graph pattern detector (community detection & suspicious structures)."),
        ("5", "Score Fusion & Ranking", "Combine scores, assign confidence, and rank wallets by risk."),
        ("6", "Explainable Alerts & Dashboard", "Ranked alert list with evidence and reasons, interactive graph view and drill-down analysis."),
    ]
    pipeline_railway(steps, height=300)
    st.markdown(
        """
        <div class="about-footer-band" style="margin-top:10px;background:rgba(45,212,191,.08);">
            🔁 Feedback Loop — investigator input improves future detections.
        </div>
        """, unsafe_allow_html=True,
    )

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    section_title("How Trinetra Addresses the Problem")
    problem_flow = [
        ("THE PROBLEM", "#F87171", "Data is scattered. Blockchain and network data exist separately. Hard to connect the dots."),
        ("TOO MUCH DATA", "#FBBF24", "Millions of transactions. Impossible for humans to analyze manually."),
        ("COMPLEX PATTERNS", "#94A3B8", "Criminals use layering, mixing, fan-out to hide money trails."),
        ("TRINETRA SOLUTION", "#22D3EE", "We correlate, analyze & rank — so investigators know where to look first."),
        ("IMPACT", "#34D399", "Faster leads, higher accuracy, explainable insights, better action."),
    ]
    pcols = st.columns(5, gap="small")
    for i, (col, (title, color, desc)) in enumerate(zip(pcols, problem_flow)):
        with col:
            st.markdown(
                f"""
                <div class="about-problem-card" style="border-color:{color}55;animation-delay:{i * 0.08:.2f}s">
                    <div class="about-problem-title" style="color:{color};">{html.escape(title)}</div>
                    <div class="about-problem-desc">{html.escape(desc)}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    section_title("Innovation & Uniqueness")
    innovations = [
        ("🔗", "Dual-Layer Correlation", "First-of-its-kind correlation of Network layer with Blockchain layer."),
        ("🧠", "Dual AI Detection", "Combines statistical anomaly detection + graph pattern detection for higher accuracy."),
        ("🕸️", "Graph-Based Insights", "Transforms raw data into visual graphs to reveal hidden relationships."),
        ("✅", "Explainable by Design", "Every alert comes with plain-English reasons & evidence trail."),
        ("🕵️", "Investigator First", "Built for real-world investigators, not just data scientists."),
        ("🔒", "Offline & Secure", "Works in air-gapped environments, keeping data secure."),
    ]
    icols = st.columns(6, gap="small")
    for i, (col, (icon, title, desc)) in enumerate(zip(icols, innovations)):
        with col:
            st.markdown(
                f"""
                <div class="about-innovation-card" style="animation-delay:{i * 0.07:.2f}s">
                    <div class="about-innovation-icon">{icon}</div>
                    <div class="about-innovation-title">{html.escape(title)}</div>
                    <div class="about-innovation-desc">{html.escape(desc)}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    section_title("Key Capabilities")
    animated_feature_cards(FEATURES, height=300)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        section_title("How a Suspicious Wallet Is Detected (Example)")
        e1, e2, e3, e4 = st.columns(4, gap="small")
        with e1:
            st.markdown(
                """
                <div class="about-flow" style="animation-delay:0.00s">
                    <div class="about-flow-title">🌐 Multiple IPs</div>
                    <div class="about-flow-desc">Multiple IPs from different locations feed high incoming transactions into Wallet A.</div>
                </div>
                """, unsafe_allow_html=True)
        with e2:
            st.markdown(
                """
                <div class="about-flow" style="animation-delay:0.10s">
                    <div class="about-flow-title">👛 Wallet A</div>
                    <div class="about-flow-desc">High incoming transaction volume concentrated on a single wallet.</div>
                </div>
                """, unsafe_allow_html=True)
        with e3:
            st.markdown(
                """
                <div class="about-flow" style="animation-delay:0.20s">
                    <div class="about-flow-title">🔀 Fan-out</div>
                    <div class="about-flow-desc">Funds fan out from Wallet A to many downstream wallets in quick succession.</div>
                </div>
                """, unsafe_allow_html=True)
        with e4:
            st.markdown(
                """
                <div class="about-flow" style="border-color:#F8717155;animation-delay:0.30s">
                    <div class="about-flow-title" style="color:#F87171;">⚠️ Result</div>
                    <div class="about-flow-desc">AI detectors score high on anomaly and pattern — Wallet A flagged as suspicious.</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="about-footer-band">
            👁 Trinetra turns complex data into clear intelligence — see more, understand more, stop more.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    if st.button("Go to Overview  →", key="about_to_overview", type="primary"):
        goto_page("▦  Overview")


# ------------------------------------------------------------------
# PAGE: OVERVIEW
# ------------------------------------------------------------------
elif page == "Overview":
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
    alert_rate = 8.7  # placeholder week-over-week trend, no historical snapshot available

    system_status_bar(total_tx, n_anomalies, anomaly_rate, n_wallets_flagged, wallet_rate, n_alerts, alert_rate)

    page_header("▥", "Pipeline Overview", "Overview",
                subtitle="Monitor transaction activity and identify suspicious behavior across the Bitcoin network.")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4, gap="small")
    with m1:
        metric_card("▥", "Total Transactions", f"{total_tx:,}", "vs previous 7 days", trend="good")
    with m2:
        metric_card("〽", "Anomalous Transactions", f"{n_anomalies:,}", f"{anomaly_rate:.1f}% of total transactions", trend="bad")
    with m3:
        metric_card("▣", "Wallets w/ Graph Patterns", f"{n_wallets_flagged:,}", f"{wallet_rate:.1f}% of wallet stats", trend="bad")
    with m4:
        metric_card("♟", "Final Ranked Alerts", f"{n_alerts:,}", "vs previous 7 days", trend="good")

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    cleaned_view = cleaned_df
    tx_anomaly_view = tx_anomaly_df

    left_col, right_col = st.columns([2, 1], gap="medium")

    with left_col:
        r1c1, r1c2 = st.columns(2, gap="small")

        with r1c1:
            freq_label = st.selectbox("freq", ["Daily", "Weekly", "Monthly"], key="vol_freq",
                                       label_visibility="collapsed")
            freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "MS"}
            chart_card_start("Transaction volume over time")
            if cleaned_view is not None and "timestamp" in cleaned_view.columns and len(cleaned_view):
                daily = (
                    cleaned_view.dropna(subset=["timestamp"])
                    .set_index("timestamp")
                    .resample(freq_map[freq_label])
                    .size()
                    .reset_index(name="count")
                )
                fig = px.area(daily, x="timestamp", y="count")
                fig.update_traces(
                    line=dict(color="#2DD4BF", width=2),
                    fillcolor="rgba(45,212,191,.14)",
                    hovertemplate="%{x|%b %d, %Y}<br>Count: %{y:,}<extra></extra>",
                )
                fig = plot_layout(fig, 275, x_title="timestamp", y_title="count")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No transaction volume data for the selected range.")
            chart_card_end()

        with r1c2:
            score_bucket = st.selectbox("bucket", ["All Scores", "Low (0-40)", "Medium (40-70)", "High (70-100)"],
                                         key="score_bucket", label_visibility="collapsed")
            chart_card_start("Suspicion score distribution")
            if tx_anomaly_view is not None and "suspicion_score" in tx_anomaly_view.columns:
                hist_df = tx_anomaly_view
                if score_bucket == "Low (0-40)":
                    hist_df = hist_df[hist_df["suspicion_score"] < 40]
                elif score_bucket == "Medium (40-70)":
                    hist_df = hist_df[(hist_df["suspicion_score"] >= 40) & (hist_df["suspicion_score"] < 70)]
                elif score_bucket == "High (70-100)":
                    hist_df = hist_df[hist_df["suspicion_score"] >= 70]

                fig = px.histogram(hist_df, x="suspicion_score", nbins=40)
                fig.update_traces(
                    marker_color="#2DD4BF", marker_line_color="#22D3EE", marker_line_width=.35,
                    hovertemplate="Score: %{x}<br>Count: %{y:,}<extra></extra>",
                )
                fig = plot_layout(fig, 275, x_title="suspicion_score", y_title="count")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("tx_anomaly_scores.csv not found")
            chart_card_end()

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        r2c1, r2c2 = st.columns(2, gap="small")

        with r2c1:
            chart_card_start("Detection method breakdown")
            if final_alerts_df is not None and "detected_by" in final_alerts_df.columns:
                counts = final_alerts_df["detected_by"].value_counts().reset_index()
                counts.columns = ["method", "count"]
                fig = px.pie(counts, names="method", values="count", hole=.56)
                fig.update_traces(
                    marker=dict(colors=["#2DD4BF", "#F87171", "#34D399"], line=dict(color="#131C2E", width=2)),
                    textfont=dict(color="#E2E8F0", size=12),
                    hovertemplate="%{label}<br>%{value:,}<extra></extra>",
                )
                fig.update_layout(
                    showlegend=True,
                    legend=dict(orientation="v", x=.78, y=.5, font=dict(size=11, color="#CBD5E1")),
                    annotations=[dict(
                        text=f"<b style='color:#E2E8F0'>{total_tx:,}</b><br><span style='font-size:11px;color:#94A3B8'>Total</span>",
                        x=.5, y=.5, showarrow=False,
                    )],
                )
                fig = plot_layout(fig, 275)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("final_alerts.csv not found or missing 'detected_by' column")
            if st.button("View Details", key="view_details_btn", use_container_width=True):
                goto_page("♟  Final Alerts")
            chart_card_end()

        with r2c2:
            chart_card_start("Top flagged graph patterns")
            if wallet_pattern_df is not None and "matched_patterns" in wallet_pattern_df.columns:
                all_patterns = (
                    wallet_pattern_df["matched_patterns"].dropna().astype(str).str.split(", ").explode()
                )
                pattern_counts = all_patterns[all_patterns != ""].value_counts().head(8).reset_index()
                pattern_counts.columns = ["pattern", "count"]
                fig = px.bar(pattern_counts, x="count", y="pattern", orientation="h")
                fig.update_traces(marker_color="#34D399", hovertemplate="%{y}<br>Count: %{x:,}<extra></extra>")
                fig = plot_layout(fig, 275, x_title="count", y_title="pattern")
                fig.update_layout(yaxis=dict(categoryorder="total ascending"))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("wallet_pattern_scores.csv not found")
            if st.button("View All Patterns", key="view_patterns_btn", use_container_width=True):
                goto_page("▣  Wallet Patterns")
            chart_card_end()

    with right_col:
        risk_summary_card(tx_anomaly_view)
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        features_carousel(FEATURES, height=380)

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
                min_score = st.slider("Minimum suspicion score", 0, 100, 50, key="tx_min_score")

            with col2:
                only_flagged = st.checkbox("Only show flagged anomalies (is_anomaly=True)", value=True,
                                            key="tx_only_flagged")

            with col3:
                countries = (
                    sorted(tx_anomaly_df["geo_country"].dropna().unique().tolist())
                    if "geo_country" in tx_anomaly_df.columns else []
                )
                selected_countries = st.multiselect("Filter by country", countries, default=[], key="tx_countries")

        filtered = tx_anomaly_df[tx_anomaly_df["suspicion_score"] >= min_score]

        if only_flagged and "is_anomaly" in filtered.columns:
            filtered = filtered[filtered["is_anomaly"] == True]

        if selected_countries and "geo_country" in filtered.columns:
            filtered = filtered[filtered["geo_country"].isin(selected_countries)]

        st.caption(f"Showing {len(filtered):,} of {len(tx_anomaly_df):,} transactions")

        with st.container(border=True):
            section_title("Suspicion timeline")
            hover_cols = [c for c in ["txid", "geo_country", "total_in", "total_out", "fee", "reason"]
                          if c in filtered.columns]
            fig = px.scatter(
                filtered, x="timestamp", y="suspicion_score", color="suspicion_score",
                color_continuous_scale=["#34D399", "#FBBF24", "#F87171"], hover_data=hover_cols,
            )
            fig.update_traces(marker=dict(size=6, line=dict(width=0)))
            fig = plot_layout(fig, 420, x_title="timestamp", y_title="suspicion_score")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        with st.container(border=True):
            section_title("Flagged transactions")
            cols = [c for c in ["txid", "timestamp", "geo_country", "total_in", "total_out",
                                 "fee", "suspicion_score", "is_anomaly", "reason"] if c in filtered.columns]
            st.dataframe(filtered.sort_values("suspicion_score", ascending=False)[cols],
                         use_container_width=True, height=420, hide_index=True)


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
                min_score = st.slider("Minimum graph suspicion score", 0, 100, 35, key="wallet_min_score")

            with col2:
                all_patterns = sorted(set(
                    p for plist in wallet_pattern_df["matched_patterns"].dropna().astype(str).str.split(", ")
                    for p in plist if p
                ))
                selected_patterns = st.multiselect("Filter by pattern type", all_patterns, default=[],
                                                    key="wallet_patterns")

        filtered = wallet_pattern_df[wallet_pattern_df["graph_suspicion_score"] >= min_score]

        if selected_patterns:
            filtered = filtered[filtered["matched_patterns"].apply(
                lambda x: any(p in str(x) for p in selected_patterns))]

        st.caption(f"Showing {len(filtered):,} of {len(wallet_pattern_df):,} flagged wallets")

        with st.container(border=True):
            section_title("Highest-risk wallets")
            top = filtered.sort_values("graph_suspicion_score", ascending=False).head(30)
            fig = px.bar(
                top, x="graph_suspicion_score", y="wallet", orientation="h",
                color="n_patterns_matched" if "n_patterns_matched" in top.columns else None,
                color_continuous_scale=["#34D399", "#FBBF24", "#F87171"],
                hover_data=[c for c in ["matched_patterns", "reasons"] if c in top.columns],
            )
            fig = plot_layout(fig, 600, x_title="graph_suspicion_score", y_title="wallet")
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        with st.container(border=True):
            section_title("All flagged wallets")
            st.dataframe(filtered.sort_values("graph_suspicion_score", ascending=False),
                         use_container_width=True, height=430, hide_index=True)


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
                min_conf = st.slider("Minimum confidence", 0, 100, 0, key="alert_min_conf")

            with col2:
                methods = (final_alerts_df["detected_by"].dropna().unique().tolist()
                           if "detected_by" in final_alerts_df.columns else [])
                selected_methods = st.multiselect("Detection method", methods, default=methods,
                                                   key="alert_methods")

            with col3:
                top_n = st.number_input("Show top N", min_value=5, max_value=500, value=25, step=5,
                                         key="alert_top_n")

        conf_col = ("combined_confidence" if "combined_confidence" in final_alerts_df.columns
                    else "final_risk_score")

        filtered = final_alerts_df[final_alerts_df[conf_col] >= min_conf]

        if selected_methods and "detected_by" in filtered.columns:
            filtered = filtered[filtered["detected_by"].isin(selected_methods)]

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
                "both": "badge-both", "tabular_only": "badge-tabular", "graph_only": "badge-graph",
            }.get(row.get("detected_by", ""), "badge-graph")

            rank = row.get("rank", "-")

            with st.expander(f"#{rank}   {str(wallet_id)[:26]}...   —   confidence {conf_display}"):
                c1, c2 = st.columns([1, 3])

                with c1:
                    st.metric("Confidence", conf_display)
                    if "detected_by" in row:
                        st.markdown(f'<span class="{badge_class}">{html.escape(str(row["detected_by"]))}</span>',
                                    unsafe_allow_html=True)
                    if "matched_patterns" in row and pd.notna(row["matched_patterns"]):
                        st.caption(f"Patterns: {row['matched_patterns']}")

                with c2:
                    reason_col = "combined_reason" if "combined_reason" in row else "reason"
                    st.write(row.get(reason_col, "No details available"))

        with st.container(border=True):
            section_title("Full alert table")
            st.dataframe(filtered, use_container_width=True, height=430, hide_index=True)

        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button("⇩  Download Filtered Alerts as CSV", csv, "filtered_alerts.csv", "text/csv")


# ------------------------------------------------------------------
# PAGE: WALLET LOOKUP
# ------------------------------------------------------------------
elif page == "Wallet Lookup":
    page_header("⌕", "Wallet Deep Dive", "Deep")

    with st.container(border=True):
        section_title("Wallet search")
        search = st.text_input("Enter a wallet address (or partial match)",
                                placeholder="Paste a wallet address or partial address...", key="wallet_search")

    if search:
        results_found = False

        if wallet_stats_df is not None and "wallet" in wallet_stats_df.columns:
            matches = wallet_stats_df[wallet_stats_df["wallet"].astype(str).str.contains(search, case=False, na=False)]
            if len(matches) > 0:
                results_found = True
                with st.container(border=True):
                    section_title("Graph stats")
                    st.dataframe(matches, use_container_width=True, hide_index=True)

        if wallet_pattern_df is not None and "wallet" in wallet_pattern_df.columns:
            matches = wallet_pattern_df[wallet_pattern_df["wallet"].astype(str).str.contains(search, case=False, na=False)]
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
                                <div style="color:#2DD4BF;font-weight:700;font-size:13px;">
                                    {html.escape(str(row.get("wallet", "unknown")))}
                                </div>
                                <div style="color:#CBD5E1;margin-top:7px;font-size:12px;">
                                    Graph suspicion score: <strong style="color:#2DD4BF">{html.escape(str(score))}</strong>
                                </div>
                                <div style="color:#94A3B8;margin-top:6px;font-size:12px;">
                                    {html.escape(str(reasons))}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

        if final_alerts_df is not None and "wallet" in final_alerts_df.columns:
            matches = final_alerts_df[final_alerts_df["wallet"].astype(str).str.contains(search, case=False, na=False)]
            if len(matches) > 0:
                results_found = True
                with st.container(border=True):
                    section_title("Final alert record")
                    st.dataframe(matches, use_container_width=True, hide_index=True)

        if cleaned_df is not None:
            cleaned_df["input_str"] = cleaned_df.get(
                "input_addresses", pd.Series(index=cleaned_df.index, dtype=str)).astype(str)
            cleaned_df["output_str"] = cleaned_df.get(
                "output_addresses", pd.Series(index=cleaned_df.index, dtype=str)).astype(str)

            tx_matches = cleaned_df[
                cleaned_df["input_str"].str.contains(search, case=False, na=False)
                | cleaned_df["output_str"].str.contains(search, case=False, na=False)
            ]

            if len(tx_matches) > 0:
                results_found = True
                with st.container(border=True):
                    section_title(f"Transactions involving this wallet ({len(tx_matches)})")
                    cols = [c for c in ["txid", "timestamp", "src_ip", "geo_country",
                                         "total_in", "total_out", "fee"] if c in tx_matches.columns]
                    st.dataframe(tx_matches[cols], use_container_width=True, height=320, hide_index=True)

        if not results_found:
            st.info("No records found for this wallet across any data source.")
    else:
        st.info("Enter a wallet address above to see everything known about it.")
