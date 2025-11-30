"""Stock Analyzer Bot - ToolCallingAgent Implementation.

This module uses ToolCallingAgent with HIGH-LEVEL tools that do everything
in a single MCP call. The MCP server handles all the complexity internally.

HIGH-LEVEL TOOLS USED:
- comprehensive_performance_report: All 4 strategies + full report (1 call)
- unified_market_scanner: Multi-stock scanning with rankings (1 call)
- fundamental_analysis_report: Financial statements analysis (1 call)

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
from typing import Any, Dict, Optional

from smolagents import InferenceClientModel, LiteLLMModel, ToolCallingAgent

from .mcp_client import configure_session, shutdown_session
from .tools import (
    HIGH_LEVEL_TOOLS,
    comprehensive_performance_report,
    configure_finance_tools,
    fundamental_analysis_report,
    shutdown_finance_tools,
    unified_market_scanner,
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
DEFAULT_MAX_STEPS = int(os.getenv("SMOLAGENT_MAX_STEPS", "25"))
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
    """Create an LLM model instance for ToolCallingAgent."""
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


def build_agent(model, tools: list, max_steps: int = DEFAULT_MAX_STEPS):
    """Create a ToolCallingAgent with HIGH-LEVEL tools."""
    return ToolCallingAgent(
        tools=tools,
        model=model,
        max_steps=max_steps,
        verbosity_level=1,
    )


# ===========================================================================
# Prompts for HIGH-LEVEL Tool Usage - Professional Report Format
# ===========================================================================

TECHNICAL_ANALYSIS_PROMPT = """You are a senior financial analyst. Analyze {symbol} using technical analysis.

YOUR TASK:
Call the comprehensive_performance_report tool to get a complete multi-strategy analysis.

TOOL TO USE:
- comprehensive_performance_report(symbol="{symbol}", period="{period}")

After receiving the tool data, create a professional report following this EXACT format:

---

# {symbol} Technical Analysis Report

## Executive Summary

Analysis of {symbol} using four technical scoring systems reveals a [BULLISH/BEARISH/NEUTRAL] outlook.

**Analysis Period:** {period}

---

## Technical Indicators Summary Table

| Indicator System | Score/Value | Signal | Key Findings |
|-----------------|-------------|---------|--------------|
| **Bollinger-Fibonacci** | [score] | [BUY/SELL/HOLD] | [one-line finding] |
| **MACD-Donchian Combined** | [score] | [BUY/SELL/HOLD] | [one-line finding] |
| **Connors RSI + Z-Score** | [score] | [BUY/SELL/HOLD] | [one-line finding] |
| **Dual Moving Average** | [score] | [BUY/SELL/HOLD] | [one-line finding] |

---

## Detailed Analysis

### 1. Bollinger-Fibonacci Strategy

- **Signal:** [BUY/SELL/HOLD]
- **Strategy Return:** [X]%
- **Excess Return vs Buy-Hold:** [X]%
- **Sharpe Ratio:** [X]
- **Max Drawdown:** [X]%

**Key Observation:** [One sentence explanation]

---

### 2. MACD-Donchian Combined Strategy

- **Signal:** [BUY/SELL/HOLD]
- **Strategy Return:** [X]%
- **Excess Return vs Buy-Hold:** [X]%
- **Sharpe Ratio:** [X]
- **Max Drawdown:** [X]%

**Key Observation:** [One sentence explanation]

---

### 3. Connors RSI + Z-Score Combined Strategy

- **Signal:** [BUY/SELL/HOLD]
- **Strategy Return:** [X]%
- **Excess Return vs Buy-Hold:** [X]%
- **Sharpe Ratio:** [X]
- **Max Drawdown:** [X]%

**Key Observation:** [One sentence explanation]

---

### 4. Dual Moving Average (50/200 EMA) Strategy

- **Signal:** [BUY/SELL/HOLD]
- **Strategy Return:** [X]%
- **Excess Return vs Buy-Hold:** [X]%
- **Sharpe Ratio:** [X]
- **Max Drawdown:** [X]%

