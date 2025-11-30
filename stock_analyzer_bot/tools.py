"""Smolagents tool wrappers that delegate to the MCP finance server.

#####################################################################
# TOOL CATEGORIES
#####################################################################
#
# HIGH-LEVEL TOOLS (for ToolCallingAgent):
# These tools do everything in ONE MCP call - the MCP server handles
# all the complexity internally. Best for simple orchestration.
#
#   - comprehensive_performance_report: Single stock, all 4 strategies, full report
#   - unified_market_scanner: Multi-stock scanning with rankings
#   - fundamental_analysis_report: Financial statements analysis
#
# LOW-LEVEL TOOLS (for CodeAgent):
# These are granular tools that CodeAgent can orchestrate with Python code.
# The LLM writes loops, conditions, and aggregations.
#
#   - bollinger_fibonacci_analysis: Single strategy, single stock
#   - macd_donchian_analysis: Single strategy, single stock
#   - connors_zscore_analysis: Single strategy, single stock
#   - dual_moving_average_analysis: Single strategy, single stock
#   - fundamental_analysis_report: Financial data (also used by CodeAgent)
#
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
    # Tool collections
    "HIGH_LEVEL_TOOLS",
    "LOW_LEVEL_TOOLS",
    "STRATEGY_TOOLS",
    "ALL_TOOLS",
    # Configuration
    "configure_finance_tools",
    "shutdown_finance_tools",
    # High-level tools
    "comprehensive_performance_report",
    "unified_market_scanner",
    "fundamental_analysis_report",
    # Low-level strategy tools
    "bollinger_fibonacci_analysis",
    "macd_donchian_analysis",
    "connors_zscore_analysis",
    "dual_moving_average_analysis",
]


def configure_finance_tools(server_path: str | Path | None = None) -> None:
    """Initialize the MCP server connection."""
    configure_session(server_path)


def shutdown_finance_tools() -> None:
    """Cleanly stop the MCP finance server session."""
    shutdown_session()


def _normalize_symbol(symbol: str) -> str:
    """Clean and validate a ticker symbol."""
    cleaned = symbol.strip().upper()
    if not cleaned:
        raise ValueError("Symbol must be a non-empty string")
    return cleaned


def _call_finance_tool(tool_name: str, parameters: Dict[str, object]) -> str:
    """Execute an MCP tool and return the result."""
    try:
        return get_session().call_tool(tool_name, parameters)
    except Exception as exc:
        logger.exception("Error while calling %s", tool_name)
        return f"Error calling {tool_name}: {exc}"


# ===========================================================================
# HIGH-LEVEL TOOLS (One call does everything - for ToolCallingAgent)
# ===========================================================================

@tool
def comprehensive_performance_report(symbol: str, period: str = "1y") -> str:
    """Generate a complete multi-strategy performance report for a single stock.

    This HIGH-LEVEL tool runs ALL 4 trading strategies internally and compiles
    a comprehensive markdown report with:
    - Executive summary with overall recommendation
    - Individual strategy results (Bollinger-Fib, MACD-Donchian, Connors, Dual MA)
    - Performance metrics comparison (returns, Sharpe, drawdown)
    - Risk assessment and position sizing guidance
    - Final consolidated recommendation

    Use this for single-stock technical analysis - ONE call gets everything.

    Args:
        symbol: Stock ticker to analyze (e.g., 'AAPL', 'MSFT', 'TSLA').
        period: Historical data period (default: '1y'). 
                Options: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max

    Returns:
        Complete markdown report with all strategy analyses and recommendations.
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
    """Scan multiple stocks and generate comparative analysis with rankings.

    This HIGH-LEVEL tool analyzes ALL provided stocks in ONE call, running
    all 4 strategies on each stock internally. Returns:
    - Executive summary with market overview
    - Ranked list of stocks by opportunity quality
    - Individual stock analysis summaries
    - BUY/HOLD/SELL recommendations for each stock
    - Portfolio allocation suggestions

    Use this for multi-stock scanning - much more efficient than calling
    individual strategy tools in a loop.

    Args:
        symbols: Comma-separated ticker symbols (e.g., 'AAPL,MSFT,GOOGL,AMZN').
        period: Historical data period (default: '1y').
        output_format: Report detail level:
            - 'detailed': Full analysis with all metrics (default)
            - 'summary': Condensed overview with key metrics
            - 'executive': Brief summary for quick decisions

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
    """Generate fundamental analysis from financial statements.

    Analyzes a company's financial health using:
    - Income Statement: Revenue, Net Income, Margins, Growth rates
    - Balance Sheet: Assets, Liabilities, Equity, Debt ratios
    - Cash Flow: Operating, Investing, Financing cash flows
    - Key Ratios: P/E, P/B, ROE, ROA, Current Ratio, Debt/Equity

    Returns investment thesis with strengths, risks, and recommendation.

    Args:
        symbol: Stock ticker to analyze (e.g., 'AAPL').
        period: Years of historical financial data (default: '3y').

    Returns:
        Fundamental analysis report with financial metrics and investment thesis.
    """
    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
    }
    return _call_finance_tool("generate_fundamental_analysis_report", params)


# ===========================================================================
# LOW-LEVEL STRATEGY TOOLS (Granular - for CodeAgent to orchestrate)
# ===========================================================================

@tool
def bollinger_fibonacci_analysis(
    symbol: str,
    period: str = "1y",
    window: int = 20,
    num_std: float = 2.0,
    window_swing_points: int = 10,
) -> str:
    """Analyze a stock using Bollinger Bands + Fibonacci retracement strategy.

    This LOW-LEVEL tool runs ONE strategy on ONE stock. CodeAgent can call
    this in loops to analyze multiple stocks or combine with other strategies.

    Strategy combines:
    - Bollinger Bands: Identifies overbought/oversold based on volatility
    - Fibonacci Retracement: Identifies support/resistance levels

    Args:
        symbol: Stock ticker (e.g., 'AAPL').
        period: Data period (default: '1y').
        window: Bollinger Band period (default: 20).
        num_std: Standard deviations for bands (default: 2.0).
        window_swing_points: Swing point detection window (default: 10).

    Returns:
        JSON string with signal, score, performance metrics, and interpretation.
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
    donchian_period: int = 20,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
) -> str:
    """Analyze a stock using MACD + Donchian Channel strategy.

    This LOW-LEVEL tool runs ONE strategy on ONE stock. CodeAgent can call
    this in loops to analyze multiple stocks or combine with other strategies.

    Strategy combines:
    - MACD: Momentum and trend direction indicator
    - Donchian Channel: Breakout detection using price channels

    Args:
        symbol: Stock ticker (e.g., 'AAPL').
        period: Data period (default: '1y').
        donchian_period: Donchian channel period (default: 20).
        macd_fast: MACD fast EMA period (default: 12).
        macd_slow: MACD slow EMA period (default: 26).
        macd_signal: MACD signal line period (default: 9).

    Returns:
        JSON string with signal, score, performance metrics, and interpretation.
    """
    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "donchian_period": donchian_period,
        "macd_fast": macd_fast,
        "macd_slow": macd_slow,
        "macd_signal": macd_signal,
    }
    return _call_finance_tool("analyze_macd_donchian_performance", params)


