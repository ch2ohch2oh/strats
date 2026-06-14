from pathlib import Path

from src.data import load_prices
from src.grids import strategy_grids
from src.metrics import build_summary
from src.plotting import save_charts
from src.reporting import format_summary
from src.strategies import (
    benchmark_weights,
    dual_momentum_weights,
    trend_following_weights,
    volatility_target_weights,
)
from src.walkforward import build_walk_forward_results, save_walk_forward_report


TICKERS = ["QQQ", "VOO", "VGT", "BIL", "IAU", "TLT"]
BASELINES = {
    "Trend Following": trend_following_weights,
    "Volatility Targeting": volatility_target_weights,
    "Dual Momentum": dual_momentum_weights,
}


def main() -> None:
    prices = load_prices(TICKERS, start="2011-01-01")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    results, selections = build_walk_forward_results(
        prices,
        strategy_grids(),
        BASELINES,
        benchmark_weights,
        first_test_year=2016,
    )

    summary = build_summary(results)
    summary.to_csv(output_dir / "walk_forward_results.csv")
    for strategy, selection in selections.items():
        filename = strategy.lower().replace(" ", "_") + "_walk_forward_selections.csv"
        selection.to_csv(output_dir / filename, index=False)

    chart_dir = output_dir / "walk_forward_charts"
    save_charts(results, chart_dir)
    report = save_walk_forward_report(
        results,
        selections,
        chart_dir / "equity_curves.png",
        output_dir / "walk_forward_report.html",
    )
    print(format_summary(summary).to_string())
    print(f"\nWalk-forward report: {report}")


if __name__ == "__main__":
    main()
