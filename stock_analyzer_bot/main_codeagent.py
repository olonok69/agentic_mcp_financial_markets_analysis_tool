"""Stock Analyzer Bot - CodeAgent Implementation.

This module uses CodeAgent with LOW-LEVEL tools that the LLM orchestrates
using Python code. The LLM can write loops, store variables, and compose
complex analysis workflows.

LOW-LEVEL TOOLS USED:
- bollinger_fibonacci_analysis: Single strategy, single stock
- macd_donchian_analysis: Single strategy, single stock
- connors_zscore_analysis: Single strategy, single stock
- dual_moving_average_analysis: Single strategy, single stock
- fundamental_analysis_report: Financial statements (also for combined analysis)

RECOMMENDATION DOCUMENTATION GUIDELINES:
All analysis outputs must be well-documented with:
1. Numbered sections with clear headers (no italic formatting)
2. Use USD instead of $ for currency values (avoids formatting errors)
3. Intermediary tool data must support final recommendations
4. Clear traceability from data to conclusion
"""
from __future__ import annotations

import argparse
import json
import os
import re
from typing import Any, Dict, Literal, Optional, Union

from smolagents import CodeAgent, InferenceClientModel, LiteLLMModel

from .mcp_client import configure_session, shutdown_session
from .tools import (
    LOW_LEVEL_TOOLS,
    bollinger_fibonacci_analysis,
    configure_finance_tools,
    connors_zscore_analysis,
    dual_moving_average_analysis,
    fundamental_analysis_report,
    macd_donchian_analysis,
    shutdown_finance_tools,
)

__all__ = [
    "run_technical_analysis",
    "run_market_scanner",
    "run_fundamental_analysis",
    "run_multi_sector_analysis",
    "run_combined_analysis",
    "DEFAULT_EXECUTOR",
    "DEFAULT_MAX_TOKENS",
]

# ===========================================================================
# Configuration
# ===========================================================================

DEFAULT_MODEL_ID = os.getenv("SMOLAGENT_MODEL_ID", "gpt-4o")
DEFAULT_MODEL_PROVIDER = os.getenv("SMOLAGENT_MODEL_PROVIDER", "litellm")
DEFAULT_MAX_STEPS = int(os.getenv("SMOLAGENT_MAX_STEPS", "20"))
DEFAULT_EXECUTOR = os.getenv("SMOLAGENT_EXECUTOR", "local")
DEFAULT_TEMPERATURE = float(os.getenv("SMOLAGENT_TEMPERATURE", "0.1"))
DEFAULT_MAX_TOKENS = int(os.getenv("SMOLAGENT_MAX_TOKENS", "8192"))


# ===========================================================================
# Agent Result Formatting Helper
# ===========================================================================

def format_agent_result(result: Any) -> str:
    """
    Format the result from agent.run() into a clean string.
    
    The smolagents agent.run() can return different formats:
    - A string directly
    - A dict with an "answer" key
    - A dict serialized as a string
    - Content with literal '\\n' that need to be converted to newlines
    - String starting with {"answer": prefix
    
    This function normalizes all these cases into a properly formatted string.
    
    Args:
        result: The raw result from agent.run()
        
    Returns:
        A clean, formatted string with proper newlines
    """
    if result is None:
        return "No report generated"
    
    # Convert to string first for unified processing
    if isinstance(result, dict):
        # Check for common keys that contain the actual answer
        for key in ["answer", "output", "result", "report", "content"]:
            if key in result:
                text = str(result[key])
                break
        else:
            try:
                text = json.dumps(result, indent=2)
            except (TypeError, ValueError):
                text = str(result)
    else:
        text = str(result)
    
    # Handle JSON string wrapper - check multiple patterns
    # Pattern 1: {"answer":"content"} or {"answer": "content"}
    # Pattern 2: String starting with {"answer":
    
    # Try to extract content from JSON wrapper
    json_patterns = [
        r'^\s*\{\s*"answer"\s*:\s*"(.*)"\s*\}\s*$',  # Full JSON object
        r'^\s*\{\s*"answer"\s*:\s*"(.*)',  # Partial JSON (truncated end)
        r'^\s*\{"answer":"(.*)',  # Compact JSON start
    ]
    
    for pattern in json_patterns:
        match = re.match(pattern, text, re.DOTALL)
        if match:
            text = match.group(1)
            # Remove trailing "} if present from truncated JSON
            if text.endswith('"}'):
                text = text[:-2]
            elif text.endswith('"'):
                text = text[:-1]
            break
    
    # Also try standard JSON parsing
    if text.strip().startswith('{'):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                for key in ["answer", "output", "result", "report", "content"]:
                    if key in parsed:
                        text = str(parsed[key])
                        break
        except (json.JSONDecodeError, TypeError):
            pass  # Keep text as-is if JSON parsing fails
    
    # Ensure text is a string
    text = str(text) if not isinstance(text, str) else text
    
    # Replace literal escape sequences with actual characters
    text = text.replace('\\n', '\n')
    text = text.replace('\\t', '\t')
    text = text.replace('\\r', '\r')
    
    # Clean up any excessive newlines (more than 3 consecutive)
    while '\n\n\n\n' in text:
        text = text.replace('\n\n\n\n', '\n\n\n')
    
    return text.strip()


