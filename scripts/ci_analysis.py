import argparse
import datetime
import json
import os
import sys
from pathlib import Path

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG


def main():
    parser = argparse.ArgumentParser(
        description="TradingAgents CI — non-interactive analysis runner"
    )
    parser.add_argument(
        "--ticker", default=os.getenv("TRADINGAGENTS_TICKER", "SPY"),
        help="Ticker symbol (default: SPY, or $TRADINGAGENTS_TICKER)"
    )
    parser.add_argument(
        "--date",
        default=datetime.datetime.now().strftime("%Y-%m-%d"),
        help="Analysis date YYYY-MM-DD (default: today)"
    )
    parser.add_argument(
        "--output-dir", default="./results",
        help="Output directory (default: ./results)"
    )
    parser.add_argument(
        "--max-debate-rounds", type=int, default=1,
        help="Max debate rounds (default: 1)"
    )
    args = parser.parse_args()

    config = DEFAULT_CONFIG.copy()
    config["max_debate_rounds"] = args.max_debate_rounds
    config["max_risk_discuss_rounds"] = args.max_debate_rounds

    # Validate we have an LLM provider + key
    provider = config["llm_provider"]
    env_key_map = {
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "xai": "XAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "qwen": "DASHSCOPE_API_KEY",
        "qwen-cn": "DASHSCOPE_CN_API_KEY",
        "glm": "ZHIPU_API_KEY",
        "glm-cn": "ZHIPU_CN_API_KEY",
        "minimax": "MINIMAX_API_KEY",
        "minimax-cn": "MINIMAX_CN_API_KEY",
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
    print(f"Debate rounds: {config['max_debate_rounds']}")
    print("---")

    ta = TradingAgentsGraph(debug=True, config=config)
    _, decision = ta.propagate(args.ticker, args.date)

    print("=== DECISION ===")
    print(decision)

    # ── 持久化到 results/ 目录 ──
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 单次结果 JSON
    result_file = output_dir / "decision.json"
    result_file.write_text(
        json.dumps({
            "ticker": args.ticker,
            "date": args.date,
            "provider": provider,
            "model": config["deep_think_llm"],
            "decision": str(decision),
            "run_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # 累计历史记录 JSONL（追加）
    history_file = output_dir / ".." / "history.jsonl"
    if not history_file.parent.exists():
        history_file.parent.mkdir(parents=True, exist_ok=True)
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ticker": args.ticker,
            "date": args.date,
            "decision": str(decision),
            "run_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }, ensure_ascii=False) + "\n")

    # 可读 Markdown
    md_file = output_dir / "decision.md"
    md_file.write_text(
        f"# {args.ticker} — {args.date}\n\n"
        f"- **Provider**: {provider}\n"
        f"- **Model**: {config['deep_think_llm']}\n"
        f"- **Run at**: {datetime.datetime.now(datetime.timezone.utc).isoformat()}\n\n"
        f"## Decision\n\n{decision}\n",
        encoding="utf-8"
    )

    print(f"\nResults saved to: {output_dir}")

    return decision


if __name__ == "__main__":
    main()
