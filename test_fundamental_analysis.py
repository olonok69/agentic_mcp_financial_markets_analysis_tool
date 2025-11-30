#!/usr/bin/env python
"""Test script for fundamental analysis module.

This script tests the fundamental analysis functionality to ensure
yfinance data extraction and report generation work correctly.
"""
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Import the module
from server.strategies.fundamental_analysis import (
    _fetch_company_profile,
    _download_statement,
    _prepare_statement,
    _latest_pair,
    _format_currency,
    _format_percent,
    _calculate_profitability_ratios,
    _calculate_liquidity_ratios,
    _calculate_leverage_ratios,
    ROW_ALIASES,
)
import yfinance as yf


def test_ticker(symbol: str = "AAPL"):
    """Test fundamental analysis for a given ticker."""
    print(f"\n{'='*60}")
    print(f"Testing Fundamental Analysis for {symbol}")
    print(f"{'='*60}")
    
    # Test company profile
    print("\n--- Company Profile ---")
    profile = _fetch_company_profile(symbol)
    print(f"Company Name: {profile.get('longName', 'N/A')}")
    print(f"Sector: {profile.get('sector', 'N/A')}")
    print(f"Industry: {profile.get('industry', 'N/A')}")
    print(f"Market Cap: {_format_currency(profile.get('marketCap'))}")
    
    # Test financial statements
    ticker = yf.Ticker(symbol)
    
    print("\n--- Income Statement ---")
    income = _prepare_statement(_download_statement(ticker, "income"))
    print(f"Shape: {income.shape}")
    if not income.empty:
        print(f"Columns (dates): {list(income.columns)[:4]}")
        print(f"Sample rows: {list(income.index)[:10]}")
        
        revenue, revenue_prev = _latest_pair(income, "Total Revenue")
        net_income, ni_prev = _latest_pair(income, "Net Income")
        ebitda, _ = _latest_pair(income, "EBITDA")
        
        print(f"\nTotal Revenue: {_format_currency(revenue)}")
        print(f"Net Income: {_format_currency(net_income)}")
        print(f"EBITDA: {_format_currency(ebitda)}")
    else:
        print("WARNING: Income statement is empty!")
    
    print("\n--- Balance Sheet ---")
    balance = _prepare_statement(_download_statement(ticker, "balance"))
    print(f"Shape: {balance.shape}")
    if not balance.empty:
        print(f"Columns (dates): {list(balance.columns)[:4]}")
        print(f"Sample rows: {list(balance.index)[:10]}")
        
        assets, _ = _latest_pair(balance, "Total Assets")
        liabilities, _ = _latest_pair(balance, "Total Liabilities")
        equity, _ = _latest_pair(balance, "Total Equity")
        
        print(f"\nTotal Assets: {_format_currency(assets)}")
        print(f"Total Liabilities: {_format_currency(liabilities)}")
        print(f"Total Equity: {_format_currency(equity)}")
    else:
        print("WARNING: Balance sheet is empty!")
    
    print("\n--- Cash Flow Statement ---")
    cash_flow = _prepare_statement(_download_statement(ticker, "cash"))
    print(f"Shape: {cash_flow.shape}")
    if not cash_flow.empty:
        print(f"Columns (dates): {list(cash_flow.columns)[:4]}")
        print(f"Sample rows: {list(cash_flow.index)[:10]}")
        
        operating, _ = _latest_pair(cash_flow, "Operating Cash Flow")
        capex, _ = _latest_pair(cash_flow, "Capital Expenditures")
        
        print(f"\nOperating Cash Flow: {_format_currency(operating)}")
        print(f"Capital Expenditures: {_format_currency(capex)}")
        
        if operating and capex:
            fcf = operating - abs(capex)
            print(f"Free Cash Flow: {_format_currency(fcf)}")
    else:
        print("WARNING: Cash flow statement is empty!")
    
    print("\n--- Financial Ratios ---")
    profitability = _calculate_profitability_ratios(income)
    liquidity = _calculate_liquidity_ratios(balance)
    leverage = _calculate_leverage_ratios(balance)
    
    print(f"Gross Margin: {_format_percent(profitability.get('gross_margin'))}")
    print(f"Net Profit Margin: {_format_percent(profitability.get('net_profit_margin'))}")
    print(f"Current Ratio: {liquidity.get('current_ratio'):.2f}x" if liquidity.get('current_ratio') else "Current Ratio: N/A")
    print(f"Debt-to-Equity: {leverage.get('debt_to_equity'):.2f}x" if leverage.get('debt_to_equity') else "Debt-to-Equity: N/A")
    
    return income, balance, cash_flow


def main():
    """Run tests for multiple tickers."""
    tickers = ["AAPL", "MSFT", "GOOGL"]
    
    print("="*60)
    print("Fundamental Analysis Module Test Suite")
    print("="*60)
    
    for symbol in tickers:
        try:
            test_ticker(symbol)
            print(f"\n✓ {symbol} test completed successfully")
        except Exception as e:
            print(f"\n✗ {symbol} test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("Test suite completed")
    print("="*60)


if __name__ == "__main__":
    main()