@tool
def connors_zscore_analysis(
    symbol: str,
    period: str = "1y",
    rsi_period: int = 3,
    streak_period: int = 2,
    rank_period: int = 100,
    zscore_period: int = 20,
) -> str:
    """Analyze a stock using Connors RSI + Z-Score mean reversion strategy.

    This LOW-LEVEL tool runs ONE strategy on ONE stock. CodeAgent can call
    this in loops to analyze multiple stocks or combine with other strategies.

    Strategy combines:
    - Connors RSI: Composite momentum indicator (RSI + streak + percentile rank)
    - Z-Score: Statistical deviation from mean for mean reversion signals

    Args:
        symbol: Stock ticker (e.g., 'AAPL').
        period: Data period (default: '1y').
        rsi_period: RSI calculation period (default: 3).
        streak_period: Up/down streak RSI period (default: 2).
        rank_period: Percentile rank lookback (default: 100).
        zscore_period: Z-score calculation period (default: 20).

    Returns:
        JSON string with signal, score, performance metrics, and interpretation.
    """
    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "rsi_period": rsi_period,
        "streak_period": streak_period,
        "rank_period": rank_period,
        "zscore_period": zscore_period,
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
    """Analyze a stock using Dual Moving Average (Golden/Death Cross) strategy.

    This LOW-LEVEL tool runs ONE strategy on ONE stock. CodeAgent can call
    this in loops to analyze multiple stocks or combine with other strategies.

    Strategy uses:
    - Short MA (default 50): Faster moving average for recent trend
    - Long MA (default 200): Slower moving average for long-term trend
    - Golden Cross: Short crosses above Long = Bullish
    - Death Cross: Short crosses below Long = Bearish

    Args:
        symbol: Stock ticker (e.g., 'AAPL').
        period: Data period (default: '1y').
        short_period: Short moving average period (default: 50).
        long_period: Long moving average period (default: 200).
        ma_type: Moving average type - 'SMA' or 'EMA' (default: 'EMA').

    Returns:
        JSON string with signal, crossover info, performance metrics.
    """
    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "short_period": short_period,
        "long_period": long_period,
        "ma_type": ma_type,
    }
    return _call_finance_tool("analyze_dual_ma_strategy", params)


# ===========================================================================
# TOOL COLLECTIONS
# ===========================================================================

# Low-level strategy tools (4 individual strategies)
STRATEGY_TOOLS: List = [
    bollinger_fibonacci_analysis,
    macd_donchian_analysis,
    connors_zscore_analysis,
    dual_moving_average_analysis,
]

# High-level tools (for ToolCallingAgent - one call does everything)
HIGH_LEVEL_TOOLS: List = [
    comprehensive_performance_report,
    unified_market_scanner,
    fundamental_analysis_report,
]

# Low-level tools for CodeAgent (strategies + fundamental for combined analysis)
LOW_LEVEL_TOOLS: List = [
    *STRATEGY_TOOLS,
    fundamental_analysis_report,  # CodeAgent needs this for combined analysis
]

# All tools combined (for reference)
ALL_TOOLS: List = [
    *STRATEGY_TOOLS,
    *HIGH_LEVEL_TOOLS,
]