"""
FastAPI backend for the LLM-powered MCP Stock Analyzer.

All analysis endpoints use smolagents with LLM to:
1. Call MCP tools to get raw financial data
2. Synthesize and interpret results
3. Generate professional markdown reports

Endpoints:
- POST /technical - Single stock technical analysis (4 strategies)
- POST /scanner - Multi-stock comparison and ranking
- POST /fundamental - Financial statement analysis
- POST /multisector - Cross-sector comparative analysis
- POST /combined - Technical + Fundamental combined analysis
"""
from __future__ import annotations

import logging
import os
import time
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .main import (
    DEFAULT_MODEL_ID,
    DEFAULT_MODEL_PROVIDER,
    DEFAULT_MAX_STEPS,
    run_technical_analysis,
    run_market_scanner,
    run_fundamental_analysis,
    run_multi_sector_analysis,
    run_combined_analysis,
)
from .tools import configure_finance_tools, shutdown_finance_tools

load_dotenv()

# Environment defaults
DEFAULT_PERIOD = os.getenv("DEFAULT_ANALYSIS_PERIOD", "1y")
DEFAULT_SCANNER_SYMBOLS = os.getenv("DEFAULT_SCANNER_SYMBOLS", "AAPL,MSFT,GOOGL,AMZN")
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_OPENAI_BASE = os.getenv("OPENAI_BASE_URL")
DEFAULT_HF_TOKEN = os.getenv("HF_TOKEN")

logger = logging.getLogger(__name__)

# =============================================================================
# FastAPI App Setup
# =============================================================================

