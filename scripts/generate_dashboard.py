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
        entries.reverse()

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
.card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; max-width: 960px; margin-left: auto; margin-right: auto; cursor: pointer; transition: border-color 0.2s; }}
.card:hover {{ border-color: #58a6ff; }}
.card-header {{ display: flex; justify-content: space-between; align-items: center; }}
.ticker {{ font-size: 1.4rem; font-weight: bold; color: #7ee787; }}
.date {{ color: #8b949e; font-size: 0.9rem; }}
.decision {{ color: #8b949e; font-size: 1rem; margin: 0.5rem 0; }}
.detail {{ display: none; background: #0d1117; border-radius: 6px; padding: 1.5rem; margin-top: 1rem; white-space: pre-wrap; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 0.9rem; line-height: 1.6; max-height: 70vh; overflow-y: auto; border-top: 1px solid #30363d; }}
.detail.show {{ display: block; }}
.detail h1, .detail h2, .detail h3 {{ color: #58a6ff; margin-top: 0.5em; }}
.detail h1 {{ font-size: 1.3rem; }}
.detail h2 {{ font-size: 1.1rem; }}
.detail h3 {{ font-size: 1rem; color: #7ee787; }}
.meta {{ color: #8b949e; font-size: 0.85rem; }}
.empty {{ text-align: center; color: #8b949e; margin-top: 4rem; }}
.footer {{ text-align: center; margin-top: 2rem; color: #484f58; font-size: 0.8rem; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }}
.badge-bull {{ background: #1b3826; color: #7ee787; }}
.badge-bear {{ background: #3a1f1f; color: #f85149; }}
.badge-hold {{ background: #2a2a1f; color: #d2a047; }}
.toggle-hint {{ color: #484f58; font-size: 0.8rem; }}
</style>
<script>
function toggle(id) {{
  const el = document.getElementById(id);
  el.classList.toggle('show');
}}
</script>
</head>
<body>
<h1>📊 TradingAgents Dashboard</h1>
<p style="text-align:center;color:#484f58;margin-bottom:1rem;font-size:0.85rem">点击卡片展开完整分析报告</p>
<div id="entries">
"""

    if not entries:
        html += '<div class="empty"><p>暂无分析记录</p><p style="margin-top:0.5rem">等待第一次 workflow 运行</p></div>'
    else:
        for i, e in enumerate(entries):
            decision_text = e.get("decision", "")
            ticker = e.get("ticker", "?")
            date = e.get("date", "?")
            run_at = e.get("run_at", "")[:19]
            report = e.get("report", decision_text)

            decision_lower = decision_text.lower()
            if any(w in decision_lower for w in ["buy", "bullish", "overweight"]):
                badge = '<span class="badge badge-bull">🟢 看涨</span>'
            elif any(w in decision_lower for w in ["sell", "bearish", "underweight", "reduce"]):
                badge = '<span class="badge badge-bear">🔴 看跌</span>'
            else:
                badge = '<span class="badge badge-hold">🟡 持有</span>'

            detail_id = f"detail-{i}"

            html += f"""
<div class="card" onclick="toggle('{detail_id}')">
  <div class="card-header">
    <span class="ticker">{ticker} {badge}</span>
    <span class="date">📅 {date}</span>
  </div>
  <div class="decision">决策: <strong>{decision_text}</strong> <span class="toggle-hint">— 点击展开详情</span></div>
  <div class="detail" id="{detail_id}">{report}</div>
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
