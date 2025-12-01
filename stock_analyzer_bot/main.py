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

Create a report matching this EXACT format:

# Market Scanner Report

## Executive Summary

Scanned {symbol_count} stocks using four technical strategies.

**Stocks Analyzed:** {symbols}

**Analysis Period:** {period}

---

## Stock Rankings Summary Table

| Rank | Symbol | BUY Signals | Overall Signal | Recommendation |
|------|--------|-------------|----------------|----------------|
| 1 | [SYMBOL] | [X]/4 | [BULLISH/NEUTRAL/BEARISH] | [STRONG BUY/BUY/HOLD/SELL/AVOID] |
| 2 | [SYMBOL] | [X]/4 | [BULLISH/NEUTRAL/BEARISH] | [STRONG BUY/BUY/HOLD/SELL/AVOID] |
[continue for each stock, ranked by BUY signals descending]

---

## Detailed Stock Analysis

### 🥇 Rank 1: [SYMBOL]

**Signal Breakdown:**

| Strategy | Signal |
|----------|--------|
| Bollinger-Fibonacci | [BUY/SELL/HOLD] |
| MACD-Donchian | [BUY/SELL/HOLD] |
| Connors RSI-ZScore | [BUY/SELL/HOLD] |
| Dual Moving Average | [BUY/SELL/HOLD] |

**Verdict:** [X]/4 BUY signals - [RECOMMENDATION]

---

[Repeat the above format for Rank 2, Rank 3, Rank 4, etc.]

---

## 🎯 TOP PICKS

### Best Opportunities (3+ BUY signals):

[List stocks with 3+ BUY signals, or "No stocks with 3+ BUY signals in this scan."]

### Stocks to Avoid (0 BUY signals):

[List stocks with 0 BUY signals, or "No stocks with 0 BUY signals in this scan."]

---

## Market Sentiment

- **Average BUY Signals:** [X.X]/4 across all stocks
- **Market Outlook:** [BULLISH/NEUTRAL/BEARISH]

**Disclaimer:** This analysis is for educational purposes only.

---

IMPORTANT RULES:
1. Extract REAL signals from the tool output for each stock
2. Rank stocks by BUY signal count (highest first)
3. Use medal emojis: 🥇 for Rank 1, 🥈 for Rank 2, 🥉 for Rank 3
4. Include the Signal Breakdown table for EACH stock
5. Calculate the average BUY signals across all stocks
"""

FUNDAMENTAL_ANALYSIS_PROMPT = """Analyze {symbol} fundamentals.

Call fundamental_analysis_report(symbol="{symbol}", period="{period}")

Create a report matching this EXACT format:

# {symbol} Fundamental Analysis Report

## Executive Summary

**Company:** {symbol}

**Analysis Period:** {period}

**Financial Health:** [STRONG/MODERATE/WEAK]

**Investment Grade:** [A/B/C/D/F]

---

## Financial Data

### [Company Name] ({symbol}) Fundamental Analysis

*Sector:* [Sector] | *Industry:* [Industry] | *Period:* {period}

### Company Overview

[Brief company description from the data]

### Market Data

- **Market Cap:** USD [X]
- **P/E Ratio (TTM):** [X]
- **Dividend Yield:** [X]%
- **Beta:** [X]

---

## Income Statement Highlights

- **Total Revenue:** USD [X]
- **Revenue YoY Change:** [X]%
- **Gross Profit:** USD [X]
- **Net Income:** USD [X]

### Profitability Ratios

- **Gross Margin:** [X]%
- **Operating Margin:** [X]%
- **Net Profit Margin:** [X]%
- **EBITDA Margin:** [X]%

---

## Balance Sheet Snapshot

- **Total Assets:** USD [X]
- **Total Liabilities:** USD [X]
- **Shareholders' Equity:** USD [X]
- **Cash & Equivalents:** USD [X]
- **Total Debt:** USD [X]
- **Long-Term Debt:** USD [X]

### Liquidity Ratios

- **Current Ratio:** [X]x
- **Quick Ratio:** [X]x
- **Cash Ratio:** [X]x

### Leverage Ratios

- **Debt-to-Equity:** [X]x
- **Debt-to-Assets:** [X]x
- **Equity Ratio:** [X]x

---

## Cash Flow Overview

- **Operating Cash Flow:** USD [X]
- **Investing Cash Flow:** USD [X]
- **Financing Cash Flow:** USD [X]
- **Capital Expenditures:** USD [X]
- **Free Cash Flow:** USD [X]
- **Dividends Paid:** USD [X]

