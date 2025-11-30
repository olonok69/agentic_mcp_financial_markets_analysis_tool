"""
CodeAgent implementation using LOW-LEVEL granular MCP tools.

#####################################################################
# CODEAGENT APPROACH
#####################################################################
#
# This agent uses LOW-LEVEL tools and writes Python code to orchestrate them.
# The LLM generates executable code that loops, combines, and analyzes.
#
# TOOLS USED:
#   - bollinger_fibonacci_analysis: Single strategy, single stock
#   - macd_donchian_analysis: Single strategy, single stock
#   - connors_zscore_analysis: Single strategy, single stock
#   - dual_moving_average_analysis: Single strategy, single stock
#   - fundamental_analysis_report: Financial data extraction
#
# ADVANTAGES:
#   - Flexible: LLM can customize analysis logic
#   - Efficient loops: One code block handles N stocks
#   - Transparent: See exactly what code runs
#
# COMPARISON WITH ToolCallingAgent:
#   - ToolCallingAgent: "Give me everything for AAPL" → 1 call
#   - CodeAgent: "Let me call 4 tools and combine results" → 4+ calls
#     BUT for multi-stock: CodeAgent writes efficient loops
#
#####################################################################
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, Literal, Optional

from dotenv import load_dotenv
from smolagents import LiteLLMModel, InferenceClientModel, CodeAgent

from .tools import (
    LOW_LEVEL_TOOLS,
    configure_finance_tools,
    shutdown_finance_tools,
)

load_dotenv()

# Default configuration
DEFAULT_MODEL_ID = os.getenv("SMOLAGENT_MODEL_ID", "gpt-4o")
DEFAULT_MODEL_PROVIDER = os.getenv("SMOLAGENT_MODEL_PROVIDER", "litellm")
DEFAULT_MAX_STEPS = int(os.getenv("SMOLAGENT_MAX_STEPS", "20"))  # CodeAgent needs more steps
DEFAULT_EXECUTOR = os.getenv("SMOLAGENT_EXECUTOR", "local")  # local, e2b, docker

__all__ = [
    "DEFAULT_MODEL_ID",
    "DEFAULT_MODEL_PROVIDER",
    "DEFAULT_MAX_STEPS",
    "DEFAULT_EXECUTOR",
    "build_model",
    "build_agent",
    "run_technical_analysis",
    "run_market_scanner",
    "run_fundamental_analysis",
    "run_multi_sector_analysis",
    "run_combined_analysis",
]


# ===========================================================================
# Model & Agent Builders
# ===========================================================================

def build_model(
    model_id: str = DEFAULT_MODEL_ID,
    provider: str = DEFAULT_MODEL_PROVIDER,
    api_key: Optional[str] = None,
    hf_token: Optional[str] = None,
    api_base: Optional[str] = None,
):
    """Create the LLM model instance."""
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

# Call all 4 strategies
bb_result = bollinger_fibonacci_analysis(symbol="{symbol}", period="{period}")
macd_result = macd_donchian_analysis(symbol="{symbol}", period="{period}")
connors_result = connors_zscore_analysis(symbol="{symbol}", period="{period}")
dual_ma_result = dual_moving_average_analysis(symbol="{symbol}", period="{period}")

# Parse results - each result is a string, may contain JSON or text
# Extract key metrics: signal, score, return %, win rate, etc.

# Count signals
buy_count = 0
sell_count = 0
hold_count = 0

# Parse each result and extract data
# Look for patterns like "Signal: BUY", "Return: +5.2%", etc.

# Build report with actual data
report = f'''
{symbol} Technical Analysis
Period: {period}

Strategy Results Summary

| Strategy | Signal | Return | Score | Key Metric |
|----------|--------|--------|-------|------------|
| Bollinger-Fibonacci | [signal from bb_result] | [%] | [score] | [level/band] |
| MACD-Donchian | [signal from macd_result] | [%] | [score] | [MACD value] |
| Connors RSI + Z-Score | [signal from connors_result] | [%] | [score] | [RSI/ZScore] |
| Dual Moving Average | [signal from dual_ma_result] | [%] | [score] | [trend] |

Signal Consensus: X BUY, Y SELL, Z HOLD

Detailed Analysis

Bollinger Bands & Fibonacci:
[Extract key details from bb_result]

MACD-Donchian:
[Extract key details from macd_result]

Connors RSI + Z-Score:
[Extract key details from connors_result]

Dual Moving Average:
[Extract key details from dual_ma_result]

Overall Recommendation
[Based on signal consensus and metrics, provide recommendation]
'''

final_answer(report)
```

CRITICAL REQUIREMENTS:
1. EXTRACT actual numbers from tool results - do not make up data
2. Use markdown tables with | separators (they render properly)
3. Include specific metrics: returns, win rates, scores, signal values
4. Show the raw data that supports your recommendation
5. Do NOT use uppercase section headers - use normal case with line breaks

Write complete code that parses the tool outputs and builds a data-rich report.
"""