**Key Observation:** [One sentence explanation]

---

## Consensus Analysis

### Overall Technical Health: **[BULLISH/BEARISH/NEUTRAL]**

| Metric | Status |
|--------|--------|
| **Trend Direction** | [Upward/Downward/Sideways] |
| **Momentum** | [Positive/Negative/Neutral] |
| **Risk Level** | [Low/Medium/High] |

### Signal Breakdown

- **BUY Signals:** [X]/4
- **SELL Signals:** [X]/4
- **HOLD Signals:** [X]/4
- **Consensus Direction:** [BULLISH/BEARISH/NEUTRAL]

---

## 🎯 FINAL RECOMMENDATION: **[BUY/SELL/HOLD/STRONG BUY/STRONG SELL/AVOID]**

### Action Plan

**For Current {symbol} Holders:**
- ✅ [Action 1]
- ✅ [Action 2]
- ❌ [What NOT to do]

**For Potential Buyers:**
- [BUY/WAIT/AVOID] at current levels
- ⏳ Key triggers to watch:
  - 📊 [Trigger 1]
  - 📊 [Trigger 2]

---

## Risk Management

- **Position Size:** Maximum [X]% of portfolio
- **Stop Loss:** [Level based on technical support]
- **Take Profit Target:** [Level based on technical resistance]

---

## Conclusion