### Return Metrics

- **Return on Assets (ROA):** [X]%
- **Return on Equity (ROE):** [X]%

---

## Analytical Insights

- [Insight 1 based on revenue/income trends]
- [Insight 2 based on profitability margins]
- [Insight 3 based on leverage ratios]
- [Insight 4 based on liquidity]
- [Insight 5 based on cash flow]
- [Insight 6 based on return metrics]

---

## Disclaimer

- This analysis is based on financial statements available through Yahoo Finance.
- Data may not reflect the most recent filings or restated figures.
- Always verify against official SEC filings (10-K, 10-Q) for investment decisions.
- This is not financial advice.

---

## 🎯 RECOMMENDATION: **[STRONG BUY/BUY/HOLD/SELL/STRONG SELL]**

**Rationale:** [2-3 sentences explaining the recommendation based on the fundamental data]

**Disclaimer:** This analysis is for educational purposes only.

---

IMPORTANT RULES:
1. Extract ALL real numbers from the tool output
2. Use USD for all currency values (never use dollar signs)
3. Include ALL sections shown above
4. Provide specific analytical insights based on the actual data
5. Grade: A (excellent), B (good), C (fair), D (poor), F (failing)
6. Health: STRONG (Grade A-B), MODERATE (Grade C), WEAK (Grade D-F)
"""

MULTI_SECTOR_PROMPT = """Compare these sectors:
{sector_details}

Period: {period}

For each sector, call unified_market_scanner(symbols="[stocks]", period="{period}", output_format="detailed")

Create a COMPREHENSIVE report matching this EXACT format:

# Multi-Sector Market Analysis Report

**Analysis Date:** [Current Date]
**Period:** {period} | **Total Stocks Analyzed:** [X] | **Sectors:** [X]

---

## 📊 Executive Summary

### Cross-Sector Performance Overview

| Sector | Stocks | Avg Buy Signals | Best Strategy | Success Rate | Best Opportunities |
|--------|--------|-----------------|---------------|--------------|-------------------|
| **[Sector 1]** | [X] | [X.X]/4 | [Strategy Name] | [X]% | [Top 2-3 symbols] |
| **[Sector 2]** | [X] | [X.X]/4 | [Strategy Name] | [X]% | [Top 2-3 symbols] |
| **OVERALL** | **[X]** | **[X.X]/4** | **[Best Overall]** | **[X]%** | **[X] Stocks** |

### Key Market Insights

🔴 **[Insight 1]**: [Description of overall market condition]
🏆 **[Insight 2]**: [Which sector leads and why]
💡 **[Insight 3]**: [Number of opportunities identified]
⚠️ **[Insight 4]**: [Risk factors or warnings]

---

## 🎯 Final Investment Recommendations

### 🟢 PRIORITY INVESTMENTS ([X] Stocks)

#### 1. [SYMBOL] - USD [Price] | [Sector]
**🎯 STRONG BUY | 📊 HIGH CONFIDENCE | 💰 [POSITION SIZE]**

- **Performance**: [X]/4 strategies signal BUY
- **Best Strategy**: [Strategy Name] ([X]% excess return)
- **Signal Consensus**: [Bullish/Mixed/Bearish] across indicators
- **Risk Level**: [Low/Medium/High]
- **Why [SYMBOL]**: [1-2 sentence rationale]

#### 2. [SYMBOL] - USD [Price] | [Sector]
[Repeat format...]

### 🔵 SECONDARY OPPORTUNITIES ([X] Stocks)

#### [X]. [SYMBOL] - USD [Price] | [Sector]
**🎯 BUY | 📊 MEDIUM CONFIDENCE | 💰 [POSITION SIZE]**

[Same format as above...]

---

## 📈 Sector-by-Sector Analysis

### 🏦 [Sector 1 Name]
**Performance**: [X.X]/4 avg BUY signals | [X]% technical success rate

**Key Findings**:
- [Finding 1]
- [Finding 2]
- [Finding 3]

**Top Picks**:
1. **[SYMBOL]** - [X]/4 BUY signals - [Brief reason]
2. **[SYMBOL]** - [X]/4 BUY signals - [Brief reason]

**Avoid List**: [Symbols with 0-1 BUY signals]

**Strategy**: [1-2 sentence sector strategy recommendation]

---

### 💻 [Sector 2 Name]
[Repeat format for each sector...]

---

## 📬 Strategy Effectiveness Analysis

### Cross-Sector Strategy Performance

