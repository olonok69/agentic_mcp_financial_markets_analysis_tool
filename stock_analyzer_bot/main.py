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
import os
from typing import Dict, Optional

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


def build_model(
    model_id: str,
    provider: str,
    api_key: Optional[str] = None,
    hf_token: Optional[str] = None,
    api_base: Optional[str] = None,
):
    """Create an LLM model instance for ToolCallingAgent."""
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


def build_agent(model, tools: list, max_steps: int = DEFAULT_MAX_STEPS):
    """Create a ToolCallingAgent with HIGH-LEVEL tools."""
    return ToolCallingAgent(
        tools=tools,
        model=model,
        max_steps=max_steps,
        verbosity_level=1,
    )


# ===========================================================================
# Prompts for HIGH-LEVEL Tool Usage
# ===========================================================================

TECHNICAL_ANALYSIS_PROMPT = """You are a senior financial analyst. Analyze {symbol} using technical analysis.

YOUR TASK:
Call the comprehensive_performance_report tool to get a complete multi-strategy analysis.

TOOL TO USE:
- comprehensive_performance_report(symbol="{symbol}", period="{period}")

CRITICAL FORMATTING RULES:
- NEVER use markdown tables with pipe characters (|) - they break the display
- NEVER put multiple data points on a single line
- Put each piece of information on its OWN LINE
- Use line breaks between sections
- Use USD for currency (never use the dollar sign)
- Do NOT use asterisks or italic text

OUTPUT FORMAT - Follow this EXACTLY:

1. EXECUTIVE SUMMARY

Symbol: {symbol}
Analysis Period: {period}
Current Price: [value] USD
Overall Recommendation: [BUY/SELL/HOLD]
Confidence Level: [HIGH/MEDIUM/LOW]

---

2. STRATEGY RESULTS

2.1 Bollinger Bands and Fibonacci Retracement

Signal: [BUY/SELL/HOLD]
Strategy Return: [percentage]
Excess Return vs Buy-Hold: [percentage]
Sharpe Ratio: [value]
Max Drawdown: [percentage]
Win Rate: [percentage]

Key Observation: [one sentence about this strategy]

2.2 MACD-Donchian Combined

Signal: [BUY/SELL/HOLD]
Strategy Return: [percentage]
Excess Return vs Buy-Hold: [percentage]
Sharpe Ratio: [value]
Max Drawdown: [percentage]
Win Rate: [percentage]

Key Observation: [one sentence about this strategy]

2.3 Connors RSI and Z-Score Combined

Signal: [BUY/SELL/HOLD]
Strategy Return: [percentage]
Excess Return vs Buy-Hold: [percentage]
Sharpe Ratio: [value]
Max Drawdown: [percentage]
Win Rate: [percentage]

Key Observation: [one sentence about this strategy]

2.4 Dual Moving Average Crossover

Signal: [BUY/SELL/HOLD]
Strategy Return: [percentage]
Excess Return vs Buy-Hold: [percentage]
Sharpe Ratio: [value]
Max Drawdown: [percentage]
Win Rate: [percentage]

Key Observation: [one sentence about this strategy]

---

3. SIGNAL CONSENSUS

Total BUY Signals: [count]
Total SELL Signals: [count]
Total HOLD Signals: [count]

Consensus Direction: [BULLISH/BEARISH/NEUTRAL]
Consensus Strength: [STRONG/MODERATE/WEAK]

---

4. PERFORMANCE SUMMARY

Best Performing Strategy: [name]
- Excess Return: [percentage]
- Why it outperformed: [brief explanation]

Buy and Hold Return: [percentage]

Strategies that beat Buy-Hold:
- [list each strategy that outperformed]

---

5. FINAL RECOMMENDATION

Action: [BUY/SELL/HOLD]
Confidence: [HIGH/MEDIUM/LOW]

Rationale:
[2-3 sentences explaining WHY this recommendation based on the data above]

Supporting Evidence:
- [Strategy 1] shows [signal] with [specific metric]
- [Strategy 2] shows [signal] with [specific metric]
- [X] out of 4 strategies agree on [direction]

---

6. RISK FACTORS

- Strategy disagreement: [X] strategies show conflicting signals
- [Other specific risks from the analysis]
- Conditions that would change this recommendation: [list]

---

REMEMBER: Each data point on its own line. No tables. No pipe characters. Extract real numbers from the tool.
"""

