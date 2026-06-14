from dataclasses import dataclass

import pandas as pd


@dataclass
class BacktestResult:
    returns: pd.Series
    gross_returns: pd.Series
    weights: pd.DataFrame
    turnover: pd.Series


def run_portfolio(
    prices: pd.DataFrame,
    weights: pd.DataFrame,
    transaction_cost: float = 0.0002,
) -> BacktestResult:
    """Apply target weights to close-to-close returns and charge cost on turnover."""
    asset_returns = prices.pct_change()
    valid = weights.notna().all(axis=1) & asset_returns.notna().all(axis=1)
    active_weights = weights.loc[valid]
    active_returns = asset_returns.loc[valid]

    # Dollar turnover is two-way: a 100% A-to-B switch has 200% turnover.
    previous_weights = active_weights.shift(1)
    previous_weights.iloc[0] = 0.0
    turnover = active_weights.sub(previous_weights).abs().sum(axis=1)
    gross_returns = (active_weights * active_returns).sum(axis=1)
    net_returns = gross_returns - transaction_cost * turnover

    return BacktestResult(net_returns, gross_returns, active_weights, turnover)


def align_results(
    results: dict[str, BacktestResult],
    transaction_cost: float = 0.0002,
) -> dict[str, BacktestResult]:
    """Trim all portfolios to the same investable evaluation period."""
    common_start = max(result.returns.index.min() for result in results.values())
    common_end = min(result.returns.index.max() for result in results.values())

    aligned = {}
    for name, result in results.items():
        index = result.returns.loc[common_start:common_end].index
        weights = result.weights.loc[index]
        previous_weights = weights.shift(1)
        previous_weights.iloc[0] = 0.0
        turnover = weights.sub(previous_weights).abs().sum(axis=1)
        gross_returns = result.gross_returns.loc[index]
        aligned[name] = BacktestResult(
            returns=gross_returns - transaction_cost * turnover,
            gross_returns=gross_returns,
            weights=weights,
            turnover=turnover,
        )
    return aligned