| Strategy | Overall Success Rate | Best Sector | Avg Signals | Reliability |
|----------|---------------------|-------------|-------------|-------------|
| **Bollinger-Fibonacci** | [X]% | [Sector] | [X.X]/stocks | [High/Medium/Low] |
| **MACD-Donchian** | [X]% | [Sector] | [X.X]/stocks | [High/Medium/Low] |
| **Connors RSI-ZScore** | [X]% | [Sector] | [X.X]/stocks | [High/Medium/Low] |
| **Dual Moving Average** | [X]% | [Sector] | [X.X]/stocks | [High/Medium/Low] |

### Key Strategy Insights
- [Insight about which strategies work best]
- [Insight about sector responsiveness]
- [Insight about current market regime]

---

## 🎯 Portfolio Construction Framework

### Recommended Portfolio Allocation

**CONSERVATIVE APPROACH (Recommended)**
- **[X]%** Cash/Fixed Income (defensive positioning)
- **[X]%** [Sector 1] (reason)
- **[X]%** [Sector 2] (reason)
- **[X]%** Top picks concentration

**AGGRESSIVE APPROACH (Higher Risk)**
- **[X]%** Cash/Fixed Income
- **[X]%** [Sector allocations...]

### Risk Management Framework

**Position Sizing Guidelines**:
- **Maximum single position**: [X]%
- **High-risk stocks**: [X]% maximum
- **Sector exposure**: [X]% maximum per sector

**Stop Loss Strategy**:
- **[SYMBOL]**: [X]% below entry
[Continue for each recommended stock...]

---

## 🔍 Market Outlook & Strategic Themes

### Current Market Environment
**[BULLISH/BEARISH/NEUTRAL] TECHNICAL REGIME**
- [Key observation 1]
- [Key observation 2]
- [Key observation 3]

### Risk Factors to Monitor
- [Risk 1]
- [Risk 2]
- [Risk 3]

---

## 🎯 Action Plan & Next Steps

### Immediate Actions (Next 30 Days)
1. [Action 1 with specific allocation]
2. [Action 2]
3. [Action 3]

### Monitoring Schedule
- **Daily**: [What to monitor]
- **Weekly**: [What to review]
- **Monthly**: [What to assess]

---

## 📊 Appendix: Detailed Holdings Summary

### PRIORITY HOLDINGS

| Symbol | Sector | Action | BUY Signals | Risk | Position |
|--------|--------|--------|-------------|------|----------|
| [SYM] | [Sector] | STRONG BUY | [X]/4 | [Risk] | [X]% |
| [SYM] | [Sector] | BUY | [X]/4 | [Risk] | [X]% |

### AVOID HOLDINGS
[Sector 1]: [List of symbols to avoid]
[Sector 2]: [List of symbols to avoid]

---

*This analysis represents a point-in-time assessment based on technical factors. Market conditions change rapidly. Past performance does not guarantee future results.*

---

IMPORTANT RULES:
1. Extract REAL data from all sector scans
2. Rank sectors by average BUY signals
3. Identify TOP 2-3 stocks across ALL sectors as priority picks
4. Calculate success rates (stocks with 2+ BUY signals / total stocks)
5. Use emojis for visual hierarchy: 📊🎯🟢🔵🏦💻⚠️
6. Provide specific position sizing recommendations
7. Include risk management with stop loss levels
"""

COMBINED_ANALYSIS_PROMPT = """Complete Technical + Fundamental analysis of {symbol}.

TOOLS TO CALL:
1. comprehensive_performance_report(symbol="{symbol}", period="{technical_period}")
2. fundamental_analysis_report(symbol="{symbol}", period="{fundamental_period}")

Create a COMPREHENSIVE report matching this EXACT format:

# {symbol} Combined Investment Analysis

## Executive Summary

**Symbol:** {symbol}

**Technical Period:** {technical_period}

**Fundamental Period:** {fundamental_period}

**COMBINED RECOMMENDATION:** [STRONG BUY/BUY/HOLD/SELL/STRONG SELL]

**Confidence Level:** [HIGH/MEDIUM/LOW]

**Technical/Fundamental Alignment:** [ALIGNED ✅ / DIVERGENT ❌]

---

## Technical Analysis Summary

### Technical Indicators Table

| Strategy | Signal |
|----------|--------|
| Bollinger-Fibonacci | [BUY/SELL/HOLD] |
| MACD-Donchian | [BUY/SELL/HOLD] |
| Connors RSI-ZScore | [BUY/SELL/HOLD] |
| Dual Moving Average | [BUY/SELL/HOLD] |

