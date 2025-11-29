import pandas as pd
import numpy as np
import yfinance as yf
from typing import List, Dict, Any, Optional


def fetch_data(ticker: str, period: str):
    """Fetch historical stock data from Yahoo Finance."""
    data = yf.download(ticker, period=period, multi_level_index=False)
    return data


def calculate_bollinger_bands(
    data: pd.DataFrame,
    ticker: str,
    period: str = "1y",
    window: int = 20,
    num_std: int = 2,
):
    """Calculate Bollinger Bands."""
    if data is None:
        fetch_data(ticker=ticker, period=period)

    # Calculate moving average and standard deviation
    data["MA"] = data["Close"].rolling(window=window).mean()
    data["STD"] = data["Close"].rolling(window=window).std()

    # Calculate upper and lower Bollinger Bands
    data["Upper_Band"] = data["MA"] + (data["STD"] * num_std)
    data["Lower_Band"] = data["MA"] - (data["STD"] * num_std)

    # Calculate Bollinger Band width
    data["BB_Width"] = (data["Upper_Band"] - data["Lower_Band"]) / data["MA"]

    # Calculate Bollinger Band %B
    data["%B"] = (data["Close"] - data["Lower_Band"]) / (
        data["Upper_Band"] - data["Lower_Band"]
    )

    return data


def find_swing_points(data: pd.DataFrame, window: int = 10, debug: bool = False):
    """
    Find swing high and swing low points for Fibonacci retracement.

    Parameters:
    -----------
    window : int
        Window size to identify swing points (default: 10)
    """
    if "Upper_Band" not in data.columns:
        calculate_bollinger_bands()

    # Find swing high points
    data["Swing_High"] = False
    data["Swing_Low"] = False

    # Find swing high points
    for i in range(window, len(data) - window):
        if all(
            data["High"].iloc[i] > data["High"].iloc[i - j]
            for j in range(1, window + 1)
        ) and all(
            data["High"].iloc[i] > data["High"].iloc[i + j]
            for j in range(1, window + 1)
        ):
            data.loc[data.index[i], "Swing_High"] = True

    # Find swing low points
    for i in range(window, len(data) - window):
        if all(
            data["Low"].iloc[i] < data["Low"].iloc[i - j] for j in range(1, window + 1)
        ) and all(
            data["Low"].iloc[i] < data["Low"].iloc[i + j] for j in range(1, window + 1)
        ):
            data.loc[data.index[i], "Swing_Low"] = True

    # Debug information
    if debug:
        high_count = data["Swing_High"].sum()
        low_count = data["Swing_Low"].sum()
        print(f"Found {high_count} swing highs and {low_count} swing lows")

        # Check if we have too few swing points
        if high_count < 2 or low_count < 2:
            print(
                "WARNING: Too few swing points detected. Consider using a smaller window or more data."
            )

    return data


