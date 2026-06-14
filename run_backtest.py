import argparse
from pathlib import Path

import pandas as pd

from src.backtest import align_results, run_portfolio
from src.data import load_prices
from src.metrics import build_summary
from src.plotting import save_charts
from src.reporting import format_summary, save_html_report
from src.strategies import (
    benchmark_weights,
    dual_momentum_weights,
    trend_following_weights,
    volatility_target_weights,
)


TICKERS = ["QQQ", "VOO", "VGT", "BIL", "IAU", "TLT"]
STRATEGY_NAMES = {
    "Trend Following": trend_following_weights,
    "Volatility Targeting": volatility_target_weights,
    "Dual Momentum": dual_momentum_weights,
    "QQQ Buy & Hold": benchmark_weights,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest systematic ETF strategies.")
    parser.add_argument("--refresh", action="store_true", help="Redownload Yahoo Finance data.")
    args = parser.parse_args()

    prices = load_prices(TICKERS, start="2011-01-01", refresh=args.refresh)
    raw_results = {
        name: run_portfolio(prices, weight_function(prices))
        for name, weight_function in STRATEGY_NAMES.items()
    }
    results = align_results(raw_results)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    summary = build_summary(results)
    summary.to_csv(output_dir / "results.csv")
    save_charts(results, output_dir)

    first_result = next(iter(results.values()))
    report_path = save_html_report(
        summary,
        prices.index.min(),
        prices.index.max(),
        first_result.returns.index.min(),
        first_result.returns.index.max(),
        output_dir,
    )

    print(f"\nAligned price history: {prices.index.min().date()} to {prices.index.max().date()}")
    print(f"Common backtest period: {first_result.returns.index.min().date()} to {first_result.returns.index.max().date()}\n")
    with pd.option_context("display.max_columns", None, "display.width", 220):
        print(format_summary(summary).to_string())
    print(f"\nHTML report: {report_path}")


if __name__ == "__main__":
    main()
