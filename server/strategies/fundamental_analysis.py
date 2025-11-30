"""Fundamental analysis MCP tool providing comprehensive financial statement insights.

This module provides tools for generating fundamental analysis reports from Yahoo Finance
data using the yfinance library. It includes comprehensive row name aliases to handle
the various naming conventions used by yfinance across different versions and markets.

The main tool generates a markdown report with:
- Company overview and profile
- Income statement highlights (revenue, net income, margins)
- Balance sheet snapshot (assets, liabilities, equity, ratios)
- Cash flow overview (operating, investing, financing)
- Key financial ratios (profitability, liquidity, leverage)
- Analytical insights and trend analysis
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd
import requests
import yfinance as yf

logger = logging.getLogger(__name__)


# =============================================================================
# ROW NAME ALIASES - Comprehensive mapping for all yfinance row name variations
# =============================================================================
# yfinance returns different row names depending on version, data source, and market.
# This mapping covers CamelCase, spaces, and various alternative names.

ROW_ALIASES: Dict[str, List[str]] = {
    # ----- INCOME STATEMENT -----
    "Total Revenue": [
        "TotalRevenue",
        "totalRevenue",
        "Total Revenue",
        "Revenue",
        "Operating Revenue",
        "OperatingRevenue",
        "operatingRevenue",
        "Net Sales",
        "NetSales",
        "Sales",
    ],
    "Gross Profit": [
        "GrossProfit",
        "grossProfit",
        "Gross Profit",
    ],
    "Operating Income": [
        "OperatingIncome",
        "operatingIncome",
        "Operating Income",
        "Operating Profit",
        "OperatingProfit",
        "EBIT",
        "Ebit",
    ],
    "Net Income": [
        "NetIncome",
        "netIncome",
        "Net Income",
        "Net Income Common Stockholders",
        "NetIncomeCommonStockholders",
        "Net Income From Continuing Operations",
        "NetIncomeFromContinuingOperations",
        "Net Income Applicable To Common Shares",
        "NetIncomeApplicableToCommonShares",
    ],
    "EBITDA": [
        "Ebitda",
        "ebitda",
        "EBITDA",
        "NormalizedEBITDA",
        "Normalized EBITDA",
    ],
    "Cost Of Revenue": [
        "CostOfRevenue",
        "costOfRevenue",
        "Cost Of Revenue",
        "Cost of Revenue",
        "Cost Of Goods Sold",
        "CostOfGoodsSold",
        "COGS",
    ],
    "Operating Expense": [
        "OperatingExpense",
        "operatingExpense",
        "Operating Expense",
        "Operating Expenses",
        "Total Operating Expenses",
        "TotalOperatingExpenses",
    ],
    "Interest Expense": [
        "InterestExpense",
        "interestExpense",
        "Interest Expense",
        "Interest Expense Non Operating",
        "InterestExpenseNonOperating",
    ],
    "Tax Provision": [
        "TaxProvision",
        "taxProvision",
        "Tax Provision",
        "Income Tax Expense",
        "IncomeTaxExpense",
        "incomeTaxExpense",
    ],
    "Research And Development": [
        "ResearchAndDevelopment",
        "researchAndDevelopment",
        "Research And Development",
        "R&D",
        "Research Development",
        "researchDevelopment",
    ],
    "Selling General And Administration": [
        "SellingGeneralAndAdministration",
        "sellingGeneralAndAdministration",
        "Selling General And Administration",
        "SG&A",
        "General And Administrative Expense",
        "GeneralAndAdministrativeExpense",
    ],
    "Diluted EPS": [
        "DilutedEPS",
        "dilutedEPS",
        "Diluted EPS",
        "Diluted Earnings Per Share",
    ],
    "Basic EPS": [
        "BasicEPS",
        "basicEPS",
        "Basic EPS",
        "Basic Earnings Per Share",
    ],

    # ----- BALANCE SHEET -----
    "Total Assets": [
        "TotalAssets",
        "totalAssets",
        "Total Assets",
    ],
    "Total Liabilities": [
        "TotalLiabilitiesNetMinorityInterest",
        "TotalLiabilities",
        "totalLiabilities",
        "Total Liabilities",
        "Total Liab",
        "totalLiab",
        "TotalLiab",
        "Total Liabilities Net Minority Interest",
    ],
    "Total Equity": [
        "TotalEquityGrossMinorityInterest",
        "StockholdersEquity",
        "TotalStockholdersEquity",
        "Stockholders Equity",
        "Total Stockholder Equity",
        "totalStockholderEquity",
        "TotalStockholderEquity",
        "Total Equity",
        "TotalEquity",
        "totalEquity",
        "Shareholders Equity",
        "ShareholdersEquity",
        "Total Equity Gross Minority Interest",
    ],
    "Total Current Assets": [
        "TotalCurrentAssets",
        "totalCurrentAssets",
        "Total Current Assets",
        "Current Assets",
        "CurrentAssets",
    ],
    "Total Current Liabilities": [
        "TotalCurrentLiabilities",
        "totalCurrentLiabilities",
        "Total Current Liabilities",
        "Current Liabilities",
        "CurrentLiabilities",
        "CurrentDebt",
    ],
    "Total Non Current Assets": [
        "TotalNonCurrentAssets",
        "totalNonCurrentAssets",
        "Total Non Current Assets",
        "Non Current Assets",
        "NonCurrentAssets",
    ],
    "Total Non Current Liabilities": [
        "TotalNonCurrentLiabilities",
        "totalNonCurrentLiabilities",
        "Total Non Current Liabilities",
        "Non Current Liabilities",
        "NonCurrentLiabilities",
        "Long Term Debt",
        "LongTermDebt",
    ],
    "Total Debt": [
        "TotalDebt",
        "totalDebt",
        "Total Debt",
        "NetDebt",
        "Net Debt",
    ],
    "Long Term Debt": [
        "LongTermDebt",
        "longTermDebt",
        "Long Term Debt",
        "LongTermDebtNonCurrent",
        "Long Term Debt Non Current",
    ],
    "Cash And Cash Equivalents": [
        "CashAndCashEquivalents",
        "cashAndCashEquivalents",
        "Cash And Cash Equivalents",
        "Cash",
        "CashCashEquivalentsAndShortTermInvestments",
        "Cash Cash Equivalents And Short Term Investments",
    ],
    "Short Term Investments": [
        "ShortTermInvestments",
        "shortTermInvestments",
        "Short Term Investments",
        "OtherShortTermInvestments",
    ],
    "Inventory": [
        "Inventory",
        "inventory",
        "Inventories",
        "RawMaterials",
        "FinishedGoods",
    ],
    "Accounts Receivable": [
        "AccountsReceivable",
        "accountsReceivable",
        "Accounts Receivable",
        "NetReceivables",
        "Receivables",
    ],
    "Accounts Payable": [
        "AccountsPayable",
        "accountsPayable",
        "Accounts Payable",
        "Payables",
    ],
    "Retained Earnings": [
        "RetainedEarnings",
        "retainedEarnings",
        "Retained Earnings",
    ],
    "Common Stock": [
        "CommonStock",
        "commonStock",
        "Common Stock",
        "CommonStockEquity",
    ],
    "Goodwill": [
        "Goodwill",
        "goodwill",
        "GoodwillAndOtherIntangibleAssets",
    ],
    "Intangible Assets": [
        "IntangibleAssets",
        "intangibleAssets",
        "Intangible Assets",
        "OtherIntangibleAssets",
    ],
    "Property Plant And Equipment": [
        "PropertyPlantAndEquipmentNet",
        "PropertyPlantEquipmentNet",
        "Property Plant Equipment Net",
        "NetPPE",
        "Net PPE",
        "FixedAssets",
        "Fixed Assets",
    ],

    # ----- CASH FLOW STATEMENT -----
    "Operating Cash Flow": [
        "OperatingCashFlow",
        "operatingCashFlow",
        "Operating Cash Flow",
        "CashFlowFromContinuingOperatingActivities",
        "Cash Flow From Continuing Operating Activities",
        "Total Cash From Operating Activities",
        "TotalCashFromOperatingActivities",
        "totalCashFromOperatingActivities",
        "Net Cash Provided By Operating Activities",
        "NetCashProvidedByOperatingActivities",
        "netCashProvidedByOperatingActivities",
        "FreeCashFlow",
    ],
    "Investing Cash Flow": [
        "InvestingCashFlow",
        "investingCashFlow",
        "Investing Cash Flow",
        "CashFlowFromContinuingInvestingActivities",
        "Cash Flow From Continuing Investing Activities",
        "Total Cash From Investing Activities",
        "TotalCashFromInvestingActivities",
        "Net Cash Used For Investing Activities",
        "NetCashUsedForInvestingActivities",
    ],
    "Financing Cash Flow": [
        "FinancingCashFlow",
        "financingCashFlow",
        "Financing Cash Flow",
        "CashFlowFromContinuingFinancingActivities",
        "Cash Flow From Continuing Financing Activities",
        "Total Cash From Financing Activities",
        "TotalCashFromFinancingActivities",
        "Net Cash Used Provided By Financing Activities",
        "NetCashUsedProvidedByFinancingActivities",
    ],
    "Capital Expenditures": [
        "CapitalExpenditure",
        "capitalExpenditure",
        "Capital Expenditure",
        "CapitalExpenditures",
        "capitalExpenditures",
        "Capital Expenditures",
        "Capex",
        "CAPEX",
        "PurchaseOfPPE",
        "Purchase Of PPE",
    ],
    "Free Cash Flow": [
        "FreeCashFlow",
        "freeCashFlow",
        "Free Cash Flow",
    ],
    "Depreciation And Amortization": [
        "DepreciationAndAmortization",
        "depreciationAndAmortization",
        "Depreciation And Amortization",
        "DepreciationAmortizationDepletion",
        "Depreciation",
        "depreciation",
    ],
    "Stock Based Compensation": [
        "StockBasedCompensation",
        "stockBasedCompensation",
        "Stock Based Compensation",
    ],
    "Dividends Paid": [
        "DividendsPaid",
        "dividendsPaid",
        "Dividends Paid",
        "CashDividendsPaid",
        "Cash Dividends Paid",
        "CommonStockDividendPaid",
    ],
    "Repurchase Of Capital Stock": [
        "RepurchaseOfCapitalStock",
        "repurchaseOfCapitalStock",
        "Repurchase Of Capital Stock",
        "Stock Repurchase",
        "StockRepurchase",
        "CommonStockIssuance",
    ],
    "Change In Working Capital": [
        "ChangeInWorkingCapital",
        "changeInWorkingCapital",
        "Change In Working Capital",
        "ChangesInWorkingCapital",
    ],
    "Net Change In Cash": [
        "NetChangeInCash",
        "netChangeInCash",
        "Net Change In Cash",
        "ChangeInCash",
        "Change In Cash",
        "ChangeInCashSupplementalAsReported",
    ],
    "Beginning Cash Position": [
        "BeginningCashPosition",
        "beginningCashPosition",
        "Beginning Cash Position",
    ],
    "End Cash Position": [
        "EndCashPosition",
        "endCashPosition",
        "End Cash Position",
        "EndingCashPosition",
    ],
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _normalize_key(value: str) -> str:
    """Normalize a key for comparison by removing non-alphanumeric chars and lowercasing."""
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize DataFrame columns to handle MultiIndex and ensure string types."""
    if df is None or df.empty:
        return pd.DataFrame()
    frame = df.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    frame.index = frame.index.map(str)
    frame.columns = frame.columns.map(str)
    return frame


