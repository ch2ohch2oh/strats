import base64
import html
from pathlib import Path

import pandas as pd


PERCENT_COLUMNS = [
    "CAGR",
    "Annualized Volatility",
    "Max Drawdown",
    "Best Year",
    "Worst Year",
    "Average Yearly Return",
    "Average Annual Turnover",
]

RATIO_COLUMNS = [
    "Sharpe Ratio",
    "Sortino Ratio",
    "Calmar Ratio",
    "Average Trades per Year",
]

CHARTS = [
    ("Equity Curve Comparison", "equity_curves.png"),
    ("Drawdown Comparison", "drawdowns.png"),
    ("Rolling 12-Month Return Comparison", "rolling_12_month_returns.png"),
    ("Yearly Returns", "yearly_returns.png"),
]


def format_summary(summary: pd.DataFrame) -> pd.DataFrame:
    formatted = summary.copy()
    for column in PERCENT_COLUMNS:
        formatted[column] = formatted[column].map(lambda value: f"{value:.2%}")
    for column in RATIO_COLUMNS:
        formatted[column] = formatted[column].map(lambda value: f"{value:.2f}")
    formatted["Number of Trades"] = formatted["Number of Trades"].astype(int)
    formatted["Final Portfolio Value"] = formatted["Final Portfolio Value"].map(
        lambda value: f"${value:,.0f}"
    )
    return formatted


def _embedded_image(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def save_html_report(
    summary: pd.DataFrame,
    price_start: pd.Timestamp,
    price_end: pd.Timestamp,
    backtest_start: pd.Timestamp,
    backtest_end: pd.Timestamp,
    output_dir: str | Path = "output",
) -> Path:
    output_dir = Path(output_dir)
    best_strategy = summary.index[0]
    best_sharpe = summary.iloc[0]["Sharpe Ratio"]
    benchmark_sharpe = summary.loc["QQQ Buy & Hold", "Sharpe Ratio"]
    formatted = format_summary(summary)
    table = formatted.to_html(
        classes="metrics",
        border=0,
        justify="right",
        escape=True,
    )

    chart_sections = "\n".join(
        f"""
        <section>
          <h2>{html.escape(title)}</h2>
          <img src="{_embedded_image(output_dir / filename)}" alt="{html.escape(title)}">
        </section>
        """
        for title, filename in CHARTS
    )

    report = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Systematic ETF Strategy Backtest</title>
  <style>
    :root {{ color-scheme: light; --ink: #172033; --muted: #5f6b7a; --line: #dce2ea; --accent: #2563eb; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #f4f7fb; color: var(--ink); font: 15px/1.55 system-ui, sans-serif; }}
    main {{ max-width: 1500px; margin: 0 auto; padding: 32px 24px 56px; }}
    h1 {{ margin-bottom: 4px; font-size: 32px; }}
    h2 {{ margin-top: 0; font-size: 21px; }}
    .subtitle {{ margin-top: 0; color: var(--muted); }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin: 24px 0; }}
    .card, section {{ background: white; border: 1px solid var(--line); border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px #1822300d; }}
    .card strong {{ display: block; color: var(--muted); font-size: 12px; letter-spacing: .06em; text-transform: uppercase; }}
    .card span {{ display: block; margin-top: 5px; font-size: 21px; font-weight: 700; }}
    section {{ margin-top: 20px; overflow-x: auto; }}
    img {{ display: block; width: 100%; height: auto; }}
    table {{ width: 100%; border-collapse: collapse; white-space: nowrap; }}
    th, td {{ padding: 9px 11px; border-bottom: 1px solid var(--line); text-align: right; }}
    th {{ background: #eef3fa; font-size: 12px; }}
    th:first-child, td:first-child {{ position: sticky; left: 0; background: white; text-align: left; font-weight: 650; }}
    thead th:first-child {{ background: #eef3fa; }}
    ul {{ padding-left: 20px; }}
    .note {{ color: var(--muted); }}
  </style>
</head>
<body>
<main>
  <h1>Systematic ETF Strategy Backtest</h1>
  <p class="subtitle">Long-only systematic strategies versus QQQ buy-and-hold, after transaction costs.</p>

  <div class="cards">
    <div class="card"><strong>Best Sharpe Ratio</strong><span>{html.escape(best_strategy)}: {best_sharpe:.2f}</span></div>
    <div class="card"><strong>QQQ Sharpe Ratio</strong><span>{benchmark_sharpe:.2f}</span></div>
    <div class="card"><strong>Common Test Period</strong><span>{backtest_start.date()} to {backtest_end.date()}</span></div>
    <div class="card"><strong>Aligned Price History</strong><span>{price_start.date()} to {price_end.date()}</span></div>
  </div>

  <section>
    <h2>Performance Summary</h2>
    {table}
  </section>

  <section>
    <h2>Strategies Tested</h2>
    <h3>QQQ Trend Following with BIL Fallback</h3>
    <p>Check daily whether QQQ's closing price is above its 200-trading-day simple moving average.
    Hold 100% QQQ when it is above the average and 100% BIL otherwise. Trade only when the signal changes.</p>

    <h3>QQQ Volatility Targeting with BIL Fallback</h3>
    <p>Estimate QQQ annualized realized volatility from its trailing 63 daily returns and target 15% volatility.
    At each month-end, set the QQQ weight to the smaller of 100% and 15% divided by realized volatility.
    Allocate the remainder to BIL. Leverage and shorting are not allowed.</p>

    <h3>Dual Momentum</h3>
    <p>At each month-end, rank QQQ, VOO, VGT, BIL, IAU, and TLT by trailing 126-trading-day total return.
    A risk asset is eligible only when its return exceeds BIL's return. Hold 100% of the highest-returning
    eligible risk or defensive asset. If no risk asset beats BIL, hold the best defensive asset among BIL,
    IAU, and TLT.</p>

    <h3>QQQ Buy-and-Hold Benchmark</h3>
    <p>Hold 100% QQQ throughout the common backtest period.</p>
  </section>

  {chart_sections}

  <section>
    <h2>Methodology and Limitations</h2>
    <ul>
      <li>Yahoo Finance auto-adjusted closes are treated as total-return prices.</li>
      <li>Signals are calculated at the close and applied to the next trading day's return.</li>
      <li>Monthly strategies use month-end signals on the first trading day of the next month.</li>
      <li>Transaction cost is 0.02% of two-way dollar turnover; leverage and shorting are not allowed.</li>
      <li>All portfolios are evaluated over the same period after required signal warm-up.</li>
      <li>BIL is used as the short-term Treasury fallback and absolute-momentum hurdle.</li>
      <li>Taxes, market impact, survivorship bias, and execution differences limit the conclusions.</li>
    </ul>
    <p class="note">Past performance does not indicate future results.</p>
  </section>
</main>
</body>
</html>
"""
    report_path = output_dir / "report.html"
    report_path.write_text(report, encoding="utf-8")
    return report_path
