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
import os
from typing import Dict, Literal, Optional

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
]

# ===========================================================================
# Configuration
# ===========================================================================

DEFAULT_MODEL_ID = os.getenv("SMOLAGENT_MODEL_ID", "gpt-4o")
DEFAULT_MODEL_PROVIDER = os.getenv("SMOLAGENT_MODEL_PROVIDER", "litellm")
DEFAULT_MAX_STEPS = int(os.getenv("SMOLAGENT_MAX_STEPS", "20"))
DEFAULT_EXECUTOR = os.getenv("SMOLAGENT_EXECUTOR", "local")


def build_model(
    model_id: str,
    provider: str,
    api_key: Optional[str] = None,
    hf_token: Optional[str] = None,
    api_base: Optional[str] = None,
):
    """Create an LLM model instance for CodeAgent."""
    if provider == "litellm":
        kwargs = {"model_id": model_id}
        if api_key:
            kwargs["api_key"] = api_key
        if api_base:
            kwargs["api_base"] = api_base
        return LiteLLMModel(**kwargs)
    else:
        token = hf_token or os.getenv("HF_TOKEN")
        return InferenceClientModel(model_id=model_id, token=token)


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
    
    # Add executor type for sandboxed execution
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

REQUIRED CODE STRUCTURE:
```python
import json
import re

# Call all 4 strategies
bb_result = bollinger_fibonacci_analysis(symbol="{symbol}", period="{period}")
macd_result = macd_donchian_analysis(symbol="{symbol}", period="{period}")
connors_result = connors_zscore_analysis(symbol="{symbol}", period="{period}")
dual_ma_result = dual_moving_average_analysis(symbol="{symbol}", period="{period}")

# Helper function to extract signal
def get_signal(result):
    text = result.upper()
    if "STRONG BUY" in text:
        return "STRONG BUY"
    elif "STRONG SELL" in text:
        return "STRONG SELL"
    elif "BUY" in text and "SELL" not in text[:text.find("BUY")+10]:
        return "BUY"
    elif "SELL" in text:
        return "SELL"
    return "HOLD"

# Extract signals from each strategy
bb_signal = get_signal(bb_result)
macd_signal = get_signal(macd_result)
connors_signal = get_signal(connors_result)
dual_ma_signal = get_signal(dual_ma_result)

# Count signals
signals = [bb_signal, macd_signal, connors_signal, dual_ma_signal]
buy_count = sum(1 for s in signals if "BUY" in s)
sell_count = sum(1 for s in signals if "SELL" in s)
hold_count = 4 - buy_count - sell_count

# Determine consensus
if buy_count >= 3:
    consensus = "STRONG BUY"
    confidence = "HIGH"
elif buy_count >= 2:
    consensus = "BUY"
    confidence = "MEDIUM"
elif sell_count >= 3:
    consensus = "STRONG SELL"
    confidence = "HIGH"
elif sell_count >= 2:
    consensus = "SELL"
    confidence = "MEDIUM"
else:
    consensus = "HOLD"
    confidence = "LOW"

# Build structured report (NO TABLES - use lists instead)
report = f'''
{symbol} TECHNICAL ANALYSIS REPORT
Period: {period}

================================================================================
1. EXECUTIVE SUMMARY
================================================================================

Symbol: {symbol}
Analysis Period: {period}
Overall Recommendation: {{consensus}}
Confidence Level: {{confidence}}

================================================================================
2. STRATEGY RESULTS
================================================================================

2.1 Bollinger Bands and Fibonacci Retracement
Signal: {{bb_signal}}
Analysis Output:
{{bb_result[:800]}}

2.2 MACD-Donchian Combined
Signal: {{macd_signal}}
Analysis Output:
{{macd_result[:800]}}

2.3 Connors RSI and Z-Score Combined
Signal: {{connors_signal}}
Analysis Output:
{{connors_result[:800]}}

2.4 Dual Moving Average Crossover
Signal: {{dual_ma_signal}}
Analysis Output:
{{dual_ma_result[:800]}}

================================================================================
3. SIGNAL CONSENSUS
================================================================================

Signal Count: {{buy_count}} BUY, {{sell_count}} SELL, {{hold_count}} HOLD
Consensus Direction: {{"BULLISH" if buy_count > sell_count else "BEARISH" if sell_count > buy_count else "NEUTRAL"}}
Consensus Strength: {{confidence}}

================================================================================
4. STRATEGY SIGNALS SUMMARY
================================================================================

- Bollinger-Fibonacci: {{bb_signal}}
- MACD-Donchian: {{macd_signal}}
- Connors RSI-ZScore: {{connors_signal}}
- Dual Moving Average: {{dual_ma_signal}}

================================================================================
5. FINAL RECOMMENDATION
================================================================================

Action: {{consensus}}
Confidence: {{confidence}}

Rationale:
Based on the analysis of 4 technical strategies:
- {{buy_count}} strategies indicate BUY signals
- {{sell_count}} strategies indicate SELL signals
- {{hold_count}} strategies indicate HOLD signals

The majority consensus supports a {{consensus}} recommendation.

Supporting Evidence:
- Bollinger-Fibonacci analysis shows {{bb_signal}} signal
- MACD-Donchian analysis shows {{macd_signal}} signal
- Connors RSI-ZScore analysis shows {{connors_signal}} signal
- Dual Moving Average analysis shows {{dual_ma_signal}} signal

================================================================================
6. RISK FACTORS
================================================================================

- Strategy disagreement: {{4 - max(buy_count, sell_count, hold_count)}} out of 4 strategies show different signals
- Market conditions may change rapidly
- Past performance does not guarantee future results
'''

final_answer(report)
```

