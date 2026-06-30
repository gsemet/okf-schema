#!/usr/bin/env python3
"""A/B Comparison viewer for okf-schema skill evals.

Generates a standalone HTML report comparing "with_skill" vs "without_skill"
results from iteration directories. Both conditions use the same assertion set
graded deterministically by grade-eval.py.

Usage:
    python eval-viewer.py --iteration results/iteration-1 --output results/iteration-1/eval-result.html
    python eval-viewer.py --serve      # Serve on localhost
"""

import argparse
import json
import sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser


def load_grading(path: Path) -> dict | None:
    """Load grading.json in the unified format produced by grade-eval.py."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        assertions = data.get("assertions", [])
        passed = sum(1 for a in assertions if a.get("result") == "PASS")
        total = len(assertions)
        primary_passed = data.get("primary_passed", 0)
        primary_total = data.get("primary_total", 0)
        return {
            "summary": {
                "pass_rate": passed / total if total else 0.0,
                "primary_pass_rate": primary_passed / primary_total if primary_total else 0.0,
                "passed": passed,
                "failed": total - passed,
                "total": total,
                "primary_passed": primary_passed,
                "primary_total": primary_total,
            },
            "expectations": [
                {
                    "text": a.get("assertion", a.get("id", "Unnamed")),
                    "passed": a.get("result") == "PASS",
                    "evidence": a.get("justification", ""),
                    "tier": a.get("tier", "secondary"),
                }
                for a in assertions
            ],
        }
    except (json.JSONDecodeError, OSError):
        return None


def load_skeptical_review(iteration_dir: Path) -> str | None:
    """Load skeptical-review.md if present."""
    path = iteration_dir / "skeptical-review.md"
    if not path.exists():
        return None
    return path.read_text()


def md_to_html(md: str) -> str:
    """Basic markdown-to-HTML for the skeptical review."""
    import re
    html = md
    # Escape HTML
    html = html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Headers
    html = re.sub(r"^#### (.+)$", r"<h4>\1</h4>", html, flags=re.MULTILINE)
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    # Bold
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    # Italic
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    # Blockquotes
    html = re.sub(r"^> (.+)$", r"<blockquote>\1</blockquote>", html, flags=re.MULTILINE)
    # Unordered lists
    html = re.sub(r"^\- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    # Ordered lists
    html = re.sub(r"^(\d+)\. (.+)$", r"<li>\2</li>", html, flags=re.MULTILINE)
    # Wrap consecutive <li> in <ul>
    lines = html.splitlines()
    out = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("<li>") and not in_list:
            out.append("<ul>")
            in_list = True
        elif not stripped.startswith("<li>") and in_list:
            out.append("</ul>")
            in_list = False
        out.append(line)
    if in_list:
        out.append("</ul>")
    html = "\n".join(out)
    # Paragraphs (lines that aren't tags)
    lines = html.splitlines()
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("<"):
            out.append(f"<p>{stripped}</p>")
        else:
            out.append(line)
    html = "\n".join(out)
    return html


def build_comparison(iteration_dir: Path) -> list[dict]:
    comparisons = []
    for eval_dir in sorted(iteration_dir.iterdir()):
        if not eval_dir.is_dir() or eval_dir.name.startswith("."):
            continue
        with_skill = load_grading(eval_dir / "with_skill" / "grading.json")
        without_skill = load_grading(eval_dir / "without_skill" / "grading.json")
        if with_skill or without_skill:
            comparisons.append({
                "name": eval_dir.name,
                "with_skill": with_skill,
                "without_skill": without_skill,
            })
    return comparisons


def generate_html(comparisons: list[dict], iteration_name: str, skeptical_review_html: str | None = None) -> str:
    rows = []
    for comp in comparisons:
        name = comp["name"]
        ws = comp["with_skill"]
        wos = comp["without_skill"]

        ws_rate = ws["summary"]["pass_rate"] * 100 if ws else 0
        wos_rate = wos["summary"]["pass_rate"] * 100 if wos else 0
        ws_primary = ws["summary"]["primary_pass_rate"] * 100 if ws else 0
        wos_primary = wos["summary"]["primary_pass_rate"] * 100 if wos else 0
        delta = ws_rate - wos_rate
        delta_primary = ws_primary - wos_primary
        delta_class = "positive" if delta > 0 else ("negative" if delta < 0 else "neutral")

        # Build expectation comparison table — same assertions for both conditions
        exp_rows = []
        all_assertions = ws["expectations"] if ws else wos["expectations"]

        for assertion in all_assertions:
            text = assertion["text"]
            tier = assertion.get("tier", "secondary")
            tier_badge = f'<span class="tier-badge tier-{tier}">{tier}</span>'
            ws_exp = next((e for e in ws.get("expectations", []) if e["text"] == text), None) if ws else None
            wos_exp = next((e for e in wos.get("expectations", []) if e["text"] == text), None) if wos else None

            ws_pass = ws_exp["passed"] if ws_exp else None
            wos_pass = wos_exp["passed"] if wos_exp else None

            if ws_pass is True and wos_pass is False:
                row_class = "improved"
                indicator = "▲ Improved"
            elif ws_pass is False and wos_pass is True:
                row_class = "regressed"
                indicator = "▼ Regressed"
            elif ws_pass == wos_pass and ws_pass is not None:
                row_class = "same"
                indicator = "● Same"
            else:
                row_class = "new"
                indicator = "◆ New"

            exp_rows.append(f"""
                <tr class="{row_class}">
                    <td class="exp-text">{tier_badge} {text}</td>
                    <td class="pass-cell {'pass' if ws_pass else ('fail' if ws_pass is False else 'na')}">{"✅ PASS" if ws_pass else ("❌ FAIL" if ws_pass is False else "—")}</td>
                    <td class="pass-cell {'pass' if wos_pass else ('fail' if wos_pass is False else 'na')}">{"✅ PASS" if wos_pass else ("❌ FAIL" if wos_pass is False else "—")}</td>
                    <td class="indicator">{indicator}</td>
                </tr>
            """)

        rows.append(f"""
        <div class="eval-card">
            <div class="eval-header">
                <h3>{name}</h3>
                <div class="scores">
                    <div class="score-box with-skill">
                        <span class="score-label">With Skill</span>
                        <span class="score-value">{ws_rate:.0f}%</span>
                        <span class="score-detail">{ws["summary"]["passed"] if ws else 0}/{ws["summary"]["total"] if ws else 0}</span>
                        <span class="score-detail primary">Primary: {ws_primary:.0f}%</span>
                    </div>
                    <div class="score-box without-skill">
                        <span class="score-label">Without Skill</span>
                        <span class="score-value">{wos_rate:.0f}%</span>
                        <span class="score-detail">{wos["summary"]["passed"] if wos else 0}/{wos["summary"]["total"] if wos else 0}</span>
                        <span class="score-detail primary">Primary: {wos_primary:.0f}%</span>
                    </div>
                    <div class="score-box delta {delta_class}">
                        <span class="score-label">Delta</span>
                        <span class="score-value">{'+' if delta > 0 else ''}{delta:.0f}%</span>
                        <span class="score-detail primary">Primary: {'+' if delta_primary > 0 else ''}{delta_primary:.0f}%</span>
                    </div>
                </div>
            </div>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Expectation</th>
                        <th>With Skill</th>
                        <th>Without Skill</th>
                        <th>Change</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(exp_rows)}
                </tbody>
            </table>
        </div>
        """)

    # Summary stats
    total_delta = sum(
        (comp["with_skill"]["summary"]["pass_rate"] * 100 if comp["with_skill"] else 0) -
        (comp["without_skill"]["summary"]["pass_rate"] * 100 if comp["without_skill"] else 0)
        for comp in comparisons
    )
    avg_delta = total_delta / len(comparisons) if comparisons else 0
    improved = sum(1 for c in comparisons if c["with_skill"] and c["without_skill"] and c["with_skill"]["summary"]["pass_rate"] > c["without_skill"]["summary"]["pass_rate"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OKF Schema Skill Eval — A/B Comparison</title>
    <style>
        :root {{
            --bg: #0d1117;
            --surface: #161b22;
            --border: #30363d;
            --text: #c9d1d9;
            --text-secondary: #8b949e;
            --accent: #58a6ff;
            --pass: #3fb950;
            --fail: #f85149;
            --improved: #2ea043;
            --regressed: #da3633;
            --neutral: #8b949e;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{ text-align: center; margin-bottom: 2rem; }}
        h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
        .subtitle {{ color: var(--text-secondary); }}
        .summary-bar {{
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }}
        .summary-pill {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem 1.5rem;
            text-align: center;
            min-width: 140px;
        }}
        .summary-pill .value {{ font-size: 1.5rem; font-weight: bold; color: var(--accent); }}
        .summary-pill .label {{ font-size: 0.85rem; color: var(--text-secondary); }}
        .eval-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            margin-bottom: 1.5rem;
            overflow: hidden;
        }}
        .eval-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border);
            flex-wrap: wrap;
            gap: 1rem;
        }}
        .eval-header h3 {{ font-size: 1.1rem; }}
        .scores {{ display: flex; gap: 1rem; }}
        .score-box {{
            text-align: center;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            background: var(--bg);
            min-width: 100px;
        }}
        .score-label {{ display: block; font-size: 0.7rem; color: var(--text-secondary); text-transform: uppercase; }}
        .score-value {{ display: block; font-size: 1.3rem; font-weight: bold; }}
        .score-detail {{ display: block; font-size: 0.75rem; color: var(--text-secondary); }}
        .score-detail.primary {{ color: var(--accent); font-weight: 600; }}
        .delta.positive {{ color: var(--pass); }}
        .delta.negative {{ color: var(--fail); }}
        .tier-badge {{ font-size: 0.65rem; text-transform: uppercase; padding: 1px 5px; border-radius: 3px; margin-right: 4px; font-weight: 600; }}
        .tier-badge.tier-primary {{ background: rgba(88, 166, 255, 0.15); color: var(--accent); }}
        .tier-badge.tier-secondary {{ background: rgba(139, 148, 158, 0.15); color: var(--text-secondary); }}
        .comparison-table {{ width: 100%; border-collapse: collapse; }}
        .comparison-table th {{
            text-align: left;
            padding: 0.75rem 1.5rem;
            font-size: 0.8rem;
            text-transform: uppercase;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border);
        }}
        .comparison-table td {{
            padding: 0.75rem 1.5rem;
            border-bottom: 1px solid var(--border);
            font-size: 0.9rem;
        }}
        .comparison-table tr:last-child td {{ border-bottom: none; }}
        .exp-text {{ max-width: 500px; }}
        .pass-cell.pass {{ color: var(--pass); font-weight: 600; }}
        .pass-cell.fail {{ color: var(--fail); font-weight: 600; }}
        .pass-cell.na {{ color: var(--text-secondary); }}
        tr.improved {{ background: rgba(46, 160, 67, 0.1); }}
        tr.regressed {{ background: rgba(218, 54, 51, 0.1); }}
        tr.same {{ }}
        tr.new {{ background: rgba(88, 166, 255, 0.05); }}
        .indicator {{ font-size: 0.8rem; font-weight: 600; }}
        tr.improved .indicator {{ color: var(--improved); }}
        tr.regressed .indicator {{ color: var(--regressed); }}
        .skeptical-review {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            margin-bottom: 1.5rem;
            padding: 1.5rem;
        }}
        .skeptical-review h2 {{
            color: var(--accent);
            margin-bottom: 1rem;
            font-size: 1.2rem;
        }}
        .skeptical-review h3 {{
            color: var(--text);
            margin-top: 1rem;
            margin-bottom: 0.5rem;
            font-size: 1rem;
        }}
        .skeptical-review p {{
            margin-bottom: 0.75rem;
            color: var(--text-secondary);
        }}
        .skeptical-review ul {{
            margin-left: 1.5rem;
            margin-bottom: 0.75rem;
        }}
        .skeptical-review li {{
            margin-bottom: 0.25rem;
            color: var(--text-secondary);
        }}
        .skeptical-review blockquote {{
            border-left: 3px solid var(--accent);
            padding-left: 1rem;
            margin: 0.75rem 0;
            color: var(--text-secondary);
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 OKF Schema Skill Eval</h1>
            <p class="subtitle">A/B Comparison: With Skill vs Without Skill — {iteration_name}</p>
        </header>
        <div class="summary-bar">
            <div class="summary-pill">
                <div class="value">{len(comparisons)}</div>
                <div class="label">Evaluations</div>
            </div>
            <div class="summary-pill">
                <div class="value">{'+' if avg_delta > 0 else ''}{avg_delta:.0f}%</div>
                <div class="label">Avg Improvement</div>
            </div>
            <div class="summary-pill">
                <div class="value">{improved}/{len(comparisons)}</div>
                <div class="label">Improved</div>
            </div>
        </div>
        {f'<div class="skeptical-review"><h2>🧐 Skeptical Assessment</h2>{skeptical_review_html}</div>' if skeptical_review_html else ''}
        {''.join(rows)}
    </div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="OKF Schema Skill Eval A/B Viewer")
    parser.add_argument("--iteration", "-i", type=Path, default=None)
    parser.add_argument("--output", "-o", type=Path, default=None)
    parser.add_argument("--serve", "-s", action="store_true", help="Serve on localhost")
    parser.add_argument("--port", "-p", type=int, default=8117)
    args = parser.parse_args()

    iteration_dir = args.iteration
    if iteration_dir is None:
        # Auto-discover latest date-stamped iteration directory
        results_dir = Path("results")
        if results_dir.exists():
            iterations = sorted(
                [d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith("iteration-")],
                key=lambda d: d.name,
                reverse=True,
            )
            if iterations:
                iteration_dir = iterations[0]
        if iteration_dir is None:
            print("Error: No iteration directory found. Specify one with --iteration.", file=sys.stderr)
            sys.exit(1)
    if not iteration_dir.exists():
        print(f"Error: {iteration_dir} not found", file=sys.stderr)
        sys.exit(1)

    comparisons = build_comparison(iteration_dir)
    if not comparisons:
        print("No eval comparisons found", file=sys.stderr)
        sys.exit(1)

    skeptical_md = load_skeptical_review(iteration_dir)
    skeptical_html = md_to_html(skeptical_md) if skeptical_md else None

    output_path = args.output or iteration_dir / "eval-result.html"
    html = generate_html(comparisons, iteration_dir.name, skeptical_html)
    output_path.write_text(html)
    print(f"Report written to: {output_path.resolve()}")

    if args.serve:
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path in ("/", "/index.html"):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(html.encode())
                else:
                    self.send_error(404)
            def log_message(self, *a): pass

        server = HTTPServer(("127.0.0.1", args.port), Handler)
        url = f"http://localhost:{args.port}"
        print(f"Serving at {url}")
        webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
