from functools import partial
from pathlib import Path

import pandas as pd

from src.backtest import align_results, run_portfolio
from src.data import build_market_cap_cache, load_prices
from src.metrics import build_summary
from src.plotting import save_charts
from src.reporting import format_summary
from src.strategies import (
    benchmark_weights,
    dynamic_equal_weight_weights,
    dynamic_mag7_composite_weights,
    trend_ensemble_weights,
    voo_benchmark_weights,
)

CANDIDATES = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
    "AVGO", "ADBE", "NFLX", "ORCL", "CSCO", "INTC", "AMD", "QCOM",
    "DIS", "KO", "PEP", "PG", "JNJ", "MRK", "ABBV", "UNH", "HD",
    "WMT", "COST", "XOM", "CVX", "JPM", "V", "MA", "BRK-B",
]
TICKERS = CANDIDATES + ["QQQ", "VOO", "BIL"]


def main() -> None:
    prices = load_prices(
        TICKERS,
        start="2011-01-01",
        cache_path="data/dynamic_mag7_prices.csv",
    )
    market_caps = build_market_cap_cache(
        CANDIDATES,
        start="2011-01-01",
        cache_path="data/market_caps.csv",
    )

    output_dir = Path("output/dynamic_mag7_study")
    output_dir.mkdir(parents=True, exist_ok=True)

    STRATEGIES = {
        "Dynamic Top7 Equal Weight": partial(
            dynamic_equal_weight_weights,
            candidates=CANDIDATES,
            market_caps=market_caps,
            top_n=7,
        ),
        "Dynamic Top7 Composite Top 3": partial(
            dynamic_mag7_composite_weights,
            candidates=CANDIDATES,
            market_caps=market_caps,
            top_n=7,
        ),
        "Dynamic Top7 Risk-Managed Top 3": partial(
            dynamic_mag7_composite_weights,
            candidates=CANDIDATES,
            market_caps=market_caps,
            top_n=7,
            risk_managed=True,
        ),
        "Dynamic Top7 Diversified Leadership": partial(
            dynamic_mag7_composite_weights,
            candidates=CANDIDATES,
            market_caps=market_caps,
            top_n=7,
            risk_managed=True,
            stock_sleeve=0.6,
        ),
        "Dynamic Top15 Risk-Managed Top 3": partial(
            dynamic_mag7_composite_weights,
            candidates=CANDIDATES,
            market_caps=market_caps,
            top_n=15,
            risk_managed=True,
        ),
        "50% QQQ-Floor Trend Ensemble": partial(
            trend_ensemble_weights, minimum_qqq_weight=0.5
        ),
        "QQQ Buy & Hold": benchmark_weights,
        "VOO Buy & Hold": voo_benchmark_weights,
    }

    raw_results = {
        name: run_portfolio(prices, weight_function(prices), name=name)
        for name, weight_function in STRATEGIES.items()
    }
    results = align_results(raw_results)
    summary = build_summary(results)
    summary.to_csv(output_dir / "results.csv")
    save_charts(results, output_dir / "charts")

    fixed_2016_raw = {}
    for name, result in raw_results.items():
        weights = result.weights.copy()
        weights.loc[weights.index.year < 2016] = float("nan")
        fixed_2016_raw[name] = run_portfolio(prices, weights, name=name)
    fixed_2016_results = align_results(fixed_2016_raw)
    fixed_2016_summary = build_summary(fixed_2016_results)
    fixed_2016_summary.to_csv(output_dir / "fixed_2016_onward_results.csv")
    save_charts(fixed_2016_results, output_dir / "fixed_2016_onward_charts")

    print("\n=== Full sample ===\n")
    print(format_summary(summary).to_string())
    print("\n=== 2016 onward ===\n")
    print(format_summary(fixed_2016_summary).to_string())


if __name__ == "__main__":
    main()
