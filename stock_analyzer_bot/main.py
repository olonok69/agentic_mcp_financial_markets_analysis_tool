"""Command-line entry point for the smolagents-powered stock analyzer bot."""
from __future__ import annotations

import argparse
import os
import textwrap
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from smolagents import CodeAgent, InferenceClientModel, LiteLLMModel

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
DEFAULT_MODEL_ID = os.getenv("SMOLAGENT_MODEL_ID", "meta-llama/Meta-Llama-3.1-8B-Instruct")
DEFAULT_MODEL_PROVIDER = os.getenv("SMOLAGENT_MODEL_PROVIDER", "auto").lower()
PROMPT_TEMPLATE = """You are a senior quantitative analyst. Analyze ticker {symbol}.
You MUST call each of the following Python functions exactly once using symbol='{symbol}' and period='{period}'.
Store every response in uniquely named variables that do NOT reuse the function names (e.g., use `bollinger_zscore_report`, never `bollinger_zscore_analysis = ...`).
Do not write helper functions that attempt to parse or convert the tool text into numbers—summarize the strings directly and quote key metrics verbatim instead of re-computing them.
Every time you execute Python code, follow this exact structure so the interpreter can run it:
Thought: explain what the code is about to do
<code>
# python code here
</code>
    - bollinger_zscore_analysis
    - bollinger_fibonacci_analysis
    - macd_donchian_analysis
    - connors_zscore_analysis
    - dual_moving_average_analysis
Store every tool response, then synthesize a markdown report with sections:
    1. Strategy Highlights (one bullet per tool)
    2. Consensus Outlook (state BUY/SELL/HOLD consensus with justification)
    3. Risk Metrics (surface drawdowns, Sharpe, volatility mentioned by tools)
    4. Final Recommendation (actionable guidance + confidence)
Cite concrete metrics from the tool outputs where possible. Respond only with markdown."""


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
        help="Model identifier passed to smolagents' InferenceClientModel",
    )
    parser.add_argument(
        "--model-provider",
        choices=["auto", "inference", "litellm"],
        default=DEFAULT_MODEL_PROVIDER,
        help="Select the backend implementation (auto detects from model id)",
    )
    parser.add_argument(
        "--hf-token",
        default=os.getenv("HF_TOKEN"),
        help="Hugging Face token used by the inference client (falls back to HF_TOKEN env variable)",
    )
    parser.add_argument(
        "--openai-api-key",
        default=os.getenv("OPENAI_API_KEY"),
        help="API key used when --model-provider=litellm (falls back to OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--openai-base-url",
        default=os.getenv("OPENAI_BASE_URL"),
        help="Optional custom base URL for LiteLLM/OpenAI compatible endpoints",
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
    # Basic heuristic: Hugging Face repos contain a slash
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


def build_prompt(symbol: str, period: str) -> str:
    return textwrap.dedent(PROMPT_TEMPLATE.format(symbol=symbol, period=period)).strip()


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
    agent = CodeAgent(
        tools=STRATEGY_TOOLS,
        model=model,
        max_steps=max_steps,
        verbosity_level=verbosity,
        stream_outputs=stream,
    )
    prompt = build_prompt(symbol.upper(), period)
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