def calculate_fibonacci_levels(
    data: pd.DataFrame,
    window: int = 10,
    fibonacci_levels: List = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1],
    debug: bool = False,
):
    """Calculate Fibonacci retracement levels based on last swing high and low."""
    if "Swing_High" not in data.columns:
        find_swing_points(data=data, window=window)

    # Find all swing highs and swing lows
    swing_highs = data[data["Swing_High"] == True]
    swing_lows = data[data["Swing_Low"] == True]

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        if debug:
            print(
                f"Not enough swing points: {len(swing_highs)} highs, {len(swing_lows)} lows"
            )
        return None

    # FIXED: Get the two most recent swings to determine trend
    recent_swings = pd.concat(
        [
            swing_highs.assign(Type="High").iloc[-2:],
            swing_lows.assign(Type="Low").iloc[-2:],
        ]
    ).sort_index()

    if len(recent_swings) < 2:
        if debug:
            print("Not enough recent swings to determine trend")
        return None

    # Determine most recent significant swing
    last_swing = recent_swings.iloc[-1]
    prev_swing = recent_swings.iloc[-2]

    # Get the most recent swing high and low for price levels
    last_swing_high = swing_highs.iloc[-1]
    last_swing_low = swing_lows.iloc[-1]

    # FIXED: Better trend determination without using undefined variables
    if last_swing["Type"] == "High" and prev_swing["Type"] == "Low":
        # Last move was up - could be either trend
        # For uptrend: higher highs and higher lows
        # For downtrend: lower highs and lower lows
        # Compare current high to previous high if available
        if len(swing_highs) >= 2:
            prev_high = swing_highs.iloc[-2]["High"]
            fib_trend = (
                "uptrend" if last_swing_high["High"] > prev_high else "downtrend"
            )
        else:
            # Not enough history, assume uptrend if price is rising
            fib_trend = "uptrend"

    elif last_swing["Type"] == "Low" and prev_swing["Type"] == "High":
        # Last move was down - could be either trend
        # Compare current low to previous low if available
        if len(swing_lows) >= 2:
            prev_low = swing_lows.iloc[-2]["Low"]
            fib_trend = "uptrend" if last_swing_low["Low"] > prev_low else "downtrend"
        else:
            # Not enough history, assume downtrend if price is falling
            fib_trend = "downtrend"
    else:
        # Two highs or two lows in a row - use the most recent price movement
        # If last swing is more recent than last significant move, use that
        fib_trend = (
            "uptrend" if last_swing_high.name > last_swing_low.name else "downtrend"
        )

    # FIXED: Set high and low price based on trend
    if fib_trend == "downtrend":
        high_price = last_swing_high["High"]
        low_price = last_swing_low["Low"]
    else:  # uptrend
        high_price = last_swing_high["High"]
        low_price = last_swing_low["Low"]

    if debug:
        print(f"Trend determined as: {fib_trend}")
        print(f"High price: {high_price}, Low price: {low_price}")

    # Calculate price range and check if it's significant
    price_range = high_price - low_price
    if abs(price_range) < 0.01 * high_price:  # Range is less than 1% of price
        if debug:
            print(f"Price range too small: {price_range}")
        return None

    # Calculate Fibonacci retracement levels
    fib_levels = {}
    for level in fibonacci_levels:
        if fib_trend == "downtrend":
            fib_levels[level] = high_price - price_range * level
        else:
            fib_levels[level] = low_price + price_range * level

    if debug:
        print(f"Fibonacci levels: {fib_levels}")

    return fib_levels, fib_trend


def rsi(series, period=14):
    """Calculate traditional RSI"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def streak_rsi(series, period=2):
    """Calculate RSI of price streaks"""
    # Calculate streaks
    price_change = series.diff()
    streaks = []
    current_streak = 0
    
    for change in price_change:
        if pd.isna(change):
            streaks.append(0)
            current_streak = 0
        elif change > 0:
            if current_streak >= 0:
                current_streak += 1
            else:
                current_streak = 1
            streaks.append(current_streak)
        elif change < 0:
            if current_streak <= 0:
                current_streak -= 1
            else:
                current_streak = -1
            streaks.append(current_streak)
        else:  # change == 0
            streaks.append(0)
            current_streak = 0
    
    streak_series = pd.Series(streaks, index=series.index)
    return rsi(streak_series, period)


def percent_rank(series, period=100):
    """Calculate percent rank over a rolling window"""
    def rank_pct(x):
        if len(x) < 2:
            return 50.0
        current_value = x.iloc[-1]
        rank = (x < current_value).sum()
        return (rank / (len(x) - 1)) * 100
    
    return series.rolling(window=period).apply(rank_pct, raw=False)


def calculate_connors_rsi_score(
    symbol: str,
    period: str = "1y",
    rsi_period: int = 3,
    streak_period: int = 2,
    rank_period: int = 100,
) -> tuple:
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
    tuple: (connors_rsi_value, connors_score, price_rsi, streak_rsi, percent_rank)
    """
    
    data = yf.download(symbol, period=period, multi_level_index=False) 
    close = data['Close']
    
    # Component 1: RSI of closing prices (33.33%)
    price_rsi = rsi(close, rsi_period)
    
    # Component 2: RSI of price streaks (33.33%)
    streak_rsi_values = streak_rsi(close, streak_period)
    
    # Component 3: Percent rank of rate of change (33.33%)
    roc = close.pct_change() * 100  # Rate of change as percentage
    percent_rank_values = percent_rank(roc, rank_period)
    
    # Calculate Connors RSI
    crsi = (price_rsi + streak_rsi_values + percent_rank_values) / 3
    
    # Convert Connors RSI to score (-100 to +100)
    # CRSI ranges from 0-100, convert to -100 to +100 scale
    # 50 becomes 0, 0 becomes -100, 100 becomes +100
    connors_score = (crsi - 50) * 2
    
    # Get latest values
    current_crsi = float(crsi.iloc[-1])
    current_score = float(connors_score.iloc[-1])
    current_price_rsi = float(price_rsi.iloc[-1])
    current_streak_rsi = float(streak_rsi_values.iloc[-1])
    current_percent_rank = float(percent_rank_values.iloc[-1])
    
    return (current_crsi, current_score, current_price_rsi, current_streak_rsi, current_percent_rank)