def build_model(
    model_id: str,
    provider: str,
    api_key: Optional[str] = None,
    hf_token: Optional[str] = None,
    api_base: Optional[str] = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
):
    """Create an LLM model instance for CodeAgent."""
    if provider == "litellm":
        kwargs = {
            "model_id": model_id,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if api_key:
            kwargs["api_key"] = api_key
        if api_base:
            kwargs["api_base"] = api_base
        return LiteLLMModel(**kwargs)
    else:
        token = hf_token or os.getenv("HF_TOKEN")
        return InferenceClientModel(
            model_id=model_id,
            token=token,
            temperature=temperature,
            max_tokens=max_tokens,
        )


def build_agent(
    model,
    tools: list,
    max_steps: int = DEFAULT_MAX_STEPS,
    executor_type: Literal["local", "e2b", "docker"] = "local",
):
    """Create a CodeAgent with LOW-LEVEL tools for Python orchestration."""
    additional_imports = [
        "statistics",
        "math",
        "collections",
        "re",
        "datetime",
        "json",
    ]
    
    agent_kwargs = {
        "tools": tools,
        "model": model,
        "max_steps": max_steps,
        "verbosity_level": 1,
        "additional_authorized_imports": additional_imports,
    }
    
    if executor_type in ("e2b", "docker"):
        agent_kwargs["executor_type"] = executor_type
    
    return CodeAgent(**agent_kwargs)


# ===========================================================================
# Prompts for LOW-LEVEL Tool Orchestration with Python Code
# ===========================================================================

TECHNICAL_ANALYSIS_PROMPT = """Analyze {symbol} using all 4 technical strategies.

TOOLS TO CALL:
1. bollinger_fibonacci_analysis(symbol="{symbol}", period="{period}")
2. macd_donchian_analysis(symbol="{symbol}", period="{period}")
3. connors_zscore_analysis(symbol="{symbol}", period="{period}")
4. dual_moving_average_analysis(symbol="{symbol}", period="{period}")

Write Python code to call all tools, extract metrics, and build a CONCISE report.

```python
import re

# Call all 4 strategy tools
bb_result = bollinger_fibonacci_analysis(symbol="{symbol}", period="{period}")
macd_result = macd_donchian_analysis(symbol="{symbol}", period="{period}")
connors_result = connors_zscore_analysis(symbol="{symbol}", period="{period}")
dual_ma_result = dual_moving_average_analysis(symbol="{symbol}", period="{period}")

# Helper to extract signal
def get_signal(result):
    text = result.upper()
    if "CURRENT SIGNAL: BUY" in text or "SIGNAL: BUY" in text:
        return "BUY"
    elif "CURRENT SIGNAL: SELL" in text or "SIGNAL: SELL" in text:
        return "SELL"
    elif "CURRENT SIGNAL: HOLD" in text or "SIGNAL: HOLD" in text:
        return "HOLD"
    elif "BUY" in text and "SELL" not in text:
        return "BUY"
    elif "SELL" in text:
        return "SELL"
    return "HOLD"

# Helper to extract numeric value
def extract_value(text, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return "N/A"

# Extract metrics from each result
def get_metrics(result):
    ret = extract_value(result, [r"Strategy Total Return[:\\s]+([\\-]?[\\d.]+)%", r"Strategy Return[:\\s]+([\\-]?[\\d.]+)%"])
    sharpe = extract_value(result, [r"Strategy Sharpe Ratio[:\\s]+([\\-]?[\\d.]+)", r"Sharpe Ratio[:\\s]+([\\-]?[\\d.]+)"])
    dd = extract_value(result, [r"Strategy Max Drawdown[:\\s]+([\\-]?[\\d.]+)%", r"Max Drawdown[:\\s]+([\\-]?[\\d.]+)%"])
    score = extract_value(result, [r"Combined Score[:\\s]+([\\-]?[\\d.]+)", r"Current BB Score[:\\s]+([\\-]?[\\d.]+)", r"Trend Strength[:\\s]+([\\-]?[\\d.]+)%"])
    return ret, sharpe, dd, score

bb_signal = get_signal(bb_result)
macd_signal = get_signal(macd_result)
connors_signal = get_signal(connors_result)
dual_ma_signal = get_signal(dual_ma_result)

bb_ret, bb_sharpe, bb_dd, bb_score = get_metrics(bb_result)
macd_ret, macd_sharpe, macd_dd, macd_score = get_metrics(macd_result)
conn_ret, conn_sharpe, conn_dd, conn_score = get_metrics(connors_result)
dual_ret, dual_sharpe, dual_dd, dual_score = get_metrics(dual_ma_result)

# Count signals
signals = [bb_signal, macd_signal, connors_signal, dual_ma_signal]
buy_count = sum(1 for s in signals if "BUY" in s)
sell_count = sum(1 for s in signals if "SELL" in s)
hold_count = 4 - buy_count - sell_count

# Determine outlook
if buy_count >= 3:
    overall = "STRONG BUY"
    outlook = "BULLISH"
elif buy_count >= 2:
    overall = "BUY"
    outlook = "MODERATELY BULLISH"
elif sell_count >= 3:
    overall = "STRONG SELL"
    outlook = "BEARISH"
elif sell_count >= 2:
    overall = "SELL"
    outlook = "MODERATELY BEARISH"
else:
    overall = "HOLD"
    outlook = "NEUTRAL"

trend = "Up" if buy_count > sell_count else "Down" if sell_count > buy_count else "Sideways"
risk = "Low" if buy_count >= 3 or sell_count >= 3 else "Medium" if buy_count >= 2 or sell_count >= 2 else "High"

# Build CONCISE report
report = f'''# {symbol} Technical Analysis Report

## Executive Summary
{{outlook}} outlook: {{buy_count}} BUY, {{sell_count}} SELL, {{hold_count}} HOLD signals.

**Period:** {period}

## Technical Indicators Summary

| Strategy | Score | Signal | Key Finding |
|----------|-------|--------|-------------|
| Bollinger-Fibonacci | {{bb_score}} | {{bb_signal}} | Return {{bb_ret}}%, Sharpe {{bb_sharpe}} |
| MACD-Donchian | {{macd_score}} | {{macd_signal}} | Return {{macd_ret}}%, Sharpe {{macd_sharpe}} |
| Connors RSI+Z | {{conn_score}} | {{connors_signal}} | Return {{conn_ret}}%, Sharpe {{conn_sharpe}} |
| Dual MA | {{dual_score}} | {{dual_ma_signal}} | Return {{dual_ret}}%, Sharpe {{dual_sharpe}} |

## Strategy Details

**1. Bollinger-Fibonacci:** {{bb_signal}} - Return: {{bb_ret}}%, Sharpe: {{bb_sharpe}}, Drawdown: {{bb_dd}}%

**2. MACD-Donchian:** {{macd_signal}} - Return: {{macd_ret}}%, Sharpe: {{macd_sharpe}}, Drawdown: {{macd_dd}}%

**3. Connors RSI+Z:** {{connors_signal}} - Return: {{conn_ret}}%, Sharpe: {{conn_sharpe}}, Drawdown: {{conn_dd}}%

**4. Dual MA:** {{dual_ma_signal}} - Return: {{dual_ret}}%, Sharpe: {{dual_sharpe}}, Drawdown: {{dual_dd}}%

## Consensus

- BUY: {{buy_count}}/4 | SELL: {{sell_count}}/4 | HOLD: {{hold_count}}/4
- Trend: {{trend}} | Risk: {{risk}}

## 🎯 Recommendation: **{{overall}}**

'''

if "BUY" in overall:
    report += "**Holders:** ✅ Hold/add | ❌ Avoid selling\\n\\n"
    report += "**Buyers:** BUY - Watch: 📊 Volume confirmation\\n\\n"
elif "SELL" in overall:
    report += "**Holders:** ✅ Reduce position | ❌ Avoid adding\\n\\n"
    report += "**Buyers:** WAIT - Watch: 📊 Reversal signals\\n\\n"
else:
    report += "**Holders:** ✅ Hold | ❌ Avoid large positions\\n\\n"
    report += "**Buyers:** WAIT - Watch: 📊 Clearer signals\\n\\n"

report += "**Risk:** Position max 5% portfolio\\n\\n"
report += "*Disclaimer: Educational purposes only.*\\n"

final_answer(report)
```

REQUIREMENTS:
1. Extract REAL metrics from tool results (returns, sharpe, drawdown)
2. Keep report CONCISE - no raw data dumps
3. Use markdown table for summary
4. Use emojis (✅, ❌, 📊, 🎯)
5. Use USD for currency (no dollar signs)
"""

MARKET_SCANNER_PROMPT = """Scan and compare these stocks: {symbols}

TOOLS TO CALL (for each stock):
1. bollinger_fibonacci_analysis(symbol, period)
2. macd_donchian_analysis(symbol, period)
3. connors_zscore_analysis(symbol, period)
4. dual_moving_average_analysis(symbol, period)

Write Python code to analyze all stocks and create a professional ranking report.

```python
import json
import re

stocks = {symbol_list}
period = "{period}"

def get_signal(result):
    text = result.upper()
    if "STRONG BUY" in text:
        return "STRONG BUY"
    elif "STRONG SELL" in text:
        return "STRONG SELL"
    elif "BUY" in text:
        return "BUY"
    elif "SELL" in text:
        return "SELL"
    return "HOLD"

def count_buy_signals(results):
    count = 0
    for result in results.values():
        signal = get_signal(result)
        if "BUY" in signal:
            count += 1
    return count

# Collect all results
all_data = {{}}
for stock in stocks:
    all_data[stock] = {{
        "bb": bollinger_fibonacci_analysis(symbol=stock, period=period),
        "macd": macd_donchian_analysis(symbol=stock, period=period),
        "connors": connors_zscore_analysis(symbol=stock, period=period),
        "dual_ma": dual_moving_average_analysis(symbol=stock, period=period),
    }}

# Parse results
stock_summaries = {{}}
for stock, results in all_data.items():
    buy_count = count_buy_signals(results)
    stock_summaries[stock] = {{
        "buy_count": buy_count,
        "bb_signal": get_signal(results["bb"]),
        "macd_signal": get_signal(results["macd"]),
        "connors_signal": get_signal(results["connors"]),
        "dual_ma_signal": get_signal(results["dual_ma"]),
    }}

# Rank stocks
ranked = sorted(stock_summaries.items(), key=lambda x: x[1]["buy_count"], reverse=True)

# Get recommendations
def get_recommendation(buy_count):
    if buy_count >= 3:
        return "STRONG BUY"
    elif buy_count >= 2:
        return "BUY"
    elif buy_count >= 1:
        return "HOLD"
    return "AVOID"

def get_outlook(buy_count):
    if buy_count >= 3:
        return "BULLISH"
    elif buy_count >= 2:
        return "MODERATELY BULLISH"
    elif buy_count >= 1:
        return "NEUTRAL"
    return "BEARISH"

# Build report
report = "# Market Scanner Report\\n\\n"
report += "## Executive Summary\\n\\n"
report += f"Scanned {{len(stocks)}} stocks using four technical strategies.\\n\\n"
report += f"**Stocks Analyzed:** {{', '.join(stocks)}}\\n\\n"
report += f"**Analysis Period:** {{period}}\\n\\n"
report += "---\\n\\n"

report += "## Stock Rankings Summary Table\\n\\n"
report += "| Rank | Symbol | BUY Signals | Overall Signal | Recommendation |\\n"
report += "|------|--------|-------------|----------------|----------------|\\n"
for i, (stock, data) in enumerate(ranked, 1):
    rec = get_recommendation(data["buy_count"])
    outlook = get_outlook(data["buy_count"])
    report += f"| {{i}} | **{{stock}}** | {{data['buy_count']}}/4 | {{outlook}} | {{rec}} |\\n"
report += "\\n---\\n\\n"

report += "## Detailed Stock Analysis\\n\\n"
medals = ["🥇", "🥈", "🥉"]
for i, (stock, data) in enumerate(ranked, 1):
    medal = medals[i-1] if i <= 3 else ""
    report += f"### {{medal}} Rank {{i}}: {{stock}}\\n\\n"
    report += "**Signal Breakdown:**\\n\\n"
    report += "| Strategy | Signal |\\n"
    report += "|----------|--------|\\n"
    report += f"| Bollinger-Fibonacci | {{data['bb_signal']}} |\\n"
    report += f"| MACD-Donchian | {{data['macd_signal']}} |\\n"
    report += f"| Connors RSI-ZScore | {{data['connors_signal']}} |\\n"
    report += f"| Dual Moving Average | {{data['dual_ma_signal']}} |\\n\\n"
    report += f"**Verdict:** {{data['buy_count']}}/4 BUY signals - {{get_recommendation(data['buy_count'])}}\\n\\n"
    report += "---\\n\\n"

# Top picks and avoid
top_picks = [(s, d) for s, d in ranked if d["buy_count"] >= 3]
to_avoid = [(s, d) for s, d in ranked if d["buy_count"] == 0]

report += "## 🎯 TOP PICKS\\n\\n"
report += "### Best Opportunities (3+ BUY signals):\\n\\n"
if top_picks:
    for i, (stock, data) in enumerate(top_picks, 1):
        report += f"{{i}}. **{{stock}}** - {{data['buy_count']}}/4 BUY signals\\n\\n"
else:
    report += "No stocks with 3+ BUY signals in this scan.\\n\\n"

report += "### Stocks to Avoid (0 BUY signals):\\n\\n"
if to_avoid:
    for i, (stock, data) in enumerate(to_avoid, 1):
        report += f"{{i}}. **{{stock}}** - 0/4 BUY signals\\n\\n"
else:
    report += "No stocks with 0 BUY signals in this scan.\\n\\n"

report += "---\\n\\n"
report += "## Market Sentiment\\n\\n"
total_buy = sum(d["buy_count"] for d in stock_summaries.values())
avg_buy = total_buy / len(stocks)
sentiment = "BULLISH" if avg_buy >= 2 else "NEUTRAL" if avg_buy >= 1 else "BEARISH"
report += f"- **Average BUY Signals:** {{avg_buy:.1f}}/4 across all stocks\\n\\n"
report += f"- **Market Outlook:** {{sentiment}}\\n\\n"
report += "\\n**Disclaimer:** This analysis is for educational purposes only.\\n\\n"

final_answer(report)
```

REQUIREMENTS:
1. Extract REAL data from each tool result
2. Use markdown tables for rankings
3. Include medals (🥇, 🥈, 🥉) for top 3
4. Show top picks and stocks to avoid
"""

FUNDAMENTAL_ANALYSIS_PROMPT = """Analyze {symbol} fundamentals.

TOOL TO CALL:
fundamental_analysis_report(symbol="{symbol}", period="{period}")

```python
import re

fund_data = fundamental_analysis_report(symbol="{symbol}", period="{period}")

# Determine assessment
if "STRONG" in fund_data.upper() and "BUY" in fund_data.upper():
    assessment = "STRONG BUY"
    health = "STRONG"
    grade = "A"
elif "BUY" in fund_data.upper():
    assessment = "BUY"
    health = "GOOD"
    grade = "B"
elif "SELL" in fund_data.upper():
    assessment = "SELL"
    health = "WEAK"
    grade = "D"
else:
    assessment = "HOLD"
    health = "MODERATE"
    grade = "C"

report = "# {symbol} Fundamental Analysis Report\\n\\n"
report += "## Executive Summary\\n\\n"
report += "**Company:** {symbol}\\n\\n"
report += "**Analysis Period:** {period}\\n\\n"
report += f"**Financial Health:** {{health}}\\n\\n"
report += f"**Investment Grade:** {{grade}}\\n\\n"
report += "---\\n\\n"

report += "## Financial Data\\n\\n"
report += f"{{fund_data}}\\n\\n"
report += "---\\n\\n"

report += f"## 🎯 RECOMMENDATION: **{{assessment}}**\\n\\n"
report += f"**Rationale:** Based on the fundamental analysis, {symbol} shows {{health.lower()}} financial health with an investment grade of {{grade}}.\\n\\n"
report += "**Disclaimer:** This analysis is for educational purposes only.\\n\\n"

final_answer(report)
```
"""

MULTI_SECTOR_PROMPT = """Analyze multiple sectors using individual strategy tools.

{sector_details}

Period: {period}

```python
from datetime import datetime

sectors = {sectors_dict}
period = "{period}"

def extract_current_signal(tool_output):
    \"\"\"
    Extract the CURRENT signal from tool output using simple string matching.
    The tool outputs contain 'Current Signal: BUY/SELL/HOLD' in the CURRENT STATUS section.
    \"\"\"
    text = tool_output.upper()
    
    # Method 1: Direct string matching for the exact patterns from tool output
    # Tools output format: "• Current Signal: BUY" or "Current Signal: SELL"
    if "CURRENT SIGNAL: BUY" in text:
        return "BUY"
    if "CURRENT SIGNAL: SELL" in text:
        return "SELL"
    if "CURRENT SIGNAL: HOLD" in text:
        return "HOLD"
    
    # Method 2: Look for "Enter Long Position" or "Enter Short Position"
    # Tools output: "Strategy Recommendation: Enter Long Position"
    if "ENTER LONG" in text:
        return "BUY"
    if "ENTER SHORT" in text:
        return "SELL"
    
    # Method 3: Look for signal interpretations
    # Some tools output: "SIGNAL: Strong Buy Signal" or "Trading Signal: Buy Signal"
    if "STRONG BUY" in text or "BUY SIGNAL" in text:
        return "BUY"
    if "STRONG SELL" in text or "SELL SIGNAL" in text:
        return "SELL"
    
    # Method 4: Check the LAST section for signal keywords
    # Split into sections and check the last part
    last_section = text[-500:] if len(text) > 500 else text
    
    # Count BUY/SELL occurrences in the last section (where current signal is)
    buy_count = last_section.count("BUY")
    sell_count = last_section.count("SELL")
    
    # If clear winner in the last section
    if buy_count > sell_count and buy_count >= 2:
        return "BUY"
    if sell_count > buy_count and sell_count >= 2:
        return "SELL"
    
    return "HOLD"

# Collect all stock data
all_stocks_data = {{}}
sector_summaries = {{}}
total_stocks = 0

for sector_name, symbols_str in sectors.items():
    stocks = [s.strip() for s in symbols_str.split(",") if s.strip()]
    
    for stock in stocks:
        # Call all 4 strategy tools
        bb_result = bollinger_fibonacci_analysis(symbol=stock, period=period)
        macd_result = macd_donchian_analysis(symbol=stock, period=period)
        connors_result = connors_zscore_analysis(symbol=stock, period=period)
        dual_ma_result = dual_moving_average_analysis(symbol=stock, period=period)
        
        # Extract signals using the improved parser
        bb_signal = extract_current_signal(bb_result)
        macd_signal = extract_current_signal(macd_result)
        connors_signal = extract_current_signal(connors_result)
        dual_ma_signal = extract_current_signal(dual_ma_result)
        
        # Count BUY signals
        signals = [bb_signal, macd_signal, connors_signal, dual_ma_signal]
        buy_count = sum(1 for s in signals if s == "BUY")
        
        all_stocks_data[stock] = {{
            "sector": sector_name,
            "buy_count": buy_count,
            "bb": bb_signal,
            "macd": macd_signal,
            "connors": connors_signal,
            "dual_ma": dual_ma_signal
        }}
        total_stocks += 1

# Calculate sector summaries
for sector_name, symbols_str in sectors.items():
    stocks = [s.strip() for s in symbols_str.split(",") if s.strip()]
    sector_stocks = [all_stocks_data[s] for s in stocks if s in all_stocks_data]
    
    if sector_stocks:
        avg_buy = sum(s["buy_count"] for s in sector_stocks) / len(sector_stocks)
        best_stock = max([(s, all_stocks_data[s]["buy_count"]) for s in stocks if s in all_stocks_data], key=lambda x: x[1])
        success_rate = sum(1 for s in sector_stocks if s["buy_count"] >= 2) / len(sector_stocks) * 100
    else:
        avg_buy = 0
        best_stock = ("N/A", 0)
        success_rate = 0
    
    sector_summaries[sector_name] = {{
        "avg": avg_buy,
        "best_stock": best_stock[0],
        "best_count": best_stock[1],
        "stock_count": len(sector_stocks),
        "success_rate": success_rate,
        "outlook": "BULLISH" if avg_buy >= 2.5 else "MODERATELY BULLISH" if avg_buy >= 1.5 else "NEUTRAL" if avg_buy >= 1 else "BEARISH"
    }}

# Rank sectors
ranked_sectors = sorted(sector_summaries.items(), key=lambda x: x[1]["avg"], reverse=True)

# Rank all stocks
all_stocks_ranked = [(sym, data["sector"], data["buy_count"], data) for sym, data in all_stocks_data.items()]
all_stocks_ranked.sort(key=lambda x: x[2], reverse=True)

# Calculate overall stats
overall_avg = sum(s[1]["avg"] for s in ranked_sectors) / len(ranked_sectors) if ranked_sectors else 0
overall_success = sum(s[1]["success_rate"] for s in ranked_sectors) / len(ranked_sectors) if ranked_sectors else 0

# Categorize picks
priority_picks = [(s, sec, c, d) for s, sec, c, d in all_stocks_ranked if c >= 3]
secondary_picks = [(s, sec, c, d) for s, sec, c, d in all_stocks_ranked if c == 2]
avoid_list = [(s, sec, c, d) for s, sec, c, d in all_stocks_ranked if c <= 1]

# Build comprehensive report
report = "# Multi-Sector Market Analysis Report\\n\\n"
report += f"**Analysis Date:** {{datetime.now().strftime('%B %d, %Y')}}\\n"
report += f"**Period:** {{period}} | **Total Stocks Analyzed:** {{total_stocks}} | **Sectors:** {{len(sectors)}}\\n\\n"
report += "---\\n\\n"

# Executive Summary
report += "## 📊 Executive Summary\\n\\n"
report += "### Cross-Sector Performance Overview\\n\\n"
report += "| Sector | Stocks | Avg BUY Signals | Success Rate | Best Stock | Outlook |\\n"
report += "|--------|--------|-----------------|--------------|------------|---------|\\n"
for sector, data in ranked_sectors:
    report += f"| **{{sector}}** | {{data['stock_count']}} | {{data['avg']:.1f}}/4 | {{data['success_rate']:.0f}}% | {{data['best_stock']}} | {{data['outlook']}} |\\n"
report += f"| **OVERALL** | **{{total_stocks}}** | **{{overall_avg:.1f}}/4** | **{{overall_success:.0f}}%** | - | - |\\n\\n"

# Key insights
report += "### Key Market Insights\\n\\n"
if overall_avg >= 2:
    report += "🟢 **Bullish Technical Environment**: Multiple sectors showing strong buy signals\\n"
elif overall_avg >= 1:
    report += "🟡 **Mixed Technical Environment**: Selective opportunities across sectors\\n"
else:
    report += "🔴 **Bearish Technical Environment**: Limited technical opportunities\\n"
report += f"🏆 **Sector Leadership**: {{ranked_sectors[0][0]}} shows strongest technical signals\\n"
report += f"💡 **Opportunities Identified**: {{len(priority_picks)}} priority + {{len(secondary_picks)}} secondary picks\\n"
report += f"⚠️ **Stocks to Avoid**: {{len(avoid_list)}} stocks with weak signals\\n\\n"
report += "---\\n\\n"

# Investment Recommendations
report += "## 🎯 Final Investment Recommendations\\n\\n"

if priority_picks:
    report += f"### 🟢 PRIORITY INVESTMENTS ({{len(priority_picks)}} Stocks)\\n\\n"
    for i, (stock, sector, buy_count, data) in enumerate(priority_picks[:5], 1):
        risk = "Low" if buy_count == 4 else "Medium"
        position = "3-5%" if buy_count == 4 else "2-3%"
        report += f"#### {{i}}. {{stock}} | {{sector}}\\n"
        report += f"**🎯 STRONG BUY | 📊 HIGH CONFIDENCE | 💰 {{position}} POSITION**\\n\\n"
        report += f"- **BUY Signals**: {{buy_count}}/4 strategies\\n"
        report += f"- **Signal Breakdown**: BB={{data['bb']}}, MACD={{data['macd']}}, Connors={{data['connors']}}, DualMA={{data['dual_ma']}}\\n"
        report += f"- **Risk Level**: {{risk}}\\n\\n"
else:
    report += "### 🟢 PRIORITY INVESTMENTS\\n\\n"
    report += "No stocks with 3+ BUY signals identified in this scan.\\n\\n"

if secondary_picks:
    report += f"### 🔵 SECONDARY OPPORTUNITIES ({{len(secondary_picks)}} Stocks)\\n\\n"
    for i, (stock, sector, buy_count, data) in enumerate(secondary_picks[:5], 1):
        report += f"#### {{stock}} | {{sector}}\\n"
        report += f"**🎯 BUY | 📊 MEDIUM CONFIDENCE | 💰 1-2% POSITION**\\n\\n"
        report += f"- **BUY Signals**: {{buy_count}}/4 strategies\\n"
        report += f"- **Signal Breakdown**: BB={{data['bb']}}, MACD={{data['macd']}}, Connors={{data['connors']}}, DualMA={{data['dual_ma']}}\\n\\n"
else:
    report += "### 🔵 SECONDARY OPPORTUNITIES\\n\\n"
    report += "No stocks with exactly 2 BUY signals identified.\\n\\n"

report += "---\\n\\n"

# Sector-by-Sector Analysis
report += "## 📈 Sector-by-Sector Analysis\\n\\n"
sector_emojis = ["🏦", "💻", "⚡", "🏥", "🛒", "🏭"]
for i, (sector, data) in enumerate(ranked_sectors):
    emoji = sector_emojis[i % len(sector_emojis)]
    report += f"### {{emoji}} {{sector}}\\n"
    report += f"**Performance**: {{data['avg']:.1f}}/4 avg BUY signals | {{data['success_rate']:.0f}}% success rate\\n\\n"
    
    sector_stocks = [(s, d) for s, sec, c, d in all_stocks_ranked if sec == sector]
    top_picks = [(s, d) for s, d in sector_stocks if d["buy_count"] >= 2]
    avoid = [s for s, d in sector_stocks if d["buy_count"] <= 1]
    
    report += "**Top Picks**:\\n"
    if top_picks:
        for stock, d in top_picks[:3]:
            report += f"- **{{stock}}** - {{d['buy_count']}}/4 BUY signals\\n"
    else:
        report += "- No strong picks in this sector\\n"
    report += "\\n"
    
    if avoid:
        report += f"**Avoid**: {{', '.join(avoid)}}\\n\\n"
    
    report += "---\\n\\n"

# Strategy Effectiveness
report += "## 📬 Strategy Effectiveness Analysis\\n\\n"
report += "| Strategy | BUY Signals | SELL Signals | HOLD Signals |\\n"
report += "|----------|-------------|--------------|--------------|\\n"

bb_buys = sum(1 for s, sec, c, d in all_stocks_ranked if d["bb"] == "BUY")
bb_sells = sum(1 for s, sec, c, d in all_stocks_ranked if d["bb"] == "SELL")
bb_holds = total_stocks - bb_buys - bb_sells

macd_buys = sum(1 for s, sec, c, d in all_stocks_ranked if d["macd"] == "BUY")
macd_sells = sum(1 for s, sec, c, d in all_stocks_ranked if d["macd"] == "SELL")
macd_holds = total_stocks - macd_buys - macd_sells

connors_buys = sum(1 for s, sec, c, d in all_stocks_ranked if d["connors"] == "BUY")
connors_sells = sum(1 for s, sec, c, d in all_stocks_ranked if d["connors"] == "SELL")
connors_holds = total_stocks - connors_buys - connors_sells

dual_ma_buys = sum(1 for s, sec, c, d in all_stocks_ranked if d["dual_ma"] == "BUY")
dual_ma_sells = sum(1 for s, sec, c, d in all_stocks_ranked if d["dual_ma"] == "SELL")
dual_ma_holds = total_stocks - dual_ma_buys - dual_ma_sells

report += f"| Bollinger-Fibonacci | {{bb_buys}}/{{total_stocks}} | {{bb_sells}}/{{total_stocks}} | {{bb_holds}}/{{total_stocks}} |\\n"
report += f"| MACD-Donchian | {{macd_buys}}/{{total_stocks}} | {{macd_sells}}/{{total_stocks}} | {{macd_holds}}/{{total_stocks}} |\\n"
report += f"| Connors RSI-ZScore | {{connors_buys}}/{{total_stocks}} | {{connors_sells}}/{{total_stocks}} | {{connors_holds}}/{{total_stocks}} |\\n"
report += f"| Dual Moving Average | {{dual_ma_buys}}/{{total_stocks}} | {{dual_ma_sells}}/{{total_stocks}} | {{dual_ma_holds}}/{{total_stocks}} |\\n\\n"

report += "---\\n\\n"

# Portfolio Construction
report += "## 🎯 Portfolio Construction Framework\\n\\n"
report += "### Recommended Allocation\\n\\n"
if len(priority_picks) >= 2:
    report += "**AGGRESSIVE APPROACH**:\\n"
    report += "- 60% in Priority Picks (distributed)\\n"
    report += "- 25% in Secondary Opportunities\\n"
    report += "- 15% Cash/Defensive\\n\\n"
else:
    report += "**CONSERVATIVE APPROACH** (Recommended):\\n"
    report += "- 40% Cash/Fixed Income (defensive)\\n"
    report += f"- 35% {{ranked_sectors[0][0]}} exposure\\n"
    report += "- 25% Selective stock picks\\n\\n"

report += "### Risk Management\\n\\n"
report += "- **Maximum single position**: 5%\\n"
report += "- **Sector exposure limit**: 30%\\n"
report += "- **Stop loss**: 8-10% below entry\\n\\n"

report += "---\\n\\n"

# Appendix
report += "## 📊 Appendix: Complete Holdings Summary\\n\\n"
report += "### ALL ANALYZED STOCKS\\n\\n"
report += "| Symbol | Sector | BUY Signals | Action | BB | MACD | Connors | DualMA |\\n"
report += "|--------|--------|-------------|--------|-----|------|---------|--------|\\n"
for stock, sector, buy_count, data in all_stocks_ranked:
    action = "STRONG BUY" if buy_count >= 3 else "BUY" if buy_count == 2 else "HOLD" if buy_count == 1 else "AVOID"
    report += f"| {{stock}} | {{sector}} | {{buy_count}}/4 | {{action}} | {{data['bb']}} | {{data['macd']}} | {{data['connors']}} | {{data['dual_ma']}} |\\n"

report += "\\n---\\n\\n"
report += "*This analysis uses 4 individual strategy tools with improved signal parsing. Past performance does not guarantee future results.*\\n"

final_answer(report)
```
"""

COMBINED_ANALYSIS_PROMPT = """Perform complete Technical + Fundamental analysis of {symbol}.

TOOLS TO CALL:
1. bollinger_fibonacci_analysis(symbol="{symbol}", period="{technical_period}")
2. macd_donchian_analysis(symbol="{symbol}", period="{technical_period}")
3. connors_zscore_analysis(symbol="{symbol}", period="{technical_period}")
4. dual_moving_average_analysis(symbol="{symbol}", period="{technical_period}")
5. fundamental_analysis_report(symbol="{symbol}", period="{fundamental_period}")

```python
symbol = "{symbol}"
tech_period = "{technical_period}"
fund_period = "{fundamental_period}"

# Get technical analysis
bb_result = bollinger_fibonacci_analysis(symbol=symbol, period=tech_period)
macd_result = macd_donchian_analysis(symbol=symbol, period=tech_period)
connors_result = connors_zscore_analysis(symbol=symbol, period=tech_period)
dual_ma_result = dual_moving_average_analysis(symbol=symbol, period=tech_period)

# Get fundamental analysis
fund_result = fundamental_analysis_report(symbol=symbol, period=fund_period)

def extract_signal(tool_output):
    \"\"\"Extract the CURRENT signal using simple string matching.\"\"\"
    text = tool_output.upper()
    
    # Direct pattern matching for "Current Signal: X"
    if "CURRENT SIGNAL: BUY" in text:
        return "BUY"
    if "CURRENT SIGNAL: SELL" in text:
        return "SELL"
    if "CURRENT SIGNAL: HOLD" in text:
        return "HOLD"
    
    # Look for recommendation patterns
    if "ENTER LONG" in text:
        return "BUY"
    if "ENTER SHORT" in text:
        return "SELL"
    
    # Look for signal interpretations
    if "STRONG BUY" in text or "BUY SIGNAL" in text:
        return "BUY"
    if "STRONG SELL" in text or "SELL SIGNAL" in text:
        return "SELL"
    
    # Fallback: count BUY/SELL in last section
    last_section = text[-500:] if len(text) > 500 else text
    buy_count = last_section.count("BUY")
    sell_count = last_section.count("SELL")
    
    if buy_count > sell_count and buy_count >= 2:
        return "BUY"
    if sell_count > buy_count and sell_count >= 2:
        return "SELL"
    
    return "HOLD"

def get_fund_outlook(fund_text):
    \"\"\"Determine fundamental outlook from the report.\"\"\"
    text = fund_text.upper()
    
    # Check for explicit recommendations
    if "STRONG BUY" in text or "INVESTMENT GRADE: A" in text:
        return "POSITIVE"
    if "STRONG SELL" in text or "INVESTMENT GRADE: F" in text or "INVESTMENT GRADE: D" in text:
        return "NEGATIVE"
    if "FINANCIAL HEALTH: STRONG" in text or "HEALTH: STRONG" in text:
        return "POSITIVE"
    if "FINANCIAL HEALTH: WEAK" in text or "HEALTH: WEAK" in text:
        return "NEGATIVE"
    
    # Count positive vs negative indicators
    positive_indicators = text.count("STRONG") + text.count("GOOD") + text.count("POSITIVE") + text.count("BUY")
    negative_indicators = text.count("WEAK") + text.count("POOR") + text.count("NEGATIVE") + text.count("SELL") + text.count("CONCERN")
    
    if positive_indicators > negative_indicators:
        return "POSITIVE"
    elif negative_indicators > positive_indicators:
        return "NEGATIVE"
    return "NEUTRAL"

# Extract signals
bb_signal = extract_signal(bb_result)
macd_signal = extract_signal(macd_result)
connors_signal = extract_signal(connors_result)
dual_ma_signal = extract_signal(dual_ma_result)
fund_outlook = get_fund_outlook(fund_result)

# Count technical signals
tech_buy = sum(1 for s in [bb_signal, macd_signal, connors_signal, dual_ma_signal] if s == "BUY")
tech_sell = sum(1 for s in [bb_signal, macd_signal, connors_signal, dual_ma_signal] if s == "SELL")

# Determine outlooks
tech_outlook = "BULLISH" if tech_buy >= 3 else "MODERATELY BULLISH" if tech_buy >= 2 else "BEARISH" if tech_sell >= 3 else "NEUTRAL"

# Determine alignment
if (tech_buy >= 2 and fund_outlook == "POSITIVE") or (tech_sell >= 2 and fund_outlook == "NEGATIVE"):
    alignment = "ALIGNED"
    align_emoji = "✅"
elif (tech_buy >= 2 and fund_outlook == "NEGATIVE") or (tech_sell >= 2 and fund_outlook == "POSITIVE"):
    alignment = "DIVERGENT"
    align_emoji = "❌"
else:
    alignment = "MIXED"
    align_emoji = "⚠️"

# Final recommendation
if tech_buy >= 3 and fund_outlook == "POSITIVE":
    final_rec = "STRONG BUY"
    confidence = "HIGH"
elif tech_buy >= 2 and fund_outlook == "POSITIVE":
    final_rec = "BUY"
    confidence = "HIGH"
elif tech_sell >= 3 and fund_outlook == "NEGATIVE":
    final_rec = "STRONG SELL"
    confidence = "HIGH"
elif tech_sell >= 2 and fund_outlook == "NEGATIVE":
    final_rec = "SELL"
    confidence = "HIGH"
elif tech_buy >= 3:
    final_rec = "BUY"
    confidence = "MEDIUM"
elif tech_sell >= 3:
    final_rec = "SELL"
    confidence = "MEDIUM"
elif tech_buy >= 2:
    final_rec = "BUY"
    confidence = "LOW"
elif tech_sell >= 2:
    final_rec = "SELL"
    confidence = "LOW"
else:
    final_rec = "HOLD"
    confidence = "LOW"

# Build report
report = f"# {{symbol}} Combined Investment Analysis\\n\\n"
report += "## Executive Summary\\n\\n"
report += f"**Symbol:** {{symbol}}\\n\\n"
report += f"**Technical Period:** {{tech_period}}\\n\\n"
report += f"**Fundamental Period:** {{fund_period}}\\n\\n"
report += f"**COMBINED RECOMMENDATION:** {{final_rec}}\\n\\n"
report += f"**Confidence Level:** {{confidence}}\\n\\n"
report += f"**Technical/Fundamental Alignment:** {{alignment}} {{align_emoji}}\\n\\n"
report += "---\\n\\n"

report += "## Technical Analysis Summary\\n\\n"
report += "### Technical Indicators Table\\n\\n"
report += "| Strategy | Signal |\\n"
report += "|----------|--------|\\n"
report += f"| Bollinger-Fibonacci | {{bb_signal}} |\\n"
report += f"| MACD-Donchian | {{macd_signal}} |\\n"
report += f"| Connors RSI-ZScore | {{connors_signal}} |\\n"
report += f"| Dual Moving Average | {{dual_ma_signal}} |\\n\\n"
report += f"**Technical Verdict:** {{tech_outlook}} with {{tech_buy}}/4 BUY signals\\n\\n"
report += "---\\n\\n"

report += "## Fundamental Analysis Summary\\n\\n"
report += f"{{fund_result}}\\n\\n"
report += f"**Fundamental Verdict:** {{fund_outlook}}\\n\\n"
report += "---\\n\\n"

report += "## Alignment Analysis\\n\\n"
report += "| Aspect | Technical | Fundamental | Alignment |\\n"
report += "|--------|-----------|-------------|-----------|\\n"
report += f"| Overall | {{tech_outlook}} | {{fund_outlook}} | {{align_emoji}} |\\n\\n"
report += f"**Alignment Status:** {{alignment}}\\n\\n"
report += "---\\n\\n"

report += f"## 🎯 FINAL RECOMMENDATION: **{{final_rec}}**\\n\\n"
report += "### Why This Recommendation?\\n\\n"
report += f"**Technical Factors:** {{tech_buy}}/4 strategies show bullish signals\\n\\n"
report += f"**Fundamental Factors:** Financial analysis shows {{fund_outlook.lower()}} outlook\\n\\n"
report += f"**Alignment:** Technical and fundamental views are {{alignment.lower()}}\\n\\n"
report += "---\\n\\n"
report += "**Disclaimer:** This analysis is for educational purposes only.\\n\\n"

final_answer(report)
```
"""


# ===========================================================================
# Analysis Functions (Using LOW-LEVEL Tools with Code)
# ===========================================================================

def run_technical_analysis(
    symbol: str,
    period: str = "1y",
    model_id: str = DEFAULT_MODEL_ID,
    model_provider: str = DEFAULT_MODEL_PROVIDER,
    openai_api_key: Optional[str] = None,
    hf_token: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    max_steps: int = DEFAULT_MAX_STEPS,
    executor_type: Literal["local", "e2b", "docker"] = "local",
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """Run technical analysis using 4 individual strategy tools."""
    configure_finance_tools()
    
    model = build_model(
        model_id=model_id,
        provider=model_provider,
        api_key=openai_api_key,
        hf_token=hf_token,
        api_base=openai_base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    agent = build_agent(model, LOW_LEVEL_TOOLS, max_steps=max_steps, executor_type=executor_type)
    prompt = TECHNICAL_ANALYSIS_PROMPT.format(symbol=symbol, period=period)
    result = agent.run(prompt)
    return format_agent_result(result)


def run_market_scanner(
    symbols: str,
    period: str = "1y",
    model_id: str = DEFAULT_MODEL_ID,
    model_provider: str = DEFAULT_MODEL_PROVIDER,
    openai_api_key: Optional[str] = None,
    hf_token: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    max_steps: int = 30,
    executor_type: Literal["local", "e2b", "docker"] = "local",
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """Run market scanner using loops over individual strategy tools."""
    configure_finance_tools()
    
    model = build_model(
        model_id=model_id,
        provider=model_provider,
        api_key=openai_api_key,
        hf_token=hf_token,
        api_base=openai_base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    agent = build_agent(model, LOW_LEVEL_TOOLS, max_steps=max_steps, executor_type=executor_type)
    symbol_list = [s.strip() for s in symbols.split(",")]
    prompt = MARKET_SCANNER_PROMPT.format(symbols=symbols, symbol_list=symbol_list, period=period)
    result = agent.run(prompt)
    return format_agent_result(result)


def run_fundamental_analysis(
    symbol: str,
    period: str = "3y",
    model_id: str = DEFAULT_MODEL_ID,
    model_provider: str = DEFAULT_MODEL_PROVIDER,
    openai_api_key: Optional[str] = None,
    hf_token: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    max_steps: int = DEFAULT_MAX_STEPS,
    executor_type: Literal["local", "e2b", "docker"] = "local",
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """Run fundamental analysis using fundamental_analysis_report tool."""
    configure_finance_tools()
    
    model = build_model(
        model_id=model_id,
        provider=model_provider,
        api_key=openai_api_key,
        hf_token=hf_token,
        api_base=openai_base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    agent = build_agent(model, LOW_LEVEL_TOOLS, max_steps=max_steps, executor_type=executor_type)
    prompt = FUNDAMENTAL_ANALYSIS_PROMPT.format(symbol=symbol, period=period)
    result = agent.run(prompt)
    return format_agent_result(result)


def run_multi_sector_analysis(
    sectors: Dict[str, str],
    period: str = "1y",
    model_id: str = DEFAULT_MODEL_ID,
    model_provider: str = DEFAULT_MODEL_PROVIDER,
    openai_api_key: Optional[str] = None,
    hf_token: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    max_steps: int = 50,
    executor_type: Literal["local", "e2b", "docker"] = "local",
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """Run multi-sector analysis using nested loops over tools."""
    configure_finance_tools()
    
    model = build_model(
        model_id=model_id,
        provider=model_provider,
        api_key=openai_api_key,
        hf_token=hf_token,
        api_base=openai_base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    agent = build_agent(model, LOW_LEVEL_TOOLS, max_steps=max_steps, executor_type=executor_type)
    sector_details = "\n".join([f"- {name}: {symbols}" for name, symbols in sectors.items()])
    prompt = MULTI_SECTOR_PROMPT.format(sector_details=sector_details, sectors_dict=sectors, period=period)
    result = agent.run(prompt)
    return format_agent_result(result)


def run_combined_analysis(
    symbol: str,
    technical_period: str = "1y",
    fundamental_period: str = "3y",
    model_id: str = DEFAULT_MODEL_ID,
    model_provider: str = DEFAULT_MODEL_PROVIDER,
    openai_api_key: Optional[str] = None,
    hf_token: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    max_steps: int = 25,
    executor_type: Literal["local", "e2b", "docker"] = "local",
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """Run combined technical + fundamental analysis."""
    configure_finance_tools()
    
    model = build_model(
        model_id=model_id,
        provider=model_provider,
        api_key=openai_api_key,
        hf_token=hf_token,
        api_base=openai_base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    agent = build_agent(model, LOW_LEVEL_TOOLS, max_steps=max_steps, executor_type=executor_type)
    prompt = COMBINED_ANALYSIS_PROMPT.format(
        symbol=symbol,
        technical_period=technical_period,
        fundamental_period=fundamental_period,
    )
    result = agent.run(prompt)
    return format_agent_result(result)


# ===========================================================================
# CLI Entry Point
# ===========================================================================

def main():
    """CLI entry point for CodeAgent analysis."""
    parser = argparse.ArgumentParser(description="CodeAgent Stock Analysis")
    parser.add_argument("symbol", help="Stock symbol or comma-separated symbols")
    parser.add_argument("--mode", choices=["technical", "scanner", "fundamental", "combined"],
                        default="technical", help="Analysis mode")
    parser.add_argument("--period", default="1y", help="Analysis period")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--model-provider", default=DEFAULT_MODEL_PROVIDER)
    parser.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS)
    parser.add_argument("--executor", choices=["local", "e2b", "docker"],
                        default=DEFAULT_EXECUTOR, help="Code executor type")
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE,
                        help="LLM temperature (default: 0.1)")
    
    args = parser.parse_args()
    
    try:
        if args.mode == "technical":
            result = run_technical_analysis(
                symbol=args.symbol, period=args.period, model_id=args.model_id,
                model_provider=args.model_provider, max_steps=args.max_steps,
                executor_type=args.executor, temperature=args.temperature,
            )
        elif args.mode == "scanner":
            result = run_market_scanner(
                symbols=args.symbol, period=args.period, model_id=args.model_id,
                model_provider=args.model_provider, max_steps=args.max_steps,
                executor_type=args.executor, temperature=args.temperature,
            )
        elif args.mode == "fundamental":
            result = run_fundamental_analysis(
                symbol=args.symbol, period=args.period, model_id=args.model_id,
                model_provider=args.model_provider, max_steps=args.max_steps,
                executor_type=args.executor, temperature=args.temperature,
            )
        elif args.mode == "combined":
            result = run_combined_analysis(
                symbol=args.symbol, technical_period=args.period, model_id=args.model_id,
                model_provider=args.model_provider, max_steps=args.max_steps,
                executor_type=args.executor, temperature=args.temperature,
            )
        
        print(result)
        
    finally:
        shutdown_finance_tools()


if __name__ == "__main__":
    main()