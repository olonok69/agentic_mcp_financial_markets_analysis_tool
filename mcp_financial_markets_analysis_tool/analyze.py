#!/usr/bin/env python3
"""
Simple CLI wrapper for the Stock Technical Analysis Tool

This script provides a simple command-line interface for running
stock technical analysis with predefined parameters.
"""

import sys
import asyncio
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from stock_analyzer import main
except ImportError as e:
    print(f"Error importing stock_analyzer: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


def run_analysis():
    """Simple CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python analyze.py <STOCK_SYMBOL>")
        print("Example: python analyze.py AAPL")
        sys.exit(1)
    
    # Add the symbol as an argument
    symbol = sys.argv[1].upper()
    sys.argv = [sys.argv[0], symbol]
    
    # Run the main analysis
    return asyncio.run(main())


if __name__ == "__main__":
    sys.exit(run_analysis())
