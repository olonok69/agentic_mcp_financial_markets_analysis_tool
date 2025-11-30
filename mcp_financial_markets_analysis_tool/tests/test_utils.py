"""
Utility tests and mock data generators for testing
"""

import pytest
from unittest.mock import Mock, MagicMock
import pandas as pd
from datetime import datetime, timedelta
import random


class MockYFinanceData:
    """Generate mock yfinance data for testing"""
    
    @staticmethod
    def generate_price_data(symbol: str, days: int = 252, start_price: float = 100.0):
        """Generate realistic mock price data"""
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=days),
            end=datetime.now(),
            freq='D'
        )
        
        prices = []
        current_price = start_price
        
        for _ in range(len(dates)):
            # Simple random walk with slight upward bias
            change_percent = random.gauss(0.001, 0.02)  # 0.1% daily average, 2% volatility
            current_price *= (1 + change_percent)
            prices.append(current_price)
        
        # Generate OHLC data
        data = []
        for i, price in enumerate(prices):
            high = price * random.uniform(1.0, 1.03)
            low = price * random.uniform(0.97, 1.0)
            open_price = prices[i-1] if i > 0 else price
            close_price = price
            volume = random.randint(1000000, 50000000)
            
            data.append({
                'Open': open_price,
                'High': high,
                'Low': low,
                'Close': close_price,
                'Volume': volume
            })
        
        return pd.DataFrame(data, index=dates)
    
    @staticmethod
    def generate_ticker_mock(symbol: str):
        """Generate a mock yfinance Ticker object"""
        ticker = Mock()
        ticker.history.return_value = MockYFinanceData.generate_price_data(symbol)
        ticker.info = {
            'symbol': symbol,
            'shortName': f'{symbol} Inc.',
            'sector': 'Technology',
            'industry': 'Software',
            'marketCap': 2000000000000,
            'beta': 1.2
        }
        return ticker


class MockMCPClient:
    """Mock MCP client for testing"""
    
    def __init__(self):
        self.connected = False
        self.call_count = 0
    
    async def __aenter__(self):
        self.connected = True
        return self
    
    async def __aexit__(self, *args):
        self.connected = False
    
    async def call_tool(self, tool_name: str, parameters: dict):
        """Mock tool call with realistic responses"""
        self.call_count += 1
        
        # Generate mock response based on tool name
        mock_responses = {
            "analyze_bollinger_zscore_performance": self._generate_bollinger_zscore_response,
            "analyze_bollinger_fibonacci_performance": self._generate_bollinger_fibonacci_response,
            "analyze_macd_donchian_performance": self._generate_macd_donchian_response,
            "analyze_connors_zscore_performance": self._generate_connors_zscore_response,
            "analyze_dual_ma_strategy": self._generate_dual_ma_response
        }
        
        response_generator = mock_responses.get(tool_name, self._generate_default_response)
        response_text = response_generator(parameters)
        
        # Create mock result object
        result = Mock()
        content = Mock()
        content.text = response_text
        result.content = [content]
        
        return result
    
    def _generate_bollinger_zscore_response(self, params):
        symbol = params.get('symbol', 'UNKNOWN')
        return f"""
Bollinger Z-Score Performance Analysis for {symbol}

Strategy Performance Metrics:
- Total Return: 15.3%
- Buy & Hold Return: 12.1%
- Sharpe Ratio: 1.45
- Maximum Drawdown: -8.2%
- Win Rate: 67%
- Total Trades: 23
- Average Trade Duration: 12 days

Signal Analysis:
- Current Z-Score: -1.2 (Oversold condition)
- Recent signals show mean reversion opportunities
- Strategy outperformed buy-and-hold by 3.2%
        """
    
    def _generate_bollinger_fibonacci_response(self, params):
        symbol = params.get('symbol', 'UNKNOWN')
        return f"""
Bollinger-Fibonacci Performance Analysis for {symbol}

Strategy Performance Metrics:
- Total Return: 18.7%
- Buy & Hold Return: 12.1%
- Sharpe Ratio: 1.62
- Maximum Drawdown: -6.8%
- Win Rate: 71%
- Total Trades: 19
- Average Trade Duration: 15 days

Fibonacci Level Analysis:
- Strong support at 61.8% retracement level
- Price currently near 38.2% level
- Strategy excelled during trending markets
        """
    
    def _generate_macd_donchian_response(self, params):
        symbol = params.get('symbol', 'UNKNOWN')
        return f"""
MACD-Donchian Performance Analysis for {symbol}

Strategy Performance Metrics:
- Total Return: 14.9%
- Buy & Hold Return: 12.1%
- Sharpe Ratio: 1.38
- Maximum Drawdown: -9.1%
- Win Rate: 64%
- Total Trades: 16
- Average Trade Duration: 22 days

Technical Analysis:
- MACD showing bullish divergence
- Price near upper Donchian channel
- Momentum strategy captured major trends well
        """
    
    def _generate_connors_zscore_response(self, params):
        symbol = params.get('symbol', 'UNKNOWN')
        return f"""
Connors RSI + Z-Score Performance Analysis for {symbol}

Strategy Performance Metrics:
- Total Return: 16.2%
- Buy & Hold Return: 12.1%
- Sharpe Ratio: 1.51
- Maximum Drawdown: -7.4%
- Win Rate: 69%
- Total Trades: 28
- Average Trade Duration: 9 days

Mean Reversion Analysis:
- Connors RSI: 25 (Oversold)
- Z-Score: -1.8 (Strong oversold)
- High-frequency mean reversion signals
        """
    
    def _generate_dual_ma_response(self, params):
        symbol = params.get('symbol', 'UNKNOWN')
        return f"""
Dual Moving Average Strategy Analysis for {symbol}

Strategy Performance Metrics:
- Total Return: 13.8%
- Buy & Hold Return: 12.1%
- Sharpe Ratio: 1.24
- Maximum Drawdown: -11.3%
- Win Rate: 58%
- Total Trades: 8
- Average Trade Duration: 45 days

Trend Analysis:
- 50 EMA above 200 EMA (Bullish trend)
- Current separation: 5.2%
- Long-term trend following captured major moves
        """
    
    def _generate_default_response(self, params):
        return "Mock analysis response for testing purposes"


