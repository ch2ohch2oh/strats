from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    returns: pd.Series
    gross_returns: pd.Series
    weights: pd.DataFrame
    turnover: pd.Series
    name: str = ""


class ConstraintViolation(Exception):
    pass


def _check_constraints(weights: pd.DataFrame, name: str) -> None:
    """Enforce research constraints: long-only, no leverage, no shorting."""
    active = weights.dropna(how="all")
    if active.isna().any(axis=None):
        invalid = active.columns[active.isna().any()]
        raise ConstraintViolation(
            f"'{name}': NaN weights in columns {list(invalid)}. Every period must have a fully specified allocation."
        )

    if (active < -1e-8).any(axis=None):
        neg_cols = (active < -1e-8).any()
        raise ConstraintViolation(
            f"'{name}': negative weights in columns {list(neg_cols[neg_cols].index)}. "
            "Shorting is not permitted."
        )

    row_sums = active.sum(axis=1)
    if not np.allclose(row_sums, 1.0, atol=1e-6):
        bad_dates = row_sums[~np.isclose(row_sums, 1.0, atol=1e-6)]
        raise ConstraintViolation(
            f"'{name}': weights do not sum to 1.0 on {len(bad_dates)} dates "
            f"(e.g. {bad_dates.index[0]}: {bad_dates.iloc[0]:.4f}). "
            "Leverage and cash residuals are not permitted."
        )


def run_portfolio(
    prices: pd.DataFrame,
    weights: pd.DataFrame,
    transaction_cost: float = 0.0002,
    name: str = "",
) -> BacktestResult:
    """Apply target weights to close-to-close returns and charge cost on turnover.

    Raises ConstraintViolation if weights violate long-only / no-leverage rules.
    """
    _check_constraints(weights, name or "unnamed strategy")

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

    return BacktestResult(net_returns, gross_returns, active_weights, turnover, name)


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
