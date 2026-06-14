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


def voo_benchmark_weights(prices: pd.DataFrame) -> pd.DataFrame:
    desired = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    desired["VOO"] = 1.0
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


def _dynamic_floor(realized_vol: pd.Series, low_vol: float = 0.12, high_vol: float = 0.35,
                   max_floor: float = 0.75, min_floor: float = 0.0) -> pd.Series:
    out = pd.Series(min_floor, index=realized_vol.index)
    low = realized_vol <= low_vol
    mid = (realized_vol > low_vol) & (realized_vol < high_vol)
    out[low] = max_floor
    fraction = (realized_vol[mid] - low_vol) / (high_vol - low_vol)
    out[mid] = max_floor - fraction * (max_floor - min_floor)
    return out


def vol_adjusted_trend_ensemble_weights(
    prices: pd.DataFrame,
    sma_days: tuple[int, ...] = (150, 200, 250),
    vol_lookback_days: int = 63,
    low_vol: float = 0.12,
    high_vol: float = 0.35,
    max_floor: float = 0.75,
    min_floor: float = 0.0,
) -> pd.DataFrame:
    """Trend ensemble with a volatility-adjusted QQQ floor.

    In calm markets (low vol) the minimum QQQ allocation rises near max_floor.
    In turbulent markets (high vol) it drops toward min_floor, letting the trend
    ensemble reduce equity exposure further than a fixed floor would allow.
    """
    signals = pd.DataFrame(
        {days: prices["QQQ"] > prices["QQQ"].rolling(days).mean() for days in sma_days}
    )
    valid = prices["QQQ"].rolling(max(sma_days)).mean().notna()
    realized_vol = prices["QQQ"].pct_change().rolling(vol_lookback_days).std() * np.sqrt(252)
    signal_weight = signals.mean(axis=1)
    floor = _dynamic_floor(realized_vol, low_vol, high_vol, max_floor, min_floor)
    qqq_weight = floor + (1.0 - floor) * signal_weight

    desired = _empty_weights(prices)
    desired.loc[valid, :] = 0.0
    desired.loc[valid, "QQQ"] = qqq_weight.loc[valid]
    desired.loc[valid, "BIL"] = 1.0 - qqq_weight.loc[valid]
    return _apply_next_day(desired)


def qqq_voo_relative_momentum_weights(
    prices: pd.DataFrame,
    lookback_days: int = 126,
) -> pd.DataFrame:
    trailing_return = prices[["QQQ", "VOO"]] / prices[["QQQ", "VOO"]].shift(lookback_days) - 1.0
    month_ends = prices.groupby(prices.index.to_period("M")).tail(1).index
    desired = _empty_weights(prices)
    valid_dates = month_ends.intersection(trailing_return.dropna().index)

    for date in valid_dates:
        selected = trailing_return.loc[date].idxmax()
        desired.loc[date, :] = 0.0
        desired.loc[date, selected] = 1.0
    return _apply_next_day(desired)


def qqq_voo_dual_horizon_weights(prices: pd.DataFrame) -> pd.DataFrame:
    six_month = prices[["QQQ", "VOO"]] / prices[["QQQ", "VOO"]].shift(126) - 1.0
    twelve_month = prices[["QQQ", "VOO"]] / prices[["QQQ", "VOO"]].shift(252) - 1.0
    score = (six_month + twelve_month) / 2.0
    month_ends = prices.groupby(prices.index.to_period("M")).tail(1).index
    desired = _empty_weights(prices)
    valid_dates = month_ends.intersection(score.dropna().index)

    for date in valid_dates:
        selected = score.loc[date].idxmax()
        desired.loc[date, :] = 0.0
        desired.loc[date, selected] = 1.0
    return _apply_next_day(desired)


def qqq_voo_risk_adjusted_momentum_weights(
    prices: pd.DataFrame,
    return_lookback_days: int = 126,
    volatility_lookback_days: int = 63,
) -> pd.DataFrame:
    assets = ["QQQ", "VOO"]
    trailing_return = prices[assets] / prices[assets].shift(return_lookback_days) - 1.0
    realized_vol = prices[assets].pct_change().rolling(volatility_lookback_days).std() * np.sqrt(252)
    score = trailing_return / realized_vol
    month_ends = prices.groupby(prices.index.to_period("M")).tail(1).index
    desired = _empty_weights(prices)
    valid_dates = month_ends.intersection(score.dropna().index)

    for date in valid_dates:
        selected = score.loc[date].idxmax()
        desired.loc[date, :] = 0.0
        desired.loc[date, selected] = 1.0
    return _apply_next_day(desired)


