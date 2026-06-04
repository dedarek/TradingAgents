"""Render completed analysis report with expandable sections."""

from __future__ import annotations

import re
from typing import Any

import streamlit as st


def _strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()


def _signal_style(signal: str) -> tuple[str, str]:
    s = signal.upper()
    if "BUY" in s or "OVERWEIGHT" in s:
        return "#22c55e", "买入"
    if "SELL" in s or "UNDERWEIGHT" in s:
        return "#ef4444", "卖出"
    return "#fbbf24", "持有"


_ANALYST_SECTIONS = [
    ("market_report", "📊 技术分析"),
    ("sentiment_report", "💬 市场情绪"),
    ("news_report", "📰 新闻舆情"),
    ("fundamentals_report", "📋 基本面"),
]


def render_report(
    final_state: dict[str, Any],
    ticker: str,
    trade_date: str,
    signal: str,
    elapsed: float | None = None,
) -> None:
    color, cn_signal = _signal_style(signal)

    stats_html = ""
    if elapsed is not None:
        m, s = divmod(int(elapsed), 60)
        stats_html = f'<div style="font-size:0.9rem; color:#888; margin-top:0.3rem;">耗时 {m}:{s:02d}</div>'

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid #333;
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            margin: 1rem 0 2rem;
        ">
            <div style="font-size:0.9rem; color:#888; letter-spacing:2px;">TRADING SIGNAL</div>
            <div style="font-size:3.5rem; font-weight:900; color:{color}; margin:0.3rem 0;">
                {cn_signal}
            </div>
            <div style="font-size:1.2rem; color:#f5f1eb;">
                {ticker} · {trade_date}
            </div>
            {stats_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption("⚠️ 本报告由 AI 自动生成，仅供学习研究，不构成投资建议。")

    col_md, col_spacer = st.columns([1, 3])
    with col_md:
        md_text = _generate_markdown(final_state, ticker, trade_date, signal)
        st.download_button(
            "📥 下载 Markdown",
            data=md_text.encode("utf-8"),
            file_name=f"TradingAgents_{ticker}_{trade_date}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.markdown("---")

    # 最终决策
    inv_plan = final_state.get("final_trade_decision", "")
    if inv_plan:
        st.markdown("### 👔 最终交易决策")
        st.markdown(_strip_think(str(inv_plan)))
        st.markdown("---")

    # 分析师报告
    st.markdown("### 📊 分析师报告")
    for key, title in _ANALYST_SECTIONS:
        content = final_state.get(key, "")
        if not content:
            continue
        with st.expander(title, expanded=False):
            st.markdown(_strip_think(str(content)))

    # 研究员辩论
    debate = final_state.get("investment_debate_state")
    if debate and isinstance(debate, dict):
        st.markdown("### ⚔️ 多空辩论")
        tab_bull, tab_bear, tab_judge = st.tabs(["多方", "空方", "研究经理"])
        with tab_bull:
            st.markdown(_strip_think(debate.get("bull_history", "") or "无数据"))
        with tab_bear:
            st.markdown(_strip_think(debate.get("bear_history", "") or "无数据"))
        with tab_judge:
            st.markdown(_strip_think(debate.get("judge_decision", "") or "无数据"))

    # 交易员
    trader_decision = final_state.get("trader_investment_plan", "")
    if trader_decision:
        with st.expander("💹 交易员方案", expanded=False):
            st.markdown(_strip_think(str(trader_decision)))

    # 风控
    risk = final_state.get("risk_debate_state")
    if risk and isinstance(risk, dict):
        st.markdown("### 🛡️ 风控评估")
        tab_agg, tab_con, tab_neu, tab_rj = st.tabs(["激进", "保守", "中性", "风控决策"])
        with tab_agg:
            st.markdown(_strip_think(risk.get("aggressive_history", "") or "无数据"))
        with tab_con:
            st.markdown(_strip_think(risk.get("conservative_history", "") or "无数据"))
        with tab_neu:
            st.markdown(_strip_think(risk.get("neutral_history", "") or "无数据"))
        with tab_rj:
            st.markdown(_strip_think(risk.get("judge_decision", "") or "无数据"))


def _generate_markdown(
    final_state: dict[str, Any], ticker: str, trade_date: str, signal: str
) -> str:
    parts = [f"# TradingAgents 分析报告\n\n**{ticker}** · {trade_date}\n\n## 最终决策\n\n{signal}\n"]
    for key, title in _ANALYST_SECTIONS:
        content = final_state.get(key, "")
        if content:
            parts.append(f"## {title}\n\n{_strip_think(str(content))}\n")
    debate = final_state.get("investment_debate_state")
    if debate and isinstance(debate, dict):
        parts.append("## 多空辩论\n")
        for role, k in [("多方", "bull_history"), ("空方", "bear_history"), ("研究经理", "judge_decision")]:
            c = debate.get(k, "")
            if c:
                parts.append(f"### {role}\n\n{_strip_think(c)}\n")
    risk = final_state.get("risk_debate_state")
    if risk and isinstance(risk, dict):
        parts.append("## 风控评估\n")
        for role, k in [("激进", "aggressive_history"), ("保守", "conservative_history"), ("中性", "neutral_history"), ("决策", "judge_decision")]:
            c = risk.get(k, "")
            if c:
                parts.append(f"### {role}\n\n{c}\n")
    return "\n".join(parts)