def _maybe_sort_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Sort DataFrame columns in descending order (newest first)."""
    if df.empty:
        return df
    try:
        # Try to parse columns as dates and sort
        col_dates = pd.to_datetime(df.columns, errors="coerce")
        if col_dates.notna().all():
            sorted_cols = df.columns[col_dates.argsort()[::-1]]
            return df.loc[:, sorted_cols]
        # Fallback to string sorting
        parsed = sorted(df.columns, reverse=True)
        return df.loc[:, parsed]
    except Exception:
        return df


def _prepare_statement(df: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Clean and prepare a financial statement DataFrame for analysis."""
    if df is None:
        logger.debug("Statement DataFrame is None; returning empty frame")
        return pd.DataFrame()
    if df.empty:
        logger.debug("Statement DataFrame is empty; returning empty frame")
        return pd.DataFrame()
    try:
        cleaned = _normalize_columns(df).copy()
        cleaned = cleaned.apply(pd.to_numeric, errors="coerce")
        cleaned = cleaned.where(pd.notnull(cleaned))
        cleaned = _maybe_sort_columns(cleaned)
        logger.debug("Prepared statement with shape %s", cleaned.shape)
        return cleaned
    except Exception:
        logger.exception("Failed to clean financial statement DataFrame")
        return pd.DataFrame()


