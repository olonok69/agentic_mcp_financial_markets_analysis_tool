# 📊 Stock Analyzer Bot

The **smolagents-powered orchestration layer** for the MCP Financial Markets Analysis Tool. This module provides two distinct agent architectures for executing financial analysis through MCP tools.

---

## 🎯 Overview

This module implements two agent types that orchestrate MCP finance tools:

| Agent Type | Implementation | Tools Used | Best For |
|------------|---------------|------------|----------|
| **ToolCallingAgent** | `main.py` | HIGH-LEVEL (1 call = full report) | Production, reliability |
| **CodeAgent** | `main_codeagent.py` | LOW-LEVEL (Python loops) | Speed, transparency |

Both agents provide identical analysis features but differ in execution approach.

---

## 📁 Module Structure

```
stock_analyzer_bot/
├── __init__.py              # Package initialization
├── main.py                  # ToolCallingAgent implementation
├── main_codeagent.py        # CodeAgent implementation
├── api.py                   # FastAPI endpoints with agent selection
├── tools.py                 # MCP tool wrappers
├── mcp_client.py            # MCP session management
└── README.md                # This file
```

---

## 🔧 Tool Categories

### HIGH-LEVEL Tools (for ToolCallingAgent)

These tools do everything in **ONE MCP call**. The MCP server handles all complexity internally.

```python
from stock_analyzer_bot.tools import HIGH_LEVEL_TOOLS

# Available tools:
# - comprehensive_performance_report: All 4 strategies + full report (1 call)
# - unified_market_scanner: Multi-stock scanning with rankings (1 call)
# - fundamental_analysis_report: Financial statements analysis (1 call)
```

**Usage:**
```python
from stock_analyzer_bot.tools import comprehensive_performance_report

result = comprehensive_performance_report("AAPL", "1y")
# Returns complete markdown report with all 4 strategies
```

### LOW-LEVEL Tools (for CodeAgent)

These are **granular tools** that CodeAgent orchestrates with Python code.

```python
from stock_analyzer_bot.tools import LOW_LEVEL_TOOLS

# Available tools:
# - bollinger_fibonacci_analysis: Single strategy, single stock
# - macd_donchian_analysis: Single strategy, single stock
# - connors_zscore_analysis: Single strategy, single stock
# - dual_moving_average_analysis: Single strategy, single stock
# - fundamental_analysis_report: Financial data (for combined analysis)
```

**Usage:**
```python
from stock_analyzer_bot.tools import bollinger_fibonacci_analysis

result = bollinger_fibonacci_analysis("AAPL", "1y")
# Returns JSON with signal, metrics, and interpretation
```

---

## 🤖 Agent Implementations

### ToolCallingAgent (`main.py`)

Uses HIGH-LEVEL tools for simple, reliable analysis.

```python
from stock_analyzer_bot.main import (
    run_technical_analysis,
    run_market_scanner,
    run_fundamental_analysis,
    run_multi_sector_analysis,
    run_combined_analysis,
)

# Technical Analysis (1 MCP call)
report = run_technical_analysis("AAPL", period="1y")

# Market Scanner (1 MCP call)
report = run_market_scanner("AAPL,MSFT,GOOGL", period="1y")

# Fundamental Analysis (1 MCP call)
report = run_fundamental_analysis("MSFT", period="3y")

# Multi-Sector Analysis (N MCP calls, one per sector)
report = run_multi_sector_analysis(
    sectors={"Banking": "JPM,BAC,WFC", "Tech": "AAPL,MSFT"},
    period="1y"
)

# Combined Analysis (2 MCP calls: fundamental + technical)
report = run_combined_analysis(
    "TSLA",
    technical_period="1y",
    fundamental_period="3y"
)
```

**Characteristics:**
- Simple, predictable behavior
- One tool call = complete result
- Lower token usage
- Best for production environments

### CodeAgent (`main_codeagent.py`)

Uses LOW-LEVEL tools with Python code orchestration.

```python
from stock_analyzer_bot.main_codeagent import (
    run_technical_analysis,
    run_market_scanner,
    run_fundamental_analysis,
    run_multi_sector_analysis,
    run_combined_analysis,
)

# Technical Analysis (4 tool calls with Python loop)
report = run_technical_analysis(
    "AAPL",
    period="1y",
    executor_type="local"  # or "e2b", "docker"
)

# Market Scanner (4 * N tool calls with nested loops)
report = run_market_scanner(
    "AAPL,MSFT,GOOGL",
    period="1y",
    executor_type="local"
)
```

**Characteristics:**
- Writes Python code to call tools
- Uses loops for multi-stock efficiency
- Transparent reasoning (see generated code)
- 2-3x faster for multi-stock analysis
- Requires sandbox for production

---

## 📡 API Endpoints

The `api.py` module exposes all analysis functions via FastAPI.

### Configuration

