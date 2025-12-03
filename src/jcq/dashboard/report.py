"""HTML report generation with Plotly."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from jcq.eval.metrics import calculate_metrics
from jcq.eval.plots import create_equity_curve, create_drawdown_curve

logger = logging.getLogger(__name__)


def generate_report(
    df_trades: pd.DataFrame,
    metrics: Dict[str, Any],
    output_path: str,
    run_id: Optional[str] = None,
) -> str:
    """
    Generate HTML report with equity curve, drawdown, and metrics.
    
    Args:
        df_trades: DataFrame with trades
        metrics: Metrics dict
        output_path: Path to output HTML file
        run_id: Optional run ID
    
    Returns:
        Path to generated report
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create subplots
    fig = make_subplots(
        rows=3,
        cols=1,
        subplot_titles=("Equity Curve (R)", "Drawdown (R)", "Trade Distribution"),
        vertical_spacing=0.1,
    )
    
    # Equity curve
    if not df_trades.empty and "r_mult" in df_trades.columns:
        equity = create_equity_curve(df_trades)
        if not equity.empty:
            fig.add_trace(
                go.Scatter(
                    x=equity.index,
                    y=equity["equity_r"],
                    mode="lines",
                    name="Equity",
                    line=dict(color="blue"),
                ),
                row=1,
                col=1,
            )
        
        # Drawdown
        drawdown = create_drawdown_curve(df_trades)
        if not drawdown.empty:
            fig.add_trace(
                go.Scatter(
                    x=drawdown.index,
                    y=drawdown["drawdown_r"],
                    mode="lines",
                    name="Drawdown",
                    fill="tozeroy",
                    line=dict(color="red"),
                ),
                row=2,
                col=1,
            )
        
        # Trade distribution
        fig.add_trace(
            go.Histogram(
                x=df_trades["r_mult"],
                nbinsx=50,
                name="R Distribution",
            ),
            row=3,
            col=1,
        )
    
    # Update layout
    fig.update_layout(
        height=1200,
        title_text=f"JcQ Backtest Report{f' - Run {run_id}' if run_id else ''}",
        showlegend=True,
    )
    
    # Add metrics table
    metrics_html = "<h2>Metrics</h2><table border='1'><tr><th>Metric</th><th>Value</th></tr>"
    for key, value in metrics.items():
        if value is not None:
            metrics_html += f"<tr><td>{key}</td><td>{value:.4f}</td></tr>"
    metrics_html += "</table>"
    
    # Generate HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>JcQ Report</title>
    </head>
    <body>
        <h1>JcQ Quantitative Trading Report</h1>
        {metrics_html}
        {fig.to_html(include_plotlyjs='cdn')}
    </body>
    </html>
    """
    
    with open(output_path, "w") as f:
        f.write(html_content)
    
    logger.info(f"Generated report: {output_path}")
    return str(output_path)