# NOTE: In MARKET_SCANNER_PROMPT, all occurrences of {stock} must be escaped as {{stock}}
# because this string uses .format() for symbols, symbol_list, and period.
# Single braces like {stock} would cause KeyError during formatting.
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

# Collect all results
all_data = {{}}
for stock in stocks:
    all_data[stock] = {{
        "bb": bollinger_fibonacci_analysis(symbol=stock, period=period),
        "macd": macd_donchian_analysis(symbol=stock, period=period),
        "connors": connors_zscore_analysis(symbol=stock, period=period),
        "dual_ma": dual_moving_average_analysis(symbol=stock, period=period),
    }}

# Parse results and extract metrics for each stock
# Look for: Signal (BUY/SELL/HOLD), Return %, Score, Win Rate
# Build a summary dict for each stock

stock_summaries = {{}}
for stock, results in all_data.items():
    # Parse each strategy result to extract signal and metrics
    # Count buy/sell/hold signals
    # Calculate average score or opportunity metric
    stock_summaries[stock] = {{
        "signals": [],
        "buy_count": 0,
        "avg_return": 0,
        "score": 0,
    }}

# Rank stocks by opportunity (buy signals, returns, etc.)
ranked = sorted(stock_summaries.items(), key=lambda x: x[1]["buy_count"], reverse=True)

# Build report with ACTUAL DATA
report = f'''
Market Scanner Results
Stocks: {{", ".join(stocks)}} | Period: {{period}}

Rankings by Technical Opportunity

| Rank | Symbol | Buy Signals | Avg Return | Score | Recommendation |
|------|--------|-------------|------------|-------|----------------|
'''

for i, (stock, data) in enumerate(ranked, 1):
    report += f"| {{i}} | {{stock}} | {{data['buy_count']}}/4 | {{data['avg_return']}}% | {{data['score']}} | [rec] |\\n"

report += '''

Individual Stock Analysis
'''

for stock in stocks:
    results = all_data[stock]
    report += f'''
{{stock}}:

| Strategy | Signal | Return | Key Metric |
|----------|--------|--------|------------|
| Bollinger-Fib | [from bb] | [%] | [score/level] |
| MACD-Donchian | [from macd] | [%] | [MACD value] |
| Connors-ZScore | [from connors] | [%] | [RSI/ZScore] |
| Dual MA | [from dual_ma] | [%] | [trend] |

'''

report += '''
Market Assessment
[Based on the actual data above, summarize market conditions]

Top Picks: [list best opportunities with reasoning based on data]
'''

final_answer(report)
```

CRITICAL REQUIREMENTS:
1. EXTRACT actual data from each tool result - parse the strings for numbers
2. Use markdown tables with proper | formatting
3. Show individual stock breakdowns with real metrics
4. Rank based on actual signals and returns, not made-up scores
5. Use normal case headers (not UPPERCASE)

Write complete code that extracts real data and builds an informative comparison.
"""

FUNDAMENTAL_ANALYSIS_PROMPT = """Analyze {symbol} fundamentals.

TOOL TO CALL:
fundamental_analysis_report(symbol="{symbol}", period="{period}")

REQUIRED CODE:
```python
# Get fundamental analysis
fund_data = fundamental_analysis_report(symbol="{symbol}", period="{period}")

# The tool returns detailed financial data
# Present it clearly with proper formatting

report = f'''
{symbol} Fundamental Analysis
Period: {period}

Financial Overview:
{{fund_data}}

Investment Assessment:
Based on the financial metrics above, here is my assessment:
[Your interpretation of the key metrics - profitability, growth, debt, valuation]

Key Strengths:
- [Based on actual data above]

Key Risks:
- [Based on actual data above]

Recommendation:
[Your recommendation with specific references to the metrics]
'''