```python
# Environment variables
DEFAULT_MODEL_ID = os.getenv("SMOLAGENT_MODEL_ID", "gpt-4o")
DEFAULT_MODEL_PROVIDER = os.getenv("SMOLAGENT_MODEL_PROVIDER", "litellm")
DEFAULT_AGENT_TYPE = os.getenv("SMOLAGENT_AGENT_TYPE", "tool_calling")
DEFAULT_TEMPERATURE = float(os.getenv("SMOLAGENT_TEMPERATURE", "0.1"))
DEFAULT_MAX_TOKENS = int(os.getenv("SMOLAGENT_MAX_TOKENS", "8192"))
```

### Endpoints

#### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "version": "2.3.0",
  "features": ["technical_analysis", "market_scanner", "fundamental_analysis", "multisector", "combined"],
  "agent_types": {
    "tool_calling": true,
    "code_agent": true
  },
  "default_agent_type": "tool_calling"
}
```

#### Technical Analysis

```http
POST /technical
Content-Type: application/json

{
  "symbol": "AAPL",
  "period": "1y",
  "agent_type": "tool_calling",
  "model_id": "gpt-4o",
  "max_steps": 25
}
```

**ToolCallingAgent:** Calls `comprehensive_performance_report` (1 MCP call)

**CodeAgent:** Calls 4 individual strategy tools with Python orchestration

#### Market Scanner

```http
POST /scanner
Content-Type: application/json

{
  "symbols": "AAPL,MSFT,GOOGL,META,NVDA",
  "period": "1y",
  "agent_type": "code_agent"
}
```

**ToolCallingAgent:** Calls `unified_market_scanner` (1 MCP call)

**CodeAgent:** Loops through stocks, calling 4 strategies each

#### Fundamental Analysis

```http
POST /fundamental
Content-Type: application/json

{
  "symbol": "MSFT",
  "period": "3y",
  "agent_type": "tool_calling"
}
```

Uses `fundamental_analysis_report` tool with 70+ row aliases for robust data extraction.

#### Multi-Sector Analysis

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

**ToolCallingAgent:** Calls `unified_market_scanner` once per sector

**CodeAgent:** Nested loops (sector → stock → strategy)

**Recommendation:** Use CodeAgent for 3-5x faster execution

#### Combined Analysis

```http
POST /combined
Content-Type: application/json

{
  "symbol": "TSLA",
  "technical_period": "1y",
  "fundamental_period": "3y",
  "agent_type": "tool_calling"
}
```

Combines technical (4 strategies) and fundamental analysis into a unified investment thesis.

### Response Format

All endpoints return:

```json
{
  "report": "# AAPL Comprehensive Technical Analysis\n...",
  "symbol": "AAPL",
  "analysis_type": "technical",
  "duration_seconds": 35.2,
  "agent_type": "tool_calling",
  "tools_approach": "HIGH-LEVEL tools (comprehensive reports in single MCP calls)"
}
```

---

## ⚙️ Configuration

### Agent Configuration

```python
# Model settings
DEFAULT_MODEL_ID = "gpt-4o"           # Recommended for CodeAgent
DEFAULT_MODEL_PROVIDER = "litellm"     # litellm (OpenAI) or inference (HuggingFace)
DEFAULT_TEMPERATURE = 0.1              # Low for deterministic outputs
DEFAULT_MAX_TOKENS = 8192              # Prevent truncation

# Agent settings
DEFAULT_MAX_STEPS = 25                 # Increase for complex analysis
DEFAULT_EXECUTOR = "local"             # local, e2b, or docker
```

### Executor Types (CodeAgent Only)

| Type | Security | Setup | Use Case |
|------|----------|-------|----------|
| `local` | ⚠️ Low | None | Development |
| `e2b` | ✅ High | E2B account | Production |
| `docker` | ✅ High | Docker installed | Self-hosted |

**E2B Setup:**
```bash
pip install 'smolagents[e2b]'
export E2B_API_KEY=your-key
```

**Docker Setup:**
```bash
pip install 'smolagents[docker]'
# Ensure Docker daemon is running
```

---

## 📝 Prompt Templates

All prompts follow strict formatting guidelines for clean output:

### Formatting Rules

1. **Currency:** Use "USD" prefix instead of "$" (avoids LaTeX interpretation)
2. **Tables:** Avoid pipe characters `|` (render poorly in Streamlit)
3. **Structure:** Each data point on its own line
4. **Headers:** Numbered sections with clear hierarchy
5. **No Italics:** Avoid `*text*` formatting

### Technical Analysis Prompt Structure

```
1. EXECUTIVE SUMMARY
   - Overall recommendation (BUY/HOLD/SELL)
   - Confidence level
   - Key metrics

2. STRATEGY ANALYSIS
   - Bollinger-Fibonacci: Signal, metrics, interpretation
   - MACD-Donchian: Signal, metrics, interpretation
   - Connors RSI-ZScore: Signal, metrics, interpretation
   - Dual Moving Average: Signal, metrics, interpretation

3. RISK ASSESSMENT
   - Position sizing guidance
   - Stop loss levels

4. FINAL RECOMMENDATION
   - Actionable conclusion