CRITICAL REQUIREMENTS:
1. EXTRACT actual data from tool results - include the tool output in the report
2. Use numbered sections (1., 2., 2.1, etc.) for clear organization
3. Do NOT use markdown tables with pipe characters - they render poorly
4. Do NOT use italic text (no asterisks for emphasis)
5. Use USD for currency values (never use the dollar sign symbol)
6. Connect the recommendation to the specific data points

Write complete code that parses tool outputs and builds a well-documented report.
"""

# NOTE: In MARKET_SCANNER_PROMPT, all occurrences of {stock} must be escaped as {{stock}}
# because this string uses .format() for symbols, symbol_list, and period.
MARKET_SCANNER_PROMPT = """Scan and compare these stocks: {symbols}

TOOLS TO CALL (for each stock):
1. bollinger_fibonacci_analysis(symbol, period)
2. macd_donchian_analysis(symbol, period)
3. connors_zscore_analysis(symbol, period)
4. dual_moving_average_analysis(symbol, period)

REQUIRED CODE STRUCTURE:
```python
import json
import re

stocks = {symbol_list}
period = "{period}"

# Helper function to extract signal
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

# Parse results for each stock
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

# Rank stocks by buy signal count
ranked = sorted(stock_summaries.items(), key=lambda x: x[1]["buy_count"], reverse=True)

# Determine top picks and stocks to avoid
top_picks = [stock for stock, data in ranked if data["buy_count"] >= 3]
stocks_to_avoid = [stock for stock, data in ranked if data["buy_count"] == 0]

# Build structured report (NO TABLES - use lists instead)
report = f'''
MARKET SCANNER REPORT
Stocks Analyzed: {{", ".join(stocks)}}
Period: {{period}}

================================================================================
1. MARKET SCANNER OVERVIEW
================================================================================

Stocks analyzed: {{", ".join(stocks)}}
Analysis period: {{period}}
Total stocks: {{len(stocks)}}

================================================================================
2. STOCK RANKINGS (Best to Worst)
================================================================================
'''

for i, (stock, data) in enumerate(ranked, 1):
    rec = "STRONG BUY" if data["buy_count"] >= 3 else "BUY" if data["buy_count"] >= 2 else "HOLD" if data["buy_count"] >= 1 else "AVOID"
    report += f'''
Rank {{i}}: {{stock}}
- Buy Signals: {{data["buy_count"]}}/4 strategies
- Recommendation: {{rec}}
'''

report += '''

================================================================================
3. DETAILED STOCK ANALYSIS
================================================================================
'''

for i, stock in enumerate(stocks, 1):
    data = stock_summaries[stock]
    results = all_data[stock]
    
    report += f'''
3.{{i}} {{stock}}

Strategy Signals:
- Bollinger-Fibonacci: {{data["bb_signal"]}}
- MACD-Donchian: {{data["macd_signal"]}}
- Connors RSI-ZScore: {{data["connors_signal"]}}
- Dual Moving Average: {{data["dual_ma_signal"]}}

Signal Consensus: {{data["buy_count"]}}/4 strategies bullish

Key Data from Tools:
BB-Fib Output: {{results["bb"][:300]}}...
MACD Output: {{results["macd"][:300]}}...

'''

report += f'''
================================================================================
4. RECOMMENDATIONS
================================================================================

Top Picks (3+ BUY signals):
'''

if top_picks:
    for i, stock in enumerate(top_picks, 1):
        data = stock_summaries[stock]
        report += f"{{i}}. {{stock}} - {{data['buy_count']}}/4 BUY signals\\n"
else:
    report += "No stocks with 3+ BUY signals\\n"

report += '''
Stocks to Avoid (0 BUY signals):
'''

if stocks_to_avoid:
    for i, stock in enumerate(stocks_to_avoid, 1):
        report += f"{{i}}. {{stock}} - 0/4 BUY signals\\n"
else:
    report += "No stocks with 0 BUY signals\\n"

total_buy = sum(d["buy_count"] for d in stock_summaries.values())
avg_buy = total_buy / len(stocks)

report += f'''

================================================================================
5. MARKET ASSESSMENT
================================================================================

Total BUY signals across all stocks: {{total_buy}}
Average BUY signals per stock: {{avg_buy:.1f}}
Market Sentiment: {{"BULLISH" if avg_buy >= 2 else "NEUTRAL" if avg_buy >= 1 else "BEARISH"}}

================================================================================
6. REFERENCE DATA (Full Tool Outputs)
================================================================================
'''

for stock in stocks:
    results = all_data[stock]
    report += f'''
--- {{stock}} ---

BOLLINGER-FIBONACCI:
{{results["bb"]}}

MACD-DONCHIAN:
{{results["macd"]}}

CONNORS RSI-ZSCORE:
{{results["connors"]}}

DUAL MOVING AVERAGE:
{{results["dual_ma"]}}

'''

final_answer(report)
```