MARKET_SCANNER_PROMPT = """You are a senior portfolio analyst. Scan these stocks: {symbols}

YOUR TASK:
Call the unified_market_scanner tool to analyze ALL stocks at once.

TOOL TO USE:
- unified_market_scanner(symbols="{symbols}", period="{period}", output_format="detailed")

CRITICAL FORMATTING RULES:
- NEVER use markdown tables with pipe characters (|) - they break the display
- NEVER put multiple data points on a single line
- Put each piece of information on its OWN LINE
- Use line breaks between sections
- Use USD for currency (never use the dollar sign)
- Do NOT use asterisks or italic text

OUTPUT FORMAT - Follow this EXACTLY:

1. MARKET SCANNER OVERVIEW

Stocks Analyzed: {symbols}
Analysis Period: {period}
Scanner Date: [date]

---

2. STOCK RANKINGS

(List stocks from best to worst opportunity)

Rank 1: [SYMBOL]
- Buy Signals: [X]/5 strategies
- Overall Score: [value]
- Recommendation: [BUY/HOLD/AVOID]

Rank 2: [SYMBOL]
- Buy Signals: [X]/5 strategies
- Overall Score: [value]
- Recommendation: [BUY/HOLD/AVOID]

Rank 3: [SYMBOL]
- Buy Signals: [X]/5 strategies
- Overall Score: [value]
- Recommendation: [BUY/HOLD/AVOID]

(continue for all stocks)

---

3. INDIVIDUAL STOCK DETAILS

3.1 [FIRST SYMBOL]

Current Price: [value] USD
Buy and Hold Return: [percentage]

Strategy Signals:

Bollinger Z-Score:
- Signal: [BUY/SELL/NEUTRAL]
- Score: [value]
- Excess Return: [percentage]

Bollinger-Fibonacci:
- Signal: [BUY/SELL/NEUTRAL]
- Score: [value]
- Excess Return: [percentage]

MACD-Donchian:
- Signal: [BUY/SELL/NEUTRAL]
- Score: [value]
- Excess Return: [percentage]

Connors RSI-ZScore:
- Signal: [BUY/SELL/NEUTRAL]
- Score: [value]
- Excess Return: [percentage]

Dual Moving Average:
- Signal: [BUY/SELL/NEUTRAL]
- Score: [value]
- Excess Return: [percentage]

Consensus: [X] BUY, [Y] SELL, [Z] NEUTRAL
Best Strategy: [name] with [percentage] excess return

---

3.2 [SECOND SYMBOL]

(repeat same format for each stock)

---

4. STRATEGY PERFORMANCE SUMMARY

Best Overall Strategy: [name]
- Average Excess Return: [percentage]
- Stocks where it outperformed: [list]

Worst Overall Strategy: [name]
- Average Excess Return: [percentage]

Strategy Agreement: [High/Medium/Low] - [brief explanation]

---

5. RECOMMENDATIONS

Top Picks:
- [SYMBOL 1]: [reason based on data]
- [SYMBOL 2]: [reason based on data]

Stocks to Avoid:
- [SYMBOL]: [reason based on data]

---

6. MARKET ASSESSMENT

Overall Sentiment: [BULLISH/BEARISH/NEUTRAL]
Total BUY signals: [count] across all stocks
Total SELL signals: [count] across all stocks

Key Observation: [main takeaway]

---

REMEMBER: Each data point on its own line. No tables. No pipe characters. Extract real numbers from the tool.
"""

