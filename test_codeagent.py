"""
Test script to compare ToolCallingAgent vs CodeAgent performance.

Run this script to see the differences in behavior and efficiency.

Usage:
    python test_codeagent.py AAPL
    python test_codeagent.py AAPL --mode scanner --symbols "AAPL,MSFT,GOOGL"
"""
from __future__ import annotations

import argparse
import time
import os
from pathlib import Path

# Add project root to path
import sys
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()


def test_technical_analysis(symbol: str, period: str = "1y"):
    """Compare technical analysis between both agent types."""
    
    from stock_analyzer_bot.tools import configure_finance_tools, shutdown_finance_tools
    
    print("=" * 70)
    print(f"TECHNICAL ANALYSIS COMPARISON: {symbol}")
    print("=" * 70)
    
    configure_finance_tools()
    
    try:
        # Test ToolCallingAgent (original)
        print("\n" + "-" * 35)
        print("1️⃣  ToolCallingAgent (Original)")
        print("-" * 35)
        
        from stock_analyzer_bot.main import run_technical_analysis as run_tool_calling
        
        start = time.time()
        result_tool = run_tool_calling(
            symbol=symbol,
            period=period,
            max_steps=25,
        )
        time_tool = time.time() - start
        
        print(f"✅ Completed in {time_tool:.1f}s")
        print(f"📝 Report length: {len(result_tool)} characters")
        
        # Test CodeAgent (new)
        print("\n" + "-" * 35)
        print("2️⃣  CodeAgent (New)")
        print("-" * 35)
        
        from stock_analyzer_bot.main_codeagent import run_technical_analysis as run_code_agent
        
        start = time.time()
        result_code = run_code_agent(
            symbol=symbol,
            period=period,
            max_steps=20,
            executor_type="local",
        )
        time_code = time.time() - start
        
        print(f"✅ Completed in {time_code:.1f}s")
        print(f"📝 Report length: {len(result_code)} characters")
        
        # Summary
        print("\n" + "=" * 70)
        print("COMPARISON SUMMARY")
        print("=" * 70)
        print(f"{'Metric':<25} {'ToolCallingAgent':<20} {'CodeAgent':<20}")
        print("-" * 65)
        print(f"{'Execution Time':<25} {time_tool:.1f}s{'':<15} {time_code:.1f}s")
        print(f"{'Report Length':<25} {len(result_tool):,} chars{'':<10} {len(result_code):,} chars")
        print(f"{'Time Difference':<25} {'':<20} {((time_code - time_tool) / time_tool * 100):+.1f}%")
        print()
        
        # Save reports for comparison
        output_dir = Path("test_outputs")
        output_dir.mkdir(exist_ok=True)
        
        (output_dir / f"{symbol}_toolcalling.md").write_text(result_tool, encoding="utf-8")
        (output_dir / f"{symbol}_codeagent.md").write_text(result_code, encoding="utf-8")
        
        print(f"📁 Reports saved to {output_dir}/")
        print(f"   - {symbol}_toolcalling.md")
        print(f"   - {symbol}_codeagent.md")
        
    finally:
        shutdown_finance_tools()


