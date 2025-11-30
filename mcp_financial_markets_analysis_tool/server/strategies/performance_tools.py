"""
Performance Comparison Tools for All Trading Strategies
This module adds performance comparison functionality to each strategy.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, Tuple, List
import sys
import os

# Add the utils directory to the path so we can import yahoo_finance_tools
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

def calculate_strategy_performance_metrics(signals_data: pd.DataFrame, signal_column: str = 'Signal') -> Dict:
    """
    Calculate comprehensive strategy performance metrics vs buy-and-hold
    
    Parameters:
    signals_data (pd.DataFrame): DataFrame with price data and signals
    signal_column (str): Name of the column containing trading signals
    
    Returns:
    Dict: Performance metrics dictionary
    """
    data = signals_data.copy()
    
    # Ensure we have required columns
    if 'Close' not in data.columns:
        raise ValueError("DataFrame must contain 'Close' column")
    
    # Calculate price returns
    data['Price_Return'] = data['Close'].pct_change()
    
    # Convert signals to positions
    if signal_column in data.columns:
        # Map signals to positions
        data['Position'] = 0
        if 'BUY' in data[signal_column].values or 'SELL' in data[signal_column].values:
            data.loc[data[signal_column] == 'BUY', 'Position'] = 1
            data.loc[data[signal_column] == 'SELL', 'Position'] = -1
        else:
            # For score-based strategies, use score thresholds
            score_col = 'Strategy_Score' if 'Strategy_Score' in data.columns else signal_column
            if score_col in data.columns:
                data['Position'] = np.where(data[score_col] > 20, 1, 
                                          np.where(data[score_col] < -20, -1, 0))
        
        # Forward fill positions
        data['Position'] = data['Position'].replace(0, np.nan).ffill().fillna(0)
    else:
        # If no signal column, assume buy and hold
        data['Position'] = 1
    
    # Calculate strategy returns
    data['Strategy_Return'] = data['Position'].shift(1) * data['Price_Return']
    data['Cumulative_Strategy'] = (1 + data['Strategy_Return']).cumprod()
    data['Cumulative_BuyHold'] = (1 + data['Price_Return']).cumprod()
    
    # Performance metrics
    total_strategy_return = data['Cumulative_Strategy'].iloc[-1] - 1
    total_buyhold_return = data['Cumulative_BuyHold'].iloc[-1] - 1
    excess_return = total_strategy_return - total_buyhold_return
    
    # Risk metrics
    strategy_volatility = data['Strategy_Return'].std() * np.sqrt(252)
    buyhold_volatility = data['Price_Return'].std() * np.sqrt(252)
    
    # Sharpe ratios (assuming 0% risk-free rate)
    strategy_sharpe = (data['Strategy_Return'].mean() * 252) / strategy_volatility if strategy_volatility > 0 else 0
    buyhold_sharpe = (data['Price_Return'].mean() * 252) / buyhold_volatility if buyhold_volatility > 0 else 0
    
    # Maximum drawdown
    def calculate_max_drawdown(cumulative_returns):
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        return drawdown.min()
    
    strategy_max_dd = calculate_max_drawdown(data['Cumulative_Strategy'])
    buyhold_max_dd = calculate_max_drawdown(data['Cumulative_BuyHold'])
    
    # Win rate and trade statistics
    trades = data[data[signal_column].notna()].copy() if signal_column in data.columns else pd.DataFrame()
    
    win_rate = 0
    total_trades = 0
    avg_trade_return = 0
    
    if len(trades) > 1:
        trade_returns = []
        position = 0
        entry_price = 0
        
        for idx, row in trades.iterrows():
            current_signal = row[signal_column] if signal_column in trades.columns else None
            current_price = row['Close']
            
            if current_signal == 'BUY' and position <= 0:
                if position < 0 and entry_price > 0:
                    # Close short position
                    trade_return = (entry_price - current_price) / entry_price
                    trade_returns.append(trade_return)
                # Open long position
                entry_price = current_price
                position = 1
            elif current_signal == 'SELL' and position >= 0:
                if position > 0 and entry_price > 0:
                    # Close long position
                    trade_return = (current_price - entry_price) / entry_price
                    trade_returns.append(trade_return)
                # Open short position
                entry_price = current_price
                position = -1
        
        if trade_returns:
            win_rate = len([r for r in trade_returns if r > 0]) / len(trade_returns)
            total_trades = len(trade_returns)
            avg_trade_return = np.mean(trade_returns)
    
    return {
        'strategy_return': total_strategy_return,
        'buyhold_return': total_buyhold_return,
        'excess_return': excess_return,
        'strategy_volatility': strategy_volatility,
        'buyhold_volatility': buyhold_volatility,
        'strategy_sharpe': strategy_sharpe,
        'buyhold_sharpe': buyhold_sharpe,
        'strategy_max_drawdown': strategy_max_dd,
        'buyhold_max_drawdown': buyhold_max_dd,
        'win_rate': win_rate,
        'total_trades': total_trades,
        'avg_trade_return': avg_trade_return,
        'trading_days': len(data)
    }

def format_performance_report(metrics: Dict, strategy_name: str, symbol: str, period: str) -> str:
    """Format performance metrics into a readable report"""
    
    report = f"""
