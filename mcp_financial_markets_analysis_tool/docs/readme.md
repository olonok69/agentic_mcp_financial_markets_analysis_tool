# Financial Analysis MCP Server

A comprehensive Model Context Protocol (MCP) server that provides advanced technical analysis tools for financial markets. This server integrates with Claude Desktop to deliver sophisticated trading strategy analysis, performance backtesting, and market scanning capabilities.

## 🚀 Features

### Core Trading Strategies
- **Bollinger Z-Score Analysis** - Mean reversion strategy using statistical Z-scores
- **Bollinger-Fibonacci Strategy** - Support/resistance analysis combining Bollinger Bands with Fibonacci retracements
- **MACD-Donchian Combined** - Momentum and breakout strategy using MACD and Donchian channels
- **Connors RSI + Z-Score** - Short-term momentum with mean reversion analysis
- **Dual Moving Average** - Trend-following strategy with EMA crossovers

### Analysis Capabilities
- **Performance Backtesting** - Compare strategy returns vs buy-and-hold
- **Market Scanner** - Analyze multiple stocks simultaneously
- **Risk Assessment** - Volatility, Sharpe ratios, and drawdown analysis
- **Signal Generation** - Real-time buy/sell/hold recommendations
- **Comprehensive Reporting** - Detailed markdown reports with reasoning

### Market Coverage
- Individual stock analysis
- Multi-stock portfolio scanning
- Sector-specific analysis (Banking, Technology, Clean Energy/EV)
- Performance ranking and comparison

## 📋 Prerequisites

- **Python 3.11+** with `uv` package manager
- **Claude Desktop** with MCP support
- **Anthropic API Key** (for Claude integration)
- **Internet connection** (for real-time market data via Yahoo Finance)

## 🛠️ Installation

### 1. Clone and Setup Project
```bash
# Create project directory
mkdir financial-mcp-server
cd financial-mcp-server

# Initialize with uv
uv init .

# Install core dependencies
uv add mcp fastmcp yfinance pandas numpy anthropic python-dotenv

# Install additional analysis dependencies
uv add python-docx docx2pdf scipy scikit-learn
```

### 2. Project Structure
```
financial-mcp-server/
├── server/
│   ├── main.py                     # Main MCP server entry point
│   ├── strategies/                 # Trading strategy modules
│   │   ├── __init__.py
│   │   ├── bollinger_zscore.py     # Z-Score mean reversion
│   │   ├── bollinger_fibonacci.py  # Bollinger-Fibonacci strategy
│   │   ├── macd_donchian.py       # MACD-Donchian momentum
│   │   ├── connors_zscore.py      # Connors RSI analysis
│   │   ├── dual_moving_average.py # EMA crossover strategy
│   │   ├── performance_tools.py   # Performance comparison tools
│   │   ├── comprehensive_analysis.py # Multi-strategy analysis
│   │   └── unified_market_scanner.py # Market scanning tools
│   └── utils/
│       ├── __init__.py
│       └── yahoo_finance_tools.py  # Market data utilities
├── .env                           # Environment variables
├── .gitignore                     # Git ignore file
└── README.md                      # This file
```

### 3. Environment Configuration
Create a `.env` file:
```bash
# Not required for this server, but useful for extensions
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

Create `.gitignore`:
```gitignore
# Python-generated files
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info

# Virtual environments
.venv
.env
.lock
```

### 4. Claude Desktop Configuration

Add to your Claude Desktop MCP configuration file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "financial-analysis": {
      "command": "uv",
      "args": ["run", "python", "server/main.py"],
      "cwd": "/path/to/your/financial-mcp-server"
    }
  }
}
```

## 🎯 Usage Examples

### Individual Stock Analysis

```
Analyze TSLA using all 5 technical strategies with performance comparison over 1 year period
```

### Market Scanning

```
Use market scanner with symbols "AAPL, MSFT, GOOGL, META, NVDA" with period "1y" and output_format "detailed"
```

### Sector Analysis

```
Scan these bank stocks: JPM, BAC, WFC, C, GS, MS, USB, PNC, TFC, COF
```

### Strategy-Specific Analysis

```
For Tesla:
- Calculate Bollinger Z-Score with 20-day period
- Analyze MACD-Donchian strategy with 1-year period
- Compare dual moving average performance using EMA 50/200
```

## 📊 Available Tools

### Core Analysis Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `calculate_bollinger_z_score` | Z-Score mean reversion analysis | `symbol`, `period` |
| `calculate_bollinger_fibonacci_score` | Bollinger-Fibonacci strategy | `symbol`, `period`, `window` |
| `calculate_combined_score_macd_donchian` | MACD-Donchian momentum | `symbol`, `period`, `window` |
| `calculate_combined_connors_zscore_tool` | Connors RSI + Z-Score | `symbol`, `period`, `weights` |
| `analyze_dual_ma_strategy` | Moving average crossovers | `symbol`, `period`, `ma_type` |

### Performance Analysis Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `analyze_bollinger_zscore_performance` | Backtest Z-Score strategy | `symbol`, `period`, `window` |
| `analyze_bollinger_fibonacci_performance` | Backtest Bollinger-Fibonacci | `symbol`, `period`, `window` |
| `analyze_macd_donchian_performance` | Backtest MACD-Donchian | `symbol`, `period`, `fast/slow` |
| `analyze_connors_zscore_performance` | Backtest Connors RSI strategy | `symbol`, `period`, `weights` |

