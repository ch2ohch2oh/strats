# Research Findings

Last updated: 2026-06-14

## Current Evidence

The BIL-based common backtest runs from 2011-10-18 through 2026-06-12.

- QQQ buy-and-hold produced the highest raw return: 19.95% CAGR, with 20.56%
  annualized volatility and a -35.12% maximum drawdown.
- The fixed 200-day trend strategy produced the strongest risk-adjusted result:
  15.53% CAGR, 1.00 Sharpe, and a -22.27% maximum drawdown.
- Fixed volatility targeting produced 15.39% CAGR, 0.99 Sharpe, and a -25.14%
  maximum drawdown.
- Dual momentum was materially weaker: 11.00% CAGR, 0.64 Sharpe, and a -44.86%
  maximum drawdown.

## Parameter Robustness

- The 200-day SMA remained the best stability-adjusted trend parameter.
- Full-history volatility optimization favored a 21-day estimate and 10%
  target, but that apparent improvement failed in walk-forward testing.
- Dual momentum improved with a 252-day lookback, but results remained unstable
  across subperiods.

## Walk-Forward Evidence

The expanding-window out-of-sample study runs from 2016-01-04 through
2026-06-12.

- Trend walk-forward: 16.93% CAGR, 1.03 Sharpe, -21.99% maximum drawdown.
- Fixed trend: 16.45% CAGR, 1.02 Sharpe, -22.27% maximum drawdown.
- QQQ: 20.43% CAGR, 0.95 Sharpe, -35.12% maximum drawdown.
- Volatility walk-forward underperformed its fixed baseline, demonstrating the
  danger of treating full-history parameter optimization as evidence.

## Research Direction

Without leverage, fully matching QQQ's CAGR while materially reducing risk is
unlikely. The next study focuses on preserving more equity exposure while using
simple trend controls:

1. Partial de-risking below the 200-day SMA.
2. Equal-weighted signals from the 150-, 200-, and 250-day SMAs.
3. A trend ensemble with a minimum QQQ allocation.

These variants are preferred over faster re-entry rules or complex defensive
rotation because they reduce binary timing risk and parameter dependence.

## External Research Used

- Meb Faber, "A Quantitative Approach to Tactical Asset Allocation":
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=962461
- Lempérière et al., "Two Centuries of Trend Following":
  https://arxiv.org/abs/1404.3274
- Levy and Lopes, "Trend-Following Strategies via Dynamic Momentum Learning":
  https://arxiv.org/abs/2106.08420
- Bernardi, Bianchi, and Bianco, "Smoothing Volatility Targeting":
  https://arxiv.org/abs/2212.07288

All findings remain sensitive to ETF history, strategy-design choices,
transaction-cost assumptions, and the unusually strong historical performance
of US technology equities.

## No-Leverage Follow-Up

Partial de-risking and trend ensembles improved the return/risk trade-off in the
full sample:

- A fixed 50% QQQ floor with the 200-day trend produced 18.68% CAGR, 1.09
  Sharpe, and a -26.25% maximum drawdown.
- A fixed 50% QQQ floor with the 150/200/250-day ensemble produced 18.67% CAGR,
  1.10 Sharpe, and a -25.52% maximum drawdown.
- A 75% floor approached QQQ's CAGR but allowed drawdowns near -30%, reducing
  the benefit of the trend overlay.

Walk-forward parameter selection favored a 75% QQQ floor in 7 of 11 years for
both strategy families. It raised CAGR to roughly 18.5%, but reduced Sharpe and
allowed roughly -30% drawdowns. This shows that maximizing historical Sharpe
can still select a high-exposure regime and does not reliably preserve the
desired risk constraint.

The fixed 50% floor is therefore the most credible current compromise to study
further. It is simple, does not require annual parameter selection, and retains
meaningful equity exposure during trend-off periods.

Over the exact 2016-2026 comparison window:

- The fixed 50% ensemble floor produced 18.89% CAGR, 1.06 Sharpe, 17.91%
  volatility, and a -25.52% maximum drawdown.
- QQQ produced 20.43% CAGR, 0.95 Sharpe, 22.25% volatility, and a -35.12%
  maximum drawdown.
- The fixed 25% ensemble floor produced the highest Sharpe at 1.07 and the
  lowest volatility among the partial-exposure variants, but its CAGR was
  lower at 17.87%.

The 50% ensemble floor currently offers the closest no-leverage approach to
QQQ-like CAGR while retaining substantial and consistent risk reduction. It
still trails QQQ by roughly 1.5 percentage points of CAGR in this window.