app = FastAPI(
    title="MCP Stock Analyzer API",
    description="""
    LLM-powered financial analysis using MCP tools and smolagents.
    
    All endpoints use AI to interpret data and generate professional reports:
    - **Technical Analysis**: 4 trading strategies on a single stock
    - **Market Scanner**: Compare multiple stocks, rank opportunities
    - **Fundamental Analysis**: Financial statements interpretation
    """,
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Startup/Shutdown Events
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize MCP connection on startup."""
    logger.info("Starting MCP finance tools...")
    configure_finance_tools()
    logger.info("MCP finance tools ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up MCP connection on shutdown."""
    logger.info("Shutting down MCP finance tools...")
    shutdown_finance_tools()
    logger.info("MCP finance tools stopped")


# =============================================================================
# Request/Response Models
# =============================================================================

class TechnicalAnalysisRequest(BaseModel):
    """Request for single-stock technical analysis."""
    symbol: str = Field(..., description="Ticker symbol to analyze (e.g., AAPL)")
    period: str = Field(DEFAULT_PERIOD, description="Historical period (1y, 6mo, 3mo, etc.)")
    model_id: Optional[str] = Field(None, description="Override LLM model (e.g., gpt-4o)")
    model_provider: Optional[str] = Field(None, description="Provider: litellm or inference")
    openai_api_key: Optional[str] = Field(None, description="Override OpenAI API key")
    hf_token: Optional[str] = Field(None, description="Override HuggingFace token")
    max_steps: Optional[int] = Field(None, description="Max agent reasoning steps")


class MarketScannerRequest(BaseModel):
    """Request for multi-stock market scanning."""
    symbols: str = Field(
        DEFAULT_SCANNER_SYMBOLS,
        description="Comma-separated ticker symbols (e.g., AAPL,MSFT,GOOGL)",
    )
    period: str = Field(DEFAULT_PERIOD, description="Historical period for analysis")
    model_id: Optional[str] = Field(None, description="Override LLM model")
    model_provider: Optional[str] = Field(None, description="Provider: litellm or inference")
    openai_api_key: Optional[str] = Field(None, description="Override OpenAI API key")
    hf_token: Optional[str] = Field(None, description="Override HuggingFace token")
    max_steps: Optional[int] = Field(50, description="Max agent steps (more for multi-stock)")


class FundamentalAnalysisRequest(BaseModel):
    """Request for fundamental financial analysis."""
    symbol: str = Field(..., description="Ticker symbol to analyze")
    period: str = Field("3y", description="Period for financial statements")
    model_id: Optional[str] = Field(None, description="Override LLM model")
    model_provider: Optional[str] = Field(None, description="Provider: litellm or inference")
    openai_api_key: Optional[str] = Field(None, description="Override OpenAI API key")
    hf_token: Optional[str] = Field(None, description="Override HuggingFace token")
    max_steps: Optional[int] = Field(None, description="Max agent reasoning steps")


class SectorConfig(BaseModel):
    """Configuration for a single sector."""
    name: str = Field(..., description="Sector name (e.g., 'Banking', 'Technology')")
    symbols: str = Field(..., description="Comma-separated ticker symbols")


class MultiSectorAnalysisRequest(BaseModel):
    """Request for multi-sector comparative analysis."""
    sectors: List[SectorConfig] = Field(
        ...,
        description="List of sectors with their symbols",
        example=[
            {"name": "Banking", "symbols": "JPM,BAC,WFC,C,GS"},
            {"name": "Technology", "symbols": "AAPL,MSFT,GOOGL,META,NVDA"},
            {"name": "Clean Energy", "symbols": "TSLA,NIO,ENPH,PLUG,NEE"},
        ],
    )
    period: str = Field("1y", description="Historical period for analysis")
    model_id: Optional[str] = Field(None, description="Override LLM model (recommend gpt-4o)")
    model_provider: Optional[str] = Field(None, description="Provider: litellm or inference")
    openai_api_key: Optional[str] = Field(None, description="Override OpenAI API key")
    hf_token: Optional[str] = Field(None, description="Override HuggingFace token")
    max_steps: Optional[int] = Field(100, description="Max agent steps (100+ for multi-sector)")


class CombinedAnalysisRequest(BaseModel):
    """Request for combined Technical + Fundamental analysis."""
    symbol: str = Field(..., description="Ticker symbol to analyze (e.g., AAPL)")
    technical_period: str = Field("1y", description="Period for technical analysis")
    fundamental_period: str = Field("3y", description="Period for fundamental data")
    model_id: Optional[str] = Field(None, description="Override LLM model")
    model_provider: Optional[str] = Field(None, description="Provider: litellm or inference")
    openai_api_key: Optional[str] = Field(None, description="Override OpenAI API key")
    hf_token: Optional[str] = Field(None, description="Override HuggingFace token")
    max_steps: Optional[int] = Field(35, description="Max agent steps (5 tools needed)")


class AnalysisResponse(BaseModel):
    """Standard response for all analysis endpoints."""
    report: str = Field(..., description="Markdown analysis report")
    symbol: str = Field(..., description="Symbol(s) analyzed")
    analysis_type: str = Field(..., description="Type of analysis performed")
    duration_seconds: float = Field(..., description="Time taken for analysis")


# =============================================================================
# Health Check
# =============================================================================

@app.get("/health", tags=["system"])
async def healthcheck() -> dict:
    """Check API health and list available features."""
    return {
        "status": "ok",
        "version": "2.2.0",
        "features": [
            "technical_analysis",
            "market_scanner", 
            "fundamental_analysis",
            "multi_sector_analysis",
            "combined_analysis",
        ],
        "model": {
            "default_id": DEFAULT_MODEL_ID,
            "default_provider": DEFAULT_MODEL_PROVIDER,
        },
    }


# =============================================================================
# Technical Analysis Endpoint
# =============================================================================

@app.post("/technical", tags=["analysis"], response_model=AnalysisResponse)
async def technical_analysis(request: TechnicalAnalysisRequest) -> dict:
    """
    Run comprehensive technical analysis on a single stock.
    
    Uses an AI agent to:
    1. Call 4 strategy tools (Bollinger-Fibonacci, MACD-Donchian, Connors-ZScore, Dual MA)
    2. Extract performance metrics from each strategy
    3. Synthesize results into a professional markdown report
    
    Returns a report similar to the Tesla technical analysis example with:
    - Executive Summary
    - Performance Summary Table
    - Individual Strategy Analysis
    - Risk Assessment
    - Final Recommendation with trading strategy
    """
    start_time = time.time()
    logger.info("Technical analysis requested for %s (period=%s)", request.symbol, request.period)
    
    try:
        result = await run_in_threadpool(
            run_technical_analysis,
            symbol=request.symbol,
            period=request.period,
            model_id=request.model_id or DEFAULT_MODEL_ID,
            model_provider=request.model_provider or DEFAULT_MODEL_PROVIDER,
            openai_api_key=request.openai_api_key or DEFAULT_API_KEY,
            hf_token=request.hf_token or DEFAULT_HF_TOKEN,
            openai_base_url=DEFAULT_OPENAI_BASE,
            max_steps=request.max_steps or DEFAULT_MAX_STEPS,
        )
    except Exception as exc:
        logger.exception("Technical analysis failed for %s", request.symbol)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
    
    duration = time.time() - start_time
    logger.info("Technical analysis completed for %s in %.2fs", request.symbol, duration)
    
    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "technical",
        "duration_seconds": round(duration, 2),
    }


# =============================================================================
# Market Scanner Endpoint
# =============================================================================

