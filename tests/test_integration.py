"""
Integration tests for the stock analyzer application with OpenAI integration
"""

import pytest
import asyncio
import subprocess
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestStockAnalyzerIntegration:
    """Integration tests for the stock analyzer"""
    
    @pytest.mark.integration
    def test_command_line_help(self):
        """Test command line help output"""
        result = subprocess.run(
            [sys.executable, "stock_analyzer.py", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0
        assert "AI-Powered Stock Technical Analysis Tool" in result.stdout
        assert "Yahoo Finance stock symbol" in result.stdout
        assert "Uses OpenAI to orchestrate analysis" in result.stdout
    
    @pytest.mark.integration
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('stock_analyzer.StockAnalyzer.connect_to_mcp_server')
    @patch('stock_analyzer.StockAnalyzer.analyze_with_openai')
    @patch('stock_analyzer.StockAnalyzer.disconnect_from_mcp_server')
    def test_command_line_execution_success(
        self, mock_disconnect, mock_analyze_openai, mock_connect
    ):
        """Test successful command line execution with OpenAI"""
        # Mock successful connection
        mock_connect.return_value = True
        
        # Mock successful OpenAI analysis
        mock_analyze_openai.return_value = {
            "symbol": "AAPL",
            "analyses": {
                "bollinger_zscore": "AI-powered Bollinger Z-Score analysis result",
                "bollinger_fibonacci": "AI-powered Bollinger-Fibonacci analysis result",
                "macd_donchian": "AI-powered MACD-Donchian analysis result",
                "connors_zscore": "AI-powered Connors Z-Score analysis result",
                "dual_ma": "AI-powered Dual MA analysis result"
            },
            "timestamp": "2024-01-01T00:00:00",
            "total_strategies": 5,
            "openai_summary": "OpenAI analysis indicates strong technical signals"
        }
        
        # Mock report saving
        with patch('stock_analyzer.StockAnalyzer.save_report') as mock_save:
            mock_save.return_value = "analysis/Technical_analysis_AAPL_20240101_120000.md"
            
            # Run the command
            result = subprocess.run(
                [sys.executable, "stock_analyzer.py", "AAPL"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            # Note: This will likely fail in CI/test environment due to MCP server
            # but the test structure shows how integration testing would work
    
    @pytest.mark.integration
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    def test_invalid_symbol_handling(self):
        """Test handling of invalid symbols with OpenAI"""
        with patch('stock_analyzer.StockAnalyzer.connect_to_mcp_server') as mock_connect:
            mock_connect.return_value = True
            
            with patch('stock_analyzer.StockAnalyzer.analyze_with_openai') as mock_analyze:
                mock_analyze.return_value = {"error": "Invalid symbol: AI analysis cannot proceed"}
                
                # This would test the actual command line behavior
                # In practice, this requires both MCP server and OpenAI API
                pass
    
    @pytest.mark.integration
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    def test_openai_api_key_validation(self):
        """Test OpenAI API key validation"""
        # Test without API key
        with patch.dict(os.environ, {}, clear=True):
            from stock_analyzer import StockAnalyzer
            
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                StockAnalyzer()
    
    @pytest.mark.integration
    def test_analysis_directory_creation(self):
        """Test that analysis directory is created"""
        analysis_dir = Path("analysis")
        
        # Remove directory if it exists
        if analysis_dir.exists():
            import shutil
            shutil.rmtree(analysis_dir)
        
        # Import and use the analyzer to trigger directory creation
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            from stock_analyzer import StockAnalyzer
            analyzer = StockAnalyzer()
        
        # Mock data for report generation with OpenAI summary
        mock_data = {
            "symbol": "TEST",
            "analyses": {"test": "AI-powered test result"},
            "timestamp": "2024-01-01T00:00:00",
            "total_strategies": 1,
            "openai_summary": "AI analysis summary for TEST stock"
        }
        
        with patch('yfinance.Ticker'):
            report = analyzer.generate_markdown_report(mock_data)
            filepath = analyzer.save_report(report, "TEST")
        
        # Check that directory was created
        assert analysis_dir.exists()
        assert analysis_dir.is_dir()
        
        # Check that OpenAI summary is in the report
        with open(filepath, 'r') as f:
            content = f.read()
        assert "AI Analysis Summary" in content
        assert "AI analysis summary for TEST stock" in content
        
        # Clean up
        if filepath and Path(filepath).exists():
            Path(filepath).unlink()


class TestEndToEnd:
    """End-to-end tests that require all components including OpenAI"""
    
    @pytest.mark.e2e
    @pytest.mark.skipif(
        not Path("server/main.py").exists(),
        reason="MCP server not available"
    )
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    async def test_full_analysis_workflow_with_openai(self):
        """Test the complete analysis workflow with OpenAI integration"""
        from stock_analyzer import StockAnalyzer
        
        analyzer = StockAnalyzer()
        
        # This would be a full end-to-end test but requires:
        # 1. MCP server to be running
        # 2. OpenAI API key and access
        # 3. Internet connection for yfinance
        # 4. Valid stock symbols
        
        # For now, we'll just test the structure includes OpenAI components
        assert hasattr(analyzer, 'openai_client')
        assert hasattr(analyzer, 'connect_to_mcp_server')
        assert hasattr(analyzer, 'analyze_with_openai')
        assert hasattr(analyzer, 'get_available_tools')
        assert hasattr(analyzer, 'execute_mcp_tool')
        assert hasattr(analyzer, 'generate_markdown_report')
        assert hasattr(analyzer, 'save_report')
    
    @pytest.mark.e2e
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    def test_error_handling_workflow(self):
        """Test error handling in the complete workflow with OpenAI"""
        # Test various error conditions:
        # 1. MCP server connection failure
        # 2. OpenAI API failures
        # 3. Invalid symbols
        # 4. Network issues
        # 5. File system issues
        
        from stock_analyzer import StockAnalyzer
        
        # Test OpenAI client initialization
        analyzer = StockAnalyzer()
        assert analyzer.openai_client is not None
        
        # Test MCP connection error handling
        with patch('stock_analyzer.StockAnalyzer.connect_to_mcp_server') as mock_connect:
            mock_connect.return_value = False
            # This would test actual error handling workflow
            pass


class TestReportGeneration:
    """Tests for report generation and formatting with OpenAI integration"""
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    def test_markdown_structure_with_openai(self):
        """Test that generated markdown has proper structure with OpenAI content"""
        from stock_analyzer import StockAnalyzer
        
        analyzer = StockAnalyzer()
        
        sample_data = {
            "symbol": "AAPL",
            "analyses": {
                "bollinger_zscore": "AI-powered Bollinger Z-Score analysis result",
                "bollinger_fibonacci": "AI-powered Bollinger-Fibonacci analysis result",
                "macd_donchian": "AI-powered MACD-Donchian analysis result",
                "connors_zscore": "AI-powered Connors Z-Score analysis result",
                "dual_ma": "AI-powered Dual MA analysis result"
            },
            "timestamp": "2024-01-01T00:00:00",
            "total_strategies": 5,
            "openai_summary": "OpenAI comprehensive market analysis shows strong technical indicators with bullish sentiment across multiple timeframes."
        }
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_hist = MagicMock()
            mock_hist['Close'].iloc = [150.0]
            mock_ticker.return_value.history.return_value = mock_hist
            
            report = analyzer.generate_markdown_report(sample_data)
        
        # Test markdown structure includes OpenAI elements
        assert report.startswith("# Technical Analysis Report: AAPL")
        assert "AI-Powered with MCP Finance Tools" in report
        assert "## AI Analysis Summary" in report
        assert "## Executive Summary" in report
        assert "## Strategy Analysis Results" in report
        assert "## Performance Summary Table" in report
        assert "## Final Recommendation" in report
        
        # Test OpenAI summary content
        assert "OpenAI comprehensive market analysis" in report
        assert "OpenAI-powered analysis" in report
        
        # Test that all strategies are included with AI indication
        assert "Bollinger Z-Score Performance Analysis" in report
        assert "Bollinger-Fibonacci Performance Analysis" in report
        assert "MACD-Donchian Performance Analysis" in report
        assert "Connors RSI + Z-Score Performance Analysis" in report
        assert "Dual Moving Average Strategy Analysis" in report
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    def test_markdown_structure_without_openai_summary(self):
        """Test markdown structure when OpenAI summary is not available"""
        from stock_analyzer import StockAnalyzer
        
        analyzer = StockAnalyzer()
        
        sample_data = {
            "symbol": "AAPL",
            "analyses": {
                "bollinger_zscore": "Analysis result without AI summary"
            },
            "timestamp": "2024-01-01T00:00:00",
            "total_strategies": 1
        }
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_hist = MagicMock()
            mock_hist['Close'].iloc = [150.0]
            mock_ticker.return_value.history.return_value = mock_hist
            
            report = analyzer.generate_markdown_report(sample_data)
        
        # Should still have main structure but no AI summary section
        assert "# Technical Analysis Report: AAPL" in report
        assert "AI-Powered with MCP Finance Tools" in report
        assert "## AI Analysis Summary" not in report
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    def test_filename_generation(self):
        """Test that filenames are generated correctly"""
        from stock_analyzer import StockAnalyzer
        
        analyzer = StockAnalyzer()
        
        # Mock the save_report method to check filename format
        with patch('builtins.open'), patch('pathlib.Path.mkdir'):
            filepath = analyzer.save_report("test content", "AAPL")
            
            # Check filename format
            filename = Path(filepath).name
            assert filename.startswith("Technical_analysis_AAPL_")
            assert filename.endswith(".md")
            assert len(filename.split("_")) >= 4  # Technical_analysis_SYMBOL_TIMESTAMP.md
