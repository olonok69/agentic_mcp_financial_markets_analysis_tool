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
    ma_type: str = Field("SMA", description="Moving average type (SMA/EMA)")
    short_period: int = Field(50, description="Short MA period")
    long_period: int = Field(200, description="Long MA period")


class FundamentalRequest(BaseModel):
    symbol: str = Field(..., description="Ticker symbol to analyze")
    period: str = Field("3y", description="Historical period for statements")


@app.get("/health", tags=["system"])
async def healthcheck() -> dict:
    return {"status": "ok", "tools": [tool.__name__ for tool in ALL_TOOLS]}


@app.post("/analyze", tags=["analysis"])
async def analyze(request: AnalyzeRequest) -> dict:
    """Run the multi-strategy analysis agent and return the markdown report."""

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
    if _needs_fallback(result):
        fallback_report = await run_in_threadpool(
            comprehensive_performance_report,
            request.symbol,
            request.period,
        )
        result = (
            "⚠️ **Agent summary was truncated or missing required sections.** "
            "Automatically appending the deterministic comprehensive performance report below.\n\n"
            f"## Agent Reply\n{result.strip() or '_Agent returned no explanation._'}\n\n"
            "## Comprehensive Performance Report\n"
            f"{fallback_report}"
        )
    return {"report": result}


@app.post("/report", tags=["analysis"])
async def comprehensive_report(request: ReportRequest) -> dict:
    """Return the MCP comprehensive multi-strategy markdown report."""

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
        request.ma_type,
        request.short_period,
        request.long_period,
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