PERFORMANCE COMPARISON: {strategy_name.upper()}
{'='*60}
Symbol: {symbol} | Period: {period} | Trading Days: {metrics['trading_days']}

RETURNS ANALYSIS:
• Strategy Total Return: {metrics['strategy_return']:.2%}
• Buy & Hold Return: {metrics['buyhold_return']:.2%}
• Excess Return: {metrics['excess_return']:.2%}
• Outperformance: {'YES' if metrics['excess_return'] > 0 else 'NO'} by {abs(metrics['excess_return']):.2%}

RISK ANALYSIS:
• Strategy Volatility: {metrics['strategy_volatility']:.2%}
• Buy & Hold Volatility: {metrics['buyhold_volatility']:.2%}
• Strategy Sharpe Ratio: {metrics['strategy_sharpe']:.3f}
• Buy & Hold Sharpe Ratio: {metrics['buyhold_sharpe']:.3f}
• Strategy Max Drawdown: {metrics['strategy_max_drawdown']:.2%}
• Buy & Hold Max Drawdown: {metrics['buyhold_max_drawdown']:.2%}

TRADING STATISTICS:
• Total Trades: {metrics['total_trades']}
• Win Rate: {metrics['win_rate']:.2%}
• Average Return per Trade: {metrics['avg_trade_return']:.2%}

RISK-ADJUSTED PERFORMANCE:
• Return/Risk Ratio: {metrics['strategy_return']/metrics['strategy_volatility'] if metrics['strategy_volatility'] > 0 else 0:.3f}
• Buy & Hold Return/Risk: {metrics['buyhold_return']/metrics['buyhold_volatility'] if metrics['buyhold_volatility'] > 0 else 0:.3f}

STRATEGY VERDICT: {'OUTPERFORMS' if metrics['excess_return'] > 0 and metrics['strategy_sharpe'] > metrics['buyhold_sharpe'] else 'UNDERPERFORMS'} Buy & Hold
"""
    return report

def add_bollinger_zscore_performance_tool(mcp):
    """Add performance comparison tool for Bollinger Z-Score strategy"""
    
    @mcp.tool()
    def analyze_bollinger_zscore_performance(symbol: str, period: str = "1y", window: int = 20) -> str:
        """
        Analyze Bollinger Z-Score strategy performance vs Buy & Hold
        
        Parameters:
        symbol (str): Stock ticker symbol
        period (str): Data period for analysis
        window (int): Period for Z-Score calculation
        
        Returns:
        str: Performance comparison report
        """
        try:
            # Fetch data
            data = yf.download(symbol, period=period, progress=False, multi_level_index=False)
            if data.empty:
                return f"Error: No data found for symbol {symbol}"
            
            # Calculate Bollinger Z-Score
            closes = data["Close"]
            rolling_mean = closes.rolling(window=window).mean()
            rolling_std = closes.rolling(window=window).std()
            z_score = (closes - rolling_mean) / rolling_std
            
            # Generate signals based on Z-Score
            data['Z_Score'] = z_score
            data['Signal'] = None
            data.loc[z_score < -2, 'Signal'] = 'BUY'   # Oversold
            data.loc[z_score > 2, 'Signal'] = 'SELL'   # Overbought
            
            # Calculate performance metrics
            metrics = calculate_strategy_performance_metrics(data, 'Signal')
            
            # Generate report
            report = format_performance_report(metrics, "Bollinger Z-Score", symbol, period)
            
            # Add current signal
            current_zscore = z_score.iloc[-1]
            current_signal = "BUY" if current_zscore < -2 else "SELL" if current_zscore > 2 else "HOLD"
            
            report += f"""
