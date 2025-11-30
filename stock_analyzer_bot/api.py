"""FastAPI backend that exposes the smolagents-powered MCP analysis bot."""
from __future__ import annotations

import logging
import time
import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .main import DEFAULT_MODEL_ID, DEFAULT_MODEL_PROVIDER, run_agent
from .tools import (
    ALL_TOOLS,
    comprehensive_performance_report,
    unified_market_scanner,
    fundamental_analysis_report,
)

load_dotenv()

DEFAULT_MAX_STEPS = int(os.getenv("SMOLAGENT_MAX_STEPS", "20"))
DEFAULT_PERIOD = os.getenv("DEFAULT_ANALYSIS_PERIOD", "1y")
DEFAULT_SCANNER_SYMBOLS = os.getenv("DEFAULT_SCANNER_SYMBOLS", "AAPL,MSFT,TSLA,AMZN")
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_OPENAI_BASE = os.getenv("OPENAI_BASE_URL")
DEFAULT_HF_TOKEN = os.getenv("HF_TOKEN")

logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Stock Analyzer API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _needs_fallback(report: str) -> bool:
    """Check if agent output needs fallback to deterministic report."""
    if not report:
        return True
    content = report.strip().lower()
    if len(content) < 200:
        return True
    required_sections = [
        "strategy highlights",
        "consensus outlook", 
        "risk metrics",
        "final recommendation",
    ]
    return any(section not in content for section in required_sections)


def _extract_recommendation(agent_output: str) -> str:
    """Extract BUY/SELL/HOLD from agent output."""
    output_upper = agent_output.strip().upper()
    if "BUY" in output_upper:
        return "BUY"
    elif "SELL" in output_upper:
        return "SELL"
    else:
        return "HOLD"


class AnalyzeRequest(BaseModel):
    symbol: str = Field(..., description="Ticker symbol to analyze")
    period: str = Field(DEFAULT_PERIOD, description="Historical period to analyze")
    model_id: Optional[str] = Field(None, description="Override the model identifier")
    model_provider: Optional[str] = Field(None, description="Override provider (auto/inference/litellm)")
    hf_token: Optional[str] = Field(None, description="Optional Hugging Face token override")
    openai_api_key: Optional[str] = Field(None, description="Optional OpenAI API key override")
    openai_base_url: Optional[str] = Field(None, description="Optional OpenAI-compatible base URL")
    max_steps: Optional[int] = Field(None, description="Override smolagents reasoning steps")


class ReportRequest(BaseModel):
    symbol: str = Field(..., description="Ticker symbol to analyze")
    period: str = Field(DEFAULT_PERIOD, description="Historical period to analyze")


class ScannerRequest(BaseModel):
    symbols: List[str] | str = Field(
        DEFAULT_SCANNER_SYMBOLS,
        description="List or comma-separated symbols",
    )
    period: str = Field("1y", description="Historical period for analysis")
    output_format: str = Field("detailed", description="Output format: detailed, summary, or executive")


class FundamentalRequest(BaseModel):
    symbol: str = Field(..., description="Ticker symbol to analyze")
    period: str = Field("3y", description="Historical period for statements")


@app.get("/health", tags=["system"])
async def healthcheck() -> dict:
    return {"status": "ok", "tools": [tool.__name__ for tool in ALL_TOOLS]}


@app.post("/analyze", tags=["analysis"])
async def analyze(request: AnalyzeRequest) -> dict:
    """
    Run the multi-strategy analysis agent and return the markdown report.
    
    This endpoint uses an AI agent (smolagents) to execute trading strategy tools
    and synthesize results. If the agent fails or produces incomplete output,
    it automatically falls back to the deterministic comprehensive report.
    """
    try:
        result = await run_in_threadpool(
            run_agent,
            request.symbol,
            request.period,
            request.model_id or DEFAULT_MODEL_ID,
            request.hf_token or DEFAULT_HF_TOKEN,
            request.model_provider or DEFAULT_MODEL_PROVIDER,
            request.openai_api_key or DEFAULT_API_KEY,
            request.openai_base_url or DEFAULT_OPENAI_BASE,
            request.max_steps or DEFAULT_MAX_STEPS,
            False,
            1,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
    
    # Check if agent output needs fallback
    if _needs_fallback(result):
        # Extract any recommendation the agent did provide
        agent_recommendation = _extract_recommendation(result)
        
        # Get the deterministic comprehensive report
        fallback_report = await run_in_threadpool(
            comprehensive_performance_report,
            request.symbol,
            request.period,
        )
        
        # Build a clean fallback response
        result = f"""# {request.symbol.upper()} Technical Analysis Report

---
⚠️ **Notice: AI Agent Output Incomplete - Using Deterministic Report**

> The AI agent attempted to analyze {request.symbol.upper()} but produced incomplete output.
> The agent's recommendation was: **{agent_recommendation}**
>
> Below is the **Comprehensive Performance Report** generated using deterministic calculations.
> This ensures you still receive complete, accurate analysis data.

---

{fallback_report}
"""
    
    return {"report": result}


@app.post("/report", tags=["analysis"])
async def comprehensive_report(request: ReportRequest) -> dict:
    """
    Return the MCP comprehensive multi-strategy markdown report.
    
    This endpoint directly executes strategy tools with fixed parameters
    and generates a structured report without AI interpretation.
    """
    result = await run_in_threadpool(
        comprehensive_performance_report,
        request.symbol,
        request.period,
    )
    return {"report": result}


@app.post("/scanner", tags=["analysis"])
async def scanner(request: ScannerRequest) -> dict:
    """Run the unified market scanner for the provided basket."""
    result = await run_in_threadpool(
        unified_market_scanner,
        request.symbols,
        request.period,
        request.output_format,
    )
    return {"report": result}


@app.post("/fundamental", tags=["analysis"])
async def fundamental(request: FundamentalRequest) -> dict:
    """Return the fundamental analysis markdown report."""
    start_time = time.time()
    logger.info("/fundamental requested for %s (period=%s)", request.symbol, request.period)
    result = await run_in_threadpool(
        fundamental_analysis_report,
        request.symbol,
        request.period,
    )
    logger.info(
        "/fundamental completed for %s in %.2fs",
        request.symbol,
        time.time() - start_time,
    )
    return {"report": result}