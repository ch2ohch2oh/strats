from functools import partial
from pathlib import Path

import pandas as pd

from src.backtest import align_results, run_portfolio
from src.data import load_prices
from src.mag7_reporting import save_mag7_report
from src.metrics import build_summary
from src.plotting import save_charts
from src.reporting import format_summary
from src.strategies import (
    benchmark_weights,
    equal_weight_monthly_weights,
    mag7_composite_weights,
    trend_ensemble_weights,
    voo_benchmark_weights,
)


MAG7 = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"]
TICKERS = MAG7 + ["QQQ", "VOO", "BIL"]
STRATEGIES = {
    "Mag7 Equal Weight": partial(equal_weight_monthly_weights, assets=MAG7),
    "Mag7 Composite Top 3": partial(mag7_composite_weights, mag7=MAG7),
    "Mag7 Risk-Managed Top 3": partial(
        mag7_composite_weights, mag7=MAG7, risk_managed=True
    ),
    "Mag7 Diversified Leadership": partial(
        mag7_composite_weights, mag7=MAG7, risk_managed=True, stock_sleeve=0.6
    ),
    "50% QQQ-Floor Trend Ensemble": partial(
        trend_ensemble_weights, minimum_qqq_weight=0.5
    ),
    "QQQ Buy & Hold": benchmark_weights,
    "VOO Buy & Hold": voo_benchmark_weights,
}


def main() -> None:
    prices = load_prices(
        TICKERS,
        start="2011-01-01",
        cache_path="data/mag7_prices.csv",
    )
    output_dir = Path("output/mag7_study")
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_results = {
        name: run_portfolio(prices, weight_function(prices))
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
        fixed_2016_raw[name] = run_portfolio(prices, weights)
    fixed_2016_results = align_results(fixed_2016_raw)
    fixed_2016_summary = build_summary(fixed_2016_results)
    fixed_2016_summary.to_csv(output_dir / "fixed_2016_onward_results.csv")
    save_charts(fixed_2016_results, output_dir / "fixed_2016_onward_charts")

    robustness_rows = []
    for top_n in [2, 3, 4]:
        for breadth_threshold in [3, 4, 5]:
            for stock_sleeve in [0.6, 0.8, 1.0]:
                weights = mag7_composite_weights(
                    prices,
                    MAG7,
                    top_n=top_n,
                    risk_managed=True,
                    stock_sleeve=stock_sleeve,
                    breadth_threshold=breadth_threshold,
                )
                weights.loc[weights.index.year < 2016] = float("nan")
                result = run_portfolio(prices, weights)
                metrics = build_summary({"variant": result}).iloc[0].to_dict()
                robustness_rows.append(
                    {
                        "Top N": top_n,
                        "Breadth Threshold": breadth_threshold,
                        "Stock Sleeve": stock_sleeve,
                        **metrics,
                    }
                )
    robustness = pd.DataFrame(robustness_rows).sort_values(
        "Sharpe Ratio", ascending=False
    )
    robustness.to_csv(output_dir / "robustness_grid.csv", index=False)

    report = save_mag7_report(
        summary,
        fixed_2016_summary,
        robustness,
        output_dir / "charts" / "equity_curves.png",
        output_dir / "fixed_2016_onward_charts" / "equity_curves.png",
        output_dir / "report.html",
    )
    print(format_summary(fixed_2016_summary).to_string())
    print(f"\nMag7 study report: {report}")


if __name__ == "__main__":
    main()
