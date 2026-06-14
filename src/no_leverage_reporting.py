import base64
import html
from pathlib import Path

import pandas as pd

from src.reporting import format_summary


def _image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def save_no_leverage_report(
    full_summary: pd.DataFrame,
    fixed_oos_summary: pd.DataFrame,
    walk_forward_summary: pd.DataFrame,
    selections: dict[str, pd.DataFrame],
    full_chart: Path,
    oos_chart: Path,
    walk_forward_chart: Path,
    output_path: str | Path,
) -> Path:
    output_path = Path(output_path)
    tables = {
        "Full-Sample Fixed Variants": format_summary(full_summary).to_html(border=0),
        "2016-2026 Fixed Variants": format_summary(fixed_oos_summary).to_html(border=0),
        "2016-2026 Walk-Forward Selection": format_summary(walk_forward_summary).to_html(border=0),
    }
    selection_parts = []
    for strategy, selection in selections.items():
        formatted = selection.copy()
        for col in formatted.columns:
            if "Robust Score" in col or "Full Sharpe" in col:
                formatted[col] = formatted[col].map(lambda value: f"{value:.2f}")
        selection_parts.append(
            f"<section><h2>{html.escape(strategy)} Annual Selections</h2>"
            f"<p>Each year, the candidate with the best robustness score (median fold Sharpe minus 0.5×std) from prior data is selected and frozen for the test year. "
            f"<strong>Training Robust Score</strong> is that stability-adjusted score on the training period. "
            f"<strong>Training Full Sharpe</strong> is the candidate's full-period Sharpe within the training data.</p>"
            f"{formatted.to_html(index=False, border=0)}</section>"
        )
    selection_html = "".join(selection_parts)



    report = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>No-Leverage Trend Study</title><style>
body{{margin:0;background:#f4f7fb;color:#172033;font:15px/1.5 system-ui,sans-serif}}
main{{max-width:1700px;margin:auto;padding:32px 24px 56px}}section{{margin:20px 0;padding:20px;overflow-x:auto;background:white;border:1px solid #dce2ea;border-radius:12px}}
table{{width:100%;border-collapse:collapse;white-space:nowrap}}th,td{{padding:8px 10px;border-bottom:1px solid #dce2ea;text-align:right}}
th{{background:#eef3fa;font-size:12px}}th:first-child,td:first-child{{text-align:left}}img{{width:100%;height:auto}}
.finding{{padding:16px;border-left:4px solid #2563eb;background:#eef5ff}}
</style></head><body><main>
<h1>No-Leverage Trend Study</h1>
<p class="finding"><strong>Current best compromise:</strong> a fixed 50% QQQ floor with either the
200-day trend or 150/200/250-day ensemble. It reached roughly 18.7% full-sample CAGR with approximately
17% volatility and a -26% maximum drawdown. Walk-forward parameter selection favored 75% floors and
weakened drawdown protection.</p>
<section><h2>Strategies Tested</h2>
<p><strong>Partial trend:</strong> hold 100% QQQ above its 200-day SMA; below it, retain a fixed
0%, 25%, 50%, or 75% QQQ allocation and place the remainder in BIL (iShares 1-3 Month Treasury Bond ETF).</p>
<p><strong>Trend ensemble:</strong> combine the 150-, 200-, and 250-day SMA signals. QQQ exposure
equals the positive-signal share, scaled above a fixed 0%, 25%, 50%, or 75% minimum; remainder goes to BIL.</p>
<p><strong>Volatility-adjusted trend ensemble:</strong> uses the same 150/200/250-day signal
combination but replaces the fixed QQQ floor with a dynamic floor. When QQQ's trailing 63-day realized
volatility is low (below ~12%), the minimum QQQ allocation rises toward 75%. When vol is high (above
~35%), the floor drops toward 0%, allowing deeper equity reduction. This lets the strategy stay more
invested in calm markets and cut deeper during turmoil.</p>
</section>
<section><h2>Full-Sample Fixed Variants</h2>{tables["Full-Sample Fixed Variants"]}</section>
<section><h2>Full-Sample Equity Curves</h2><img src="data:image/png;base64,{_image(full_chart)}"></section>
<section><h2>2016-2026 Fixed Variants</h2>{tables["2016-2026 Fixed Variants"]}</section>
<section><h2>2016-2026 Fixed Equity Curves</h2><img src="data:image/png;base64,{_image(oos_chart)}"></section>
<section><h2>2016-2026 Walk-Forward Selection</h2>{tables["2016-2026 Walk-Forward Selection"]}</section>
<section><h2>Walk-Forward Equity Curves</h2><img src="data:image/png;base64,{_image(walk_forward_chart)}"></section>
{selection_html}
</main></body></html>"""
    output_path.write_text(report, encoding="utf-8")
    return output_path