def calculate_zscore_indicator(symbol: str, period: str = "1y", window: int = 20) -> tuple:
    """
    Calculate Z-Score indicator score for mean reversion analysis.
    
    Z-Score measures how many standard deviations the current price is from its mean.
    This helps identify potential mean reversion opportunities.
    
    Parameters:
    symbol (str): ticker Yahoo finance 
    period (str): Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
    window (int): The lookback period for calculating mean and standard deviation
    
    Returns:
    tuple: (current_zscore, current_score, current_price, current_mean, current_std)
    """
    
    data = yf.download(symbol, period=period, multi_level_index=False) 
    close = data['Close']
    
    # Calculate rolling mean and standard deviation
    rolling_mean = close.rolling(window=window).mean()
    rolling_std = close.rolling(window=window).std()
    
    # Calculate Z-Score
    zscore = (close - rolling_mean) / rolling_std
    
    # Convert to score (-100 to +100), capping at 3 standard deviations
    zscore_score = zscore.clip(-3, 3) * (100/3)
    
    # Get latest values
    current_zscore = float(zscore.iloc[-1])
    current_score = float(zscore_score.iloc[-1])
    current_price = float(close.iloc[-1])
    current_mean = float(rolling_mean.iloc[-1])
    current_std = float(rolling_std.iloc[-1])
    
    return (current_zscore, current_score, current_price, current_mean, current_std)


