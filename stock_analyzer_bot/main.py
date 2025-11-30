"""
Smolagents-powered stock analyzer with LLM interpretation for all analysis types.

This module provides three core analysis functions, all powered by LLM:
1. Technical Analysis - Single stock, multiple strategies
2. Market Scanner - Multiple stocks comparison
3. Fundamental Analysis - Financial statements interpretation
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from smolagents import ToolCallingAgent, LiteLLMModel, InferenceClientModel

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

# Defaults - prefer OpenAI for reliability
DEFAULT_MODEL_ID = os.getenv("SMOLAGENT_MODEL_ID", "gpt-4.1")
DEFAULT_MODEL_PROVIDER = os.getenv("SMOLAGENT_MODEL_PROVIDER", "litellm")
DEFAULT_MAX_STEPS = int(os.getenv("SMOLAGENT_MAX_STEPS", "25"))


# =============================================================================
# PROMPT TEMPLATES FOR EACH ANALYSIS TYPE
# =============================================================================

TECHNICAL_ANALYSIS_PROMPT = """You are a senior quantitative analyst creating a comprehensive technical analysis report.

## CRITICAL: OUTPUT FORMAT REQUIREMENT
Your final answer MUST be the complete markdown report itself - not a summary or description of what you found.
When you finish gathering data, write the full formatted report as your final answer.

## Your Task
Analyze {symbol} stock using these 4 technical strategy tools with period='{period}':

1. **bollinger_fibonacci_analysis** - Bollinger Bands + Fibonacci retracement levels
2. **macd_donchian_analysis** - MACD momentum + Donchian channel breakouts  
3. **connors_zscore_analysis** - Connors RSI + Z-Score mean reversion
4. **dual_moving_average_analysis** - 50/200 EMA crossover (Golden/Death Cross)

## Instructions
1. Call ALL 4 strategy tools with symbol='{symbol}' and period='{period}'
2. Extract key metrics from each: signal, score, return %, Sharpe ratio, max drawdown, win rate
3. Synthesize into a professional markdown report

## Required Report Structure

Create a markdown report with these sections:

