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
    # Normalize control characters that can break Markdown rendering
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = ''.join(ch for ch in text if ch in ('\n', '\t') or ord(ch) >= 32)
    
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

Write Python code to:
1. Call all 4 strategy tools
2. Parse the results to extract signals and metrics
3. Build a professional markdown report

REQUIRED CODE STRUCTURE:
```python
import json
import re

# Call all 4 strategy tools
bb_result = bollinger_fibonacci_analysis(symbol="{symbol}", period="{period}")
macd_result = macd_donchian_analysis(symbol="{symbol}", period="{period}")
connors_result = connors_zscore_analysis(symbol="{symbol}", period="{period}")
dual_ma_result = dual_moving_average_analysis(symbol="{symbol}", period="{period}")

# Helper function to extract signal from result
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

# Helper to extract numeric value after a label
def extract_value(text, label):
    pattern = label + r"[:\\s]+([\\-]?[\\d.]+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1)
    return "N/A"

# Parse signals
bb_signal = get_signal(bb_result)
macd_signal = get_signal(macd_result)
connors_signal = get_signal(connors_result)
dual_ma_signal = get_signal(dual_ma_result)

# Count signals
signals = [bb_signal, macd_signal, connors_signal, dual_ma_signal]
buy_count = sum(1 for s in signals if "BUY" in s)
sell_count = sum(1 for s in signals if "SELL" in s)
hold_count = 4 - buy_count - sell_count

# Determine overall recommendation
if buy_count >= 3:
    overall = "STRONG BUY" if buy_count == 4 else "BUY"
    confidence = "HIGH"
    outlook = "BULLISH"
elif buy_count >= 2:
    overall = "BUY"
    confidence = "MEDIUM"
    outlook = "MODERATELY BULLISH"
elif sell_count >= 3:
    overall = "STRONG SELL" if sell_count == 4 else "SELL"
    confidence = "HIGH"
    outlook = "BEARISH"
elif sell_count >= 2:
    overall = "SELL"
    confidence = "MEDIUM"
    outlook = "MODERATELY BEARISH"
else:
    overall = "HOLD"
    confidence = "LOW"
    outlook = "NEUTRAL"

# Determine momentum and trend
momentum = "Positive" if buy_count > sell_count else "Negative" if sell_count > buy_count else "Neutral"
trend = "Upward" if buy_count >= 3 else "Downward" if sell_count >= 3 else "Sideways"
risk = "Low" if buy_count >= 3 or sell_count >= 3 else "Medium" if buy_count >= 2 or sell_count >= 2 else "High"

# Build professional report
report = "# {symbol} Technical Analysis Report\\n\\n"
report += "## Executive Summary\\n\\n"
report += f"Analysis of {symbol} using four technical scoring systems reveals a **{{outlook}}** outlook.\\n\\n"
report += "**Analysis Period:** {period}\\n\\n"
report += "---\\n\\n"

report += "## Technical Indicators Summary Table\\n\\n"
report += "| Indicator System | Signal | Key Findings |\\n"
report += "|-----------------|--------|--------------|\\n"
report += f"| **Bollinger-Fibonacci** | {{bb_signal}} | Strategy analysis complete |\\n"
report += f"| **MACD-Donchian Combined** | {{macd_signal}} | Strategy analysis complete |\\n"
report += f"| **Connors RSI + Z-Score** | {{connors_signal}} | Strategy analysis complete |\\n"
report += f"| **Dual Moving Average** | {{dual_ma_signal}} | Strategy analysis complete |\\n\\n"
report += "---\\n\\n"

report += "## Detailed Analysis\\n\\n"
report += "### 1. Bollinger-Fibonacci Strategy\\n\\n"
report += f"- **Signal:** {{bb_signal}}\\n\\n"
report += f"**Full Analysis:**\\n\\n{{bb_result}}\\n\\n"
report += "---\\n\\n"

report += "### 2. MACD-Donchian Combined Strategy\\n\\n"
report += f"- **Signal:** {{macd_signal}}\\n\\n"
report += f"**Full Analysis:**\\n\\n{{macd_result}}\\n\\n"
report += "---\\n\\n"

report += "### 3. Connors RSI + Z-Score Combined Strategy\\n\\n"
report += f"- **Signal:** {{connors_signal}}\\n\\n"
report += f"**Full Analysis:**\\n\\n{{connors_result}}\\n\\n"
report += "---\\n\\n"

report += "### 4. Dual Moving Average (50/200 EMA) Strategy\\n\\n"
report += f"- **Signal:** {{dual_ma_signal}}\\n\\n"
report += f"**Full Analysis:**\\n\\n{{dual_ma_result}}\\n\\n"
report += "---\\n\\n"

report += "## Consensus Analysis\\n\\n"
report += f"### Overall Technical Health: **{{outlook}}**\\n\\n"
report += "| Metric | Status |\\n"
report += "|--------|--------|\\n"
report += f"| **Trend Direction** | {{trend}} |\\n"
report += f"| **Momentum** | {{momentum}} |\\n"
report += f"| **Risk Level** | {{risk}} |\\n\\n"

report += "### Signal Breakdown\\n\\n"
report += f"- **BUY Signals:** {{buy_count}}/4\\n\\n"
report += f"- **SELL Signals:** {{sell_count}}/4\\n\\n"
report += f"- **HOLD Signals:** {{hold_count}}/4\\n\\n"
report += f"- **Consensus Direction:** {{outlook}}\\n\\n"
report += "---\\n\\n"

report += f"## 🎯 FINAL RECOMMENDATION: **{{overall}}**\\n\\n"
report += "### Action Plan\\n\\n"

if "BUY" in overall:
    report += f"**For Current {symbol} Holders:**\\n\\n"
    report += "- ✅ HOLD and consider adding to position\\n\\n"
    report += "- ✅ Set trailing stop-loss to protect gains\\n\\n"
    report += "- ❌ Do NOT sell prematurely\\n\\n"
    report += f"**For Potential Buyers:**\\n\\n"
    report += "- BUY at current levels with proper position sizing\\n\\n"
    report += "- ⏳ Key triggers to watch:\\n\\n"
    report += "  - 📊 Volume confirmation on breakouts\\n\\n"
    report += "  - 📊 Support levels holding\\n\\n"
elif "SELL" in overall:
    report += f"**For Current {symbol} Holders:**\\n\\n"
    report += "- ✅ Consider reducing position size\\n\\n"
    report += "- ✅ Set tight stop-loss levels\\n\\n"
    report += "- ❌ Do NOT add to positions\\n\\n"
    report += f"**For Potential Buyers:**\\n\\n"
    report += "- WAIT for better entry points\\n\\n"
    report += "- ⏳ Key triggers to watch:\\n\\n"
    report += "  - 📊 Reversal signals\\n\\n"
    report += "  - 📊 Support levels\\n\\n"
else:
    report += f"**For Current {symbol} Holders:**\\n\\n"
    report += "- ✅ HOLD current positions\\n\\n"
    report += "- ✅ Monitor for direction confirmation\\n\\n"
    report += "- ❌ Avoid large new positions\\n\\n"
    report += f"**For Potential Buyers:**\\n\\n"
    report += "- WAIT for clearer signals\\n\\n"
    report += "- ⏳ Key triggers to watch:\\n\\n"
    report += "  - 📊 Breakout above resistance\\n\\n"
    report += "  - 📊 All indicators turning positive\\n\\n"

report += "---\\n\\n"
report += "## Risk Management\\n\\n"
report += "- **Position Size:** Maximum 2-5% of portfolio\\n\\n"
report += "- **Stop Loss:** Set based on recent support levels\\n\\n"
report += "- **Take Profit:** Set based on resistance levels\\n\\n"
report += "---\\n\\n"

report += "## Conclusion\\n\\n"
report += f"Based on comprehensive analysis using four technical strategies, {symbol} shows a **{{outlook}}** outlook with {{buy_count}}/4 bullish signals. "
report += f"The recommendation is **{{overall}}** with **{{confidence}}** confidence. "
report += "Always conduct your own due diligence before investing.\\n\\n"
report += "**Disclaimer:** This analysis is for educational purposes only.\\n\\n"

final_answer(report)
```

