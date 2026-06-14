from functools import partial
from pathlib import Path

from src.backtest import align_results, run_portfolio
from src.data import load_prices
from src.metrics import build_summary
from src.plotting import save_charts
from src.reporting import format_summary
from src.strategies import (
    benchmark_weights,
    qqq_leadership_filter_weights,
    qqq_voo_blended_momentum_weights,
    qqq_voo_dual_horizon_weights,
    qqq_voo_relative_momentum_weights,
    qqq_voo_risk_adjusted_momentum_weights,
    trend_ensemble_weights,
    voo_benchmark_weights,
)


TICKERS = ["QQQ", "VOO", "VGT", "BIL", "IAU", "TLT"]
STRATEGIES = {
    "Relative Momentum 126d": qqq_voo_relative_momentum_weights,
    "Dual-Horizon Momentum": qqq_voo_dual_horizon_weights,
    "Risk-Adjusted Momentum": qqq_voo_risk_adjusted_momentum_weights,
    "QQQ Leadership Filter": qqq_leadership_filter_weights,
    "Blended Momentum 75/25": qqq_voo_blended_momentum_weights,
    "50% QQQ-Floor Trend Ensemble": partial(trend_ensemble_weights, minimum_qqq_weight=0.5),
    "QQQ Buy & Hold": benchmark_weights,
    "VOO Buy & Hold": voo_benchmark_weights,
}


def main() -> None:
    prices = load_prices(TICKERS, start="2011-01-01")
    output_dir = Path("output/qqq_voo_rotation")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = align_results(
        {
            name: run_portfolio(prices, weight_function(prices), name=name)
            for name, weight_function in STRATEGIES.items()
        }
    )
    summary = build_summary(results)
    summary.to_csv(output_dir / "results.csv")
    save_charts(results, output_dir / "charts")

    oos_raw = {}
    for name, weight_function in STRATEGIES.items():
        weights = weight_function(prices)
        weights.loc[weights.index.year < 2016] = float("nan")
        oos_raw[name] = run_portfolio(prices, weights, name=name)
    oos_results = align_results(oos_raw)
    oos_summary = build_summary(oos_results)
    oos_summary.to_csv(output_dir / "fixed_2016_onward_results.csv")
    save_charts(oos_results, output_dir / "fixed_2016_onward_charts")

    print(format_summary(summary).to_string())
    print("\nFixed variants from 2016 onward\n")
    print(format_summary(oos_summary).to_string())
    print(f"\nQQQ/VOO rotation results: {output_dir / 'results.csv'}")


if __name__ == "__main__":
    main()
