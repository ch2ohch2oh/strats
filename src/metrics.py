import numpy as np
import pandas as pd

from src.backtest import BacktestResult


def yearly_returns(returns: pd.Series) -> pd.Series:
    return (1.0 + returns).groupby(returns.index.year).prod() - 1.0


def calculate_metrics(
    result: BacktestResult,
    initial_capital: float = 100_000.0,
) -> dict[str, float]:
    returns = result.returns
    equity = (1.0 + returns).cumprod()
    years = len(returns) / 252.0
    cagr = equity.iloc[-1] ** (1.0 / years) - 1.0
    annual_vol = returns.std(ddof=0) * np.sqrt(252)
    sharpe = returns.mean() / returns.std(ddof=0) * np.sqrt(252)
    downside = returns[returns < 0].std(ddof=0) * np.sqrt(252)
    sortino = returns.mean() * 252 / downside if downside > 0 else np.nan
    drawdown = equity / equity.cummax() - 1.0
    max_drawdown = drawdown.min()
    annual = yearly_returns(returns)

    return {
        "CAGR": cagr,
        "Annualized Volatility": annual_vol,
        "Sharpe Ratio": sharpe,
        "Sortino Ratio": sortino,
        "Max Drawdown": max_drawdown,
        "Calmar Ratio": cagr / abs(max_drawdown) if max_drawdown < 0 else np.nan,
        "Best Year": annual.max(),
        "Worst Year": annual.min(),
        "Average Yearly Return": annual.mean(),
        "Number of Trades": int((result.turnover > 1e-10).sum()),
        "Average Trades per Year": (result.turnover > 1e-10).sum() / years,
        "Average Annual Turnover": result.turnover.sum() / years,
        "Final Portfolio Value": initial_capital * equity.iloc[-1],
    }


def build_summary(results: dict[str, BacktestResult]) -> pd.DataFrame:
    summary = pd.DataFrame(
        {name: calculate_metrics(result) for name, result in results.items()}
    ).T
    return summary.sort_values("Sharpe Ratio", ascending=False)