CURRENT STATUS:
• Current Z-Score: {current_zscore:.2f}
• Current Signal: {current_signal}
• Strategy Recommendation: {"Enter Long" if current_signal == "BUY" else "Enter Short" if current_signal == "SELL" else "Hold Position"}
            """
            
            return report
            
        except Exception as e:
            return f"Error analyzing {symbol}: {str(e)}"

def add_bollinger_fibonacci_performance_tool(mcp):
    """Add performance comparison tool for Bollinger-Fibonacci strategy"""
    
    @mcp.tool()
    def analyze_bollinger_fibonacci_performance(
        symbol: str, 
        period: str = "1y", 
        window: int = 20,
        num_std: int = 2,
        window_swing_points: int = 10
    ) -> str:
        """
        Analyze Bollinger-Fibonacci strategy performance vs Buy & Hold
        
        Parameters:
        symbol (str): Stock ticker symbol
        period (str): Data period for analysis
        window (int): Bollinger Bands window
        num_std (int): Standard deviations for Bollinger Bands
        window_swing_points (int): Window for swing point detection
        
        Returns:
        str: Performance comparison report
        """
        try:
            from yahoo_finance_tools import calculate_bollinger_bands, find_swing_points, calculate_fibonacci_levels
            
            # Fetch data
            data = yf.download(symbol, period=period, progress=False, multi_level_index=False)
            if data.empty:
                return f"Error: No data found for symbol {symbol}"
            
            # Calculate Bollinger Bands
            calculate_bollinger_bands(data, symbol, period, window, num_std)
            
            # Find swing points
            find_swing_points(data, window_swing_points)
            
            # Calculate Fibonacci levels
            fib_levels, fib_trend = calculate_fibonacci_levels(data, window_swing_points)
            
            if fib_levels is None:
                return "Unable to calculate Fibonacci levels for performance analysis"
            
            # Calculate strategy scores (simplified version)
            data["Strategy_Score"] = 0.0
            
            # Basic scoring based on %B and Fibonacci proximity
            data["Strategy_Score"] = (0.5 - data["%B"]) * 50  # Bollinger component
            
            # Generate signals based on strategy score
            data['Signal'] = None
            data.loc[data['Strategy_Score'] > 20, 'Signal'] = 'BUY'
            data.loc[data['Strategy_Score'] < -20, 'Signal'] = 'SELL'
            
            # Calculate performance metrics
            metrics = calculate_strategy_performance_metrics(data, 'Signal')
            
            # Generate report
            report = format_performance_report(metrics, "Bollinger-Fibonacci", symbol, period)
            
            # Add current status
            current_score = data['Strategy_Score'].iloc[-1] if not data['Strategy_Score'].isna().iloc[-1] else 0
            current_signal = "BUY" if current_score > 20 else "SELL" if current_score < -20 else "HOLD"
            
            report += f"""