CRITICAL REQUIREMENTS:
1. EXTRACT actual data from each tool result
2. Use numbered sections for organization
3. Do NOT use markdown tables with pipe characters - they render poorly
4. Do NOT use italic text
5. Use USD for currency (never use the dollar sign symbol)
6. Include tool outputs in the reference section
7. Rank based on actual signal counts

Write complete code that extracts real data and builds an informative, well-documented report.
"""

FUNDAMENTAL_ANALYSIS_PROMPT = """Analyze {symbol} fundamentals.

TOOL TO CALL:
fundamental_analysis_report(symbol="{symbol}", period="{period}")

REQUIRED CODE:
```python
import re

# Get fundamental analysis
fund_data = fundamental_analysis_report(symbol="{symbol}", period="{period}")

# The tool returns detailed financial data
# Parse key metrics if possible
def extract_value(text, pattern, default="N/A"):
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1) if match else default

# Determine overall assessment
if "STRONG" in fund_data.upper() and "BUY" in fund_data.upper():
    assessment = "STRONG BUY"
    health = "EXCELLENT"
elif "BUY" in fund_data.upper():
    assessment = "BUY"
    health = "GOOD"
elif "SELL" in fund_data.upper():
    assessment = "SELL"
    health = "WEAK"
else:
    assessment = "HOLD"
    health = "MODERATE"

# Build structured report
report = f'''
{symbol} FUNDAMENTAL ANALYSIS REPORT
Period: {period}

================================================================================
1. COMPANY OVERVIEW
================================================================================
Symbol: {symbol}
Analysis Period: {period}

================================================================================
2. FINANCIAL DATA FROM TOOL
================================================================================
The fundamental_analysis_report tool returned the following data:

{{fund_data}}

================================================================================
3. FINANCIAL HEALTH ASSESSMENT
================================================================================
Based on the tool output above:
- Overall Financial Health: {{health}}
- Investment Assessment: {{assessment}}

================================================================================
4. KEY OBSERVATIONS
================================================================================
(Extracted from the tool output above)

The financial data shows the following key points:
- Revenue and profitability trends are visible in the tool output
- Balance sheet strength indicators are included
- Cash flow metrics provide liquidity insights

================================================================================
5. INVESTMENT RECOMMENDATION
================================================================================
Action: {{assessment}}

Rationale:
This recommendation is based on the financial metrics provided in Section 2.
The fundamental analysis tool has evaluated:
- Income statement metrics
- Balance sheet health
- Cash flow sustainability
- Key financial ratios

Supporting Evidence:
Please refer to Section 2 above for the complete financial data that supports
this recommendation. Key metrics from the tool output include revenue trends,
profitability margins, debt levels, and cash flow status.

================================================================================
6. RISK FACTORS
================================================================================
- Financial markets are subject to volatility
- Company-specific risks may exist
- Economic conditions affect all investments
- Past financial performance does not guarantee future results

================================================================================
7. DISCLAIMER
================================================================================
This analysis is based on historical financial data. Investors should conduct
their own due diligence and consider consulting a financial advisor.
'''

final_answer(report)
```