def calculate_macd_score(
    symbol: str,
    period: str = "1y",
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> str:
    """
    Calculate a MACD score between -100 and 100 for the tickek and given period
    first we create the MACD indicator with the parameters fast_period (int): Fast EMA period, slow_period (int): Slow EMA period and signal_period (int): Signal line period
    The MACD score combines three components:

    ### MACD Line Position vs. Signal Line (40%)

    - Positive when MACD line is above signal line (bullish)
    - Negative when MACD line is below signal line (bearish)


    ### MACD Line Position vs. Zero (30%)

    - Positive when MACD line is above zero (strong bullish trend)
    - Negative when MACD line is below zero (strong bearish trend)


    ### Histogram Momentum (30%)

    Measures the rate of change in the histogram

    - Positive when histogram is increasing (accelerating momentum)
    - Negative when histogram is decreasing (decelerating momentum)

    Parameters:
    symbol (str): ticker Yahoo finance
    period (str): Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max. Either Use period parameter or use start and end
    fast_period (int) : This parameter defines the period (number of days/periods) for the "fast" Exponential Moving Average (EMA). By default, it's set to 12 periods, which is the standard setting for MACD. This shorter period EMA is more responsive to recent price changes.
    slow_period (int) : This parameter defines the period for the "slow" EMA. By default, it's set to 26 periods, which is also standard. This longer period EMA responds more slowly to price changes and captures longer-term trends.
    signal_period( int) : This parameter defines the period for calculating the signal line, which is an EMA of the MACD line itself. By default, it's set to 9 periods, which is the typical setting. The signal line helps identify potential buy/sell signals when it crosses the MACD line.

    Returns:
    (str) : message with:
    Symbol: {symbol}, Period: {period}
    Latest MACD score: {current_macd_score:.2f}
    Latest component 1. MACD line position relative to signal line (40% of score): {current_line_position:.2f}
    Latest component 3: MACD line position relative to zero (30% of score) {current_zero_position:.2f}
    Latest component 3 Histogram direction and momentum (30% of score) : {current_hist_momentum:.2f}
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
    macd_data = pd.DataFrame(
        {
            "macd_line": macd_line,
            "signal_line": signal_line,
            "macd_histogram": macd_histogram,
        },
        index=data.index,
    )

    score = pd.Series(0, index=data.index)

    # Component 1: MACD line position relative to signal line (40% of score)
    # Normalize using typical range
    typical_range = macd_data["macd_line"].std() * 3  # 3 standard deviations

    if typical_range == 0:
        typical_range = 0.001  # Prevent division by zero

    line_position = (macd_data["macd_line"] - macd_data["signal_line"]) / typical_range
    component1 = line_position.clip(-1, 1) * 40

    # Component 2: MACD line position relative to zero (30% of score)
    zero_position = macd_data["macd_line"] / typical_range
    component2 = zero_position.clip(-1, 1) * 30

    # Component 3: Histogram direction and momentum (30% of score)
    # Rate of change in histogram (smoothed)
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
    Symbol: {symbol}, Period: {period}\n
    Latest MACD score: {current_macd_score:.2f}\n
    Latest first component score. MACD line position relative to signal line (40% of score): {current_line_position:.2f}\n
    Latest second component score. MACD line position relative to zero (30% of score): {current_zero_position:.2f}\n
    Latest third component score. Histogram direction and momentum (30% of score) : {current_hist_momentum:.2f}
    """
    return current_macd_score


def calculate_donchian_channel_score(symbol: str, period: str = "1y", window: int = 20):
    """
    Calculate Donchian score for the given symbol, period and window period
    Donchian Channel Score (-100 to +100)

    Parameters:
    symbol (str): ticker Yahoo finance
    period (str): Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max. Either Use period parameter or use start and end
    window (int): The lookback period for calculating channels upper, middle, and lower bands
    ### Price Position Within Channel (50%)

    - +50 when price is at the upper band
    - 0 when price is at the middle band
    - -50 when price is at the lower band

    Donchian Channel Score (-100 to +100). it has 3 components

    ### Channel Direction (30%)

    - Positive when channel is trending upward
    - Negative when channel is trending downward


    ### Channel Width Trend (20%)

    - Positive when channel is widening (increasing volatility)
    - Negative when channel is narrowing (decreasing volatility)
    Returns:
    (str) : message with:
    Symbol: {symbol}, Period: {period}\n
    Latest donchian band score: {current_donchian_score:.2f}\n
    Latest first component score. Position within the channel (50% of score) 0% at lower band, 50% at middle band, 100% at upper band: {current_line_position:.2f}\n
    Latest second component score. Channel direction (30% of score): {current_zero_position:.2f}\n
    Latest third component score. Channel width trend (20% of score) Narrowing channel is bearish, widening is bullish: {current_hist_momentum:.2f}

    """
    data = yf.download(symbol, period=period, multi_level_index=False)
    # Calculate upper and lower bands
    upper_band = data["High"].rolling(window=window).max()
    lower_band = data["Low"].rolling(window=window).min()

    # Calculate middle band (average of upper and lower)
    middle_band = (upper_band + lower_band) / 2

    # Create result DataFrame
    channels = pd.DataFrame(
        {"upper": upper_band, "middle": middle_band, "lower": lower_band},
        index=data.index,
    )

    score = pd.Series(0, index=data.index)

    # Component 1: Position within the channel (50% of score)
    # 0% at lower band, 50% at middle band, 100% at upper band
    channel_width = channels["upper"] - channels["lower"]

    # Prevent division by zero
    channel_width = channel_width.replace(0, 0.001)

    position_pct = (data["Close"] - channels["lower"]) / channel_width
    component1 = ((position_pct * 2) - 1) * 50  # Scale to -50 to +50

    # Component 2: Channel direction (30% of score)
    channel_direction = channels["middle"].diff(5).rolling(window=5).mean()
    channel_direction_range = channel_direction.std() * 3

    if channel_direction_range == 0:
        channel_direction_range = 0.001  # Prevent division by zero

    normalized_direction = channel_direction / channel_direction_range
    component2 = normalized_direction.clip(-1, 1) * 30

    # Component 3: Channel width trend (20% of score)
    # Narrowing channel is bearish, widening is bullish
    width_change = channel_width.diff(5).rolling(window=5).mean()
    width_change_range = width_change.std() * 3

    if width_change_range == 0:
        width_change_range = 0.001  # Prevent division by zero

    normalized_width = width_change / width_change_range
    component3 = normalized_width.clip(-1, 1) * 20

    # Combine components
    score = component1 + component2 + component3

    current_donchian_score = float(score.iloc[-1])
    current_line_position = float(component1.iloc[-1])
    current_zero_position = float(component2.iloc[-1])
    current_hist_momentum = float(component3.iloc[-1])
    message = f"""
    Symbol: {symbol}, Period: {period}\n
    Latest donchian band score: {current_donchian_score:.2f}\n
    Latest first component score. Position within the channel (50% of score) 0% at lower band, 50% at middle band, 100% at upper band: {current_line_position:.2f}\n
    Latest second component score. Channel direction (30% of score): {current_zero_position:.2f}\n
    Latest third component score. Channel width trend (20% of score) Narrowing channel is bearish, widening is bullish: {current_hist_momentum:.2f}
    """
    return current_donchian_score