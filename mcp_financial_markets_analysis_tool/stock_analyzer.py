#!/usr/bin/env python3
"""
Stock Technical Analysis Tool

A command-line application that performs comprehensive technical analysis
on stock symbols using multiple trading strategies and generates detailed reports.
"""

import os
import sys
import argparse
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from contextlib import AsyncExitStack
except ImportError:
    logger.error("MCP library not found. Please install with: pip install mcp")
    sys.exit(1)

try:
    import yfinance as yf
except ImportError:
    logger.error("yfinance library not found. Please install with: pip install yfinance")
    sys.exit(1)

try:
    import openai
except ImportError:
    logger.error("OpenAI library not found. Please install with: pip install openai")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not found. Environment variables from .env file won't be loaded.")
    pass


class StockAnalyzer:
    """Main class for stock technical analysis using OpenAI with MCP finance tools"""
    
    def __init__(self):
        self.openai_client = None
        self.session = None
        self.exit_stack = AsyncExitStack()
        self.analysis_results = {}
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OpenAI API key is required")
        
        self.openai_client = openai.OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized")
        
    async def connect_to_mcp_server(self) -> bool:
        """Connect to the finance tools MCP server"""
        try:
            # Get the path to the MCP server from current directory
            server_path = Path(__file__).parent / "server" / "main.py"
            
            if not server_path.exists():
                logger.error(f"MCP server not found at {server_path}")
                return False
            
            # Create server parameters
            server_params = StdioServerParameters(
                command="python",
                args=[str(server_path)]
            )
            
            # Connect using the pattern from your working client
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio_read, stdio_write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(stdio_read, stdio_write)
            )
            
            await self.session.initialize()
            
            logger.info("Successfully connected to finance tools MCP server")
            return True
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def disconnect_from_mcp_server(self):
        """Disconnect from MCP server"""
        try:
            await self.exit_stack.aclose()
            logger.info("Disconnected from MCP server")
        except Exception as e:
            logger.error(f"Error disconnecting from MCP server: {e}")
        finally:
            self.session = None
    
    async def get_available_tools(self) -> list:
        """Get list of available tools from MCP server"""
        try:
            response = await self.session.list_tools()
            return response.tools if response else []
        except Exception as e:
            logger.error(f"Error getting available tools: {e}")
            return []
    
    def create_openai_tools_schema(self, mcp_tools: list) -> list:
        """Convert MCP tools to OpenAI function calling schema"""
        openai_tools = []
        
        # Define the specific tools we want to use for our analysis
        target_tools = [
            "analyze_bollinger_zscore_performance",
            "analyze_bollinger_fibonacci_performance", 
            "analyze_macd_donchian_performance",
            "analyze_connors_zscore_performance",
            "analyze_dual_ma_strategy"
        ]
        
        for tool in mcp_tools:
            if tool.name in target_tools:
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or f"Execute {tool.name} analysis",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                }
                
                # Add basic parameters that we know these tools need
                if "symbol" not in openai_tool["function"]["parameters"]["properties"]:
                    openai_tool["function"]["parameters"]["properties"]["symbol"] = {
                        "type": "string",
                        "description": "Stock ticker symbol"
                    }
                    openai_tool["function"]["parameters"]["required"].append("symbol")
                
                openai_tools.append(openai_tool)
        
        return openai_tools
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if the symbol exists and has data"""
        if not symbol or not symbol.strip():
            logger.warning("Empty symbol provided")
            return False
        
        try:
            # Try to fetch a small amount of data to validate
            ticker = yf.Ticker(symbol.strip().upper())
            hist = ticker.history(period="5d")
            
            if hist.empty:
                logger.warning(f"No data found for symbol: {symbol}")
                return False
                
            logger.info(f"Symbol {symbol.upper()} validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {e}")
            return False
    
    async def execute_mcp_tool(self, tool_name: str, parameters: dict) -> Optional[str]:
        """Execute a tool on the MCP server"""
        try:
            result = await self.session.call_tool(tool_name, parameters)
            return result.content[0].text if result.content else None
        except Exception as e:
            logger.error(f"Error executing {tool_name}: {e}")
            return None
    
    async def analyze_with_openai(self, symbol: str) -> Dict[str, Any]:
        """Use OpenAI to orchestrate the technical analysis using MCP tools"""
        try:
            # Get available tools from MCP server
            mcp_tools = await self.get_available_tools()
            openai_tools = self.create_openai_tools_schema(mcp_tools)
            
            if not openai_tools:
                logger.error("No compatible tools found on MCP server")
                return {"error": "No analysis tools available"}
            
            logger.info(f"Found {len(openai_tools)} analysis tools")
            
            # Create the analysis prompt
            analysis_prompt = f"""
