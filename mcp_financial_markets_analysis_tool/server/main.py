from mcp.server.fastmcp import FastMCP

# Import existing strategy modules
from strategies.bollinger_fibonacci import register_bollinger_fibonacci_tools
from strategies.macd_donchian import register_macd_donchian_tools
from strategies.connors_zscore import register_connors_zscore_tools
from strategies.dual_moving_average import register_dual_ma_tools
from strategies.bollinger_zscore import register_bollinger_zscore_tools

# Import performance tools
from strategies.performance_tools import add_all_performance_tools
from strategies.comprehensive_analysis import add_comprehensive_strategy_analysis_tool

# Import UNIFIED market scanner (replaces both old scanners)
from strategies.unified_market_scanner import add_unified_market_scanner_tool

# Initialize FastMCP server
mcp = FastMCP("finance tools", "1.0.0")

# Register existing strategy tools
register_bollinger_fibonacci_tools(mcp)
register_macd_donchian_tools(mcp)
register_connors_zscore_tools(mcp)
register_dual_ma_tools(mcp)
register_bollinger_zscore_tools(mcp)

# Register performance tools
add_all_performance_tools(mcp)
add_comprehensive_strategy_analysis_tool(mcp)

# Register UNIFIED market scanner (replaces comprehensive_market_scanner and enhanced_market_scanner)
add_unified_market_scanner_tool(mcp)

if __name__ == "__main__":
    mcp.run(transport='stdio')