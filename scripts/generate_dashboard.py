import argparse
import json
from pathlib import Path
from datetime import datetime


def generate_dashboard(history_path, output_dir):
    history_file = Path(history_path)
    if not history_file.exists():
        entries = []
    else:
        entries = []
        for line in history_file.read_text(encoding="utf-8").strip().split("\n"):
            if line:
                entries.append(json.loads(line))
        entries.reverse()  # 最新在前

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TradingAgents Dashboard</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0d1117; color: #c9d1d9; padding: 2rem; }}
h1 {{ text-align: center; margin-bottom: 2rem; color: #58a6ff; }}
.card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; max-width: 900px; margin-left: auto; margin-right: auto; }}
.card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }}
.ticker {{ font-size: 1.4rem; font-weight: bold; color: #7ee787; }}
.date {{ color: #8b949e; font-size: 0.9rem; }}
.decision {{ background: #0d1117; border-radius: 6px; padding: 1rem; white-space: pre-wrap; font-family: monospace; font-size: 0.9rem; line-height: 1.5; max-height: 400px; overflow-y: auto; }}
.meta {{ color: #8b949e; font-size: 0.85rem; margin-top: 0.5rem; }}
.empty {{ text-align: center; color: #8b949e; margin-top: 4rem; }}
.footer {{ text-align: center; margin-top: 2rem; color: #484f58; font-size: 0.8rem; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }}
.badge-bull {{ background: #1b3826; color: #7ee787; }}
.badge-bear {{ background: #3a1f1f; color: #f85149; }}
.badge-hold {{ background: #2a2a1f; color: #d2a047; }}
</style>
</head>
<body>
<h1>📊 TradingAgents Dashboard</h1>
<div id="entries">
"""

    if not entries:
        html += '<div class="empty"><p>暂无分析记录</p><p style="margin-top:0.5rem">等待第一次 workflow 运行</p></div>'
    else:
        for e in entries:
            decision_text = e.get("decision", "")
            ticker = e.get("ticker", "?")
            date = e.get("date", "?")
            run_at = e.get("run_at", "")[:19]

            # 简单判断倾向
            decision_lower = decision_text.lower()
            if any(w in decision_lower for w in ["buy", "bullish", "买入", "看涨"]):
                badge = '<span class="badge badge-bull">看涨</span>'
            elif any(w in decision_lower for w in ["sell", "bearish", "卖出", "看跌"]):
                badge = '<span class="badge badge-bear">看跌</span>'
            else:
                badge = '<span class="badge badge-hold">持有</span>'

            html += f"""
<div class="card">
  <div class="card-header">
    <span class="ticker">{ticker} {badge}</span>
    <span class="date">📅 {date}</span>
  </div>
  <div class="decision">{decision_text}</div>
  <div class="meta">运行时间: {run_at}</div>
</div>"""

    html += f"""
</div>
<div class="footer">
  自动更新 · 最后刷新: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC ·
  <a href="https://github.com/dedarek/TradingAgents" style="color:#58a6ff">GitHub</a>
</div>
</body>
</html>"""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html, encoding="utf-8")
    print(f"Dashboard generated: {out / 'index.html'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", default="./history.jsonl")
    parser.add_argument("--output-dir", default="./docs")
    args = parser.parse_args()
    generate_dashboard(args.history, args.output_dir)
