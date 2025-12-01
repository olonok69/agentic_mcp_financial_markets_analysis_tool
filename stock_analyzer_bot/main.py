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
    "DEFAULT_MODEL_ID",
    "DEFAULT_MODEL_PROVIDER",
    "DEFAULT_MAX_STEPS",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_MAX_TOKENS",
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
    """
    Create an LLM model instance for ToolCallingAgent.
    
    Note: LiteLLMModel passes additional kwargs to the LiteLLM completion call.
    We pass temperature and max_tokens to control output generation.
    """
    if provider == "litellm":
        # LiteLLMModel accepts model_id, api_key, api_base, and additional kwargs
        # that get passed to litellm.completion()
        kwargs = {
            "model_id": model_id,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if api_key:
            kwargs["api_key"] = api_key
        if api_base:
            kwargs["api_base"] = api_base
        
        # Log configuration for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            "Creating LiteLLMModel: model=%s, temperature=%s, max_tokens=%s",
            model_id, temperature, max_tokens
        )
        
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
Call comprehensive_performance_report(symbol="{symbol}", period="{period}") then create a concise report.

REPORT FORMAT (be concise, extract real data):

# {symbol} Technical Analysis Report

## Executive Summary
[1-2 sentences: BULLISH/BEARISH/NEUTRAL outlook based on signal count]

**Period:** {period}

## Technical Indicators Summary

| Strategy | Score | Signal | Key Finding |
|----------|-------|--------|-------------|
| Bollinger-Fibonacci | [score] | [signal] | [brief] |
| MACD-Donchian | [score] | [signal] | [brief] |
| Connors RSI+Z | [score] | [signal] | [brief] |
| Dual MA | [trend%] | [signal] | [brief] |

## Strategy Details

**1. Bollinger-Fibonacci:** [Signal] - Return: [X]%, Sharpe: [X], Drawdown: [X]%

**2. MACD-Donchian:** [Signal] - Return: [X]%, Sharpe: [X], Drawdown: [X]%

**3. Connors RSI+Z:** [Signal] - Return: [X]%, Sharpe: [X], Drawdown: [X]%

**4. Dual MA:** [Signal] - Return: [X]%, Sharpe: [X], Drawdown: [X]%

## Consensus

- BUY: [X]/4 | SELL: [X]/4 | HOLD: [X]/4
- Trend: [Up/Down/Sideways] | Risk: [Low/Med/High]

## 🎯 Recommendation: **[STRONG BUY/BUY/HOLD/SELL/STRONG SELL]**

**Holders:** ✅ [action] | ❌ [avoid]

**Buyers:** [BUY/WAIT/AVOID] - Watch: 📊 [key trigger]

**Risk:** Position max [X]% portfolio, Stop at [level]

---
*Disclaimer: Educational purposes only.*

RULES:
1. Extract REAL numbers from tool output
2. Keep each section brief (1-2 lines max)
3. Use USD for currency (no dollar signs)
4. Total report should be under 400 words
"""

MARKET_SCANNER_PROMPT = """You are a senior financial analyst. Scan these stocks: {symbols}

Call unified_market_scanner(symbols="{symbols}", period="{period}", output_format="detailed")

Create a CONCISE report:

# Market Scanner Report

## Summary
Scanned {symbol_count} stocks | Period: {period}

## Rankings

| Rank | Symbol | BUY Signals | Outlook | Action |
|------|--------|-------------|---------|--------|
| 1 | [SYM] | [X]/4 | [BULL/BEAR] | [BUY/HOLD/SELL] |
| 2 | [SYM] | [X]/4 | [BULL/BEAR] | [BUY/HOLD/SELL] |
[continue for each stock...]

## 🎯 Top Picks (3+ BUY signals)
🥇 **[SYM]** - [X]/4 BUY - [reason]
🥈 **[SYM]** - [X]/4 BUY - [reason]

## Avoid (0-1 BUY signals)
- **[SYM]** - [reason]

## Market Outlook: [BULLISH/BEARISH/NEUTRAL]

*Extract real data. Keep brief.*
"""

FUNDAMENTAL_ANALYSIS_PROMPT = """Analyze {symbol} fundamentals.

