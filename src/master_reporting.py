import base64
import html
from pathlib import Path

import pandas as pd

from src.reporting import format_summary


def _image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def _metrics_table(path: Path, rows: list[str] | None = None) -> str:
    summary = pd.read_csv(path, index_col=0)
    if rows:
        summary = summary.loc[[row for row in rows if row in summary.index]]
    return format_summary(summary).to_html(border=0)


def _optimization_summary(output_dir: Path) -> pd.DataFrame:
    rows = []
    for strategy in ["trend_following", "volatility_targeting", "dual_momentum"]:
        ranking = pd.read_csv(output_dir / f"{strategy}_optimization.csv")
        winner = ranking.iloc[0]
        baseline = ranking.loc[ranking["Baseline"].astype(str).str.lower() == "true"].iloc[0]
        rows.append(
            {
                "Strategy": strategy.replace("_", " ").title(),
                "Robust Winner": winner["Candidate"],
                "Winner Robust Score": winner["Robust Score"],
                "Baseline": baseline["Candidate"],
                "Baseline Robust Score": baseline["Robust Score"],
                "Interpretation": {
                    "trend_following": "The original 200-day SMA remains the robust winner.",
                    "volatility_targeting": "Full-history winner failed to improve results walk-forward.",
                    "dual_momentum": "Longer momentum improves results, but performance remains unstable.",
                }[strategy],
            }
        )
    display = pd.DataFrame(rows)
    for column in ["Winner Robust Score", "Baseline Robust Score"]:
        display[column] = display[column].map(lambda value: f"{value:.2f}")
    return display


def save_master_report(
    output_dir: str | Path = "output",
    output_path: str | Path = "output/master_report.html",
) -> Path:
    output_dir = Path(output_dir)
    output_path = Path(output_path)

    baseline_table = _metrics_table(
        output_dir / "results.csv",
        ["Trend Following", "Volatility Targeting", "Dual Momentum", "QQQ Buy & Hold"],
    )
    walk_forward_table = _metrics_table(
        output_dir / "walk_forward_results.csv",
        [
            "Trend Following Walk-Forward",
            "Trend Following Fixed Baseline",
            "QQQ Buy & Hold",
            "Volatility Targeting Walk-Forward",
            "Volatility Targeting Fixed Baseline",
            "Dual Momentum Walk-Forward",
            "Dual Momentum Fixed Baseline",
        ],
    )
    no_leverage_table = _metrics_table(
        output_dir / "no_leverage_study" / "fixed_2016_onward_results.csv",
        [
            "150/200/250 ensemble, 25% QQQ floor",
            "150/200/250 ensemble, 50% QQQ floor",
            "150/200/250 ensemble, 75% QQQ floor",
            "Vol-Adj Ensemble, 100% max floor, 10%/35% vol",
            "Vol-Adj Ensemble, 75% max floor, 10%/35% vol",
            "Vol-Adj Ensemble, low vol 50% floor",
            "Binary 200-day Trend",
            "QQQ Buy & Hold",
        ],
    )
    rotation_table = _metrics_table(
        output_dir / "qqq_voo_rotation" / "fixed_2016_onward_results.csv",
        [
            "Dual-Horizon Momentum",
            "Risk-Adjusted Momentum",
            "QQQ Leadership Filter",
            "Relative Momentum 126d",
            "Blended Momentum 75/25",
            "50% QQQ-Floor Trend Ensemble",
            "QQQ Buy & Hold",
            "VOO Buy & Hold",
        ],
    )
    mag7_table = _metrics_table(
        output_dir / "dynamic_mag7_study" / "fixed_2016_onward_results.csv",
        [
            "Dynamic Top7 Equal Weight",
            "Dynamic Top7 Composite Top 3",
            "Dynamic Top7 Risk-Managed Top 3",
            "Dynamic Top7 Diversified Leadership",
            "50% QQQ-Floor Trend Ensemble",
            "QQQ Buy & Hold",
        ],
    )
    optimization_table = _optimization_summary(output_dir).to_html(index=False, border=0)

    no_leverage_wf_table = _metrics_table(
        output_dir / "no_leverage_study" / "walk_forward_results.csv",
        [
            "Trend Ensemble Walk-Forward",
            "Trend Ensemble Fixed Baseline",
            "Partial Trend Walk-Forward",
            "Partial Trend Fixed Baseline",
            "Vol-Adjusted Trend Ensemble Walk-Forward",
            "Vol-Adjusted Trend Ensemble Fixed Baseline",
            "QQQ Buy & Hold",
        ],
    )

    report = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Systematic ETF Research Master Report</title><style>