class TestUtilities:
    """Utility functions for testing"""
    
    @staticmethod
    def create_sample_analysis_data(symbol: str = "AAPL", num_strategies: int = 5, include_openai_summary: bool = True):
        """Create sample analysis data for testing with optional OpenAI summary"""
        strategies = [
            "bollinger_zscore", "bollinger_fibonacci", "macd_donchian",
            "connors_zscore", "dual_ma"
        ]
        
        analyses = {}
        for i in range(min(num_strategies, len(strategies))):
            analyses[strategies[i]] = f"AI-powered mock analysis result for {strategies[i]}"
        
        data = {
            "symbol": symbol,
            "analyses": analyses,
            "timestamp": datetime.now().isoformat(),
            "total_strategies": num_strategies
        }
        
        if include_openai_summary:
            data["openai_summary"] = f"AI-powered comprehensive analysis for {symbol} showing mixed signals across {num_strategies} strategies"
        
        return data
    
    @staticmethod
    def validate_markdown_structure(markdown_text: str, expect_openai_summary: bool = False):
        """Validate that markdown has proper structure with optional OpenAI content"""
        required_sections = [
            "# Technical Analysis Report:",
            "## Executive Summary",
            "## Strategy Analysis Results",
            "## Performance Summary Table",
            "## Final Recommendation"
        ]
        
        for section in required_sections:
            assert section in markdown_text, f"Missing required section: {section}"
        
        # Check for OpenAI-specific content if expected
        if expect_openai_summary:
            assert "## AI Analysis Summary" in markdown_text, "Missing AI Analysis Summary section"
            assert "AI-Powered with MCP Finance Tools" in markdown_text, "Missing AI-powered indicator"
        
        # Check for basic markdown formatting
        assert markdown_text.count("#") >= 5, "Insufficient heading structure"
        assert "|" in markdown_text, "Missing table formatting"
        assert "```" in markdown_text, "Missing code blocks"
    
    @staticmethod
    def create_temp_config():
        """Create temporary configuration for testing"""
        return {
            "mcp_server_path": "test/path/to/server",
            "analysis_dir": "test_analysis",
            "default_period": "1y",
            "strategies": {
                "bollinger_zscore": {"window": 20},
                "bollinger_fibonacci": {"window": 20, "num_std": 2},
                "macd_donchian": {"fast": 12, "slow": 26, "signal": 9, "donchian": 20},
                "connors_zscore": {"rsi_period": 3, "streak_period": 2, "rank_period": 100},
                "dual_ma": {"short": 50, "long": 200, "type": "EMA"}
            }
        }