REQUIREMENTS:
1. Extract REAL data from tool results
2. Use markdown tables for summary
3. Use emojis (✅, ❌, ⏳, 📊, 🎯) for scannability
4. Include action plans for holders and buyers
5. Use USD for currency (never use dollar sign)
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

MULTI_SECTOR_PROMPT = """Analyze multiple sectors:

{sector_details}

Period: {period}

```python
import json

sectors = {sectors_dict}
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

def count_buy_signals(bb, macd, connors, dual_ma):
    count = 0
    for result in [bb, macd, connors, dual_ma]:
        if "BUY" in get_signal(result):
            count += 1
    return count

# Analyze all sectors
all_data = {{}}
sector_summaries = {{}}

for sector_name, symbols_str in sectors.items():
    stocks = [s.strip() for s in symbols_str.split(",")][:5]
    all_data[sector_name] = {{}}
    
    sector_buy = 0
    best_stock = None
    best_count = -1
    
    for stock in stocks:
        bb = bollinger_fibonacci_analysis(symbol=stock, period=period)
        macd = macd_donchian_analysis(symbol=stock, period=period)
        connors = connors_zscore_analysis(symbol=stock, period=period)
        dual_ma = dual_moving_average_analysis(symbol=stock, period=period)
        
        buy_count = count_buy_signals(bb, macd, connors, dual_ma)
        all_data[sector_name][stock] = {{"buy_count": buy_count}}
        sector_buy += buy_count
        
        if buy_count > best_count:
            best_count = buy_count
            best_stock = stock
    
    avg = sector_buy / len(stocks) if stocks else 0
    sector_summaries[sector_name] = {{
        "avg": avg,
        "best_stock": best_stock,
        "best_count": best_count,
        "outlook": "BULLISH" if avg >= 2 else "NEUTRAL" if avg >= 1 else "BEARISH"
    }}

ranked_sectors = sorted(sector_summaries.items(), key=lambda x: x[1]["avg"], reverse=True)

# Build report
report = "# Multi-Sector Analysis Report\\n\\n"
report += "## Executive Summary\\n\\n"
report += f"**Sectors Analyzed:** {{', '.join(sectors.keys())}}\\n\\n"
report += f"**Analysis Period:** {{period}}\\n\\n"
report += f"**Strongest Sector:** {{ranked_sectors[0][0]}}\\n\\n"
report += f"**Weakest Sector:** {{ranked_sectors[-1][0]}}\\n\\n"
report += "---\\n\\n"

report += "## Sector Rankings Summary Table\\n\\n"
report += "| Rank | Sector | Avg BUY Signals | Best Stock | Outlook |\\n"
report += "|------|--------|-----------------|------------|---------|\\n"
for i, (sector, data) in enumerate(ranked_sectors, 1):
    report += f"| {{i}} | {{sector}} | {{data['avg']:.1f}}/4 | {{data['best_stock']}} | {{data['outlook']}} |\\n"
report += "\\n---\\n\\n"

# Top picks across sectors
all_stocks = []
for sector, stocks_data in all_data.items():
    for stock, data in stocks_data.items():
        all_stocks.append((stock, sector, data["buy_count"]))
all_stocks.sort(key=lambda x: x[2], reverse=True)

report += "## 🎯 TOP PICKS ACROSS ALL SECTORS\\n\\n"
for i, (stock, sector, buy_count) in enumerate(all_stocks[:5], 1):
    rec = "STRONG BUY" if buy_count >= 3 else "BUY" if buy_count >= 2 else "HOLD"
    report += f"{{i}}. **{{stock}}** ({{sector}}) - {{buy_count}}/4 BUY signals - {{rec}}\\n\\n"

report += "---\\n\\n"
report += "**Disclaimer:** This analysis is for educational purposes only.\\n\\n"

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
import json
import re

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

def get_signal(result):
    if "STRONG BUY" in result.upper():
        return "STRONG BUY"
    elif "STRONG SELL" in result.upper():
        return "STRONG SELL"
    elif "BUY" in result.upper():
        return "BUY"
    elif "SELL" in result.upper():
        return "SELL"
    return "HOLD"

# Extract signals
bb_signal = get_signal(bb_result)
macd_signal = get_signal(macd_result)
connors_signal = get_signal(connors_result)
dual_ma_signal = get_signal(dual_ma_result)
fund_signal = get_signal(fund_result)

# Count technical signals
tech_buy = sum(1 for s in [bb_signal, macd_signal, connors_signal, dual_ma_signal] if "BUY" in s)
tech_sell = sum(1 for s in [bb_signal, macd_signal, connors_signal, dual_ma_signal] if "SELL" in s)

# Determine outlooks
tech_outlook = "BULLISH" if tech_buy >= 3 else "MODERATELY BULLISH" if tech_buy >= 2 else "BEARISH" if tech_sell >= 3 else "NEUTRAL"
fund_outlook = "POSITIVE" if "BUY" in fund_signal else "NEGATIVE" if "SELL" in fund_signal else "NEUTRAL"

# Determine alignment
if (tech_buy >= 2 and "BUY" in fund_signal) or (tech_sell >= 2 and "SELL" in fund_signal):
    alignment = "ALIGNED"
    align_emoji = "✅"
elif (tech_buy >= 2 and "SELL" in fund_signal) or (tech_sell >= 2 and "BUY" in fund_signal):
    alignment = "DIVERGENT"
    align_emoji = "❌"
else:
    alignment = "MIXED"
    align_emoji = "⚠️"

# Final recommendation
if tech_buy >= 3 and "BUY" in fund_signal:
    final_rec = "STRONG BUY"
    confidence = "HIGH"
elif tech_buy >= 2 and "BUY" in fund_signal:
    final_rec = "BUY"
    confidence = "MEDIUM"
elif tech_sell >= 3 and "SELL" in fund_signal:
    final_rec = "STRONG SELL"
    confidence = "HIGH"
elif tech_sell >= 2 and "SELL" in fund_signal:
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