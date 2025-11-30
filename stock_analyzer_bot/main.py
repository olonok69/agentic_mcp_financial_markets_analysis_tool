"""Command-line entry point for the smolagents-powered stock analyzer bot."""
from __future__ import annotations

import argparse
import os
import textwrap
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from smolagents import CodeAgent, ToolCallingAgent, InferenceClientModel, LiteLLMModel

# Support running either as a package module or as a standalone script.
if __package__ in (None, ""):
    import sys

    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from stock_analyzer_bot.tools import (  # type: ignore
        STRATEGY_TOOLS,
        configure_finance_tools,
        shutdown_finance_tools,
    )
else:
    from .tools import (
        STRATEGY_TOOLS,
        configure_finance_tools,
        shutdown_finance_tools,
    )

load_dotenv()
DEFAULT_MODEL_ID = os.getenv("SMOLAGENT_MODEL_ID", "gpt-4o-mini")
DEFAULT_MODEL_PROVIDER = os.getenv("SMOLAGENT_MODEL_PROVIDER", "litellm").lower()

# Prompt for CodeAgent (HuggingFace models)
CODE_AGENT_PROMPT = """Analyze {symbol} stock using these 4 strategy tools with period='{period}'.

Call each tool and store results:
1. bollinger_fibonacci_analysis(symbol="{symbol}", period="{period}")
2. macd_donchian_analysis(symbol="{symbol}", period="{period}")
3. connors_zscore_analysis(symbol="{symbol}", period="{period}")
4. dual_moving_average_analysis(symbol="{symbol}", period="{period}")

After getting all results, print a markdown report with:
- Executive Summary
- Strategy Highlights (one bullet per strategy)
- Consensus Outlook (BUY/SELL/HOLD based on strategy agreement)
- Risk Metrics (Sharpe ratios, volatility, drawdown)
- Final Recommendation

Include specific numbers from the tool outputs."""

# Prompt for ToolCallingAgent (OpenAI/LiteLLM models)
TOOL_CALLING_PROMPT = """You are a senior quantitative analyst. Analyze {symbol} stock.

Call ALL 4 of these tools with symbol='{symbol}' and period='{period}':
1. bollinger_fibonacci_analysis
2. macd_donchian_analysis
3. connors_zscore_analysis
4. dual_moving_average_analysis

After calling all tools, create a markdown report with these sections:

## Executive Summary
Brief overview of {symbol}'s technical position.

## Strategy Highlights
One bullet per strategy with key finding and signal.

## Consensus Outlook
Overall BUY/SELL/HOLD based on how many strategies agree.

## Risk Metrics
Key metrics: Sharpe ratios, volatility, max drawdown.

## Final Recommendation
Actionable guidance with confidence level.

Quote specific metrics from tool outputs."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the smolagents stock analyzer bot that taps into the MCP finance server.",
    )
    parser.add_argument("symbol", help="Ticker symbol to analyze (e.g. AAPL)")
    parser.add_argument(
        "--period",
        default="1y",
        help="Historical period to request from each MCP tool (default: 1y)",
    )
    parser.add_argument(
        "--server-script",
        type=Path,
        help="Override path to the MCP server entry point (defaults to server/main.py)",
    )
    parser.add_argument(
        "--model-id",
        default=DEFAULT_MODEL_ID,
        help="Model identifier (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--model-provider",
        choices=["auto", "inference", "litellm"],
        default=DEFAULT_MODEL_PROVIDER,
        help="Select the backend: inference (HuggingFace) or litellm (OpenAI)",
    )
    parser.add_argument(
        "--hf-token",
        default=os.getenv("HF_TOKEN"),
        help="Hugging Face token (falls back to HF_TOKEN env variable)",
    )
    parser.add_argument(
        "--openai-api-key",
        default=os.getenv("OPENAI_API_KEY"),
        help="API key for LiteLLM/OpenAI (falls back to OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--openai-base-url",
        default=os.getenv("OPENAI_BASE_URL"),
        help="Optional custom base URL for OpenAI-compatible endpoints",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=20,
        help="Maximum reasoning steps for the agent (default: 20)",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming outputs from smolagents",
    )
    parser.add_argument(
        "--verbosity",
        type=int,
        default=1,
        help="Set smolagents verbosity level (0-2)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to save the final markdown report",
    )
    return parser.parse_args()


def _resolve_provider(model_id: str, requested_provider: str) -> str:
    if requested_provider != "auto":
        return requested_provider
    # Heuristic: HuggingFace model IDs contain a slash (org/model)
    return "inference" if "/" in model_id else "litellm"


def build_model(
    model_id: str,
    hf_token: Optional[str],
    provider: str,
    openai_api_key: Optional[str],
    openai_base_url: Optional[str],
):
    resolved = _resolve_provider(model_id, provider)
    if resolved == "inference":
        return InferenceClientModel(model_id=model_id, token=hf_token)
    if resolved == "litellm":
        return LiteLLMModel(model_id=model_id, api_key=openai_api_key, api_base=openai_base_url)
    raise ValueError(f"Unsupported model provider: {resolved}")


def build_prompt(symbol: str, period: str, use_code_agent: bool) -> str:
    template = CODE_AGENT_PROMPT if use_code_agent else TOOL_CALLING_PROMPT
    return textwrap.dedent(template.format(symbol=symbol, period=period)).strip()


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
    model = build_model(model_id, hf_token, model_provider, openai_api_key, openai_base_url)
    
    # Determine which agent type to use based on provider
    resolved_provider = _resolve_provider(model_id, model_provider)
    use_code_agent = (resolved_provider == "inference")
    
    if use_code_agent:
        # CodeAgent for HuggingFace models - they work better with code generation
        agent = CodeAgent(
            tools=STRATEGY_TOOLS,
            model=model,
            max_steps=max_steps,
            verbosity_level=verbosity,
            stream_outputs=stream,
        )
    else:
        # ToolCallingAgent for OpenAI/LiteLLM - they support native tool calling
        agent = ToolCallingAgent(
            tools=STRATEGY_TOOLS,
            model=model,
            max_steps=max_steps,
            verbosity_level=verbosity,
        )
    
    prompt = build_prompt(symbol.upper(), period, use_code_agent)
    return agent.run(prompt)


def main() -> int:
    args = parse_args()
    try:
        configure_finance_tools(args.server_script)
        result = run_agent(
            symbol=args.symbol,
            period=args.period,
            model_id=args.model_id,
            hf_token=args.hf_token,
            model_provider=args.model_provider,
            openai_api_key=args.openai_api_key,
            openai_base_url=args.openai_base_url,
            max_steps=args.max_steps,
            stream=not args.no_stream,
            verbosity=args.verbosity,
        )
    except KeyboardInterrupt:
        print("Analysis interrupted by user.")
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