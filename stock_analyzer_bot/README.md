# 🤖 Stock Analyzer Bot

Smolagents-powered AI orchestration layer that connects LLMs to MCP financial analysis tools. This module supports **two agent architectures**: ToolCallingAgent (JSON-based) and CodeAgent (Python code-based).

---

## 📋 Table of Contents

- [Overview](#overview)
- [Agent Types](#agent-types)
- [Architecture](#architecture)
- [Module Reference](#module-reference)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Stock Analyzer Bot is the **AI orchestration layer** that:

1. Receives analysis requests from the API
2. Uses an LLM (OpenAI/HuggingFace) to decide which tools to call
3. Executes MCP tools via the client connection
4. Synthesizes results into professional markdown reports

### Key Features

- **Dual Agent Support**: ToolCallingAgent OR CodeAgent
- **5 Analysis Types**: Technical, Scanner, Fundamental, Multi-Sector, Combined
- **MCP Integration**: Seamless connection to financial tools
- **LLM Agnostic**: Works with OpenAI, HuggingFace, and more

---

## Agent Types

### 🔧 ToolCallingAgent (`main.py`)

The original implementation using JSON-based tool calls.

**How It Works:**
```
User: "Analyze AAPL"
     ↓
LLM: {"tool": "bollinger_fibonacci_analysis", "args": {"symbol": "AAPL"}}
     ↓
Execute tool → Return result
     ↓
LLM: {"tool": "macd_donchian_analysis", "args": {"symbol": "AAPL"}}
     ↓
Execute tool → Return result
     ↓
... (repeat for each tool)
     ↓
LLM: Synthesize all results → Generate report
```

**Characteristics:**
- One tool call per LLM round
- Sequential execution
- Simple and predictable
- No code execution risks

### 🐍 CodeAgent (`main_codeagent.py`)

The advanced implementation where LLM writes Python code.

**How It Works:**
```
User: "Analyze AAPL, MSFT, GOOGL"
     ↓
LLM generates Python code:
┌──────────────────────────────────────────────────┐
│ results = {}                                      │
│ for stock in ["AAPL", "MSFT", "GOOGL"]:          │
│     results[stock] = {                            │
│         "bb": bollinger_fibonacci_analysis(stock),│
│         "macd": macd_donchian_analysis(stock),   │
│     }                                             │
│                                                   │
│ # Rank by performance                             │
│ ranked = sorted(results.items(), key=...)        │
│ final_answer(generate_report(ranked))            │
└──────────────────────────────────────────────────┘
     ↓
Python Executor runs code → Calls all tools
     ↓
Return final report
```

**Characteristics:**
- Multiple tools in one LLM round
- Loop-based for multi-stock
- Can store variables and compute
- Requires code execution sandbox

### Comparison Table

| Feature | ToolCallingAgent | CodeAgent |
|---------|-----------------|-----------|
| Tool calls per round | 1 | Many (via loops) |
| Multi-stock efficiency | ⚠️ Slow | ✅ Fast |
| Variable storage | ❌ No | ✅ Yes |
| Debugging | ✅ Easy | ⚠️ Harder |
| Security | ✅ Safe | ⚠️ Needs sandbox |
| LLM requirements | Any LLM | Good at Python |

---

## Architecture

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         STOCK ANALYZER BOT                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐                                                        │
│  │   api.py    │  ← FastAPI endpoints                                   │
│  │             │    Receives requests, selects agent type               │
│  └──────┬──────┘                                                        │
│         │                                                               │
│         ▼                                                               │
│  ┌──────────────────────────────────────────────────┐                   │
│  │              AGENT SELECTION                     │                   │
│  │  ┌──────────────────┐  ┌──────────────────────┐  │                   │
│  │  │     main.py      │  │  main_codeagent.py   │  │                   │
│  │  │ ToolCallingAgent │  │     CodeAgent        │  │                   │
│  │  │   (JSON-based)   │  │  (Python code)       │  │                   │
│  │  └────────┬─────────┘  └──────────┬───────────┘  │                   │
│  └───────────┼───────────────────────┼──────────────┘                   │
│              │                       │                                  │
│              └───────────┬───────────┘                                  │
│                          ▼                                              │
│  ┌─────────────────────────────────────────────────┐                    │
│  │               tools.py                          │                    │
│  │    @tool decorated functions                    │                    │
│  │    bollinger_fibonacci_analysis()               │                    │
│  │    macd_donchian_analysis()                     │                    │
│  │    connors_zscore_analysis()                    │                    │
│  │    dual_moving_average_analysis()               │                    │
│  │    fundamental_analysis_report()                │                    │
│  └──────────────────────┬──────────────────────────┘                    │
│                         │                                               │
│                         ▼                                               │
│  ┌─────────────────────────────────────────────────┐                    │
│  │            mcp_client.py                        │                    │
│  │    MCPFinanceSession                            │                    │
│  │    - Manages MCP server connection              │                    │
│  │    - Sends tool calls via stdio                 │                    │
│  └──────────────────────┬──────────────────────────┘                    │
│                         │ stdio                                         │
└─────────────────────────┼───────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │    MCP SERVER         │
              │   (server/main.py)    │
              │   Financial Tools     │
              └───────────────────────┘
```

### File Structure

```
stock_analyzer_bot/
├── __init__.py              # Package initialization
├── main.py                  # ToolCallingAgent implementation
├── main_codeagent.py        # CodeAgent implementation (NEW)
├── api.py                   # FastAPI REST endpoints
├── tools.py                 # Smolagents @tool wrappers
├── mcp_client.py            # MCP server connection manager
└── README.md                # This file
```

---

## Module Reference

### `main.py` - ToolCallingAgent Implementation

**Constants:**
```python
DEFAULT_MODEL_ID = "gpt-4o"           # LLM model
DEFAULT_MODEL_PROVIDER = "litellm"    # Provider type
DEFAULT_MAX_STEPS = 25                # Max reasoning steps
```

**Functions:**

| Function | Description | Tools Used |
|----------|-------------|------------|
| `build_model()` | Creates LLM model instance | - |
| `build_agent()` | Creates ToolCallingAgent | - |
| `run_technical_analysis()` | Single stock, 4 strategies | 4 |
| `run_market_scanner()` | Multi-stock comparison | 4 × N stocks |
| `run_fundamental_analysis()` | Financial statements | 1 |
| `run_multi_sector_analysis()` | Cross-sector | 4 × total stocks |
| `run_combined_analysis()` | Tech + Fundamental | 5 |

### `main_codeagent.py` - CodeAgent Implementation

**Additional Constants:**
```python
DEFAULT_EXECUTOR = "local"  # Code execution: local, e2b, docker
```

**Functions:**
Same as `main.py` but using CodeAgent internally.

**Key Difference - Agent Creation:**
```python
# main.py (ToolCallingAgent)
def build_agent(model, tools, max_steps=25):
    return ToolCallingAgent(
        tools=tools,
        model=model,
        max_steps=max_steps,
    )

# main_codeagent.py (CodeAgent)
def build_agent(model, tools, max_steps=20, executor_type="local"):
    return CodeAgent(
        tools=tools,
        model=model,
        max_steps=max_steps,
        executor_type=executor_type,  # NEW
        additional_authorized_imports=["statistics", "math"],
    )
```

### `api.py` - FastAPI Endpoints

**Version:** 2.3.0

**Request Models (all support agent_type):**
```python
class TechnicalAnalysisRequest(BaseModel):
    symbol: str
    period: str = "1y"
    agent_type: Optional[Literal["tool_calling", "code_agent"]] = None
    executor_type: Optional[Literal["local", "e2b", "docker"]] = None
    # ... model settings
```

**Response Model:**
```python
class AnalysisResponse(BaseModel):
    report: str               # Markdown report
    symbol: str               # Symbol(s) analyzed
    analysis_type: str        # technical, scanner, etc.
    duration_seconds: float   # Time taken
    agent_type: str           # Which agent was used (NEW)
```

### `tools.py` - Smolagents Tool Wrappers

**Available Tools:**
```python
STRATEGY_TOOLS = [
    bollinger_fibonacci_analysis,    # Bollinger + Fibonacci
    macd_donchian_analysis,          # MACD + Donchian
    connors_zscore_analysis,         # Connors RSI + Z-Score
    dual_moving_average_analysis,    # 50/200 EMA Crossover
]

# Additional tools
fundamental_analysis_report          # Financial statements
unified_market_scanner               # Multi-stock scanner
comprehensive_performance_report     # Backtesting report
```

**Tool Definition Pattern:**
```python
from smolagents import tool

@tool
def bollinger_fibonacci_analysis(symbol: str, period: str = "1y") -> str:
    """
    Analyze stock using Bollinger Bands + Fibonacci retracement.
    
    Args:
        symbol: Stock ticker (e.g., AAPL)
        period: Analysis period (1y, 6mo, etc.)
    
    Returns:
        JSON string with analysis results
    """
    return _call_finance_tool(
        "analyze_bollinger_fibonacci_performance",
        {"ticker": symbol, "period": period}
    )
```

### `mcp_client.py` - MCP Connection

**MCPFinanceSession Class:**
```python
class MCPFinanceSession:
    """Manages long-lived connection to MCP server."""
    
    def start(self):
        """Start background thread with async event loop."""
        
    def stop(self):
        """Clean up connection."""
        
    def call_tool(self, tool_name: str, args: dict) -> Any:
        """Synchronous wrapper for async MCP calls."""
```

**Module Functions:**
```python
def configure_session(server_script: Path = None):
    """Initialize global MCP session."""

def get_session() -> MCPFinanceSession:
    """Get the global session."""

def shutdown_session():
    """Clean up global session."""
```

---

## API Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "version": "2.3.0",
  "features": ["technical_analysis", "market_scanner", ...],
  "agent_types": {
    "tool_calling": true,
    "code_agent": true
  },
  "default_agent_type": "tool_calling"
}
```

### Technical Analysis

```http
POST /technical
Content-Type: application/json

{
  "symbol": "AAPL",
  "period": "1y",
  "agent_type": "code_agent",
  "executor_type": "local"
}
```

### Market Scanner

```http
POST /scanner
Content-Type: application/json

{
  "symbols": "AAPL,MSFT,GOOGL,META,NVDA",
  "period": "1y",
  "agent_type": "code_agent"
}
```

### Fundamental Analysis

```http
POST /fundamental
Content-Type: application/json

{
  "symbol": "MSFT",
  "period": "3y",
  "agent_type": "tool_calling"
}
```

### Multi-Sector Analysis

```http
POST /multisector
Content-Type: application/json

{
  "sectors": [
    {"name": "Banking", "symbols": "JPM,BAC,WFC"},
    {"name": "Technology", "symbols": "AAPL,MSFT,GOOGL"}
  ],
  "period": "1y",
  "agent_type": "code_agent"
}
```

### Combined Analysis

```http
POST /combined
Content-Type: application/json

{
  "symbol": "TSLA",
  "technical_period": "1y",
  "fundamental_period": "3y",
  "agent_type": "code_agent"
}
```

---

## Usage Examples

### Python - Direct Import

```python
from stock_analyzer_bot.tools import configure_finance_tools, shutdown_finance_tools

# Initialize MCP connection
configure_finance_tools()

try:
    # Using ToolCallingAgent
    from stock_analyzer_bot.main import run_technical_analysis
    report = run_technical_analysis(symbol="AAPL", period="1y")
    
    # Using CodeAgent
    from stock_analyzer_bot.main_codeagent import run_market_scanner
    report = run_market_scanner(
        symbols="AAPL,MSFT,GOOGL",
        period="1y",
        executor_type="local"
    )
    
    print(report)
finally:
    shutdown_finance_tools()
```

### CLI - ToolCallingAgent

```bash
python -m stock_analyzer_bot.main AAPL --mode technical --period 1y
python -m stock_analyzer_bot.main "AAPL,MSFT" --mode scanner
python -m stock_analyzer_bot.main MSFT --mode fundamental
```

### CLI - CodeAgent

```bash
python -m stock_analyzer_bot.main_codeagent AAPL --mode technical --executor local
python -m stock_analyzer_bot.main_codeagent "AAPL,MSFT,GOOGL" --mode scanner
python -m stock_analyzer_bot.main_codeagent TSLA --mode combined
```

### cURL - API

```bash
# Technical with CodeAgent
curl -X POST "http://localhost:8000/technical" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "agent_type": "code_agent"}'

# Scanner with ToolCallingAgent
curl -X POST "http://localhost:8000/scanner" \
  -H "Content-Type: application/json" \
  -d '{"symbols": "AAPL,MSFT", "agent_type": "tool_calling"}'
```

---

## Configuration

### Environment Variables

```bash
# LLM Configuration
OPENAI_API_KEY=sk-...           # Required for OpenAI
HF_TOKEN=hf_...                 # Required for HuggingFace
OPENAI_BASE_URL=                # Optional: Custom endpoint

# Model Settings
SMOLAGENT_MODEL_ID=gpt-4o       # Model to use
SMOLAGENT_MODEL_PROVIDER=litellm # litellm or inference

# Agent Settings (NEW)
SMOLAGENT_AGENT_TYPE=code_agent  # tool_calling or code_agent
SMOLAGENT_EXECUTOR=local         # local, e2b, or docker
SMOLAGENT_MAX_STEPS=25           # Max reasoning steps

# Analysis Defaults
DEFAULT_ANALYSIS_PERIOD=1y
DEFAULT_SCANNER_SYMBOLS=AAPL,MSFT,GOOGL,AMZN

# API Server
STOCK_ANALYZER_API_URL=http://localhost:8000
```

### Executor Types for CodeAgent

| Type | Setup | Security | Performance |
|------|-------|----------|-------------|
| `local` | None | ⚠️ Low | Fast |
| `e2b` | E2B account | ✅ High | Medium |
| `docker` | Docker installed | ✅ High | Medium |

**E2B Setup:**
```bash
pip install 'smolagents[e2b]'
# Create account at e2b.dev
export E2B_API_KEY=your-key
```

**Docker Setup:**
```bash
pip install 'smolagents[docker]'
# Ensure Docker is running
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "CodeAgent not available" | `main_codeagent.py` missing | Copy file to `stock_analyzer_bot/` |
| "MCP server not found" | Server path incorrect | Check `server/main.py` exists |
| "Connection refused" | FastAPI not running | Start with `uvicorn` |
| "Code execution failed" | Invalid Python from LLM | Try different model (gpt-4o) |
| "Timeout" | Too many stocks | Reduce count or use CodeAgent |
| "Authentication error" | Invalid API key | Check `OPENAI_API_KEY` |
| "Import not allowed" | CodeAgent sandbox | Add to `additional_authorized_imports` |

### Debugging Tips

**Enable verbose logging:**
```python
agent = CodeAgent(
    tools=tools,
    model=model,
    verbosity_level=2,  # 0=quiet, 1=normal, 2=verbose
)
```

**Check agent output:**
```python
result = agent.run(prompt)
print(agent.logs)  # View reasoning steps
```

---

## Related Documentation

- [Root README](../README.md) - Project overview
- [Server README](../server/README.md) - MCP tools reference
- [Smolagents Docs](https://huggingface.co/docs/smolagents/index) - Official docs
- [Secure Code Execution](https://huggingface.co/docs/smolagents/tutorials/secure_code_execution) - CodeAgent security

---

<p align="center">
  <i>Stock Analyzer Bot v2.3.0 - Now with dual agent support</i>
</p>