[2-3 sentence summary connecting all the data points to the final recommendation. Be specific about WHY you're recommending this action based on the technical indicators.]

**Disclaimer:** This analysis is for educational purposes only. Always conduct your own research before investing.

---

IMPORTANT INSTRUCTIONS:
1. Extract REAL numbers from the tool output - do not make up values
2. The table format with | is REQUIRED for the summary
3. Use emojis (✅, ❌, ⏳, 📊, 🎯) to make the report scannable
4. Be specific and data-driven in your observations
5. Use USD for currency (never use the dollar sign symbol)
"""

MARKET_SCANNER_PROMPT = """You are a senior financial analyst. Scan and rank these stocks: {symbols}

YOUR TASK:
Call unified_market_scanner to analyze all stocks at once.

TOOL TO USE:
- unified_market_scanner(symbols="{symbols}", period="{period}", output_format="detailed")

After receiving the tool data, create a professional report following this format:

---

# Market Scanner Report

## Executive Summary

Scanned {symbol_count} stocks using four technical strategies.

**Stocks Analyzed:** {symbols}

**Analysis Period:** {period}

---

## Stock Rankings Summary Table

| Rank | Symbol | BUY Signals | Overall Signal | Recommendation |
|------|--------|-------------|----------------|----------------|
| 1 | [SYMBOL] | [X]/4 | [BULLISH/BEARISH/NEUTRAL] | [STRONG BUY/BUY/HOLD/SELL/AVOID] |
| 2 | [SYMBOL] | [X]/4 | [BULLISH/BEARISH/NEUTRAL] | [STRONG BUY/BUY/HOLD/SELL/AVOID] |
| ... | ... | ... | ... | ... |

---

## Detailed Stock Analysis

### 🥇 Rank 1: [SYMBOL]

**Signal Breakdown:**

| Strategy | Signal | Return vs B&H |
|----------|--------|---------------|
| Bollinger-Fibonacci | [SIGNAL] | [X]% |
| MACD-Donchian | [SIGNAL] | [X]% |
| Connors RSI-ZScore | [SIGNAL] | [X]% |
| Dual Moving Average | [SIGNAL] | [X]% |

**Verdict:** [1-2 sentence summary]

---

[Repeat for each stock...]

---

## 🎯 TOP PICKS

### Best Opportunities (3+ BUY signals):
1. **[SYMBOL]** - [X]/4 BUY signals - [Brief reason]
2. **[SYMBOL]** - [X]/4 BUY signals - [Brief reason]

### Stocks to Avoid (0-1 BUY signals):
1. **[SYMBOL]** - [X]/4 BUY signals - [Brief reason]

---

## Market Sentiment

- **Average BUY Signals:** [X.X]/4 across all stocks
- **Market Outlook:** [BULLISH/BEARISH/NEUTRAL]
- **Recommendation:** [Summary action]

---

IMPORTANT: Extract REAL data from the tool output. Use tables for clarity.
"""

FUNDAMENTAL_ANALYSIS_PROMPT = """You are a senior financial analyst. Analyze {symbol} fundamentals.

YOUR TASK:
Call fundamental_analysis_report to get complete financial statement analysis.

TOOL TO USE:
- fundamental_analysis_report(symbol="{symbol}", period="{period}")

After receiving the tool data, create a professional report following this format:

---

# {symbol} Fundamental Analysis Report

## Executive Summary

**Company:** {symbol}

**Analysis Period:** {period}

**Financial Health:** [STRONG/MODERATE/WEAK]

**Investment Grade:** [A/B/C/D/F]

---

## Key Metrics Summary Table

| Category | Metric | Value | Assessment |
|----------|--------|-------|------------|
| **Profitability** | ROE | [X]% | [Good/Fair/Poor] |
| **Profitability** | Net Margin | [X]% | [Good/Fair/Poor] |
| **Leverage** | Debt/Equity | [X] | [Good/Fair/Poor] |
| **Liquidity** | Current Ratio | [X] | [Good/Fair/Poor] |
| **Valuation** | P/E Ratio | [X] | [Good/Fair/Poor] |
| **Growth** | Revenue Growth | [X]% | [Good/Fair/Poor] |

---

## Financial Statements Analysis

### Income Statement Highlights

- **Revenue:** [X] USD
- **Net Income:** [X] USD
- **Gross Margin:** [X]%
- **Operating Margin:** [X]%

### Balance Sheet Highlights

- **Total Assets:** [X] USD
- **Total Debt:** [X] USD
- **Shareholders Equity:** [X] USD

### Cash Flow Highlights

- **Operating Cash Flow:** [X] USD
- **Free Cash Flow:** [X] USD
- **CapEx:** [X] USD

---

## Strengths and Weaknesses

### ✅ Strengths
1. [Strength 1 with data]
2. [Strength 2 with data]

### ❌ Weaknesses
1. [Weakness 1 with data]
2. [Weakness 2 with data]

---

## 🎯 RECOMMENDATION: **[BUY/SELL/HOLD]**

**Rationale:** [2-3 sentences explaining why based on the fundamentals]

---

IMPORTANT: Extract REAL numbers from the tool output. Use USD for currency.
"""

MULTI_SECTOR_PROMPT = """You are a senior financial analyst. Compare these sectors:

{sector_details}

Analysis Period: {period}

YOUR TASK:
For each sector, call unified_market_scanner to analyze the stocks.

TOOL TO USE:
- unified_market_scanner(symbols="[stocks]", period="{period}", output_format="detailed")

After receiving ALL sector data, create a professional report following this format:

---

# Multi-Sector Analysis Report

## Executive Summary

**Sectors Analyzed:** [List sectors]

**Analysis Period:** {period}

**Strongest Sector:** [Name]

**Weakest Sector:** [Name]

---

## Sector Rankings Summary Table

| Rank | Sector | Avg BUY Signals | Best Stock | Sector Outlook |
|------|--------|-----------------|------------|----------------|
| 1 | [Sector] | [X.X]/4 | [SYMBOL] | [BULLISH/NEUTRAL/BEARISH] |
| 2 | [Sector] | [X.X]/4 | [SYMBOL] | [BULLISH/NEUTRAL/BEARISH] |
| ... | ... | ... | ... | ... |

---

## Sector-by-Sector Analysis

### 🥇 Rank 1: [SECTOR NAME]

**Stocks Analyzed:** [List]

**Average BUY Signals:** [X.X]/4

| Stock | BUY Signals | Recommendation |
|-------|-------------|----------------|
| [SYM] | [X]/4 | [REC] |
| [SYM] | [X]/4 | [REC] |

**Sector Verdict:** [1-2 sentences]

---

[Repeat for each sector...]

---

## 🎯 TOP PICKS ACROSS ALL SECTORS

1. **[SYMBOL]** ([Sector]) - [X]/4 BUY signals
2. **[SYMBOL]** ([Sector]) - [X]/4 BUY signals
3. **[SYMBOL]** ([Sector]) - [X]/4 BUY signals

---

## Investment Strategy

**Recommended Sector Allocation:**
- [Sector 1]: [X]% - [Reason]
- [Sector 2]: [X]% - [Reason]

---

IMPORTANT: Extract REAL data from tool outputs. Use tables for clarity.
"""

COMBINED_ANALYSIS_PROMPT = """You are a senior investment analyst. Perform complete analysis of {symbol}.

YOUR TASK:
Combine BOTH technical and fundamental analysis.

TOOLS TO USE:
1. comprehensive_performance_report(symbol="{symbol}", period="{technical_period}") - for technicals
2. fundamental_analysis_report(symbol="{symbol}", period="{fundamental_period}") - for fundamentals

After receiving BOTH tool outputs, create a professional report following this format:

---

# {symbol} Combined Investment Analysis

## Executive Summary

**Symbol:** {symbol}

**Technical Period:** {technical_period}

**Fundamental Period:** {fundamental_period}

**COMBINED RECOMMENDATION:** [STRONG BUY/BUY/HOLD/SELL/STRONG SELL]

**Confidence Level:** [HIGH/MEDIUM/LOW]

**Technical/Fundamental Alignment:** [ALIGNED/DIVERGENT/MIXED]

---

## Technical Analysis Summary

### Technical Indicators Table

| Strategy | Signal | Return vs B&H | Sharpe Ratio |
|----------|--------|---------------|--------------|
| Bollinger-Fibonacci | [SIGNAL] | [X]% | [X] |
| MACD-Donchian | [SIGNAL] | [X]% | [X] |
| Connors RSI-ZScore | [SIGNAL] | [X]% | [X] |
| Dual Moving Average | [SIGNAL] | [X]% | [X] |

**Technical Verdict:** [BULLISH/BEARISH/NEUTRAL] with [X]/4 BUY signals

---

## Fundamental Analysis Summary

### Key Metrics Table

| Metric | Value | Assessment |
|--------|-------|------------|
| ROE | [X]% | [Good/Fair/Poor] |
| Debt/Equity | [X] | [Good/Fair/Poor] |
| Current Ratio | [X] | [Good/Fair/Poor] |
| P/E Ratio | [X] | [Good/Fair/Poor] |

**Fundamental Verdict:** [STRONG/MODERATE/WEAK] financial health

---

## Alignment Analysis

| Aspect | Technical View | Fundamental View | Alignment |
|--------|----------------|------------------|-----------|
| Overall | [BULLISH/BEARISH/NEUTRAL] | [POSITIVE/NEGATIVE/NEUTRAL] | [✅/❌] |
| Momentum | [Status] | [Growth trend] | [✅/❌] |
| Risk | [Level] | [Financial stability] | [✅/❌] |

**Alignment Status:** [ALIGNED/DIVERGENT/MIXED]

---

## 🎯 FINAL RECOMMENDATION: **[RECOMMENDATION]**

### Why This Recommendation?

**Technical Factors:**
- [Factor 1 with data]
- [Factor 2 with data]

**Fundamental Factors:**
- [Factor 1 with data]
- [Factor 2 with data]

### Action Plan

**For Current Holders:**
- ✅ [Action 1]
- ✅ [Action 2]

**For Potential Buyers:**
- [Action with conditions]

### Risk Management

- **Position Size:** Max [X]% of portfolio
- **Stop Loss:** Based on [technical level]
- **Time Horizon:** [Short/Medium/Long] term

---

## Conclusion

[3-4 sentences connecting both technical and fundamental analysis to justify the final recommendation. Be specific about the alignment or divergence between the two analyses.]

**Disclaimer:** This analysis is for educational purposes only.

---

IMPORTANT: 
1. Extract REAL data from BOTH tool outputs
2. Use tables for clarity and scannability
3. Use emojis (✅, ❌, 🎯) to highlight key points
4. Explicitly address whether technical and fundamental views ALIGN or DIVERGE
5. Use USD for currency values
"""


# ===========================================================================
# Analysis Functions (Using HIGH-LEVEL Tools)
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
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    Run technical analysis using comprehensive_performance_report (1 MCP call).
    
    ToolCallingAgent approach: One tool call gets all 4 strategies analyzed.
    """
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
    
    agent = build_agent(model, HIGH_LEVEL_TOOLS, max_steps=max_steps)
    
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
    max_steps: int = DEFAULT_MAX_STEPS,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    Run market scanner using unified_market_scanner (1 MCP call).
    
    ToolCallingAgent approach: One tool call analyzes all stocks at once.
    """
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
    
    agent = build_agent(model, HIGH_LEVEL_TOOLS, max_steps=max_steps)
    
    symbol_list = [s.strip() for s in symbols.split(",")]
    
    prompt = MARKET_SCANNER_PROMPT.format(
        symbols=symbols,
        symbol_count=len(symbol_list),
        period=period,
    )
    
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
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    Run fundamental analysis using fundamental_analysis_report (1 MCP call).
    
    ToolCallingAgent approach: One tool call gets complete financial analysis.
    """
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
    
    agent = build_agent(model, HIGH_LEVEL_TOOLS, max_steps=max_steps)
    
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
    max_steps: int = 40,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    Run multi-sector analysis (N MCP calls, one per sector).
    
    ToolCallingAgent approach: One scanner call per sector (N calls total).
    """
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
    
    agent = build_agent(model, HIGH_LEVEL_TOOLS, max_steps=max_steps)
    
    sector_details = "\n".join([
        f"- {name}: {symbols}"
        for name, symbols in sectors.items()
    ])
    
    prompt = MULTI_SECTOR_PROMPT.format(
        sector_details=sector_details,
        period=period,
    )
    
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
    max_steps: int = DEFAULT_MAX_STEPS,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    Run combined technical + fundamental analysis (2 MCP calls).
    
    ToolCallingAgent approach:
    - comprehensive_performance_report for technicals
    - fundamental_analysis_report for fundamentals
    """
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
    
    agent = build_agent(model, HIGH_LEVEL_TOOLS, max_steps=max_steps)
    
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
    """CLI entry point for ToolCallingAgent analysis."""
    parser = argparse.ArgumentParser(
        description="ToolCallingAgent Stock Analysis (HIGH-LEVEL tools)"
    )
    parser.add_argument("symbol", help="Stock symbol or comma-separated symbols")
    parser.add_argument("--mode", choices=["technical", "scanner", "fundamental", "combined"],
                        default="technical", help="Analysis mode")
    parser.add_argument("--period", default="1y", help="Analysis period")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--model-provider", default=DEFAULT_MODEL_PROVIDER)
    parser.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE,
                        help="LLM temperature (default: 0.1)")
    
    args = parser.parse_args()
    
    try:
        if args.mode == "technical":
            result = run_technical_analysis(
                symbol=args.symbol,
                period=args.period,
                model_id=args.model_id,
                model_provider=args.model_provider,
                max_steps=args.max_steps,
                temperature=args.temperature,
            )
        elif args.mode == "scanner":
            result = run_market_scanner(
                symbols=args.symbol,
                period=args.period,
                model_id=args.model_id,
                model_provider=args.model_provider,
                max_steps=args.max_steps,
                temperature=args.temperature,
            )
        elif args.mode == "fundamental":
            result = run_fundamental_analysis(
                symbol=args.symbol,
                period=args.period,
                model_id=args.model_id,
                model_provider=args.model_provider,
                max_steps=args.max_steps,
                temperature=args.temperature,
            )
        elif args.mode == "combined":
            result = run_combined_analysis(
                symbol=args.symbol,
                technical_period=args.period,
                model_id=args.model_id,
                model_provider=args.model_provider,
                max_steps=args.max_steps,
                temperature=args.temperature,
            )
        
        print(result)
        
    finally:
        shutdown_finance_tools()


if __name__ == "__main__":
    main()