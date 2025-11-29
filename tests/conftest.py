"""
Test configuration and fixtures for stock analyzer tests
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_analysis_dir():
    """Create a temporary analysis directory for testing"""
    temp_dir = tempfile.mkdtemp()
    analysis_dir = Path(temp_dir) / "analysis"
    analysis_dir.mkdir()
    yield analysis_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for testing"""
    client = AsyncMock()
    
    # Mock successful tool calls
    mock_result = Mock()
    mock_result.content = [Mock(text="Mock analysis result")]
    client.call_tool.return_value = mock_result
    
    return client


@pytest.fixture
def sample_analysis_data():
    """Sample analysis data for testing"""
    return {
        "symbol": "AAPL",
        "analyses": {
            "bollinger_zscore": "Mock Bollinger Z-Score analysis result",
            "bollinger_fibonacci": "Mock Bollinger-Fibonacci analysis result",
            "macd_donchian": "Mock MACD-Donchian analysis result",
            "connors_zscore": "Mock Connors RSI + Z-Score analysis result",
            "dual_ma": "Mock Dual Moving Average analysis result"
        },
        "timestamp": "2024-01-01T00:00:00",
        "total_strategies": 5
    }


@pytest.fixture
def sample_yfinance_data():
    """Mock yfinance data"""
    import pandas as pd
    from datetime import datetime, timedelta
    
    # Create sample price data
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=30),
        end=datetime.now(),
        freq='D'
    )
    
    data = pd.DataFrame({
        'Close': [150 + i for i in range(len(dates))],
        'Open': [149 + i for i in range(len(dates))],
        'High': [152 + i for i in range(len(dates))],
        'Low': [148 + i for i in range(len(dates))],
        'Volume': [1000000 + i * 10000 for i in range(len(dates))]
    }, index=dates)
    
    return data


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