You are a professional financial analyst. I need you to perform a comprehensive technical analysis of the stock symbol '{symbol}' using multiple trading strategies.

Please use ALL of the following analysis tools to analyze {symbol}:

1. analyze_bollinger_zscore_performance - for Bollinger Z-Score analysis (period: "1y", window: 20)
2. analyze_bollinger_fibonacci_performance - for Bollinger-Fibonacci analysis (period: "1y", window: 20, num_std: 2, fibonacci_levels: [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1])
3. analyze_macd_donchian_performance - for MACD-Donchian analysis (period: "1y", macd_params: {{"fast_period": 12, "slow_period": 26, "signal_period": 9}}, donchian_window: 20)
4. analyze_connors_zscore_performance - for Connors RSI + Z-Score analysis (period: "1y", connors_params: {{"rsi_period": 3, "streak_period": 2, "rank_period": 100}}, zscore_window: 20)
5. analyze_dual_ma_strategy - for Dual Moving Average analysis (period: "1y", short_period: 50, long_period: 200, ma_type: "EMA")

Execute each tool with the specified parameters for symbol '{symbol}'. After running all tools, provide a summary of what each analysis revealed.
"""

            # Make the OpenAI API call with function calling
            response = self.openai_client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4"),
                messages=[
                    {"role": "system", "content": "You are a financial analysis assistant. Use the provided tools to analyze stocks thoroughly."},
                    {"role": "user", "content": analysis_prompt}
                ],
                tools=openai_tools,
                tool_choice="auto"
            )
            
            # Process the response and tool calls
            analysis_results = {}
            message = response.choices[0].message
            
            if message.tool_calls:
                logger.info(f"OpenAI requested {len(message.tool_calls)} tool executions")
                
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = eval(tool_call.function.arguments) if tool_call.function.arguments else {}
                    
                    # Add our specific parameters for each tool
                    tool_params = {"symbol": symbol}
                    
                    if tool_name == "analyze_bollinger_zscore_performance":
                        tool_params.update({"period": "1y", "window": 20})
                    elif tool_name == "analyze_bollinger_fibonacci_performance":
                        tool_params.update({
                            "period": "1y", "window": 20, "num_std": 2,
                            "fibonacci_levels": [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
                        })
                    elif tool_name == "analyze_macd_donchian_performance":
                        tool_params.update({
                            "period": "1y",
                            "macd_params": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
                            "donchian_window": 20
                        })
                    elif tool_name == "analyze_connors_zscore_performance":
                        tool_params.update({
                            "period": "1y",
                            "connors_params": {"rsi_period": 3, "streak_period": 2, "rank_period": 100},
                            "zscore_window": 20
                        })
                    elif tool_name == "analyze_dual_ma_strategy":
                        tool_params.update({
                            "period": "1y", "short_period": 50, "long_period": 200, "ma_type": "EMA"
                        })
                    
                    # Execute the tool
                    logger.info(f"Executing {tool_name} with parameters: {tool_params}")
                    result = await self.execute_mcp_tool(tool_name, tool_params)
                    
                    if result:
                        # Map tool names to our internal keys
                        key_mapping = {
                            "analyze_bollinger_zscore_performance": "bollinger_zscore",
                            "analyze_bollinger_fibonacci_performance": "bollinger_fibonacci",
                            "analyze_macd_donchian_performance": "macd_donchian",
                            "analyze_connors_zscore_performance": "connors_zscore",
                            "analyze_dual_ma_strategy": "dual_ma"
                        }
                        
                        analysis_key = key_mapping.get(tool_name, tool_name)
                        analysis_results[analysis_key] = result
                        logger.info(f"Successfully executed {tool_name}")
                    else:
                        logger.warning(f"No result from {tool_name}")
            
            if not analysis_results:
                return {"error": "No analysis results obtained from OpenAI tool calls"}
            
            return {
                "symbol": symbol,
                "analyses": analysis_results,
                "timestamp": datetime.now().isoformat(),
                "total_strategies": len(analysis_results),
                "openai_summary": message.content or "Analysis completed via tool calls"
            }
            
        except Exception as e:
            logger.error(f"Error in OpenAI analysis: {e}")
            return {"error": f"OpenAI analysis failed: {str(e)}"}
    
    async def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        """Run comprehensive analysis on a stock symbol using OpenAI with MCP tools"""
        symbol = symbol.upper().strip()
        
        if not self.validate_symbol(symbol):
            return {"error": f"Invalid or non-existent symbol: {symbol}"}
        
        logger.info(f"Starting comprehensive OpenAI-powered analysis for {symbol}")
        
        # Use OpenAI to orchestrate the analysis
        analysis_data = await self.analyze_with_openai(symbol)
        
        return analysis_data
    
    async def generate_final_report_with_ai(self, symbol: str, analysis_data: Dict[str, Any]) -> str:
        """Use OpenAI to generate a comprehensive final report from all strategy analyses"""
        try:
            # Prepare all individual analysis results
            individual_analyses = []
            strategy_names = {
                "bollinger_zscore": "Bollinger Z-Score Performance Analysis",
                "bollinger_fibonacci": "Bollinger-Fibonacci Performance Analysis", 
                "macd_donchian": "MACD-Donchian Performance Analysis",
                "connors_zscore": "Connors RSI + Z-Score Performance Analysis",
                "dual_ma": "Dual Moving Average Strategy Analysis"
            }
            
            for strategy_key, analysis_result in analysis_data["analyses"].items():
                strategy_name = strategy_names.get(strategy_key, strategy_key.title())
                individual_analyses.append(f"### {strategy_name}\n\n{analysis_result}")
            
            # Get current price for context
            try:
                ticker = yf.Ticker(symbol)
                current_price = ticker.history(period="1d")['Close'].iloc[-1]
                price_info = f"${current_price:.2f}"
            except:
                price_info = "N/A"
            
            # Create comprehensive prompt for final analysis
            final_analysis_prompt = f"""You are a senior financial analyst tasked with creating a comprehensive technical analysis report for {symbol}. 

