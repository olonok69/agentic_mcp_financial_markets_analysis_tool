"""
MACD Donchian Strategy Module for MCP Server

This module implements MACD and Donchian Channel indicators and their combined analysis.
"""

import pandas as pd
import numpy as np
import yfinance as yf


def register_macd_donchian_tools(mcp):
    """Register MACD and Donchian Channel tools with the MCP server"""
    
    @mcp.tool()
    def calculate_macd_score_tool(
        symbol: str,
        period: str = "1y",
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> str:
        """
        Calculate a MACD score between -100 and 100 for the ticker and given period.
        
        The MACD score combines three components:
        - MACD Line Position vs. Signal Line (40%)
        - MACD Line Position vs. Zero (30%)
        - Histogram Momentum (30%)
        
        Parameters:
        symbol (str): ticker Yahoo finance
        period (str): Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        fast_period (int): Fast EMA period (default: 12)
        slow_period (int): Slow EMA period (default: 26)
        signal_period (int): Signal line period (default: 9)
        
        Returns:
        str: MACD analysis with component scores
        """
        data = yf.download(symbol, period=period, multi_level_index=False)
        
        # Calculate the fast and slow EMAs
        ema_fast = data["Close"].ewm(span=fast_period, adjust=False).mean()
        ema_slow = data["Close"].ewm(span=slow_period, adjust=False).mean()

        # Calculate the MACD line
        macd_line = ema_fast - ema_slow

        # Calculate the signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        # Calculate the MACD histogram
        macd_histogram = macd_line - signal_line

        # Create result DataFrame
        macd_data = pd.DataFrame({
            "macd_line": macd_line,
            "signal_line": signal_line,
            "macd_histogram": macd_histogram,
        }, index=data.index)

        # Component 1: MACD line position relative to signal line (40% of score)
        typical_range = macd_data["macd_line"].std() * 3  # 3 standard deviations
        if typical_range == 0:
            typical_range = 0.001  # Prevent division by zero

        line_position = (macd_data["macd_line"] - macd_data["signal_line"]) / typical_range
        component1 = line_position.clip(-1, 1) * 40

        # Component 2: MACD line position relative to zero (30% of score)
        zero_position = macd_data["macd_line"] / typical_range
        component2 = zero_position.clip(-1, 1) * 30

        # Component 3: Histogram direction and momentum (30% of score)
        hist_change = macd_data["macd_histogram"].diff(3).rolling(window=3).mean()
        hist_typical_range = hist_change.std() * 3
        if hist_typical_range == 0:
            hist_typical_range = 0.001  # Prevent division by zero

        hist_momentum = hist_change / hist_typical_range
        component3 = hist_momentum.clip(-1, 1) * 30

        # Combine components
        score = component1 + component2 + component3
        current_macd_score = float(score.iloc[-1])
        current_line_position = float(component1.iloc[-1])
        current_zero_position = float(component2.iloc[-1])
        current_hist_momentum = float(component3.iloc[-1])
        
        message = f"""
Symbol: {symbol}, Period: {period}
Latest MACD score: {current_macd_score:.2f}
Latest first component score. MACD line position relative to signal line (40% of score): {current_line_position:.2f}
Latest second component score. MACD line position relative to zero (30% of score): {current_zero_position:.2f}
Latest third component score. Histogram direction and momentum (30% of score): {current_hist_momentum:.2f}
        """
        return message

    @mcp.tool()
    def calculate_donchian_channel_score_tool(
        symbol: str, period: str = "1y", window: int = 20
    ) -> str:
        """
        Calculate Donchian Channel score for the given symbol, period and window period.
        
        Donchian Channel Score (-100 to +100) with 3 components:
        - Price Position Within Channel (50%)
        - Channel Direction (30%)
        - Channel Width Trend (20%)
        
        Parameters:
        symbol (str): ticker Yahoo finance
        period (str): Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        window (int): The lookback period for calculating channels
        
        Returns:
        str: Donchian Channel analysis with component scores
        """
        data = yf.download(symbol, period=period, multi_level_index=False)
        
        # Calculate upper and lower bands
        upper_band = data["High"].rolling(window=window).max()
        lower_band = data["Low"].rolling(window=window).min()
        middle_band = (upper_band + lower_band) / 2

        # Create result DataFrame
        channels = pd.DataFrame({
            "upper": upper_band, 
            "middle": middle_band, 
            "lower": lower_band
        }, index=data.index)

        # Component 1: Position within the channel (50% of score)
        channel_width = channels["upper"] - channels["lower"]
        channel_width = channel_width.replace(0, 0.001)  # Prevent division by zero

        position_pct = (data["Close"] - channels["lower"]) / channel_width
        component1 = ((position_pct * 2) - 1) * 50  # Scale to -50 to +50

        # Component 2: Channel direction (30% of score)
        channel_direction = channels["middle"].diff(5).rolling(window=5).mean()
        channel_direction_range = channel_direction.std() * 3
        if channel_direction_range == 0:
            channel_direction_range = 0.001

        normalized_direction = channel_direction / channel_direction_range
        component2 = normalized_direction.clip(-1, 1) * 30

        # Component 3: Channel width trend (20% of score)
        width_change = channel_width.diff(5).rolling(window=5).mean()
        width_change_range = width_change.std() * 3
        if width_change_range == 0:
            width_change_range = 0.001

        normalized_width = width_change / width_change_range
        component3 = normalized_width.clip(-1, 1) * 20

        # Combine components
        score = component1 + component2 + component3

        current_donchian_score = float(score.iloc[-1])
        current_line_position = float(component1.iloc[-1])
        current_zero_position = float(component2.iloc[-1])
        current_hist_momentum = float(component3.iloc[-1])
        
        message = f"""
Symbol: {symbol}, Period: {period}
Latest donchian band score: {current_donchian_score:.2f}
Latest first component score. Position within the channel (50% of score): {current_line_position:.2f}
Latest second component score. Channel direction (30% of score): {current_zero_position:.2f}
Latest third component score. Channel width trend (20% of score): {current_hist_momentum:.2f}
        """
        return message

    @mcp.tool()
    def calculate_combined_score_macd_donchian(
        symbol: str,
        period: str = "1y",
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        window: int = 20,
    ) -> str:
        """
        Calculate a combined MACD Donchian score between -100 and 100.
        
        The combined score is a simple average of the MACD and Donchian scores,
        giving equal weight to momentum (MACD) and price range (Donchian) indicators.
        
        Trading Signals:
        - +75 to +100: Strong Buy
        - +50 to +75: Buy
        - +25 to +50: Weak Buy
        - -25 to +25: Neutral (Hold)
        - -50 to -25: Weak Sell
        - -75 to -50: Sell
        - -100 to -75: Strong Sell
        
        Parameters:
        symbol (str): ticker Yahoo finance
        period (str): Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        fast_period (int): Fast EMA period (default: 12)
        slow_period (int): Slow EMA period (default: 26)
        signal_period (int): Signal line period (default: 9)
        window (int): Donchian channel lookback period (default: 20)
        
        Returns:
        str: Combined analysis with trading signal
        """
        from utils.yahoo_finance_tools import calculate_macd_score, calculate_donchian_channel_score
        
        # Calculate MACD score
        macd_score = calculate_macd_score(
            symbol=symbol,
            period=period,
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
        )
        
        # Calculate Donchian score
        donchian_score = calculate_donchian_channel_score(
            symbol=symbol,
            period=period,
            window=window,
        )
        
        # Equal weight to both indicators
        score = (float(macd_score) + float(donchian_score)) / 2
        score = float(score)
        
        message = f"""
Symbol: {symbol}, Period: {period}
Latest combined score: {score:.2f}
Latest MACD score: {float(macd_score):.2f}
Latest Donchian score: {float(donchian_score):.2f}
Trading Signal: """
        
        if score > 75:
            return message + "Strong Buy Signal"
        elif score > 50:
            return message + "Buy Signal"
        elif score > 25:
            return message + "Weak Buy Signal"
        elif score > -25:
            return message + "Neutral"
        elif score > -50:
            return message + "Weak Sell Signal"
        elif score > -75:
            return message + "Sell Signal"
        else:
            return message + "Strong Sell Signal"