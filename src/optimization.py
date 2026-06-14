import html
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

from src.backtest import BacktestResult, align_results, run_portfolio
from src.metrics import calculate_metrics


def _slice_result(
    result: BacktestResult,
    index: pd.Index,
    transaction_cost: float = 0.0002,
) -> BacktestResult:
    weights = result.weights.loc[index]
    previous_weights = weights.shift(1)
    previous_weights.iloc[0] = 0.0
    turnover = weights.sub(previous_weights).abs().sum(axis=1)
    gross_returns = result.gross_returns.loc[index]
    return BacktestResult(
        returns=gross_returns - transaction_cost * turnover,
        gross_returns=gross_returns,
        weights=weights,
        turnover=turnover,
    )


def optimize_strategy(
    prices: pd.DataFrame,
    candidates: list[tuple[str, dict[str, float], Callable[[pd.DataFrame], pd.DataFrame]]],
    folds: int = 3,
) -> pd.DataFrame:
    """Rank candidates using stable Sharpe ratios across chronological subperiods."""
    raw_results = {
        candidate_name: run_portfolio(prices, weight_function(prices))
        for candidate_name, _, weight_function in candidates
    }
    aligned = align_results(raw_results)
    common_index = next(iter(aligned.values())).returns.index
    fold_indexes = np.array_split(common_index, folds)

    rows = []
    parameters_by_name = {name: parameters for name, parameters, _ in candidates}
    for candidate_name, result in aligned.items():
        full_metrics = calculate_metrics(result)
        fold_metrics = [
            calculate_metrics(_slice_result(result, fold_index))
            for fold_index in fold_indexes
        ]
        fold_sharpes = np.array([metrics["Sharpe Ratio"] for metrics in fold_metrics])

        row = {
            "Candidate": candidate_name,
            **parameters_by_name[candidate_name],
            "Robust Score": np.median(fold_sharpes) - 0.5 * np.std(fold_sharpes),
            "Full Sharpe": full_metrics["Sharpe Ratio"],
            "Full CAGR": full_metrics["CAGR"],
            "Full Max Drawdown": full_metrics["Max Drawdown"],
            "Full Annual Turnover": full_metrics["Average Annual Turnover"],
            "Worst Fold Sharpe": fold_sharpes.min(),
            "Median Fold Sharpe": np.median(fold_sharpes),
            "Fold Sharpe Std": fold_sharpes.std(),
            "Evaluation Start": common_index.min().date().isoformat(),
            "Evaluation End": common_index.max().date().isoformat(),
        }
        for number, metrics in enumerate(fold_metrics, start=1):
            row[f"Fold {number} Sharpe"] = metrics["Sharpe Ratio"]
            row[f"Fold {number} CAGR"] = metrics["CAGR"]
        rows.append(row)

    return pd.DataFrame(rows).sort_values("Robust Score", ascending=False).reset_index(drop=True)


def save_optimization_report(
    rankings: dict[str, pd.DataFrame],
    output_path: str | Path = "output/optimization_report.html",
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sections = []
    for strategy, ranking in rankings.items():
        display = ranking.head(10).copy()
        for column in ["Full CAGR", "Full Max Drawdown", "Full Annual Turnover"]:
            display[column] = display[column].map(lambda value: f"{value:.2%}")
        for column in [
            "Robust Score",
            "Full Sharpe",
            "Worst Fold Sharpe",
            "Median Fold Sharpe",
            "Fold Sharpe Std",
            "Fold 1 Sharpe",
            "Fold 2 Sharpe",
            "Fold 3 Sharpe",
        ]:
            display[column] = display[column].map(lambda value: f"{value:.2f}")

        sections.append(
            f"<section><h2>{html.escape(strategy)}</h2>"
            f"<p>Top 10 candidates ranked by stability-adjusted subperiod Sharpe.</p>"
            f"{display.to_html(index=False, border=0, classes='results')}</section>"
        )

    report = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Strategy Parameter Optimization</title>
  <style>
    body {{ margin: 0; background: #f4f7fb; color: #172033; font: 15px/1.5 system-ui, sans-serif; }}
    main {{ max-width: 1600px; margin: auto; padding: 32px 24px 56px; }}
    section {{ margin: 20px 0; padding: 20px; overflow-x: auto; background: white; border: 1px solid #dce2ea; border-radius: 12px; }}
    table {{ width: 100%; border-collapse: collapse; white-space: nowrap; }}
    th, td {{ padding: 8px 10px; border-bottom: 1px solid #dce2ea; text-align: right; }}
    th {{ background: #eef3fa; font-size: 12px; }}
    th:first-child, td:first-child {{ text-align: left; }}
    .warning {{ padding: 16px; border-left: 4px solid #c47a00; background: #fff8e8; }}
  </style>
</head>
<body>
<main>
  <h1>Strategy Parameter Optimization</h1>
  <p class="warning"><strong>Important:</strong> These rankings are robustness checks, not proof of future
  performance. Every parameter was evaluated on historical data. Prefer broad plateaus of similar results
  and simple parameters over an isolated winner.</p>
  <p><strong>Robust Score</strong> = median Sharpe across three chronological subperiods minus
  0.5 times the standard deviation of those Sharpes. Candidates within each strategy use identical
  evaluation dates.</p>
  {''.join(sections)}
</main>
</body>
</html>
"""
    output_path.write_text(report, encoding="utf-8")
    return output_path
