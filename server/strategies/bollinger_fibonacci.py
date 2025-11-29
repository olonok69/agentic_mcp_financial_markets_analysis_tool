"""
Bollinger Bands and Fibonacci Retracement Strategy Module for MCP Server

This module implements the Bollinger Bands and Fibonacci Retracement combined strategy.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import List
from utils.yahoo_finance_tools import (
    calculate_bollinger_bands,
    find_swing_points,
    calculate_fibonacci_levels,
)


def register_bollinger_fibonacci_tools(mcp):
    """Register Bollinger Bands and Fibonacci tools with the MCP server"""
    
    @mcp.tool()
    def calculate_bollinger_fibonacci_score(
        ticker: str,
        period: str = "1y",
        window: int = 20,
        num_std: int = 2,
        window_swing_points: int = 10,
        fibonacci_levels: List = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1],
        num_days: int = 3,
    ) -> str:
        """
        Calculate Bollinger Bands and Fibonacci Retracement strategy score to indicate buy/sell/hold signals.

        The strategy score ranges from -100 to +100 and is categorized into five signal zones:

        +60 to +100: Strong Buy
        +20 to +60: Moderate Buy
        -20 to +20: Hold
        -60 to -20: Moderate Sell
        -100 to -60: Strong Sell

        ### How the Score is Calculated
        The score is a weighted combination of four key components:

        ### Bollinger Band Position (30% weight) - Based on the %B indicator:
        When price is near the lower band (%B close to 0): Positive contribution 
        When price is near the upper band (%B close to 1): Negative contribution

        ### Volatility Assessment (15% weight):
        Considers both current Bollinger Band width and recent changes in width 
        Narrow bands with expanding width can signal potential breakouts 
        High volatility reduces signal reliability

        ### Fibonacci Level Interaction (35% weight):
        Highest weight because it's the core of this combined strategy 
        Measures proximity to key Fibonacci levels 
        Considers whether price is bouncing off or breaking through a level 
        Accounts for whether the level is acting as support or resistance

        ### Price Momentum (20% weight):
        RSI-like momentum indicator to identify overbought/oversold conditions 
        Oversold conditions (like RSI below 30) contribute positively 
        Overbought conditions (like RSI above 70) contribute negatively

        Parameters:
        ticker (str): ticker Yahoo finance
        period (str): Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        window (int): period to calculate the middle Bollinger Bands moving average
        num_std (int): Number of standard deviation to use to calculate lower and upper Bollinger Bands
        window_swing_points (int): Swing points are critical reference points used to identify significant price reversals
        fibonacci_levels (List[float]): List of float which help us to identify possible resistance and support levels
        num_days (int): Number of days from the last day to calculate scores. Default is 3 (3 last days)

        Returns:
        str: message with the scores for the last n days
        """
        data = yf.download(ticker, period=period, multi_level_index=False)
        if data is None or "Upper_Band" not in data.columns:
            calculate_bollinger_bands(
                data=data, window=window, ticker=ticker, num_std=num_std
            )

        if "Swing_High" not in data.columns:
            find_swing_points(data=data, window=window_swing_points)

        # Calculate Fibonacci levels if not already done
        fib_levels, fib_trend = calculate_fibonacci_levels(
            data=data, window=window_swing_points, fibonacci_levels=fibonacci_levels
        )

        # Initialize score column
        data["Strategy_Score"] = 0.0
        data["BB_Score"] = 0.0
        data["Volatility_Score"] = 0.0
        data["Fib_Score"] = 0.0
        data["Momentum_Score"] = 0.0

        # Skip calculation if Fibonacci levels couldn't be determined
        if fib_levels is None:
            return "Unable to calculate Fibonacci levels. Not enough data or no significant swing points found."

        # 1. Score based on %B (position within Bollinger Bands)
        # %B near 0 (price near lower band) = positive score
        # %B near 1 (price near upper band) = negative score
        data["BB_Score"] = (0.5 - data["%B"]) * 50  # Range: -25 to +25

        # 2. Score based on Bollinger Band width (volatility)
        # Lower volatility means more reliable signals
        # Normalize BB width to a range of 0-1 based on recent history
        rolling_max_width = data["BB_Width"].rolling(window=60, min_periods=20).max()
        rolling_min_width = data["BB_Width"].rolling(window=60, min_periods=20).min()

        # Avoid division by zero by adding small epsilon
        width_range = rolling_max_width - rolling_min_width
        width_range = width_range.replace(0, 1e-10)

        normalized_width = (data["BB_Width"] - rolling_min_width) / width_range

        # Expanding BB width (increasing volatility) can signal upcoming trend change
        bb_width_change = data["BB_Width"].pct_change(5)  # 5-day change in BB width

        # Combine into volatility score (range: -15 to +15)
        # Narrow bands with expanding width can signal breakout potential
        data["Volatility_Score"] = 15 - normalized_width * 30 + bb_width_change * 100
        data["Volatility_Score"] = data["Volatility_Score"].clip(-15, 15)

        # 3. Score based on proximity to Fibonacci levels
        data["Closest_Fib_Level"] = None
        data["Closest_Fib_Price"] = np.nan
        data["Fib_Distance_Pct"] = np.nan

        for i in range(len(data)):
            if i < window:  # Skip initial periods without enough data
                continue

            current_price = data["Close"].iloc[i]

            # Find closest Fibonacci level
            closest_fib = min(fib_levels.items(), key=lambda x: abs(x[1] - current_price))
            closest_fib_level, closest_fib_price = closest_fib

            # Store for debugging
            data.loc[data.index[i], "Closest_Fib_Level"] = closest_fib_level
            data.loc[data.index[i], "Closest_Fib_Price"] = closest_fib_price

            # Calculate percent distance to closest Fibonacci level
            percent_distance = abs(current_price - closest_fib_price) / closest_fib_price
            data.loc[data.index[i], "Fib_Distance_Pct"] = percent_distance

            # Only consider very close distances to be significant (max 3%)
            if percent_distance > 0.03:
                continue

            # Higher score for closer proximity
            proximity_factor = 1.0 - (percent_distance / 0.03)
            proximity_score = 35.0 * proximity_factor  # Max score of 35

            # Get price direction (using 5-day change)
            if i >= 5:
                price_5d_ago = data["Close"].iloc[i - 5]
                price_direction = 1 if current_price > price_5d_ago else -1

                # Determine if we're at support or resistance
                is_support_level = False
                is_resistance_level = False

                # In downtrend, lower Fibonacci levels act as support
                # In uptrend, higher Fibonacci levels act as resistance
                if fib_trend == "downtrend":
                    is_support_level = closest_fib_level <= 0.382
                    is_resistance_level = closest_fib_level >= 0.618
                else:  # uptrend
                    is_support_level = closest_fib_level <= 0.382
                    is_resistance_level = closest_fib_level >= 0.618

                # Simplified scoring logic
                if is_support_level:
                    # At support: positive score if price is rising (bouncing), negative if falling (breaking)
                    score = proximity_score if price_direction > 0 else -proximity_score
                elif is_resistance_level:
                    # At resistance: negative score if price is falling (rejecting), positive if rising (breaking)
                    score = -proximity_score if price_direction < 0 else proximity_score
                else:
                    # Mid-range fibonacci levels (like 0.5) - use smaller scores
                    score = proximity_score * 0.5 * price_direction

                data.loc[data.index[i], "Fib_Score"] = score

        # 4. Score based on momentum
        # RSI-like momentum indicator (simplified)
        price_change = data["Close"].diff(1)
        gain = price_change.clip(lower=0)
        loss = -price_change.clip(upper=0)
        avg_gain = gain.rolling(window=14, min_periods=5).mean()
        avg_loss = loss.rolling(window=14, min_periods=5).mean()

        # Avoid division by zero
        avg_loss_safe = avg_loss.replace(0, 1e-10)
        rs = avg_gain / avg_loss_safe
        rsi = 100 - (100 / (1 + rs))

        # Convert RSI to momentum score (-30 to +30)
        # RSI < 30 = oversold = positive score
        # RSI > 70 = overbought = negative score
        data["Momentum_Score"] = np.where(
            rsi < 30,
            30 * (30 - rsi) / 30,
            np.where(
                rsi > 70,
                -30 * (rsi - 70) / 30,
                (50 - rsi) * 0.6,  # Scaled score for middle range
            ),
        )

        # Combine all scores into the final strategy score
        # Weights: BB 30%, Volatility 15%, Fibonacci 35%, Momentum 20%
        data["Strategy_Score"] = (
            0.30 * data["BB_Score"]
            + 0.15 * data["Volatility_Score"]
            + 0.35 * data["Fib_Score"]
            + 0.20 * data["Momentum_Score"]
        )

        # Handle NaN and infinite values
        data["Strategy_Score"] = (
            data["Strategy_Score"].fillna(0).replace([np.inf, -np.inf], 0)
        )

        # Clip to desired range and round but keep as float
        data["Strategy_Score"] = data["Strategy_Score"].clip(-100, 100).round()

        # Determine signal category - use float values for bins
        data["Signal_Category"] = pd.cut(
            data["Strategy_Score"],
            bins=[-100.0, -60.0, -20.0, 20.0, 60.0, 100.0],
            labels=["Strong Sell", "Moderate Sell", "Hold", "Moderate Buy", "Strong Buy"],
        )

        # Ensure n doesn't exceed available data
        num_days = min(num_days, len(data))

        # Create message with info for last n days
        message = f"""