final_answer(report)
```

Present the fundamental data clearly. The tool already provides structured output - display it properly.
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

# Collect data for all stocks in all sectors
all_data = {{}}
sector_scores = {{}}

for sector_name, symbols_str in sectors.items():
    stock_list = [s.strip() for s in symbols_str.split(",")]
    all_data[sector_name] = {{}}
    
    for stock in stock_list:
        all_data[sector_name][stock] = {{
            "bb": bollinger_fibonacci_analysis(symbol=stock, period=period),
            "macd": macd_donchian_analysis(symbol=stock, period=period),
            "connors": connors_zscore_analysis(symbol=stock, period=period),
            "dual_ma": dual_moving_average_analysis(symbol=stock, period=period),
        }}
    
    # Calculate sector average metrics
    # Parse results and compute buy signal counts, average returns, etc.

# Build detailed report
report = '''
Multi-Sector Analysis Report
Period: ''' + period + '''

Sector Comparison Summary

| Sector | Stocks | Avg Buy Signals | Best Stock | Sector Outlook |
|--------|--------|-----------------|------------|----------------|
'''

for sector_name in sectors.keys():
    # Add row with actual data from parsing
    report += f"| {{sector_name}} | [count] | [X/4] | [best] | [outlook] |\\n"

report += '''

Detailed Sector Analysis
'''

for sector_name, stocks_data in all_data.items():
    report += f'''
--- {{sector_name}} ---

| Stock | BB-Fib | MACD | Connors | DualMA | Consensus |
|-------|--------|------|---------|--------|-----------|
'''
    for stock, results in stocks_data.items():
        # Extract signals from each result
        report += f"| {{stock}} | [sig] | [sig] | [sig] | [sig] | [X/4] |\\n"

report += '''

Cross-Sector Recommendations

Top Picks Overall:
1. [Stock] (Sector) - [reasoning with data]
2. [Stock] (Sector) - [reasoning with data]
3. [Stock] (Sector) - [reasoning with data]

Portfolio Allocation Suggestion:
[Based on sector strength analysis]
'''

final_answer(report)
```

REQUIREMENTS:
1. Parse actual data from tool results
2. Use markdown tables for readability
3. Show per-stock breakdown within each sector
4. Rank and recommend based on real metrics
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

# Parse all results and extract key metrics
# Technical: signals, returns, scores
# Fundamental: revenue, margins, growth, ratios

# Build combined report
report = f'''
{{symbol}} Combined Analysis
Technical Period: {{tech_period}} | Fundamental Period: {{fund_period}}

TECHNICAL ANALYSIS

Strategy Summary

| Strategy | Signal | Return | Score |
|----------|--------|--------|-------|
| Bollinger-Fibonacci | [from bb_result] | [%] | [score] |
| MACD-Donchian | [from macd_result] | [%] | [score] |
| Connors RSI + Z-Score | [from connors_result] | [%] | [score] |
| Dual Moving Average | [from dual_ma_result] | [%] | [score] |

Technical Consensus: [X BUY / Y SELL / Z HOLD]
Technical Outlook: [BULLISH/BEARISH/NEUTRAL based on signals]

FUNDAMENTAL ANALYSIS

{{fund_result}}

Key Financial Metrics:
[Extract and highlight the most important metrics]

ALIGNMENT ANALYSIS

Technical View: [Summary]
Fundamental View: [Summary]
Agreement: [YES/NO/PARTIAL] - [Explanation]

INVESTMENT THESIS

[Synthesize both analyses into clear recommendation]
- Entry strategy: [if bullish]
- Risk factors: [from both analyses]
- Conviction level: [HIGH/MEDIUM/LOW]

Final Recommendation: [BUY/HOLD/SELL] with [X]% confidence
'''

final_answer(report)
```

REQUIREMENTS:
1. Extract actual metrics from all 5 tool results
2. Use markdown tables for clear presentation
3. Explicitly analyze whether technical and fundamental views align
4. Provide specific, data-backed reasoning for recommendation
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
        f"- **{name}**: {symbols}"
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
                        default=DEFAULT_EXECUTOR, help="Code execution environment")
    
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