Call fundamental_analysis_report(symbol="{symbol}", period="{period}")

Create a CONCISE report:

# {symbol} Fundamental Analysis

## Summary
**Health:** [STRONG/MODERATE/WEAK] | **Grade:** [A/B/C/D/F] | **Period:** {period}

## Key Metrics

| Metric | Value | Rating |
|--------|-------|--------|
| ROE | [X]% | [Good/Fair/Poor] |
| Net Margin | [X]% | [Good/Fair/Poor] |
| Debt/Equity | [X] | [Good/Fair/Poor] |
| Current Ratio | [X] | [Good/Fair/Poor] |
| P/E | [X] | [Good/Fair/Poor] |

## Financials
- Revenue: [X] USD | Net Income: [X] USD
- Assets: [X] USD | Debt: [X] USD
- Op. Cash Flow: [X] USD | Free Cash Flow: [X] USD

## Assessment
✅ Strengths: [1-2 key points]
❌ Weaknesses: [1-2 key points]

## 🎯 Recommendation: **[BUY/HOLD/SELL]**
[1-2 sentence rationale]

*Extract real numbers. Use USD.*
"""

MULTI_SECTOR_PROMPT = """Compare these sectors:
{sector_details}

Period: {period}

For each sector, call unified_market_scanner(symbols="[stocks]", period="{period}", output_format="detailed")

Create a CONCISE report:

# Multi-Sector Analysis

## Summary
**Strongest:** [Sector] | **Weakest:** [Sector] | **Period:** {period}

## Sector Rankings

| Rank | Sector | Avg BUY | Best Stock | Outlook |
|------|--------|---------|------------|---------|
| 1 | [Sector] | [X.X]/4 | [SYM] | [BULL/BEAR] |
| 2 | [Sector] | [X.X]/4 | [SYM] | [BULL/BEAR] |

## Sector Details

**[Sector 1]:** [X.X]/4 avg - Top: [SYM] ([X]/4)

**[Sector 2]:** [X.X]/4 avg - Top: [SYM] ([X]/4)

## 🎯 Top Picks Across Sectors
1. **[SYM]** ([Sector]) - [X]/4 BUY
2. **[SYM]** ([Sector]) - [X]/4 BUY

## Allocation
- [Sector 1]: [X]% - [reason]
- [Sector 2]: [X]% - [reason]

*Extract real data. Keep brief.*
"""

COMBINED_ANALYSIS_PROMPT = """Complete analysis of {symbol}.

TOOLS:
1. comprehensive_performance_report(symbol="{symbol}", period="{technical_period}")
2. fundamental_analysis_report(symbol="{symbol}", period="{fundamental_period}")

Create a CONCISE report:

# {symbol} Combined Analysis

## Summary
**Recommendation:** [STRONG BUY/BUY/HOLD/SELL] | **Confidence:** [HIGH/MED/LOW]
**Alignment:** [ALIGNED/DIVERGENT] (Tech vs Fundamental)

## Technical Summary (Period: {technical_period})

| Strategy | Signal | Excess Return |
|----------|--------|---------------|
| Bollinger-Fib | [SIG] | [X]% |
| MACD-Donchian | [SIG] | [X]% |
| Connors RSI-Z | [SIG] | [X]% |
| Dual MA | [SIG] | [X]% |

**Technical:** [BULLISH/BEARISH/NEUTRAL] - [X]/4 BUY signals

## Fundamental Summary (Period: {fundamental_period})

| Metric | Value | Rating |
|--------|-------|--------|
| ROE | [X]% | [G/F/P] |
| Debt/Eq | [X] | [G/F/P] |
| P/E | [X] | [G/F/P] |

**Fundamental:** [STRONG/MODERATE/WEAK] health

## Alignment
- Technical: [BULL/BEAR] | Fundamental: [POS/NEG] | Match: [✅/❌]

## 🎯 Recommendation: **[ACTION]**
**Why:** [1-2 sentences combining both analyses]

**Holders:** ✅ [action]
**Buyers:** [BUY/WAIT] - [condition]
**Risk:** Max [X]% position, Stop at [level]

*Educational purposes only.*
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