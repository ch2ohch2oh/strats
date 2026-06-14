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
- **Dynamic Mag7 leadership study:** exploratory stock-level momentum, trend,
  breadth, and inverse-volatility allocation. This study uses today's Mag7
  membership historically and is explicitly labeled as survivorship-biased.

## Run

```bash
uv sync
uv run python run_all_studies.py
```

The primary deliverable is the consolidated `output/master_report.html`.
Use `uv run python run_backtest.py --refresh` first when price data should be
redownloaded.

Individual study commands remain available for focused iteration:

```bash
uv run python run_backtest.py
uv run python optimize_strategies.py
uv run python run_walk_forward.py
uv run python run_no_leverage_study.py
uv run python run_qqq_voo_rotation_study.py
uv run python run_mag7_study.py
uv run python generate_master_report.py
```

Detailed reports and CSV files remain available for audit. Findings and
rationale are preserved in `RESEARCH_FINDINGS.md`.

Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`.
`requirements.txt` is retained for compatibility with non-uv environments.

The master report includes the strategy definitions, key metrics, methodology,
optimization caveats, walk-forward evidence, and no-leverage conclusions.

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
