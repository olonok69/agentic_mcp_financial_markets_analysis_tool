"""Smolagents tool wrappers that delegate to the MCP finance server.

#####################################################################
# STRATEGY TOOLS CONFIGURATION
#####################################################################
# This file defines the 4 strategy tools used by the Full Strategy Analysis:
#
# 1. bollinger_fibonacci_analysis - Bollinger Bands + Fibonacci Retracement
# 2. macd_donchian_analysis - MACD + Donchian Channel Breakout
# 3. connors_zscore_analysis - Connors RSI + Z-Score Mean Reversion
# 4. dual_moving_average_analysis - 50/200 EMA Crossover (Golden/Death Cross)
#
# NOTE: bollinger_zscore_analysis is NOT included in STRATEGY_TOOLS
#       but is still available as an individual tool in ALL_TOOLS.
#####################################################################
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

from smolagents import tool

from .mcp_client import configure_session, get_session, shutdown_session

logger = logging.getLogger(__name__)

__all__ = [
    "STRATEGY_TOOLS",
    "ALL_TOOLS",
    "configure_finance_tools",
    "shutdown_finance_tools",
    "bollinger_fibonacci_analysis",
    "macd_donchian_analysis",
    "connors_zscore_analysis",
    "dual_moving_average_analysis",
    "comprehensive_performance_report",
    "unified_market_scanner",
    "fundamental_analysis_report",
]


def configure_finance_tools(server_path: str | Path | None = None) -> None:
    """Allow callers to override the default MCP server path before running the agent."""
    configure_session(server_path)


def shutdown_finance_tools() -> None:
    """Cleanly stop the MCP finance server session."""
    shutdown_session()


def _normalize_symbol(symbol: str) -> str:
    cleaned = symbol.strip().upper()
    if not cleaned:
        raise ValueError("Symbol must be a non-empty string")
    return cleaned


def _call_finance_tool(tool_name: str, parameters: Dict[str, object]) -> str:
    try:
        return get_session().call_tool(tool_name, parameters)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error while calling %s", tool_name)
        return f"Error calling {tool_name}: {exc}"


# ---------------------------------------------------------------------------
# Strategy Analysis Tools (4 strategies for Full Strategy Analysis)
# ---------------------------------------------------------------------------

@tool
def bollinger_fibonacci_analysis(
    symbol: str,
    period: str = "1y",
    window: int = 20,
    num_std: float = 2.0,
    window_swing_points: int = 10,
) -> str:
    """Run the Bollinger-Fibonacci combined MCP strategy analysis.

    This strategy combines Bollinger Bands (mean reversion) with Fibonacci 
    retracement levels (support/resistance) for comprehensive price analysis.

    Args:
        symbol: Ticker to analyze (e.g., 'AAPL', 'MSFT').
        period: Historical period string accepted by yfinance (default: '1y').
        window: Bollinger band lookback window in days (default: 20).
        num_std: Number of standard deviations for band width (default: 2.0).
        window_swing_points: Lookback for swing high/low detection (default: 10).
    
    Returns:
        Detailed performance report with signals, metrics, and recommendation.
    """
    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "window": window,
        "num_std": num_std,
        "window_swing_points": window_swing_points,
    }
    return _call_finance_tool("analyze_bollinger_fibonacci_performance", params)


@tool
def macd_donchian_analysis(
    symbol: str,
    period: str = "1y",
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    window: int = 20,
) -> str:
    """Run the MACD-Donchian combined MCP strategy analysis.

    This strategy combines MACD (momentum/trend) with Donchian Channels 
    (breakout detection) for trend-following analysis.

    Args:
        symbol: Ticker to analyze (e.g., 'AAPL', 'MSFT').
        period: Historical period string accepted by yfinance (default: '1y').
        fast_period: Fast EMA period for MACD (default: 12).
        slow_period: Slow EMA period for MACD (default: 26).
        signal_period: Signal line EMA period for MACD (default: 9).
        window: Donchian channel window in days (default: 20).
    
    Returns:
        Detailed performance report with signals, metrics, and recommendation.
    """
    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "fast_period": fast_period,
        "slow_period": slow_period,
        "signal_period": signal_period,
        "window": window,
    }
    return _call_finance_tool("analyze_macd_donchian_performance", params)


@tool
def connors_zscore_analysis(
    symbol: str,
    period: str = "1y",
    rsi_period: int = 3,
    streak_period: int = 2,
    rank_period: int = 100,
    zscore_window: int = 20,
    connors_weight: float = 0.7,
    zscore_weight: float = 0.3,
) -> str:
    """Run the Connors RSI + Z-Score combined MCP analyzer.

    This strategy combines Connors RSI (short-term momentum) with Z-Score 
    (statistical mean reversion) for short-term trading signals.

    Args:
        symbol: Ticker to analyze (e.g., 'AAPL', 'MSFT').
        period: Historical period string accepted by yfinance (default: '1y').
        rsi_period: RSI window used by Connors RSI (default: 3).
        streak_period: Streak RSI window (default: 2).
        rank_period: Percent-rank lookback window (default: 100).
        zscore_window: Rolling window used for price z-score (default: 20).
        connors_weight: Weight applied to Connors RSI component (default: 0.7).
        zscore_weight: Weight applied to Z-Score component (default: 0.3).
    
    Returns:
        Detailed performance report with signals, metrics, and recommendation.
    """
    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "rsi_period": rsi_period,
        "streak_period": streak_period,
        "rank_period": rank_period,
        "zscore_window": zscore_window,
        "connors_weight": connors_weight,
        "zscore_weight": zscore_weight,
    }
    return _call_finance_tool("analyze_connors_zscore_performance", params)


@tool
def dual_moving_average_analysis(
    symbol: str,
    period: str = "1y",
    short_period: int = 50,
    long_period: int = 200,
    ma_type: str = "EMA",
) -> str:
    """Execute the dual moving average crossover MCP strategy analysis.

    This strategy uses Golden Cross (short MA crosses above long MA = BUY) 
    and Death Cross (short MA crosses below long MA = SELL) signals.

    Args:
        symbol: Ticker to analyze (e.g., 'AAPL', 'MSFT').
        period: Historical period string accepted by yfinance (default: '1y').
        short_period: Short moving-average length in days (default: 50).
        long_period: Long moving-average length in days (default: 200).
        ma_type: Moving-average type: 'SMA' or 'EMA' (default: 'EMA').
    
    Returns:
        Detailed performance report with signals, metrics, and recommendation.
    """
    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "short_period": short_period,
        "long_period": long_period,
        "ma_type": ma_type,
    }
    return _call_finance_tool("analyze_dual_ma_strategy", params)


# ---------------------------------------------------------------------------
# STRATEGY_TOOLS: The 4 strategies used by Full Strategy Analysis
# ---------------------------------------------------------------------------
STRATEGY_TOOLS: List = [
    bollinger_fibonacci_analysis,
    macd_donchian_analysis,
    connors_zscore_analysis,
    dual_moving_average_analysis,
]


# ---------------------------------------------------------------------------
# Additional Tools (not part of the 4-strategy analysis)
# ---------------------------------------------------------------------------

@tool
def comprehensive_performance_report(symbol: str, period: str = "1y") -> str:
    """Call the MCP tool that generates the multi-strategy performance markdown report.

    This is a deterministic report that runs all 4 strategies and compiles results
    into a structured format without AI interpretation.

    Args:
        symbol: Ticker to analyze.
        period: Historical period for analysis.
    
    Returns:
        Complete markdown report with all strategy results and recommendations.
    """
    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
    }
    return _call_finance_tool("generate_comprehensive_analysis_report", params)


@tool
def unified_market_scanner(
    symbols: str,
    period: str = "1y",
    output_format: str = "detailed",
) -> str:
    """Invoke the MCP unified market scanner for a basket of tickers.

    Args:
        symbols: Comma-separated ticker symbols (e.g., 'AAPL,MSFT,GOOGL').
        period: Historical period for analysis (default: '1y').
        output_format: Report format - 'detailed', 'summary', or 'executive'.
    
    Returns:
        Multi-stock analysis report with rankings and recommendations.
    """
    params: Dict[str, object] = {
        "symbols": symbols,
        "period": period,
        "output_format": output_format,
    }
    return _call_finance_tool("market_scanner", params)


@tool
def fundamental_analysis_report(symbol: str, period: str = "3y") -> str:
    """Generate a fundamental analysis report using financial statements.

    Args:
        symbol: Ticker to analyze.
        period: Historical period for financial data.
    
    Returns:
        Fundamental analysis report with financial metrics and ratios.
    """
    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
    }
    return _call_finance_tool("generate_fundamental_analysis_report", params)


# ---------------------------------------------------------------------------
# ALL_TOOLS: Complete list including additional analysis tools
# ---------------------------------------------------------------------------
ALL_TOOLS: List = [
    *STRATEGY_TOOLS,
    comprehensive_performance_report,
    unified_market_scanner,
    fundamental_analysis_report,
]