REQUIREMENTS:
1. Include the COMPLETE tool output in the report (Section 2)
2. Use numbered sections for clear organization
3. Do NOT use italic text
4. Use USD for currency values (never use $ symbol)
5. Make the connection between data and recommendation explicit
"""

MULTI_SECTOR_PROMPT = """Analyze multiple sectors and compare them.

SECTORS:
{sector_details}

TOOLS (call for each stock in each sector):
1. bollinger_fibonacci_analysis(symbol, period)
2. macd_donchian_analysis(symbol, period)
3. connors_zscore_analysis(symbol, period)
4. dual_moving_average_analysis(symbol, period)

REQUIRED CODE:
```python
import json
import re

sectors = {sectors_dict}
period = "{period}"

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

def count_buy_signals(results):
    count = 0
    for result in results.values():
        signal = get_signal(result)
        if "BUY" in signal:
            count += 1
    return count

# Collect data for all stocks in all sectors
all_data = {{}}
sector_summaries = {{}}

for sector_name, symbols_str in sectors.items():
    stock_list = [s.strip() for s in symbols_str.split(",")]
    all_data[sector_name] = {{}}
    sector_buy_total = 0
    sector_best_stock = None
    sector_best_count = -1
    
    for stock in stock_list:
        results = {{
            "bb": bollinger_fibonacci_analysis(symbol=stock, period=period),
            "macd": macd_donchian_analysis(symbol=stock, period=period),
            "connors": connors_zscore_analysis(symbol=stock, period=period),
            "dual_ma": dual_moving_average_analysis(symbol=stock, period=period),
        }}
        all_data[sector_name][stock] = results
        
        buy_count = count_buy_signals(results)
        sector_buy_total += buy_count
        if buy_count > sector_best_count:
            sector_best_count = buy_count
            sector_best_stock = stock
    
    avg_buy = sector_buy_total / len(stock_list) if stock_list else 0
    sector_summaries[sector_name] = {{
        "stocks": stock_list,
        "total_buy_signals": sector_buy_total,
        "avg_buy_signals": avg_buy,
        "best_stock": sector_best_stock,
        "best_stock_signals": sector_best_count,
        "outlook": "BULLISH" if avg_buy >= 2 else "NEUTRAL" if avg_buy >= 1 else "BEARISH"
    }}

# Rank sectors
ranked_sectors = sorted(sector_summaries.items(), key=lambda x: x[1]["avg_buy_signals"], reverse=True)

# Find top picks across all sectors
all_stocks_ranked = []
for sector_name, stocks_data in all_data.items():
    for stock, results in stocks_data.items():
        buy_count = count_buy_signals(results)
        all_stocks_ranked.append((stock, sector_name, buy_count))
all_stocks_ranked.sort(key=lambda x: x[2], reverse=True)

# Build report
report = f'''
MULTI-SECTOR ANALYSIS REPORT
Period: {{period}}

================================================================================
1. MULTI-SECTOR ANALYSIS OVERVIEW
================================================================================
Sectors analyzed: {{", ".join(sectors.keys())}}
Total stocks analyzed: {{sum(len(s["stocks"]) for s in sector_summaries.values())}}
Analysis period: {{period}}

================================================================================
2. SECTOR-BY-SECTOR RESULTS
================================================================================
'''

for i, (sector_name, summary) in enumerate(ranked_sectors, 1):
    report += f'''
2.{{i}} {{sector_name}}
    Stocks analyzed: {{", ".join(summary["stocks"])}}
    Total BUY signals: {{summary["total_buy_signals"]}}
    Average BUY signals per stock: {{summary["avg_buy_signals"]:.1f}}/4
    Best performer: {{summary["best_stock"]}} with {{summary["best_stock_signals"]}}/4 BUY signals
    Sector Outlook: {{summary["outlook"]}}
'''

report += '''

================================================================================
3. CROSS-SECTOR COMPARISON
================================================================================
| Rank | Sector | Stocks | Avg Buy Signals | Best Stock | Outlook |
|------|--------|--------|-----------------|------------|---------|
'''

for i, (sector_name, summary) in enumerate(ranked_sectors, 1):
    report += f"| {{i}} | {{sector_name}} | {{len(summary['stocks'])}} | {{summary['avg_buy_signals']:.1f}}/4 | {{summary['best_stock']}} | {{summary['outlook']}} |\\n"

report += f'''

================================================================================
4. TOP PICKS ACROSS ALL SECTORS
================================================================================
'''

for i, (stock, sector, buy_count) in enumerate(all_stocks_ranked[:5], 1):
    report += f'''
4.{{i}} {{stock}} ({{sector}})
    BUY signals: {{buy_count}}/4
    Recommendation: {{"STRONG BUY" if buy_count >= 3 else "BUY" if buy_count >= 2 else "HOLD"}}
'''

report += f'''

================================================================================
5. PORTFOLIO ALLOCATION BY SECTOR
================================================================================
Based on sector strength (higher allocation to stronger sectors):
'''

total_avg = sum(s["avg_buy_signals"] for s in sector_summaries.values())
for sector_name, summary in ranked_sectors:
    if total_avg > 0:
        allocation = (summary["avg_buy_signals"] / total_avg) * 100
    else:
        allocation = 100 / len(sector_summaries)
    report += f"- {{sector_name}}: {{allocation:.0f}}% allocation ({{summary['outlook']}} outlook)\\n"

report += f'''

================================================================================
6. OVERALL MARKET ASSESSMENT
================================================================================
Strongest Sector: {{ranked_sectors[0][0]}} with {{ranked_sectors[0][1]["avg_buy_signals"]:.1f}} avg BUY signals
Weakest Sector: {{ranked_sectors[-1][0]}} with {{ranked_sectors[-1][1]["avg_buy_signals"]:.1f}} avg BUY signals

Market Sentiment: {{"BULLISH" if sum(s["avg_buy_signals"] for s in sector_summaries.values()) / len(sector_summaries) >= 2 else "NEUTRAL" if sum(s["avg_buy_signals"] for s in sector_summaries.values()) / len(sector_summaries) >= 1 else "BEARISH"}}

================================================================================
7. STRATEGIC RECOMMENDATIONS
================================================================================
Primary Recommendation:
Focus on {{ranked_sectors[0][0]}} sector with strongest technical signals.
Best individual pick: {{all_stocks_ranked[0][0]}} from {{all_stocks_ranked[0][1]}} with {{all_stocks_ranked[0][2]}}/4 BUY signals.

Alternative Strategy:
Diversify across top 2-3 sectors with above-average signals.

================================================================================
8. DETAILED SECTOR DATA (Reference)
================================================================================
'''

for sector_name, stocks_data in all_data.items():
    report += f'''
--- {{sector_name}} ---
'''
    for stock, results in stocks_data.items():
        report += f'''
{{stock}}:
  BB-Fib Signal: {{get_signal(results["bb"])}}
  MACD Signal: {{get_signal(results["macd"])}}
  Connors Signal: {{get_signal(results["connors"])}}
  DualMA Signal: {{get_signal(results["dual_ma"])}}
'''

final_answer(report)
```

