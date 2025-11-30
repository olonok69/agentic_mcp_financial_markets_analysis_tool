"""
Smolagents-powered stock analyzer using CodeAgent for better tool orchestration.

This module uses CodeAgent instead of ToolCallingAgent, allowing the LLM to write
Python code to call tools. This provides:
- Better composability (loops, conditionals)
- More efficient multi-tool calls
- Natural code-based reasoning

Analysis types:
1. Technical Analysis - Single stock, multiple strategies
2. Market Scanner - Multiple stocks comparison
3. Fundamental Analysis - Financial statements interpretation
4. Multi-Sector Analysis - Cross-sector comparison
5. Combined Analysis - Technical + Fundamental

Reference: https://huggingface.co/docs/smolagents/tutorials/secure_code_execution
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Literal

from dotenv import load_dotenv
from smolagents import CodeAgent, LiteLLMModel, InferenceClientModel

# Support running either as a package module or as a standalone script.
if __package__ in (None, ""):
    import sys
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from stock_analyzer_bot.tools import (
        STRATEGY_TOOLS,
        ALL_TOOLS,
        configure_finance_tools,
        shutdown_finance_tools,
        fundamental_analysis_report,
    )
else:
    from .tools import (
        STRATEGY_TOOLS,
        ALL_TOOLS,
        configure_finance_tools,
        shutdown_finance_tools,
        fundamental_analysis_report,
    )

load_dotenv()

# Defaults - prefer OpenAI for reliability with CodeAgent
DEFAULT_MODEL_ID = os.getenv("SMOLAGENT_MODEL_ID", "gpt-4o")
DEFAULT_MODEL_PROVIDER = os.getenv("SMOLAGENT_MODEL_PROVIDER", "litellm")
DEFAULT_MAX_STEPS = int(os.getenv("SMOLAGENT_MAX_STEPS", "20"))

# Executor type: "local", "e2b", or "docker"
DEFAULT_EXECUTOR = os.getenv("SMOLAGENT_EXECUTOR", "local")


# =============================================================================
# PROMPT TEMPLATES FOR CODEAGENT
# =============================================================================
# CodeAgent prompts are designed for the LLM to write Python code that calls tools.
# The LLM will write code like:
#   result = bollinger_fibonacci_analysis(symbol="AAPL", period="1y")
#   print(result)
# =============================================================================

TECHNICAL_ANALYSIS_PROMPT = """You are a senior quantitative analyst. Your task is to analyze {symbol} stock using 4 technical strategy tools.

## Available Tools
You have access to these 4 strategy analysis tools:
1. `bollinger_fibonacci_analysis(symbol, period)` - Bollinger Bands + Fibonacci retracement
2. `macd_donchian_analysis(symbol, period)` - MACD momentum + Donchian channel breakouts
3. `connors_zscore_analysis(symbol, period)` - Connors RSI + Z-Score mean reversion
4. `dual_moving_average_analysis(symbol, period)` - 50/200 EMA crossover (Golden/Death Cross)

## Instructions
1. Call ALL 4 tools with symbol="{symbol}" and period="{period}"
2. Store results in a dictionary for easy access
3. Extract key metrics: signal, score, return %, Sharpe ratio, max drawdown
4. Count buy/sell/hold signals for consensus
5. Generate a comprehensive markdown report

## Code Strategy
Write Python code that:
```python
# Call all 4 strategies and collect results
results = {{}}
results["bollinger_fib"] = bollinger_fibonacci_analysis(symbol="{symbol}", period="{period}")
results["macd_donchian"] = macd_donchian_analysis(symbol="{symbol}", period="{period}")
results["connors_zscore"] = connors_zscore_analysis(symbol="{symbol}", period="{period}")
results["dual_ma"] = dual_moving_average_analysis(symbol="{symbol}", period="{period}")

# Analyze the results and create report
# ... your analysis code ...

final_answer(report)
```

## Required Report Format

Your final_answer MUST be a complete markdown report starting with:

