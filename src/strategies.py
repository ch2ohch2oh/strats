import numpy as np
import pandas as pd


def _empty_weights(prices: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)


def _apply_next_day(desired_weights: pd.DataFrame) -> pd.DataFrame:
    """Carry target weights forward and apply each close-based signal next day."""
    return desired_weights.ffill().shift(1)


def benchmark_weights(prices: pd.DataFrame) -> pd.DataFrame:
    desired = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    desired["QQQ"] = 1.0
    return _apply_next_day(desired)


def trend_following_weights(prices: pd.DataFrame, sma_days: int = 200) -> pd.DataFrame:
    sma = prices["QQQ"].rolling(sma_days).mean()
    signal = prices["QQQ"] > sma
    valid = sma.notna()

    desired = _empty_weights(prices)
    desired.loc[valid, :] = 0.0
    desired.loc[valid & signal, "QQQ"] = 1.0
    desired.loc[valid & ~signal, "BIL"] = 1.0
    return _apply_next_day(desired)


def partial_trend_weights(
    prices: pd.DataFrame,
    sma_days: int = 200,
    minimum_qqq_weight: float = 0.5,
) -> pd.DataFrame:
    """Retain partial QQQ exposure below its moving-average trend."""
    sma = prices["QQQ"].rolling(sma_days).mean()
    signal = prices["QQQ"] > sma
    valid = sma.notna()

    desired = _empty_weights(prices)
    desired.loc[valid, :] = 0.0
    desired.loc[valid, "QQQ"] = minimum_qqq_weight
    desired.loc[valid, "BIL"] = 1.0 - minimum_qqq_weight
    desired.loc[valid & signal, "QQQ"] = 1.0
    desired.loc[valid & signal, "BIL"] = 0.0
    return _apply_next_day(desired)


def trend_ensemble_weights(
    prices: pd.DataFrame,
    sma_days: tuple[int, ...] = (150, 200, 250),
    minimum_qqq_weight: float = 0.0,
) -> pd.DataFrame:
    """Scale QQQ exposure by the share of moving-average signals that are positive."""
    signals = pd.DataFrame(
        {
            days: prices["QQQ"] > prices["QQQ"].rolling(days).mean()
            for days in sma_days
        }
    )
    valid = prices["QQQ"].rolling(max(sma_days)).mean().notna()
    signal_weight = signals.mean(axis=1)
    qqq_weight = minimum_qqq_weight + (1.0 - minimum_qqq_weight) * signal_weight

    desired = _empty_weights(prices)
    desired.loc[valid, :] = 0.0
    desired.loc[valid, "QQQ"] = qqq_weight.loc[valid]
    desired.loc[valid, "BIL"] = 1.0 - qqq_weight.loc[valid]
    return _apply_next_day(desired)


def volatility_target_weights(
    prices: pd.DataFrame,
    lookback_days: int = 63,
    target_volatility: float = 0.15,
) -> pd.DataFrame:
    realized_vol = prices["QQQ"].pct_change().rolling(lookback_days).std() * np.sqrt(252)
    month_ends = prices.groupby(prices.index.to_period("M")).tail(1).index

    desired = _empty_weights(prices)
    valid_dates = month_ends.intersection(realized_vol.dropna().index)
    qqq_weight = (target_volatility / realized_vol.loc[valid_dates]).clip(upper=1.0)
    desired.loc[valid_dates, :] = 0.0
    desired.loc[valid_dates, "QQQ"] = qqq_weight
    desired.loc[valid_dates, "BIL"] = 1.0 - qqq_weight
    return _apply_next_day(desired)


def dual_momentum_weights(
    prices: pd.DataFrame,
    lookback_days: int = 126,
) -> pd.DataFrame:
    risk_assets = ["QQQ", "VOO", "VGT"]
    defensive_assets = ["BIL", "IAU", "TLT"]
    trailing_return = prices / prices.shift(lookback_days) - 1.0
    month_ends = prices.groupby(prices.index.to_period("M")).tail(1).index

    desired = _empty_weights(prices)
    for date in month_ends:
        momentum = trailing_return.loc[date]
        if momentum.isna().any():
            continue

        eligible_risk = [ticker for ticker in risk_assets if momentum[ticker] > momentum["BIL"]]
        candidates = eligible_risk + defensive_assets if eligible_risk else defensive_assets
        selected = momentum[candidates].idxmax()
        desired.loc[date, :] = 0.0
        desired.loc[date, selected] = 1.0

    return _apply_next_day(desired)