REQUIREMENTS:
1. Parse actual data from tool results
2. Use numbered sections for organization
3. Do NOT use italic text
4. Use USD for currency (never use $ symbol)
5. Show per-stock breakdown within each sector
6. Rank and recommend based on real metrics
7. Include reference data section for traceability
"""

# NOTE: In COMBINED_ANALYSIS_PROMPT, variables like {symbol}, {tech_period}, {fund_period}
# inside the code example must be escaped as {{symbol}}, {{tech_period}}, {{fund_period}}
# because this string uses .format() for technical_period and fundamental_period.
COMBINED_ANALYSIS_PROMPT = """Perform complete Technical + Fundamental analysis of {symbol}.

TOOLS TO CALL:
Technical (all 4 strategies):
1. bollinger_fibonacci_analysis(symbol="{symbol}", period="{technical_period}")
2. macd_donchian_analysis(symbol="{symbol}", period="{technical_period}")
3. connors_zscore_analysis(symbol="{symbol}", period="{technical_period}")
4. dual_moving_average_analysis(symbol="{symbol}", period="{technical_period}")

Fundamental:
5. fundamental_analysis_report(symbol="{symbol}", period="{fundamental_period}")

REQUIRED CODE:
```python
import json
import re

symbol = "{symbol}"
tech_period = "{technical_period}"
fund_period = "{fundamental_period}"

# Get technical analysis from all 4 strategies
bb_result = bollinger_fibonacci_analysis(symbol=symbol, period=tech_period)
macd_result = macd_donchian_analysis(symbol=symbol, period=tech_period)
connors_result = connors_zscore_analysis(symbol=symbol, period=tech_period)
dual_ma_result = dual_moving_average_analysis(symbol=symbol, period=tech_period)

# Get fundamental analysis
fund_result = fundamental_analysis_report(symbol=symbol, period=fund_period)

# Helper to extract signal
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

# Extract signals from each strategy
bb_signal = get_signal(bb_result)
macd_signal = get_signal(macd_result)
connors_signal = get_signal(connors_result)
dual_ma_signal = get_signal(dual_ma_result)
fund_signal = get_signal(fund_result)

# Count technical signals
tech_signals = [bb_signal, macd_signal, connors_signal, dual_ma_signal]
tech_buy = sum(1 for s in tech_signals if "BUY" in s)
tech_sell = sum(1 for s in tech_signals if "SELL" in s)
tech_hold = 4 - tech_buy - tech_sell

# Determine technical outlook
if tech_buy >= 3:
    tech_outlook = "BULLISH"
    tech_confidence = "HIGH"
elif tech_buy >= 2:
    tech_outlook = "MODERATELY BULLISH"
    tech_confidence = "MEDIUM"
elif tech_sell >= 3:
    tech_outlook = "BEARISH"
    tech_confidence = "HIGH"
elif tech_sell >= 2:
    tech_outlook = "MODERATELY BEARISH"
    tech_confidence = "MEDIUM"
else:
    tech_outlook = "NEUTRAL"
    tech_confidence = "LOW"

# Determine fundamental outlook
if "BUY" in fund_signal:
    fund_outlook = "POSITIVE"
elif "SELL" in fund_signal:
    fund_outlook = "NEGATIVE"
else:
    fund_outlook = "NEUTRAL"

# Check alignment
if (tech_buy >= 2 and "BUY" in fund_signal) or (tech_sell >= 2 and "SELL" in fund_signal):
    alignment = "YES"
    alignment_desc = "Technical and fundamental views are aligned"
elif (tech_buy >= 2 and "SELL" in fund_signal) or (tech_sell >= 2 and "BUY" in fund_signal):
    alignment = "NO"
    alignment_desc = "Technical and fundamental views are conflicting"
else:
    alignment = "PARTIAL"
    alignment_desc = "Mixed signals between technical and fundamental analysis"

# Final recommendation
if alignment == "YES" and tech_buy >= 2:
    final_rec = "BUY"
    final_confidence = "HIGH"
elif alignment == "YES" and tech_sell >= 2:
    final_rec = "SELL"
    final_confidence = "HIGH"
elif tech_buy >= 3:
    final_rec = "BUY"
    final_confidence = "MEDIUM"
elif tech_sell >= 3:
    final_rec = "SELL"
    final_confidence = "MEDIUM"
else:
    final_rec = "HOLD"
    final_confidence = "LOW"

# Build comprehensive report
report = f'''
{{symbol}} COMBINED INVESTMENT ANALYSIS REPORT
Technical Period: {{tech_period}} | Fundamental Period: {{fund_period}}

================================================================================
1. INVESTMENT ANALYSIS SUMMARY
================================================================================
Symbol: {{symbol}}
Technical Analysis Period: {{tech_period}}
Fundamental Analysis Period: {{fund_period}}
Final Recommendation: {{final_rec}}
Confidence Level: {{final_confidence}}

================================================================================
2. TECHNICAL ANALYSIS RESULTS
================================================================================

2.1 Strategy Signals Summary
| Strategy | Signal |
|----------|--------|
| Bollinger-Fibonacci | {{bb_signal}} |
| MACD-Donchian | {{macd_signal}} |
| Connors RSI-ZScore | {{connors_signal}} |
| Dual Moving Average | {{dual_ma_signal}} |

2.2 Technical Consensus
Signal Count: {{tech_buy}} BUY, {{tech_sell}} SELL, {{tech_hold}} HOLD
Technical Outlook: {{tech_outlook}}
Confidence Level: {{tech_confidence}}

2.3 Technical Tool Outputs (Supporting Data)

BOLLINGER-FIBONACCI OUTPUT:
{{bb_result}}

MACD-DONCHIAN OUTPUT:
{{macd_result}}

CONNORS RSI-ZSCORE OUTPUT:
{{connors_result}}

DUAL MOVING AVERAGE OUTPUT:
{{dual_ma_result}}

================================================================================
3. FUNDAMENTAL ANALYSIS RESULTS
================================================================================

3.1 Fundamental Outlook: {{fund_outlook}}
3.2 Fundamental Signal: {{fund_signal}}

3.3 Fundamental Tool Output (Supporting Data):
{{fund_result}}

================================================================================
4. ALIGNMENT ANALYSIS
================================================================================
4.1 Technical View: {{tech_outlook}} ({{tech_buy}}/4 strategies bullish)
4.2 Fundamental View: {{fund_outlook}}
4.3 Do They Align? {{alignment}}
4.4 Explanation: {{alignment_desc}}

================================================================================
5. INVESTMENT THESIS
================================================================================

5.1 Overall Recommendation: {{final_rec}}

5.2 Confidence Level: {{final_confidence}}

5.3 Supporting Evidence from Technical Analysis:
- {{tech_buy}} out of 4 technical strategies signal buying opportunity
- Bollinger-Fibonacci: {{bb_signal}}
- MACD-Donchian: {{macd_signal}}
- Connors RSI-ZScore: {{connors_signal}}
- Dual Moving Average: {{dual_ma_signal}}

5.4 Supporting Evidence from Fundamental Analysis:
- Fundamental analysis indicates {{fund_outlook}} outlook
- See Section 3.3 for detailed financial metrics

5.5 Investment Rationale:
The {{final_rec}} recommendation is based on:
- Technical consensus: {{tech_outlook}} with {{tech_confidence}} confidence
- Fundamental outlook: {{fund_outlook}}
- Alignment status: {{alignment}} - {{alignment_desc}}

================================================================================
6. RISK ASSESSMENT
================================================================================

6.1 Technical Risks:
- {{4 - max(tech_buy, tech_sell)}}/4 strategies show conflicting signals
- Market conditions may change rapidly
- Technical indicators are lagging by nature

6.2 Fundamental Risks:
- Past financial performance does not guarantee future results
- Market and economic conditions affect fundamentals
- Industry-specific risks may apply

6.3 Conditions That Would Invalidate This Recommendation:
- Technical: If {{3 - tech_buy if tech_buy >= 2 else 3 - tech_sell}} more strategies flip to opposite signal
- Fundamental: Significant change in company financials
- Market: Major market correction or sector rotation

================================================================================
7. CONCLUSION
================================================================================
Based on comprehensive analysis of both technical indicators and fundamental data,
the recommendation for {{symbol}} is {{final_rec}} with {{final_confidence}} confidence.

Technical analysis shows {{tech_outlook}} sentiment with {{tech_buy}}/4 bullish signals.
Fundamental analysis indicates {{fund_outlook}} financial health.
Views are {{alignment.lower()}} aligned: {{alignment_desc}}

This recommendation should be considered alongside personal risk tolerance and
investment objectives. Always conduct additional due diligence before investing.
'''

final_answer(report)
```

