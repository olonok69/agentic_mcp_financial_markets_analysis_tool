# AI-Powered Stock Technical Analysis Command Line Tool

A comprehensive command-line application for performing technical analysis on stock symbols using OpenAI and multiple trading strategies through MCP (Model Context Protocol).

## Features

- **🤖 OpenAI Integration**: Uses OpenAI models to orchestrate and interpret analysis
- **🔧 MCP Finance Tools**: Connects to our custom MCP server with 5 advanced trading strategies
- **📊 Intelligent Analysis**: AI-powered insights and pattern recognition
- **📝 Enhanced Reports**: AI-generated summaries and recommendations

### Trading Strategies Available:
- **Bollinger Z-Score** (Mean Reversion)
- **Bollinger-Fibonacci** (Volatility + Retracement)  
- **MACD-Donchian** (Momentum + Breakout)
- **Connors RSI + Z-Score** (Advanced Mean Reversion)
- **Dual Moving Average** (Trend Following)

## Prerequisites

### Required Environment Variables
1. **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/)
2. **OpenAI Model**: Recommended `gpt-4` (default)

### Required Services
- Internet connection for stock data (Yahoo Finance)
- MCP finance tools server (included in project)

## Installation

1. **Clone the repository** (if not already done)

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

4. **Configure your .env file**:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4
   ```

## Usage

### Basic Usage

```bash
# Analyze Apple stock with AI
python stock_analyzer.py AAPL

# Analyze Microsoft stock with verbose output
python stock_analyzer.py MSFT --verbose

# Analyze Tesla stock
python stock_analyzer.py TSLA
```

### Alternative CLI

```bash
# Using the simple wrapper
python analyze.py AAPL
```

### Command Line Options

- `symbol`: Yahoo Finance stock symbol (required)
- `--verbose, -v`: Enable verbose logging
- `--help, -h`: Show help message

## How It Works

### AI-Powered Analysis Flow

1. **Symbol Validation**: Validates stock symbol with Yahoo Finance
2. **OpenAI Orchestration**: AI model plans the analysis strategy
3. **Tool Execution**: OpenAI calls MCP finance tools with optimal parameters
4. **Results Integration**: AI synthesizes results from all strategies
5. **Report Generation**: Creates comprehensive markdown report with AI insights

### Architecture

```
CLI App → OpenAI API → MCP Client → Finance Tools Server → Yahoo Finance
    ↓
AI-Enhanced Markdown Report
```

## Output

The tool generates AI-enhanced markdown reports saved to the `analysis/` directory with the filename format:
```
Technical_analysis_{SYMBOL}_{TIMESTAMP}.md
```

Example: `Technical_analysis_AAPL_20240808_143022.md`

### Sample Output
```bash
$ python stock_analyzer.py AAPL

🤖 Starting AI-powered technical analysis for AAPL...
Using OpenAI with MCP finance tools...
This may take a few moments...

✅ AI-powered analysis completed successfully!
📊 Report saved to: analysis/Technical_analysis_AAPL_20240808_143022.md
📈 Strategies analyzed: 5
🤖 Analysis enhanced with OpenAI insights
```

## Analysis Parameters

The AI automatically uses optimized parameters for each strategy:

| Strategy | AI-Optimized Parameters |
|----------|------------------------|
| **Bollinger Z-Score** | Period: 1 year, Window: 20 days |
| **Bollinger-Fibonacci** | Period: 1 year, Window: 20 days, Std Dev: 2 |
| **MACD-Donchian** | Period: 1 year, MACD: 12/26/9, Donchian: 20 days |
| **Connors RSI + Z-Score** | Period: 1 year, RSI: 3/2/100, Z-Score: 20 days |
| **Dual Moving Average** | Period: 1 year, EMA: 50/200 days |

## Report Structure

Each AI-generated report includes:

1. **Executive Summary**: AI-powered overview and current price
2. **AI Analysis Summary**: OpenAI's interpretation of the technical indicators
3. **Strategy Analysis Results**: Detailed results from each MCP tool
4. **Performance Summary Table**: Key metrics comparison
5. **Final Recommendation**: AI-enhanced analysis with risk considerations

## Examples

### Successful Analysis
```bash
$ python stock_analyzer.py AAPL

🤖 Starting AI-powered technical analysis for AAPL...
Using OpenAI with MCP finance tools...
This may take a few moments...

✅ AI-powered analysis completed successfully!
📊 Report saved to: analysis/Technical_analysis_AAPL_20240808_143022.md
📈 Strategies analyzed: 5
🤖 Analysis enhanced with OpenAI insights
```

### Error Handling
```bash
$ python stock_analyzer.py INVALID

ERROR - Invalid or non-existent symbol: INVALID

$ python stock_analyzer.py AAPL
❌ Error: OpenAI API key not found
Please set the OPENAI_API_KEY environment variable in your .env file
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m performance    # Performance tests only

# Run with coverage
pytest --cov=stock_analyzer --cov-report=html
```

## Troubleshooting

### Common Issues

1. **"OpenAI API key not found"**
   ```bash
   # Add to your .env file:
   OPENAI_API_KEY=your_api_key_here
   ```

2. **"MCP library not found"**
   ```bash
   pip install mcp
   ```

3. **"yfinance library not found"**
   ```bash
   pip install yfinance
   ```

4. **"Failed to connect to MCP server"**
   - Ensure the server path is correct
   - Check that `server/main.py` exists and is executable
   - Verify Python can run the MCP server

5. **"OpenAI API quota exceeded"**
   - Check your OpenAI API usage limits
   - Consider using a different model (gpt-3.5-turbo)

6. **"No data found for symbol"**
   - Verify the symbol is valid on Yahoo Finance
   - Check your internet connection
   - Some symbols may not have sufficient historical data

### Debug Mode

Enable verbose logging for troubleshooting:
```bash
python stock_analyzer.py AAPL --verbose
```

### Environment Variables

Required in your `.env` file:
```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4  # Optional, defaults to gpt-4
```

## Security

- **API Keys**: Stored securely in `.env` file (not in version control)
- **No sensitive data** in reports or logs
- **Environment variable** protection for OpenAI credentials
- **Secure API communication** with OpenAI and Yahoo Finance

## Performance

- **Analysis time**: 1-3 minutes per symbol (depending on OpenAI response time)
- **Memory usage**: < 100MB for standard analysis
- **AI-enhanced insights**: Intelligent pattern recognition and correlation analysis
- **Token usage**: Optimized prompts to minimize OpenAI API costs

## API Costs

Estimated OpenAI API costs per analysis:
- **GPT-4**: ~$0.10-0.30 per analysis
- **GPT-3.5-Turbo**: ~$0.01-0.05 per analysis

*Costs depend on analysis complexity and current OpenAI pricing*

## Limitations

- Requires OpenAI API key and credits
- Analysis limited to Yahoo Finance supported symbols
- Internet connection required for both stock data and AI analysis
- MCP server must be running for tool execution
- API rate limits may affect analysis speed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation for AI-related changes
6. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Run with `--verbose` flag for detailed logs
3. Verify OpenAI API key and credits
4. Check MCP server connectivity
5. Review test results with `pytest`