@app.post("/scanner", tags=["analysis"], response_model=AnalysisResponse)
async def market_scanner(request: MarketScannerRequest) -> dict:
    """
    Scan multiple stocks and generate comparative analysis.
    
    Uses an AI agent to:
    1. Call 4 strategy tools for EACH stock in the list
    2. Collect and compare performance metrics
    3. Rank stocks by opportunity quality
    4. Generate a comprehensive comparison report
    
    Returns a report similar to the banking sector analysis with:
    - Cross-Stock Performance Overview
    - Investment Recommendations (BUY/HOLD/AVOID)
    - Individual Stock Analysis
    - Strategy Effectiveness Ranking
    - Portfolio Construction suggestions
    
    Note: This requires many tool calls and may take longer than single-stock analysis.
    """
    start_time = time.time()
    symbols_clean = request.symbols.replace(" ", "").upper()
    logger.info("Market scanner requested for %s (period=%s)", symbols_clean, request.period)
    
    try:
        result = await run_in_threadpool(
            run_market_scanner,
            symbols=symbols_clean,
            period=request.period,
            model_id=request.model_id or DEFAULT_MODEL_ID,
            model_provider=request.model_provider or DEFAULT_MODEL_PROVIDER,
            openai_api_key=request.openai_api_key or DEFAULT_API_KEY,
            hf_token=request.hf_token or DEFAULT_HF_TOKEN,
            openai_base_url=DEFAULT_OPENAI_BASE,
            max_steps=request.max_steps or 50,
        )
    except Exception as exc:
        logger.exception("Market scanner failed for %s", symbols_clean)
        raise HTTPException(status_code=500, detail=f"Scanner failed: {exc}") from exc
    
    duration = time.time() - start_time
    logger.info("Market scanner completed for %s in %.2fs", symbols_clean, duration)
    
    return {
        "report": result,
        "symbol": symbols_clean,
        "analysis_type": "scanner",
        "duration_seconds": round(duration, 2),
    }


# =============================================================================
# Fundamental Analysis Endpoint
# =============================================================================

@app.post("/fundamental", tags=["analysis"], response_model=AnalysisResponse)
async def fundamental_analysis(request: FundamentalAnalysisRequest) -> dict:
    """
    Run fundamental analysis on a stock's financial statements.
    
    Uses an AI agent to:
    1. Call the fundamental analysis tool to get financial data
    2. Interpret income statement, balance sheet, and cash flow metrics
    3. Generate an investment thesis with strengths, risks, and recommendation
    
    Returns a report with:
    - Company Overview
    - Key Metrics Summary Table
    - Income Statement Analysis
    - Balance Sheet Strength
    - Cash Flow Analysis
    - Investment Assessment (Strengths/Risks)
    - Final Recommendation
    """
    start_time = time.time()
    logger.info("Fundamental analysis requested for %s (period=%s)", request.symbol, request.period)
    
    try:
        result = await run_in_threadpool(
            run_fundamental_analysis,
            symbol=request.symbol,
            period=request.period,
            model_id=request.model_id or DEFAULT_MODEL_ID,
            model_provider=request.model_provider or DEFAULT_MODEL_PROVIDER,
            openai_api_key=request.openai_api_key or DEFAULT_API_KEY,
            hf_token=request.hf_token or DEFAULT_HF_TOKEN,
            openai_base_url=DEFAULT_OPENAI_BASE,
            max_steps=request.max_steps or DEFAULT_MAX_STEPS,
        )
    except Exception as exc:
        logger.exception("Fundamental analysis failed for %s", request.symbol)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
    
    duration = time.time() - start_time
    logger.info("Fundamental analysis completed for %s in %.2fs", request.symbol, duration)
    
    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "fundamental",
        "duration_seconds": round(duration, 2),
    }


# =============================================================================
# Multi-Sector Analysis Endpoint
# =============================================================================