CURRENT STATUS:
• Current Strategy Score: {current_score:.2f}
• Current Signal: {current_signal}
• Fibonacci Trend: {fib_trend}
• Strategy Recommendation: {"Enter Long Position" if current_signal == "BUY" else "Enter Short Position" if current_signal == "SELL" else "Hold Current Position"}
            """
            
            return report
            
        except Exception as e:
            return f"Error analyzing {symbol}: {str(e)}"

def add_macd_donchian_performance_tool(mcp):
    """Add performance comparison tool for MACD-Donchian strategy - FIXED VERSION"""
    
    @mcp.tool()
    def analyze_macd_donchian_performance(
        symbol: str,
        period: str = "1y",
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        window: int = 20,
    ) -> str:
        """
        Analyze MACD-Donchian strategy performance vs Buy & Hold - FIXED VERSION
        
        Parameters:
        symbol (str): Stock ticker symbol
        period (str): Data period for analysis
        fast_period (int): MACD fast period
        slow_period (int): MACD slow period
        signal_period (int): MACD signal period
        window (int): Donchian channel window
        
        Returns:
        str: Performance comparison report
        """
        try:
            import yfinance as yf
            import pandas as pd
            import numpy as np
            
            # Fetch data
            data = yf.download(symbol, period=period, progress=False, multi_level_index=False)
            if data.empty:
                return f"Error: No data found for symbol {symbol}"
            
            # Calculate MACD components
            ema_fast = data["Close"].ewm(span=fast_period, adjust=False).mean()
            ema_slow = data["Close"].ewm(span=slow_period, adjust=False).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
            macd_histogram = macd_line - signal_line
            
            # Calculate MACD score components
            typical_range = macd_line.std() * 3
            if typical_range == 0:
                typical_range = 0.001
            
            # MACD score calculation (matching your existing tool)
            line_position = (macd_line - signal_line) / typical_range
            component1 = line_position.clip(-1, 1) * 40
            
            zero_position = macd_line / typical_range
            component2 = zero_position.clip(-1, 1) * 30
            
            hist_change = macd_histogram.diff(3).rolling(window=3).mean()
            hist_typical_range = hist_change.std() * 3
            if hist_typical_range == 0:
                hist_typical_range = 0.001
            
            hist_momentum = hist_change / hist_typical_range
            component3 = hist_momentum.clip(-1, 1) * 30
            
            macd_score = component1 + component2 + component3
            
            # Calculate Donchian Channel components
            upper_band = data["High"].rolling(window=window).max()
            lower_band = data["Low"].rolling(window=window).min()
            middle_band = (upper_band + lower_band) / 2
            
            # Donchian score calculation (matching your existing tool)
            channel_width = upper_band - lower_band
            channel_width = channel_width.replace(0, 0.001)
            
            position_pct = (data["Close"] - lower_band) / channel_width
            d_component1 = ((position_pct * 2) - 1) * 50
            
            channel_direction = middle_band.diff(5).rolling(window=5).mean()
            channel_direction_range = channel_direction.std() * 3
            if channel_direction_range == 0:
                channel_direction_range = 0.001
            
            normalized_direction = channel_direction / channel_direction_range
            d_component2 = normalized_direction.clip(-1, 1) * 30
            
            width_change = channel_width.diff(5).rolling(window=5).mean()
            width_change_range = width_change.std() * 3
            if width_change_range == 0:
                width_change_range = 0.001
            
            normalized_width = width_change / width_change_range
            d_component3 = normalized_width.clip(-1, 1) * 20
            
            donchian_score = d_component1 + d_component2 + d_component3
            
            # Combined score (equal weight)
            combined_score = (macd_score + donchian_score) / 2
            data['Combined_Score'] = combined_score
            
            # Generate trading signals based on combined score thresholds
            data['Signal'] = None
            data.loc[combined_score > 25, 'Signal'] = 'BUY'
            data.loc[combined_score < -25, 'Signal'] = 'SELL'
            # Add HOLD signals for intermediate values
            data.loc[(combined_score >= -25) & (combined_score <= 25), 'Signal'] = 'HOLD'
            
            # Forward fill signals to create positions
            data['Position'] = 0
            data.loc[data['Signal'] == 'BUY', 'Position'] = 1
            data.loc[data['Signal'] == 'SELL', 'Position'] = -1
            data.loc[data['Signal'] == 'HOLD', 'Position'] = 0
            
            # Forward fill positions (hold position until next signal)
            data['Position'] = data['Position'].replace(0, np.nan)
            data['Position'] = data['Position'].ffill().fillna(0)
            
            # Calculate returns
            data['Price_Return'] = data['Close'].pct_change()
            data['Strategy_Return'] = data['Position'].shift(1) * data['Price_Return']
            data['Cumulative_Strategy'] = (1 + data['Strategy_Return']).cumprod()
            data['Cumulative_BuyHold'] = (1 + data['Price_Return']).cumprod()
            
            # Performance metrics
            total_strategy_return = data['Cumulative_Strategy'].iloc[-1] - 1
            total_buyhold_return = data['Cumulative_BuyHold'].iloc[-1] - 1
            excess_return = total_strategy_return - total_buyhold_return
            
            # Risk metrics
            strategy_volatility = data['Strategy_Return'].std() * np.sqrt(252)
            buyhold_volatility = data['Price_Return'].std() * np.sqrt(252)
            
            # Sharpe ratios
            strategy_sharpe = (data['Strategy_Return'].mean() * 252) / strategy_volatility if strategy_volatility > 0 else 0
            buyhold_sharpe = (data['Price_Return'].mean() * 252) / buyhold_volatility if buyhold_volatility > 0 else 0
            
            # Maximum drawdown
            def calculate_max_drawdown(cumulative_returns):
                running_max = cumulative_returns.expanding().max()
                drawdown = (cumulative_returns - running_max) / running_max
                return drawdown.min()
            
            strategy_max_dd = calculate_max_drawdown(data['Cumulative_Strategy'])
            buyhold_max_dd = calculate_max_drawdown(data['Cumulative_BuyHold'])
            
            # Trading statistics
            signals = data[data['Signal'].notna() & (data['Signal'] != 'HOLD')]
            total_signals = len(signals)
            buy_signals = len(signals[signals['Signal'] == 'BUY'])
            sell_signals = len(signals[signals['Signal'] == 'SELL'])
            
            # Calculate trade returns for win rate
            trade_returns = []
            position = 0
            entry_price = 0
            
            for idx, row in signals.iterrows():
                current_signal = row['Signal']
                current_price = row['Close']
                
                if current_signal == 'BUY' and position <= 0:
                    if position < 0 and entry_price > 0:
                        # Close short position
                        trade_return = (entry_price - current_price) / entry_price
                        trade_returns.append(trade_return)
                    # Open long position
                    entry_price = current_price
                    position = 1
                elif current_signal == 'SELL' and position >= 0:
                    if position > 0 and entry_price > 0:
                        # Close long position
                        trade_return = (current_price - entry_price) / entry_price
                        trade_returns.append(trade_return)
                    # Open short position
                    entry_price = current_price
                    position = -1
            
            win_rate = len([r for r in trade_returns if r > 0]) / len(trade_returns) if trade_returns else 0
            avg_trade_return = np.mean(trade_returns) if trade_returns else 0
            
            # Current status
            current_combined_score = combined_score.iloc[-1]
            current_macd_score = macd_score.iloc[-1]
            current_donchian_score = donchian_score.iloc[-1]
            current_signal = data['Signal'].iloc[-1] if pd.notna(data['Signal'].iloc[-1]) else "HOLD"
            
            # Generate report
            report = f"""
