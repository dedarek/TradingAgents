import argparse
import datetime
import json
import os
import sys
from pathlib import Path

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG


def build_full_report(ticker, date, final_state, config):
    """从 final_state 提取完整多 Agent 分析报告"""
    parts = [f"# {ticker} — {date}\n"]

    # 分析师报告
    analysts = []
    if final_state.get("market_report"):
        analysts.append(("技术面分析", final_state["market_report"]))
    if final_state.get("sentiment_report"):
        analysts.append(("市场情绪", final_state["sentiment_report"]))
    if final_state.get("news_report"):
        analysts.append(("宏观新闻", final_state["news_report"]))
    if final_state.get("fundamentals_report"):
        analysts.append(("基本面分析", final_state["fundamentals_report"]))
    if analysts:
        parts.append("## 📊 分析师报告\n")
        for title, content in analysts:
            parts.append(f"### {title}\n{content}\n")

    # 研究员辩论
    if final_state.get("investment_debate_state"):
        debate = final_state["investment_debate_state"]
        parts.append("## ⚔️ 研究员辩论\n")
        if debate.get("bull_history"):
            parts.append(f"### 多头研究员\n{debate['bull_history']}\n")
        if debate.get("bear_history"):
            parts.append(f"### 空头研究员\n{debate['bear_history']}\n")
        if debate.get("judge_decision"):
            parts.append(f"### 研究主管裁定\n{debate['judge_decision']}\n")

    # 交易员
    if final_state.get("trader_investment_plan"):
        parts.append("## 💰 交易员方案\n")
        parts.append(f"{final_state['trader_investment_plan']}\n")

    # 风控
    if final_state.get("risk_debate_state"):
        risk = final_state["risk_debate_state"]
        parts.append("## 🛡️ 风控评估\n")
        if risk.get("aggressive_history"):
            parts.append(f"### 激进分析\n{risk['aggressive_history']}\n")
        if risk.get("conservative_history"):
            parts.append(f"### 保守分析\n{risk['conservative_history']}\n")
        if risk.get("neutral_history"):
            parts.append(f"### 中性分析\n{risk['neutral_history']}\n")
        if risk.get("judge_decision"):
            parts.append(f"### 投资组合经理决策\n{risk['judge_decision']}\n")

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="TradingAgents CI — non-interactive analysis runner"
    )
    parser.add_argument(
        "--ticker", default=os.getenv("TRADINGAGENTS_TICKER", "SPY"),
        help="Ticker symbol"
    )
    parser.add_argument(
        "--date", default=datetime.datetime.now().strftime("%Y-%m-%d"),
        help="Analysis date YYYY-MM-DD"
    )
    parser.add_argument(
        "--output-dir", default="./results",
        help="Output directory"
    )
    parser.add_argument(
        "--max-debate-rounds", type=int, default=1,
        help="Max debate rounds"
    )
    args = parser.parse_args()

    config = DEFAULT_CONFIG.copy()
    config["max_debate_rounds"] = args.max_debate_rounds
    config["max_risk_discuss_rounds"] = args.max_debate_rounds

    provider = config["llm_provider"]
    env_key_map = {
        "openai": "OPENAI_API_KEY", "google": "GOOGLE_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY", "xai": "XAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "qwen": "DASHSCOPE_API_KEY", "qwen-cn": "DASHSCOPE_CN_API_KEY",
        "glm": "ZHIPU_API_KEY", "glm-cn": "ZHIPU_CN_API_KEY",
        "minimax": "MINIMAX_API_KEY", "minimax-cn": "MINIMAX_CN_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }
    key_var = env_key_map.get(provider)
    if key_var and not os.environ.get(key_var):
        print(f"::error::Missing API key: {key_var} is not set for provider '{provider}'")
        sys.exit(1)

    print(f"Ticker: {args.ticker}")
    print(f"Date: {args.date}")
    print(f"Provider: {provider}")
    print(f"Deep model: {config['deep_think_llm']}")
    print(f"Quick model: {config['quick_think_llm']}")
    print("---")

    ta = TradingAgentsGraph(debug=False, config=config)
    final_state, decision = ta.propagate(args.ticker, args.date)

    print("=== DECISION ===")
    print(decision)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    full_report = build_full_report(args.ticker, args.date, final_state, config)

    # 完整报告 Markdown
    (output_dir / "decision.md").write_text(full_report, encoding="utf-8")

    # JSON 摘要
    (output_dir / "decision.json").write_text(
        json.dumps({
            "ticker": args.ticker, "date": args.date,
            "provider": provider, "model": config["deep_think_llm"],
            "decision": str(decision),
            "report": full_report,
            "run_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # 追加历史（含完整报告，供仪表盘使用）
    history_file = output_dir / ".." / "history.jsonl"
    if not history_file.parent.exists():
        history_file.parent.mkdir(parents=True, exist_ok=True)
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ticker": args.ticker, "date": args.date,
            "decision": str(decision),
            "report": full_report,
            "run_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }, ensure_ascii=False) + "\n")

    print(f"\nResults saved to: {output_dir}")

    return decision


if __name__ == "__main__":
    main()
