from pathlib import Path

import pandas as pd

from src.data import load_prices
from src.grids import strategy_grids
from src.optimization import optimize_strategy, save_optimization_report

TICKERS = ["QQQ", "VOO", "VGT", "BIL", "IAU", "TLT"]


def main() -> None:
    prices = load_prices(TICKERS, start="2011-01-01")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    grids = strategy_grids()

    rankings = {}
    for strategy, candidates in grids.items():
        ranking = optimize_strategy(prices, candidates)
        rankings[strategy] = ranking
        filename = strategy.lower().replace(" ", "_") + "_optimization.csv"
        ranking.to_csv(output_dir / filename, index=False)

    report_path = save_optimization_report(rankings, output_dir / "optimization_report.html")
    print(f"\nOptimization report: {report_path}\n")
    for strategy, ranking in rankings.items():
        print(strategy)
        with pd.option_context("display.max_columns", None, "display.width", 180):
            print(ranking.head(5).to_string(index=False))
        print()


if __name__ == "__main__":
    main()
