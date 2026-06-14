# Systematic ETF Strategy Backtest

This project compares three long-only systematic investing strategies with QQQ
buy-and-hold, emphasizing risk-adjusted performance.

## Strategies

- **Trend Following:** hold QQQ when its close is above its 200-day SMA;
  otherwise hold BIL. The signal is checked daily and trades occur only when
  the signal changes.
- **Volatility Targeting:** target 15% annualized QQQ volatility using a
  trailing 63-day estimate, with the remainder in BIL. Rebalances monthly,
  without leverage or shorting.
- **Dual Momentum:** monthly selection among QQQ, VOO, VGT, BIL, IAU, and TLT
  using trailing 126-trading-day total return and the specified BIL hurdle.
- **Benchmark:** QQQ buy-and-hold.

## Run

```bash
uv sync
uv run python run_backtest.py
```

Use `uv run python run_backtest.py --refresh` to ignore the local
`data/prices.csv` cache and redownload data.

Run the coarse-grid robustness analysis separately:

```bash
uv run python optimize_strategies.py
```

This writes strategy-specific optimization CSVs and
`output/optimization_report.html`. Candidates are ranked using stable Sharpe
ratios across three chronological subperiods, rather than full-period Sharpe
alone. This still uses historical data and should not be treated as a true
out-of-sample result.

Run the stronger expanding-window walk-forward study:

```bash
uv run python run_walk_forward.py
```

At each year-end, this selects parameters using only prior data and applies
them unchanged throughout the following year. Results and annual parameter
selections are written to `output/walk_forward_report.html` and CSV files.

Run the follow-up no-leverage study:

```bash
uv run python run_no_leverage_study.py
```

This compares partial trend de-risking and multi-horizon trend ensembles using
both full-sample and walk-forward tests. Existing baseline reports are not
overwritten. Findings and rationale are preserved in `RESEARCH_FINDINGS.md`.

Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`.
`requirements.txt` is retained for compatibility with non-uv environments.

Results are written to `output/results.csv`; four comparison charts and a
self-contained `output/report.html` report are also generated. The report
includes strategy definitions, metrics, methodology, and embedded charts.

## Assumptions and limitations

- Yahoo Finance auto-adjusted close prices are treated as total-return prices.
- Data begins on the first date where every ETF has a valid price. With BIL as
  the Treasury fallback, the requested test can use the full history from 2011.
- All portfolios are trimmed to a common evaluation period after their longest
  signal warm-up, making metrics directly comparable. Each portfolio is treated
  as newly funded at that common start, so its initial purchase incurs cost and
  counts as a trade.
- Signals use information available at the close and weights take effect for
  the next trading day's close-to-close return. Month-end signals therefore
  rebalance on the first trading day of the next month.
- Transaction cost is 0.02% of two-way dollar turnover. A complete switch from
  one ETF to another creates 200% turnover and costs 0.04%.
- Trades are counted as trading days with nonzero turnover. Gradual allocation
  changes count as one trade day, not separate buy and sell orders.
- The test ignores taxes, bid-ask spreads beyond the fixed cost, market impact,
  and execution differences between the close and a realizable next-day fill.
- ETF history creates survivorship and launch-date limitations. This is a
  relatively short out-of-sample window and is not evidence of future returns.
