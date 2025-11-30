"""
Unit tests for the StockAnalyzer class with OpenAI integration
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import sys
import os

# Add the parent directory to the path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stock_analyzer import StockAnalyzer


class TestStockAnalyzer:
    """Test cases for StockAnalyzer class with OpenAI integration"""
    
    @pytest.fixture
    def analyzer(self):
        """Create a StockAnalyzer instance for testing"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('stock_analyzer.openai.OpenAI'):
                return StockAnalyzer()
    
    def test_init_with_api_key(self):
        """Test StockAnalyzer initialization with API key"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('stock_analyzer.openai.OpenAI') as mock_openai:
                analyzer = StockAnalyzer()
                assert analyzer.openai_client is not None
                assert analyzer.mcp_client is None
                assert analyzer.analysis_results == {}
                mock_openai.assert_called_once()
    
    def test_init_without_api_key(self):
        """Test StockAnalyzer initialization without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                StockAnalyzer()
    
    @patch('yfinance.Ticker')
    def test_validate_symbol_valid(self, mock_ticker, analyzer):
        """Test symbol validation with valid symbol"""
        # Mock yfinance response
        mock_hist = MagicMock()
        mock_hist.empty = False
        mock_ticker.return_value.history.return_value = mock_hist
        
        result = analyzer.validate_symbol("AAPL")
        assert result is True
        mock_ticker.assert_called_once_with("AAPL")
    
    @patch('yfinance.Ticker')
    def test_validate_symbol_invalid(self, mock_ticker, analyzer):
        """Test symbol validation with invalid symbol"""
        # Mock yfinance response for invalid symbol
        mock_hist = MagicMock()
        mock_hist.empty = True
        mock_ticker.return_value.history.return_value = mock_hist
        
        result = analyzer.validate_symbol("INVALID")
        assert result is False
    
    def test_validate_symbol_empty(self, analyzer):
        """Test symbol validation with empty symbol"""
        result = analyzer.validate_symbol("")
        assert result is False
        
        result = analyzer.validate_symbol("   ")
        assert result is False
        
        result = analyzer.validate_symbol(None)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_available_tools_success(self, analyzer):
        """Test getting available tools from MCP server"""
        analyzer.mcp_client = AsyncMock()
        
        # Mock tools response
        mock_tools = [
            Mock(name="analyze_bollinger_zscore_performance", description="Test tool 1"),
            Mock(name="analyze_macd_donchian_performance", description="Test tool 2")
        ]
        mock_result = Mock(tools=mock_tools)
        analyzer.mcp_client.list_tools.return_value = mock_result
        
        tools = await analyzer.get_available_tools()
        assert len(tools) == 2
        assert tools[0].name == "analyze_bollinger_zscore_performance"
    
    @pytest.mark.asyncio
    async def test_get_available_tools_failure(self, analyzer):
        """Test getting available tools failure"""
        analyzer.mcp_client = AsyncMock()
        analyzer.mcp_client.list_tools.side_effect = Exception("Connection error")
        
        tools = await analyzer.get_available_tools()
        assert tools == []
    
    def test_create_openai_tools_schema(self, analyzer):
        """Test creating OpenAI tools schema from MCP tools"""
        # Mock MCP tools
        mcp_tools = [
            Mock(name="analyze_bollinger_zscore_performance", description="Bollinger Z-Score analysis"),
            Mock(name="analyze_macd_donchian_performance", description="MACD-Donchian analysis"),
            Mock(name="some_other_tool", description="Not used")
        ]
        
        openai_tools = analyzer.create_openai_tools_schema(mcp_tools)
        
        # Should only include the target tools
        assert len(openai_tools) == 2
        
        # Check structure of first tool
        first_tool = openai_tools[0]
        assert first_tool["type"] == "function"
        assert "function" in first_tool
        assert "name" in first_tool["function"]
        assert "parameters" in first_tool["function"]
        assert "symbol" in first_tool["function"]["parameters"]["properties"]
    
    @pytest.mark.asyncio
    async def test_execute_mcp_tool_success(self, analyzer):
        """Test successful MCP tool execution"""
        analyzer.mcp_client = AsyncMock()
        
        # Mock tool result
        mock_result = Mock()
        mock_result.content = [Mock(text="Analysis result")]
        analyzer.mcp_client.call_tool.return_value = mock_result
        
        result = await analyzer.execute_mcp_tool("test_tool", {"symbol": "AAPL"})
        
        assert result == "Analysis result"
        analyzer.mcp_client.call_tool.assert_called_once_with("test_tool", {"symbol": "AAPL"})
    
    @pytest.mark.asyncio
    async def test_execute_mcp_tool_failure(self, analyzer):
        """Test MCP tool execution failure"""
        analyzer.mcp_client = AsyncMock()
        analyzer.mcp_client.call_tool.side_effect = Exception("Tool error")
        
        result = await analyzer.execute_mcp_tool("test_tool", {"symbol": "AAPL"})
        assert result is None
    
    @pytest.mark.asyncio
    async def test_analyze_with_openai_success(self, analyzer):
        """Test successful OpenAI analysis"""
        # Mock MCP client and tools
        analyzer.mcp_client = AsyncMock()
        
        # Mock available tools
        mock_tools = [
            Mock(name="analyze_bollinger_zscore_performance", description="Test tool"),
            Mock(name="analyze_macd_donchian_performance", description="Test tool")
        ]
        analyzer.get_available_tools = AsyncMock(return_value=mock_tools)
        
        # Mock OpenAI response
        mock_tool_call = Mock()
        mock_tool_call.function.name = "analyze_bollinger_zscore_performance"
        mock_tool_call.function.arguments = '{"symbol": "AAPL"}'
        
        mock_message = Mock()
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = "Analysis summary"
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        analyzer.openai_client.chat.completions.create.return_value = mock_response
        
        # Mock tool execution
        analyzer.execute_mcp_tool = AsyncMock(return_value="Tool result")
        
        result = await analyzer.analyze_with_openai("AAPL")
        
        assert result["symbol"] == "AAPL"
        assert "analyses" in result
        assert "timestamp" in result
        assert result["total_strategies"] > 0
    
    @pytest.mark.asyncio
    async def test_analyze_with_openai_no_tools(self, analyzer):
        """Test OpenAI analysis with no available tools"""
        analyzer.get_available_tools = AsyncMock(return_value=[])
        
        result = await analyzer.analyze_with_openai("AAPL")
        
        assert "error" in result
        assert "No analysis tools available" in result["error"]
    
    @pytest.mark.asyncio
    @patch('stock_analyzer.StockAnalyzer.validate_symbol')
    @patch('stock_analyzer.StockAnalyzer.analyze_with_openai')
    async def test_analyze_stock_success(self, mock_analyze_openai, mock_validate, analyzer):
        """Test successful stock analysis"""
        # Setup mocks
        mock_validate.return_value = True
        mock_analyze_openai.return_value = {
            "symbol": "AAPL",
            "analyses": {"bollinger_zscore": "result"},
            "timestamp": "2024-01-01T00:00:00",
            "total_strategies": 1
        }
        
        result = await analyzer.analyze_stock("AAPL")
        
        assert result["symbol"] == "AAPL"
        assert result["total_strategies"] == 1
        assert "analyses" in result
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    @patch('stock_analyzer.StockAnalyzer.validate_symbol')
    async def test_analyze_stock_invalid_symbol(self, mock_validate, analyzer):
        """Test stock analysis with invalid symbol"""
        mock_validate.return_value = False
        
        result = await analyzer.analyze_stock("INVALID")
        
        assert "error" in result
        assert "Invalid or non-existent symbol" in result["error"]
    
    def test_generate_markdown_report_with_openai(self, analyzer):
        """Test markdown report generation with OpenAI summary"""
        sample_data = {
            "symbol": "AAPL",
            "analyses": {
                "bollinger_zscore": "Bollinger Z result",
                "macd_donchian": "MACD result"
            },
            "timestamp": "2024-01-01T00:00:00",
            "total_strategies": 2,
            "openai_summary": "AI analysis shows strong buy signals"
        }
        
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock current price
            mock_hist = MagicMock()
            mock_hist['Close'].iloc = [150.0]
            mock_ticker.return_value.history.return_value = mock_hist
            
            report = analyzer.generate_markdown_report(sample_data)
            
            assert "# Technical Analysis Report: AAPL" in report
            assert "AI-Powered with MCP Finance Tools" in report
            assert "AI Analysis Summary" in report
            assert "AI analysis shows strong buy signals" in report
            assert "OpenAI-powered analysis" in report
    
    def test_generate_markdown_report_without_openai_summary(self, analyzer):
        """Test markdown report generation without OpenAI summary"""
        sample_data = {
            "symbol": "AAPL",
            "analyses": {"bollinger_zscore": "Result"},
            "timestamp": "2024-01-01T00:00:00",
            "total_strategies": 1
        }
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_hist = MagicMock()
            mock_hist['Close'].iloc = [150.0]
            mock_ticker.return_value.history.return_value = mock_hist
            
            report = analyzer.generate_markdown_report(sample_data)
            
            assert "# Technical Analysis Report: AAPL" in report
            assert "AI Analysis Summary" not in report
    
    def test_save_report(self, analyzer, temp_analysis_dir):
        """Test report saving"""
        # Change to temp directory for testing
        original_cwd = os.getcwd()
        os.chdir(temp_analysis_dir.parent)
        
        try:
            report_content = "# Test Report\nThis is a test report."
            filepath = analyzer.save_report(report_content, "AAPL")
            
            assert filepath != ""
            assert Path(filepath).exists()
            
            # Check file content
            with open(filepath, 'r') as f:
                content = f.read()
            assert "# Test Report" in content
            
        finally:
            os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_connect_to_mcp_server_missing_file(self, analyzer):
        """Test MCP server connection with missing server file"""
        with patch('pathlib.Path.exists', return_value=False):
            result = await analyzer.connect_to_mcp_server()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_disconnect_from_mcp_server(self, analyzer):
        """Test MCP server disconnection"""
        # Mock client
        analyzer.mcp_client = AsyncMock()
        
        await analyzer.disconnect_from_mcp_server()
        
        analyzer.mcp_client.__aexit__.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_from_mcp_server_no_client(self, analyzer):
        """Test MCP server disconnection with no client"""
        analyzer.mcp_client = None
        
        # Should not raise exception
        await analyzer.disconnect_from_mcp_server()
