"""
Bollinger Z-Score Strategy Module for MCP Server

This module implements the Bollinger Z-Score indicator for mean reversion analysis.
"""

import pandas as pd
import numpy as np
import yfinance as yf


def register_bollinger_zscore_tools(mcp):
    """Register Bollinger Z-Score tools with the MCP server"""
    
    @mcp.tool()
    def calculate_bollinger_z_score(symbol: str, period: int = 20) -> str:
        """
        Calculate the Bollinger Z-Score for mean reversion analysis.
        
        The Bollinger Z-Score is a technical indicator used to assess the position of a 
        security's price relative to its Bollinger Bands. It's a normalized measure that 
        helps traders understand whether a price is relatively high or low compared to 
        its recent trading range.

        Interpretation:
        - Z-Score of 0: Current price is exactly at the middle Bollinger Band (SMA)
        - Positive Z-Score: Price is above the middle band (potentially overbought)
        - Negative Z-Score: Price is below the middle band (potentially oversold)
        
        Trading Guidelines:
        - Z-Score > +2: Price considered overbought (potential sell signal)
        - Z-Score < -2: Price considered oversold (potential buy signal)
        - Z-Score between -2 and +2: Price within "normal" trading range

        Important Considerations:
        - Trend: Z-Score should be interpreted with overall trend context
        - Volatility: More volatile securities have wider bands and larger Z-Score fluctuations
        - False Signals: Can generate false signals in trending markets

        Parameters:
        symbol (str): Stock ticker symbol to analyze
        period (int): Period for calculating moving average and standard deviation (default: 20)
        
        Returns:
        str: Message with Bollinger Z-Score analysis
        """
        # Fetch historical data
        data = yf.download(symbol, period=f"{period+50}d")
        if data.empty:
            return f"Could not find data for symbol: {symbol}"

        closes = data["Close"]
        rolling_mean = closes.rolling(window=period).mean()
        rolling_std = closes.rolling(window=period).std()
        upper_band = rolling_mean + (2 * rolling_std)
        lower_band = rolling_mean - (2 * rolling_std)
        z_score = (closes - rolling_mean) / rolling_std

        latest_z_score = z_score.iloc[-1]
        latest_upper_band = upper_band.iloc[-1]
        latest_lower_band = lower_band.iloc[-1]
        latest_close = closes.iloc[-1]
        latest_mean = rolling_mean.iloc[-1]

        # Handle potential MultiIndex from yfinance
        if hasattr(latest_z_score, 'values'):
            latest_z_score = latest_z_score.values[0] if len(latest_z_score.values) > 0 else latest_z_score
        if hasattr(latest_upper_band, 'values'):
            latest_upper_band = latest_upper_band.values[0] if len(latest_upper_band.values) > 0 else latest_upper_band
        if hasattr(latest_lower_band, 'values'):
            latest_lower_band = latest_lower_band.values[0] if len(latest_lower_band.values) > 0 else latest_lower_band
        if hasattr(latest_close, 'values'):
            latest_close = latest_close.values[0] if len(latest_close.values) > 0 else latest_close
        if hasattr(latest_mean, 'values'):
            latest_mean = latest_mean.values[0] if len(latest_mean.values) > 0 else latest_mean

        # Determine market condition and recommendation
        if latest_z_score > 2:
            condition = "OVERBOUGHT - Strong Sell Signal"
            recommendation = "Consider selling or shorting the security"
        elif latest_z_score > 1:
            condition = "Moderately Overbought - Weak Sell Signal"
            recommendation = "Monitor for potential reversal or take partial profits"
        elif latest_z_score < -2:
            condition = "OVERSOLD - Strong Buy Signal"
            recommendation = "Consider buying the security"
        elif latest_z_score < -1:
            condition = "Moderately Oversold - Weak Buy Signal"
            recommendation = "Monitor for potential bounce or consider accumulating"
        else:
            condition = "NORMAL RANGE - Hold"
            recommendation = "Price within normal trading range, monitor trend"

        # Calculate distance from bands as percentage
        distance_from_upper = (latest_close - latest_upper_band) / latest_upper_band * 100
        distance_from_lower = (latest_close - latest_lower_band) / latest_lower_band * 100

        message = f"""
Symbol: {symbol}, Period: {period} days

=== BOLLINGER Z-SCORE ANALYSIS ===
Latest Close Price: USD {latest_close:.2f}
Rolling Mean ({period}-day): USD {latest_mean:.2f}
Upper Bollinger Band: USD {latest_upper_band:.2f}
Lower Bollinger Band: USD {latest_lower_band:.2f}

=== Z-SCORE METRICS ===
Latest Bollinger Z-Score: {latest_z_score:.2f}
Standard Deviations from Mean: {abs(latest_z_score):.2f}

=== POSITION ANALYSIS ===
Distance from Upper Band: {distance_from_upper:+.2f}%
Distance from Lower Band: {distance_from_lower:+.2f}%

=== TRADING SIGNAL ===
Market Condition: {condition}
Recommendation: {recommendation}

=== RISK CONSIDERATIONS ===
• Use in conjunction with trend analysis
• Consider overall market conditions
• Be aware of potential false signals in strong trends
• Adjust position sizing based on volatility
        """
        return message