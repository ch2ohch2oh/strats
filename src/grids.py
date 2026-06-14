from functools import partial

from src.strategies import (
    dual_momentum_weights,
    trend_following_weights,
    volatility_target_weights,
)


def strategy_grids():
    return {
        "Trend Following": [
            (
                f"SMA {sma_days}",
                {"SMA Days": sma_days, "Baseline": sma_days == 200},
                partial(trend_following_weights, sma_days=sma_days),
            )
            for sma_days in [100, 150, 200, 250, 300]
        ],
        "Volatility Targeting": [
            (
                f"Lookback {lookback_days}, Target {target_volatility:.0%}",
                {
                    "Lookback Days": lookback_days,
                    "Target Volatility": target_volatility,
                    "Baseline": lookback_days == 63 and target_volatility == 0.15,
                },
                partial(
                    volatility_target_weights,
                    lookback_days=lookback_days,
                    target_volatility=target_volatility,
                ),
            )
            for lookback_days in [21, 42, 63, 126]
            for target_volatility in [0.10, 0.12, 0.15, 0.18, 0.20]
        ],
        "Dual Momentum": [
            (
                f"Lookback {lookback_days}",
                {"Lookback Days": lookback_days, "Baseline": lookback_days == 126},
                partial(dual_momentum_weights, lookback_days=lookback_days),
            )
            for lookback_days in [63, 126, 189, 252]
        ],
    }