def qqq_leadership_filter_weights(
    prices: pd.DataFrame,
    momentum_lookback_days: int = 126,
    sma_days: int = 200,
) -> pd.DataFrame:
    qqq_return = prices["QQQ"] / prices["QQQ"].shift(momentum_lookback_days) - 1.0
    voo_return = prices["VOO"] / prices["VOO"].shift(momentum_lookback_days) - 1.0
    qqq_sma = prices["QQQ"].rolling(sma_days).mean()
    qqq_leads = (qqq_return > voo_return) & (prices["QQQ"] > qqq_sma)
    valid = qqq_return.notna() & voo_return.notna() & qqq_sma.notna()
    month_ends = prices.groupby(prices.index.to_period("M")).tail(1).index
    valid_dates = month_ends.intersection(prices.index[valid])

    desired = _empty_weights(prices)
    desired.loc[valid_dates, :] = 0.0
    desired.loc[valid_dates, "VOO"] = 1.0
    desired.loc[valid_dates[qqq_leads.loc[valid_dates]], "QQQ"] = 1.0
    desired.loc[valid_dates[qqq_leads.loc[valid_dates]], "VOO"] = 0.0
    return _apply_next_day(desired)


def qqq_voo_blended_momentum_weights(
    prices: pd.DataFrame,
    lookback_days: int = 126,
    leader_weight: float = 0.75,
) -> pd.DataFrame:
    trailing_return = prices[["QQQ", "VOO"]] / prices[["QQQ", "VOO"]].shift(lookback_days) - 1.0
    month_ends = prices.groupby(prices.index.to_period("M")).tail(1).index
    desired = _empty_weights(prices)
    valid_dates = month_ends.intersection(trailing_return.dropna().index)

    for date in valid_dates:
        leader = trailing_return.loc[date].idxmax()
        laggard = "VOO" if leader == "QQQ" else "QQQ"
        desired.loc[date, :] = 0.0
        desired.loc[date, leader] = leader_weight
        desired.loc[date, laggard] = 1.0 - leader_weight
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


def equal_weight_monthly_weights(
    prices: pd.DataFrame,
    assets: list[str],
) -> pd.DataFrame:
    """Rebalance an equal-weight basket at each month-end."""
    month_ends = prices.groupby(prices.index.to_period("M")).tail(1).index
    desired = _empty_weights(prices)
    desired.loc[month_ends, :] = 0.0
    desired.loc[month_ends, assets] = 1.0 / len(assets)
    return _apply_next_day(desired)


def mag7_composite_weights(
    prices: pd.DataFrame,
    mag7: list[str],
    top_n: int = 3,
    risk_managed: bool = False,
    stock_sleeve: float = 1.0,
    breadth_threshold: int = 4,
) -> pd.DataFrame:
    """Select Mag7 leaders using momentum, trend, and risk-adjusted momentum.

    The risk-managed version requires broad Mag7 participation and a positive
    QQQ trend. In a weak regime it holds the existing 50/50 QQQ/BIL fallback.
    """
    stock_prices = prices[mag7]
    returns_63 = stock_prices.pct_change().rolling(63).std() * np.sqrt(252)
    momentum_126 = stock_prices / stock_prices.shift(126) - 1.0
    momentum_252 = stock_prices / stock_prices.shift(252) - 1.0
    risk_adjusted = momentum_126 / returns_63

    # Cross-sectional percentile ranks keep unlike score components comparable.
    score = (
        momentum_126.rank(axis=1, pct=True)
        + momentum_252.rank(axis=1, pct=True)
        + risk_adjusted.rank(axis=1, pct=True)
    )
    above_trend = stock_prices > stock_prices.rolling(200).mean()
    breadth = above_trend.sum(axis=1)
    qqq_trend = prices["QQQ"] > prices["QQQ"].rolling(200).mean()
    month_ends = prices.groupby(prices.index.to_period("M")).tail(1).index
    desired = _empty_weights(prices)

    for date in month_ends:
        healthy_regime = (
            breadth.loc[date] >= breadth_threshold and qqq_trend.loc[date]
        )
        if risk_managed and not healthy_regime:
            desired.loc[date, :] = 0.0
            desired.loc[date, "QQQ"] = 0.5
            desired.loc[date, "BIL"] = 0.5
            continue

        valid = (
            score.loc[date].notna()
            & above_trend.loc[date]
            & (momentum_126.loc[date] > 0.0)
        )
        if valid.sum() < top_n:
            if risk_managed:
                desired.loc[date, :] = 0.0
                desired.loc[date, "QQQ"] = 0.5
                desired.loc[date, "BIL"] = 0.5
            continue

        desired.loc[date, :] = 0.0
        selected = score.loc[date, valid].nlargest(top_n).index
        if risk_managed:
            inverse_vol = 1.0 / returns_63.loc[date, selected]
            allocation = inverse_vol / inverse_vol.sum() * stock_sleeve
        else:
            allocation = pd.Series(stock_sleeve / top_n, index=selected)
        desired.loc[date, selected] = allocation
        desired.loc[date, "VOO"] = 1.0 - stock_sleeve

    return _apply_next_day(desired)