FUNDAMENTAL_ANALYSIS_PROMPT = """You are a senior fundamental analyst. Analyze {symbol}'s financials.

YOUR TASK:
Call the fundamental_analysis_report tool to get complete financial analysis.

TOOL TO USE:
- fundamental_analysis_report(symbol="{symbol}", period="{period}")

CRITICAL FORMATTING RULES:
- NEVER use markdown tables with pipe characters (|) - they break the display
- NEVER put multiple data points on a single line
- Put each piece of information on its OWN LINE
- Use line breaks between sections
- Use USD for currency (never use the dollar sign)
- Do NOT use asterisks or italic text

OUTPUT FORMAT - Follow this EXACTLY:

1. COMPANY OVERVIEW

Symbol: {symbol}
Analysis Period: {period}

---

2. INCOME STATEMENT ANALYSIS

Revenue:
- Total Revenue: [value] USD
- Revenue Growth: [percentage]
- Trend: [increasing/decreasing/stable]

Profitability:
- Net Income: [value] USD
- Gross Margin: [percentage]
- Operating Margin: [percentage]
- Net Margin: [percentage]

---

3. BALANCE SHEET ANALYSIS

Assets:
- Total Assets: [value] USD
- Cash and Equivalents: [value] USD

Liabilities and Equity:
- Total Debt: [value] USD
- Shareholders Equity: [value] USD
- Debt-to-Equity Ratio: [value]

---

4. CASH FLOW ANALYSIS

Operating Cash Flow: [value] USD
Free Cash Flow: [value] USD
Cash Flow Trend: [positive/negative/stable]

---

5. KEY FINANCIAL RATIOS

ROE (Return on Equity):
- Value: [percentage]
- Assessment: [Good/Fair/Poor]
- Interpretation: [one sentence]

ROA (Return on Assets):
- Value: [percentage]
- Assessment: [Good/Fair/Poor]
- Interpretation: [one sentence]

Current Ratio:
- Value: [number]
- Assessment: [Good/Fair/Poor]
- Interpretation: [one sentence]

Quick Ratio:
- Value: [number]
- Assessment: [Good/Fair/Poor]
- Interpretation: [one sentence]

P/E Ratio:
- Value: [number]
- Assessment: [Good/Fair/Poor]
- Interpretation: [one sentence]

---

6. FINANCIAL HEALTH ASSESSMENT

Overall Health: [STRONG/MODERATE/WEAK]

Strengths:
- [Strength 1 based on data above]
- [Strength 2 based on data above]

Weaknesses:
- [Weakness 1 based on data above]
- [Weakness 2 based on data above]

---

7. INVESTMENT RECOMMENDATION

Action: [BUY/SELL/HOLD]
Confidence: [HIGH/MEDIUM/LOW]

Rationale:
[2-3 sentences explaining the recommendation based on the financial data]

Key Supporting Metrics:
- [Metric 1]: [Value] - supports recommendation because [reason]
- [Metric 2]: [Value] - supports recommendation because [reason]

---

8. RISK FACTORS

- [Financial risk 1]
- [Financial risk 2]

Conditions to Monitor:
- [what would change the outlook]

---

REMEMBER: Each data point on its own line. No tables. No pipe characters. Extract real numbers from the tool.
"""

MULTI_SECTOR_PROMPT = """You are a senior portfolio strategist. Analyze these sectors:

{sector_details}

YOUR TASK:
For EACH sector, call unified_market_scanner to analyze all stocks in that sector.
Then synthesize cross-sector insights.

TOOLS TO USE:
For each sector, call:
- unified_market_scanner(symbols="<sector_symbols>", period="{period}", output_format="detailed")

CRITICAL FORMATTING RULES:
- NEVER use markdown tables with pipe characters (|) - they break the display
- NEVER put multiple data points on a single line
- Put each piece of information on its OWN LINE
- Use line breaks between sections
- Use USD for currency (never use the dollar sign)
- Do NOT use asterisks or italic text

OUTPUT FORMAT - Follow this EXACTLY:

1. MULTI-SECTOR ANALYSIS OVERVIEW

Sectors Analyzed: [list]
Total Stocks: [count]
Analysis Period: {period}

---

2. SECTOR RESULTS

2.1 [SECTOR NAME 1]

Stocks Analyzed: [list]
Best Performer: [Symbol]
Best Performer Return: [percentage]
Sector Outlook: [BULLISH/BEARISH/NEUTRAL]
Average Buy Signals: [X]/5 strategies

Top Stock Details:
- Symbol: [best stock]
- Buy Signals: [count]/5
- Reason: [why it's the top pick]

---

2.2 [SECTOR NAME 2]

(repeat same format)

---

(continue for all sectors)

---

3. SECTOR RANKINGS

Rank 1: [SECTOR NAME]
- Average Score: [value]
- Best Stock: [symbol]
- Outlook: [BULLISH/BEARISH/NEUTRAL]

Rank 2: [SECTOR NAME]
- Average Score: [value]
- Best Stock: [symbol]
- Outlook: [BULLISH/BEARISH/NEUTRAL]

(continue for all sectors)

---

4. TOP PICKS ACROSS ALL SECTORS

Pick 1: [SYMBOL] from [SECTOR]
- Buy Signals: [X]/5 strategies
- Best Strategy: [name]
- Best Strategy Return: [percentage]
- Why Selected: [specific reasoning]

Pick 2: [SYMBOL] from [SECTOR]
- Buy Signals: [X]/5 strategies
- Best Strategy: [name]
- Best Strategy Return: [percentage]
- Why Selected: [specific reasoning]

Pick 3: [SYMBOL] from [SECTOR]
- Buy Signals: [X]/5 strategies
- Best Strategy: [name]
- Best Strategy Return: [percentage]
- Why Selected: [specific reasoning]

---

5. PORTFOLIO ALLOCATION BY SECTOR

[Sector 1]: [X]%
- Reason: [based on data]

[Sector 2]: [X]%
- Reason: [based on data]

[Sector 3]: [X]%
- Reason: [based on data]

---

6. OVERALL MARKET ASSESSMENT

Strongest Sector: [NAME]
- Why: [data points]

Weakest Sector: [NAME]
- Why: [data points]

Market Sentiment: [BULLISH/BEARISH/NEUTRAL]

---

7. STRATEGIC RECOMMENDATIONS

Primary Recommendation:
[Clear action with supporting data]

Risk Factors:
- [key risk 1]
- [key risk 2]

Alternative Approach:
[For different risk tolerance]

---

REMEMBER: Each data point on its own line. No tables. No pipe characters. Extract real numbers from the tools.
"""

