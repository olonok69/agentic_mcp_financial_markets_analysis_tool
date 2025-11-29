"""Smolagents tool wrappers that proxy to the MCP finance server."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

from smolagents import tool

from .mcp_client import configure_session, get_session, shutdown_session

logger = logging.getLogger(__name__)


def configure_finance_tools(server_path: str | Path | None = None) -> None:
    """Allow callers to override the default MCP server path before running the agent."""
    configure_session(server_path)


def shutdown_finance_tools() -> None:
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


@tool
def bollinger_zscore_analysis(symbol: str, period: str = "1y", window: int = 20) -> str:
    """Run the MCP Bollinger Z-Score performance analysis.

    Args:
        symbol: Ticker to analyze (e.g. AAPL).
        period: Historical period string accepted by yfinance.
        window: Rolling window length used by the MCP tool.
    """
    params: Dict[str, object] = {"symbol": _normalize_symbol(symbol), "period": period, "window": window}
    return _call_finance_tool("analyze_bollinger_zscore_performance", params)


@tool
def bollinger_fibonacci_analysis(
    symbol: str,
    period: str = "1y",
    window: int = 20,
    num_std: int = 2,
    window_swing_points: int = 10,
) -> str:
    """Execute the Bollinger + Fibonacci MCP tool.

    Args:
        symbol: Ticker to analyze (e.g. TSLA).
        period: Historical period string accepted by yfinance.
        window: Bollinger Bands lookback window.
        num_std: Standard deviations for the upper/lower bands.
        window_swing_points: Window used for swing-point detection.
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
    """Invoke the MACD + Donchian channel MCP performance comparison tool.

    Args:
        symbol: Ticker to analyze.
        period: Historical period string accepted by yfinance.
        fast_period: Fast EMA period for MACD.
        slow_period: Slow EMA period for MACD.
        signal_period: Signal line EMA period for MACD.
        window: Donchian channel window.
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

    Args:
        symbol: Ticker to analyze.
        period: Historical period string accepted by yfinance.
        rsi_period: RSI window used by Connors RSI.
        streak_period: Streak RSI window.
        rank_period: Percent-rank lookback window.
        zscore_window: Rolling window used for price z-score.
        connors_weight: Weight applied to Connors RSI component.
        zscore_weight: Weight applied to Z-Score component.
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

    Args:
        symbol: Ticker to analyze.
        period: Historical period string accepted by yfinance.
        short_period: Short moving-average length.
        long_period: Long moving-average length.
        ma_type: Moving-average type accepted by MCP tool (SMA/EMA).
    """
    params: Dict[str, object] = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "short_period": short_period,
        "long_period": long_period,
        "ma_type": ma_type,
    }
    return _call_finance_tool("analyze_dual_ma_strategy", params)


STRATEGY_TOOLS: List = [
    bollinger_zscore_analysis,
    bollinger_fibonacci_analysis,
    macd_donchian_analysis,
    connors_zscore_analysis,
    dual_moving_average_analysis,
]


@tool
def comprehensive_performance_report(symbol: str, period: str = "1y") -> str:
    """Call the MCP tool that generates the multi-strategy performance markdown report.

    Args:
        symbol: Ticker to analyze.
        period: Historical period string accepted by yfinance.
    """
    params: Dict[str, object] = {"symbol": _normalize_symbol(symbol), "period": period}
    return _call_finance_tool("generate_comprehensive_analysis_report", params)


@tool
def unified_market_scanner(
    symbols: List[str] | str,
    ma_type: str = "SMA",
    short_period: int = 50,
    long_period: int = 200,
) -> str:
    """Run the MCP unified market scanner across a basket of tickers.

    Args:
        symbols: List of tickers or comma-separated string.
        ma_type: Moving-average type (SMA/EMA) for scanner.
        short_period: Short MA length.
        long_period: Long MA length.
    """
    params: Dict[str, object] = {
        "symbols": symbols,
        "ma_type": ma_type,
        "short_period": short_period,
        "long_period": long_period,
    }
    return _call_finance_tool("market_scanner", params)


@tool
def fundamental_analysis_report(symbol: str, period: str = "3y") -> str:
    """Call the MCP fundamental analysis report tool.

    Args:
        symbol: Stock ticker to analyze (e.g., MSFT).
        period: Historical span for statements (default 3y).
    """

    params: Dict[str, object] = {"symbol": _normalize_symbol(symbol), "period": period}
    return _call_finance_tool("generate_fundamental_analysis_report", params)


ALL_TOOLS: List = STRATEGY_TOOLS + [comprehensive_performance_report, unified_market_scanner, fundamental_analysis_report]


@tool
def inspect_statement_indices(symbol: str) -> str:
    """Inspect available financial statement rows from yfinance for troubleshooting.

    Args:
        symbol: Ticker to inspect (e.g., MSFT).
    """

    params: Dict[str, object] = {"symbol": _normalize_symbol(symbol)}
    return _call_finance_tool("inspect_financial_statement_indices", params)


ALL_TOOLS: List = STRATEGY_TOOLS + [
    comprehensive_performance_report,
    unified_market_scanner,
    fundamental_analysis_report,
    inspect_statement_indices,
]