Symbol: {ticker}
Period download data: {period}
Window Bollinger Bands: {window}
Fibonacci levels: {str(fibonacci_levels)}
        """

        # Add score information for each day
        for i in range(1, num_days + 1):
            idx = -i  # Index from the end of the dataframe
            day_date = data.index[idx].strftime("%Y-%m-%d")

            bb_score = float(data.iloc[idx].BB_Score)
            volatility_score = float(data.iloc[idx].Volatility_Score)
            fib_score = float(data.iloc[idx].Fib_Score)
            momentum_score = float(data.iloc[idx].Momentum_Score)
            strategy_score = float(data.iloc[idx].Strategy_Score)
            signal_category = str(data.iloc[idx].Signal_Category)

            # Add a day header with clear day identification
            if i == 1:
                day_label = "Latest trading day"
            else:
                day_label = f"{i-1} trading day(s) before latest"

            message += f"""
=========== {day_label} ({day_date}) ===========
Bollinger Bands score (30% of score): {bb_score:.2f}
Volatility score (15% of score): {volatility_score:.2f}
Fibonacci Retracement score (35% of score): {fib_score:.2f}
Momentum score (20% of score): {momentum_score:.2f}
Strategy score: {strategy_score:.2f}
Signal Category: {signal_category}
            """

        return message