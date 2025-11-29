"""Fundamental analysis MCP tool providing financial statement insights."""
from __future__ import annotations

from typing import Dict, Optional, Tuple, List, Literal

import numpy as np
import pandas as pd
import yfinance as yf
import requests
import logging
import time
import re

logger = logging.getLogger(__name__)

ROW_ALIASES: Dict[str, List[str]] = {
    "Total Revenue": ["totalRevenue", "TotalRevenue"],
    "Net Income": ["netIncome", "NetIncome"],
    "Ebitda": ["EBITDA", "ebitda", "Ebitda"],
    "Total Assets": ["totalAssets", "TotalAssets"],
    "Total Liab": ["Total Liabilities", "totalLiab", "totalLiabilities", "TotalLiabilities", "TotalLiab"],
    "Total Stockholder Equity": ["Total Equity", "totalStockholderEquity", "TotalStockholderEquity"],
    "Total Current Assets": ["totalCurrentAssets", "TotalCurrentAssets"],
    "Total Current Liabilities": ["totalCurrentLiabilities", "TotalCurrentLiabilities"],
    "Total Cash From Operating Activities": [
        "operatingCashFlow",
        "Net Cash Provided by Operating Activities",
        "totalCashFromOperatingActivities",
        "TotalCashFromOperatingActivities",
        "netCashProvidedByOperatingActivitie",
    ],
    "Capital Expenditures": ["capitalExpenditures", "Capital Expenditure", "CapitalExpenditures"],
}


def _normalize_key(value: str) -> str:
    sanitized = re.sub(r"[^a-z0-9]", "", value.lower())
    return sanitized


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    frame.index = frame.index.map(str)
    frame.columns = frame.columns.map(str)
    return frame


def _maybe_sort_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    try:
        parsed = sorted(df.columns, reverse=True)
        df = df.loc[:, parsed]
    except Exception:
        pass
    return df


def _prepare_statement(df: Optional[pd.DataFrame]) -> pd.DataFrame:
    if df is None:
        logger.debug("Statement dataframe missing; returning empty frame")
        return pd.DataFrame()
    try:
        cleaned = _normalize_columns(df).copy()
        cleaned = cleaned.apply(pd.to_numeric, errors="coerce")
        cleaned = cleaned.where(pd.notnull(cleaned))
        cleaned = _maybe_sort_columns(cleaned)
    except Exception:
        logger.exception("Failed to clean financial statement dataframe")
        return pd.DataFrame()
    logger.debug("Prepared statement with shape %s", cleaned.shape)
    return cleaned


def _latest_pair(df: pd.DataFrame, row: str) -> Tuple[Optional[float], Optional[float]]:
    if df.empty:
        logger.warning("Requested row '%s' but dataframe is empty", row)
        return None, None
    normalized_map = {_normalize_key(idx): idx for idx in df.index}
    candidates = [row] + ROW_ALIASES.get(row, [])
    normalized_candidates = [_normalize_key(candidate) for candidate in candidates]

    def _extract_series(label: str, match_key: str) -> Tuple[Optional[float], Optional[float]]:
        series = pd.to_numeric(df.loc[label], errors="coerce").dropna()
        if series.empty:
            return None, None
        latest = float(series.iloc[0])
        previous = float(series.iloc[1]) if len(series) > 1 else None
        logger.debug(
            "Row '%s' resolved via '%s' (normalized '%s') with latest=%s previous=%s",
            row,
            label,
            match_key,
            latest,
            previous,
        )
        return latest, previous

    # Exact normalized match
    for match_key in normalized_candidates:
        if match_key in normalized_map:
            return _extract_series(normalized_map[match_key], match_key)

    # Fuzzy fallback: substring containment
    anchor = normalized_candidates[0]
    if anchor:
        for key, original_label in normalized_map.items():
            if anchor in key or key in anchor:
                values = _extract_series(original_label, key)
                if values[0] is not None:
                    logger.debug("Fuzzy matched '%s' via '%s'", row, original_label)
                    return values

    logger.warning(
        "Row '%s' (aliases %s) not found. Available normalized keys: %s",
        row,
        candidates,
        list(normalized_map.keys()),
    )
    return None, None


def _format_currency(value: Optional[float]) -> str:
    if value is None or np.isnan(value):
        return "N/A"
    abs_val = abs(value)
    for threshold, suffix in [(1e12, "T"), (1e9, "B"), (1e6, "M")]:
        if abs_val >= threshold:
            return f"{value / threshold:.2f}{suffix}"
    return f"{value:,.0f}"


def _format_percent(value: Optional[float]) -> str:
    if value is None or np.isnan(value):
        return "N/A"
    return f"{value * 100:.1f}%"


