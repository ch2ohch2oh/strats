import base64
from pathlib import Path

import pandas as pd

from src.reporting import format_summary


def _image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def save_mag7_report(
    full_summary: pd.DataFrame,
    fixed_summary: pd.DataFrame,
    robustness: pd.DataFrame,
    full_chart: Path,
    fixed_chart: Path,
    output_path: Path,
) -> Path:
    full_table = format_summary(full_summary).to_html(border=0)
    fixed_table = format_summary(fixed_summary).to_html(border=0)
    robustness_display = robustness.head(10)[
        ["Top N", "Breadth Threshold", "Stock Sleeve", "CAGR", "Annualized Volatility", "Sharpe Ratio", "Max Drawdown"]
    ].copy()
    for column in ["Stock Sleeve", "CAGR", "Annualized Volatility", "Max Drawdown"]:
        robustness_display[column] = robustness_display[column].map(lambda value: f"{value:.2%}")
    robustness_display["Sharpe Ratio"] = robustness_display["Sharpe Ratio"].map(lambda value: f"{value:.2f}")
    robustness_table = robustness_display.to_html(index=False, border=0)
    best = fixed_summary.index[0]
    best_sharpe = fixed_summary.iloc[0]["Sharpe Ratio"]
    report = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Mag7 Leadership Study</title>
<style>
body{{margin:0;background:#f4f7fb;color:#172033;font:15px/1.55 system-ui,sans-serif}}
main{{max-width:1600px;margin:auto;padding:32px 24px}}section{{margin:20px 0;padding:22px;overflow-x:auto;background:white;border:1px solid #dce2ea;border-radius:12px}}
.warning{{padding:16px;border-left:5px solid #c47a00;background:#fff8e8}}table{{width:100%;border-collapse:collapse;white-space:nowrap}}
th,td{{padding:8px 10px;border-bottom:1px solid #dce2ea;text-align:right}}th:first-child,td:first-child{{text-align:left}}
th{{background:#eef3fa}}img{{width:100%;height:auto}}code{{background:#eef3fa;padding:2px 4px}}</style></head>
<body><main><h1>Dynamic Mag7 Leadership Study</h1>
<p>A stock-selection and regime-control study, not a recreation of the MAGS ETF.</p>
<p class="warning"><strong>Exploratory only:</strong> the study applies today's Mag7 membership throughout
history. That creates severe survivorship and selection bias. Results cannot be treated as out-of-sample evidence.</p>
<section><h2>Strategy Design</h2><ol>
<li>At month-end, rank each Mag7 stock using 126-day momentum, 252-day momentum, and 126-day return divided by 63-day volatility.</li>
<li>Only stocks above their 200-day average with positive 126-day returns are eligible.</li>
<li>Select the top three. Risk-managed variants weight them by inverse volatility.</li>
<li>The risk regime requires at least four of seven stocks above trend and QQQ above its 200-day average.</li>
<li>In a weak regime, risk-managed variants hold 50% QQQ and 50% BIL (iShares 1-3 Month Treasury Bond ETF). The diversified variant holds only a 60% stock-selection sleeve and 40% VOO in healthy regimes.</li>
<li>Signals calculated at the close take effect on the next trading day; costs are 0.02% of two-way turnover.</li>
</ol></section>
<section><h2>2016-Onward Result</h2><p>Highest fixed-period Sharpe: <strong>{best}</strong> at <strong>{best_sharpe:.2f}</strong>.</p>{fixed_table}</section>
<section><h2>2016-Onward Equity Curves</h2><img src="data:image/png;base64,{_image(fixed_chart)}"></section>
<section><h2>Parameter Stability Grid</h2><p>Top 10 of 27 risk-managed combinations. This is an in-sample
sensitivity check, not optimization evidence.</p>{robustness_table}</section>
<section><h2>Full Common History</h2>{full_table}</section>
<section><h2>Full-History Equity Curves</h2><img src="data:image/png;base64,{_image(full_chart)}"></section>
<section><h2>Limitations</h2><ul><li>Today's winners are selected with hindsight.</li>
<li>Stock-level Yahoo Finance data and corporate-history treatment can differ from institutional datasets.</li>
<li>The parameter choices were designed after observing a technology-led market and require genuine future validation.</li>
<li>Taxes, spreads beyond fixed costs, market impact, and practical close execution are excluded.</li></ul></section>
</main></body></html>"""
    output_path.write_text(report, encoding="utf-8")
    return output_path