# {symbol} Comprehensive Technical Analysis
*Analysis Date: [today's date]*

## Executive Summary
[2-3 paragraph overview synthesizing all strategy findings]

## Strategy Performance Summary

| Strategy | Signal | Score | Return | vs B&H | Sharpe | Max DD |
|----------|--------|-------|--------|--------|--------|--------|
| Bollinger-Fib | [signal] | [score] | [%] | [%] | [ratio] | [%] |
| MACD-Donchian | [signal] | [score] | [%] | [%] | [ratio] | [%] |
| Connors-ZScore | [signal] | [score] | [%] | [%] | [ratio] | [%] |
| Dual MA | [signal] | [score] | [%] | [%] | [ratio] | [%] |

## Signal Consensus
[X/4 strategies signal BUY, Y/4 signal SELL, Z/4 signal HOLD]

## Individual Strategy Analysis
[Detailed breakdown of each strategy with key insights]

## Risk Assessment
[Volatility analysis, max drawdown concerns, position sizing suggestions]

## Final Recommendation: **[BUY/HOLD/SELL]**

### Entry Strategy
[Specific entry points, stop loss levels]

### Risk Management
[Position sizing, stop loss placement]

*This analysis is for educational purposes only.*

---

IMPORTANT: Your final_answer must be the COMPLETE markdown report, not just a summary.
"""


MARKET_SCANNER_PROMPT = """You are a senior portfolio strategist analyzing multiple stocks for investment opportunities.

## Your Task
Scan these stocks: {symbols}
Period: {period}

## Available Tools
For EACH stock, use these 4 strategy tools:
1. `bollinger_fibonacci_analysis(symbol, period)`
2. `macd_donchian_analysis(symbol, period)`
3. `connors_zscore_analysis(symbol, period)`
4. `dual_moving_average_analysis(symbol, period)`

## Code Strategy
Write efficient Python code using loops:

```python
symbols = "{symbols}".split(",")
all_results = {{}}

for symbol in symbols:
    symbol = symbol.strip()
    all_results[symbol] = {{
        "bollinger_fib": bollinger_fibonacci_analysis(symbol=symbol, period="{period}"),
        "macd_donchian": macd_donchian_analysis(symbol=symbol, period="{period}"),
        "connors_zscore": connors_zscore_analysis(symbol=symbol, period="{period}"),
        "dual_ma": dual_moving_average_analysis(symbol=symbol, period="{period}"),
    }}

# Analyze and rank stocks
# ... your ranking logic ...

final_answer(report)
```

## Required Report Format

# Multi-Stock Market Analysis Report
*Analysis Date: [date]*
*Stocks Analyzed: {symbols}*

## Executive Summary
[Key findings across all stocks]

## Performance Ranking

| Rank | Symbol | Consensus | Avg Return | Best Strategy | Risk Level | Action |
|------|--------|-----------|------------|---------------|------------|--------|
| 1 | [SYM] | [X/4 BUY] | [%] | [strategy] | [Low/Med/High] | [BUY] |
| 2 | [SYM] | [X/4 BUY] | [%] | [strategy] | [Low/Med/High] | [HOLD] |
| ... | ... | ... | ... | ... | ... | ... |

## Top Opportunities
### 🟢 Strong BUY
[Stocks with 3-4 BUY signals]

### 🟡 Moderate BUY / HOLD
[Stocks with mixed signals]

### 🔴 AVOID
[Stocks with SELL signals]

## Individual Stock Breakdown
[Brief analysis of each stock]

## Portfolio Recommendations
[Suggested allocation, diversification notes]

*This analysis is for educational purposes only.*
"""


FUNDAMENTAL_ANALYSIS_PROMPT = """You are a senior fundamental analyst creating an investment thesis.

## Your Task
Analyze {symbol}'s fundamentals using the fundamental_analysis_report tool.

## Available Tool
`fundamental_analysis_report(symbol, period)` - Returns comprehensive financial data

## Code Strategy
```python
# Get fundamental data
fundamentals = fundamental_analysis_report(symbol="{symbol}", period="{period}")

# Parse and analyze the data
# Create comprehensive report

final_answer(report)
```

## Required Report Format

# {symbol} Fundamental Analysis Report
*Analysis Date: [date]*
*Data Period: {period}*

## Executive Summary
[Investment thesis - 2-3 paragraphs]

## Key Metrics

| Metric | Value | Assessment |
|--------|-------|------------|
| Revenue | $[X] | [trend] |
| Net Income | $[X] | [trend] |
| Net Margin | [%] | [healthy/weak] |
| Debt-to-Equity | [X] | [conservative/aggressive] |
| Current Ratio | [X] | [liquid/illiquid] |
| Free Cash Flow | $[X] | [positive/negative] |

## Income Statement Analysis
[Revenue trends, profitability]

## Balance Sheet Strength
[Assets, liabilities, leverage]

## Cash Flow Analysis
[Operating CF, Free CF, capital allocation]

## Investment Assessment
### Strengths
- [Point 1]
- [Point 2]

### Risks
- [Risk 1]
- [Risk 2]

## Final Recommendation: **[BUY/HOLD/SELL]**
[Rationale and suitable investor profile]

*This analysis is for educational purposes only.*
"""


MULTI_SECTOR_ANALYSIS_PROMPT = """You are a senior portfolio strategist analyzing multiple sectors.

## Your Task
Analyze these sectors:
{sectors_formatted}

Period: {period}
Total stocks: {total_stocks}

## Available Tools
For EACH stock, use these 4 strategy tools:
1. `bollinger_fibonacci_analysis(symbol, period)`
2. `macd_donchian_analysis(symbol, period)`
3. `connors_zscore_analysis(symbol, period)`
4. `dual_moving_average_analysis(symbol, period)`

## Code Strategy
Use nested loops for efficient analysis:

```python
sectors = {{
{sectors_dict}
}}

all_results = {{}}
for sector_name, symbols in sectors.items():
    all_results[sector_name] = {{}}
    for symbol in symbols:
        all_results[sector_name][symbol] = {{
            "bollinger_fib": bollinger_fibonacci_analysis(symbol=symbol, period="{period}"),
            "macd_donchian": macd_donchian_analysis(symbol=symbol, period="{period}"),
            "connors_zscore": connors_zscore_analysis(symbol=symbol, period="{period}"),
            "dual_ma": dual_moving_average_analysis(symbol=symbol, period="{period}"),
        }}

# Cross-sector analysis and ranking
# ... analysis code ...

final_answer(report)
```

## Required Report Format

# Multi-Sector Market Analysis Report
*Analysis Date: [date]*

## Executive Summary
[Cross-sector insights, market themes]

## Cross-Sector Performance Overview

| Sector | Top Pick | Avg Signal | Best Return | Recommendation |
|--------|----------|------------|-------------|----------------|
| [Sector1] | [SYM] | [X/4 BUY] | [%] | [Overweight/Neutral/Underweight] |

## Sector Rankings
1. **[Best Sector]** - [Why]
2. **[Second]** - [Why]
...

## Priority Investment Recommendations
### 🥇 Top 3 Picks Across All Sectors
1. [Symbol] ([Sector]) - [Rationale]
2. [Symbol] ([Sector]) - [Rationale]
3. [Symbol] ([Sector]) - [Rationale]

## Sector-by-Sector Analysis
[Detailed breakdown of each sector]

## Portfolio Construction
[Suggested allocation across sectors]

*This analysis is for educational purposes only.*
"""


COMBINED_ANALYSIS_PROMPT = """You are a senior investment analyst combining Technical and Fundamental analysis.

## Philosophy
- Fundamental Analysis = "WHAT to buy" (company quality, intrinsic value)
- Technical Analysis = "WHEN to buy" (timing, entry/exit points)
- Combined = 360-degree investment view

## Your Task
Analyze {symbol} using BOTH approaches:
- Technical: {technical_period} period
- Fundamental: {fundamental_period} period

## Available Tools
Technical (4 tools):
1. `bollinger_fibonacci_analysis(symbol, period)`
2. `macd_donchian_analysis(symbol, period)`
3. `connors_zscore_analysis(symbol, period)`
4. `dual_moving_average_analysis(symbol, period)`

Fundamental (1 tool):
5. `fundamental_analysis_report(symbol, period)`

## Code Strategy
```python
# Get fundamental data first
fundamentals = fundamental_analysis_report(symbol="{symbol}", period="{fundamental_period}")

# Get all technical data
technical = {{
    "bollinger_fib": bollinger_fibonacci_analysis(symbol="{symbol}", period="{technical_period}"),
    "macd_donchian": macd_donchian_analysis(symbol="{symbol}", period="{technical_period}"),
    "connors_zscore": connors_zscore_analysis(symbol="{symbol}", period="{technical_period}"),
    "dual_ma": dual_moving_average_analysis(symbol="{symbol}", period="{technical_period}"),
}}

# Analyze alignment between FA and TA
# ... your synthesis logic ...

final_answer(report)
```

## Required Report Format

# {symbol} Combined Investment Analysis
*Analysis Date: [date]*

## Executive Summary
[Synthesized view combining FA + TA findings]

## Signal Alignment Analysis

| Aspect | Fundamental View | Technical View | Alignment |
|--------|-----------------|----------------|-----------|
| Overall | [Bullish/Bearish] | [Bullish/Bearish] | [✅ Aligned / ⚠️ Divergent] |
| Timing | N/A | [Good/Poor entry] | - |
| Risk | [Low/Med/High] | [Low/Med/High] | [Match?] |

**Alignment Status**: [ALIGNED / DIVERGENT]
- If ALIGNED → High conviction opportunity
- If DIVERGENT → Proceed with caution

## Fundamental Analysis Summary
[Key financial metrics, strengths, risks]

## Technical Analysis Summary
[Strategy signals, consensus, key levels]

## Combined Recommendation

### For Long-Term Investors (FA-focused)
[Recommendation based on fundamentals]

### For Swing Traders (TA-focused)
[Recommendation based on technicals]

### Optimal Strategy
[Entry points, position sizing, stop loss]

## Final Verdict: **[STRONG BUY / BUY / HOLD / SELL / STRONG SELL]**
[Comprehensive rationale combining both perspectives]

*This analysis is for educational purposes only.*
"""


# =============================================================================
# MODEL AND AGENT BUILDERS
# =============================================================================

def _resolve_provider(model_id: str, requested_provider: str) -> str:
    """Determine the actual provider based on model_id pattern."""
    if requested_provider not in ("auto", ""):
        return requested_provider
    # HuggingFace model IDs contain a slash (org/model)
    return "inference" if "/" in model_id else "litellm"


def build_model(
    model_id: str,
    provider: str,
    hf_token: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    openai_base_url: Optional[str] = None,
):
    """Build the appropriate model based on provider."""
    resolved = _resolve_provider(model_id, provider)
    
    if resolved == "inference":
        return InferenceClientModel(
            model_id=model_id,
            token=hf_token or os.getenv("HF_TOKEN"),
        )
    
    if resolved == "litellm":
        return LiteLLMModel(
            model_id=model_id,
            api_key=openai_api_key or os.getenv("OPENAI_API_KEY"),
            api_base=openai_base_url or os.getenv("OPENAI_BASE_URL"),
        )
    
    raise ValueError(f"Unsupported provider: {resolved}")


def build_agent(
    model,
    tools: list,
    max_steps: int = 20,
    executor_type: Literal["local", "e2b", "docker"] = "local",
):
    """
    Build a CodeAgent with the given model and tools.
    
    CodeAgent writes Python code to call tools, which is more efficient
    than JSON-based tool calling for multi-step analysis.
    
    Args:
        model: The LLM model to use
        tools: List of tools available to the agent
        max_steps: Maximum reasoning steps
        executor_type: Code execution environment
            - "local": Runs in local Python (default, use for development)
            - "e2b": Runs in E2B sandbox (secure, requires E2B account)
            - "docker": Runs in Docker container (secure, requires Docker)
    
    Returns:
        CodeAgent instance
    """
    # Additional imports the agent might need for analysis
    additional_imports = [
        "statistics",
        "math",
        "collections",
        "re",
        "datetime",
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


# =============================================================================
# ANALYSIS FUNCTIONS (All LLM-Powered with CodeAgent)
# =============================================================================

def run_technical_analysis(
    symbol: str,
    period: str = "1y",
    model_id: str = DEFAULT_MODEL_ID,
    model_provider: str = DEFAULT_MODEL_PROVIDER,
    hf_token: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    max_steps: int = DEFAULT_MAX_STEPS,
    executor_type: str = DEFAULT_EXECUTOR,
) -> str:
    """
    Run comprehensive technical analysis on a single stock using CodeAgent.
    
    The CodeAgent will write Python code to:
    1. Call all 4 strategy tools efficiently
    2. Parse and analyze results
    3. Generate a comprehensive markdown report
    """
    model = build_model(model_id, model_provider, hf_token, openai_api_key, openai_base_url)
    agent = build_agent(model, STRATEGY_TOOLS, max_steps, executor_type)
    
    prompt = TECHNICAL_ANALYSIS_PROMPT.format(
        symbol=symbol.upper(),
        period=period,
    )
    
    return agent.run(prompt)


def run_market_scanner(
    symbols: str,
    period: str = "1y",
    model_id: str = DEFAULT_MODEL_ID,
    model_provider: str = DEFAULT_MODEL_PROVIDER,
    hf_token: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    max_steps: int = 30,
    executor_type: str = DEFAULT_EXECUTOR,
) -> str:
    """
    Scan multiple stocks using CodeAgent with efficient looping.
    
    CodeAgent advantage: Can write a for-loop to process all stocks
    in fewer LLM calls compared to ToolCallingAgent.
    """
    model = build_model(model_id, model_provider, hf_token, openai_api_key, openai_base_url)
    
    # Clean up symbols string
    if isinstance(symbols, list):
        symbols = ",".join(symbols)
    symbols_clean = symbols.replace(" ", "").upper()
    
    # Calculate steps needed (CodeAgent is more efficient)
    symbol_list = [s.strip() for s in symbols_clean.split(",") if s.strip()]
    # CodeAgent can batch calls in loops, so fewer steps needed
    adjusted_max_steps = max(max_steps, len(symbol_list) * 2 + 10)
    
    agent = build_agent(model, STRATEGY_TOOLS, adjusted_max_steps, executor_type)
    
    prompt = MARKET_SCANNER_PROMPT.format(
        symbols=symbols_clean,
        period=period,
    )
    
    return agent.run(prompt)


def run_fundamental_analysis(
    symbol: str,
    period: str = "3y",
    model_id: str = DEFAULT_MODEL_ID,
    model_provider: str = DEFAULT_MODEL_PROVIDER,
    hf_token: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    max_steps: int = DEFAULT_MAX_STEPS,
    executor_type: str = DEFAULT_EXECUTOR,
) -> str:
    """
    Run fundamental analysis on a stock's financial statements using CodeAgent.
    """
    model = build_model(model_id, model_provider, hf_token, openai_api_key, openai_base_url)
    agent = build_agent(model, [fundamental_analysis_report], max_steps, executor_type)
    
    prompt = FUNDAMENTAL_ANALYSIS_PROMPT.format(
        symbol=symbol.upper(),
        period=period,
    )
    
    return agent.run(prompt)


def run_multi_sector_analysis(
    sectors: dict,
    period: str = "1y",
    model_id: str = DEFAULT_MODEL_ID,
    model_provider: str = DEFAULT_MODEL_PROVIDER,
    hf_token: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    max_steps: int = 50,
    executor_type: str = DEFAULT_EXECUTOR,
) -> str:
    """
    Run comprehensive multi-sector analysis using CodeAgent.
    
    CodeAgent advantage: Can use nested loops to efficiently process
    all stocks across all sectors with fewer LLM reasoning steps.
    """
    model = build_model(model_id, model_provider, hf_token, openai_api_key, openai_base_url)
    
    # Calculate totals
    sector_count = len(sectors)
    total_stocks = 0
    sectors_formatted_lines = []
    sectors_dict_lines = []
    
    for sector_name, symbols in sectors.items():
        if isinstance(symbols, list):
            symbol_list = symbols
        else:
            symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        
        total_stocks += len(symbol_list)
        symbols_str = ", ".join(symbol_list)
        sectors_formatted_lines.append(f"**{sector_name}**: {symbols_str}")
        
        # Build Python dict representation for the prompt
        symbols_py = ", ".join([f'"{s}"' for s in symbol_list])
        sectors_dict_lines.append(f'    "{sector_name}": [{symbols_py}],')
    
    sectors_formatted = "\n".join(sectors_formatted_lines)
    sectors_dict = "\n".join(sectors_dict_lines)
    
    # CodeAgent needs fewer steps due to efficient looping
    adjusted_max_steps = max(max_steps, total_stocks + 15)
    
    agent = build_agent(model, STRATEGY_TOOLS, adjusted_max_steps, executor_type)
    
    prompt = MULTI_SECTOR_ANALYSIS_PROMPT.format(
        sectors_formatted=sectors_formatted,
        sectors_dict=sectors_dict,
        period=period,
        sector_count=sector_count,
        total_stocks=total_stocks,
    )
    
    return agent.run(prompt)


def run_combined_analysis(
    symbol: str,
    technical_period: str = "1y",
    fundamental_period: str = "3y",
    model_id: str = DEFAULT_MODEL_ID,
    model_provider: str = DEFAULT_MODEL_PROVIDER,
    hf_token: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    max_steps: int = 25,
    executor_type: str = DEFAULT_EXECUTOR,
) -> str:
    """
    Run combined Technical + Fundamental analysis using CodeAgent.
    
    CodeAgent can efficiently call all 5 tools and synthesize results
    in a single code execution block.
    """
    model = build_model(model_id, model_provider, hf_token, openai_api_key, openai_base_url)
    
    # Include both strategy tools and fundamental tool
    combined_tools = STRATEGY_TOOLS + [fundamental_analysis_report]
    
    agent = build_agent(model, combined_tools, max_steps, executor_type)
    
    prompt = COMBINED_ANALYSIS_PROMPT.format(
        symbol=symbol.upper(),
        technical_period=technical_period,
        fundamental_period=fundamental_period,
    )
    
    return agent.run(prompt)


# =============================================================================
# LEGACY SUPPORT
# =============================================================================

def run_agent(
    symbol: str,
    period: str,
    model_id: str,
    hf_token: Optional[str],
    model_provider: str,
    openai_api_key: Optional[str],
    openai_base_url: Optional[str],
    max_steps: int,
    stream: bool,
    verbosity: int,
) -> str:
    """Legacy function for backward compatibility."""
    return run_technical_analysis(
        symbol=symbol,
        period=period,
        model_id=model_id,
        model_provider=model_provider,
        hf_token=hf_token,
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        max_steps=max_steps,
    )


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main() -> int:
    """Command-line entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run LLM-powered stock analysis using CodeAgent + MCP finance tools.",
    )
    parser.add_argument("symbol", help="Ticker symbol(s) to analyze")
    parser.add_argument(
        "--mode",
        choices=["technical", "scanner", "fundamental", "combined"],
        default="technical",
        help="Analysis mode (default: technical)",
    )
    parser.add_argument("--period", default="1y", help="Historical period (default: 1y)")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID, help="Model identifier")
    parser.add_argument("--model-provider", default=DEFAULT_MODEL_PROVIDER, help="Provider")
    parser.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS, help="Max agent steps")
    parser.add_argument(
        "--executor",
        choices=["local", "e2b", "docker"],
        default=DEFAULT_EXECUTOR,
        help="Code execution environment (default: local)",
    )
    parser.add_argument("--output", type=Path, help="Save report to file")
    
    args = parser.parse_args()
    
    print(f"🤖 Using CodeAgent with {args.executor} executor")
    print(f"📊 Model: {args.model_id}")
    print(f"🔧 Mode: {args.mode}")
    print()
    
    try:
        configure_finance_tools()
        
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
                model_id=args.model_id,
                model_provider=args.model_provider,
                max_steps=args.max_steps,
                executor_type=args.executor,
            )
        else:
            print(f"Unknown mode: {args.mode}")
            return 1
            
    except KeyboardInterrupt:
        print("\nAnalysis interrupted.")
        return 1
    finally:
        shutdown_finance_tools()
    
    if args.output:
        args.output.write_text(result, encoding="utf-8")
        print(f"Report saved to {args.output}")
    else:
        print(result)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())