REQUIREMENTS:
1. Extract actual metrics from all 5 tool results
2. Include COMPLETE tool outputs as supporting evidence
3. Use numbered sections for clear organization
4. Do NOT use italic text (no asterisks)
5. Use USD for currency values (never use $ symbol)
6. Explicitly analyze whether technical and fundamental views align
7. Provide specific, data-backed reasoning for recommendation
8. Make the report fully traceable - every conclusion must reference data
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
) -> str:
    """
    Run technical analysis using 4 individual strategy tools.
    
    CodeAgent approach: LLM writes Python code to call and combine all 4 tools.
    """
    configure_finance_tools()
    
    model = build_model(
        model_id=model_id,
        provider=model_provider,
        api_key=openai_api_key,
        hf_token=hf_token,
        api_base=openai_base_url,
    )
    
    agent = build_agent(model, LOW_LEVEL_TOOLS, max_steps=max_steps, executor_type=executor_type)
    
    prompt = TECHNICAL_ANALYSIS_PROMPT.format(symbol=symbol, period=period)
    
    return agent.run(prompt)


def run_market_scanner(
    symbols: str,
    period: str = "1y",
    model_id: str = DEFAULT_MODEL_ID,
    model_provider: str = DEFAULT_MODEL_PROVIDER,
    openai_api_key: Optional[str] = None,
    hf_token: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    max_steps: int = 30,  # More steps for loops
    executor_type: Literal["local", "e2b", "docker"] = "local",
) -> str:
    """
    Run market scanner using loops over individual strategy tools.
    
    CodeAgent approach: LLM writes Python loops to iterate over stocks and strategies.
    """
    configure_finance_tools()
    
    model = build_model(
        model_id=model_id,
        provider=model_provider,
        api_key=openai_api_key,
        hf_token=hf_token,
        api_base=openai_base_url,
    )
    
    agent = build_agent(model, LOW_LEVEL_TOOLS, max_steps=max_steps, executor_type=executor_type)
    
    # Parse symbols for the prompt
    symbol_list = [s.strip() for s in symbols.split(",")]
    
    prompt = MARKET_SCANNER_PROMPT.format(
        symbols=symbols,
        symbol_list=symbol_list,
        period=period,
    )
    
    return agent.run(prompt)


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
) -> str:
    """
    Run fundamental analysis using fundamental_analysis_report tool.
    
    CodeAgent approach: Simple single tool call with interpretation.
    """
    configure_finance_tools()
    
    model = build_model(
        model_id=model_id,
        provider=model_provider,
        api_key=openai_api_key,
        hf_token=hf_token,
        api_base=openai_base_url,
    )
    
    agent = build_agent(model, LOW_LEVEL_TOOLS, max_steps=max_steps, executor_type=executor_type)
    
    prompt = FUNDAMENTAL_ANALYSIS_PROMPT.format(symbol=symbol, period=period)
    
    return agent.run(prompt)


