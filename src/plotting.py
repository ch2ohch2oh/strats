from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.backtest import BacktestResult
from src.metrics import yearly_returns


def _save_figure(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()


def save_charts(results: dict[str, BacktestResult], output_dir: str | Path = "output") -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    returns = pd.DataFrame({name: result.returns for name, result in results.items()})
    equity = (1.0 + returns).cumprod()

    equity.plot(figsize=(12, 7), logy=True, title="Equity Curve Comparison")
    plt.ylabel("Growth of $1 (log scale)")
    _save_figure(output_dir / "equity_curves.png")

    drawdowns = equity / equity.cummax() - 1.0
    drawdowns.plot(figsize=(12, 7), title="Drawdown Comparison")
    plt.ylabel("Drawdown")
    plt.gca().yaxis.set_major_formatter(plt.matplotlib.ticker.PercentFormatter(1.0))
    _save_figure(output_dir / "drawdowns.png")

    rolling_returns = (1.0 + returns).rolling(252).apply(lambda values: values.prod(), raw=True) - 1.0
    rolling_returns.plot(figsize=(12, 7), title="Rolling 12-Month Return Comparison")
    plt.ylabel("Trailing 252-day return")
    plt.gca().yaxis.set_major_formatter(plt.matplotlib.ticker.PercentFormatter(1.0))
    _save_figure(output_dir / "rolling_12_month_returns.png")

    annual = pd.DataFrame({name: yearly_returns(result.returns) for name, result in results.items()})
    annual.plot(kind="bar", figsize=(13, 7), title="Yearly Returns")
    plt.ylabel("Return")
    plt.xlabel("Year")
    plt.gca().yaxis.set_major_formatter(plt.matplotlib.ticker.PercentFormatter(1.0))
    plt.axhline(0, color="black", linewidth=0.8)
    _save_figure(output_dir / "yearly_returns.png")
