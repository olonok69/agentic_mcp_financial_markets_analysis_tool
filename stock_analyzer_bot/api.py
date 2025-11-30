"""
FastAPI backend for the LLM-powered MCP Stock Analyzer.

#####################################################################
# TWO AGENT ARCHITECTURES
#####################################################################
#
# 1. TOOLCALLINGAGENT (main.py)
#    - Uses HIGH-LEVEL tools that do everything in one MCP call
#    - Tools: comprehensive_performance_report, unified_market_scanner, fundamental_analysis_report
#    - Simple, fast, predictable
#    - Best for: Production, reliability, straightforward analysis
#
# 2. CODEAGENT (main_codeagent.py)
#    - Uses LOW-LEVEL granular tools + writes Python code to orchestrate
#    - Tools: bollinger_fibonacci, macd_donchian, connors_zscore, dual_ma, fundamental
#    - Flexible, transparent, custom logic
#    - Best for: Custom analysis, debugging, educational purposes
#
#####################################################################

Endpoints:
- POST /technical - Single stock technical analysis
- POST /scanner - Multi-stock comparison and ranking
- POST /fundamental - Financial statement analysis
- POST /multisector - Cross-sector comparative analysis
- POST /combined - Technical + Fundamental combined analysis
"""
from __future__ import annotations

import logging
import os
import time
from typing import List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import ToolCallingAgent functions (HIGH-LEVEL tools)
from .main import (
    DEFAULT_MODEL_ID,
    DEFAULT_MODEL_PROVIDER,
    DEFAULT_MAX_STEPS,
    run_technical_analysis as run_technical_toolcalling,
    run_market_scanner as run_scanner_toolcalling,
    run_fundamental_analysis as run_fundamental_toolcalling,
    run_multi_sector_analysis as run_multisector_toolcalling,
    run_combined_analysis as run_combined_toolcalling,
)

# Import CodeAgent functions (LOW-LEVEL tools)
try:
    from .main_codeagent import (
        run_technical_analysis as run_technical_codeagent,
        run_market_scanner as run_scanner_codeagent,
        run_fundamental_analysis as run_fundamental_codeagent,
        run_multi_sector_analysis as run_multisector_codeagent,
        run_combined_analysis as run_combined_codeagent,
        DEFAULT_EXECUTOR,
    )
    CODEAGENT_AVAILABLE = True
except ImportError:
    CODEAGENT_AVAILABLE = False
    DEFAULT_EXECUTOR = "local"

from .tools import configure_finance_tools, shutdown_finance_tools

load_dotenv()

# Environment defaults
DEFAULT_PERIOD = os.getenv("DEFAULT_ANALYSIS_PERIOD", "1y")
DEFAULT_SCANNER_SYMBOLS = os.getenv("DEFAULT_SCANNER_SYMBOLS", "AAPL,MSFT,GOOGL,AMZN")
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_OPENAI_BASE = os.getenv("OPENAI_BASE_URL")
DEFAULT_HF_TOKEN = os.getenv("HF_TOKEN")
DEFAULT_AGENT_TYPE = os.getenv("SMOLAGENT_AGENT_TYPE", "tool_calling")

logger = logging.getLogger(__name__)

# =============================================================================
# FastAPI App Setup
# =============================================================================