def _growth(latest: Optional[float], previous: Optional[float]) -> Optional[float]:
    if latest is None or previous in (None, 0):
        return None
    try:
        return (latest - previous) / abs(previous)
    except ZeroDivisionError:
        return None


def _insight(description: str, change: Optional[float]) -> Optional[str]:
    if change is None:
        return None
    direction = "higher" if change > 0 else "lower"
    magnitude = _format_percent(abs(change))
    return f"{description} is {direction} by {magnitude} year over year."


def _fetch_company_profile(symbol: str) -> Dict[str, str]:
    url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=price&modules=assetProfile"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        result = (payload.get("quoteSummary", {}).get("result") or [{}])[0]
        price = result.get("price", {})
        profile = result.get("assetProfile", {})
        return {
            "longName": price.get("longName") or price.get("shortName"),
            "sector": profile.get("sector"),
            "industry": profile.get("industry"),
            "longBusinessSummary": profile.get("longBusinessSummary"),
        }
    except Exception:
        logger.exception("Failed to fetch company profile for %s", symbol)
        return {}


def _download_statement(ticker: yf.Ticker, kind: Literal["income", "balance", "cash"]) -> pd.DataFrame:
    fetch_plan: List[Tuple[str, callable]] = []
    if kind == "income":
        fetch_plan = [
            ("get_income_stmt_annual", lambda: ticker.get_income_stmt(freq="annual")),
            ("income_stmt", lambda: ticker.income_stmt),
            ("quarterly_income_stmt", lambda: ticker.quarterly_income_stmt),
        ]
    elif kind == "balance":
        fetch_plan = [
            ("get_balance_sheet_annual", lambda: ticker.get_balance_sheet(freq="annual")),
            ("balance_sheet", lambda: ticker.balance_sheet),
            ("quarterly_balance_sheet", lambda: ticker.quarterly_balance_sheet),
        ]
    elif kind == "cash":
        fetch_plan = [
            ("get_cash_flow_annual", lambda: ticker.get_cashflow(freq="annual")),
            ("cash_flow", lambda: getattr(ticker, "cashflow", getattr(ticker, "cash_flow", pd.DataFrame()))),
            (
                "quarterly_cash_flow",
                lambda: getattr(ticker, "quarterly_cashflow", getattr(ticker, "quarterly_cash_flow", pd.DataFrame())),
            ),
        ]
    for label, fetcher in fetch_plan:
        try:
            df = fetcher()
        except Exception:
            logger.debug("Fetcher %s for %s statements raised", label, kind, exc_info=True)
            continue
        if isinstance(df, pd.DataFrame) and not df.empty:
            logger.info("Fetched %s statement using %s with shape %s", kind, label, df.shape)
            return df
    logger.warning("All data sources for %s statements returned empty.", kind)
    return pd.DataFrame()


