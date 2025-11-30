# Financial Analysis MCP Server

A comprehensive Model Context Protocol (MCP) server providing advanced technical and fundamental analysis tools for financial markets. This server integrates with Claude Desktop, smolagents, and other MCP clients to deliver sophisticated trading strategy analysis, performance backtesting, and market scanning capabilities.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Available Tools](#available-tools)
  - [Strategy Analysis Tools](#strategy-analysis-tools)
  - [Performance Backtesting Tools](#performance-backtesting-tools)
  - [Market Scanning Tools](#market-scanning-tools)
  - [Fundamental Analysis Tools](#fundamental-analysis-tools)
- [Tool Reference](#tool-reference)
- [Utility Functions](#utility-functions)
- [Usage Examples](#usage-examples)
- [Integration Guide](#integration-guide)

---

## Overview

The MCP Finance Server implements **five distinct technical analysis strategies** plus **fundamental analysis** with comprehensive performance backtesting capabilities. Built on the FastMCP framework, it provides a standardized interface for AI assistants and automation tools to access sophisticated financial analysis.

### Key Features

| Feature | Description |
|---------|-------------|
| **5 Technical Strategies** | Bollinger-Fibonacci, MACD-Donchian, Connors RSI, Dual MA, Bollinger Z-Score |
| **Fundamental Analysis** | Income statement, balance sheet, cash flow analysis |
| **Performance Backtesting** | Compare strategy returns vs buy-and-hold with detailed metrics |
| **Market Scanner** | Analyze multiple stocks simultaneously with rankings |
| **Risk Assessment** | Volatility, Sharpe ratios, maximum drawdown calculations |
| **Signal Generation** | Real-time BUY/HOLD/SELL recommendations with confidence scores |

---

## Architecture

```
server/
├── main.py                          # MCP server entry point
├── strategies/                      # Trading strategy modules
│   ├── __init__.py
│   ├── bollinger_fibonacci.py       # Bollinger Bands + Fibonacci Retracement
│   ├── bollinger_zscore.py          # Bollinger Bands + Z-Score Mean Reversion
│   ├── macd_donchian.py             # MACD + Donchian Channel Breakout
│   ├── connors_zscore.py            # Connors RSI + Z-Score Combined
│   ├── dual_moving_average.py       # EMA/SMA Crossover Strategy
│   ├── fundamental_analysis.py      # Financial Statement Analysis
│   ├── performance_tools.py         # Backtesting & Performance Comparison
│   ├── comprehensive_analysis.py    # Multi-Strategy Reports
│   └── unified_market_scanner.py    # Multi-Stock Market Scanner
└── utils/
    ├── __init__.py
    └── yahoo_finance_tools.py       # Data fetching & indicator calculations
```

### Data Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   MCP Client    │────▶│   MCP Server    │────▶│  Yahoo Finance  │
│ (Claude/Agent)  │◀────│   (FastMCP)     │◀────│      API        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Strategy Modules   │
                    │  - Calculations     │
                    │  - Backtesting      │
                    │  - Signal Gen       │
                    └─────────────────────┘
```

---

## Installation

### Prerequisites

- Python 3.10+
- Internet connection (Yahoo Finance data access)

### Dependencies

```bash
pip install mcp fastmcp yfinance pandas numpy scipy
```

### Quick Start

```bash
# Run the server directly
python server/main.py

# Or with UV package manager
uv run python server/main.py
```

---

## Configuration

### Claude Desktop Integration

Add to `claude_desktop_config.json`:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "finance-tools": {
      "command": "python",
      "args": ["/path/to/server/main.py"]
    }
  }
}
```

### VS Code MCP Extension

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "finance-tools": {
      "command": "python",
      "args": ["D:\\path\\to\\server\\main.py"]
    }
  }
}
```

---

## Available Tools

### Strategy Analysis Tools

These tools calculate real-time scores and signals based on current market data.

| Tool | Strategy | Signal Range | Use Case |
|------|----------|--------------|----------|
| `calculate_bollinger_fibonacci_score` | Bollinger + Fibonacci | -100 to +100 | Support/Resistance |
| `calculate_bollinger_z_score` | Bollinger + Z-Score | -100 to +100 | Mean Reversion |
| `calculate_combined_score_macd_donchian` | MACD + Donchian | -100 to +100 | Momentum/Breakout |
| `calculate_connors_rsi_score_tool` | Connors RSI | 0 to 100 | Short-term Momentum |
| `calculate_combined_connors_zscore_tool` | Connors + Z-Score | -100 to +100 | Combined Momentum |
| `analyze_dual_ma_strategy` | Dual Moving Average | BUY/HOLD/SELL | Trend Following |

### Performance Backtesting Tools

These tools run historical backtests and compare strategy performance vs buy-and-hold.

| Tool | Description | Key Metrics |
|------|-------------|-------------|
| `analyze_bollinger_fibonacci_performance` | Backtest BB-Fib strategy | Return %, Sharpe, Max DD |
| `analyze_bollinger_zscore_performance` | Backtest BB-ZScore strategy | Return %, Win Rate |
| `analyze_macd_donchian_performance` | Backtest MACD-Donchian | Excess Return, Trades |
| `analyze_connors_zscore_performance` | Backtest Connors-ZScore | Strategy vs B&H |
| `analyze_dual_ma_strategy` | Backtest Dual MA | Golden/Death Cross stats |

### Market Scanning Tools

| Tool | Description | Output Formats |
|------|-------------|----------------|
| `market_scanner` | Unified multi-stock scanner | detailed, summary, executive |
| `generate_comprehensive_analysis_report` | Single stock, all strategies | Full markdown report |

### Fundamental Analysis Tools

| Tool | Description | Data Source |
|------|-------------|-------------|
| `fundamental_analysis` | Complete financial analysis | yfinance financials |
| `get_financial_statement_index` | List available metrics | Income, Balance, Cash Flow |

---

## Tool Reference

### 1. Bollinger Bands + Fibonacci Retracement

**Tool:** `calculate_bollinger_fibonacci_score`

**Strategy Logic:**
- Combines Bollinger Bands (volatility) with Fibonacci retracement levels (support/resistance)
- Identifies potential reversal points where price meets both BB and Fib levels

**Score Components (weighted):**
| Component | Weight | Description |
|-----------|--------|-------------|
| Bollinger Band Position | 30% | %B indicator (0-1 range) |
| Volatility Assessment | 15% | BB width and expansion |
| Fibonacci Interaction | 35% | Proximity to key Fib levels |
| Price Momentum | 20% | RSI-like momentum indicator |

**Signal Zones:**
```
+60 to +100: Strong Buy
+20 to +60:  Moderate Buy
-20 to +20:  Hold
-60 to -20:  Moderate Sell
-100 to -60: Strong Sell
```

**Parameters:**
```python
calculate_bollinger_fibonacci_score(
    ticker: str,           # Stock symbol (e.g., "AAPL")
    period: str = "1y",    # Data period: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
    window: int = 20,      # Bollinger Band period
    num_std: int = 2,      # Standard deviations for bands
    window_swing_points: int = 10,  # Swing point detection window
    fibonacci_levels: List = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
)
```

---

### 2. MACD + Donchian Channel

**Tool:** `calculate_combined_score_macd_donchian`

**Strategy Logic:**
- MACD identifies momentum and trend direction
- Donchian Channels identify breakouts and range boundaries
- Combined for momentum-confirmed breakout signals

**Score Components:**
| Component | Weight | Description |
|-----------|--------|-------------|
| MACD Line vs Signal | 40% | Crossover momentum |
| MACD vs Zero Line | 30% | Trend direction |
| MACD Histogram | 30% | Momentum acceleration |
| Donchian Position | 50% | Channel breakout detection |

**Parameters:**
```python
calculate_combined_score_macd_donchian(
    symbol: str,
    period: str = "1y",
    fast_period: int = 12,    # MACD fast EMA
    slow_period: int = 26,    # MACD slow EMA
    signal_period: int = 9,   # MACD signal line
    window: int = 20          # Donchian channel period
)
```

---

### 3. Connors RSI + Z-Score

**Tool:** `calculate_combined_connors_zscore_tool`

**Strategy Logic:**
- Connors RSI: Short-term mean reversion indicator
- Z-Score: Statistical deviation from mean
- Combined for high-probability reversal signals

**Connors RSI Components:**
| Component | Weight | Description |
|-----------|--------|-------------|
| Price RSI | 33.3% | Traditional RSI of closes |
| Streak RSI | 33.3% | RSI of up/down streaks |
| Percent Rank | 33.3% | Percentile of rate of change |

**Combined Score Weights:**
- Connors RSI: 70%
- Z-Score: 30%

**Signal Interpretation:**
```
CRSI < 20: Oversold (Potential Buy)
CRSI > 80: Overbought (Potential Sell)
Z-Score < -2: Extremely Oversold
Z-Score > +2: Extremely Overbought
```

**Parameters:**
```python
calculate_combined_connors_zscore_tool(
    symbol: str,
    period: str = "1y",
    rsi_period: int = 3,      # Connors RSI period
    streak_period: int = 2,   # Streak RSI period
    rank_period: int = 100,   # Percent rank lookback
    zscore_window: int = 20,  # Z-Score calculation window
    connors_weight: float = 0.7,
    zscore_weight: float = 0.3
)
```

---

### 4. Dual Moving Average Crossover

**Tool:** `analyze_dual_ma_strategy`

**Strategy Logic:**
- Classic trend-following strategy
- Golden Cross (50 > 200): Bullish signal
- Death Cross (50 < 200): Bearish signal

**Signal Generation:**
```
BUY:  Short MA crosses ABOVE Long MA
SELL: Short MA crosses BELOW Long MA
HOLD: No recent crossover
```

**Parameters:**
```python
analyze_dual_ma_strategy(
    symbol: str,
    period: str = "2y",
    short_period: int = 50,   # Short MA period (days)
    long_period: int = 200,   # Long MA period (days)
    ma_type: str = "EMA"      # "SMA" or "EMA"
)
```

**Output Metrics:**
- Total Return vs Buy & Hold
- Excess Return
- Win Rate
- Total Trades (crossovers)
- Sharpe Ratio
- Maximum Drawdown

---

### 5. Bollinger Z-Score (Mean Reversion)

**Tool:** `calculate_bollinger_z_score`

**Strategy Logic:**
- Pure statistical mean reversion
- Z-Score measures standard deviations from moving average
- Buy when oversold (low Z), sell when overbought (high Z)

**Signal Zones:**
```
Z < -2.0: Strong Buy (oversold)
Z < -1.0: Buy
-1 < Z < 1: Hold
Z > 1.0: Sell
Z > 2.0: Strong Sell (overbought)
```

**Parameters:**
```python
calculate_bollinger_z_score(
    symbol: str,
    period: str = "1y",
    window: int = 20    # Z-Score calculation window
)
```

---

### 6. Market Scanner

**Tool:** `market_scanner`

**Description:**
Analyzes multiple stocks simultaneously using all 5 strategies, ranks them by performance and signal strength, and provides structured recommendations.

**Parameters:**
```python
market_scanner(
    symbols: str,              # Comma-separated: "AAPL,MSFT,GOOGL"
    period: str = "1y",
    output_format: str = "detailed"  # "detailed", "summary", "executive"
)
```

**Output Includes:**
- Executive Summary with market insights
- Individual stock analysis with all strategies
- Performance comparison vs buy-and-hold
- Signal consensus and strength
- Risk assessment
- Ranked recommendations

---

### 7. Fundamental Analysis

**Tool:** `fundamental_analysis`

**Description:**
Analyzes company financial statements including income statement, balance sheet, and cash flow statement.

**Parameters:**
```python
fundamental_analysis(
    symbol: str,
    period: str = "3y"    # Years of financial data
)
```

**Metrics Analyzed:**
| Category | Metrics |
|----------|---------|
| **Profitability** | Revenue, Net Income, Margins, ROE, ROA |
| **Growth** | Revenue Growth, Earnings Growth |
| **Liquidity** | Current Ratio, Quick Ratio |
| **Leverage** | Debt-to-Equity, Interest Coverage |
| **Cash Flow** | Operating CF, Free Cash Flow, CapEx |
| **Valuation** | P/E, P/B, P/S (when available) |

---

## Utility Functions

Located in `utils/yahoo_finance_tools.py`:

### Data Fetching

```python
fetch_data(ticker: str, period: str) -> pd.DataFrame
```

### Technical Indicators

```python
# Bollinger Bands
calculate_bollinger_bands(data, ticker, period, window, num_std) -> pd.DataFrame

# Fibonacci Levels
find_swing_points(data, window) -> pd.DataFrame
calculate_fibonacci_levels(swing_high, swing_low, levels) -> Dict

# RSI Calculations
rsi(series, period) -> pd.Series
streak_rsi(series, period) -> pd.Series
percent_rank(series, period) -> pd.Series

# Connors RSI
calculate_connors_rsi_score(symbol, period, rsi_period, streak_period, rank_period) -> Tuple

# Z-Score
calculate_zscore_indicator(symbol, period, window) -> Tuple

# MACD
calculate_macd_score(symbol, period, fast, slow, signal) -> float

# Donchian Channels
calculate_donchian_channel_score(symbol, period, window) -> float
```

---

## Usage Examples

### Claude Desktop Prompts

**Single Stock Analysis:**
```
Analyze TSLA using the Bollinger-Fibonacci strategy with a 1-year period
```

**Multi-Stock Comparison:**
```
Use market scanner with symbols "AAPL, MSFT, GOOGL, META, NVDA" 
with period "1y" and output_format "detailed"
```

**Sector Analysis:**
```
Scan these bank stocks: JPM, BAC, WFC, C, GS, MS, USB, PNC, TFC, COF
```

**Comprehensive Analysis:**
```
For AAPL:
- Run analyze_bollinger_fibonacci_performance with 1 year period
- Run analyze_macd_donchian_performance with 1 year period
- Run analyze_connors_zscore_performance with default parameters
- Run analyze_dual_ma_strategy with 50/200 EMA
- Compile results into a comprehensive report
```

### Python Direct Usage

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def analyze_stock():
    server_params = StdioServerParameters(
        command="python",
        args=["server/main.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Call a tool
            result = await session.call_tool(
                "analyze_bollinger_fibonacci_performance",
                {"symbol": "AAPL", "period": "1y", "window": 20}
            )
            print(result.content[0].text)
```

---

## Integration Guide

### With smolagents (stock_analyzer_bot)

The server is designed to work with the `stock_analyzer_bot` which uses smolagents:

```python
from stock_analyzer_bot.tools import (
    bollinger_fibonacci_analysis,
    macd_donchian_analysis,
    connors_zscore_analysis,
    dual_moving_average_analysis,
)

# These tools internally call the MCP server
result = bollinger_fibonacci_analysis("AAPL", "1y")
```

### With FastAPI Backend

The `stock_analyzer_bot/api.py` exposes these tools via REST:

```bash
# Start the API server
uvicorn stock_analyzer_bot.api:app --reload --port 8000

# Available endpoints:
# POST /technical - Single stock technical analysis
# POST /scanner - Multi-stock market scanner
# POST /fundamental - Fundamental analysis
# POST /multisector - Cross-sector analysis
# POST /combined - Technical + Fundamental combined
```

### With Streamlit Frontend

```bash
streamlit run streamlit_app.py
```

Provides a web UI for all analysis types.

---

## Performance Metrics Glossary

| Metric | Description | Good Value |
|--------|-------------|------------|
| **Total Return** | Strategy cumulative return | > Buy & Hold |
| **Excess Return** | Return above buy-and-hold | > 0% |
| **Sharpe Ratio** | Risk-adjusted return | > 1.0 |
| **Max Drawdown** | Largest peak-to-trough decline | > -20% |
| **Win Rate** | Percentage of profitable trades | > 50% |
| **Volatility** | Annualized standard deviation | Lower = less risk |

---

## Error Handling

The server handles common errors gracefully:

- **Invalid Symbol**: Returns error message with suggestion
- **No Data**: Handles missing Yahoo Finance data
- **Calculation Errors**: Returns partial results where possible
- **Network Issues**: Timeout handling for API calls

---

## Version History

| Version | Changes |
|---------|---------|
| 1.0.0 | Initial release with 5 technical strategies |
| 1.1.0 | Added unified market scanner |
| 1.2.0 | Added fundamental analysis tools |
| 1.3.0 | Performance optimizations, better error handling |

---

## License

This server is provided for educational and research purposes. Always verify analysis results and consult financial professionals before making investment decisions.

---

*Built with [FastMCP](https://github.com/anthropics/anthropic-cookbook/tree/main/misc/mcp) and [yfinance](https://github.com/ranaroussi/yfinance)*