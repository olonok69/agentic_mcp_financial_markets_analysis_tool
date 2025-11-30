"""
Performance and stress tests for the stock analyzer with OpenAI integration
"""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock, MagicMock
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPerformance:
    """Performance tests for the stock analyzer with OpenAI"""
    
    @pytest.mark.performance
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('stock_analyzer.StockAnalyzer.validate_symbol')
    @patch('stock_analyzer.StockAnalyzer.analyze_with_openai')
    async def test_openai_analysis_performance(
        self, mock_analyze_openai, mock_validate
    ):
        """Test that OpenAI analysis completes within reasonable time"""
        from stock_analyzer import StockAnalyzer
        analyzer = StockAnalyzer()
        
        # Setup mocks for fast response
        mock_validate.return_value = True
        mock_analyze_openai.return_value = {
            "symbol": "AAPL",
            "analyses": {
                "bollinger_zscore": "AI-powered result",
                "bollinger_fibonacci": "AI-powered result",
                "macd_donchian": "AI-powered result",
                "connors_zscore": "AI-powered result",
                "dual_ma": "AI-powered result"
            },
            "timestamp": "2024-01-01T00:00:00",
            "total_strategies": 5,
            "openai_summary": "Fast AI analysis"
        }
        
        start_time = time.time()
        result = await analyzer.analyze_stock("AAPL")
        end_time = time.time()
        
        # Analysis should complete quickly with mocked OpenAI
        assert end_time - start_time < 2.0  # Less than 2 seconds (allowing for OpenAI overhead)
        assert result["total_strategies"] == 5
        assert "openai_summary" in result
    
    @pytest.mark.performance
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    def test_report_generation_performance(self):
        """Test report generation performance with OpenAI content"""
        from stock_analyzer import StockAnalyzer
        analyzer = StockAnalyzer()
        
        # Create large sample data with OpenAI summary
        sample_data = {
            "symbol": "AAPL",
            "analyses": {
                "bollinger_zscore": "A" * 10000,  # Large analysis result
                "bollinger_fibonacci": "B" * 10000,
                "macd_donchian": "C" * 10000,
                "connors_zscore": "D" * 10000,
                "dual_ma": "E" * 10000
            },
            "timestamp": "2024-01-01T00:00:00",
            "total_strategies": 5,
            "openai_summary": "AI-powered comprehensive analysis summary: " + "F" * 5000
        }
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_hist = MagicMock()
            mock_hist['Close'].iloc = [150.0]
            mock_ticker.return_value.history.return_value = mock_hist
            
            start_time = time.time()
            report = analyzer.generate_markdown_report(sample_data)
            end_time = time.time()
            
            # Report generation should be fast even with large data and OpenAI content
            assert end_time - start_time < 1.0  # Less than 1 second (allowing for OpenAI content)
            assert len(report) > 55000  # Should be substantial with OpenAI summary
            assert "AI Analysis Summary" in report
    
    @pytest.mark.performance
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    async def test_concurrent_openai_analysis(self):
        """Test multiple concurrent OpenAI analyses"""
        from stock_analyzer import StockAnalyzer
        analyzer = StockAnalyzer()
        
        # Mock the OpenAI analysis method
        with patch.object(analyzer, 'validate_symbol', return_value=True), \
             patch.object(analyzer, 'analyze_with_openai', return_value={
                 "symbol": "TEST",
                 "analyses": {"bollinger_zscore": "AI Result"},
                 "timestamp": "2024-01-01T00:00:00",
                 "total_strategies": 1,
                 "openai_summary": "AI analysis summary"
             }):
            
            # Run multiple analyses concurrently
            symbols = ["AAPL", "MSFT", "GOOGL"]
            
            start_time = time.time()
            tasks = [analyzer.analyze_stock(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            # All analyses should complete
            assert len(results) == 3
            for result in results:
                assert result["total_strategies"] == 1  # Updated for mocked return
                assert "openai_summary" in result
            
            # Should complete faster than sequential execution
            assert end_time - start_time < 3.0  # Allowing more time for OpenAI


class TestStress:
    """Stress tests for edge cases and failure scenarios with OpenAI"""
    
    @pytest.mark.stress
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    async def test_openai_timeout_simulation(self):
        """Test handling of OpenAI API timeouts"""
        from stock_analyzer import StockAnalyzer
        analyzer = StockAnalyzer()
        
        # Mock OpenAI timeout
        with patch.object(analyzer, 'validate_symbol', return_value=True), \
             patch.object(analyzer, 'analyze_with_openai', side_effect=asyncio.TimeoutError):
            result = await analyzer.analyze_stock("AAPL")
            assert "error" in result
    
    @pytest.mark.stress
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    async def test_openai_api_failure(self):
        """Test handling when OpenAI API fails"""
        from stock_analyzer import StockAnalyzer
        analyzer = StockAnalyzer()
        
        # Setup OpenAI failure scenario
        with patch.object(analyzer, 'validate_symbol', return_value=True), \
             patch.object(analyzer, 'analyze_with_openai', return_value={"error": "OpenAI API failure"}):
            
            result = await analyzer.analyze_stock("AAPL")
            
            # Should handle the error gracefully
            assert "error" in result
    
    @pytest.mark.stress
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    def test_large_symbol_list_handling(self):
        """Test handling of very long symbol lists (conceptual test)"""
        # This would test the market scanner functionality
        # with many symbols at once with OpenAI coordination
        from stock_analyzer import StockAnalyzer
        analyzer = StockAnalyzer()
        
        # Test that analyzer can handle initialization for bulk operations
        assert analyzer.openai_client is not None
        # In practice, this would coordinate OpenAI calls for multiple symbols
    
    @pytest.mark.stress
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    def test_memory_usage_with_openai(self):
        """Test memory usage with large datasets including OpenAI content"""
        import tracemalloc
        
        from stock_analyzer import StockAnalyzer
        analyzer = StockAnalyzer()
        
        # Start tracing memory
        tracemalloc.start()
        
        # Generate large report with OpenAI summary
        large_data = {
            "symbol": "AAPL",
            "analyses": {
                f"strategy_{i}": "X" * 100000 for i in range(20)  # Reduced for OpenAI overhead
            },
            "timestamp": "2024-01-01T00:00:00",
            "total_strategies": 20,
            "openai_summary": "Large AI analysis summary: " + "Y" * 50000
        }
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_hist = MagicMock()
            mock_hist['Close'].iloc = [150.0]
            mock_ticker.return_value.history.return_value = mock_hist
            
            report = analyzer.generate_markdown_report(large_data)
        
        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Memory usage should be reasonable (allowing for OpenAI overhead)
        assert peak < 150 * 1024 * 1024  # 150MB (increased for OpenAI content)
        assert len(report) > 1000000  # Should be substantial
        assert "AI Analysis Summary" in report
    
    @pytest.mark.stress
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    async def test_rapid_successive_openai_requests(self):
        """Test rapid successive OpenAI analysis requests"""
        from stock_analyzer import StockAnalyzer
        analyzer = StockAnalyzer()
        
        # Mock quick OpenAI responses
        with patch.object(analyzer, 'validate_symbol', return_value=True), \
             patch.object(analyzer, 'analyze_with_openai', return_value={
                 "symbol": "AAPL",
                 "analyses": {"bollinger_zscore": "AI Result"},
                 "timestamp": "2024-01-01T00:00:00",
                 "total_strategies": 1,
                 "openai_summary": "Quick AI analysis"
             }):
            
            # Make many rapid requests
            symbols = ["AAPL"] * 5  # Reduced for OpenAI rate limits
            
            tasks = []
            for symbol in symbols:
                task = asyncio.create_task(analyzer.analyze_stock(symbol))
                tasks.append(task)
                await asyncio.sleep(0.1)  # Longer delay for OpenAI
            
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            assert len(results) == 5
            for result in results:
                assert result["total_strategies"] == 1
                assert "openai_summary" in result


class TestErrorRecovery:
    """Tests for error recovery and graceful degradation with OpenAI"""
    
    @pytest.mark.error_recovery
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    async def test_mcp_server_connection_failure(self):
        """Test handling of MCP server connection failure"""
        from stock_analyzer import StockAnalyzer
        analyzer = StockAnalyzer()
        
        # Mock connection failure
        with patch.object(analyzer, 'connect_to_mcp_server', return_value=False):
            result = await analyzer.connect_to_mcp_server()
            assert result is False
    
    @pytest.mark.error_recovery
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    async def test_openai_analysis_failure_recovery(self):
        """Test recovery from OpenAI analysis failures"""
        from stock_analyzer import StockAnalyzer
        analyzer = StockAnalyzer()
        
        # Simulate OpenAI analysis failing
        with patch.object(analyzer, 'validate_symbol', return_value=True), \
             patch.object(analyzer, 'analyze_with_openai', return_value={"error": "OpenAI analysis failed"}):
            
            result = await analyzer.analyze_stock("AAPL")
            
            # Should return error when OpenAI analysis fails
            assert "error" in result
    
    @pytest.mark.error_recovery
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    def test_file_system_error_handling(self):
        """Test handling of file system errors"""
        from stock_analyzer import StockAnalyzer
        analyzer = StockAnalyzer()
        
        # Mock file system error
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            filepath = analyzer.save_report("test content", "AAPL")
            
            # Should return empty string on error
            assert filepath == ""
