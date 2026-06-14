from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


def build_market_cap_cache(
    tickers: list[str],
    start: str,
    cache_path: str | Path = "data/market_caps.csv",
    refresh: bool = False,
) -> pd.DataFrame:
    """Build a DataFrame of daily market cap (price × shares outstanding).

    Uses actual (non-adjusted) close prices and shares outstanding from
    yfinance.  Cached to CSV to avoid repeated API calls.
    """
    cache_path = Path(cache_path)
    if cache_path.exists() and not refresh:
        return pd.read_csv(cache_path, index_col=0, parse_dates=True)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    raw = yf.download(tickers, start=start, auto_adjust=False, progress=False, actions=False)
    if raw.empty:
        raise RuntimeError("No price data was downloaded for market cap computation.")

    actual_close = raw["Close"]
    actual_close.index = pd.to_datetime(actual_close.index).tz_localize(None)
    actual_close = actual_close.sort_index()

    caps = pd.DataFrame(index=actual_close.index, columns=tickers, dtype=np.float64)
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        shares = stock.get_shares_full(start=start)
        if shares.empty:
            caps[ticker] = float("nan")
            continue
        shares.index = pd.to_datetime(shares.index).tz_localize(None)
        # Remove any duplicate dates after timezone stripping
        shares = shares.groupby(shares.index).last().sort_index()
        shares_aligned = shares.reindex(actual_close.index, method="ffill")
        caps[ticker] = actual_close[ticker] * shares_aligned

    caps.to_csv(cache_path)
    return caps


def load_prices(
    tickers: list[str],
    start: str,
    cache_path: str | Path = "data/prices.csv",
    refresh: bool = False,
) -> pd.DataFrame:
    """Load auto-adjusted closing prices, using a local CSV cache when available."""
    cache_path = Path(cache_path)

    if cache_path.exists() and not refresh:
        prices = pd.read_csv(cache_path, index_col=0, parse_dates=True)
    else:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        downloaded = yf.download(
            tickers,
            start=start,
            auto_adjust=True,
            progress=False,
            group_by="column",
        )
        if downloaded.empty:
            raise RuntimeError("No price data was downloaded from Yahoo Finance.")

        prices = downloaded["Close"] if isinstance(downloaded.columns, pd.MultiIndex) else downloaded
        if isinstance(prices, pd.Series):
            prices = prices.to_frame(name=tickers[0])
        prices.index = pd.to_datetime(prices.index).tz_localize(None)
        prices = prices.sort_index()
        prices.to_csv(cache_path)

    missing = sorted(set(tickers) - set(prices.columns))
    if missing:
        raise ValueError(f"Cached/downloaded prices are missing tickers: {missing}")

    prices = prices.loc[prices.index >= pd.Timestamp(start), tickers].astype(float)
    # A common calendar keeps every portfolio and the benchmark directly comparable.
    return prices.dropna(how="any")