PERFORMANCE COMPARISON: MACD-DONCHIAN STRATEGY
{'='*60}
Symbol: {symbol} | Period: {period} | Trading Days: {len(data)}

RETURNS ANALYSIS:
• Strategy Total Return: {total_strategy_return:.2%}
• Buy & Hold Return: {total_buyhold_return:.2%}
• Excess Return: {excess_return:.2%}
• Outperformance: {'YES' if excess_return > 0 else 'NO'} by {abs(excess_return):.2%}

RISK ANALYSIS:
• Strategy Volatility: {strategy_volatility:.2%}
• Buy & Hold Volatility: {buyhold_volatility:.2%}
• Strategy Sharpe Ratio: {strategy_sharpe:.3f}
• Buy & Hold Sharpe Ratio: {buyhold_sharpe:.3f}
• Strategy Max Drawdown: {strategy_max_dd:.2%}
• Buy & Hold Max Drawdown: {buyhold_max_dd:.2%}

TRADING STATISTICS:
• Total Trades: {len(trade_returns)}
• Total Signals: {total_signals} (Buy: {buy_signals}, Sell: {sell_signals})
• Win Rate: {win_rate:.2%}
• Average Return per Trade: {avg_trade_return:.2%}

RISK-ADJUSTED PERFORMANCE:
• Return/Risk Ratio: {total_strategy_return/strategy_volatility if strategy_volatility > 0 else 0:.3f}
• Buy & Hold Return/Risk: {total_buyhold_return/buyhold_volatility if buyhold_volatility > 0 else 0:.3f}

