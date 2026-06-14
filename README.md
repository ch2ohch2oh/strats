# Systematic ETF Strategy Backtest

This project compares long-only systematic investing strategies with QQQ
buy-and-hold, emphasizing risk-adjusted performance.

## Constraints

Every strategy in this project must satisfy all of the following rules:

1. **Long-only** — weights are always between 0% and 100%. No negative positions.
2. **No shorting** — no strategy may profit from declining asset prices.
3. **No options** — all positions use spot ETFs only. No derivatives of any kind.
4. **No leverage** — cash held in BIL does not count as leverage. Position weights
   must sum to 100% at all times, and no position may exceed 100% of portfolio value.
5. **QQQ benchmark** — every study must include QQQ buy-and-hold as the reference.
6. **Risk-adjusted superiority** — a strategy must beat QQQ on risk-adjusted
   metrics (Sharpe, Sortino, Calmar, or drawdown), not just on total return. A
   strategy that only matches or trails QQQ's total return without improving risk
   is not considered a viable alternative.

## Backtest Requirements

Every backtest in this project must satisfy the following methodological standards:

1. **Use only data available before each trade** — signals are computed on close
   prices and applied to the next trading day's return. Walk-forward tests select
   parameters using only prior data. No future information may leak into any
   signal, parameter choice, or performance evaluation.

2. **Separate in-sample and out-of-sample periods** — full-history results are
   diagnostic. The fixed 2016-onward window and annual walk-forward selection
   are the primary out-of-sample evidence. A strategy that only works in-sample
   is not considered viable.

3. **Test parameter sensitivity** — the optimization study ranks candidates by
   subperiod stability (median fold Sharpe minus 0.5×std). A strategy whose
   performance collapses under small parameter changes is not robust enough to
   act on.

4. **Show rolling performance over time** — all reports include equity curves,
   drawdown charts, rolling 12-month returns, and yearly return bar charts to
   reveal whether outperformance is concentrated in a single period.

5. **Explain when the strategy fails** — each report documents periods of
   underperformance, the conditions that caused it, and why a reasonable
   investor might abandon the strategy at the worst possible time.

6. **Reject fragile results** — a strategy is rejected if its apparent success
   depends on:
   - one lucky subperiod (isolated outperformance in a single fold or year)
   - one exact parameter value (sharp performance drop at adjacent settings)
   - unrealistic assumptions (survivorship bias, hindsight bias, zero costs,
     perfect execution, or data unavailable at trade time)

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

The primary deliverable is the consolidated [`master_report.html`](https://ch2ohch2oh.github.io/strats/master_report.html).
All reports are published via [GitHub Pages](https://ch2ohch2oh.github.io/strats/).
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
