"""
ToolCallingAgent implementation using HIGH-LEVEL MCP tools.

#####################################################################
# TOOLCALLINGAGENT APPROACH
#####################################################################
#
# This agent uses HIGH-LEVEL tools that do everything in ONE MCP call.
# The MCP server handles all complexity internally.
#
# TOOLS USED:
#   - comprehensive_performance_report: Single stock → Full report (1 call)
#   - unified_market_scanner: Multi-stock → Rankings & analysis (1 call)
#   - fundamental_analysis_report: Financials → Investment thesis (1 call)
#
# ADVANTAGES:
#   - Simple: Few tool calls, predictable behavior
#   - Fast: MCP server optimizes internally
#   - Reliable: Less LLM orchestration needed
#
# COMPARISON WITH CodeAgent:
#   - ToolCallingAgent: "Give me everything for AAPL" → 1 call
#   - CodeAgent: "Let me call 4 tools and combine results" → 4+ calls
#
#####################################################################
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, Optional

from dotenv import load_dotenv
from smolagents import LiteLLMModel, InferenceClientModel, ToolCallingAgent

from .tools import (
    HIGH_LEVEL_TOOLS,
    configure_finance_tools,
    shutdown_finance_tools,
)

load_dotenv()

# Default configuration
DEFAULT_MODEL_ID = os.getenv("SMOLAGENT_MODEL_ID", "gpt-4o")
DEFAULT_MODEL_PROVIDER = os.getenv("SMOLAGENT_MODEL_PROVIDER", "litellm")
DEFAULT_MAX_STEPS = int(os.getenv("SMOLAGENT_MAX_STEPS", "15"))  # Fewer steps needed

__all__ = [
    "DEFAULT_MODEL_ID",
    "DEFAULT_MODEL_PROVIDER",
    "DEFAULT_MAX_STEPS",
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
This tool runs ALL 4 trading strategies internally and returns a comprehensive report.

TOOL TO USE:
- comprehensive_performance_report(symbol="{symbol}", period="{period}")

WHAT YOU'LL RECEIVE:
The tool returns a complete report with all 4 strategy results, performance metrics,
risk assessment, and final recommendation.

YOUR OUTPUT:
Present the report results directly. Do NOT add extra markdown headers or formatting.
Keep the output clean and readable. Do NOT call individual strategy tools.
"""

MARKET_SCANNER_PROMPT = """You are a senior portfolio analyst. Scan these stocks: {symbols}

YOUR TASK:
Call the unified_market_scanner tool to analyze ALL stocks at once.
This tool runs all strategies on all stocks and returns rankings.

TOOL TO USE:
- unified_market_scanner(symbols="{symbols}", period="{period}", output_format="detailed")

WHAT YOU'LL RECEIVE:
The tool returns a complete analysis with market overview, ranked stocks,
individual summaries, and recommendations.

YOUR OUTPUT:
Present the scanner results directly. Do NOT add extra markdown headers or bold text.
Keep the output clean and readable. Do NOT call individual tools for each stock.
"""

FUNDAMENTAL_ANALYSIS_PROMPT = """You are a senior fundamental analyst. Analyze {symbol}'s financials.

YOUR TASK:
Call the fundamental_analysis_report tool to get complete financial analysis.

TOOL TO USE:
- fundamental_analysis_report(symbol="{symbol}", period="{period}")

WHAT YOU'LL RECEIVE:
The tool returns analysis of Income Statement, Balance Sheet, Cash Flow,
Key Ratios, and an investment thesis with recommendation.

YOUR OUTPUT:
Present the fundamental analysis directly. Do NOT add extra markdown headers.
Keep the output clean and readable.
"""

MULTI_SECTOR_PROMPT = """You are a senior portfolio strategist. Analyze these sectors:

{sector_details}

YOUR TASK:
For EACH sector, call unified_market_scanner to analyze all stocks in that sector.
Then synthesize cross-sector insights.

TOOLS TO USE:
For each sector, call:
- unified_market_scanner(symbols="<sector_symbols>", period="{period}", output_format="summary")

YOUR OUTPUT:
After scanning all sectors, provide:
1. Sector-by-sector summary
2. Cross-sector comparison
3. Top picks across all sectors
4. Portfolio allocation by sector
5. Overall market assessment

Do NOT use large markdown headers. Keep output clean with plain text section labels.
"""

COMBINED_ANALYSIS_PROMPT = """You are a senior investment analyst. Perform complete analysis of {symbol}.

YOUR TASK:
Combine BOTH technical and fundamental analysis:
1. Call comprehensive_performance_report for technical analysis
2. Call fundamental_analysis_report for fundamental analysis

TOOLS TO USE:
- comprehensive_performance_report(symbol="{symbol}", period="{technical_period}")
- fundamental_analysis_report(symbol="{symbol}", period="{fundamental_period}")

YOUR OUTPUT:
Synthesize both analyses into a complete investment thesis:
1. Technical outlook
2. Fundamental health
3. Alignment analysis (do technicals and fundamentals agree?)
4. Final recommendation with conviction level
5. Entry/exit strategy if applicable

Do NOT use large markdown headers. Keep output clean and readable.
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
        f"- **{name}**: {symbols}"
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