COMBINED_ANALYSIS_PROMPT = """You are a senior investment analyst. Perform complete analysis of {symbol}.

YOUR TASK:
Combine BOTH technical and fundamental analysis:
1. Call comprehensive_performance_report for technical analysis
2. Call fundamental_analysis_report for fundamental analysis

TOOLS TO USE:
- comprehensive_performance_report(symbol="{symbol}", period="{technical_period}")
- fundamental_analysis_report(symbol="{symbol}", period="{fundamental_period}")

CRITICAL FORMATTING RULES:
- NEVER use markdown tables with pipe characters (|) - they break the display
- NEVER put multiple data points on a single line
- Put each piece of information on its OWN LINE
- Use line breaks between sections
- Use USD for currency (never use the dollar sign)
- Do NOT use asterisks or italic text

OUTPUT FORMAT - Follow this EXACTLY:

1. INVESTMENT ANALYSIS SUMMARY

Symbol: {symbol}
Technical Period: {technical_period}
Fundamental Period: {fundamental_period}
Final Recommendation: [BUY/SELL/HOLD]
Confidence Level: [HIGH/MEDIUM/LOW]

---

2. TECHNICAL ANALYSIS RESULTS

2.1 Strategy Signals

Bollinger-Fibonacci Strategy:
- Signal: [BUY/SELL/HOLD]
- Return vs Buy-Hold: [percentage]
- Sharpe Ratio: [value]
- Max Drawdown: [percentage]

MACD-Donchian Strategy:
- Signal: [BUY/SELL/HOLD]
- Return vs Buy-Hold: [percentage]
- Sharpe Ratio: [value]
- Max Drawdown: [percentage]

Connors RSI-ZScore Strategy:
- Signal: [BUY/SELL/HOLD]
- Return vs Buy-Hold: [percentage]
- Sharpe Ratio: [value]
- Max Drawdown: [percentage]

Dual Moving Average Strategy:
- Signal: [BUY/SELL/HOLD]
- Return vs Buy-Hold: [percentage]
- Sharpe Ratio: [value]
- Max Drawdown: [percentage]

2.2 Technical Consensus

Signal Count: [X] BUY, [Y] SELL, [Z] HOLD
Technical Outlook: [BULLISH/BEARISH/NEUTRAL]
Confidence Level: [HIGH/MEDIUM/LOW]

2.3 Best Performing Strategy

Strategy Name: [name]
Excess Return: [percentage]
Reason: [brief explanation]

---

3. FUNDAMENTAL ANALYSIS RESULTS

3.1 Financial Health Snapshot

Revenue: [value] USD
Net Income: [value] USD
Free Cash Flow: [value] USD

3.2 Key Financial Ratios

ROE (Return on Equity):
- Value: [percentage]
- Assessment: [Good/Fair/Poor]

Debt-to-Equity:
- Value: [number]
- Assessment: [Good/Fair/Poor]

Current Ratio:
- Value: [number]
- Assessment: [Good/Fair/Poor]

P/E Ratio:
- Value: [number]
- Assessment: [Good/Fair/Poor]

3.3 Fundamental Outlook

Financial Health: [STRONG/MODERATE/WEAK]
Growth Trend: [POSITIVE/NEGATIVE/STABLE]

---

4. ALIGNMENT ANALYSIS

4.1 Technical View Summary:
[2-3 sentences summarizing technical outlook]

4.2 Fundamental View Summary:
[2-3 sentences summarizing fundamental outlook]

4.3 Agreement Assessment:
Do They Align: [YES/NO/PARTIAL]
Explanation: [why they agree or disagree]

---

5. INVESTMENT THESIS

5.1 Overall Recommendation: [BUY/SELL/HOLD]

5.2 Confidence Level: [HIGH/MEDIUM/LOW]

5.3 Supporting Evidence from Technical Analysis:
- [specific metric and what it indicates]
- [specific metric and what it indicates]

5.4 Supporting Evidence from Fundamental Analysis:
- [specific metric and what it indicates]
- [specific metric and what it indicates]

5.5 Entry Strategy:
[When and how to enter if recommending BUY]

5.6 Exit Considerations:
[When to exit or reconsider the position]

---

6. RISK ASSESSMENT

Technical Risks:
- [risk 1]
- [risk 2]

Fundamental Risks:
- [risk 1]
- [risk 2]

Conditions That Would Invalidate This Recommendation:
- [condition 1]
- [condition 2]

---

7. CONCLUSION

[2-3 sentence final summary with clear action recommendation]

---

REMEMBER: Each data point on its own line. No tables. No pipe characters. Extract real numbers from the tools.
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
) -> str:
    """
    Run technical analysis using comprehensive_performance_report (1 MCP call).
    
    ToolCallingAgent approach: Use high-level tool that does everything.
    """
    configure_finance_tools()
    
    model = build_model(
        model_id=model_id,
        provider=model_provider,
        api_key=openai_api_key,
        hf_token=hf_token,
        api_base=openai_base_url,
    )
    
    agent = build_agent(model, HIGH_LEVEL_TOOLS, max_steps=max_steps)
    
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
    max_steps: int = DEFAULT_MAX_STEPS,
) -> str:
    """
    Run market scanner using unified_market_scanner (1 MCP call).
    
    ToolCallingAgent approach: One tool call scans all stocks at once.
    """
    configure_finance_tools()
    
    model = build_model(
        model_id=model_id,
        provider=model_provider,
        api_key=openai_api_key,
        hf_token=hf_token,
        api_base=openai_base_url,
    )
    
    agent = build_agent(model, HIGH_LEVEL_TOOLS, max_steps=max_steps)
    
    prompt = MARKET_SCANNER_PROMPT.format(symbols=symbols, period=period)
    
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
) -> str:
    """
    Run fundamental analysis using fundamental_analysis_report (1 MCP call).
    
    ToolCallingAgent approach: One tool call gets all financials.
    """
    configure_finance_tools()
    
    model = build_model(
        model_id=model_id,
        provider=model_provider,
        api_key=openai_api_key,
        hf_token=hf_token,
        api_base=openai_base_url,
    )
    
    agent = build_agent(model, HIGH_LEVEL_TOOLS, max_steps=max_steps)
    
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
    max_steps: int = 30,  # More steps for multiple sectors
) -> str:
    """
    Run multi-sector analysis using unified_market_scanner per sector.
    
    ToolCallingAgent approach: One scanner call per sector (N calls total).
    """
    configure_finance_tools()
    
    model = build_model(
        model_id=model_id,
        provider=model_provider,
        api_key=openai_api_key,
        hf_token=hf_token,
        api_base=openai_base_url,
    )
    
    agent = build_agent(model, HIGH_LEVEL_TOOLS, max_steps=max_steps)
    
    # Format sector details for prompt
    sector_details = "\n".join([
        f"- {name}: {symbols}"
        for name, symbols in sectors.items()
    ])
    
    prompt = MULTI_SECTOR_PROMPT.format(
        sector_details=sector_details,
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
    max_steps: int = DEFAULT_MAX_STEPS,
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
    )
    
    agent = build_agent(model, HIGH_LEVEL_TOOLS, max_steps=max_steps)
    
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
    
    args = parser.parse_args()
    
    try:
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
        elif args.mode == "combined":
            result = run_combined_analysis(
                symbol=args.symbol,
                technical_period=args.period,
                model_id=args.model_id,
                model_provider=args.model_provider,
                max_steps=args.max_steps,
            )
        
        print(result)
        
    finally:
        shutdown_finance_tools()


if __name__ == "__main__":
    main()