**Technical Verdict:** [BULLISH/BEARISH/NEUTRAL] with [X]/4 BUY signals

---

## Fundamental Analysis Summary

### [Company Name] ({symbol}) Fundamental Analysis

*Sector:* [Sector] | *Industry:* [Industry] | *Period:* {fundamental_period}

### Company Overview

[Company description from the fundamental data]

### Market Data

- **Market Cap:** USD [X]
- **P/E Ratio (TTM):** [X]
- **Dividend Yield:** [X]%
- **Beta:** [X]

### Income Statement Highlights

- **Total Revenue:** USD [X]
- **Revenue YoY Change:** [X]%
- **Gross Profit:** USD [X]
- **Operating Income:** USD [X]
- **Net Income:** USD [X]
- **Net Income YoY Change:** [X]%
- **EBITDA:** USD [X]
- **Diluted EPS:** [X]

### Profitability Ratios

- **Gross Margin:** [X]%
- **Operating Margin:** [X]%
- **Net Profit Margin:** [X]%
- **EBITDA Margin:** [X]%

### Balance Sheet Snapshot

- **Total Assets:** USD [X]
- **Total Liabilities:** USD [X]
- **Shareholders' Equity:** USD [X]
- **Cash & Equivalents:** USD [X]
- **Total Debt:** USD [X]
- **Long-Term Debt:** USD [X]

### Liquidity Ratios

- **Current Ratio:** [X]x
- **Quick Ratio:** [X]x
- **Cash Ratio:** [X]x

### Leverage Ratios

- **Debt-to-Equity:** [X]x
- **Debt-to-Assets:** [X]x
- **Equity Ratio:** [X]x

### Cash Flow Overview

- **Operating Cash Flow:** USD [X]
- **Investing Cash Flow:** USD [X]
- **Financing Cash Flow:** USD [X]
- **Capital Expenditures:** USD [X]
- **Free Cash Flow:** USD [X]
- **Dividends Paid:** USD [X]

### Return Metrics

- **Return on Assets (ROA):** [X]%
- **Return on Equity (ROE):** [X]%

### Analytical Insights

- [Insight 1 based on revenue/income trends]
- [Insight 2 based on profitability margins]
- [Insight 3 based on leverage ratios]
- [Insight 4 based on liquidity]
- [Insight 5 based on cash flow]
- [Insight 6 based on return metrics]

### Disclaimer

- This analysis is based on financial statements available through Yahoo Finance.
- Data may not reflect the most recent filings or restated figures.
- Always verify against official SEC filings (10-K, 10-Q) for investment decisions.
- This is not financial advice.

**Fundamental Verdict:** [POSITIVE/NEUTRAL/NEGATIVE]

---

## Alignment Analysis

| Aspect | Technical | Fundamental | Alignment |
|--------|-----------|-------------|-----------|
| Overall | [BULLISH/BEARISH/NEUTRAL] | [POSITIVE/NEUTRAL/NEGATIVE] | [✅/❌] |

**Alignment Status:** [ALIGNED/DIVERGENT]

---

## 🎯 FINAL RECOMMENDATION: **[STRONG BUY/BUY/HOLD/SELL/STRONG SELL]**

### Why This Recommendation?

**Technical Factors:** [X]/4 strategies show [bullish/bearish/mixed] signals

**Fundamental Factors:** Financial analysis shows [positive/neutral/negative] outlook

**Alignment:** Technical and fundamental views are [aligned/divergent]

---

### Investment Action Plan

**For Current Holders:**
- [Specific action recommendation]

**For Potential Buyers:**
- [Buy/Wait recommendation with conditions]

**Risk Management:**
- **Position Size:** Maximum [X]% of portfolio
- **Stop Loss:** [X]% below entry or USD [price level]
- **Take Profit:** Consider at [X]% gain

---

**Disclaimer:** This analysis is for educational purposes only. Always conduct your own research and consult with a financial advisor before making investment decisions.

---

IMPORTANT RULES:
1. Extract ALL real numbers from BOTH tool outputs
2. Include the FULL fundamental analysis with all sections
3. Use USD for all currency values (never use dollar signs)
4. Determine alignment: ALIGNED if both bullish/positive OR both bearish/negative
5. Confidence: HIGH if 3-4 BUY signals + positive fundamentals, MEDIUM if mixed, LOW if divergent
6. Provide specific, actionable recommendations based on the data
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