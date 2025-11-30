# Stock Analyzer Bot

An AI-powered financial analysis application built with **smolagents**, **FastAPI**, and **MCP** (Model Context Protocol). This bot uses Large Language Models to orchestrate financial analysis tools and generate professional investment reports.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Configuration](#configuration)
- [Module Reference](#module-reference)
  - [main.py - Core Analysis Engine](#mainpy---core-analysis-engine)
  - [api.py - FastAPI Backend](#apipy---fastapi-backend)
  - [tools.py - Smolagents Tool Wrappers](#toolspy---smolagents-tool-wrappers)
  - [mcp_client.py - MCP Server Connection](#mcp_clientpy---mcp-server-connection)
- [API Endpoints](#api-endpoints)
- [Analysis Types](#analysis-types)
- [Streamlit Frontend](#streamlit-frontend)
- [Environment Variables](#environment-variables)
- [Usage Examples](#usage-examples)

---

## Overview

The Stock Analyzer Bot transforms raw financial data into actionable investment insights using AI. Unlike traditional analysis tools that output raw numbers, this system uses LLMs to:

1. **Orchestrate** - Decide which tools to call and in what order
2. **Execute** - Call MCP finance tools to get market data
3. **Interpret** - Understand what the numbers mean
4. **Synthesize** - Combine multiple data sources into coherent analysis
5. **Report** - Generate professional markdown reports with recommendations

### Key Features

| Feature | Description |
|---------|-------------|
| **5 Analysis Types** | Technical, Scanner, Fundamental, Multi-Sector, Combined |
| **AI-Powered Reports** | LLM interprets data, not just displays it |
| **Multiple LLM Support** | OpenAI, HuggingFace, and other LiteLLM-compatible models |
| **REST API** | FastAPI backend for integration |
| **Web UI** | Streamlit frontend for interactive analysis |
| **MCP Integration** | Connects to MCP server for financial tools |

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         STOCK ANALYZER BOT                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │  Streamlit  │───▶│   FastAPI   │───▶│  smolagents │                 │
│  │  Frontend   │    │   Backend   │    │    Agent    │                 │
│  └─────────────┘    └─────────────┘    └──────┬──────┘                 │
│                                               │                         │
│                                               ▼                         │
│                                        ┌─────────────┐                 │
│                                        │   LLM API   │                 │
│                                        │ (OpenAI/HF) │                 │
│                                        └──────┬──────┘                 │
│                                               │                         │
│                                               ▼                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │    MCP      │◀───│   tools.py  │◀───│   Agent     │                 │
│  │   Client    │    │  (wrappers) │    │  Decisions  │                 │
│  └──────┬──────┘    └─────────────┘    └─────────────┘                 │
│         │                                                               │
└─────────┼───────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────┐
│   MCP SERVER    │
│  (server/main)  │
│                 │
│  ┌───────────┐  │
│  │ Strategies│  │
│  │  Tools    │  │
│  └─────┬─────┘  │
│        │        │
│        ▼        │
│  ┌───────────┐  │
│  │  Yahoo    │  │
│  │  Finance  │  │
│  └───────────┘  │
└─────────────────┘
```

### Folder Structure

```
stock_analyzer_bot/
├── __init__.py           # Package initialization
├── main.py               # Core analysis engine with LLM prompts
├── api.py                # FastAPI REST endpoints
├── tools.py              # Smolagents tool wrappers for MCP
└── mcp_client.py         # MCP server connection manager
```

### Data Flow

```
User Request
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. FastAPI Endpoint receives request                        │
│    - Validates input (symbol, period, etc.)                 │
│    - Calls appropriate run_*_analysis() function            │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Analysis Function (main.py)                              │
│    - Builds LLM model (OpenAI/HuggingFace)                  │
│    - Creates ToolCallingAgent with specific tools           │
│    - Formats prompt with user parameters                    │
│    - Runs agent.run(prompt)                                 │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Smolagents ToolCallingAgent                              │
│    - LLM reads prompt and decides which tools to call       │
│    - For each tool call:                                    │
│      a. Agent generates tool name + parameters              │
│      b. Tool wrapper (tools.py) is invoked                  │
│      c. Wrapper calls MCP client                            │
│      d. MCP client sends request to MCP server              │
│      e. Server executes tool, returns data                  │
│      f. Data returned to agent                              │
│    - Agent synthesizes all results                          │
│    - Agent generates final markdown report                  │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Response                                                 │
│    - Markdown report returned to FastAPI                    │
│    - FastAPI wraps in JSON response                         │
│    - Streamlit displays formatted report                    │
└─────────────────────────────────────────────────────────────┘
```

---

## How It Works

### The Smolagents Pattern

Smolagents is a framework for building AI agents that can use tools. Here's how we use it:

```python
from smolagents import ToolCallingAgent, LiteLLMModel

# 1. Build the model (connection to LLM)
model = LiteLLMModel(model_id="gpt-4o", api_key="...")

# 2. Create agent with tools
agent = ToolCallingAgent(
    tools=[tool1, tool2, tool3],  # Functions the LLM can call
    model=model,
    max_steps=25,  # Limit reasoning iterations
)

# 3. Run with a prompt
result = agent.run("Analyze AAPL stock using all available tools")
```

### Tool Execution Flow

When the agent decides to call a tool:

```
Agent Decision: "I need to call bollinger_fibonacci_analysis for AAPL"
          │
          ▼
    ┌─────────────────────────────────────────────┐
    │ @tool                                       │
    │ def bollinger_fibonacci_analysis(symbol):   │
    │     return _call_finance_tool(              │
    │         "analyze_bollinger_fibonacci_...",  │
    │         {"symbol": symbol, "period": "1y"}  │
    │     )                                       │
    └─────────────────────────────────────────────┘
          │
          ▼
    ┌─────────────────────────────────────────────┐
    │ _call_finance_tool()                        │
    │     session = get_session()                 │
    │     return session.call_tool(name, params)  │
    └─────────────────────────────────────────────┘
          │
          ▼
    ┌─────────────────────────────────────────────┐
    │ MCPFinanceSession.call_tool()               │
    │     # Sends JSON-RPC to MCP server          │
    │     # via stdio transport                   │
    └─────────────────────────────────────────────┘
          │
          ▼
    ┌─────────────────────────────────────────────┐
    │ MCP Server (server/main.py)                 │
    │     # Executes strategy calculation         │
    │     # Returns performance data              │
    └─────────────────────────────────────────────┘
          │
          ▼
    Data flows back up to agent
```

---

## Installation

### Prerequisites

- Python 3.10+
- MCP Server (`server/` folder at project root)
- OpenAI API key (or HuggingFace token)

### Dependencies

```bash
pip install smolagents fastapi uvicorn streamlit requests python-dotenv mcp
```

### Quick Start

```bash
# 1. Start the FastAPI backend
uvicorn stock_analyzer_bot.api:app --reload --port 8000

# 2. (Optional) Start Streamlit frontend
streamlit run streamlit_app.py

# 3. (Optional) Run CLI analysis
python -m stock_analyzer_bot.main AAPL --period 1y
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# LLM Configuration
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_BASE_URL=                      # Optional: for custom endpoints
HF_TOKEN=hf_your_huggingface_token    # For HuggingFace models

# Model Defaults
SMOLAGENT_MODEL_ID=gpt-4.1            # Default model
SMOLAGENT_MODEL_PROVIDER=litellm       # litellm or inference
SMOLAGENT_MAX_STEPS=25                 # Max agent iterations

# Analysis Defaults
DEFAULT_ANALYSIS_PERIOD=1y
DEFAULT_SCANNER_SYMBOLS=AAPL,MSFT,GOOGL,AMZN

# API Server
STOCK_ANALYZER_API_URL=http://localhost:8000
```

---

## Module Reference

### main.py - Core Analysis Engine

The heart of the application. Contains LLM prompts and analysis orchestration functions.

#### Key Components

**Prompt Templates:**
```python
TECHNICAL_ANALYSIS_PROMPT    # Single stock, 4 strategies
MARKET_SCANNER_PROMPT        # Multiple stocks comparison
FUNDAMENTAL_ANALYSIS_PROMPT  # Financial statements
MULTI_SECTOR_ANALYSIS_PROMPT # Cross-sector comparison
COMBINED_ANALYSIS_PROMPT     # Technical + Fundamental
```

**Builder Functions:**
```python
def build_model(model_id, provider, ...) -> Model:
    """Create LiteLLMModel or InferenceClientModel based on provider."""
    
def build_agent(model, tools, max_steps) -> ToolCallingAgent:
    """Create smolagents ToolCallingAgent with specified tools."""
```

**Analysis Functions:**

| Function | Purpose | Tools Used | Max Steps |
|----------|---------|------------|-----------|
| `run_technical_analysis()` | Single stock, 4 strategies | STRATEGY_TOOLS (4) | 25 |
| `run_market_scanner()` | Compare multiple stocks | STRATEGY_TOOLS (4) | 50+ |
| `run_fundamental_analysis()` | Financial statements | fundamental_analysis_report | 25 |
| `run_multi_sector_analysis()` | Cross-sector comparison | STRATEGY_TOOLS (4) | 100+ |
| `run_combined_analysis()` | Tech + Fundamental | STRATEGY_TOOLS + fundamental | 35 |

#### Function Signatures

```python
def run_technical_analysis(
    symbol: str,                    # e.g., "AAPL"
    period: str = "1y",             # Historical period
    model_id: str = "gpt-4.1",      # LLM model
    model_provider: str = "litellm", # Provider type
    hf_token: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    max_steps: int = 25,
) -> str:  # Returns markdown report
```

---

### api.py - FastAPI Backend

RESTful API exposing all analysis functions.

#### Application Setup

```python
app = FastAPI(
    title="MCP Stock Analyzer API",
    version="2.2.0",
)

# CORS enabled for frontend access
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

# Lifecycle events
@app.on_event("startup")   # Initialize MCP connection
@app.on_event("shutdown")  # Clean up MCP connection
```

#### Request Models

```python
class TechnicalAnalysisRequest(BaseModel):
    symbol: str           # Required: ticker symbol
    period: str = "1y"    # Historical period
    model_id: Optional[str]
    model_provider: Optional[str]
    openai_api_key: Optional[str]
    hf_token: Optional[str]
    max_steps: Optional[int]

class MarketScannerRequest(BaseModel):
    symbols: str          # Comma-separated: "AAPL,MSFT,GOOGL"
    period: str = "1y"
    # ... same optional fields

class FundamentalAnalysisRequest(BaseModel):
    symbol: str
    period: str = "3y"    # Years of financial data
    # ... same optional fields

class MultiSectorAnalysisRequest(BaseModel):
    sectors: List[SectorConfig]  # [{"name": "Banking", "symbols": "JPM,BAC"}]
    period: str = "1y"
    # ... same optional fields

class CombinedAnalysisRequest(BaseModel):
    symbol: str
    technical_period: str = "1y"
    fundamental_period: str = "3y"
    # ... same optional fields
```

#### Response Model

```python
class AnalysisResponse(BaseModel):
    report: str              # Markdown analysis report
    symbol: str              # Symbol(s) analyzed
    analysis_type: str       # "technical", "scanner", etc.
    duration_seconds: float  # Processing time
```

---

### tools.py - Smolagents Tool Wrappers

Bridges smolagents with MCP server. Each tool is a decorated function that the LLM can call.

#### Tool Categories

**STRATEGY_TOOLS (4 tools for technical analysis):**
```python
STRATEGY_TOOLS = [
    bollinger_fibonacci_analysis,   # BB + Fibonacci
    macd_donchian_analysis,         # MACD + Donchian
    connors_zscore_analysis,        # Connors RSI + Z-Score
    dual_moving_average_analysis,   # 50/200 EMA Crossover
]
```

**Additional Tools:**
```python
comprehensive_performance_report  # Deterministic multi-strategy report
unified_market_scanner           # Multi-stock scanner
fundamental_analysis_report      # Financial statements
```

#### Tool Definition Pattern

```python
from smolagents import tool

@tool
def bollinger_fibonacci_analysis(
    symbol: str,
    period: str = "1y",
    window: int = 20,
    num_std: float = 2.0,
    window_swing_points: int = 10,
) -> str:
    """Run the Bollinger-Fibonacci combined MCP strategy analysis.
    
    This strategy combines Bollinger Bands (mean reversion) with Fibonacci 
    retracement levels (support/resistance) for comprehensive price analysis.
    
    Args:
        symbol: Ticker to analyze (e.g., 'AAPL', 'MSFT').
        period: Historical period (default: '1y').
        window: Bollinger band lookback window (default: 20).
        num_std: Standard deviations for bands (default: 2.0).
        window_swing_points: Swing point detection window (default: 10).
    
    Returns:
        Detailed performance report with signals and metrics.
    """
    params = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "window": window,
        "num_std": num_std,
        "window_swing_points": window_swing_points,
    }
    return _call_finance_tool("analyze_bollinger_fibonacci_performance", params)
```

#### Internal Helper Functions

```python
def _normalize_symbol(symbol: str) -> str:
    """Clean and validate ticker symbol."""
    cleaned = symbol.strip().upper()
    if not cleaned:
        raise ValueError("Symbol must be a non-empty string")
    return cleaned

def _call_finance_tool(tool_name: str, parameters: Dict) -> str:
    """Call MCP server tool via session."""
    try:
        return get_session().call_tool(tool_name, parameters)
    except Exception as exc:
        logger.exception("Error calling %s", tool_name)
        return f"Error calling {tool_name}: {exc}"
```

---

### mcp_client.py - MCP Server Connection

Manages the long-lived connection to the MCP finance server.

#### MCPFinanceSession Class

```python
class MCPFinanceSession:
    """Manage a long-lived connection to the finance MCP server."""
    
    def __init__(self, server_path: Path = None):
        self.server_path = server_path or _DEFAULT_SERVER_PATH
        self._session: Optional[ClientSession] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        
    def start(self):
        """Start MCP server connection in background thread."""
        # Creates async event loop in separate thread
        # Establishes stdio connection to server/main.py
        
    def stop(self):
        """Stop MCP server connection."""
        
    def call_tool(self, name: str, arguments: Dict) -> str:
        """Call a tool on the MCP server synchronously."""
        # Bridges sync code to async MCP calls
```

#### Connection Pattern

```python
# Default server path (relative to mcp_client.py)
_DEFAULT_SERVER_PATH = Path(__file__).resolve().parents[1] / "server" / "main.py"

# Server parameters for stdio transport
server_params = StdioServerParameters(
    command="python",
    args=[str(self.server_path)]
)

# Connection via MCP protocol
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        # Session ready for tool calls
```

#### Module-Level Functions

```python
# Global session management
_session: Optional[MCPFinanceSession] = None

def configure_session(server_path: Path = None):
    """Initialize MCP session (called on startup)."""
    global _session
    _session = MCPFinanceSession(server_path)
    _session.start()

def get_session() -> MCPFinanceSession:
    """Get the active MCP session."""
    if _session is None:
        configure_session()
    return _session

def shutdown_session():
    """Stop the MCP session (called on shutdown)."""
    global _session
    if _session:
        _session.stop()
        _session = None
```

---

## API Endpoints

### GET /health

Health check and feature list.

**Response:**
```json
{
  "status": "ok",
  "version": "2.2.0",
  "features": [
    "technical_analysis",
    "market_scanner",
    "fundamental_analysis",
    "multi_sector_analysis",
    "combined_analysis"
  ],
  "model": {
    "default_id": "gpt-4.1",
    "default_provider": "litellm"
  }
}
```

---

### POST /technical

Single stock technical analysis with 4 strategies.

**Request:**
```json
{
  "symbol": "AAPL",
  "period": "1y"
}
```

**What Happens:**
1. Agent calls 4 strategy tools for AAPL
2. Each tool returns performance metrics
3. Agent synthesizes into report

**Response:**
```json
{
  "report": "# AAPL Comprehensive Technical Analysis\n...",
  "symbol": "AAPL",
  "analysis_type": "technical",
  "duration_seconds": 45.2
}
```

---

### POST /scanner

Multi-stock comparison and ranking.

**Request:**
```json
{
  "symbols": "AAPL,MSFT,GOOGL,META,NVDA",
  "period": "1y"
}
```

**What Happens:**
1. Agent calls 4 strategy tools for EACH stock (20 total calls)
2. Compares performance across all stocks
3. Ranks and identifies best opportunities

**Response:**
```json
{
  "report": "# Multi-Stock Market Analysis Report\n...",
  "symbol": "AAPL,MSFT,GOOGL,META,NVDA",
  "analysis_type": "scanner",
  "duration_seconds": 180.5
}
```

---

### POST /fundamental

Financial statement analysis.

**Request:**
```json
{
  "symbol": "MSFT",
  "period": "3y"
}
```

**What Happens:**
1. Agent calls fundamental_analysis_report tool
2. Gets income statement, balance sheet, cash flow
3. Interprets financial health and creates thesis

**Response:**
```json
{
  "report": "# MSFT Fundamental Analysis Report\n...",
  "symbol": "MSFT",
  "analysis_type": "fundamental",
  "duration_seconds": 35.0
}
```

---

### POST /multisector

Cross-sector comparative analysis.

**Request:**
```json
{
  "sectors": [
    {"name": "Banking", "symbols": "JPM,BAC,WFC,C,GS"},
    {"name": "Technology", "symbols": "AAPL,MSFT,GOOGL,META,NVDA"},
    {"name": "Clean Energy", "symbols": "TSLA,NIO,ENPH,PLUG,NEE"}
  ],
  "period": "1y"
}
```

**What Happens:**
1. Agent processes each sector
2. Calls 4 tools per stock (60 total calls for 15 stocks)
3. Compares performance ACROSS sectors
4. Identifies best opportunities from entire universe

**Response:**
```json
{
  "report": "# Multi-Sector Market Analysis Report\n...",
  "symbol": "Banking, Technology, Clean Energy",
  "analysis_type": "multi_sector",
  "duration_seconds": 450.0
}
```

---

### POST /combined

Combined Technical + Fundamental analysis.

**Request:**
```json
{
  "symbol": "AAPL",
  "technical_period": "1y",
  "fundamental_period": "3y"
}
```

**What Happens:**
1. Agent calls fundamental_analysis_report
2. Agent calls 4 technical strategy tools
3. Synthesizes BOTH perspectives
4. Determines if signals align or diverge

**Response:**
```json
{
  "report": "# AAPL Combined Investment Analysis\n...",
  "symbol": "AAPL",
  "analysis_type": "combined",
  "duration_seconds": 75.0
}
```

---

## Analysis Types

### Comparison Table

| Type | Endpoint | Stocks | Tools/Stock | Purpose | Time |
|------|----------|--------|-------------|---------|------|
| Technical | `/technical` | 1 | 4 | Deep dive single stock | 30-60s |
| Scanner | `/scanner` | N | 4 | Compare opportunities | 2-5min |
| Fundamental | `/fundamental` | 1 | 1 | Financial health | 30s |
| Multi-Sector | `/multisector` | N×M | 4 | Cross-sector comparison | 5-15min |
| Combined | `/combined` | 1 | 5 | Complete analysis | 60-90s |

### When to Use Each

| Use Case | Recommended Analysis |
|----------|---------------------|
| "Should I buy AAPL?" | Combined Analysis |
| "What's the best tech stock?" | Market Scanner |
| "Is MSFT financially healthy?" | Fundamental Analysis |
| "Where should I invest across sectors?" | Multi-Sector Analysis |
| "What do the charts say about TSLA?" | Technical Analysis |

---

## Streamlit Frontend

The `streamlit_app.py` provides a web UI with 5 tabs:

### Features

- **Technical Analysis Tab**: Single stock, period selector
- **Market Scanner Tab**: Multi-stock input, comparison
- **Fundamental Analysis Tab**: Financial statement analysis
- **Multi-Sector Tab**: Configurable sectors with add/remove
- **Combined Analysis Tab**: Tech + Fundamental together

### Session State

```python
st.session_state.messages     # Analysis history
st.session_state.api_url      # Backend URL
st.session_state.model_id     # LLM model
st.session_state.model_provider  # Provider
st.session_state.openai_api_key  # API key override
```

### API Communication

```python
def call_api(endpoint: str, payload: Dict) -> Dict:
    """Call FastAPI backend with model settings."""
    # Adds model_id, model_provider, openai_api_key to payload
    # Timeout: 600s normal, 1200s for multi-sector
    response = requests.post(url, json=payload, timeout=timeout)
    return response.json()
```

---

## Usage Examples

### CLI Usage

```bash
# Basic technical analysis
python -m stock_analyzer_bot.main AAPL

# With custom period
python -m stock_analyzer_bot.main TSLA --period 2y

# With custom model
python -m stock_analyzer_bot.main MSFT --model-id gpt-4o --model-provider litellm

# Save output to file
python -m stock_analyzer_bot.main GOOGL --output report.md
```

### Python API

```python
from stock_analyzer_bot.main import (
    run_technical_analysis,
    run_market_scanner,
    run_fundamental_analysis,
    run_combined_analysis,
)

# Technical Analysis
report = run_technical_analysis("AAPL", period="1y")
print(report)

# Market Scanner
report = run_market_scanner("AAPL,MSFT,GOOGL", period="1y")
print(report)

# Fundamental Analysis
report = run_fundamental_analysis("MSFT", period="3y")
print(report)

# Combined Analysis
report = run_combined_analysis("AAPL", technical_period="1y", fundamental_period="3y")
print(report)
```

### REST API

```bash
# Technical Analysis
curl -X POST "http://localhost:8000/technical" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "period": "1y"}'

# Market Scanner
curl -X POST "http://localhost:8000/scanner" \
  -H "Content-Type: application/json" \
  -d '{"symbols": "AAPL,MSFT,GOOGL", "period": "1y"}'

# Multi-Sector
curl -X POST "http://localhost:8000/multisector" \
  -H "Content-Type: application/json" \
  -d '{
    "sectors": [
      {"name": "Tech", "symbols": "AAPL,MSFT"},
      {"name": "Finance", "symbols": "JPM,BAC"}
    ],
    "period": "1y"
  }'
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "MCP server not found" | Server path incorrect | Check `server/main.py` exists |
| "Connection refused" | FastAPI not running | Start with `uvicorn` |
| "Timeout" | Too many stocks | Reduce stock count or increase timeout |
| "Authentication error" | Invalid API key | Check `OPENAI_API_KEY` in `.env` |
| "Agent stopped early" | Max steps reached | Increase `max_steps` parameter |

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
uvicorn stock_analyzer_bot.api:app --reload --port 8000
```

---

## Version History

| Version | Changes |
|---------|---------|
| 1.0.0 | Initial release with technical analysis |
| 2.0.0 | Added Market Scanner, Fundamental Analysis |
| 2.1.0 | Added Multi-Sector Analysis |
| 2.2.0 | Added Combined Technical + Fundamental Analysis |

---

## License

This software is provided for educational and research purposes. Always verify analysis results and consult financial professionals before making investment decisions.

---

*Built with [smolagents](https://github.com/huggingface/smolagents), [FastAPI](https://fastapi.tiangolo.com/), and [MCP](https://modelcontextprotocol.io/)*