@app.post("/multisector", tags=["analysis"], response_model=AnalysisResponse)
async def multi_sector_analysis(request: MultiSectorAnalysisRequest) -> dict:
    """
    Run comprehensive multi-sector comparative analysis.
    
    Uses an AI agent to:
    1. Analyze ALL stocks across ALL provided sectors
    2. Call 4 strategy tools for each stock
    3. Compare performance across sectors
    4. Generate a comprehensive cross-sector report
    
    Returns a report similar to multi_sector_analysis_report.md with:
    - Cross-Sector Performance Overview
    - Priority Investment Recommendations
    - Sector-by-Sector Analysis
    - Strategy Effectiveness Ranking
    - Portfolio Construction suggestions
    - Action Plan
    
    ⚠️ NOTE: This is a compute-intensive operation. For 3 sectors with 10 stocks each,
    expect 120+ tool calls and 5-15 minutes of processing time.
    Recommend using gpt-4o for best results.
    """
    start_time = time.time()
    
    # Convert sectors list to dictionary
    sectors_dict = {s.name: s.symbols for s in request.sectors}
    
    # Calculate total stocks for logging
    total_stocks = sum(
        len([x for x in s.symbols.split(",") if x.strip()])
        for s in request.sectors
    )
    sector_names = ", ".join(s.name for s in request.sectors)
    
    logger.info(
        "Multi-sector analysis requested: %d sectors, %d stocks (period=%s)",
        len(request.sectors), total_stocks, request.period
    )
    
    try:
        result = await run_in_threadpool(
            run_multi_sector_analysis,
            sectors=sectors_dict,
            period=request.period,
            model_id=request.model_id or DEFAULT_MODEL_ID,
            model_provider=request.model_provider or DEFAULT_MODEL_PROVIDER,
            openai_api_key=request.openai_api_key or DEFAULT_API_KEY,
            hf_token=request.hf_token or DEFAULT_HF_TOKEN,
            openai_base_url=DEFAULT_OPENAI_BASE,
            max_steps=request.max_steps or 100,
        )
    except Exception as exc:
        logger.exception("Multi-sector analysis failed")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
    
    duration = time.time() - start_time
    logger.info(
        "Multi-sector analysis completed: %d sectors in %.2fs",
        len(request.sectors), duration
    )
    
    return {
        "report": result,
        "symbol": sector_names,
        "analysis_type": "multi_sector",
        "duration_seconds": round(duration, 2),
    }


# =============================================================================
# Combined Technical + Fundamental Analysis Endpoint
# =============================================================================

@app.post("/combined", tags=["analysis"], response_model=AnalysisResponse)
async def combined_analysis(request: CombinedAnalysisRequest) -> dict:
    """
    Run combined Technical + Fundamental analysis on a single stock.
    
    This powerful analysis approach combines:
    
    **Fundamental Analysis ("What to Buy")**
    - Assesses company financial health
    - Evaluates profitability, debt, cash flow
    - Determines intrinsic value
    
    **Technical Analysis ("When to Buy")**  
    - Analyzes price trends and momentum
    - Identifies entry/exit points
    - Provides timing signals
    
    **Combined Benefits:**
    - 360-degree investment view
    - When FA + TA align → High conviction opportunity
    - When they diverge → Caution, deeper analysis needed
    
    Returns a comprehensive report with:
    - Executive Summary synthesizing both perspectives
    - Fundamental Health Scorecard
    - Technical Strategy Performance
    - Signal Alignment Analysis
    - Entry/Exit Strategy with price levels
    - Risk Assessment from both angles
    """
    start_time = time.time()
    logger.info(
        "Combined analysis requested for %s (tech=%s, fund=%s)",
        request.symbol, request.technical_period, request.fundamental_period
    )
    
    try:
        result = await run_in_threadpool(
            run_combined_analysis,
            symbol=request.symbol,
            technical_period=request.technical_period,
            fundamental_period=request.fundamental_period,
            model_id=request.model_id or DEFAULT_MODEL_ID,
            model_provider=request.model_provider or DEFAULT_MODEL_PROVIDER,
            openai_api_key=request.openai_api_key or DEFAULT_API_KEY,
            hf_token=request.hf_token or DEFAULT_HF_TOKEN,
            openai_base_url=DEFAULT_OPENAI_BASE,
            max_steps=request.max_steps or 35,
        )
    except Exception as exc:
        logger.exception("Combined analysis failed for %s", request.symbol)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
    
    duration = time.time() - start_time
    logger.info("Combined analysis completed for %s in %.2fs", request.symbol, duration)
    
    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "combined",
        "duration_seconds": round(duration, 2),
    }


# =============================================================================
# Legacy Endpoints (for backward compatibility)
# =============================================================================

@app.post("/analyze", tags=["legacy"], include_in_schema=False)
async def legacy_analyze(request: TechnicalAnalysisRequest) -> dict:
    """Legacy endpoint - redirects to /technical."""
    response = await technical_analysis(request)
    return {"report": response["report"]}


@app.post("/report", tags=["legacy"], include_in_schema=False)
async def legacy_report(request: TechnicalAnalysisRequest) -> dict:
    """Legacy endpoint - redirects to /technical."""
    response = await technical_analysis(request)
    return {"report": response["report"]}