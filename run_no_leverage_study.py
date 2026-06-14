from functools import partial
from pathlib import Path

import pandas as pd

from src.backtest import align_results, run_portfolio
from src.data import load_prices
from src.metrics import build_summary
from src.no_leverage_reporting import save_no_leverage_report
from src.plotting import save_charts
from src.reporting import format_summary
from src.strategies import (
    benchmark_weights,
    partial_trend_weights,
    trend_ensemble_weights,
    trend_following_weights,
)
from src.walkforward import build_walk_forward_results, save_walk_forward_report


TICKERS = ["QQQ", "VOO", "VGT", "BIL", "IAU", "TLT"]


def candidate_families():
    return {
        "Partial Trend": [
            (
                f"200-day SMA, {floor:.0%} QQQ floor",
                {"QQQ Floor": floor, "Baseline": floor == 0.0},
                partial(partial_trend_weights, sma_days=200, minimum_qqq_weight=floor),
            )
            for floor in [0.0, 0.25, 0.50, 0.75]
        ],
        "Trend Ensemble": [
            (
                f"150/200/250 ensemble, {floor:.0%} QQQ floor",
                {"QQQ Floor": floor, "Baseline": floor == 0.0},
                partial(trend_ensemble_weights, minimum_qqq_weight=floor),
            )
            for floor in [0.0, 0.25, 0.50, 0.75]
        ],
    }


def main() -> None:
    prices = load_prices(TICKERS, start="2011-01-01")
    output_dir = Path("output/no_leverage_study")
    output_dir.mkdir(parents=True, exist_ok=True)
    families = candidate_families()

    fixed_functions = {
        "QQQ Buy & Hold": benchmark_weights,
        "Binary 200-day Trend": trend_following_weights,
    }
    for candidates in families.values():
        for name, _, weight_function in candidates:
            fixed_functions[name] = weight_function

    fixed_results = align_results(
        {
            name: run_portfolio(prices, weight_function(prices))
            for name, weight_function in fixed_functions.items()
        }
    )
    fixed_summary = build_summary(fixed_results)
    fixed_summary.to_csv(output_dir / "full_sample_results.csv")
    save_charts(fixed_results, output_dir / "full_sample_charts")

    fixed_oos_raw = {}
    for name, weight_function in fixed_functions.items():
        weights = weight_function(prices)
        weights.loc[weights.index.year < 2016] = float("nan")
        fixed_oos_raw[name] = run_portfolio(prices, weights)
    fixed_oos_results = align_results(fixed_oos_raw)
    fixed_oos_summary = build_summary(fixed_oos_results)
    fixed_oos_summary.to_csv(output_dir / "fixed_2016_onward_results.csv")
    save_charts(fixed_oos_results, output_dir / "fixed_2016_onward_charts")

    baselines = {
        "Partial Trend": trend_following_weights,
        "Trend Ensemble": trend_ensemble_weights,
    }
    walk_forward_results, selections = build_walk_forward_results(
        prices,
        families,
        baselines,
        benchmark_weights,
        first_test_year=2016,
    )
    walk_forward_summary = build_summary(walk_forward_results)
    walk_forward_summary.to_csv(output_dir / "walk_forward_results.csv")
    for strategy, selection in selections.items():
        filename = strategy.lower().replace(" ", "_") + "_selections.csv"
        selection.to_csv(output_dir / filename, index=False)

    chart_dir = output_dir / "walk_forward_charts"
    save_charts(walk_forward_results, chart_dir)
    save_walk_forward_report(
        walk_forward_results,
        selections,
        chart_dir / "equity_curves.png",
        output_dir / "walk_forward_only_report.html",
    )
    report = save_no_leverage_report(
        fixed_summary,
        fixed_oos_summary,
        walk_forward_summary,
        selections,
        output_dir / "full_sample_charts" / "equity_curves.png",
        output_dir / "fixed_2016_onward_charts" / "equity_curves.png",
        chart_dir / "equity_curves.png",
        output_dir / "report.html",
    )

    print("\nFull-sample variants\n")
    print(format_summary(fixed_summary).to_string())
    print("\nFixed variants from 2016 onward\n")
    print(format_summary(fixed_oos_summary).to_string())
    print("\nWalk-forward variants\n")
    print(format_summary(walk_forward_summary).to_string())
    print(f"\nNo-leverage study report: {report}")


if __name__ == "__main__":
    main()