def test_market_scanner(symbols: str, period: str = "1y"):
    """Compare market scanner between both agent types."""
    
    from stock_analyzer_bot.tools import configure_finance_tools, shutdown_finance_tools
    
    symbol_list = [s.strip() for s in symbols.split(",")]
    
    print("=" * 70)
    print(f"MARKET SCANNER COMPARISON: {len(symbol_list)} stocks")
    print(f"Symbols: {symbols}")
    print("=" * 70)
    
    configure_finance_tools()
    
    try:
        # Test ToolCallingAgent
        print("\n" + "-" * 35)
        print("1️⃣  ToolCallingAgent (Original)")
        print("-" * 35)
        print("⏳ This may take a while with multiple stocks...")
        
        from stock_analyzer_bot.main import run_market_scanner as run_scanner_tool
        
        start = time.time()
        result_tool = run_scanner_tool(
            symbols=symbols,
            period=period,
            max_steps=len(symbol_list) * 4 + 20,
        )
        time_tool = time.time() - start
        
        print(f"✅ Completed in {time_tool:.1f}s")
        print(f"📝 Report length: {len(result_tool)} characters")
        
        # Test CodeAgent
        print("\n" + "-" * 35)
        print("2️⃣  CodeAgent (New)")
        print("-" * 35)
        print("⏳ CodeAgent should be faster with loops...")
        
        from stock_analyzer_bot.main_codeagent import run_market_scanner as run_scanner_code
        
        start = time.time()
        result_code = run_scanner_code(
            symbols=symbols,
            period=period,
            max_steps=len(symbol_list) * 2 + 15,
            executor_type="local",
        )
        time_code = time.time() - start
        
        print(f"✅ Completed in {time_code:.1f}s")
        print(f"📝 Report length: {len(result_code)} characters")
        
        # Summary
        print("\n" + "=" * 70)
        print("COMPARISON SUMMARY")
        print("=" * 70)
        print(f"{'Metric':<25} {'ToolCallingAgent':<20} {'CodeAgent':<20}")
        print("-" * 65)
        print(f"{'Execution Time':<25} {time_tool:.1f}s{'':<15} {time_code:.1f}s")
        print(f"{'Report Length':<25} {len(result_tool):,} chars{'':<10} {len(result_code):,} chars")
        print(f"{'Stocks Analyzed':<25} {len(symbol_list):<20} {len(symbol_list):<20}")
        print(f"{'Time per Stock':<25} {time_tool/len(symbol_list):.1f}s{'':<15} {time_code/len(symbol_list):.1f}s")
        print(f"{'Time Difference':<25} {'':<20} {((time_code - time_tool) / time_tool * 100):+.1f}%")
        print()
        
        # Save reports
        output_dir = Path("test_outputs")
        output_dir.mkdir(exist_ok=True)
        
        (output_dir / "scanner_toolcalling.md").write_text(result_tool, encoding="utf-8")
        (output_dir / "scanner_codeagent.md").write_text(result_code, encoding="utf-8")
        
        print(f"📁 Reports saved to {output_dir}/")
        
    finally:
        shutdown_finance_tools()


def test_codeagent_only(symbol: str, mode: str = "technical", period: str = "1y"):
    """Test CodeAgent only (for quick testing)."""
    
    from stock_analyzer_bot.tools import configure_finance_tools, shutdown_finance_tools
    
    print("=" * 70)
    print(f"CODEAGENT TEST: {mode.upper()} - {symbol}")
    print("=" * 70)
    
    configure_finance_tools()
    
    try:
        from stock_analyzer_bot.main_codeagent import (
            run_technical_analysis,
            run_fundamental_analysis,
            run_combined_analysis,
        )
        
        start = time.time()
        
        if mode == "technical":
            result = run_technical_analysis(symbol=symbol, period=period)
        elif mode == "fundamental":
            result = run_fundamental_analysis(symbol=symbol, period=period)
        elif mode == "combined":
            result = run_combined_analysis(symbol=symbol)
        else:
            print(f"Unknown mode: {mode}")
            return
        
        elapsed = time.time() - start
        
        print(f"\n✅ Completed in {elapsed:.1f}s")
        print(f"📝 Report length: {len(result)} characters")
        print("\n" + "=" * 70)
        print("REPORT OUTPUT")
        print("=" * 70)
        print(result)
        
        # Save report
        output_dir = Path("test_outputs")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"{symbol}_{mode}_codeagent.md"
        output_file.write_text(result, encoding="utf-8")
        print(f"\n📁 Report saved to {output_file}")
        
    finally:
        shutdown_finance_tools()


def main():
    parser = argparse.ArgumentParser(
        description="Test CodeAgent vs ToolCallingAgent performance"
    )
    parser.add_argument("symbol", help="Stock symbol to analyze")
    parser.add_argument(
        "--mode",
        choices=["compare", "scanner", "codeagent-only"],
        default="compare",
        help="Test mode: compare (default), scanner, or codeagent-only",
    )
    parser.add_argument(
        "--analysis",
        choices=["technical", "fundamental", "combined"],
        default="technical",
        help="Analysis type for codeagent-only mode",
    )
    parser.add_argument(
        "--symbols",
        default="AAPL,MSFT,GOOGL",
        help="Comma-separated symbols for scanner mode",
    )
    parser.add_argument("--period", default="1y", help="Analysis period")
    
    args = parser.parse_args()
    
    print("\n🧪 CodeAgent vs ToolCallingAgent Test\n")
    
    if args.mode == "compare":
        test_technical_analysis(args.symbol, args.period)
    elif args.mode == "scanner":
        test_market_scanner(args.symbols, args.period)
    elif args.mode == "codeagent-only":
        test_codeagent_only(args.symbol, args.analysis, args.period)


if __name__ == "__main__":
    main()