# {symbol} Comprehensive Technical Analysis
*Analysis Date: [today's date]*  
*Current Price: $[price from tool outputs]*

## Executive Summary
2-3 paragraph overview of {symbol}'s technical position. Include:
- Overall market stance (bullish/bearish/neutral)
- Key support/resistance levels mentioned in tools
- Consensus signal across strategies

## Performance Summary Table

| Strategy | Signal | Return % | vs Buy&Hold | Sharpe | Max Drawdown | Win Rate |
|----------|--------|----------|-------------|--------|--------------|----------|
| Bollinger-Fibonacci | [signal] | [%] | [excess %] | [ratio] | [%] | [%] |
| MACD-Donchian | [signal] | [%] | [excess %] | [ratio] | [%] | [%] |
| Connors RSI-ZScore | [signal] | [%] | [excess %] | [ratio] | [%] | [%] |
| Dual Moving Average | [signal] | [%] | [excess %] | [ratio] | [%] | [%] |

## Individual Strategy Analysis

### 1. Bollinger Bands & Fibonacci Retracement
[Detailed analysis from tool output - scores, levels, interpretation]

### 2. MACD-Donchian Combined Strategy  
[Detailed analysis from tool output - MACD values, Donchian levels, momentum]

### 3. Connors RSI & Z-Score Analysis
[Detailed analysis from tool output - RSI values, Z-score, mean reversion signals]

### 4. Dual Moving Average Strategy
[Detailed analysis from tool output - EMA values, crossover status, trend strength]

## Strategy Consensus Analysis

**Signal Breakdown:**
- BUY signals: [count] strategies
- HOLD signals: [count] strategies  
- SELL signals: [count] strategies

**Best Performing Strategy:** [name] with [excess return]%
**Worst Performing Strategy:** [name] with [excess return]%

## Risk Assessment
- Overall volatility assessment based on strategy metrics
- Maximum drawdown risk across strategies
- Risk-adjusted return evaluation (Sharpe ratios)

## Final Recommendation: **[BUY/HOLD/SELL]**

### Rationale
[3-4 bullet points explaining the recommendation]

### Trading Strategy
1. **Current Holders:** [advice]
2. **New Buyers:** [entry points, conditions]
3. **Risk Management:** [stop loss levels, position sizing]

### Key Levels to Watch
- **Resistance:** $[level] ([source])
- **Support:** $[level] ([source])
- **Stop Loss:** $[level]

*This analysis is for educational purposes only and should not be considered financial advice.*

---

## FINAL REMINDER

When you call final_answer, your answer MUST be the complete markdown report starting with:

# {symbol} Comprehensive Technical Analysis

Do NOT say things like "I have analyzed the data" or "The tools returned...". 
Just output the full report directly. The report IS your final answer.
"""


MARKET_SCANNER_PROMPT = """You are a senior portfolio strategist analyzing multiple stocks for investment opportunities.

## CRITICAL: OUTPUT FORMAT REQUIREMENT
Your final answer MUST be the complete markdown report itself - not a summary or description of what you found.
When you finish gathering data, write the full formatted report as your final answer.

## CRITICAL: DO NOT STOP EARLY
You MUST call all 4 strategy tools for EVERY stock in the list before writing the report.
For {symbols}, this means approximately {symbol_count} tool calls total.
Do NOT call final_answer until you have data for ALL stocks.

## Your Task
Scan these stocks: {symbols}
Period: {period}

For EACH stock, call these 4 strategy tools:
1. bollinger_fibonacci_analysis
2. macd_donchian_analysis
3. connors_zscore_analysis
4. dual_moving_average_analysis

## Instructions
1. Loop through each symbol and call all 4 tools
2. Collect: current price, signals, returns, Sharpe ratios, excess returns vs buy-and-hold
3. Rank stocks by opportunity quality
4. **WRITE THE FULL MARKDOWN REPORT AS YOUR FINAL ANSWER**

## CRITICAL INSTRUCTIONS - READ CAREFULLY

**YOUR FINAL ANSWER MUST BE THE COMPLETE MARKDOWN REPORT ITSELF.**

DO NOT:
- Say "I have gathered the data" or "The analysis shows..."
- Provide meta-commentary about what you found
- Summarize that you called the tools
- Give a brief description of results
- Stop before analyzing ALL stocks

DO:
- Call all 4 tools for EVERY stock ({symbols})
- Write the FULL markdown report with all sections below
- Include actual numbers from the tool outputs
- Format tables properly with | characters
- Provide specific recommendations with price levels

## Required Report Structure (COPY THIS STRUCTURE EXACTLY):

# Multi-Stock Market Analysis Report
*Analysis Date: [today's date]*  
*Period: {period} | Stocks Analyzed: [count]*

## 📊 Executive Summary

### Cross-Stock Performance Overview

| Symbol | Price | Buy&Hold % | Best Strategy | Best Excess % | Signals (B/H/S) | Recommendation |
|--------|-------|------------|---------------|---------------|-----------------|----------------|
| [sym] | $[price] | [%] | [strategy] | [%] | [#/#/#] | [BUY/HOLD/AVOID] |

### Key Market Insights
- [Insight about overall market condition]
- [Best opportunity identified]  
- [Key risks or warnings]

## 🎯 Investment Recommendations

### 🟢 BUY Recommendations
[For each stock worth buying:]

#### [SYMBOL] - $[price]
**Recommendation: BUY | Confidence: HIGH/MEDIUM/LOW | Position: [%] of portfolio**
- Best Strategy: [name] with [excess return]%
- Signal Consensus: [X/4 bullish]
- Why: [2-3 reasons]
- Entry: $[level] | Stop Loss: $[level] | Target: $[level]

### ⚪ HOLD/WATCH
[Stocks that are neutral - brief notes]

### ❌ AVOID
[Stocks to avoid for technical trading - brief reasons]

## 📈 Individual Stock Analysis

[For each stock, include:]
### [SYMBOL] - $[price]
**Overall: [RECOMMENDATION]**

| Strategy | Signal | Return | Excess | Sharpe | Verdict |
|----------|--------|--------|--------|--------|---------|
| Bollinger-Fib | [sig] | [%] | [%] | [ratio] | [OUT/UNDER] |
| MACD-Donchian | [sig] | [%] | [%] | [ratio] | [OUT/UNDER] |
| Connors-ZScore | [sig] | [%] | [%] | [ratio] | [OUT/UNDER] |
| Dual MA | [sig] | [%] | [%] | [ratio] | [OUT/UNDER] |

**Analysis:** [2-3 sentences interpreting the data]

## 📊 Strategy Effectiveness Ranking

| Strategy | Stocks Outperforming | Avg Excess Return | Success Rate |
|----------|---------------------|-------------------|--------------|
| [name] | [X out of Y] | [%] | [%] |

## 🎯 Portfolio Construction

### Recommended Allocation
- **[SYMBOL]**: [%] - [brief reason]
- **Cash**: [%] - [reason]

### Risk Management
- Maximum single position: [%]
- Stop loss strategy: [description]

## 📋 Action Plan

### Immediate Actions
1. [Action item]
2. [Action item]

*This analysis is for educational purposes only.*

---

## FINAL REMINDER

When you call final_answer, your answer MUST be the complete markdown report starting with:

# Multi-Stock Market Analysis Report

Do NOT say things like "I have analyzed the data" or "Here is what I found". 
Just output the report directly. The report IS your final answer.
"""


FUNDAMENTAL_ANALYSIS_PROMPT = """You are a senior fundamental analyst creating an investment thesis based on financial statements.

## CRITICAL: OUTPUT FORMAT REQUIREMENT
Your final answer MUST be the complete markdown report itself - not a summary or description of what you found.
When you finish gathering data, write the full formatted report as your final answer.

## Your Task
Analyze {symbol}'s fundamentals using the fundamental_analysis_report tool with period='{period}'.

## Instructions
1. Call the fundamental_analysis_report tool for {symbol}
2. Extract and interpret all financial metrics
3. Create a comprehensive fundamental analysis report

## Required Report Structure

Create a markdown report with these sections:

# {symbol} Fundamental Analysis Report
*Analysis Date: [today's date]*  
*Data Period: {period}*

## Company Overview
[From tool output: company name, sector, industry, business description]

## 📊 Executive Summary

### Investment Thesis
[2-3 paragraphs: Is this a good investment? Why or why not?]

### Key Metrics at a Glance

| Metric | Value | Assessment |
|--------|-------|------------|
| Revenue | $[amount] | [growing/declining] |
| Net Income | $[amount] | [trend] |
| Revenue Growth | [%] | [strong/weak/negative] |
| Net Margin | [%] | [healthy/concerning] |
| Debt-to-Equity | [ratio] | [conservative/aggressive] |
| Current Ratio | [ratio] | [liquid/illiquid] |
| Free Cash Flow | $[amount] | [positive/negative] |

## 💰 Income Statement Analysis

### Revenue Performance
- Current Revenue: $[amount]
- YoY Growth: [%]
- Trend Analysis: [interpretation]

### Profitability
- Net Income: $[amount]
- Net Margin: [%]
- EBITDA: $[amount]
- Interpretation: [is the company profitable? margins expanding/contracting?]

## 📋 Balance Sheet Strength

### Asset Quality
- Total Assets: $[amount]
- Asset composition analysis

### Leverage & Solvency
- Total Liabilities: $[amount]
- Debt-to-Equity: [ratio]
- Assessment: [is leverage manageable?]

### Liquidity Position
- Current Ratio: [ratio]
- Working capital assessment

## 💵 Cash Flow Analysis

### Operating Cash Flow
- Amount: $[amount]
- Quality of earnings assessment

### Capital Allocation
- CapEx: $[amount]
- Free Cash Flow: $[amount]
- Cash generation ability

## 🎯 Investment Assessment

### Strengths
- [Strength 1 with data]
- [Strength 2 with data]
- [Strength 3 with data]

### Risks & Concerns
- [Risk 1 with data]
- [Risk 2 with data]

### Valuation Perspective
[Based on the metrics, is this stock potentially undervalued/overvalued/fairly valued?]

## Final Recommendation: **[BUY/HOLD/SELL]**

### Investment Rationale
[3-4 bullet points supporting the recommendation]

### Suitable For
- [Type of investor this suits]
- [Investment horizon]
- [Risk tolerance level]

### Key Catalysts to Watch
1. [Catalyst 1]
2. [Catalyst 2]

*This analysis is for educational purposes only. Verify data against official SEC filings.*

---

## FINAL REMINDER

When you call final_answer, your answer MUST be the complete markdown report starting with:

# {symbol} Fundamental Analysis Report

Do NOT say things like "I have analyzed the financials" or "The tool returned...". 
Just output the full report directly. The report IS your final answer.
"""


MULTI_SECTOR_ANALYSIS_PROMPT = """You are a senior portfolio strategist creating a comprehensive multi-sector market analysis report.

## CRITICAL: OUTPUT FORMAT REQUIREMENT
Your final answer MUST be the complete markdown report itself - not a summary or description of what you found.
When you finish gathering data, write the full formatted report as your final answer.

## CRITICAL: DO NOT STOP EARLY
You MUST analyze ALL stocks in ALL sectors before writing the report.
Total sectors: {sector_count}
Total stocks: {total_stocks}
This requires approximately {total_tool_calls} tool calls. Do NOT stop until all data is collected.

## Your Task
Analyze these sectors and their stocks:

{sectors_formatted}

Period: {period}

For EACH stock in EACH sector, call these 4 strategy tools:
1. bollinger_fibonacci_analysis
2. macd_donchian_analysis  
3. connors_zscore_analysis
4. dual_moving_average_analysis

## Instructions
1. Process each sector one by one
2. For each stock, call all 4 tools and collect metrics
3. After ALL sectors are analyzed, write the comprehensive report
4. Compare performance ACROSS sectors
5. Identify the BEST opportunities across ALL sectors

## Required Report Structure (COPY THIS EXACTLY):

# Multi-Sector Market Analysis Report
*Analysis Date: [today's date]*  
*Period: {period} | Total Stocks Analyzed: {total_stocks} | Sectors: {sector_count}*

---

## 📊 Executive Summary

### Cross-Sector Performance Overview

| Sector | Stocks | Avg Buy & Hold | Avg Strategy Excess | Success Rate | Best Opportunities |
|--------|--------|----------------|---------------------|--------------|-------------------|
| [Sector 1] | [count] | [%] | [%] | [%] | [top 1-2 symbols] |
| [Sector 2] | [count] | [%] | [%] | [%] | [top 1-2 symbols] |
| [Sector 3] | [count] | [%] | [%] | [%] | [top 1-2 symbols] |
| **OVERALL** | **{total_stocks}** | **[%]** | **[%]** | **[%]** | **[top picks]** |

### Key Market Insights
🔴/🟢/🟡 [Overall market assessment - bearish/bullish/mixed technical environment]
🏆 [Sector leadership - which sector is strongest]
💡 [Number of clear opportunities identified]
⚠️ [Key risks - volatility, sector-specific concerns]

---

## 🎯 Final Investment Recommendations

### 🟢 PRIORITY INVESTMENTS (Top 2-3 stocks across ALL sectors)

#### 1. [SYMBOL] - $[price] | [Sector]
**🎯 STRONG BUY | 📊 HIGH CONFIDENCE | 💰 [POSITION SIZE] (X-Y%)**

- **Performance**: [X/4] strategies outperform buy-and-hold
- **Best Strategy**: [name] (+[excess]% excess return)
- **Signal Consensus**: [Bullish/Mixed/Bearish] across indicators
- **Risk Level**: [Low/Medium/High]
- **Why [SYMBOL]**: [2-3 sentence rationale]

#### 2. [SYMBOL] - $[price] | [Sector]
[Same structure as above]

### 🔵 SECONDARY OPPORTUNITIES (2-3 stocks)

#### [SYMBOL] - $[price] | [Sector]
**🎯 BUY | 📊 MEDIUM CONFIDENCE | 💰 SMALL POSITION (1-2%)**
[Brief rationale]

### ❌ AVOID (Stocks with poor technical performance)
[List symbols by sector with brief reason]

---

## 📈 Sector-by-Sector Analysis

### 🏦 [Sector 1 Name]
**Performance**: [avg return]% avg return | [success rate]% technical success rate

**Sector Summary:**
[2-3 sentences about sector technical performance]

**Individual Stocks:**

| Symbol | Price | Buy&Hold | Best Strategy | Best Excess | Signals (B/H/S) | Rating |
|--------|-------|----------|---------------|-------------|-----------------|--------|
| [SYM] | $[X] | [%] | [strategy] | [%] | [#/#/#] | [BUY/HOLD/AVOID] |

**Top Pick in Sector:** [SYMBOL] - [1 sentence reason]

### 💻 [Sector 2 Name]
[Same structure]

### ⚡ [Sector 3 Name]
[Same structure]

---

## 📊 Strategy Effectiveness Across Sectors

| Strategy | Sector 1 Success | Sector 2 Success | Sector 3 Success | Overall |
|----------|------------------|------------------|------------------|---------|
| Bollinger-Fibonacci | [%] | [%] | [%] | [%] |
| MACD-Donchian | [%] | [%] | [%] | [%] |
| Connors-ZScore | [%] | [%] | [%] | [%] |
| Dual Moving Avg | [%] | [%] | [%] | [%] |

**Best Overall Strategy:** [name] with [X]% success rate across all stocks

---

## 🎯 Portfolio Construction

### Recommended Allocation

**CONSERVATIVE APPROACH (Lower Risk)**
- [%] Cash/Fixed Income
- [%] [Sector with best risk-adjusted returns]
- [%] [Secondary sector]
- [%] Individual picks: [specific symbols]

**AGGRESSIVE APPROACH (Higher Risk)**
- [%] Cash
- [%] [Primary sector]
- [%] Concentrated positions in top picks

### Position Sizing Guidelines
- **Maximum single position**: [%]
- **High-risk stocks**: [%] maximum
- **Sector exposure**: [%] maximum per sector

---

## 🔍 Market Outlook & Strategic Themes

### Current Market Environment
[Assessment of overall technical regime - bullish/bearish/mixed]

### Investment Themes for Next 6-12 Months
1. **[Theme 1]**: [Brief explanation with relevant stocks]
2. **[Theme 2]**: [Brief explanation with relevant stocks]
3. **[Theme 3]**: [Brief explanation with relevant stocks]

### Risk Factors to Monitor
- [Risk 1]
- [Risk 2]
- [Risk 3]

---

## 📋 Action Plan & Next Steps

### Immediate Actions (Next 30 Days)
1. [Action with specific stocks/amounts]
2. [Action]
3. [Action]

### Monitoring Schedule
- **Daily**: [what to watch]
- **Weekly**: [review items]
- **Monthly**: [rebalancing considerations]

### Success Metrics
- **Absolute Performance**: Target [%] annual return
- **Risk-Adjusted Returns**: Sharpe ratio > [X]
- **Downside Protection**: Maximum drawdown < [%]

---

## 📊 Appendix: Complete Holdings Summary

### PRIORITY HOLDINGS

| Symbol | Sector | Price | Action | Strategy | Excess Return | Risk | Position |
|--------|--------|-------|--------|----------|---------------|------|----------|
| [SYM] | [Sector] | $[X] | [BUY] | [strategy] | [%] | [risk] | [%] |

### AVOID HOLDINGS
[List by sector]

---

*This analysis represents a point-in-time assessment based on technical and fundamental factors. Market conditions change rapidly, and this report should be updated regularly. Past performance does not guarantee future results. Consider your risk tolerance and investment objectives before implementing any recommendations.*

---

## FINAL REMINDER

When you call final_answer, your answer MUST be the complete markdown report starting with:

# Multi-Sector Market Analysis Report

Do NOT provide meta-commentary. Output the FULL report as your final answer.
"""


COMBINED_ANALYSIS_PROMPT = """You are a senior investment analyst creating a comprehensive stock analysis that combines both Technical Analysis (TA) and Fundamental Analysis (FA).

## CRITICAL: OUTPUT FORMAT REQUIREMENT
Your final answer MUST be the complete markdown report itself - not a summary or description of what you found.
When you finish gathering data, write the full formatted report as your final answer.

## ANALYSIS PHILOSOPHY

**Why Combine TA + FA?**
- Fundamental Analysis tells you "WHAT to buy" - identifies companies with strong financials and intrinsic value
- Technical Analysis tells you "WHEN to buy" - identifies optimal entry/exit points based on price trends
- Combined approach provides a 360-degree view for more informed investment decisions

**The Combined Approach:**
1. FA assesses company health, profitability, and long-term value
2. TA identifies market sentiment, trends, and timing signals
3. When FA and TA signals ALIGN → High-conviction opportunity
4. When they DIVERGE → Caution required, understand why

## Your Task
Analyze {symbol} using BOTH fundamental and technical analysis:

**Step 1: Fundamental Analysis**
Call: fundamental_analysis_report with symbol='{symbol}' and period='{fundamental_period}'

**Step 2: Technical Analysis (4 strategies)**
Call all 4 with symbol='{symbol}' and period='{technical_period}':
1. bollinger_fibonacci_analysis
2. macd_donchian_analysis
3. connors_zscore_analysis
4. dual_moving_average_analysis

## Required Report Structure (COPY THIS EXACTLY):

# {symbol} Combined Investment Analysis
*Analysis Date: [today's date]*  
*Current Price: $[from technical tools]*

---

## 📊 Executive Summary

### Investment Thesis
[2-3 paragraphs synthesizing BOTH fundamental and technical perspectives:
- What does the company's financial health tell us?
- What does the technical picture tell us?
- Do they align or diverge? What does this mean?]

### Quick Assessment

| Dimension | Assessment | Signal |
|-----------|------------|--------|
| **Fundamental Health** | [Strong/Moderate/Weak] | [🟢/🟡/🔴] |
| **Technical Trend** | [Bullish/Neutral/Bearish] | [🟢/🟡/🔴] |
| **Valuation** | [Undervalued/Fair/Overvalued] | [🟢/🟡/🔴] |
| **Entry Timing** | [Favorable/Neutral/Poor] | [🟢/🟡/🔴] |
| **Risk Level** | [Low/Medium/High] | [🟢/🟡/🔴] |
| **Overall** | [Strong Buy/Buy/Hold/Sell/Strong Sell] | [signal] |

### Signal Alignment Analysis
**FA + TA Alignment: [ALIGNED / PARTIALLY ALIGNED / DIVERGENT]**

[Explanation: Do fundamental and technical signals point in the same direction?
- If ALIGNED: Both suggest the same action - high conviction
- If DIVERGENT: Explain the disconnect and what it means]

---

## 💰 Fundamental Analysis

### Company Profile
- **Company**: [Name from fundamental tool]
- **Sector/Industry**: [from tool]
- **Business**: [Brief description]

### Financial Health Scorecard

| Metric | Value | Assessment | Benchmark |
|--------|-------|------------|-----------|
| Revenue | $[amount] | [trend] | - |
| Revenue Growth | [%] | [Strong/Moderate/Weak] | >10% good |
| Net Income | $[amount] | [trend] | - |
| Net Margin | [%] | [Healthy/Moderate/Concerning] | >10% good |
| Debt-to-Equity | [ratio] | [Conservative/Moderate/Aggressive] | <1.0 good |
| Current Ratio | [ratio] | [Strong/Adequate/Weak] | >1.5 good |
| Free Cash Flow | $[amount] | [Positive/Negative] | Positive good |
| ROE | [%] | [Strong/Moderate/Weak] | >15% good |

### Fundamental Strengths
1. [Strength with specific data point]
2. [Strength with specific data point]
3. [Strength with specific data point]

### Fundamental Concerns
1. [Concern with specific data point]
2. [Concern with specific data point]

### Fundamental Verdict: [STRONG / MODERATE / WEAK]
[1-2 sentences summarizing fundamental quality]

---

## 📈 Technical Analysis

### Technical Overview
- **Current Price**: $[price]
- **Trend**: [Bullish/Bearish/Sideways]
- **Momentum**: [Strong/Moderate/Weak]

### Strategy Performance Summary

| Strategy | Signal | Return % | vs Buy&Hold | Sharpe | Max DD | Win Rate |
|----------|--------|----------|-------------|--------|--------|----------|
| Bollinger-Fibonacci | [signal] | [%] | [%] | [ratio] | [%] | [%] |
| MACD-Donchian | [signal] | [%] | [%] | [ratio] | [%] | [%] |
| Connors RSI-ZScore | [signal] | [%] | [%] | [ratio] | [%] | [%] |
| Dual Moving Average | [signal] | [%] | [%] | [ratio] | [%] | [%] |

### Signal Consensus
- **BUY signals**: [X] strategies
- **HOLD signals**: [X] strategies
- **SELL signals**: [X] strategies
- **Consensus**: [BUY/HOLD/SELL]

### Key Technical Levels
- **Resistance**: $[level]
- **Support**: $[level]
- **50-day EMA**: $[level]
- **200-day EMA**: $[level]

### Technical Verdict: [BULLISH / NEUTRAL / BEARISH]
[1-2 sentences summarizing technical picture]

---

## 🔄 Combined Analysis: Where FA Meets TA

### Alignment Matrix

| Factor | Fundamental View | Technical View | Alignment |
|--------|------------------|----------------|-----------|
| Overall Outlook | [Positive/Neutral/Negative] | [Bullish/Neutral/Bearish] | [✅/⚠️/❌] |
| Investment Horizon | [Long-term value?] | [Short-term momentum?] | [✅/⚠️/❌] |
| Risk Assessment | [Financial risk level] | [Volatility/drawdown risk] | [✅/⚠️/❌] |
| Entry Timing | [Valuation attractive?] | [Technical entry favorable?] | [✅/⚠️/❌] |

### Synthesis
[3-4 paragraphs combining both analyses:

**Paragraph 1 - Fundamental Foundation:**
What does the company's financial health tell us about its long-term prospects?

**Paragraph 2 - Technical Timing:**
What does the technical picture suggest about current market sentiment and optimal entry?

**Paragraph 3 - Alignment or Divergence:**
Do FA and TA agree? If yes, this strengthens conviction. If no, explain the divergence.

**Paragraph 4 - Investment Implications:**
What does this combined view mean for different types of investors?]

---

## 🎯 Final Recommendation: **[STRONG BUY / BUY / HOLD / SELL / STRONG SELL]**

### Confidence Level: [HIGH / MEDIUM / LOW]

### Rationale
[4-5 bullet points combining both FA and TA reasoning]

### Recommended Action by Investor Type

| Investor Type | Recommendation | Rationale |
|---------------|----------------|-----------|
| **Long-term (1+ years)** | [Action] | [FA-based reasoning] |
| **Swing Trader (weeks-months)** | [Action] | [TA-based reasoning] |
| **Short-term (days-weeks)** | [Action] | [TA signals] |

### Entry Strategy
- **Ideal Entry**: $[price level] - [reasoning from TA]
- **Alternative Entry**: $[price level] - [if waiting for pullback]
- **Avoid Entry If**: [condition based on TA]

### Exit Strategy
- **Profit Target 1**: $[level] ([%] gain) - [reasoning]
- **Profit Target 2**: $[level] ([%] gain) - [reasoning]
- **Stop Loss**: $[level] ([%] below entry) - [reasoning from TA]

### Position Sizing Guidance
- **Conservative**: [%] of portfolio - [for risk-averse investors]
- **Moderate**: [%] of portfolio - [balanced approach]
- **Aggressive**: [%] of portfolio - [high conviction based on FA+TA alignment]

---

## ⚠️ Risk Factors

### Fundamental Risks
1. [Risk from financial analysis]
2. [Risk from financial analysis]

### Technical Risks
1. [Risk from technical analysis]
2. [Risk from technical analysis]

### Combined Risk Assessment
[Overall risk evaluation considering both perspectives]

---

## 📋 Monitoring Checklist

### Fundamental Triggers (Review Quarterly)
- [ ] Earnings growth on track
- [ ] Margins stable or improving
- [ ] Debt levels manageable
- [ ] Cash flow positive

### Technical Triggers (Monitor Weekly/Daily)
- [ ] Price above/below key moving averages
- [ ] Strategy signals unchanged
- [ ] Volume patterns normal
- [ ] No breakdown of support levels

---

*This analysis combines fundamental and technical perspectives to provide a comprehensive investment view. Fundamental analysis identifies the quality of the investment, while technical analysis helps optimize entry and exit timing. Past performance does not guarantee future results. This is not financial advice.*

---

## FINAL REMINDER

When you call final_answer, your answer MUST be the complete markdown report starting with:

# {symbol} Combined Investment Analysis

Do NOT provide meta-commentary. Output the FULL report as your final answer.
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


def build_agent(model, tools: list, max_steps: int = 25):
    """Build a ToolCallingAgent with the given model and tools."""
    return ToolCallingAgent(
        tools=tools,
        model=model,
        max_steps=max_steps,
        verbosity_level=1,
    )


# =============================================================================
# ANALYSIS FUNCTIONS (All LLM-Powered)
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
) -> str:
    """
    Run comprehensive technical analysis on a single stock.
    
    Uses LLM to call 4 strategy tools and synthesize results into a report
    similar to the tesla_technical_analysis.md example.
    """
    model = build_model(model_id, model_provider, hf_token, openai_api_key, openai_base_url)
    agent = build_agent(model, STRATEGY_TOOLS, max_steps)
    
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
    max_steps: int = 50,  # More steps needed for multiple stocks
) -> str:
    """
    Scan multiple stocks and generate comparative analysis.
    
    Uses LLM to call strategy tools for each stock and create a report
    similar to banking_sector_comprehensive_analysis.md.
    """
    model = build_model(model_id, model_provider, hf_token, openai_api_key, openai_base_url)
    
    # Clean up symbols string
    if isinstance(symbols, list):
        symbols = ",".join(symbols)
    symbols_clean = symbols.replace(" ", "").upper()
    
    # Calculate symbol count for prompt
    symbol_list = [s.strip() for s in symbols_clean.split(",") if s.strip()]
    symbol_count = len(symbol_list) * 4  # 4 tools per stock
    
    # Adjust max_steps based on number of stocks (4 tools per stock + buffer)
    adjusted_max_steps = max(max_steps, symbol_count + 10)
    
    agent = build_agent(model, STRATEGY_TOOLS, adjusted_max_steps)
    
    prompt = MARKET_SCANNER_PROMPT.format(
        symbols=symbols_clean,
        period=period,
        symbol_count=symbol_count,
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
) -> str:
    """
    Run fundamental analysis on a stock's financial statements.
    
    Uses LLM to interpret financial data and create an investment thesis.
    """
    model = build_model(model_id, model_provider, hf_token, openai_api_key, openai_base_url)
    agent = build_agent(model, [fundamental_analysis_report], max_steps)
    
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
    max_steps: int = 100,  # Many steps needed for multi-sector
) -> str:
    """
    Run comprehensive multi-sector analysis comparing multiple sectors.
    
    Uses LLM to call strategy tools for all stocks across all sectors
    and generate a report like multi_sector_analysis_report.md.
    
    Args:
        sectors: Dictionary mapping sector names to comma-separated symbol strings
                 e.g., {"Banking": "JPM,BAC,WFC", "Technology": "AAPL,MSFT,GOOGL"}
        period: Historical period for analysis
        model_id: LLM model to use
        model_provider: Provider (litellm or inference)
        
    Returns:
        Comprehensive multi-sector markdown report
    """
    model = build_model(model_id, model_provider, hf_token, openai_api_key, openai_base_url)
    
    # Calculate totals for the prompt
    sector_count = len(sectors)
    total_stocks = 0
    sectors_formatted_lines = []
    
    for sector_name, symbols in sectors.items():
        if isinstance(symbols, list):
            symbol_list = symbols
        else:
            symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        
        total_stocks += len(symbol_list)
        symbols_str = ", ".join(symbol_list)
        sectors_formatted_lines.append(f"**{sector_name}**: {symbols_str}")
    
    sectors_formatted = "\n".join(sectors_formatted_lines)
    total_tool_calls = total_stocks * 4  # 4 tools per stock
    
    # Adjust max_steps based on total tool calls needed
    adjusted_max_steps = max(max_steps, total_tool_calls + 15)
    
    agent = build_agent(model, STRATEGY_TOOLS, adjusted_max_steps)
    
    prompt = MULTI_SECTOR_ANALYSIS_PROMPT.format(
        sectors_formatted=sectors_formatted,
        period=period,
        sector_count=sector_count,
        total_stocks=total_stocks,
        total_tool_calls=total_tool_calls,
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
    max_steps: int = 35,  # 5 tools needed
) -> str:
    """
    Run combined Technical + Fundamental analysis on a single stock.
    
    This approach combines:
    - Fundamental Analysis: "What to buy" - company health, financials, intrinsic value
    - Technical Analysis: "When to buy" - price trends, momentum, entry/exit timing
    
    The combination provides a 360-degree investment view:
    - When FA and TA align → High conviction opportunity
    - When they diverge → Caution required
    
    Args:
        symbol: Ticker symbol to analyze
        technical_period: Period for technical analysis (default: 1y)
        fundamental_period: Period for fundamental data (default: 3y)
        model_id: LLM model to use
        model_provider: Provider (litellm or inference)
        
    Returns:
        Comprehensive combined analysis markdown report
    """
    model = build_model(model_id, model_provider, hf_token, openai_api_key, openai_base_url)
    
    # Include both strategy tools and fundamental tool
    combined_tools = STRATEGY_TOOLS + [fundamental_analysis_report]
    
    agent = build_agent(model, combined_tools, max_steps)
    
    prompt = COMBINED_ANALYSIS_PROMPT.format(
        symbol=symbol.upper(),
        technical_period=technical_period,
        fundamental_period=fundamental_period,
    )
    
    return agent.run(prompt)


# =============================================================================
# LEGACY SUPPORT - Keep run_agent for backward compatibility
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
    stream: bool,  # Ignored for ToolCallingAgent
    verbosity: int,  # Ignored - using default
) -> str:
    """Legacy function for backward compatibility. Calls run_technical_analysis."""
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
        description="Run LLM-powered stock analysis using MCP finance tools.",
    )
    parser.add_argument("symbol", help="Ticker symbol(s) to analyze")
    parser.add_argument(
        "--mode",
        choices=["technical", "scanner", "fundamental"],
        default="technical",
        help="Analysis mode (default: technical)",
    )
    parser.add_argument("--period", default="1y", help="Historical period (default: 1y)")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID, help="Model identifier")
    parser.add_argument("--model-provider", default=DEFAULT_MODEL_PROVIDER, help="Provider")
    parser.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS, help="Max agent steps")
    parser.add_argument("--output", type=Path, help="Save report to file")
    
    args = parser.parse_args()
    
    try:
        configure_finance_tools()
        
        if args.mode == "technical":
            result = run_technical_analysis(
                symbol=args.symbol,
                period=args.period,
                model_id=args.model_id,
                model_provider=args.model_provider,
                max_steps=args.max_steps,
            )
        elif args.mode == "scanner":
            result = run_market_scanner(
                symbols=args.symbol,
                period=args.period,
                model_id=args.model_id,
                model_provider=args.model_provider,
                max_steps=args.max_steps,
            )
        elif args.mode == "fundamental":
            result = run_fundamental_analysis(
                symbol=args.symbol,
                period=args.period,
                model_id=args.model_id,
                model_provider=args.model_provider,
                max_steps=args.max_steps,
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