```

### Market Scanner Prompt Structure

```
1. MARKET OVERVIEW
   - Total stocks analyzed
   - Market conditions

2. RANKED OPPORTUNITIES
   - Stock rankings with scores
   - All 5 strategies per stock:
     * Bollinger Z-Score
     * Bollinger-Fibonacci
     * MACD-Donchian
     * Connors RSI-ZScore
     * Dual Moving Average

3. TOP RECOMMENDATIONS
   - Best opportunities with rationale

4. PORTFOLIO ALLOCATION
   - Suggested allocation percentages
```

---

## 🧪 Usage Examples

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
# Technical with ToolCallingAgent
curl -X POST "http://localhost:8000/technical" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "agent_type": "tool_calling"}'

# Scanner with CodeAgent
curl -X POST "http://localhost:8000/scanner" \
  -H "Content-Type: application/json" \
  -d '{"symbols": "AAPL,MSFT", "agent_type": "code_agent"}'

# Multi-sector with CodeAgent (recommended)
curl -X POST "http://localhost:8000/multisector" \
  -H "Content-Type: application/json" \
  -d '{
    "sectors": [
      {"name": "Banking", "symbols": "JPM,BAC,WFC"},
      {"name": "Tech", "symbols": "AAPL,MSFT,GOOGL"}
    ],
    "agent_type": "code_agent"
  }'
```

---

## 📊 Performance Comparison

### Benchmarks: ToolCallingAgent vs CodeAgent

| Scenario | ToolCallingAgent | CodeAgent (local) | Improvement |
|----------|-----------------|-------------------|-------------|
| Single stock (4 strategies) | ~45s | ~40s | 10% |
| 3-stock comparison | ~180s | ~90s | 50% |
| 5-stock comparison | ~300s | ~100s | 66% |
| Multi-sector (3 sectors) | ~600s | ~200s | 66% |

**Conclusions:**
- ✅ CodeAgent is 2-3x faster for multi-stock analysis (uses loops)
- ✅ ToolCallingAgent is more stable for simple analysis
- ⚠️ CodeAgent requires sandbox (e2b/docker) in production

---

## 🛠️ Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "CodeAgent not available" | `main_codeagent.py` missing | Ensure file exists in `stock_analyzer_bot/` |
| "MCP server not found" | Server path incorrect | Check `server/main.py` exists at project root |
| "Connection refused" | FastAPI not running | Start with `uvicorn stock_analyzer_bot.api:app --port 8000` |
| "Code execution failed" | Invalid Python from LLM | Try different model (gpt-4o recommended) |
| "Timeout" | Too many stocks | Reduce count or use CodeAgent |
| "Authentication error" | Invalid API key | Check `OPENAI_API_KEY` environment variable |
| "Import not allowed" | CodeAgent sandbox | Add to `additional_authorized_imports` |
| "Truncated output" | Token limit exceeded | Increase `max_tokens` to 8192+ |
| "LaTeX formatting" | Dollar signs in output | Code uses USD prefix instead of $ |

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

**Test MCP connection:**
```python
from stock_analyzer_bot.tools import configure_finance_tools
from stock_analyzer_bot.mcp_client import get_session

configure_finance_tools()
session = get_session()
print(f"Session active: {session is not None}")
```

---

## 📚 Related Documentation

- [Root README](../README.md) - Project overview
- [Server README](../server/README.md) - MCP tools reference
- [Smolagents Docs](https://huggingface.co/docs/smolagents/index) - Official documentation
- [Secure Code Execution](https://huggingface.co/docs/smolagents/tutorials/secure_code_execution) - CodeAgent security

---

## 🔄 Recent Changes

### v2.3.0 - Output Formatting & Stability

- **Temperature Configuration:** Set to 0.1 for more deterministic outputs
- **Currency Formatting:** Changed from "$" to "USD" prefix to avoid LaTeX interpretation
- **Token Limits:** Increased default to 8192 to prevent truncation
- **Market Scanner:** Fixed missing MACD-Donchian and Connors RSI-ZScore strategies
- **Template Escaping:** Fixed Python format conflicts in prompt templates
- **Response Formatting:** Added `format_agent_result()` helper for clean output

### v2.2.0 - Fundamental Analysis Improvements

- **Row Aliases:** Expanded to 70+ aliases for robust yfinance data extraction
- **Multi-tier Matching:** Exact → Alias → Fuzzy substring matching
- **Financial Ratios:** Added comprehensive ratio calculations across 4 categories
- **Fallback Handling:** Graceful degradation when data extraction fails

### v2.1.0 - Dual Agent Architecture

- **CodeAgent:** Added Python code execution for efficient multi-stock loops
- **Executor Options:** Support for local, e2b, and docker sandboxes
- **Tool Categories:** Separated HIGH-LEVEL and LOW-LEVEL tool collections
- **Agent Selection:** API parameter to choose agent type per request

---

<p align="center">
  <i>Stock Analyzer Bot v2.3.0 - Dual agent support with ToolCallingAgent & CodeAgent</i>
</p>