def dynamic_equal_weight_weights(
    prices: pd.DataFrame,
    market_caps: pd.DataFrame,
    candidates: list[str],
    top_n: int = 7,
) -> pd.DataFrame:
    """Equal-weight the top N stocks by market cap at each month-end."""
    month_ends = prices.groupby(prices.index.to_period("M")).tail(1).index
    desired = _empty_weights(prices)
    for date in month_ends:
        if date not in market_caps.index:
            continue
        valid_caps = market_caps.loc[date].dropna()
        if len(valid_caps) < top_n:
            universe = valid_caps.nlargest(len(valid_caps)).index.tolist()
        else:
            universe = valid_caps.nlargest(top_n).index.tolist()
        universe = [t for t in universe if t in prices.columns]
        if not universe:
            continue
        desired.loc[date, :] = 0.0
        desired.loc[date, universe] = 1.0 / len(universe)
    return _apply_next_day(desired)


def dynamic_mag7_composite_weights(
    prices: pd.DataFrame,
    market_caps: pd.DataFrame,
    candidates: list[str],
    top_n: int = 7,
    max_stocks: int = 3,
    risk_managed: bool = False,
    stock_sleeve: float = 1.0,
    breadth_threshold: int = 4,
) -> pd.DataFrame:
    """Select Mag7-like leaders using a dynamic top-N-by-market-cap universe.

    At each month-end, the universe is the *top_n* stocks by market cap from
    *candidates*.  The same momentum / trend / risk-adjusted ranking from
    ``mag7_composite_weights`` then selects *max_stocks* from that universe.
    This eliminates the fixed-universe survivorship bias that affects the
    static Mag7 study.
    """
    month_ends = prices.groupby(prices.index.to_period("M")).tail(1).index
    desired = _empty_weights(prices)

    for date in month_ends:
        if date not in market_caps.index:
            continue
        valid_caps = market_caps.loc[date].dropna()
        if len(valid_caps) < max(2, top_n):
            continue
        universe = valid_caps.nlargest(top_n).index.tolist()
        universe = [t for t in universe if t in prices.columns]

        if len(universe) < max(2, max_stocks):
            if risk_managed:
                desired.loc[date, :] = 0.0
                desired.loc[date, "QQQ"] = 0.5
                desired.loc[date, "BIL"] = 0.5
            continue

        stock_prices = prices[universe]
        returns_63 = stock_prices.pct_change().rolling(63).std() * np.sqrt(252)
        momentum_126 = stock_prices / stock_prices.shift(126) - 1.0
        momentum_252 = stock_prices / stock_prices.shift(252) - 1.0
        risk_adjusted = momentum_126 / returns_63
        above_trend = stock_prices > stock_prices.rolling(200).mean()

        score = (
            momentum_126.rank(axis=1, pct=True)
            + momentum_252.rank(axis=1, pct=True)
            + risk_adjusted.rank(axis=1, pct=True)
        )
        breadth = above_trend.sum(axis=1)
        qqq_trend = prices["QQQ"] > prices["QQQ"].rolling(200).mean()
        healthy_regime = breadth.loc[date] >= breadth_threshold and qqq_trend.loc[date]
        if risk_managed and not healthy_regime:
            desired.loc[date, :] = 0.0
            desired.loc[date, "QQQ"] = 0.5
            desired.loc[date, "BIL"] = 0.5
            continue

        valid = (
            score.loc[date].notna()
            & above_trend.loc[date]
            & (momentum_126.loc[date] > 0.0)
        )
        valid_count = valid.sum()
        if valid_count < max_stocks:
            if risk_managed:
                desired.loc[date, :] = 0.0
                desired.loc[date, "QQQ"] = 0.5
                desired.loc[date, "BIL"] = 0.5
            continue

        desired.loc[date, :] = 0.0
        selected = score.loc[date, valid].nlargest(max_stocks).index
        if risk_managed:
            inverse_vol = 1.0 / returns_63.loc[date, selected]
            allocation = inverse_vol / inverse_vol.sum() * stock_sleeve
        else:
            allocation = pd.Series(stock_sleeve / max_stocks, index=selected)
        desired.loc[date, selected] = allocation
        desired.loc[date, "VOO"] = 1.0 - stock_sleeve

    return _apply_next_day(desired)