I have conducted 5 different technical analysis strategies on {symbol} and need you to:

1. **Analyze all the individual strategy results** and extract key metrics
2. **Create a performance summary table** with actual numbers from the analyses
3. **Provide a comprehensive final recommendation** based on the collective insights
4. **Generate the complete report in markdown format**

## Context:
- **Symbol:** {symbol}
- **Current Price:** {price_info}
- **Analysis Period:** 1 Year
- **Number of Strategies:** {analysis_data['total_strategies']}

## Individual Strategy Analysis Results:

{chr(10).join(individual_analyses)}

## Instructions for Your Report:

Please create a complete markdown report with the following structure:

1. **Header Section** with symbol, price, date, etc.
2. **Executive Summary** explaining what was analyzed
3. **Performance Summary Table** - Extract the actual metrics from each strategy:
   - Strategy Name
   - Total Return (%)
   - Sharpe Ratio
   - Max Drawdown (%)
   - Win Rate (%)
   - Current Signal (BUY/SELL/HOLD)

4. **Strategy Consensus Analysis** - Analyze the signals:
   - How many strategies recommend BUY vs SELL vs HOLD
   - Which strategies are performing best/worst
   - Any conflicting signals and why

5. **Risk Assessment** - Based on the metrics:
   - Overall volatility assessment
   - Drawdown analysis
   - Risk-adjusted return evaluation