# Test fixtures using the utility classes
@pytest.fixture
def mock_yfinance_ticker():
    """Fixture providing mock yfinance ticker"""
    return MockYFinanceData.generate_ticker_mock("AAPL")


@pytest.fixture
def mock_mcp_client():
    """Fixture providing mock MCP client"""
    return MockMCPClient()


@pytest.fixture
def sample_price_data():
    """Fixture providing sample price data"""
    return MockYFinanceData.generate_price_data("AAPL", days=252)


@pytest.fixture
def sample_analysis_result():
    """Fixture providing sample analysis result"""
    return TestUtilities.create_sample_analysis_data("AAPL", 5)


# Test the utility classes themselves
class TestMockUtilities:
    """Test the mock utilities"""
    
    def test_mock_yfinance_data_generation(self):
        """Test mock yfinance data generation"""
        data = MockYFinanceData.generate_price_data("AAPL", days=30)
        
        assert len(data) >= 30  # Could be 30 or 31 depending on date range
        assert all(col in data.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume'])
        assert all(data['High'] >= data['Low'])  # High should be >= Low for each row
        assert data['Volume'].min() > 0  # Volume should be positive
    
    def test_mock_ticker_creation(self):
        """Test mock ticker object creation"""
        ticker = MockYFinanceData.generate_ticker_mock("AAPL")
        
        assert ticker.info['symbol'] == 'AAPL'
        assert hasattr(ticker, 'history')
        
        hist = ticker.history()
        assert not hist.empty
    
    @pytest.mark.asyncio
    async def test_mock_mcp_client(self):
        """Test mock MCP client functionality"""
        client = MockMCPClient()
        
        async with client:
            assert client.connected
            
            result = await client.call_tool("analyze_bollinger_zscore_performance", {"symbol": "AAPL"})
            assert result.content[0].text is not None
            assert "AAPL" in result.content[0].text
        
        assert not client.connected
    
    def test_sample_analysis_data_creation(self):
        """Test sample analysis data creation with OpenAI content"""
        # Test with OpenAI summary
        data_with_ai = TestUtilities.create_sample_analysis_data("MSFT", 3, include_openai_summary=True)
        
        assert data_with_ai["symbol"] == "MSFT"
        assert data_with_ai["total_strategies"] == 3
        assert len(data_with_ai["analyses"]) == 3
        assert "timestamp" in data_with_ai
        assert "openai_summary" in data_with_ai
        assert "AI-powered comprehensive analysis" in data_with_ai["openai_summary"]
        
        # Test without OpenAI summary
        data_without_ai = TestUtilities.create_sample_analysis_data("MSFT", 3, include_openai_summary=False)
        assert "openai_summary" not in data_without_ai
    
    def test_markdown_validation_with_openai(self):
        """Test markdown structure validation with OpenAI content"""
        valid_markdown_with_ai = """
# Technical Analysis Report: AAPL
*AI-Powered with MCP Finance Tools*
## AI Analysis Summary
AI analysis shows strong signals
## Executive Summary
Test content
## Strategy Analysis Results
```
code block
```
## Performance Summary Table
| Column | Value |
|--------|-------|
| Test   | 123   |
## Final Recommendation
Final content
        """
        
        # Should not raise assertion error
        TestUtilities.validate_markdown_structure(valid_markdown_with_ai, expect_openai_summary=True)
        
        # Test traditional markdown without AI content
        valid_markdown_without_ai = """
# Technical Analysis Report: AAPL
## Executive Summary
Test content
## Strategy Analysis Results
```
code block
```
## Performance Summary Table
| Column | Value |
|--------|-------|
| Test   | 123   |
## Final Recommendation
Final content
        """
        
        TestUtilities.validate_markdown_structure(valid_markdown_without_ai, expect_openai_summary=False)
