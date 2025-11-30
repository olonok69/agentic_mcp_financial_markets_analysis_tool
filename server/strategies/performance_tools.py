"""
Performance comparison tools for all trading strategies.
This module provides backtesting and performance analysis for each strategy.

STRATEGIES INCLUDED (4 total):
1. Bollinger Bands & Fibonacci Retracement
2. MACD-Donchian Combined
3. Connors RSI & Z-Score Combined
4. Dual Moving Average Crossover

NOTE: Bollinger Z-Score is intentionally NOT included in comprehensive analysis.
"""

import re
from datetime import datetime
from typing import Dict, List

import numpy as np
import pandas as pd
import yfinance as yf

# Store strategy functions for comprehensive analysis
STRATEGY_FUNCTIONS: Dict = {}


def calculate_strategy_performance_metrics(data: pd.DataFrame, signal_column: str) -> Dict:
    """Calculate comprehensive performance metrics for a strategy"""
    
    # Calculate daily returns
    data = data.copy()
    data['Daily_Return'] = data['Close'].pct_change()
    
    # Calculate strategy returns (assumes we're in position when signal is BUY)
    data['Position'] = 0
    data.loc[data[signal_column] == 'BUY', 'Position'] = 1
    data.loc[data[signal_column] == 'SELL', 'Position'] = -1
    
    # Forward fill positions (stay in position until next signal)
    data['Position'] = data['Position'].replace(0, np.nan).ffill().fillna(0)
    
    # Strategy returns = position * daily return (shifted to avoid look-ahead bias)
    data['Strategy_Return'] = data['Position'].shift(1) * data['Daily_Return']
    
    # Calculate cumulative returns
    data['Cumulative_Strategy'] = (1 + data['Strategy_Return'].fillna(0)).cumprod()
    data['Cumulative_BuyHold'] = (1 + data['Daily_Return'].fillna(0)).cumprod()
    
    # Performance metrics
    strategy_return = data['Cumulative_Strategy'].iloc[-1] - 1
    buyhold_return = data['Cumulative_BuyHold'].iloc[-1] - 1
    excess_return = strategy_return - buyhold_return
    
    # Risk metrics
    strategy_volatility = data['Strategy_Return'].std() * np.sqrt(252)
    buyhold_volatility = data['Daily_Return'].std() * np.sqrt(252)
    
    # Sharpe Ratio (assuming 0% risk-free rate for simplicity)
    strategy_sharpe = (data['Strategy_Return'].mean() * 252) / strategy_volatility if strategy_volatility > 0 else 0
    buyhold_sharpe = (data['Daily_Return'].mean() * 252) / buyhold_volatility if buyhold_volatility > 0 else 0
    
    # Maximum Drawdown
    strategy_cummax = data['Cumulative_Strategy'].cummax()
    strategy_drawdown = (data['Cumulative_Strategy'] - strategy_cummax) / strategy_cummax
    strategy_max_dd = strategy_drawdown.min()
    
    buyhold_cummax = data['Cumulative_BuyHold'].cummax()
    buyhold_drawdown = (data['Cumulative_BuyHold'] - buyhold_cummax) / buyhold_cummax
    buyhold_max_dd = buyhold_drawdown.min()
    
    # Win rate calculation
    trades = data[data[signal_column].isin(['BUY', 'SELL'])].copy()
    if len(trades) > 1:
        trades['Trade_Return'] = trades['Close'].pct_change()
        winning_trades = (trades['Trade_Return'] > 0).sum()
        total_trades = len(trades) - 1
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        avg_trade_return = trades['Trade_Return'].mean()
    else:
        win_rate = 0
        total_trades = 0
        avg_trade_return = 0
    
    return {
        'strategy_return': strategy_return,
        'buyhold_return': buyhold_return,
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


# =============================================================================
# BOLLINGER Z-SCORE PERFORMANCE TOOL
# Note: This tool is still registered but NOT used in comprehensive analysis
# =============================================================================

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

    STRATEGY_FUNCTIONS["bollinger_zscore"] = analyze_bollinger_zscore_performance


# =============================================================================
# BOLLINGER-FIBONACCI PERFORMANCE TOOL (STRATEGY 1)
# =============================================================================

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
        num_std (int): Standard deviations for bands
        window_swing_points (int): Window for swing point detection
        
        Returns:
        str: Performance comparison report
        """
        try:
            # Fetch data
            data = yf.download(symbol, period=period, progress=False, multi_level_index=False)
            if data.empty:
                return f"Error: No data found for symbol {symbol}"
            
            # Calculate Bollinger Bands
            closes = data["Close"]
            rolling_mean = closes.rolling(window=window).mean()
            rolling_std = closes.rolling(window=window).std()
            upper_band = rolling_mean + (num_std * rolling_std)
            lower_band = rolling_mean - (num_std * rolling_std)
            
            # Calculate %B (position within bands)
            percent_b = (closes - lower_band) / (upper_band - lower_band)
            
            # Generate Bollinger-Fibonacci score
            bb_score = (0.5 - percent_b) * 100  # Inverted: oversold = positive
            
            # Generate signals
            data['BB_Score'] = bb_score
            data['Signal'] = None
            data.loc[bb_score > 25, 'Signal'] = 'BUY'   # Oversold
            data.loc[bb_score < -25, 'Signal'] = 'SELL'  # Overbought
            
            # Calculate performance metrics
            metrics = calculate_strategy_performance_metrics(data, 'Signal')
            
            # Generate report
            report = format_performance_report(metrics, "Bollinger-Fibonacci", symbol, period)
            
            # Add current signal
            current_bb_score = bb_score.iloc[-1] if not bb_score.isna().iloc[-1] else 0
            current_percent_b = percent_b.iloc[-1] if not percent_b.isna().iloc[-1] else 0.5
            current_signal = "BUY" if current_bb_score > 25 else "SELL" if current_bb_score < -25 else "HOLD"
            
            report += f"""
CURRENT STATUS:
• Current %B: {current_percent_b:.2%}
• Current BB Score: {current_bb_score:.2f}
• Current Signal: {current_signal}
• Band Position: {"Below Lower Band (Oversold)" if current_percent_b < 0 else "Above Upper Band (Overbought)" if current_percent_b > 1 else "Within Bands"}
• Strategy Recommendation: {"Enter Long Position" if current_signal == "BUY" else "Enter Short Position" if current_signal == "SELL" else "Hold Current Position"}
            """
            
            return report
            
        except Exception as e:
            return f"Error analyzing {symbol}: {str(e)}"

    STRATEGY_FUNCTIONS["bollinger_fibonacci"] = analyze_bollinger_fibonacci_performance


# =============================================================================
# MACD-DONCHIAN PERFORMANCE TOOL (STRATEGY 2)
# =============================================================================

def add_macd_donchian_performance_tool(mcp):
    """Add performance comparison tool for MACD-Donchian strategy"""
    
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
        Analyze MACD-Donchian strategy performance vs Buy & Hold
        
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
            
            # Calculate Donchian Channels
            upper_channel = data["High"].rolling(window=window).max()
            lower_channel = data["Low"].rolling(window=window).min()
            channel_mid = (upper_channel + lower_channel) / 2
            
            # Position within Donchian channel (0 to 1)
            position_pct = (data["Close"] - lower_channel) / (upper_channel - lower_channel)
            
            # Calculate MACD score
            typical_range = macd_line.std() * 3
            if typical_range == 0:
                typical_range = 0.001
            
            line_position = (macd_line - signal_line) / typical_range
            macd_score = line_position.clip(-1, 1) * 50
            
            # Calculate Donchian score
            donchian_score = (position_pct - 0.5) * 100
            
            # Combined score
            combined_score = (macd_score * 0.6) + (donchian_score * 0.4)
            
            # Generate signals
            data['Combined_Score'] = combined_score
            data['Signal'] = None
            data.loc[combined_score > 25, 'Signal'] = 'BUY'
            data.loc[combined_score < -25, 'Signal'] = 'SELL'
            
            # Calculate performance metrics
            metrics = calculate_strategy_performance_metrics(data, 'Signal')
            
            # Generate report
            report = format_performance_report(metrics, "MACD-Donchian", symbol, period)
            
            # Current values
            current_macd_score = macd_score.iloc[-1] if not macd_score.isna().iloc[-1] else 0
            current_donchian_score = donchian_score.iloc[-1] if not donchian_score.isna().iloc[-1] else 0
            current_combined = combined_score.iloc[-1] if not combined_score.isna().iloc[-1] else 0
            current_signal = "BUY" if current_combined > 25 else "SELL" if current_combined < -25 else "HOLD"
            
            report += f"""
CURRENT STATUS:
• Current MACD Score: {current_macd_score:.2f}
• Current Donchian Score: {current_donchian_score:.2f}
• Combined Score: {current_combined:.2f}
• Current Signal: {current_signal}
• MACD Position: {"Above Signal" if macd_line.iloc[-1] > signal_line.iloc[-1] else "Below Signal"}
• Donchian Position: {position_pct.iloc[-1]:.2%} of channel range
• Strategy Recommendation: {"Enter Long Position" if current_signal == "BUY" else "Enter Short Position" if current_signal == "SELL" else "Hold Current Position"}
            """
            
            return report
            
        except Exception as e:
            return f"Error analyzing MACD-Donchian strategy for {symbol}: {str(e)}"

    STRATEGY_FUNCTIONS["macd_donchian"] = analyze_macd_donchian_performance


# =============================================================================
# CONNORS RSI-ZSCORE PERFORMANCE TOOL (STRATEGY 3)
# =============================================================================

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
            
            close = data['Close']
            
            # Calculate RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / loss
            price_rsi = 100 - (100 / (1 + rs))
            
            # Connors RSI score (simplified)
            connors_rsi = price_rsi
            connors_score = (connors_rsi - 50) * 2  # Convert to ±100 scale
            
            # Z-Score calculation
            rolling_mean = close.rolling(window=zscore_window).mean()
            rolling_std = close.rolling(window=zscore_window).std()
            zscore = (close - rolling_mean) / rolling_std
            zscore_score = zscore.clip(-3, 3) * (100/3)
            
            # Combined score
            combined_score = (connors_score * connors_weight) + (zscore_score * zscore_weight)
            
            # Generate signals
            data['Combined_Score'] = combined_score
            data['Signal'] = None
            data.loc[combined_score > 25, 'Signal'] = 'BUY'
            data.loc[combined_score < -25, 'Signal'] = 'SELL'
            
            # Calculate performance metrics
            metrics = calculate_strategy_performance_metrics(data, 'Signal')
            
            # Generate report
            report = format_performance_report(metrics, "Connors RSI-Z Score", symbol, period)
            
            # Current values
            current_connors = connors_rsi.iloc[-1] if not connors_rsi.isna().iloc[-1] else 50
            current_zscore = zscore.iloc[-1] if not zscore.isna().iloc[-1] else 0
            current_combined = combined_score.iloc[-1] if not combined_score.isna().iloc[-1] else 0
            current_signal = "BUY" if current_combined > 25 else "SELL" if current_combined < -25 else "HOLD"
            
            report += f"""
CURRENT STATUS:
• Current Connors RSI: {current_connors:.2f}
• Current Z-Score: {current_zscore:.2f}
• Combined Score: {current_combined:.2f}
• Current Signal: {current_signal}
• Strategy Recommendation: {"Enter Long Position" if current_signal == "BUY" else "Enter Short Position" if current_signal == "SELL" else "Hold Current Position"}
            """
            
            return report
            
        except Exception as e:
            return f"Error analyzing {symbol}: {str(e)}"

    STRATEGY_FUNCTIONS["connors_zscore"] = analyze_connors_zscore_performance


# =============================================================================
# DUAL MOVING AVERAGE PERFORMANCE TOOL (STRATEGY 4)
# =============================================================================

def add_dual_ma_performance_tool(mcp):
    """Add performance comparison tool for Dual Moving Average strategy"""
    
    @mcp.tool()
    def analyze_dual_ma_strategy(
        symbol: str,
        period: str = "1y",
        short_period: int = 50,
        long_period: int = 200,
        ma_type: str = "EMA",
    ) -> str:
        """
        Analyze Dual Moving Average Crossover strategy performance vs Buy & Hold
        
        Parameters:
        symbol (str): Stock ticker symbol
        period (str): Data period for analysis
        short_period (int): Short MA period (default: 50)
        long_period (int): Long MA period (default: 200)
        ma_type (str): Moving average type - SMA or EMA (default: EMA)
        
        Returns:
        str: Performance comparison report with crossover signals
        """
        try:
            # Fetch data
            data = yf.download(symbol, period=period, progress=False, multi_level_index=False)
            if data.empty:
                return f"Error: No data found for symbol {symbol}"
            
            closes = data["Close"]
            
            # Calculate moving averages
            if ma_type.upper() == "EMA":
                short_ma = closes.ewm(span=short_period, adjust=False).mean()
                long_ma = closes.ewm(span=long_period, adjust=False).mean()
            else:  # SMA
                short_ma = closes.rolling(window=short_period).mean()
                long_ma = closes.rolling(window=long_period).mean()
            
            data['Short_MA'] = short_ma
            data['Long_MA'] = long_ma
            
            # Generate crossover signals
            data['Signal'] = None
            
            # Golden Cross (short crosses above long) = BUY
            golden_cross = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
            data.loc[golden_cross, 'Signal'] = 'BUY'
            
            # Death Cross (short crosses below long) = SELL
            death_cross = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))
            data.loc[death_cross, 'Signal'] = 'SELL'
            
            # Calculate performance metrics
            metrics = calculate_strategy_performance_metrics(data, 'Signal')
            
            # Count signals
            golden_crosses = golden_cross.sum()
            death_crosses = death_cross.sum()
            
            # Get recent signals
            signal_dates = data[data['Signal'].notna()][['Signal']].tail(5)
            recent_signals = []
            for date, row in signal_dates.iterrows():
                signal_type = "Golden Cross - BUY" if row['Signal'] == 'BUY' else "Death Cross - SELL"
                price = closes.loc[date]
                recent_signals.append(f"• {date.strftime('%Y-%m-%d')}: {signal_type} at ${price:.2f}")
            
            # Current position
            current_short = short_ma.iloc[-1]
            current_long = long_ma.iloc[-1]
            current_price = closes.iloc[-1]
            trend_strength = abs(current_short - current_long) / current_long * 100
            
            if current_short > current_long:
                current_position = "LONG"
                trend = "BULLISH 🟢"
            else:
                current_position = "SHORT"
                trend = "BEARISH 🔴"
            
            # Determine current signal based on position
            if current_position == "LONG":
                current_signal = "BUY"
            else:
                current_signal = "SELL"
            
            # Generate report
            report = f"""
DUAL MOVING AVERAGE ANALYSIS - {symbol.upper()}
{'='*50}
STRATEGY PARAMETERS:
• Moving Average Type: {ma_type.upper()}
• Short Period: {short_period} days
• Long Period: {long_period} days
• Analysis Period: {period}

CURRENT STATUS:
• Current Price: ${current_price:.2f}
• {short_period}-day {ma_type.upper()}: ${current_short:.2f}
• {long_period}-day {ma_type.upper()}: ${current_long:.2f}
• Current Position: {current_position}
• Current Signal: {current_signal}
• Trend: {trend}
• Trend Strength: {trend_strength:.2f}%

PERFORMANCE METRICS:
• Strategy Return: {metrics['strategy_return']:.2%}
• Buy & Hold Return: {metrics['buyhold_return']:.2%}
• Excess Return: {metrics['excess_return']:.2%}
• Win Rate: {metrics['win_rate']:.2%}
• Total Trades: {metrics['total_trades']}
• Sharpe Ratio: {metrics['strategy_sharpe']:.3f}
• Max Drawdown: {metrics['strategy_max_drawdown']:.2%}
• Strategy Volatility: {metrics['strategy_volatility']:.2%}

SIGNAL SUMMARY:
• Golden Cross (Buy) Signals: {golden_crosses}
• Death Cross (Sell) Signals: {death_crosses}

Recent Signals:
{chr(10).join(recent_signals) if recent_signals else "• No recent signals"}

MARKET CONDITION:
{"Strong uptrend - MAs show bullish alignment" if trend_strength > 5 and current_position == "LONG" else "Strong downtrend - MAs show bearish alignment" if trend_strength > 5 and current_position == "SHORT" else "Moderate uptrend - MAs show bullish alignment" if current_position == "LONG" else "Moderate downtrend - MAs show bearish alignment"}

STRATEGY VERDICT: {'OUTPERFORMS' if metrics['excess_return'] > 0 else 'UNDERPERFORMS'} Buy & Hold
"""
            
            return report
            
        except Exception as e:
            return f"Error analyzing Dual MA strategy for {symbol}: {str(e)}"

    STRATEGY_FUNCTIONS["dual_ma"] = analyze_dual_ma_strategy


# =============================================================================
# COMPREHENSIVE ANALYSIS TOOL
# This tool runs all 4 strategies (NOT including bollinger_zscore)
# =============================================================================

def add_comprehensive_analysis_tool(mcp):
    """Add tool for comprehensive multi-strategy analysis with performance comparison"""
    
    @mcp.tool()
    def generate_comprehensive_analysis_report(symbol: str, period: str = "1y") -> str:
        """
        Generate a comprehensive analysis report comparing all 4 core strategies.
        
        Strategies included:
        1. Bollinger Bands & Fibonacci Retracement
        2. MACD-Donchian Combined
        3. Connors RSI & Z-Score Combined
        4. Dual Moving Average Crossover
        
        Parameters:
        symbol (str): Stock ticker symbol to analyze
        period (str): Data period for analysis
        
        Returns:
        str: Comprehensive markdown report with all strategies and performance comparisons
        """
        try:
            data = yf.download(symbol, period="5d", progress=False, multi_level_index=False)
            current_price_value = data['Close'].iloc[-1] if not data.empty else None
        except Exception:
            current_price_value = None

        analysis_date = datetime.now().strftime("%B %d, %Y")
        current_price = (
            f"${current_price_value:.2f}"
            if isinstance(current_price_value, (int, float, np.floating))
            else "N/A"
        )

        signal_pattern = re.compile(r"Current Signal:\s*([A-Za-z]+)", re.IGNORECASE)
        verdict_pattern = re.compile(r"STRATEGY VERDICT:\s*([^\n]+)", re.IGNORECASE)

        def extract_value(text: str, pattern: re.Pattern, fallback: str) -> str:
            match = pattern.search(text)
            return match.group(1).strip().upper() if match else fallback

        # =================================================================
        # STRATEGIES LIST - 4 STRATEGIES (NO bollinger_zscore)
        # =================================================================
        strategies = [
            (
                "bollinger_fibonacci",
                "Bollinger Bands & Fibonacci Retracement Strategy",
                {"period": period, "window": 20, "num_std": 2, "window_swing_points": 10},
            ),
            (
                "macd_donchian",
                "MACD-Donchian Combined Strategy",
                {
                    "period": period,
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9,
                    "window": 20,
                },
            ),
            (
                "connors_zscore",
                "Connors RSI & Z-Score Combined Analysis",
                {
                    "period": period,
                    "rsi_period": 3,
                    "streak_period": 2,
                    "rank_period": 100,
                    "zscore_window": 20,
                    "connors_weight": 0.7,
                    "zscore_weight": 0.3,
                },
            ),
            (
                "dual_ma",
                "Dual Moving Average Crossover Strategy",
                {
                    "period": period,
                    "short_period": 50,
                    "long_period": 200,
                    "ma_type": "EMA",
                },
            ),
        ]

        highlights: List[str] = []
        sections: List[str] = []
        strategy_details: List[Dict[str, str]] = []

        for key, title, params in strategies:
            func = STRATEGY_FUNCTIONS.get(key)
            if not func:
                content = f"Strategy '{title}' is not registered on the MCP server."
                signal = "N/A"
                verdict = "UNAVAILABLE"
            else:
                try:
                    content = func(symbol, **params)
                    signal = extract_value(content, signal_pattern, "N/A")
                    verdict = extract_value(content, verdict_pattern, "N/A")
                except Exception as exc:
                    content = f"Error executing {title}: {exc}"
                    signal = "ERROR"
                    verdict = "ERROR"

            highlights.append(f"- **{title}**: {signal} ({verdict})")
            sections.append(f"### {title}\n\n```\n{content}\n```\n")
            strategy_details.append({"title": title, "signal": signal, "verdict": verdict})

        # Generate recommendation based on signals
        buy_count = sum(1 for d in strategy_details if d["signal"] == "BUY")
        sell_count = sum(1 for d in strategy_details if d["signal"] == "SELL")
        hold_count = sum(1 for d in strategy_details if d["signal"] == "HOLD")
        
        if buy_count > sell_count and buy_count >= 2:
            recommendation = f"**BUY** - {buy_count} out of 4 strategies signal buying opportunity."
        elif sell_count > buy_count and sell_count >= 2:
            recommendation = f"**SELL** - {sell_count} out of 4 strategies signal selling opportunity."
        else:
            recommendation = f"**HOLD** - Mixed signals ({buy_count} BUY, {sell_count} SELL, {hold_count} HOLD). Wait for clearer consensus."

        signals_breakdown = "\n".join(
            f"- **{detail['title']}** – {detail['signal']} ({detail['verdict']})"
            for detail in strategy_details
        ) or "- No strategy data available."

        report_parts = [
            f"# {symbol.upper()} Comprehensive Technical Analysis with Performance Comparison",
            f"*Analysis Date: {analysis_date}*  ",
            f"*Current Price: {current_price}*",
            "",
            "---",
            "",
            "📊 **Report Type:** Comprehensive Performance Report (Deterministic)",
            "",
            "*This report uses fixed parameters and direct calculations for consistent, reproducible results.*",
            "",
            "---",
            "",
            "## Executive Summary",
            f"This report analyzes {symbol.upper()} using 4 technical analysis strategies:",
            "1. Bollinger Bands & Fibonacci Retracement",
            "2. MACD-Donchian Combined",
            "3. Connors RSI & Z-Score Combined",
            "4. Dual Moving Average Crossover",
            "",
            "## Strategy Highlights",
            "\n".join(highlights) if highlights else "- No strategy data available.",
            "",
            "## Individual Strategy Analysis",
            "",
            "\n".join(sections).strip(),
            "",
            "## Consensus & Recommendation",
            "",
            f"**Signal Summary:** {buy_count} BUY | {sell_count} SELL | {hold_count} HOLD",
            "",
            f"**Recommendation:** {recommendation}",
            "",
            "### Signals by Strategy",
            signals_breakdown,
            "",
            "---",
            "*This report aggregates the live outputs from each individual strategy tool.*",
            "*Note: Bollinger Z-Score is not included in this comprehensive analysis.*",
        ]

        return "\n".join(part for part in report_parts if part is not None)


# =============================================================================
# REGISTER ALL TOOLS
# =============================================================================

def add_all_performance_tools(mcp):
    """Add all performance comparison tools to the MCP server"""
    add_bollinger_zscore_performance_tool(mcp)  # Still available but not in comprehensive
    add_bollinger_fibonacci_performance_tool(mcp)
    add_macd_donchian_performance_tool(mcp)
    add_connors_zscore_performance_tool(mcp)
    add_dual_ma_performance_tool(mcp)  # Added Dual MA
    add_comprehensive_analysis_tool(mcp)