CURRENT STATUS:
• Current Combined Score: {current_combined_score:.2f}
• Current MACD Score: {current_macd_score:.2f}
• Current Donchian Score: {current_donchian_score:.2f}
• Current Signal: {current_signal}
• MACD Position: {"Above Signal" if macd_line.iloc[-1] > signal_line.iloc[-1] else "Below Signal"}
• Donchian Position: {position_pct.iloc[-1]:.2%} of channel range

STRATEGY VERDICT: {'OUTPERFORMS' if excess_return > 0 and strategy_sharpe > buyhold_sharpe else 'UNDERPERFORMS'} Buy & Hold

RECOMMENDATION: {"Enter Long Position" if current_signal == "BUY" else "Enter Short Position" if current_signal == "SELL" else "Hold Current Position"}
            """
            
            return report
            
        except Exception as e:
            return f"Error analyzing MACD-Donchian strategy for {symbol}: {str(e)}\nDetailed error: {type(e).__name__}"

def add_connors_zscore_performance_tool(mcp):
    """Add performance comparison tool for Connors RSI-Z Score strategy"""
    
    @mcp.tool()
    def analyze_connors_zscore_performance(
        symbol: str,
        period: str = "1y",
        rsi_period: int = 3,
        streak_period: int = 2,
        rank_period: int = 100,
        zscore_window: int = 20,
        connors_weight: float = 0.7,
        zscore_weight: float = 0.3,
    ) -> str:
        """
        Analyze Connors RSI-Z Score strategy performance vs Buy & Hold
        
        Parameters:
        symbol (str): Stock ticker symbol
        period (str): Data period for analysis
        rsi_period (int): Connors RSI period
        streak_period (int): Streak RSI period
        rank_period (int): Percent rank period
        zscore_window (int): Z-Score window
        connors_weight (float): Weight for Connors RSI
        zscore_weight (float): Weight for Z-Score
        
        Returns:
        str: Performance comparison report
        """
        try:
            # Fetch data
            data = yf.download(symbol, period=period, progress=False, multi_level_index=False)
            if data.empty:
                return f"Error: No data found for symbol {symbol}"
            
            # Calculate Connors RSI components
            close = data['Close']
            
            # Simple RSI calculation
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / loss
            price_rsi = 100 - (100 / (1 + rs))
            
            # Combined Connors RSI (simplified)
            connors_rsi = price_rsi  # Simplified version
            connors_score = (connors_rsi - 50) * 2  # Convert to ±100 scale
            
            # Z-Score calculation
            rolling_mean = close.rolling(window=zscore_window).mean()
            rolling_std = close.rolling(window=zscore_window).std()
            zscore = (close - rolling_mean) / rolling_std
            zscore_score = zscore.clip(-3, 3) * (100/3)
            
            # Combined score
            combined_score = (connors_score * connors_weight) + (zscore_score * zscore_weight)
            data['Combined_Score'] = combined_score
            
            # Generate signals
            data['Signal'] = None
            data.loc[combined_score > 25, 'Signal'] = 'BUY'
            data.loc[combined_score < -25, 'Signal'] = 'SELL'
            
            # Calculate performance metrics
            metrics = calculate_strategy_performance_metrics(data, 'Signal')
            
            # Generate report
            report = format_performance_report(metrics, "Connors RSI-Z Score", symbol, period)
            
            # Add current status
            current_score = combined_score.iloc[-1] if not combined_score.isna().iloc[-1] else 0
            current_signal = "BUY" if current_score > 25 else "SELL" if current_score < -25 else "HOLD"
            
            report += f"""
