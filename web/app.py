"""TradingAgents — Streamlit WebUI."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

load_dotenv(_PROJECT_ROOT / ".env")

from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402
from web.components.progress_panel import render_progress  # noqa: E402
from web.components.report_viewer import render_report  # noqa: E402
from web.components.sidebar import render_sidebar  # noqa: E402
from web.history import extract_signal, load_analysis  # noqa: E402
from web.progress import ProgressTracker  # noqa: E402
from web.runner import run_analysis_in_thread  # noqa: E402

st.set_page_config(
    page_title="TradingAgents 投研系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

    #MainMenu, footer,
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"],
    div[data-testid="stToolbarActions"],
    div[data-testid="stAppDeployButton"],
    span[data-testid="stMainMenu"] { display: none !important; }
    header[data-testid="stHeader"] {
        background: transparent !important;
        box-shadow: none !important;
    }
    button[data-testid="stExpandSidebarButton"],
    button[data-testid="stSidebarCollapseButton"],
    button[data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
    }

    html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
    .stApp { background: #0a0a0a; }
    section[data-testid="stSidebar"] {
        background: #0f0f0f;
        border-right: 1px solid #1a1a1a;
    }
    .stMetric label { color: #888 !important; font-size: 0.8rem !important; }
    .stMetric [data-testid="stMetricValue"] {
        color: #ff5a1f !important;
        font-weight: 700 !important;
    }
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #ff5a1f, #ff8c42) !important;
    }
    button[kind="primary"] {
        background: linear-gradient(135deg, #ff5a1f, #ff8c42) !important;
        border: none !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
        box-shadow: 0 4px 15px rgba(255,90,31,0.3) !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #e04d15, #ff5a1f) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.session_state.setdefault("llm_provider", "deepseek")
st.session_state.setdefault("deep_think_llm", "deepseek-v4-pro")
st.session_state.setdefault("quick_think_llm", "deepseek-v4-flash")
st.session_state.setdefault("llm_base_url", "")
st.session_state.setdefault("tracker", None)
st.session_state.setdefault("start_analysis", None)
st.session_state.setdefault("viewing_history", None)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    render_sidebar()

# ── Main Content ─────────────────────────────────────────────────────────────
tracker: ProgressTracker | None = st.session_state["tracker"]
viewing = st.session_state.get("viewing_history")

if viewing:
    data = load_analysis(viewing)
    signal = extract_signal(data)
    ticker = data.get("ticker", Path(viewing).parent.parent.name)
    # Determine date - since the data itself doesn't have a date field directly
    date_str = ""
    for k in data:
        if isinstance(data.get(k), str) and len(data[k]) < 20:
            pass  # not a useful date field
    render_report(data, ticker, "", signal)
elif tracker is not None and (tracker.is_running or tracker.is_complete):
    if tracker.is_complete:
        render_report(
            tracker.final_state,
            tracker.ticker,
            tracker.trade_date,
            tracker.signal,
            tracker.elapsed,
        )
    else:
        render_progress(tracker)
elif st.session_state.get("start_analysis") and tracker is None:
    params = st.session_state["start_analysis"]
    del st.session_state["start_analysis"]

    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = st.session_state["llm_provider"]
    config["deep_think_llm"] = st.session_state["deep_think_llm"]
    config["quick_think_llm"] = st.session_state["quick_think_llm"]
    config["backend_url"] = st.session_state.get("llm_base_url", "") or None

    tracker = ProgressTracker()
    st.session_state["tracker"] = tracker
    run_analysis_in_thread(params["ticker"], params["trade_date"], config, tracker)
    st.rerun()
else:
    st.markdown(
        """
        <div style="height:60vh; display:flex; flex-direction:column; align-items:center; justify-content:center;">
            <div style="font-size:5rem; margin-bottom:1rem;">📈</div>
            <div style="font-size:1.5rem; font-weight:700; color:#f5f1eb; margin-bottom:0.5rem;">
                TradingAgents 投研系统
            </div>
            <div style="color:#888; font-size:0.95rem; text-align:center; max-width:500px;">
                多 Agent LLM 驱动的投资分析框架<br>
                在左侧输入股票代码，选择模型，点击开始分析
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