def run_multi_sector_analysis(
    sectors: Dict[str, str],
    period: str = "1y",
    model_id: str = DEFAULT_MODEL_ID,
    model_provider: str = DEFAULT_MODEL_PROVIDER,
    openai_api_key: Optional[str] = None,
    hf_token: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    max_steps: int = 50,  # Many steps for nested loops
    executor_type: Literal["local", "e2b", "docker"] = "local",
) -> str:
    """
    Run multi-sector analysis using nested loops over tools.
    
    CodeAgent approach: LLM writes nested loops (sector -> stock -> strategy).
    """
    configure_finance_tools()
    
    model = build_model(
        model_id=model_id,
        provider=model_provider,
        api_key=openai_api_key,
        hf_token=hf_token,
        api_base=openai_base_url,
    )
    
    agent = build_agent(model, LOW_LEVEL_TOOLS, max_steps=max_steps, executor_type=executor_type)
    
    # Format for prompt
    sector_details = "\n".join([
        f"- {name}: {symbols}"
        for name, symbols in sectors.items()
    ])
    
    prompt = MULTI_SECTOR_PROMPT.format(
        sector_details=sector_details,
        sectors_dict=sectors,
        period=period,
    )
    
    return agent.run(prompt)


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
) -> str:
    """
    Run combined technical + fundamental analysis.
    
    CodeAgent approach: LLM writes code to call all 5 tools and synthesize.
    """
    configure_finance_tools()
    
    model = build_model(
        model_id=model_id,
        provider=model_provider,
        api_key=openai_api_key,
        hf_token=hf_token,
        api_base=openai_base_url,
    )
    
    agent = build_agent(model, LOW_LEVEL_TOOLS, max_steps=max_steps, executor_type=executor_type)
    
    prompt = COMBINED_ANALYSIS_PROMPT.format(
        symbol=symbol,
        technical_period=technical_period,
        fundamental_period=fundamental_period,
    )
    
    return agent.run(prompt)