### Market Scanning Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `market_scanner` | Unified market analysis | `symbols`, `period`, `output_format` |
| `comprehensive_strategy_analysis` | Multi-strategy comparison | `symbol`, `period` |

## 📈 Sample Reports

### Individual Stock Analysis
The server generates comprehensive reports like this [Tesla analysis example](reports_Example/tesla_technical_analysis.md):

- **Executive Summary** with overall recommendation
- **Individual Strategy Analysis** with scores and signals
- **Performance Comparison** vs buy-and-hold
- **Current Signal Status** with confidence levels
- **Risk Assessment** and position sizing

### Sector Analysis
Detailed sector reports like this [Banking Sector analysis](reports_Example/banking_sector_comprehensive_analysis.md):

- **Performance Summary Table** with all stocks
- **Strategy Effectiveness Rankings**
- **Individual Stock Breakdowns**
- **Risk Management Framework**
- **Final Investment Recommendations**

### Multi-Sector Analysis
Comprehensive market reports like this [Multi-Sector analysis](reports_Example/multi_sector_analysis_report.md):

- **Cross-Sector Performance Overview**
- **Priority Investment Recommendations**
- **Portfolio Construction Framework**
- **Market Outlook & Strategic Themes**

## 🔧 Technical Architecture

### MCP Integration
This server uses the **FastMCP** framework for seamless integration with Claude Desktop:

```python
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("finance tools", "1.0.0")

# Register strategy tools
register_bollinger_fibonacci_tools(mcp)
register_macd_donchian_tools(mcp)
# ... other strategies

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

### Strategy Implementation
Each strategy follows a consistent pattern:

1. **Data Acquisition** - Yahoo Finance API integration
2. **Indicator Calculation** - Technical analysis computations
3. **Signal Generation** - Buy/sell/hold recommendations
4. **Performance Backtesting** - Historical strategy validation
5. **Report Generation** - Structured markdown output

### Performance Calculation
The server implements comprehensive performance metrics:

```python
def calculate_strategy_performance_metrics(signals_data, signal_column):
    # Calculate returns, volatility, Sharpe ratios
    # Generate win rates and drawdown analysis
    # Compare vs buy-and-hold baseline
    return performance_metrics
```

## ⚙️ Configuration Options

### Time Periods
- **Valid periods:** `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max`

### Strategy Parameters
- **Bollinger Bands:** Window (default: 20), Standard deviations (default: 2)
- **MACD:** Fast period (12), Slow period (26), Signal period (9)
- **Moving Averages:** Short period (50), Long period (200), Type (SMA/EMA)
- **Z-Score:** Window for mean/std calculation (default: 20)

### Output Formats
- **detailed:** Full analysis with all metrics
- **summary:** Condensed overview with key findings
- **executive:** High-level summary for decision makers

## 🚨 Risk Disclaimers

⚠️ **Important:** This tool is for educational and informational purposes only.

- **Not Financial Advice:** All analysis should be verified independently
- **Past Performance:** Does not guarantee future results
- **Market Risk:** All trading involves substantial risk of loss
- **Strategy Limitations:** Technical analysis has inherent limitations
- **Data Accuracy:** Market data is provided by Yahoo Finance

## 🔍 Troubleshooting

### Common Issues

**Connection Problems:**
- Verify server script paths in Claude Desktop config
- Check that Python/uv environments are properly configured
- Ensure all dependencies are installed

**Performance Issues:**
- First responses may take 30+ seconds (normal for data download)
- Subsequent responses are typically faster
- Consider using shorter time periods for faster analysis

**Data Issues:**
- Verify ticker symbols are correct and actively traded
- Check internet connectivity for Yahoo Finance access
- Some tools require minimum data periods (e.g., 200-day MA needs 200+ days)

### Debug Mode
Enable detailed logging by modifying the server:

```python
import sys
print(f"Analyzing {symbol}...", file=sys.stderr)
```

## 🤝 Contributing

### Adding New Strategies
1. Create new strategy module in `server/strategies/`
2. Implement core analysis function
3. Add performance backtesting capability
4. Register with main MCP server
5. Add comprehensive documentation

### Extending Analysis
- Add new technical indicators
- Implement additional risk metrics
- Create sector-specific analysis tools
- Enhance reporting formats

## 📚 Additional Resources

### Model Context Protocol (MCP)
- [Official MCP Documentation](https://modelcontextprotocol.io/)
- [MCP Concepts and Architecture](https://modelcontextprotocol.io/docs/concepts/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)

### Technical Analysis Resources
- **Bollinger Bands:** Statistical price channels for volatility analysis
- **MACD:** Moving Average Convergence Divergence for momentum
- **Fibonacci Retracements:** Support/resistance based on mathematical ratios
- **Connors RSI:** Short-term mean reversion indicator
- **Donchian Channels:** Breakout analysis using price ranges

### Market Data
- **Yahoo Finance:** Free historical and real-time market data
- **Data Coverage:** Global stocks, indices, currencies, commodities
- **API Limitations:** Rate limits and data availability constraints

## 📄 License

This project is provided for educational purposes. Please review and comply with:
- Yahoo Finance Terms of Service for market data usage
- Anthropic Terms of Service for Claude API usage
- Local regulations regarding financial analysis tools

---

**Built with:** Python, FastMCP, Yahoo Finance API, Claude Desktop
**Author:** Financial Analysis MCP Server
**Version:** 1.0.0