6. **Final Investment Recommendation** - Your professional opinion:
   - Overall market signal (BULLISH/BEARISH/NEUTRAL)
   - Confidence level
   - Specific action recommendations
   - Position sizing guidance
   - Risk management suggestions
   - Key levels to monitor

7. **Strategic Insights** - Higher-level analysis:
   - Market environment assessment
   - Which strategy types work best for this stock
   - Economic or sector considerations
   - Time horizon recommendations

Please make the report professional, actionable, and insightful. Extract all numerical data accurately from the individual analyses. Provide clear reasoning for your recommendations.

Focus on creating value through synthesis and interpretation rather than just summarizing the individual results.
"""

            # Make the OpenAI API call for final report generation
            response = self.openai_client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4"),
                messages=[
                    {"role": "system", "content": "You are a senior financial analyst specializing in technical analysis. Create comprehensive, professional investment reports based on multiple strategy analyses."},
                    {"role": "user", "content": final_analysis_prompt}
                ],
                max_tokens=4000,
                temperature=0.3  # Lower temperature for more consistent, factual analysis
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating AI final report: {e}")
            return f"# Technical Analysis Report: {symbol}\n\nError generating comprehensive report: {str(e)}"

    async def generate_markdown_report(self, analysis_data: Dict[str, Any]) -> str:
        """Generate comprehensive markdown report using AI analysis of all strategy results"""
        symbol = analysis_data["symbol"]
        
        # Use AI to generate the complete final report
        return await self.generate_final_report_with_ai(symbol, analysis_data)
    
    def save_report(self, report: str, symbol: str) -> str:
        """Save the markdown report to analysis folder"""
        # Create analysis directory if it doesn't exist
        analysis_dir = Path("analysis")
        analysis_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Technical_analysis_{symbol}_{timestamp}.md"
        filepath = analysis_dir / filename
        
        # Save the report
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"Report saved to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return ""


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="AI-Powered Stock Technical Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python stock_analyzer.py AAPL
  python stock_analyzer.py MSFT
  python stock_analyzer.py TSLA

Environment Variables Required:
  OPENAI_API_KEY: Your OpenAI API key
  OPENAI_MODEL: OpenAI model to use (default: gpt-4)
        """
    )
    parser.add_argument("symbol", help="Yahoo Finance stock symbol (e.g., AAPL, MSFT, TSLA)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable is required")
        print("❌ Error: OpenAI API key not found")
        print("Please set the OPENAI_API_KEY environment variable in your .env file")
        return 1
    
    try:
        analyzer = StockAnalyzer()
    except ValueError as e:
        logger.error(f"Initialization error: {e}")
        print(f"❌ Error: {e}")
        return 1
    
    try:
        # Connect to MCP server
        if not await analyzer.connect_to_mcp_server():
            logger.error("Failed to connect to MCP server. Exiting.")
            print("❌ Error: Could not connect to finance tools MCP server")
            return 1
        
        print(f"\n🤖 Starting AI-powered technical analysis for {args.symbol.upper()}...")
        print("Using OpenAI with MCP finance tools...")
        print("This may take a few moments...\n")
        
        # Analyze the stock
        analysis_data = await analyzer.analyze_stock(args.symbol)
        
        if "error" in analysis_data:
            logger.error(analysis_data["error"])
            print(f"❌ Analysis failed: {analysis_data['error']}")
            return 1
        
        # Generate and save report using AI
        report = await analyzer.generate_markdown_report(analysis_data)
        filepath = analyzer.save_report(report, analysis_data["symbol"])
        
        if filepath:
            print(f"✅ AI-powered analysis completed successfully!")
            print(f"📊 Report saved to: {filepath}")
            print(f"📈 Strategies analyzed: {analysis_data['total_strategies']}")
            print(f"🤖 Analysis enhanced with OpenAI insights")
        else:
            print("❌ Error saving report")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        return 1
    finally:
        await analyzer.disconnect_from_mcp_server()
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
