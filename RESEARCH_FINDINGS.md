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

## QQQ / VOO Rotation Follow-Up

Monthly rotation between QQQ and VOO was tested using 126-day relative
momentum, combined 126/252-day momentum, return divided by realized volatility,
a QQQ leadership-plus-trend filter, and a 75/25 blended allocation.

The conclusion is that rotation improves on VOO and reduces QQQ drawdowns, but
does not improve on the 50% QQQ-floor trend ensemble on a risk-adjusted basis.
QQQ and VOO daily returns had a 0.93 correlation from 2016 onward:

- Dual-horizon QQQ/VOO momentum produced the highest rotation CAGR at 18.95%,
  with 19.17% volatility, a 1.00 Sharpe, and a -28.56% maximum drawdown.
- Risk-adjusted QQQ/VOO momentum produced the highest rotation Sharpe at 1.03,
  with 18.50% CAGR and a -28.56% maximum drawdown.
- The 50% QQQ-floor trend ensemble produced a 1.07 Sharpe and a -25.52%
  maximum drawdown over the rotation study's common period.

Over the exact 2016-2026 comparison window:

- Dual-horizon momentum produced 19.26% CAGR, 20.59% volatility, a 0.96
  Sharpe, and a -28.56% maximum drawdown.
- The 50% QQQ-floor trend ensemble produced 18.89% CAGR, 17.91% volatility, a
  1.06 Sharpe, and a -25.52% maximum drawdown.
- QQQ produced 20.43% CAGR, 22.25% volatility, a 0.95 Sharpe, and a -35.12%
  maximum drawdown.

Because QQQ and VOO share broad US large-cap exposure, switching between them
changes concentration more than it changes the underlying equity-market risk.

## Dynamic Mag7 Leadership Follow-Up

A stock-level Mag7 study was designed to be more sophisticated than an
equal-weight MAGS-like basket. At each month-end it ranks AAPL, MSFT, AMZN,
GOOGL, META, NVDA, and TSLA using 126-day momentum, 252-day momentum, and
126-day return divided by 63-day volatility. Eligible stocks must have positive
126-day momentum and trade above their 200-day moving average.

The fixed risk-managed strategy selects the top three using inverse-volatility
weights when at least four of seven stocks and QQQ are above trend. Otherwise,
it holds 50% QQQ and 50% BIL. From 2016 through June 12, 2026:

- Risk-managed top three: 33.56% CAGR, 26.24% volatility, 1.24 Sharpe, and
  -34.80% maximum drawdown.
- Diversified leadership with a 60% stock sleeve and 40% VOO: 25.70% CAGR,
  21.07% volatility, 1.19 Sharpe, and -34.24% maximum drawdown.
- Equal-weight Mag7: 34.99% CAGR, 28.70% volatility, 1.19 Sharpe, and -49.38%
  maximum drawdown.
- QQQ: 20.43% CAGR, 22.25% volatility, 0.95 Sharpe, and -35.12% maximum
  drawdown.

A 27-combination sensitivity grid showed that top-three and top-four variants
generally retained Sharpe ratios above QQQ, with the top-three family averaging
a 1.25 Sharpe. The fixed midpoint specification was retained rather than
replacing it with the best in-sample parameters.

These results are exploratory and materially biased. Applying today's Mag7
membership throughout history selects known winners with hindsight, and the
strategy was designed after observing a technology-led period. It may warrant
paper trading or a future point-in-time constituent study, but it does not
replace the 50% QQQ-floor trend ensemble as the most credible core strategy.