def _latest_pair(df: pd.DataFrame, row: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Extract the latest and previous values for a given row from the DataFrame.

    Uses ROW_ALIASES to find the row, trying exact matches first, then normalized
    matches, and finally fuzzy substring matches.

    Args:
        df: The prepared financial statement DataFrame
        row: The row name to look for (should be a key in ROW_ALIASES)

    Returns:
        Tuple of (latest_value, previous_value), with None for missing values
    """
    if df.empty:
        logger.warning("Requested row '%s' but DataFrame is empty", row)
        return None, None

    # Build normalized index map
    normalized_map = {_normalize_key(idx): idx for idx in df.index}
    candidates = [row] + ROW_ALIASES.get(row, [])
    normalized_candidates = [_normalize_key(c) for c in candidates]

    def _extract_series(label: str, match_key: str) -> Tuple[Optional[float], Optional[float]]:
        """Extract latest and previous values from a matched row."""
        try:
            series = pd.to_numeric(df.loc[label], errors="coerce").dropna()
            if series.empty:
                return None, None
            latest = float(series.iloc[0]) if len(series) > 0 else None
            previous = float(series.iloc[1]) if len(series) > 1 else None
            logger.debug(
                "Row '%s' resolved via '%s' (normalized '%s') -> latest=%s, previous=%s",
                row, label, match_key, latest, previous
            )
            return latest, previous
        except Exception as e:
            logger.debug("Error extracting series for %s: %s", label, e)
            return None, None

    # Try exact normalized match
    for match_key in normalized_candidates:
        if match_key in normalized_map:
            result = _extract_series(normalized_map[match_key], match_key)
            if result[0] is not None:
                return result

    # Try fuzzy substring match
    anchor = normalized_candidates[0] if normalized_candidates else ""
    if anchor:
        for key, original_label in normalized_map.items():
            if anchor in key or key in anchor:
                result = _extract_series(original_label, key)
                if result[0] is not None:
                    logger.debug("Fuzzy matched '%s' via '%s'", row, original_label)
                    return result

    logger.warning(
        "Row '%s' (aliases %s) not found. Available normalized keys: %s",
        row, candidates[:3], list(normalized_map.keys())[:10]
    )
    return None, None


def _get_value(df: pd.DataFrame, row: str, column_idx: int = 0) -> Optional[float]:
    """Get a single value from a DataFrame for a given row and column index."""
    latest, _ = _latest_pair(df, row)
    return latest


def _format_currency(value: Optional[float]) -> str:
    """Format a numeric value as currency with appropriate suffix (T/B/M/K)."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A"
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    for threshold, suffix in [(1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")]:
        if abs_val >= threshold:
            return f"{sign}${abs_val / threshold:.2f}{suffix}"
    return f"{sign}${abs_val:,.0f}"


def _format_percent(value: Optional[float]) -> str:
    """Format a numeric value as a percentage."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A"
    return f"{value * 100:+.1f}%" if value >= 0 else f"{value * 100:.1f}%"


def _format_ratio(value: Optional[float], suffix: str = "x") -> str:
    """Format a numeric value as a ratio."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A"
    return f"{value:.2f}{suffix}"


def _growth(latest: Optional[float], previous: Optional[float]) -> Optional[float]:
    """Calculate growth rate between two values."""
    if latest is None or previous is None or previous == 0:
        return None
    try:
        return (latest - previous) / abs(previous)
    except (ZeroDivisionError, TypeError):
        return None


def _safe_divide(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    """Safely divide two numbers, returning None if division is not possible."""
    if numerator is None or denominator is None or denominator == 0:
        return None
    try:
        return numerator / denominator
    except (ZeroDivisionError, TypeError):
        return None


def _insight(description: str, change: Optional[float], threshold: float = 0.05) -> Optional[str]:
    """Generate an insight string for a year-over-year change."""
    if change is None or abs(change) < threshold:
        return None
    direction = "increased" if change > 0 else "decreased"
    magnitude = f"{abs(change) * 100:.1f}%"
    return f"- {description} {direction} by {magnitude} year-over-year."


# =============================================================================
# DATA FETCHING FUNCTIONS
# =============================================================================

def _fetch_company_profile(symbol: str) -> Dict[str, Any]:
    """
    Fetch company profile information using multiple fallback methods.

    Tries:
    1. yfinance Ticker.info property
    2. Direct Yahoo Finance API call

    Args:
        symbol: Stock ticker symbol

    Returns:
        Dictionary with company profile data
    """
    profile: Dict[str, Any] = {}

    # Method 1: Try yfinance Ticker.info
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        if info:
            profile = {
                "longName": info.get("longName") or info.get("shortName") or symbol.upper(),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "longBusinessSummary": info.get("longBusinessSummary"),
                "website": info.get("website"),
                "country": info.get("country"),
                "fullTimeEmployees": info.get("fullTimeEmployees"),
                "marketCap": info.get("marketCap"),
                "trailingPE": info.get("trailingPE"),
                "forwardPE": info.get("forwardPE"),
                "dividendYield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
                "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
                "averageVolume": info.get("averageVolume"),
            }
            if profile.get("longName"):
                logger.info("Fetched company profile via yfinance.info for %s", symbol)
                return profile
    except Exception as e:
        logger.debug("yfinance.info failed for %s: %s", symbol, e)

    # Method 2: Try direct Yahoo Finance API
    try:
        url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
        params = {"modules": "price,assetProfile,summaryDetail"}
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        result = (payload.get("quoteSummary", {}).get("result") or [{}])[0]
        price = result.get("price", {})
        asset_profile = result.get("assetProfile", {})
        summary_detail = result.get("summaryDetail", {})

        profile = {
            "longName": price.get("longName") or price.get("shortName") or symbol.upper(),
            "sector": asset_profile.get("sector"),
            "industry": asset_profile.get("industry"),
            "longBusinessSummary": asset_profile.get("longBusinessSummary"),
            "website": asset_profile.get("website"),
            "country": asset_profile.get("country"),
            "fullTimeEmployees": asset_profile.get("fullTimeEmployees"),
            "marketCap": price.get("marketCap", {}).get("raw"),
            "trailingPE": summary_detail.get("trailingPE", {}).get("raw"),
            "forwardPE": summary_detail.get("forwardPE", {}).get("raw"),
            "dividendYield": summary_detail.get("dividendYield", {}).get("raw"),
            "beta": summary_detail.get("beta", {}).get("raw"),
        }
        logger.info("Fetched company profile via Yahoo API for %s", symbol)
    except Exception as e:
        logger.warning("Failed to fetch company profile for %s: %s", symbol, e)
        profile = {"longName": symbol.upper()}

    return profile


def _download_statement(
    ticker: yf.Ticker,
    kind: Literal["income", "balance", "cash"]
) -> pd.DataFrame:
    """
    Download a financial statement from yfinance using multiple fallback methods.

    Args:
        ticker: yfinance Ticker object
        kind: Type of statement ("income", "balance", "cash")

    Returns:
        DataFrame with financial statement data, or empty DataFrame if all methods fail
    """
    fetch_plan: List[Tuple[str, callable]] = []

    if kind == "income":
        fetch_plan = [
            ("income_stmt", lambda: ticker.income_stmt),
            ("get_income_stmt_annual", lambda: ticker.get_income_stmt(freq="annual")),
            ("financials", lambda: ticker.financials),
            ("quarterly_income_stmt", lambda: ticker.quarterly_income_stmt),
        ]
    elif kind == "balance":
        fetch_plan = [
            ("balance_sheet", lambda: ticker.balance_sheet),
            ("get_balance_sheet_annual", lambda: ticker.get_balance_sheet(freq="annual")),
            ("quarterly_balance_sheet", lambda: ticker.quarterly_balance_sheet),
        ]
    elif kind == "cash":
        fetch_plan = [
            ("cash_flow", lambda: ticker.cash_flow),
            ("cashflow", lambda: ticker.cashflow),
            ("get_cash_flow_annual", lambda: ticker.get_cashflow(freq="annual")),
            ("quarterly_cashflow", lambda: ticker.quarterly_cashflow),
        ]

    for label, fetcher in fetch_plan:
        try:
            df = fetcher()
            if isinstance(df, pd.DataFrame) and not df.empty:
                logger.info("Fetched %s statement using '%s' with shape %s", kind, label, df.shape)
                return df
        except Exception as e:
            logger.debug("Fetcher '%s' for %s statement raised: %s", label, kind, e)
            continue

    logger.warning("All data sources for %s statement returned empty", kind)
    return pd.DataFrame()


# =============================================================================
# FINANCIAL RATIO CALCULATIONS
# =============================================================================

def _calculate_profitability_ratios(
    income: pd.DataFrame,
) -> Dict[str, Optional[float]]:
    """Calculate profitability ratios from income statement."""
    revenue = _get_value(income, "Total Revenue")
    gross_profit = _get_value(income, "Gross Profit")
    operating_income = _get_value(income, "Operating Income")
    net_income = _get_value(income, "Net Income")
    ebitda = _get_value(income, "EBITDA")

    return {
        "gross_margin": _safe_divide(gross_profit, revenue),
        "operating_margin": _safe_divide(operating_income, revenue),
        "net_profit_margin": _safe_divide(net_income, revenue),
        "ebitda_margin": _safe_divide(ebitda, revenue),
    }


def _calculate_liquidity_ratios(
    balance: pd.DataFrame,
) -> Dict[str, Optional[float]]:
    """Calculate liquidity ratios from balance sheet."""
    current_assets = _get_value(balance, "Total Current Assets")
    current_liabilities = _get_value(balance, "Total Current Liabilities")
    cash = _get_value(balance, "Cash And Cash Equivalents")
    inventory = _get_value(balance, "Inventory")

    quick_assets = None
    if current_assets is not None:
        inventory_val = inventory if inventory is not None else 0
        quick_assets = current_assets - inventory_val

    return {
        "current_ratio": _safe_divide(current_assets, current_liabilities),
        "quick_ratio": _safe_divide(quick_assets, current_liabilities),
        "cash_ratio": _safe_divide(cash, current_liabilities),
    }


def _calculate_leverage_ratios(
    balance: pd.DataFrame,
) -> Dict[str, Optional[float]]:
    """Calculate leverage ratios from balance sheet."""
    total_liabilities = _get_value(balance, "Total Liabilities")
    total_equity = _get_value(balance, "Total Equity")
    total_assets = _get_value(balance, "Total Assets")
    total_debt = _get_value(balance, "Total Debt")
    long_term_debt = _get_value(balance, "Long Term Debt")

    return {
        "debt_to_equity": _safe_divide(total_liabilities, total_equity),
        "debt_to_assets": _safe_divide(total_liabilities, total_assets),
        "equity_ratio": _safe_divide(total_equity, total_assets),
        "long_term_debt_to_equity": _safe_divide(long_term_debt, total_equity),
    }


def _calculate_efficiency_ratios(
    income: pd.DataFrame,
    balance: pd.DataFrame,
) -> Dict[str, Optional[float]]:
    """Calculate efficiency and return ratios."""
    net_income = _get_value(income, "Net Income")
    total_assets = _get_value(balance, "Total Assets")
    total_equity = _get_value(balance, "Total Equity")

    return {
        "return_on_assets": _safe_divide(net_income, total_assets),
        "return_on_equity": _safe_divide(net_income, total_equity),
    }


# =============================================================================
# MCP TOOL REGISTRATION
# =============================================================================

def add_fundamental_analysis_tool(mcp) -> None:
    """Register the fundamental analysis tool with the MCP server."""

    @mcp.tool()
    def generate_fundamental_analysis_report(symbol: str, period: str = "3y") -> str:
        """
        Generate a comprehensive fundamental analysis report for a stock.

        This tool analyzes financial statements from Yahoo Finance and produces
        a detailed markdown report including income statement highlights,
        balance sheet metrics, cash flow analysis, and key financial ratios.

        Args:
            symbol: Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)
            period: Analysis period (default: 3y). Note: yfinance typically
                    returns up to 4 years of annual data regardless of this setting.

        Returns:
            Markdown-formatted fundamental analysis report
        """
        start_time = time.time()
        logger.info("Starting fundamental analysis for %s (period=%s)", symbol, period)

        # Fetch data
        ticker = yf.Ticker(symbol)
        info = _fetch_company_profile(symbol)

        income = _prepare_statement(_download_statement(ticker, "income"))
        balance = _prepare_statement(_download_statement(ticker, "balance"))
        cash_flow = _prepare_statement(_download_statement(ticker, "cash"))

        logger.debug(
            "Statement shapes for %s -> income: %s, balance: %s, cash_flow: %s",
            symbol, income.shape, balance.shape, cash_flow.shape
        )

        # Extract income statement metrics
        revenue_curr, revenue_prev = _latest_pair(income, "Total Revenue")
        net_income_curr, net_income_prev = _latest_pair(income, "Net Income")
        gross_profit_curr, _ = _latest_pair(income, "Gross Profit")
        operating_income_curr, _ = _latest_pair(income, "Operating Income")
        ebitda_curr, _ = _latest_pair(income, "EBITDA")
        diluted_eps, _ = _latest_pair(income, "Diluted EPS")

        # Extract balance sheet metrics
        assets_curr, _ = _latest_pair(balance, "Total Assets")
        liabilities_curr, _ = _latest_pair(balance, "Total Liabilities")
        equity_curr, _ = _latest_pair(balance, "Total Equity")
        current_assets, _ = _latest_pair(balance, "Total Current Assets")
        current_liabilities, _ = _latest_pair(balance, "Total Current Liabilities")
        cash_curr, _ = _latest_pair(balance, "Cash And Cash Equivalents")
        total_debt, _ = _latest_pair(balance, "Total Debt")
        long_term_debt, _ = _latest_pair(balance, "Long Term Debt")

        # Extract cash flow metrics
        operating_cash, _ = _latest_pair(cash_flow, "Operating Cash Flow")
        investing_cash, _ = _latest_pair(cash_flow, "Investing Cash Flow")
        financing_cash, _ = _latest_pair(cash_flow, "Financing Cash Flow")
        capex, _ = _latest_pair(cash_flow, "Capital Expenditures")
        dividends_paid, _ = _latest_pair(cash_flow, "Dividends Paid")

        # Calculate derived metrics
        free_cash = None
        if operating_cash is not None and capex is not None:
            free_cash = operating_cash - abs(capex)

        revenue_growth = _growth(revenue_curr, revenue_prev)
        net_income_growth = _growth(net_income_curr, net_income_prev)

        # Calculate ratios
        profitability = _calculate_profitability_ratios(income)
        liquidity = _calculate_liquidity_ratios(balance)
        leverage = _calculate_leverage_ratios(balance)
        efficiency = _calculate_efficiency_ratios(income, balance)

        # Generate insights
        insights: List[str] = []

        # Revenue insights
        if revenue_growth is not None:
            insight = _insight("Revenue", revenue_growth)
            if insight:
                insights.append(insight)

        # Net income insights
        if net_income_growth is not None:
            insight = _insight("Net income", net_income_growth)
            if insight:
                insights.append(insight)

        # Profitability insights
        gross_margin = profitability.get("gross_margin")
        if gross_margin is not None:
            if gross_margin > 0.5:
                insights.append("- High gross margin (>50%) indicates strong pricing power or low production costs.")
            elif gross_margin < 0.2:
                insights.append("- Low gross margin (<20%) may indicate competitive pressure or high production costs.")

        net_margin = profitability.get("net_profit_margin")
        if net_margin is not None:
            if net_margin > 0.2:
                insights.append("- Strong net profit margin (>20%) suggests efficient operations.")
            elif net_margin < 0:
                insights.append("- Negative net profit margin indicates the company is currently unprofitable.")

        # Leverage insights
        debt_to_equity = leverage.get("debt_to_equity")
        if debt_to_equity is not None:
            if debt_to_equity < 0.5:
                insights.append("- Low debt-to-equity ratio (<0.5x) indicates conservative leverage.")
            elif debt_to_equity > 2:
                insights.append("- High debt-to-equity ratio (>2x) signals elevated leverage risk.")

        # Liquidity insights
        current_ratio = liquidity.get("current_ratio")
        if current_ratio is not None:
            if current_ratio > 2:
                insights.append("- Strong current ratio (>2x) indicates solid short-term liquidity.")
            elif current_ratio < 1:
                insights.append("- Current ratio below 1x may indicate potential liquidity concerns.")

        # Cash flow insights
        if free_cash is not None:
            if free_cash > 0:
                insights.append("- Positive free cash flow supports dividends, buybacks, or debt reduction.")
            else:
                insights.append("- Negative free cash flow may require external financing for growth.")

        # ROE insights
        roe = efficiency.get("return_on_equity")
        if roe is not None:
            if roe > 0.15:
                insights.append("- Strong return on equity (>15%) indicates efficient use of shareholder capital.")
            elif roe < 0:
                insights.append("- Negative return on equity reflects current losses.")

        # Build report
        company_name = info.get("longName") or symbol.upper()
        sector = info.get("sector") or "N/A"
        industry = info.get("industry") or "N/A"
        summary = info.get("longBusinessSummary") or "Business summary unavailable."
        market_cap = info.get("marketCap")
        trailing_pe = info.get("trailingPE")
        dividend_yield = info.get("dividendYield")
        beta = info.get("beta")

        report_sections = [
            f"# {company_name} ({symbol.upper()}) Fundamental Analysis",
            f"*Sector:* {sector}  |  *Industry:* {industry}  |  *Period:* {period}",
            "",
            "## Company Overview",
            summary[:1000] + "..." if len(summary) > 1000 else summary,
            "",
            "### Market Data",
            f"- **Market Cap:** {_format_currency(market_cap)}",
            f"- **P/E Ratio (TTM):** {_format_ratio(trailing_pe, '') if trailing_pe else 'N/A'}",
            f"- **Dividend Yield:** {_format_percent(dividend_yield) if dividend_yield else 'N/A'}",
            f"- **Beta:** {_format_ratio(beta, '') if beta else 'N/A'}",
            "",
            "---",
            "",
            "## Income Statement Highlights",
            f"- **Total Revenue:** {_format_currency(revenue_curr)}",
            f"- **Revenue YoY Change:** {_format_percent(revenue_growth)}",
            f"- **Gross Profit:** {_format_currency(gross_profit_curr)}",
            f"- **Operating Income:** {_format_currency(operating_income_curr)}",
            f"- **Net Income:** {_format_currency(net_income_curr)}",
            f"- **Net Income YoY Change:** {_format_percent(net_income_growth)}",
            f"- **EBITDA:** {_format_currency(ebitda_curr)}",
            f"- **Diluted EPS:** {_format_ratio(diluted_eps, '') if diluted_eps else 'N/A'}",
            "",
            "### Profitability Ratios",
            f"- **Gross Margin:** {_format_percent(profitability.get('gross_margin'))}",
            f"- **Operating Margin:** {_format_percent(profitability.get('operating_margin'))}",
            f"- **Net Profit Margin:** {_format_percent(profitability.get('net_profit_margin'))}",
            f"- **EBITDA Margin:** {_format_percent(profitability.get('ebitda_margin'))}",
            "",
            "---",
            "",
            "## Balance Sheet Snapshot",
            f"- **Total Assets:** {_format_currency(assets_curr)}",
            f"- **Total Liabilities:** {_format_currency(liabilities_curr)}",
            f"- **Shareholders' Equity:** {_format_currency(equity_curr)}",
            f"- **Cash & Equivalents:** {_format_currency(cash_curr)}",
            f"- **Total Debt:** {_format_currency(total_debt)}",
            f"- **Long-Term Debt:** {_format_currency(long_term_debt)}",
            "",
            "### Liquidity Ratios",
            f"- **Current Ratio:** {_format_ratio(liquidity.get('current_ratio'))}",
            f"- **Quick Ratio:** {_format_ratio(liquidity.get('quick_ratio'))}",
            f"- **Cash Ratio:** {_format_ratio(liquidity.get('cash_ratio'))}",
            "",
            "### Leverage Ratios",
            f"- **Debt-to-Equity:** {_format_ratio(leverage.get('debt_to_equity'))}",
            f"- **Debt-to-Assets:** {_format_ratio(leverage.get('debt_to_assets'))}",
            f"- **Equity Ratio:** {_format_ratio(leverage.get('equity_ratio'))}",
            "",
            "---",
            "",
            "## Cash Flow Overview",
            f"- **Operating Cash Flow:** {_format_currency(operating_cash)}",
            f"- **Investing Cash Flow:** {_format_currency(investing_cash)}",
            f"- **Financing Cash Flow:** {_format_currency(financing_cash)}",
            f"- **Capital Expenditures:** {_format_currency(capex)}",
            f"- **Free Cash Flow:** {_format_currency(free_cash)}",
            f"- **Dividends Paid:** {_format_currency(dividends_paid)}",
            "",
            "### Return Metrics",
            f"- **Return on Assets (ROA):** {_format_percent(efficiency.get('return_on_assets'))}",
            f"- **Return on Equity (ROE):** {_format_percent(efficiency.get('return_on_equity'))}",
            "",
            "---",
            "",
            "## Analytical Insights",
            "\n".join(insights) if insights else "- Insufficient data to derive directional insights.",
            "",
            "---",
            "",
            "## Disclaimer",
            "- This analysis is based on financial statements available through Yahoo Finance.",
            "- Data may not reflect the most recent filings or restated figures.",
            "- Always verify against official SEC filings (10-K, 10-Q) for investment decisions.",
            "- This is not financial advice.",
        ]

        duration = time.time() - start_time
        logger.info("Completed fundamental analysis for %s in %.2fs", symbol, duration)
        return "\n".join(report_sections)


def add_financial_statement_index_tool(mcp) -> None:
    """Register a diagnostic tool to inspect raw yfinance DataFrame indices."""

    @mcp.tool()
    def inspect_financial_statement_indices(symbol: str) -> str:
        """
        Inspect available row names in yfinance financial statements.

        This diagnostic tool helps identify the exact row names returned by
        yfinance for a given ticker, which is useful for troubleshooting
        data extraction issues.

        Args:
            symbol: Stock ticker symbol to inspect (e.g., MSFT, AAPL)

        Returns:
            Markdown-formatted list of available row names for each statement type
        """
        ticker = yf.Ticker(symbol)
        tables = {
            "income": _prepare_statement(_download_statement(ticker, "income")),
            "balance": _prepare_statement(_download_statement(ticker, "balance")),
            "cash": _prepare_statement(_download_statement(ticker, "cash")),
        }

        sections = [f"# Financial Statement Indices for {symbol.upper()}"]
        sections.append("")
        sections.append("This diagnostic output shows the available row names in each financial statement.")
        sections.append("")

        for label, frame in tables.items():
            sections.append(f"## {label.title()} Statement")
            sections.append(f"Shape: {frame.shape}")
            sections.append("")

            if frame.empty:
                sections.append("- No data returned (DataFrame empty)")
            else:
                indices = list(frame.index)
                sections.append("**Available rows:**")
                for idx in indices[:50]:  # Limit to 50 rows
                    normalized = _normalize_key(idx)
                    sections.append(f"- `{idx}` → normalized: `{normalized}`")
                if len(indices) > 50:
                    sections.append(f"- ... and {len(indices) - 50} more rows")

            sections.append("")

        return "\n".join(sections)


def add_financial_ratios_tool(mcp) -> None:
    """Register a tool for calculating specific financial ratios."""

    @mcp.tool()
    def calculate_financial_ratios(symbol: str) -> str:
        """
        Calculate key financial ratios for a stock.

        Provides a focused view of profitability, liquidity, leverage,
        and efficiency ratios without the full fundamental analysis context.

        Args:
            symbol: Stock ticker symbol (e.g., AAPL, MSFT)

        Returns:
            Markdown-formatted financial ratios summary
        """
        ticker = yf.Ticker(symbol)
        income = _prepare_statement(_download_statement(ticker, "income"))
        balance = _prepare_statement(_download_statement(ticker, "balance"))

        profitability = _calculate_profitability_ratios(income)
        liquidity = _calculate_liquidity_ratios(balance)
        leverage = _calculate_leverage_ratios(balance)
        efficiency = _calculate_efficiency_ratios(income, balance)

        sections = [
            f"# Financial Ratios for {symbol.upper()}",
            "",
            "## Profitability Ratios",
            f"- Gross Margin: {_format_percent(profitability.get('gross_margin'))}",
            f"- Operating Margin: {_format_percent(profitability.get('operating_margin'))}",
            f"- Net Profit Margin: {_format_percent(profitability.get('net_profit_margin'))}",
            f"- EBITDA Margin: {_format_percent(profitability.get('ebitda_margin'))}",
            "",
            "## Liquidity Ratios",
            f"- Current Ratio: {_format_ratio(liquidity.get('current_ratio'))}",
            f"- Quick Ratio: {_format_ratio(liquidity.get('quick_ratio'))}",
            f"- Cash Ratio: {_format_ratio(liquidity.get('cash_ratio'))}",
            "",
            "## Leverage Ratios",
            f"- Debt-to-Equity: {_format_ratio(leverage.get('debt_to_equity'))}",
            f"- Debt-to-Assets: {_format_ratio(leverage.get('debt_to_assets'))}",
            f"- Equity Ratio: {_format_ratio(leverage.get('equity_ratio'))}",
            "",
            "## Efficiency Ratios",
            f"- Return on Assets (ROA): {_format_percent(efficiency.get('return_on_assets'))}",
            f"- Return on Equity (ROE): {_format_percent(efficiency.get('return_on_equity'))}",
        ]

        return "\n".join(sections)