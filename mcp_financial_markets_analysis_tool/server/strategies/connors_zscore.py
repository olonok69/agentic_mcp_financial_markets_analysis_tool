"""
Connors RSI and Z-Score Strategy Module for MCP Server

This module implements Connors RSI and Z-Score indicators for mean reversion analysis.
"""

import pandas as pd
import numpy as np
import yfinance as yf


def register_connors_zscore_tools(mcp):
    """Register Connors RSI and Z-Score tools with the MCP server"""
    
    @mcp.tool()
    def calculate_connors_rsi_score_tool(
        symbol: str,
        period: str = "1y",
        rsi_period: int = 3,
        streak_period: int = 2,
        rank_period: int = 100,
    ) -> str:
        """
        Calculate a Connors RSI score between -100 and 100 for the given symbol and period.
        
        Connors RSI combines three components:
        1. Price RSI (33.33%): Traditional RSI of closing prices
        2. Streak RSI (33.33%): RSI of consecutive up/down movements  
        3. Percent Rank (33.33%): Percentile ranking of rate of change
        
        Parameters:
        symbol (str): ticker Yahoo finance 
        period (str): Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        rsi_period (int): Period for price RSI (default 3)
        streak_period (int): Period for streak RSI (default 2)
        rank_period (int): Period for percent rank (default 100)
        
        Returns:
        str: message with detailed Connors RSI analysis
        """
        from utils.yahoo_finance_tools import calculate_connors_rsi_score
        
        # Get the calculation results from the utility function
        current_crsi, current_score, current_price_rsi, current_streak_rsi, current_percent_rank = calculate_connors_rsi_score(
            symbol=symbol,
            period=period,
            rsi_period=rsi_period,
            streak_period=streak_period,
            rank_period=rank_period
        )
        
        # Component scores (each worth 33.33% of total)
        price_rsi_score = (current_price_rsi - 50) * 2 * 0.3333
        streak_rsi_score = (current_streak_rsi - 50) * 2 * 0.3333
        percent_rank_score = (current_percent_rank - 50) * 2 * 0.3333
        
        # Determine market condition
        if current_crsi < 20:
            market_condition = "Oversold (Potential Buy Signal)"
        elif current_crsi > 80:
            market_condition = "Overbought (Potential Sell Signal)"
        else:
            market_condition = "Normal Range"
        
        message = f"""
Symbol: {symbol}, Period: {period}
Latest Connors RSI: {current_crsi:.2f}
Latest Connors RSI Score: {current_score:.2f}

Component Analysis:
1. Price RSI (33.33% weight): {current_price_rsi:.2f} -> Score: {price_rsi_score:.2f}
2. Streak RSI (33.33% weight): {current_streak_rsi:.2f} -> Score: {streak_rsi_score:.2f}
3. Percent Rank (33.33% weight): {current_percent_rank:.2f} -> Score: {percent_rank_score:.2f}

Market Condition: {market_condition}
        """
        return message

    @mcp.tool()
    def calculate_zscore_indicator_tool(
        symbol: str, 
        period: str = "1y", 
        window: int = 20
    ) -> str:
        """
        Calculate Z-Score indicator score for mean reversion analysis.
        
        Z-Score measures how many standard deviations the current price is from its mean.
        This helps identify potential mean reversion opportunities.
        
        Parameters:
        symbol (str): ticker Yahoo finance 
        period (str): Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        window (int): The lookback period for calculating mean and standard deviation
        
        Returns:
        str: message with Z-Score analysis
        """
        from utils.yahoo_finance_tools import calculate_zscore_indicator
        
        # Get the calculation results from the utility function
        current_zscore, current_score, current_price, current_mean, current_std = calculate_zscore_indicator(
            symbol=symbol,
            period=period,
            window=window
        )
        
        # Determine mean reversion signal
        if current_zscore > 2:
            reversion_signal = "Strong Mean Reversion Expected (Price very high)"
        elif current_zscore > 1:
            reversion_signal = "Moderate Mean Reversion Expected (Price high)" 
        elif current_zscore < -2:
            reversion_signal = "Strong Bounce Expected (Price very low)"
        elif current_zscore < -1:
            reversion_signal = "Moderate Bounce Expected (Price low)"
        else:
            reversion_signal = "Price near mean (No strong reversion signal)"
        
        message = f"""
Symbol: {symbol}, Period: {period}, Window: {window}
Current Price: ${current_price:.2f}
Rolling Mean: ${current_mean:.2f}
Current Z-Score: {current_zscore:.2f}
Z-Score Indicator Score: {current_score:.2f}

Mean Reversion Analysis: {reversion_signal}
Standard Deviations from Mean: {abs(current_zscore):.2f}
        """
        return message

    @mcp.tool()
    def calculate_combined_connors_zscore_tool(
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
        Calculate a combined score using Connors RSI and Z-Score indicators.
        
        This combines momentum analysis (Connors RSI) with mean reversion analysis (Z-Score)
        to provide a comprehensive trading signal.
        
        Parameters:
        symbol (str): ticker Yahoo finance
        period (str): Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        rsi_period (int): Period for price RSI (default 3)
        streak_period (int): Period for streak RSI (default 2)
        rank_period (int): Period for percent rank (default 100)
        zscore_window (int): Window for Z-Score calculation (default 20)
        connors_weight (float): Weight for Connors RSI (default 0.7)
        zscore_weight (float): Weight for Z-Score (default 0.3)
        
        Returns:
        str: Combined analysis with trading recommendation
        """
        from utils.yahoo_finance_tools import calculate_connors_rsi_score, calculate_zscore_indicator
        
        # Calculate Connors RSI
        current_crsi, connors_score, current_price_rsi, current_streak_rsi, current_percent_rank = calculate_connors_rsi_score(
            symbol=symbol,
            period=period,
            rsi_period=rsi_period,
            streak_period=streak_period,
            rank_period=rank_period
        )
        
        # Calculate Z-Score
        current_zscore, zscore_score, current_price, current_mean, current_std = calculate_zscore_indicator(
            symbol=symbol,
            period=period,
            window=zscore_window
        )
        
        # Calculate combined score
        combined_score = (connors_score * connors_weight) + (zscore_score * zscore_weight)
        
        # Interpret the combined score
        if combined_score > 75:
            signal = "Strong Buy Signal"
        elif combined_score > 50:
            signal = "Buy Signal"
        elif combined_score > 25:
            signal = "Weak Buy Signal"
        elif combined_score > -25:
            signal = "Neutral"
        elif combined_score > -50:
            signal = "Weak Sell Signal"
        elif combined_score > -75:
            signal = "Sell Signal"
        else:
            signal = "Strong Sell Signal"
        
        # Market conditions
        connors_condition = "Oversold" if current_crsi < 20 else "Overbought" if current_crsi > 80 else "Normal Range"
        zscore_condition = "Extremely High" if abs(current_zscore) > 2 else "High" if abs(current_zscore) > 1 else "Normal"
        
        message = f"""
Symbol: {symbol}, Period: {period}
Current Price: ${current_price:.2f}

=== CONNORS RSI ANALYSIS ===
Connors RSI: {current_crsi:.2f}
Connors RSI Score: {connors_score:.2f}
Market Condition: {connors_condition}
Weight in Combined Score: {connors_weight*100:.1f}%

=== Z-SCORE ANALYSIS ===
Z-Score: {current_zscore:.2f}
Z-Score Indicator Score: {zscore_score:.2f}
Price vs Mean: {zscore_condition}
Weight in Combined Score: {zscore_weight*100:.1f}%

=== COMBINED ANALYSIS ===
Combined Score: {combined_score:.2f}
Trading Signal: {signal}

=== INTERPRETATION ===
Momentum (Connors RSI): {"Bullish" if connors_score > 0 else "Bearish" if connors_score < 0 else "Neutral"}
Mean Reversion (Z-Score): {"Price High - Reversion Expected" if current_zscore > 0 else "Price Low - Bounce Expected" if current_zscore < 0 else "Price Fair"}
        """
        return message