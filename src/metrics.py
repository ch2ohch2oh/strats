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


RISK_COLUMNS = ["Sharpe Ratio", "Sortino Ratio", "Calmar Ratio", "Max Drawdown"]


def qqq_comparison(summary: pd.DataFrame) -> pd.DataFrame:
    """Annotate summary with whether each strategy beats QQQ on risk-adjusted metrics.

    A strategy must improve at least one risk column relative to QQQ Buy & Hold
    to be considered viable. A pure return chase without risk improvement is flagged.
    """
    if "QQQ Buy & Hold" not in summary.index:
        return summary
    qqq = summary.loc["QQQ Buy & Hold"]
    beats = pd.Series(False, index=summary.index, dtype=bool)
    for col in RISK_COLUMNS:
        if col == "Max Drawdown":
            beats |= summary[col] > qqq[col]
        else:
            beats |= summary[col] > qqq[col]
    beats["QQQ Buy & Hold"] = True
    summary = summary.assign(BeatsQQQ=beats)
    return summary


def build_summary(results: dict[str, BacktestResult]) -> pd.DataFrame:
    summary = pd.DataFrame(
        {name: calculate_metrics(result) for name, result in results.items()}
    ).T
    summary = summary.sort_values("Sharpe Ratio", ascending=False)
    return qqq_comparison(summary)