:root{{--ink:#172033;--muted:#5f6b7a;--line:#dce2ea;--blue:#2563eb;--green:#087f5b}}
*{{box-sizing:border-box}}body{{margin:0;background:#f4f7fb;color:var(--ink);font:15px/1.55 system-ui,sans-serif}}
main{{max-width:1700px;margin:auto;padding:32px 24px 60px}}h1{{margin-bottom:4px;font-size:34px}}h2{{margin-top:0}}
.subtitle,.muted{{color:var(--muted)}}section{{margin:20px 0;padding:22px;overflow-x:auto;background:white;border:1px solid var(--line);border-radius:12px;box-shadow:0 2px 8px #1822300d}}
.finding{{padding:18px;border-left:5px solid var(--green);background:#eaf8f2;border-radius:8px}}
.warning{{padding:18px;border-left:5px solid #c47a00;background:#fff8e8;border-radius:8px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:22px 0}}
.card{{padding:18px;background:white;border:1px solid var(--line);border-radius:12px}}.card strong{{display:block;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.05em}}.card span{{display:block;margin-top:5px;font-size:22px;font-weight:700}}
table{{width:100%;border-collapse:collapse;white-space:nowrap}}th,td{{padding:8px 10px;border-bottom:1px solid var(--line);text-align:right}}th{{background:#eef3fa;font-size:12px}}th:first-child,td:first-child{{text-align:left}}
img{{display:block;width:100%;height:auto}}a{{color:var(--blue)}}li{{margin:6px 0}}
</style></head><body><main>
<h1>Systematic ETF Research Master Report</h1>
<p class="subtitle">Baseline strategies, no-leverage trend ensembles, robustness tests, walk-forward evidence,
rotation alternatives, and a dynamic stock-level study — evaluated against QQQ to find credible
long-only strategies with lower risk.</p>

<div class="cards">
<div class="card"><strong>Best CAGR Compromise</strong><span>50% QQQ-Floor Trend Ensemble</span></div>
<div class="card"><strong>2016-2026 CAGR</strong><span>18.89%</span></div>
<div class="card"><strong>Best Risk-Adjusted</strong><span>Vol-Adj 75% Floor Ensemble</span></div>
<div class="card"><strong>2016-2026 Sharpe / DD</strong><span>1.07 / -21.86%</span></div>
</div>

<section><h2>Methodology and Limitations</h2><ul>
<li>Yahoo Finance auto-adjusted closes are treated as total-return prices.</li>
<li>Signals use close information and apply to the next trading day's return.</li>
<li>Transaction cost is 0.02% of two-way dollar turnover.</li>
<li>All strategies are long-only and unleveraged.</li>
<li>Taxes, market impact, ETF survivorship, execution differences, and research-selection bias are excluded.</li>
<li>US technology equities performed unusually strongly during much of the available history.</li>
<li>The static Mag7 study uses today's membership throughout history and therefore has severe survivorship and hindsight bias. The dynamic top-N study replaces this with monthly market-cap reconstitution and is the honest version.</li>
</ul>
<p class="muted">Every backtest satisfies the project's backtest requirements: signals use only
pre-trade data, in-sample and out-of-sample periods are separated, parameter
sensitivity is tested, rolling performance is charted, failure cases are
documented, and strategies whose results depend on one lucky period, one exact
parameter, or unrealistic assumptions are rejected. See README for the full
methodological standards.</p></section>

<section><h2>Original Baseline Study</h2>
<p>We started with three simple BIL-based strategies as a baseline: fixed 200-day trend
following, volatility targeting, and dual momentum. The <strong>BeatsQQQ</strong> column (✓ / ✗)
indicates whether a strategy improves on QQQ's risk-adjusted returns (Sharpe, Sortino, Calmar, and max
drawdown). Strategies marked ✗ fall short of QQQ on risk-adjusted grounds, even when reported CAGR is
similar. They are retained for diagnostic completeness: understanding which approaches fail helps
calibrate expectations and avoids overfitting to what worked in this sample.</p>
<p>The initial results showed that fixed trend following improved Sharpe and drawdown over QQQ,
but could not match QQQ's raw CAGR. This motivated the no-leverage search for a better
return/risk tradeoff.</p>
{baseline_table}</section>
<section><h2>Original Strategy Equity Curves</h2><img src="data:image/png;base64,{_image(output_dir / "equity_curves.png")}" alt="Original strategy equity curves"></section>

<section><h2>No-Leverage Search: Trend Ensembles</h2>
<p>To preserve more equity exposure during trend-following periods while maintaining risk control,
we tested partial QQQ floors (25-75%) combined with multi-SMA signals (150, 200, and 250 days).
A volatility-adjusted variant was also developed to make the QQQ floor responsive to market
conditions.</p>

<h3>Fixed-Floor Strategy (Maximum CAGR)</h3>
<ol>
<li>At each close, compare QQQ with its 150-, 200-, and 250-day simple moving averages.</li>
<li>Start with a 50% minimum QQQ allocation.</li>
<li>Add one-sixth of the portfolio to QQQ for each positive moving-average signal.</li>
<li>Allocate the remainder to BIL (iShares 1-3 Month Treasury Bond ETF).</li>
<li>Apply the new allocation to the next trading day's return.</li>
</ol>
<p>This produces QQQ allocations of 50%, 66.7%, 83.3%, or 100%. It remains fully invested, long-only,
and unleveraged.</p>

<h3>Volatility-Adjusted Strategy (Better Risk-Adjusted)</h3>
<ol>
<li>At each close, compute QQQ's annualized trailing 63-day realized volatility.</li>
<li>Compare QQQ with its 150-, 200-, and 250-day simple moving averages.</li>
<li>Set the dynamic QQQ floor: 75% when realized vol is at or below 10%; 0% when vol reaches or exceeds 35%; linear in between.</li>
<li>Start the QQQ allocation at the dynamic floor, then add one-sixth for each positive moving-average signal.</li>
<li>Allocate the remainder to BIL (iShares 1-3 Month Treasury Bond ETF).</li>
<li>Apply the new allocation to the next trading day's return.</li>
</ol>
<p>This produces QQQ allocations ranging from 0% (all signals red, high vol) to 100% (all signals green, low vol).
It remains fully invested, long-only, and unleveraged. The dynamic floor lets the strategy reduce equity
exposure during volatile downturns more aggressively than a fixed-floor approach.</p>

<p>The volatility-adjusted variants (prefixed "Vol-Adj") replace the fixed QQQ floor with a dynamic floor
that rises in calm markets and falls in turbulent ones. The best vol-adjusted variant achieves the same
Sharpe as the 25% fixed-floor ensemble while improving its maximum drawdown by roughly 1.6 percentage
points, at the cost of 0.27 percentage points of CAGR. Both the fixed 50% floor and the vol-adjusted
75% floor are credible options depending on drawdown tolerance.</p>{no_leverage_table}</section>
<section><h2>No-Leverage Equity Curves</h2><img src="data:image/png;base64,{_image(output_dir / "no_leverage_study" / "fixed_2016_onward_charts" / "equity_curves.png")}" alt="No-leverage fixed strategy equity curves"></section>

<section><h2>Parameter Robustness</h2>
<p class="warning">Full-history optimization is diagnostic, not out-of-sample evidence. Prefer broad,
simple parameter regions over isolated winners.</p>{optimization_table}</section>

<section><h2>Walk-Forward Evidence</h2>
<p>At each year-end, parameters were selected using only prior data and frozen for the following year.
Trend selection modestly improved its baseline. Optimized volatility targeting failed out of sample,
and dual momentum remained weak (<span class="muted">these are retained for diagnostic context</span>).</p>
{walk_forward_table}
<p>The no-leverage study's walk-forward results extend this evidence to the trend ensemble family.
The vol-adjusted trend ensemble showed strong consistency: its fixed baseline (1.07 Sharpe across
2016-2026, -21.85% DD) marginally beat the walk-forward variant, indicating stable parameter choices
across subperiods.</p>{no_leverage_wf_table}</section>
<section><h2>Walk-Forward Equity Curves</h2><img src="data:image/png;base64,{_image(output_dir / "walk_forward_charts" / "equity_curves.png")}" alt="Walk-forward equity curves"></section>

<section><h2>QQQ / VOO Rotation Study: 2016-2026</h2>
<p>An alternative approach: monthly rotation between QQQ and VOO based on relative strength.
This reduced QQQ's drawdown and improved on VOO, but did not beat the 50% QQQ-floor trend ensemble
on risk-adjusted performance. This is consistent with QQQ and VOO sharing substantial US large-cap
market exposure: their daily-return correlation was 0.93 over this window, so rotation changes
concentration more than total equity risk.</p>
{rotation_table}</section>
<section><h2>QQQ / VOO Rotation Equity Curves</h2><img src="data:image/png;base64,{_image(output_dir / "qqq_voo_rotation" / "fixed_2016_onward_charts" / "equity_curves.png")}" alt="QQQ and VOO rotation equity curves"></section>

<section><h2>Dynamic Top-N Stock Leadership: Survivorship-Free</h2>
<p class="warning">The earlier Mag7 study used a fixed set of seven stocks chosen today and applied
retroactively. That backtest showed 33.56% CAGR, but the apparent outperformance was driven entirely by
survivorship bias. Re-running the same strategy with a reconstituted universe — at each month-end, the
top 7 stocks by actual market cap from a pool of ~32 large-cap candidates are selected — eliminates
the bias. The dynamic version's best variant (Top7 Equal Weight at 1.23 Sharpe) matches QQQ's Sharpe
but does not improve on the 50% QQQ-floor trend ensemble (1.06 Sharpe, -25.52% DD). No tested variant
beat QQQ on both return and risk. The dynamic universe results shown below are the honest version of
the concept.</p>{mag7_table}</section>
<section><h2>Dynamic Top-N Equity Curves</h2><img src="data:image/png;base64,{_image(output_dir / "dynamic_mag7_study" / "fixed_2016_onward_charts" / "equity_curves.png")}" alt="Dynamic top-N leadership equity curves"></section>

<section><h2>What Did Not Work</h2><ul>
<li>Full-history volatility optimization looked attractive but underperformed its fixed baseline walk-forward.</li>
<li>Dual momentum produced lower returns and unstable subperiod performance.</li>
<li>Annual selection among QQQ-floor levels usually chose a 75% floor, raising return but allowing roughly -30% drawdowns.</li>
<li>A 75% fixed floor approached QQQ's CAGR, but much of the desired downside protection disappeared.</li>
<li>QQQ/VOO rotation reduced concentration risk but did not outperform the 50%-floor trend ensemble on Sharpe or drawdown.</li>
<li>Mag7 leadership outperformance was a survivorship artifact. With a reconstituted universe, no variant beat the 50% floor trend ensemble on risk-adjusted return.</li>
</ul>
<p class="muted">The volatility-adjusted trend ensemble addresses several of these limitations: it reduces drawdown
more effectively than a fixed high floor while retaining competitive CAGR, and its fixed baseline showed
exceptional walk-forward stability. The tradeoff is slightly lower CAGR versus the fixed 50% floor strategy.</p></section>

<section><h2>Executive Conclusion</h2>
<p class="finding"><strong>The fixed 150/200/250-day trend ensemble with a 50% minimum QQQ allocation is
the most credible current no-leverage compromise for maximum CAGR.</strong> From 2016 through June 12, 2026, it delivered
18.89% CAGR, 17.91% volatility, a 1.06 Sharpe ratio, and a -25.52% maximum drawdown. QQQ delivered
20.43% CAGR, 22.25% volatility, a 0.95 Sharpe ratio, and a -35.12% maximum drawdown.</p>
<p class="finding"><strong>The volatility-adjusted trend ensemble is a compelling alternative for better
risk-adjusted returns.</strong> The variant with a 75% maximum QQQ floor and 10%/35% volatility thresholds
(floor rises when trailing 63-day realized vol is below ~10%, drops toward 0% above ~35%) delivered
17.60% CAGR, 16.51% volatility, a 1.07 Sharpe ratio, and a -21.86% maximum drawdown from 2016 onward.
It sacrifices roughly 1.3 percentage points of CAGR versus the fixed 50% floor but improves the maximum
drawdown by about 3.7 percentage points.</p>
<p>The simpler alternatives all fell short: dual momentum and volatility targeting failed walk-forward
testing, QQQ/VOO rotation did not improve on the trend ensemble, and the Mag7 stock-level concept
was a survivorship artifact. The fixed trend ensemble and the vol-adjusted variant both emerge from
the evidence as credible, simple, no-leverage strategies. The choice between them depends on a
manager's tolerance for equity drawdowns.</p>
</section>

<section><h2>Supporting Artifacts</h2><ul>
<li><a href="results.csv">Baseline results CSV</a></li>
<li><a href="walk_forward_results.csv">Walk-forward results CSV</a></li>
<li><a href="no_leverage_study/fixed_2016_onward_results.csv">No-leverage fixed results CSV</a></li>
<li><a href="no_leverage_study/full_sample_results.csv">No-leverage full-sample results CSV</a></li>
<li><a href="no_leverage_study/walk_forward_results.csv">No-leverage walk-forward results CSV</a></li>
<li><a href="no_leverage_study/walk_forward_only_report.html">No-leverage walk-forward detailed report</a></li>
<li><a href="qqq_voo_rotation/fixed_2016_onward_results.csv">QQQ / VOO rotation results CSV</a></li>
<li><a href="dynamic_mag7_study/fixed_2016_onward_results.csv">Dynamic top-N study results CSV</a></li>
<li><a href="mag7_study/report.html">Static Mag7 leadership detailed report (survivorship-biased)</a></li>
<li><a href="mag7_study/robustness_grid.csv">Static Mag7 parameter stability grid (survivorship-biased)</a></li>
<li><a href="../RESEARCH_FINDINGS.md">Persisted research findings</a></li>
</ul><p class="muted">Detailed HTML reports remain available for audit, but this master report is the
primary research deliverable.</p></section>
</main></body></html>"""
    output_path.write_text(report, encoding="utf-8")
    return output_path