def add_fundamental_analysis_tool(mcp) -> None:
    """Register the fundamental analysis tool with the MCP server."""

    @mcp.tool()
    def generate_fundamental_analysis_report(symbol: str, period: str = "3y") -> str:
        """Produce a multi-statement fundamental analysis for the requested symbol."""
        start_time = time.time()
        logger.info("Starting fundamental analysis for %s (period=%s)", symbol, period)
        ticker = yf.Ticker(symbol)
        info: Dict[str, str] = _fetch_company_profile(symbol)

        income = _prepare_statement(_download_statement(ticker, "income"))
        balance = _prepare_statement(_download_statement(ticker, "balance"))
        cash_flow = _prepare_statement(_download_statement(ticker, "cash"))
        logger.debug(
            "Statement shapes for %s -> income: %s, balance: %s, cash_flow: %s",
            symbol,
            income.shape,
            balance.shape,
            cash_flow.shape,
        )

        revenue_curr, revenue_prev = _latest_pair(income, "Total Revenue")
        net_income_curr, net_income_prev = _latest_pair(income, "Net Income")
        ebitda_curr, _ = _latest_pair(income, "Ebitda")

        assets_curr, _ = _latest_pair(balance, "Total Assets")
        liabilities_curr, _ = _latest_pair(balance, "Total Liab")
        equity_curr, _ = _latest_pair(balance, "Total Stockholder Equity")
        current_assets, _ = _latest_pair(balance, "Total Current Assets")
        current_liabilities, _ = _latest_pair(balance, "Total Current Liabilities")

        operating_cash, _ = _latest_pair(cash_flow, "Total Cash From Operating Activities")
        capex, _ = _latest_pair(cash_flow, "Capital Expenditures")
        free_cash = None
        if operating_cash is not None and capex is not None:
            free_cash = operating_cash - abs(capex)

        revenue_growth = _growth(revenue_curr, revenue_prev)
        net_income_growth = _growth(net_income_curr, net_income_prev)

        debt_to_equity = None
        if equity_curr not in (None, 0):
            debt_to_equity = liabilities_curr / equity_curr if liabilities_curr is not None else None

        current_ratio = None
        if current_liabilities not in (None, 0):
            if current_assets is not None:
                current_ratio = current_assets / current_liabilities

        insights: List[str] = []
        for desc, change in [
            ("Revenue", revenue_growth),
            ("Net income", net_income_growth),
        ]:
            sentence = _insight(desc, change)
            if sentence:
                insights.append(sentence)

        if free_cash is not None and operating_cash is not None and operating_cash > 0:
            insights.append(
                "Operating cash flows currently cover capital expenditures, supporting positive free cash generation."
            )

        if debt_to_equity is not None:
            if debt_to_equity < 1:
                insights.append("Leverage remains conservative with debt-to-equity below 1x.")
            elif debt_to_equity > 2:
                insights.append("Debt-to-equity exceeds 2x, signaling elevated leverage risk.")

        company_name = info.get("longName") or symbol.upper()
        sector = info.get("sector") or "N/A"
        industry = info.get("industry") or "N/A"
        summary = info.get("longBusinessSummary") or "Business summary unavailable via Yahoo Finance."

        debt_to_equity_display = (
            f"{debt_to_equity:.2f}x" if debt_to_equity not in (None, np.nan) else "N/A"
        )
        current_ratio_display = (
            f"{current_ratio:.2f}x" if current_ratio not in (None, np.nan) else "N/A"
        )

        report_sections = [
            f"# {company_name} Fundamental Analysis",
            f"*Sector:* {sector}  |  *Industry:* {industry}  |  *Requested Period:* {period}",
            "",
            "## Company Overview",
            summary,
            "",
            "## Income Statement Highlights",
            f"- **Total Revenue:** {_format_currency(revenue_curr)}",
            f"- **Revenue YoY Change:** {_format_percent(revenue_growth)}",
            f"- **Net Income:** {_format_currency(net_income_curr)}",
            f"- **Net Income YoY Change:** {_format_percent(net_income_growth)}",
            f"- **EBITDA:** {_format_currency(ebitda_curr)}",
            "",
            "## Balance Sheet Snapshot",
            f"- **Total Assets:** {_format_currency(assets_curr)}",
            f"- **Total Liabilities:** {_format_currency(liabilities_curr)}",
            f"- **Shareholder Equity:** {_format_currency(equity_curr)}",
            f"- **Debt-to-Equity:** {debt_to_equity_display}",
            f"- **Current Ratio:** {current_ratio_display}",
            "",
            "## Cash Flow Overview",
            f"- **Operating Cash Flow:** {_format_currency(operating_cash)}",
            f"- **Capital Expenditures:** {_format_currency(capex)}",
            f"- **Free Cash Flow (OpCF - CapEx):** {_format_currency(free_cash)}",
            "",
            "## Analytical Insights",
            "\n".join(insights) if insights else "- Insufficient data to derive directional insights.",
            "",
            "## Considerations",
            "- Fundamental outputs rely on the latest financial statements available through Yahoo Finance.",
            "- Confirm data against official filings for investment decisions.",
        ]

        duration = time.time() - start_time
        logger.info("Finished fundamental analysis for %s in %.2fs", symbol, duration)
        return "\n".join(report_sections)

    return None


def add_financial_statement_index_tool(mcp) -> None:
    """Register a diagnostic tool to inspect raw yfinance DataFrame indices."""

    @mcp.tool()
    def inspect_financial_statement_indices(symbol: str) -> str:
        """Return available rows for income, balance sheet, and cashflow statements.

        Args:
            symbol: Stock ticker to inspect (e.g., MSFT).
        """

        ticker = yf.Ticker(symbol)
        tables = {
            "income": _prepare_statement(_download_statement(ticker, "income")),
            "balance": _prepare_statement(_download_statement(ticker, "balance")),
            "cash": _prepare_statement(_download_statement(ticker, "cash")),
        }

        sections = [f"# Raw Financial Statement Indices for {symbol.upper()}"]
        for label, frame in tables.items():
            indices = list(frame.index)
            normalized = [_normalize_key(idx) for idx in indices]
            sections.append(f"\n## {label.title()} Statement")
            if not indices:
                sections.append("- No rows returned (DataFrame empty).")
            else:
                sections.append("- Original rows:")
                sections.append("  - " + "\n  - ".join(indices))
                sections.append("- Normalized row tokens:")
                sections.append("  - " + "\n  - ".join(normalized))
        return "\n".join(sections)

    return None