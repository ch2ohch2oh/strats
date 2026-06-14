from pathlib import Path

import pandas as pd
import yfinance as yf


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