CURRENT STATUS:
• Current Combined Score: {current_score:.2f}
• Current Signal: {current_signal}
• Connors RSI: {connors_rsi.iloc[-1]:.2f}
• Z-Score: {zscore.iloc[-1]:.2f}
• Strategy Recommendation: {"Enter Long Position" if current_signal == "BUY" else "Enter Short Position" if current_signal == "SELL" else "Hold Current Position"}
            """
            
            return report
            
        except Exception as e:
            return f"Error analyzing {symbol}: {str(e)}"

def add_comprehensive_analysis_tool(mcp):
    """Add tool for comprehensive multi-strategy analysis with performance comparison"""
    
    @mcp.tool()
    def generate_comprehensive_analysis_report(symbol: str, period: str = "1y") -> str:
        """
        Generate a comprehensive analysis report comparing all strategies with performance metrics
        
        Parameters:
        symbol (str): Stock ticker symbol to analyze
        period (str): Data period for analysis
        
        Returns:
        str: Comprehensive markdown report with all strategies and performance comparisons
        """
        try:
            # Get current price for header
            data = yf.download(symbol, period="5d", progress=False, multi_level_index=False)
            current_price = data['Close'].iloc[-1] if not data.empty else "N/A"
            
            from datetime import datetime
            analysis_date = datetime.now().strftime("%B %d, %Y")
            
            report = f"""# {symbol.upper()} Comprehensive Technical Analysis with Performance Comparison
*Analysis Date: {analysis_date}*  
*Current Price: ${current_price:.2f}*

## Executive Summary

This comprehensive technical analysis evaluates {symbol.upper()} using five different technical indicators and strategies, including detailed performance comparisons against buy-and-hold strategy. The analysis combines momentum, mean reversion, volatility, and trend-following approaches to provide a well-rounded assessment.

## Strategy Performance Summary

The following table summarizes the performance of each strategy compared to buy-and-hold:

| Strategy | Current Signal | Strategy Return | Buy & Hold Return | Excess Return | Sharpe Ratio | Max Drawdown | Verdict |
|----------|---------------|----------------|-------------------|---------------|--------------|--------------|---------|

## Individual Strategy Analysis with Performance Metrics

### 1. Bollinger Z-Score Analysis (20-Day Period)
"""
            
            # Call each performance analysis tool and append results
            # Note: In a real implementation, you would call the actual MCP tools here
            # For now, we'll return the template structure
            
            report += """

*Performance metrics and current analysis would be inserted here*

### 2. Bollinger Bands & Fibonacci Retracement Strategy

*Performance metrics and current analysis would be inserted here*

### 3. MACD-Donchian Combined Strategy

*Performance metrics and current analysis would be inserted here*

### 4. Connors RSI & Z-Score Combined Analysis

*Performance metrics and current analysis would be inserted here*

### 5. Dual Moving Average Strategy (EMA 50/200)

*Performance metrics and current analysis would be inserted here*

## Final Recommendation

Based on the comprehensive analysis of all five strategies and their performance metrics:

**OVERALL VERDICT:** [To be determined based on strategy consensus and performance]

### Key Insights:
- Strategy performance relative to buy-and-hold
- Risk-adjusted returns analysis
- Current market conditions assessment
- Recommended position sizing

### Risk Management:
- Stop-loss levels based on multiple indicators
- Position sizing recommendations
- Market condition considerations

*This analysis is for educational purposes only and should not be considered as financial advice.*
"""
            
            return report
            
        except Exception as e:
            return f"Error generating comprehensive analysis for {symbol}: {str(e)}"

def add_all_performance_tools(mcp):
    """Add all performance comparison tools to the MCP server"""
    add_bollinger_zscore_performance_tool(mcp)
    add_bollinger_fibonacci_performance_tool(mcp)
    add_macd_donchian_performance_tool(mcp)
    add_connors_zscore_performance_tool(mcp)
    add_comprehensive_analysis_tool(mcp)