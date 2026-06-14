import base64
import html
from pathlib import Path

import pandas as pd

from src.backtest import BacktestResult, align_results, run_portfolio
from src.metrics import build_summary
from src.optimization import optimize_strategy


def walk_forward_strategy(
    prices: pd.DataFrame,
    candidates,
    first_test_year: int = 2016,
) -> tuple[BacktestResult, pd.DataFrame]:
    """Select parameters on prior data, then hold them fixed for each test year."""
    candidate_weights = {
        name: weight_function(prices) for name, _, weight_function in candidates
    }
    selected_weights = pd.DataFrame(index=prices.index, columns=prices.columns, dtype=float)
    selections = []

    for test_year in range(first_test_year, prices.index.max().year + 1):
        training_prices = prices.loc[prices.index.year < test_year]
        test_index = prices.index[prices.index.year == test_year]
        if training_prices.empty or test_index.empty:
            continue

        ranking = optimize_strategy(training_prices, candidates)
        winner = ranking.iloc[0]
        winner_name = winner["Candidate"]
        selected_weights.loc[test_index] = candidate_weights[winner_name].loc[test_index]
        selections.append(
            {
                "Test Year": test_year,
                "Selected Candidate": winner_name,
                "Training Start": winner["Evaluation Start"],
                "Training End": winner["Evaluation End"],
                "Training Robust Score": winner["Robust Score"],
                "Training Full Sharpe": winner["Full Sharpe"],
            }
        )

    return run_portfolio(prices, selected_weights), pd.DataFrame(selections)


def build_walk_forward_results(
    prices: pd.DataFrame,
    grids,
    baselines,
    benchmark_weights,
    first_test_year: int = 2016,
) -> tuple[dict[str, BacktestResult], dict[str, pd.DataFrame]]:
    results = {}
    selections = {}
    for strategy, candidates in grids.items():
        result, selection = walk_forward_strategy(prices, candidates, first_test_year)
        results[f"{strategy} Walk-Forward"] = result
        selections[strategy] = selection

    for strategy, weight_function in baselines.items():
        results[f"{strategy} Fixed Baseline"] = run_portfolio(prices, weight_function(prices))
    results["QQQ Buy & Hold"] = run_portfolio(prices, benchmark_weights(prices))
    return align_results(results), selections


def save_walk_forward_report(
    results: dict[str, BacktestResult],
    selections: dict[str, pd.DataFrame],
    chart_path: Path,
    output_path: str | Path = "output/walk_forward_report.html",
) -> Path:
    output_path = Path(output_path)
    summary = build_summary(results)
    display = summary.copy()
    for column in [
        "CAGR",
        "Annualized Volatility",
        "Max Drawdown",
        "Best Year",
        "Worst Year",
        "Average Yearly Return",
        "Average Annual Turnover",
    ]:
        display[column] = display[column].map(lambda value: f"{value:.2%}")
    for column in ["Sharpe Ratio", "Sortino Ratio", "Calmar Ratio", "Average Trades per Year"]:
        display[column] = display[column].map(lambda value: f"{value:.2f}")
    display["Number of Trades"] = display["Number of Trades"].astype(int)
    display["Final Portfolio Value"] = display["Final Portfolio Value"].map(lambda value: f"${value:,.0f}")

    selection_sections = []
    for strategy, selection in selections.items():
        formatted = selection.copy()
        formatted["Training Robust Score"] = formatted["Training Robust Score"].map(lambda value: f"{value:.2f}")
        formatted["Training Full Sharpe"] = formatted["Training Full Sharpe"].map(lambda value: f"{value:.2f}")
        selection_sections.append(
            f"<section><h2>{html.escape(strategy)} Annual Selections</h2>"
            f"<p><strong>Training Robust Score</strong> = stability-adjusted score (median fold Sharpe minus 0.5×std) on the training period. "
            f"<strong>Training Full Sharpe</strong> = the candidate's full-period Sharpe within the training data.</p>"
            f"{formatted.to_html(index=False, border=0)}</section>"
        )

    image = base64.b64encode(chart_path.read_bytes()).decode("ascii")
    start = next(iter(results.values())).returns.index.min().date()
    end = next(iter(results.values())).returns.index.max().date()
    report = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Walk-Forward Strategy Study</title>
<style>
body {{ margin:0; background:#f4f7fb; color:#172033; font:15px/1.5 system-ui,sans-serif }}
main {{ max-width:1600px; margin:auto; padding:32px 24px 56px }}
section {{ margin:20px 0; padding:20px; overflow-x:auto; background:white; border:1px solid #dce2ea; border-radius:12px }}
table {{ width:100%; border-collapse:collapse; white-space:nowrap }}
th,td {{ padding:8px 10px; border-bottom:1px solid #dce2ea; text-align:right }}
th {{ background:#eef3fa; font-size:12px }} th:first-child,td:first-child {{ text-align:left }}
img {{ width:100%; height:auto }} .note {{ padding:16px; border-left:4px solid #2563eb; background:#eef5ff }}
</style></head><body><main>
<h1>Walk-Forward Strategy Study</h1>
<p class="note">Parameters are selected using only data available before each test year, then frozen for
that full year. This is a stronger out-of-sample test than full-history optimization, though the shared
strategy design and parameter grids still introduce research bias.</p>
<p><strong>Out-of-sample period:</strong> {start} to {end}</p>
<section><h2>Out-of-Sample Performance</h2>{display.to_html(border=0)}</section>
<section><h2>Equity Curves</h2><img src="data:image/png;base64,{image}" alt="Walk-forward equity curves"></section>
{''.join(selection_sections)}
</main></body></html>"""
    output_path.write_text(report, encoding="utf-8")
    return output_path