app = FastAPI(
    title="MCP Stock Analyzer API",
    description="""
    LLM-powered financial analysis using MCP tools and smolagents.
    
    ## Two Agent Architectures
    
    ### 🔧 ToolCallingAgent (tool_calling)
    - Uses **HIGH-LEVEL** tools that do everything in one MCP call
    - `comprehensive_performance_report` - Full technical analysis in 1 call
    - `unified_market_scanner` - Multi-stock scanning in 1 call
    - `fundamental_analysis_report` - Complete financials in 1 call
    - **Best for:** Production, speed, reliability
    
    ### 🐍 CodeAgent (code_agent)
    - Uses **LOW-LEVEL** granular tools + Python code orchestration
    - 4 individual strategy tools called via loops
    - LLM writes custom Python code to combine results
    - **Best for:** Custom analysis, transparency, learning
    
    ## Endpoints
    - **POST /technical** - Single stock, all strategies
    - **POST /scanner** - Multi-stock comparison
    - **POST /fundamental** - Financial statements
    - **POST /multisector** - Cross-sector analysis
    - **POST /combined** - Technical + Fundamental
    """,
    version="3.0.0",
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
    logger.info("ToolCallingAgent: Uses HIGH-LEVEL tools (comprehensive_performance_report, etc.)")
    if CODEAGENT_AVAILABLE:
        logger.info("CodeAgent: Available - Uses LOW-LEVEL tools (4 strategies + Python code)")
    else:
        logger.warning("CodeAgent: Not available - main_codeagent.py not found")


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
    agent_type: Optional[Literal["tool_calling", "code_agent"]] = Field(
        None, 
        description="tool_calling (HIGH-LEVEL tools) or code_agent (LOW-LEVEL tools)"
    )
    executor_type: Optional[Literal["local", "e2b", "docker"]] = Field(
        None,
        description="Code execution environment for CodeAgent"
    )


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
    max_steps: Optional[int] = Field(None, description="Max agent steps")
    agent_type: Optional[Literal["tool_calling", "code_agent"]] = Field(
        None,
        description="tool_calling (1 scanner call) or code_agent (loops over tools)"
    )
    executor_type: Optional[Literal["local", "e2b", "docker"]] = Field(
        None,
        description="Code execution environment for CodeAgent"
    )


class FundamentalAnalysisRequest(BaseModel):
    """Request for fundamental financial analysis."""
    symbol: str = Field(..., description="Ticker symbol to analyze")
    period: str = Field("3y", description="Period for financial statements")
    model_id: Optional[str] = Field(None, description="Override LLM model")
    model_provider: Optional[str] = Field(None, description="Provider: litellm or inference")
    openai_api_key: Optional[str] = Field(None, description="Override OpenAI API key")
    hf_token: Optional[str] = Field(None, description="Override HuggingFace token")
    max_steps: Optional[int] = Field(None, description="Max agent reasoning steps")
    agent_type: Optional[Literal["tool_calling", "code_agent"]] = Field(
        None,
        description="Both use fundamental_analysis_report tool"
    )
    executor_type: Optional[Literal["local", "e2b", "docker"]] = Field(
        None,
        description="Code execution environment for CodeAgent"
    )


class SectorConfig(BaseModel):
    """Configuration for a single sector."""
    name: str = Field(..., description="Sector name (e.g., Banking, Technology)")
    symbols: str = Field(..., description="Comma-separated ticker symbols")


class MultiSectorAnalysisRequest(BaseModel):
    """Request for multi-sector comparative analysis."""
    sectors: List[SectorConfig] = Field(..., description="List of sectors to analyze")
    period: str = Field(DEFAULT_PERIOD, description="Historical period for analysis")
    model_id: Optional[str] = Field(None, description="Override LLM model")
    model_provider: Optional[str] = Field(None, description="Provider: litellm or inference")
    openai_api_key: Optional[str] = Field(None, description="Override OpenAI API key")
    hf_token: Optional[str] = Field(None, description="Override HuggingFace token")
    max_steps: Optional[int] = Field(None, description="Max agent steps")
    agent_type: Optional[Literal["tool_calling", "code_agent"]] = Field(
        None,
        description="tool_calling (scanner per sector) or code_agent (nested loops)"
    )
    executor_type: Optional[Literal["local", "e2b", "docker"]] = Field(
        None,
        description="Code execution environment for CodeAgent"
    )


class CombinedAnalysisRequest(BaseModel):
    """Request for combined Technical + Fundamental analysis."""
    symbol: str = Field(..., description="Ticker symbol to analyze")
    technical_period: str = Field("1y", description="Period for technical analysis")
    fundamental_period: str = Field("3y", description="Period for fundamental data")
    model_id: Optional[str] = Field(None, description="Override LLM model")
    model_provider: Optional[str] = Field(None, description="Provider: litellm or inference")
    openai_api_key: Optional[str] = Field(None, description="Override OpenAI API key")
    hf_token: Optional[str] = Field(None, description="Override HuggingFace token")
    max_steps: Optional[int] = Field(None, description="Max agent steps")
    agent_type: Optional[Literal["tool_calling", "code_agent"]] = Field(
        None,
        description="tool_calling (2 calls) or code_agent (5 tools + synthesis)"
    )
    executor_type: Optional[Literal["local", "e2b", "docker"]] = Field(
        None,
        description="Code execution environment for CodeAgent"
    )


class AnalysisResponse(BaseModel):
    """Standard response for all analysis endpoints."""
    report: str = Field(..., description="Markdown analysis report")
    symbol: str = Field(..., description="Symbol(s) analyzed")
    analysis_type: str = Field(..., description="Type of analysis performed")
    duration_seconds: float = Field(..., description="Time taken for analysis")
    agent_type: str = Field(..., description="Agent used: tool_calling or code_agent")
    tools_approach: str = Field(..., description="HIGH-LEVEL or LOW-LEVEL tools")


# =============================================================================
# Health Check
# =============================================================================

@app.get("/health", tags=["system"])
async def healthcheck() -> dict:
    """Check API health and list available features."""
    return {
        "status": "ok",
        "version": "3.0.0",
        "features": [
            "technical_analysis",
            "market_scanner", 
            "fundamental_analysis",
            "multi_sector_analysis",
            "combined_analysis",
        ],
        "agent_types": {
            "tool_calling": {
                "available": True,
                "approach": "HIGH-LEVEL tools",
                "tools": ["comprehensive_performance_report", "unified_market_scanner", "fundamental_analysis_report"],
            },
            "code_agent": {
                "available": CODEAGENT_AVAILABLE,
                "approach": "LOW-LEVEL tools + Python code",
                "tools": ["bollinger_fibonacci", "macd_donchian", "connors_zscore", "dual_ma", "fundamental"],
            },
        },
        "default_agent_type": DEFAULT_AGENT_TYPE,
        "model": {
            "default_id": DEFAULT_MODEL_ID,
            "default_provider": DEFAULT_MODEL_PROVIDER,
        },
    }


# =============================================================================
# Helper Functions
# =============================================================================

def get_agent_type(request_agent_type: Optional[str]) -> str:
    """Determine which agent type to use."""
    agent_type = request_agent_type or DEFAULT_AGENT_TYPE
    
    if agent_type == "code_agent" and not CODEAGENT_AVAILABLE:
        logger.warning("CodeAgent requested but not available, falling back to tool_calling")
        return "tool_calling"
    
    return agent_type


def get_tools_approach(agent_type: str) -> str:
    """Return description of tools approach for response."""
    if agent_type == "code_agent":
        return "LOW-LEVEL tools (4 strategies + Python code orchestration)"
    return "HIGH-LEVEL tools (comprehensive reports in single MCP calls)"


# =============================================================================
# Technical Analysis Endpoint
# =============================================================================

@app.post("/technical", tags=["analysis"], response_model=AnalysisResponse)
async def technical_analysis(request: TechnicalAnalysisRequest) -> dict:
    """
    Run comprehensive technical analysis on a single stock.
    
    **ToolCallingAgent (tool_calling):**
    - Calls `comprehensive_performance_report` (1 MCP call)
    - Gets complete report with all 4 strategies
    
    **CodeAgent (code_agent):**
    - Calls 4 individual strategy tools
    - LLM writes Python code to combine results
    """
    start_time = time.time()
    agent_type = get_agent_type(request.agent_type)
    
    logger.info(
        "Technical analysis: %s (period=%s, agent=%s)", 
        request.symbol, request.period, agent_type
    )
    
    try:
        if agent_type == "code_agent":
            result = await run_in_threadpool(
                run_technical_codeagent,
                symbol=request.symbol,
                period=request.period,
                model_id=request.model_id or DEFAULT_MODEL_ID,
                model_provider=request.model_provider or DEFAULT_MODEL_PROVIDER,
                openai_api_key=request.openai_api_key or DEFAULT_API_KEY,
                hf_token=request.hf_token or DEFAULT_HF_TOKEN,
                openai_base_url=DEFAULT_OPENAI_BASE,
                max_steps=request.max_steps or 20,
                executor_type=request.executor_type or DEFAULT_EXECUTOR,
            )
        else:
            result = await run_in_threadpool(
                run_technical_toolcalling,
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
    logger.info("Technical analysis completed: %s in %.2fs (%s)", request.symbol, duration, agent_type)
    
    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "technical",
        "duration_seconds": round(duration, 2),
        "agent_type": agent_type,
        "tools_approach": get_tools_approach(agent_type),
    }


# =============================================================================
# Market Scanner Endpoint
# =============================================================================

@app.post("/scanner", tags=["analysis"], response_model=AnalysisResponse)
async def market_scanner(request: MarketScannerRequest) -> dict:
    """
    Scan multiple stocks and generate comparative analysis.
    
    **ToolCallingAgent (tool_calling):**
    - Calls `unified_market_scanner` (1 MCP call for all stocks)
    - Most efficient for multi-stock analysis
    
    **CodeAgent (code_agent):**
    - Writes Python loops to call 4 tools per stock
    - More transparent but slower
    """
    start_time = time.time()
    agent_type = get_agent_type(request.agent_type)
    
    symbol_count = len([s for s in request.symbols.split(",") if s.strip()])
    logger.info("Market scanner: %d stocks (agent=%s)", symbol_count, agent_type)
    
    try:
        if agent_type == "code_agent":
            result = await run_in_threadpool(
                run_scanner_codeagent,
                symbols=request.symbols,
                period=request.period,
                model_id=request.model_id or DEFAULT_MODEL_ID,
                model_provider=request.model_provider or DEFAULT_MODEL_PROVIDER,
                openai_api_key=request.openai_api_key or DEFAULT_API_KEY,
                hf_token=request.hf_token or DEFAULT_HF_TOKEN,
                openai_base_url=DEFAULT_OPENAI_BASE,
                max_steps=request.max_steps or 30,
                executor_type=request.executor_type or DEFAULT_EXECUTOR,
            )
        else:
            result = await run_in_threadpool(
                run_scanner_toolcalling,
                symbols=request.symbols,
                period=request.period,
                model_id=request.model_id or DEFAULT_MODEL_ID,
                model_provider=request.model_provider or DEFAULT_MODEL_PROVIDER,
                openai_api_key=request.openai_api_key or DEFAULT_API_KEY,
                hf_token=request.hf_token or DEFAULT_HF_TOKEN,
                openai_base_url=DEFAULT_OPENAI_BASE,
                max_steps=request.max_steps or DEFAULT_MAX_STEPS,
            )
    except Exception as exc:
        logger.exception("Market scanner failed")
        raise HTTPException(status_code=500, detail=f"Scanner failed: {exc}") from exc
    
    duration = time.time() - start_time
    logger.info("Scanner completed in %.2fs (%s)", duration, agent_type)
    
    return {
        "report": result,
        "symbol": request.symbols.upper(),
        "analysis_type": "scanner",
        "duration_seconds": round(duration, 2),
        "agent_type": agent_type,
        "tools_approach": get_tools_approach(agent_type),
    }


# =============================================================================
# Fundamental Analysis Endpoint
# =============================================================================

@app.post("/fundamental", tags=["analysis"], response_model=AnalysisResponse)
async def fundamental_analysis(request: FundamentalAnalysisRequest) -> dict:
    """
    Run fundamental analysis on a stock's financial statements.
    
    Both agents use `fundamental_analysis_report` tool.
    The difference is in how they process/present the results.
    """
    start_time = time.time()
    agent_type = get_agent_type(request.agent_type)
    
    logger.info("Fundamental analysis: %s (agent=%s)", request.symbol, agent_type)
    
    try:
        if agent_type == "code_agent":
            result = await run_in_threadpool(
                run_fundamental_codeagent,
                symbol=request.symbol,
                period=request.period,
                model_id=request.model_id or DEFAULT_MODEL_ID,
                model_provider=request.model_provider or DEFAULT_MODEL_PROVIDER,
                openai_api_key=request.openai_api_key or DEFAULT_API_KEY,
                hf_token=request.hf_token or DEFAULT_HF_TOKEN,
                openai_base_url=DEFAULT_OPENAI_BASE,
                max_steps=request.max_steps or 15,
                executor_type=request.executor_type or DEFAULT_EXECUTOR,
            )
        else:
            result = await run_in_threadpool(
                run_fundamental_toolcalling,
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
    logger.info("Fundamental analysis completed: %s in %.2fs", request.symbol, duration)
    
    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "fundamental",
        "duration_seconds": round(duration, 2),
        "agent_type": agent_type,
        "tools_approach": get_tools_approach(agent_type),
    }


# =============================================================================
# Multi-Sector Analysis Endpoint
# =============================================================================

@app.post("/multisector", tags=["analysis"], response_model=AnalysisResponse)
async def multi_sector_analysis(request: MultiSectorAnalysisRequest) -> dict:
    """
    Run comprehensive multi-sector analysis.
    
    **ToolCallingAgent (tool_calling):**
    - Calls `unified_market_scanner` once per sector
    - N sectors = N MCP calls
    
    **CodeAgent (code_agent):**
    - Writes nested loops (sector → stock → strategy)
    - More granular but slower
    """
    start_time = time.time()
    agent_type = get_agent_type(request.agent_type)
    
    sectors_dict = {sector.name: sector.symbols for sector in request.sectors}
    total_stocks = sum(
        len([s for s in sector.symbols.split(",") if s.strip()])
        for sector in request.sectors
    )
    
    logger.info(
        "Multi-sector analysis: %d sectors, %d stocks (agent=%s)",
        len(request.sectors), total_stocks, agent_type
    )
    
    try:
        if agent_type == "code_agent":
            result = await run_in_threadpool(
                run_multisector_codeagent,
                sectors=sectors_dict,
                period=request.period,
                model_id=request.model_id or DEFAULT_MODEL_ID,
                model_provider=request.model_provider or DEFAULT_MODEL_PROVIDER,
                openai_api_key=request.openai_api_key or DEFAULT_API_KEY,
                hf_token=request.hf_token or DEFAULT_HF_TOKEN,
                openai_base_url=DEFAULT_OPENAI_BASE,
                max_steps=request.max_steps or 50,
                executor_type=request.executor_type or DEFAULT_EXECUTOR,
            )
        else:
            result = await run_in_threadpool(
                run_multisector_toolcalling,
                sectors=sectors_dict,
                period=request.period,
                model_id=request.model_id or DEFAULT_MODEL_ID,
                model_provider=request.model_provider or DEFAULT_MODEL_PROVIDER,
                openai_api_key=request.openai_api_key or DEFAULT_API_KEY,
                hf_token=request.hf_token or DEFAULT_HF_TOKEN,
                openai_base_url=DEFAULT_OPENAI_BASE,
                max_steps=request.max_steps or 30,
            )
    except Exception as exc:
        logger.exception("Multi-sector analysis failed")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
    
    duration = time.time() - start_time
    sector_names = ", ".join(sectors_dict.keys())
    logger.info("Multi-sector completed in %.2fs (%s)", duration, agent_type)
    
    return {
        "report": result,
        "symbol": sector_names,
        "analysis_type": "multi_sector",
        "duration_seconds": round(duration, 2),
        "agent_type": agent_type,
        "tools_approach": get_tools_approach(agent_type),
    }


# =============================================================================
# Combined Analysis Endpoint
# =============================================================================

@app.post("/combined", tags=["analysis"], response_model=AnalysisResponse)
async def combined_analysis(request: CombinedAnalysisRequest) -> dict:
    """
    Run combined Technical + Fundamental analysis.
    
    **ToolCallingAgent (tool_calling):**
    - `comprehensive_performance_report` (1 call) + `fundamental_analysis_report` (1 call)
    - 2 MCP calls total
    
    **CodeAgent (code_agent):**
    - 4 strategy tools + fundamental_analysis_report
    - 5 tool calls via Python code
    """
    start_time = time.time()
    agent_type = get_agent_type(request.agent_type)
    
    logger.info("Combined analysis: %s (agent=%s)", request.symbol, agent_type)
    
    try:
        if agent_type == "code_agent":
            result = await run_in_threadpool(
                run_combined_codeagent,
                symbol=request.symbol,
                technical_period=request.technical_period,
                fundamental_period=request.fundamental_period,
                model_id=request.model_id or DEFAULT_MODEL_ID,
                model_provider=request.model_provider or DEFAULT_MODEL_PROVIDER,
                openai_api_key=request.openai_api_key or DEFAULT_API_KEY,
                hf_token=request.hf_token or DEFAULT_HF_TOKEN,
                openai_base_url=DEFAULT_OPENAI_BASE,
                max_steps=request.max_steps or 25,
                executor_type=request.executor_type or DEFAULT_EXECUTOR,
            )
        else:
            result = await run_in_threadpool(
                run_combined_toolcalling,
                symbol=request.symbol,
                technical_period=request.technical_period,
                fundamental_period=request.fundamental_period,
                model_id=request.model_id or DEFAULT_MODEL_ID,
                model_provider=request.model_provider or DEFAULT_MODEL_PROVIDER,
                openai_api_key=request.openai_api_key or DEFAULT_API_KEY,
                hf_token=request.hf_token or DEFAULT_HF_TOKEN,
                openai_base_url=DEFAULT_OPENAI_BASE,
                max_steps=request.max_steps or DEFAULT_MAX_STEPS,
            )
    except Exception as exc:
        logger.exception("Combined analysis failed for %s", request.symbol)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
    
    duration = time.time() - start_time
    logger.info("Combined analysis completed: %s in %.2fs", request.symbol, duration)
    
    return {
        "report": result,
        "symbol": request.symbol.upper(),
        "analysis_type": "combined",
        "duration_seconds": round(duration, 2),
        "agent_type": agent_type,
        "tools_approach": get_tools_approach(agent_type),
    }