# ===========================================================================
# CLI Entry Point
# ===========================================================================

def main():
    """CLI entry point for CodeAgent analysis."""
    parser = argparse.ArgumentParser(
        description="CodeAgent Stock Analysis (LOW-LEVEL tools with Python orchestration)"
    )
    parser.add_argument("symbol", help="Stock symbol or comma-separated symbols")
    parser.add_argument("--mode", choices=["technical", "scanner", "fundamental", "combined"],
                        default="technical", help="Analysis mode")
    parser.add_argument("--period", default="1y", help="Analysis period")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--model-provider", default=DEFAULT_MODEL_PROVIDER)
    parser.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS)
    parser.add_argument("--executor", choices=["local", "e2b", "docker"],
                        default=DEFAULT_EXECUTOR, help="Code executor type")
    
    args = parser.parse_args()
    
    try:
        if args.mode == "technical":
            result = run_technical_analysis(
                symbol=args.symbol,
                period=args.period,
                model_id=args.model_id,
                model_provider=args.model_provider,
                max_steps=args.max_steps,
                executor_type=args.executor,
            )
        elif args.mode == "scanner":
            result = run_market_scanner(
                symbols=args.symbol,
                period=args.period,
                model_id=args.model_id,
                model_provider=args.model_provider,
                max_steps=args.max_steps,
                executor_type=args.executor,
            )
        elif args.mode == "fundamental":
            result = run_fundamental_analysis(
                symbol=args.symbol,
                period=args.period,
                model_id=args.model_id,
                model_provider=args.model_provider,
                max_steps=args.max_steps,
                executor_type=args.executor,
            )
        elif args.mode == "combined":
            result = run_combined_analysis(
                symbol=args.symbol,
                technical_period=args.period,
                model_id=args.model_id,
                model_provider=args.model_provider,
                max_steps=args.max_steps,
                executor_type=args.executor,
            )
        
        print(result)
        
    finally:
        shutdown_finance_tools()


if __name__ == "__main__":
    main()