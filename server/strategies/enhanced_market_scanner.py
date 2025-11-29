"""
Enhanced Comprehensive Market Scanner Tool for MCP Server
This version includes detailed performance analysis and individual strategy breakdowns.
Focuses on current signals and market sentiment
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import warnings
import sys
import os

# Suppress all warnings that could interfere with JSON-RPC
warnings.filterwarnings('ignore')
os.environ['YFINANCE_SUPPRESS_WARNINGS'] = 'True'

# Import utility functions
from utils.yahoo_finance_tools import (
    calculate_bollinger_bands,
    find_swing_points,
    calculate_fibonacci_levels,
    calculate_connors_rsi_score,
    calculate_zscore_indicator,
    calculate_macd_score,
    calculate_donchian_channel_score,
)

# Valid periods for yfinance
VALID_PERIODS = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']

def validate_period(period: str) -> str:
    """Validate and fix period parameter"""
    # Common fixes
    period_fixes = {
        '6m': '6mo',
        '3m': '3mo', 
        '1m': '1mo',
        '2m': '2mo',
        '12m': '1y',
        '24m': '2y'
    }
    
    if period in period_fixes:
        return period_fixes[period]
    
    if period not in VALID_PERIODS:
        print(f"Warning: Invalid period '{period}', using '1y' instead", file=sys.stderr)
        return '1y'
    
    return period

def add_enhanced_market_scanner_tool(mcp):
    """Add enhanced market scanner tool with detailed performance analysis"""
    
    @mcp.tool()
    def enhanced_market_scanner(
        symbols,
        period: str = "1y",
        output_format: str = "detailed"
    ) -> str:
        """
        Enhanced market scanner with detailed performance analysis and strategy breakdowns.
        
        Features:
        1. Analyzes each symbol using all 5 strategies
        2. Calculates performance vs buy-and-hold for each strategy
        3. Provides detailed individual strategy tables
        4. Generates comprehensive reasoning for recommendations
        
        Parameters:
        symbols: List of stock ticker symbols (comma-separated string or list)
        period (str): Data period - 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max (default: 1y)
        output_format (str): "detailed", "summary", or "performance" (default: detailed)
        
        Returns:
        str: Enhanced market analysis report with performance metrics
        """
        
        try:
            # Validate and fix period
            period = validate_period(period)
            
            # Handle both list and string inputs
            if isinstance(symbols, str):
                symbol_list = [s.strip().upper() for s in symbols.replace('"', '').replace("'", "").split(',')]
                symbol_list = [s for s in symbol_list if s and s.replace('.', '').replace('-', '').isalnum()]
            elif isinstance(symbols, list):
                symbol_list = [str(s).strip().upper() for s in symbols if str(s).strip()]
            else:
                return "Error: Symbols must be provided as a list or comma-separated string"

            if not symbol_list:
                return "Error: No valid symbols provided for scanning"

            # Limit to prevent overload
            if len(symbol_list) > 15:  # Reduced for detailed analysis
                symbol_list = symbol_list[:15]
                
            analysis_date = datetime.now().strftime("%B %d, %Y")
            
            # Initialize results storage
            results = []
            failed_symbols = []
            
            # Analyze each symbol with detailed performance metrics
            for symbol in symbol_list:
                try:
                    analysis_result = analyze_symbol_with_performance(symbol, period)
                    if analysis_result:
                        results.append(analysis_result)
                    else:
                        failed_symbols.append(symbol)
                except Exception as e:
                    print(f"Error analyzing {symbol}: {str(e)}", file=sys.stderr)
                    failed_symbols.append(symbol)
            
            if not results:
                return f"Error: No valid analysis results for any symbols in {symbol_list}"
            
            # Generate enhanced report based on format
            if output_format.lower() == "summary":
                return generate_enhanced_summary(results, failed_symbols, analysis_date, period)
            elif output_format.lower() == "performance":
                return generate_performance_focused_report(results, failed_symbols, analysis_date, period)
            else:
                return generate_detailed_enhanced_report(results, failed_symbols, analysis_date, period)
                
        except Exception as e:
            print(f"Critical error in enhanced market scanner: {str(e)}", file=sys.stderr)
            return f"Error: Critical failure in enhanced market scanner - {str(e)}"

def analyze_symbol_with_performance(symbol: str, period: str) -> Optional[Dict]:
    """Analyze a single symbol with detailed performance metrics"""
    
    try:
        # Download data for the analysis period
        data = yf.download(symbol, period=period, progress=False, multi_level_index=False)
        if data.empty:
            return None
            
        # Get basic price info
        current_price = float(data['Close'].iloc[-1])
        start_price = float(data['Close'].iloc[0])
        
        price_change_1d = float((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2] * 100) if len(data) > 1 else 0.0
        buy_hold_return = float((current_price - start_price) / start_price * 100)
        
        # Initialize enhanced result dictionary
        result = {
            'symbol': symbol,
            'current_price': current_price,
            'start_price': start_price,
            'price_change_1d': price_change_1d,
            'buy_hold_return': buy_hold_return,
            'strategies': {},
            'performance_metrics': {},
            'overall_score': 0.0,
            'overall_signal': 'NEUTRAL',
            'signal_consensus': 'MIXED',
            'risk_level': 'MEDIUM',
            'recommendation_reasoning': ''
        }
        
        # Strategy 1: Bollinger Z-Score with performance
        try:
            zscore_result, zscore_performance = analyze_bollinger_zscore_with_performance(symbol, period, data)
            result['strategies']['bollinger_zscore'] = zscore_result
            result['performance_metrics']['bollinger_zscore'] = zscore_performance
        except Exception as e:
            result['strategies']['bollinger_zscore'] = {'error': 'Analysis failed', 'score': 0, 'signal': 'NEUTRAL'}
            result['performance_metrics']['bollinger_zscore'] = {'strategy_return': 0, 'excess_return': 0, 'win_rate': 0}
        
        # Strategy 2: Bollinger-Fibonacci with performance
        try:
            fib_result, fib_performance = analyze_bollinger_fibonacci_with_performance(symbol, period, data)
            result['strategies']['bollinger_fibonacci'] = fib_result
            result['performance_metrics']['bollinger_fibonacci'] = fib_performance
        except Exception as e:
            result['strategies']['bollinger_fibonacci'] = {'error': 'Analysis failed', 'score': 0, 'signal': 'NEUTRAL'}
            result['performance_metrics']['bollinger_fibonacci'] = {'strategy_return': 0, 'excess_return': 0, 'win_rate': 0}
        
        # Strategy 3: MACD-Donchian with performance
        try:
            macd_result, macd_performance = analyze_macd_donchian_with_performance(symbol, period, data)
            result['strategies']['macd_donchian'] = macd_result
            result['performance_metrics']['macd_donchian'] = macd_performance
        except Exception as e:
            result['strategies']['macd_donchian'] = {'error': 'Analysis failed', 'score': 0, 'signal': 'NEUTRAL'}
            result['performance_metrics']['macd_donchian'] = {'strategy_return': 0, 'excess_return': 0, 'win_rate': 0}
        
        # Strategy 4: Connors RSI-Z Score with performance
        try:
            connors_result, connors_performance = analyze_connors_zscore_with_performance(symbol, period, data)
            result['strategies']['connors_zscore'] = connors_result
            result['performance_metrics']['connors_zscore'] = connors_performance
        except Exception as e:
            result['strategies']['connors_zscore'] = {'error': 'Analysis failed', 'score': 0, 'signal': 'NEUTRAL'}
            result['performance_metrics']['connors_zscore'] = {'strategy_return': 0, 'excess_return': 0, 'win_rate': 0}
        
        # Strategy 5: Dual Moving Average with performance
        try:
            dual_ma_result, dual_ma_performance = analyze_dual_ma_with_performance(symbol, period, data)
            result['strategies']['dual_ma'] = dual_ma_result
            result['performance_metrics']['dual_ma'] = dual_ma_performance
        except Exception as e:
            result['strategies']['dual_ma'] = {'error': 'Analysis failed', 'score': 0, 'signal': 'NEUTRAL'}
            result['performance_metrics']['dual_ma'] = {'strategy_return': 0, 'excess_return': 0, 'win_rate': 0}
        
        # Calculate enhanced overall metrics
        calculate_enhanced_overall_metrics(result)
        
        return result
        
    except Exception as e:
        print(f"Critical error analyzing {symbol}: {e}", file=sys.stderr)
        return None

def analyze_bollinger_zscore_with_performance(symbol: str, period: str, data: pd.DataFrame) -> Tuple[Dict, Dict]:
    """Analyze Bollinger Z-Score strategy with performance metrics"""
    
    window = 20
    closes = data["Close"]
    rolling_mean = closes.rolling(window=window).mean()
    rolling_std = closes.rolling(window=window).std()
    z_score = (closes - rolling_mean) / rolling_std
    
    latest_z_score = float(z_score.iloc[-1])
    
    # Generate trading signals
    data_copy = data.copy()
    data_copy['z_score'] = z_score
    data_copy['signal'] = 'HOLD'
    data_copy.loc[z_score < -2, 'signal'] = 'BUY'
    data_copy.loc[z_score > 2, 'signal'] = 'SELL'
    
    # Calculate performance
    performance = calculate_strategy_performance(data_copy, 'signal')
    
    # Determine current signal
    if latest_z_score > 2:
        signal = "STRONG_SELL"
        score = -80.0
        confidence = min(abs(latest_z_score - 2) * 40 + 60, 100)
    elif latest_z_score > 1:
        signal = "SELL"
        score = -40.0
        confidence = min(abs(latest_z_score - 1) * 40 + 40, 100)
    elif latest_z_score < -2:
        signal = "STRONG_BUY"
        score = 80.0
        confidence = min(abs(latest_z_score + 2) * 40 + 60, 100)
    elif latest_z_score < -1:
        signal = "BUY"
        score = 40.0
        confidence = min(abs(latest_z_score + 1) * 40 + 40, 100)
    else:
        signal = "NEUTRAL"
        score = float(latest_z_score * 20)
        confidence = 50 - abs(latest_z_score) * 25
    
    strategy_result = {
        'z_score': latest_z_score,
        'signal': signal,
        'score': score,
        'confidence': max(confidence, 0),
        'description': f"Z-Score: {latest_z_score:.2f} - {'Oversold' if latest_z_score < -1 else 'Overbought' if latest_z_score > 1 else 'Normal'}",
        'interpretation': get_zscore_interpretation(latest_z_score)
    }
    
    return strategy_result, performance

def analyze_bollinger_fibonacci_with_performance(symbol: str, period: str, data: pd.DataFrame) -> Tuple[Dict, Dict]:
    """Analyze Bollinger-Fibonacci strategy with performance metrics"""
    
    window = 20
    
    # Calculate Bollinger Bands
    try:
        calculate_bollinger_bands(data, symbol, period, window, 2)
    except Exception:
        pass
    
    # Calculate basic strategy score
    if "%B" in data.columns and not data["%B"].isna().iloc[-1]:
        bb_score = float((0.5 - data["%B"].iloc[-1]) * 50)
        percentB = float(data["%B"].iloc[-1])
    else:
        bb_score = 0.0
        percentB = 0.5
    
    # Generate signals based on %B
    data_copy = data.copy()
    data_copy['bb_score'] = (0.5 - data.get("%B", 0.5)) * 50
    data_copy['signal'] = 'HOLD'
    data_copy.loc[data_copy['bb_score'] > 20, 'signal'] = 'BUY'
    data_copy.loc[data_copy['bb_score'] < -20, 'signal'] = 'SELL'
    
    # Calculate performance
    performance = calculate_strategy_performance(data_copy, 'signal')
    
    # Determine signal
    if bb_score > 20:
        signal = "BUY"
        score = bb_score
        confidence = min(abs(bb_score - 20) * 2 + 60, 100)
    elif bb_score < -20:
        signal = "SELL"
        score = bb_score
        confidence = min(abs(bb_score + 20) * 2 + 60, 100)
    else:
        signal = "NEUTRAL"
        score = bb_score
        confidence = 50 - abs(bb_score) * 1.5
    
    strategy_result = {
        'bb_score': bb_score,
        'percent_b': percentB,
        'signal': signal,
        'score': score,
        'confidence': max(confidence, 0),
        'description': f"BB-Fib Score: {bb_score:.1f} - {signal}",
        'interpretation': get_bollinger_interpretation(percentB)
    }
    
    return strategy_result, performance

def analyze_macd_donchian_with_performance(symbol: str, period: str, data: pd.DataFrame) -> Tuple[Dict, Dict]:
    """Analyze MACD-Donchian strategy with performance metrics"""
    
    # Calculate MACD and Donchian scores
    macd_score = calculate_macd_score(symbol, period)
    donchian_score = calculate_donchian_channel_score(symbol, period)
    
    combined_score = (float(macd_score) + float(donchian_score)) / 2
    
    # Generate signals
    data_copy = data.copy()
    data_copy['combined_score'] = combined_score
    data_copy['signal'] = 'HOLD'
    data_copy.loc[combined_score > 25, 'signal'] = 'BUY'
    data_copy.loc[combined_score < -25, 'signal'] = 'SELL'
    
    # Calculate performance
    performance = calculate_strategy_performance(data_copy, 'signal')
    
    if combined_score > 25:
        signal = "BUY"
        confidence = min(abs(combined_score - 25) * 2 + 60, 100)
    elif combined_score < -25:
        signal = "SELL" 
        confidence = min(abs(combined_score + 25) * 2 + 60, 100)
    else:
        signal = "NEUTRAL"
        confidence = 50 - abs(combined_score) * 1.5
    
    strategy_result = {
        'macd_score': float(macd_score),
        'donchian_score': float(donchian_score),
        'combined_score': combined_score,
        'signal': signal,
        'score': combined_score,
        'confidence': max(confidence, 0),
        'description': f"MACD-Don Score: {combined_score:.1f} - {signal}",
        'interpretation': get_macd_donchian_interpretation(float(macd_score), float(donchian_score))
    }
    
    return strategy_result, performance

def analyze_connors_zscore_with_performance(symbol: str, period: str, data: pd.DataFrame) -> Tuple[Dict, Dict]:
    """Analyze Connors RSI-Z Score strategy with performance metrics"""
    
    # Calculate components
    current_crsi, connors_score, _, _, _ = calculate_connors_rsi_score(symbol, period)
    current_zscore, zscore_score, _, _, _ = calculate_zscore_indicator(symbol, period)
    
    # Combined score (70% Connors, 30% Z-Score)
    combined_score = (float(connors_score) * 0.7) + (float(zscore_score) * 0.3)
    
    # Generate signals
    data_copy = data.copy()
    data_copy['combined_score'] = combined_score
    data_copy['signal'] = 'HOLD'
    data_copy.loc[combined_score > 25, 'signal'] = 'BUY'
    data_copy.loc[combined_score < -25, 'signal'] = 'SELL'
    
    # Calculate performance
    performance = calculate_strategy_performance(data_copy, 'signal')
    
    if combined_score > 25:
        signal = "BUY"
        confidence = min(abs(combined_score - 25) * 2 + 60, 100)
    elif combined_score < -25:
        signal = "SELL"
        confidence = min(abs(combined_score + 25) * 2 + 60, 100)
    else:
        signal = "NEUTRAL"
        confidence = 50 - abs(combined_score) * 1.5
    
    strategy_result = {
        'connors_rsi': float(current_crsi),
        'z_score': float(current_zscore),
        'combined_score': combined_score,
        'signal': signal,
        'score': combined_score,
        'confidence': max(confidence, 0),
        'description': f"Connors-Z Score: {combined_score:.1f} - {signal}",
        'interpretation': get_connors_zscore_interpretation(float(current_crsi), float(current_zscore))
    }
    
    return strategy_result, performance

def analyze_dual_ma_with_performance(symbol: str, period: str, data: pd.DataFrame) -> Tuple[Dict, Dict]:
    """Analyze Dual Moving Average strategy with performance metrics"""
    
    # Calculate EMAs
    short_period, long_period = 50, 200
    ema_short = data['Close'].ewm(span=short_period).mean()
    ema_long = data['Close'].ewm(span=long_period).mean()
    
    current_short_ema = float(ema_short.iloc[-1])
    current_long_ema = float(ema_long.iloc[-1])
    
    # Generate signals
    data_copy = data.copy()
    data_copy['ema_short'] = ema_short
    data_copy['ema_long'] = ema_long
    data_copy['signal'] = 'HOLD'
    
    # Golden Cross (short > long) = BUY, Death Cross (short < long) = SELL
    short_above_long = ema_short > ema_long
    short_above_long_prev = short_above_long.shift(1)
    
    golden_cross = (short_above_long & ~short_above_long_prev.fillna(False))
    death_cross = (~short_above_long & short_above_long_prev.fillna(True))
    
    data_copy.loc[golden_cross, 'signal'] = 'BUY'
    data_copy.loc[death_cross, 'signal'] = 'SELL'
    
    # Calculate performance
    performance = calculate_strategy_performance(data_copy, 'signal')
    
    # Calculate current metrics
    ma_separation = (current_short_ema - current_long_ema) / current_long_ema * 100
    score = float(np.clip(ma_separation * 10, -100, 100))
    
    if score > 20:
        signal = "BUY"
        confidence = min(abs(score - 20) * 2 + 60, 100)
    elif score < -20:
        signal = "SELL"
        confidence = min(abs(score + 20) * 2 + 60, 100)
    else:
        signal = "NEUTRAL"
        confidence = 50 - abs(score) * 1.5
    
    trend = "BULLISH" if current_short_ema > current_long_ema else "BEARISH"
    
    strategy_result = {
        'ma_separation': ma_separation,
        'ema_short': current_short_ema,
        'ema_long': current_long_ema,
        'trend': trend,
        'signal': signal,
        'score': score,
        'confidence': max(confidence, 0),
        'description': f"Dual MA: {trend} - {signal}",
        'interpretation': get_dual_ma_interpretation(ma_separation, trend)
    }
    
    return strategy_result, performance

def calculate_strategy_performance(data: pd.DataFrame, signal_col: str) -> Dict:
    """Calculate strategy performance metrics vs buy and hold"""
    
    try:
        # Calculate returns
        data_copy = data.copy()
        data_copy['returns'] = data_copy['Close'].pct_change()
        
        # Create position based on signals
        data_copy['position'] = 0
        data_copy.loc[data_copy[signal_col] == 'BUY', 'position'] = 1
        data_copy.loc[data_copy[signal_col] == 'SELL', 'position'] = -1
        
        # Forward fill positions
        data_copy['position'] = data_copy['position'].replace(0, np.nan).ffill().fillna(0)
        
        # Calculate strategy returns
        data_copy['strategy_returns'] = data_copy['position'].shift(1) * data_copy['returns']
        
        # Performance metrics
        total_return = float((data_copy['Close'].iloc[-1] / data_copy['Close'].iloc[0] - 1) * 100)
        strategy_return = float((1 + data_copy['strategy_returns']).prod() - 1) * 100
        excess_return = strategy_return - total_return
        
        # Trading metrics
        signals = data_copy[data_copy[signal_col].isin(['BUY', 'SELL'])]
        total_trades = len(signals)
        
        # Win rate calculation
        if total_trades > 0:
            trade_returns = []
            position = 0
            entry_price = 0
            
            for idx, row in signals.iterrows():
                if row[signal_col] == 'BUY' and position <= 0:
                    if position < 0 and entry_price > 0:
                        trade_return = (entry_price - row['Close']) / entry_price
                        trade_returns.append(trade_return)
                    entry_price = row['Close']
                    position = 1
                elif row[signal_col] == 'SELL' and position >= 0:
                    if position > 0 and entry_price > 0:
                        trade_return = (row['Close'] - entry_price) / entry_price
                        trade_returns.append(trade_return)
                    entry_price = row['Close']
                    position = -1
            
            win_rate = float(len([r for r in trade_returns if r > 0]) / len(trade_returns) * 100) if trade_returns else 0
        else:
            win_rate = 0
        
        # Volatility
        strategy_vol = float(data_copy['strategy_returns'].std() * np.sqrt(252) * 100)
        buyhold_vol = float(data_copy['returns'].std() * np.sqrt(252) * 100)
        
        # Sharpe ratio (simplified, assuming 0% risk-free rate)
        sharpe_ratio = float((strategy_return / strategy_vol) if strategy_vol > 0 else 0)
        
        return {
            'strategy_return': strategy_return,
            'buyhold_return': total_return,
            'excess_return': excess_return,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'strategy_volatility': strategy_vol,
            'buyhold_volatility': buyhold_vol,
            'sharpe_ratio': sharpe_ratio
        }
        
    except Exception as e:
        return {
            'strategy_return': 0,
            'buyhold_return': 0,
            'excess_return': 0,
            'win_rate': 0,
            'total_trades': 0,
            'strategy_volatility': 0,
            'buyhold_volatility': 0,
            'sharpe_ratio': 0
        }

def get_zscore_interpretation(z_score: float) -> str:
    """Get interpretation for Z-Score"""
    if z_score > 2:
        return "Price extremely overbought, strong mean reversion expected"
    elif z_score > 1:
        return "Price moderately overbought, potential pullback ahead"
    elif z_score < -2:
        return "Price extremely oversold, strong bounce potential"
    elif z_score < -1:
        return "Price moderately oversold, upside opportunity"
    else:
        return "Price trading within normal statistical range"

def get_bollinger_interpretation(percent_b: float) -> str:
    """Get interpretation for Bollinger %B"""
    if percent_b > 0.8:
        return "Price near upper band, potential reversal zone"
    elif percent_b < 0.2:
        return "Price near lower band, potential support zone"
    else:
        return "Price within normal Bollinger Band range"

def get_macd_donchian_interpretation(macd: float, donchian: float) -> str:
    """Get interpretation for MACD-Donchian combination"""
    if macd > 0 and donchian > 0:
        return "Both momentum and breakout indicators bullish"
    elif macd < 0 and donchian < 0:
        return "Both momentum and breakout indicators bearish"
    else:
        return "Mixed signals between momentum and breakout indicators"

def get_connors_zscore_interpretation(crsi: float, zscore: float) -> str:
    """Get interpretation for Connors RSI-Z Score combination"""
    if crsi < 20 and zscore < -1:
        return "Both short-term momentum and mean reversion suggest oversold"
    elif crsi > 80 and zscore > 1:
        return "Both short-term momentum and mean reversion suggest overbought"
    else:
        return "Mixed short-term momentum and mean reversion signals"

def get_dual_ma_interpretation(separation: float, trend: str) -> str:
    """Get interpretation for Dual Moving Average"""
    if abs(separation) > 5:
        return f"Strong {trend.lower()} trend with significant MA separation"
    elif abs(separation) > 2:
        return f"Moderate {trend.lower()} trend developing"
    else:
        return "Weak trend, MAs converging - potential direction change"

def calculate_enhanced_overall_metrics(result: Dict):
    """Calculate enhanced overall metrics with reasoning"""
    
    try:
        valid_strategies = [s for s in result['strategies'].values() if 'error' not in s]
        
        if not valid_strategies:
            result['overall_score'] = 0.0
            result['overall_signal'] = 'ERROR'
            result['recommendation_reasoning'] = 'Unable to analyze - insufficient data'
            return
        
        # Calculate weighted scores (performance-adjusted)
        scores = []
        signals = []
        performance_weights = []
        
        for strategy_name, strategy_data in result['strategies'].items():
            if 'error' not in strategy_data:
                strategy_score = float(strategy_data.get('score', 0))
                strategy_signal = strategy_data.get('signal', 'NEUTRAL')
                
                # Get performance metrics for weighting
                perf_data = result['performance_metrics'].get(strategy_name, {})
                excess_return = perf_data.get('excess_return', 0)
                win_rate = perf_data.get('win_rate', 50)
                
                # Calculate performance weight (better performing strategies get higher weight)
                perf_weight = max(0.5, min(2.0, (excess_return / 10 + win_rate / 100 + 1)))
                
                scores.append(strategy_score * perf_weight)
                signals.append(strategy_signal)
                performance_weights.append(perf_weight)
        
        # Weighted overall score
        if performance_weights:
            result['overall_score'] = float(np.average(scores, weights=performance_weights))
        else:
            result['overall_score'] = float(np.mean(scores))
        
        # Signal consensus analysis
        buy_signals = sum(1 for s in signals if 'BUY' in s)
        sell_signals = sum(1 for s in signals if 'SELL' in s)
        neutral_signals = len(signals) - buy_signals - sell_signals
        
        # Determine overall signal
        if result['overall_score'] > 30:
            result['overall_signal'] = 'STRONG_BUY'
        elif result['overall_score'] > 15:
            result['overall_signal'] = 'BUY'
        elif result['overall_score'] < -30:
            result['overall_signal'] = 'STRONG_SELL'
        elif result['overall_score'] < -15:
            result['overall_signal'] = 'SELL'
        else:
            result['overall_signal'] = 'NEUTRAL'
        
        # Signal consensus
        total_signals = len(signals)
        if buy_signals > total_signals * 0.6:
            result['signal_consensus'] = 'BULLISH_CONSENSUS'
        elif sell_signals > total_signals * 0.6:
            result['signal_consensus'] = 'BEARISH_CONSENSUS'
        elif neutral_signals > total_signals * 0.6:
            result['signal_consensus'] = 'NEUTRAL_CONSENSUS'
        else:
            result['signal_consensus'] = 'MIXED_SIGNALS'
        
        # Risk level based on volatility and confidence
        avg_volatility = np.mean([result['performance_metrics'].get(s, {}).get('strategy_volatility', 20) 
                                  for s in result['performance_metrics']])
        
        if avg_volatility > 30:
            result['risk_level'] = 'HIGH_RISK'
        elif avg_volatility > 20:
            result['risk_level'] = 'MEDIUM_RISK'
        else:
            result['risk_level'] = 'LOW_RISK'
        
        # Generate reasoning
        result['recommendation_reasoning'] = generate_recommendation_reasoning(result)
        
    except Exception:
        result['overall_score'] = 0.0
        result['overall_signal'] = 'ERROR'
        result['signal_consensus'] = 'ERROR'
        result['risk_level'] = 'ERROR'
        result['recommendation_reasoning'] = 'Error in analysis calculations'

def generate_recommendation_reasoning(result: Dict) -> str:
    """Generate detailed reasoning for the recommendation"""
    
    try:
        reasoning_parts = []
        
        # Performance analysis
        avg_excess_return = np.mean([result['performance_metrics'].get(s, {}).get('excess_return', 0) 
                                     for s in result['performance_metrics']])
        
        if avg_excess_return > 5:
            reasoning_parts.append(f"Strategies show strong outperformance vs buy-hold (+{avg_excess_return:.1f}%)")
        elif avg_excess_return > 0:
            reasoning_parts.append(f"Strategies show modest outperformance vs buy-hold (+{avg_excess_return:.1f}%)")
        else:
            reasoning_parts.append(f"Strategies underperform buy-hold ({avg_excess_return:.1f}%)")
        
        # Signal consensus
        signals = [result['strategies'][s].get('signal', 'NEUTRAL') for s in result['strategies'] if 'error' not in result['strategies'][s]]
        buy_count = sum(1 for s in signals if 'BUY' in s)
        sell_count = sum(1 for s in signals if 'SELL' in s)
        
        if buy_count > sell_count:
            reasoning_parts.append(f"{buy_count}/{len(signals)} strategies signal bullish")
        elif sell_count > buy_count:
            reasoning_parts.append(f"{sell_count}/{len(signals)} strategies signal bearish")
        else:
            reasoning_parts.append("Mixed signals across strategies")
        
        # Risk assessment
        avg_win_rate = np.mean([result['performance_metrics'].get(s, {}).get('win_rate', 50) 
                                for s in result['performance_metrics']])
        
        if avg_win_rate > 60:
            reasoning_parts.append(f"High reliability ({avg_win_rate:.0f}% avg win rate)")
        elif avg_win_rate > 50:
            reasoning_parts.append(f"Moderate reliability ({avg_win_rate:.0f}% avg win rate)")
        else:
            reasoning_parts.append(f"Lower reliability ({avg_win_rate:.0f}% avg win rate)")
        
        # Specific strategy highlights
        best_performing = max(result['performance_metrics'].items(), 
                             key=lambda x: x[1].get('excess_return', -999))
        
        if best_performing[1].get('excess_return', 0) > 5:
            reasoning_parts.append(f"Best strategy: {best_performing[0].replace('_', ' ').title()} (+{best_performing[1]['excess_return']:.1f}%)")
        
        return ". ".join(reasoning_parts) + "."
        
    except Exception:
        return "Analysis completed with mixed results across multiple technical indicators."

def generate_detailed_enhanced_report(results: List[Dict], failed_symbols: List[str], analysis_date: str, period: str) -> str:
    """Generate detailed enhanced report with all performance metrics"""
    
    try:
        # Sort results by overall score
        results.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Categorize results
        strong_buys = [r for r in results if r['overall_signal'] == 'STRONG_BUY']
        buys = [r for r in results if r['overall_signal'] == 'BUY']
        neutrals = [r for r in results if r['overall_signal'] == 'NEUTRAL']
        sells = [r for r in results if r['overall_signal'] == 'SELL']
        strong_sells = [r for r in results if r['overall_signal'] == 'STRONG_SELL']
        
        report = f"""# Enhanced Comprehensive Market Analysis Report
*Analysis Date: {analysis_date}*  
*Period: {period} | Analyzed: {len(results)} symbols | Failed: {len(failed_symbols)}*

## Executive Summary

This enhanced analysis combines five technical strategies with detailed performance metrics versus buy-and-hold. Each strategy is evaluated on its historical effectiveness and current signal strength.

### Market Overview
- **Strong Buy Signals:** {len(strong_buys)} stocks ({len(strong_buys)/len(results)*100:.1f}%)
- **Buy Signals:** {len(buys)} stocks ({len(buys)/len(results)*100:.1f}%)
- **Neutral:** {len(neutrals)} stocks ({len(neutrals)/len(results)*100:.1f}%)
- **Sell Signals:** {len(sells)} stocks ({len(sells)/len(results)*100:.1f}%)
- **Strong Sell Signals:** {len(strong_sells)} stocks ({len(strong_sells)/len(results)*100:.1f}%)

## Overall Performance Rankings

| Rank | Symbol | Price | 1D % | Overall Score | Signal | Buy&Hold % | Best Strategy Excess % | Risk Level |
|------|--------|-------|------|---------------|--------|------------|----------------------|------------|
"""
        
        # Add top opportunities with performance data
        for i, result in enumerate(results[:12], 1):
            price_change_emoji = "🟢" if result['price_change_1d'] > 0 else "🔴" if result['price_change_1d'] < 0 else "⚪"
            
            # Find best performing strategy
            best_excess = max([result['performance_metrics'].get(s, {}).get('excess_return', -999) 
                              for s in result['performance_metrics']])
            
            report += f"| {i} | {result['symbol']} | ${result['current_price']:.2f} | {price_change_emoji} {result['price_change_1d']:+.1f}% | {result['overall_score']:.1f} | {result['overall_signal']} | {result['buy_hold_return']:+.1f}% | {best_excess:+.1f}% | {result['risk_level'].replace('_', ' ')} |\n"
        
        # Detailed analysis for top picks
        if strong_buys:
            report += f"""

## 🟢 Strong Buy Recommendations ({len(strong_buys)} stocks)

These stocks show compelling bullish signals with strong performance validation:

"""
            for stock in strong_buys[:3]:
                report += generate_detailed_stock_analysis(stock)
        
        if buys:
            report += f"""

## 🔵 Buy Opportunities ({len(buys)} stocks)

These stocks show moderate bullish signals:

"""
            for stock in buys[:2]:
                report += generate_detailed_stock_analysis(stock)
        
        if strong_sells:
            report += f"""

## 🔴 Strong Sell Warnings ({len(strong_sells)} stocks)

These stocks show concerning bearish signals:

"""
            for stock in strong_sells[-2:]:
                report += generate_detailed_stock_analysis(stock)
        
        # Strategy performance comparison
        report += generate_strategy_performance_tables(results)
        
        # Market sentiment and conclusion
        report += generate_market_conclusion(results, period)
        
        if failed_symbols:
            report += f"""

## ⚠️ Analysis Failures
Could not analyze: {', '.join(failed_symbols)}

"""
        
        report += """
---
*This analysis is for educational purposes only and should not be considered as financial advice. Past performance does not guarantee future results.*
"""
        
        return report
        
    except Exception as e:
        return f"Error generating detailed report: {str(e)}"

def generate_detailed_stock_analysis(stock: Dict) -> str:
    """Generate detailed individual stock analysis"""
    
    analysis = f"""
### {stock['symbol']} - ${stock['current_price']:.2f} ({stock['price_change_1d']:+.1f}%)

**Overall Assessment:** {stock['overall_signal']} (Score: {stock['overall_score']:.1f})  
**Buy & Hold Return ({stock.get('period', '1y')}):** {stock['buy_hold_return']:+.1f}%  
**Signal Consensus:** {stock['signal_consensus'].replace('_', ' ')}  
**Risk Level:** {stock['risk_level'].replace('_', ' ')}

**Recommendation Reasoning:** {stock['recommendation_reasoning']}

#### Individual Strategy Analysis:

| Strategy | Signal | Score | Confidence | Performance vs B&H | Win Rate | Interpretation |
|----------|--------|-------|------------|-------------------|----------|----------------|
"""
    
    for strategy_name, strategy_data in stock['strategies'].items():
        if 'error' not in strategy_data:
            strategy_display = strategy_name.replace('_', ' ').title()
            perf_data = stock['performance_metrics'].get(strategy_name, {})
            
            analysis += f"| {strategy_display} | {strategy_data.get('signal', 'N/A')} | {strategy_data.get('score', 0):.1f} | {strategy_data.get('confidence', 0):.0f}% | {perf_data.get('excess_return', 0):+.1f}% | {perf_data.get('win_rate', 0):.0f}% | {strategy_data.get('interpretation', 'N/A')} |\n"
    
    analysis += "\n"
    return analysis

def generate_strategy_performance_tables(results: List[Dict]) -> str:
    """Generate comprehensive strategy performance comparison"""
    
    strategy_names = ['bollinger_zscore', 'bollinger_fibonacci', 'macd_donchian', 'connors_zscore', 'dual_ma']
    
    report = """

## 📊 Strategy Performance Analysis

### Strategy Effectiveness Comparison

| Strategy | Avg Excess Return | Avg Win Rate | Success Rate | Best For | Avg Confidence |
|----------|------------------|-------------|--------------|----------|----------------|
"""
    
    for strategy in strategy_names:
        strategy_display = strategy.replace('_', ' ').title()
        
        # Collect performance data across all stocks
        excess_returns = []
        win_rates = []
        confidences = []
        successes = 0
        
        for result in results:
            if strategy in result['performance_metrics']:
                perf = result['performance_metrics'][strategy]
                excess_returns.append(perf.get('excess_return', 0))
                win_rates.append(perf.get('win_rate', 0))
                
                if perf.get('excess_return', 0) > 0:
                    successes += 1
                    
            if strategy in result['strategies'] and 'error' not in result['strategies'][strategy]:
                confidences.append(result['strategies'][strategy].get('confidence', 0))
        
        avg_excess = np.mean(excess_returns) if excess_returns else 0
        avg_win_rate = np.mean(win_rates) if win_rates else 0
        avg_confidence = np.mean(confidences) if confidences else 0
        success_rate = (successes / len(results) * 100) if results else 0
        
        # Determine what each strategy is best for
        best_for = ""
        if "zscore" in strategy:
            best_for = "Mean Reversion"
        elif "macd" in strategy:
            best_for = "Trend Momentum"
        elif "fibonacci" in strategy:
            best_for = "Support/Resistance"
        elif "connors" in strategy:
            best_for = "Short-term Timing"
        elif "dual_ma" in strategy:
            best_for = "Trend Following"
        
        report += f"| {strategy_display} | {avg_excess:+.1f}% | {avg_win_rate:.0f}% | {success_rate:.0f}% | {best_for} | {avg_confidence:.0f}% |\n"
    
    return report

def generate_market_conclusion(results: List[Dict], period: str) -> str:
    """Generate comprehensive market conclusion with reasoning"""
    
    # Calculate market metrics
    total_stocks = len(results)
    bullish_stocks = len([r for r in results if 'BUY' in r['overall_signal']])
    bearish_stocks = len([r for r in results if 'SELL' in r['overall_signal']])
    
    avg_score = np.mean([r['overall_score'] for r in results])
    avg_buy_hold = np.mean([r['buy_hold_return'] for r in results])
    
    # Determine market sentiment
    if bullish_stocks > bearish_stocks * 1.5:
        market_sentiment = "BULLISH"
        sentiment_emoji = "🟢"
    elif bearish_stocks > bullish_stocks * 1.5:
        market_sentiment = "BEARISH" 
        sentiment_emoji = "🔴"
    else:
        market_sentiment = "NEUTRAL"
        sentiment_emoji = "🟡"
    
    conclusion = f"""

## 🎯 Market Conclusion & Strategic Recommendations

### Overall Market Sentiment: {sentiment_emoji} {market_sentiment}

**Key Findings:**
- **Average Technical Score:** {avg_score:.1f}/100
- **Average Buy & Hold Performance:** {avg_buy_hold:+.1f}% over {period}
- **Bullish Signals:** {bullish_stocks}/{total_stocks} stocks ({bullish_stocks/total_stocks*100:.1f}%)
- **Bearish Signals:** {bearish_stocks}/{total_stocks} stocks ({bearish_stocks/total_stocks*100:.1f}%)

### Strategic Recommendations:

"""
    
    if market_sentiment == "BULLISH":
        conclusion += """
**🟢 BULLISH MARKET ENVIRONMENT**

**Recommended Actions:**
1. **Focus on Strong Buy signals** - These stocks show both technical strength and performance validation
2. **Gradual position building** - Consider scaling into positions on any weakness
3. **Sector diversification** - Spread risk across multiple winning positions
4. **Momentum strategies** - MACD-Donchian and Dual MA strategies likely to perform well

**Risk Management:**
- Use 7-10% stop losses below key technical support levels
- Take partial profits at 15-20% gains
- Monitor for reversal signals from mean reversion indicators

"""
    elif market_sentiment == "BEARISH":
        conclusion += """
**🔴 BEARISH MARKET ENVIRONMENT**

**Recommended Actions:**
1. **Defensive positioning** - Reduce exposure or consider short positions on Strong Sell signals
2. **Cash preservation** - Maintain higher cash levels for future opportunities
3. **Mean reversion focus** - Bollinger Z-Score strategy may identify oversold bounces
4. **Quality bias** - Focus on financially strong companies if investing

**Risk Management:**
- Tighter stop losses (5-7%) in downtrending environment
- Avoid catching falling knives - wait for confirmed reversals
- Consider protective puts or hedging strategies

"""
    else:
        conclusion += """
**🟡 NEUTRAL/MIXED MARKET ENVIRONMENT**

**Recommended Actions:**
1. **Selective approach** - Focus only on highest conviction Strong Buy signals
2. **Range trading** - Use Bollinger-Fibonacci for support/resistance levels
3. **Patience** - Wait for clearer directional signals before major positioning
4. **Strategy diversification** - No single approach dominates, use multiple strategies

**Risk Management:**
- Balanced position sizing - avoid overconcentration
- Quick profit taking on 10-15% moves
- Stay flexible and ready to adjust as trends develop

"""
    
    # Add performance-based insights
    best_performing_stocks = sorted(results, key=lambda x: x['overall_score'], reverse=True)[:3]
    worst_performing_stocks = sorted(results, key=lambda x: x['overall_score'])[:2]
    
    conclusion += f"""
### Top Opportunities:
"""
    for i, stock in enumerate(best_performing_stocks, 1):
        conclusion += f"{i}. **{stock['symbol']}** (Score: {stock['overall_score']:.1f}) - {stock['recommendation_reasoning']}\n"
    
    conclusion += f"""
### Stocks to Avoid:
"""
    for i, stock in enumerate(worst_performing_stocks, 1):
        conclusion += f"{i}. **{stock['symbol']}** (Score: {stock['overall_score']:.1f}) - Weak technical signals across multiple indicators\n"
    
    conclusion += f"""

### Final Market Assessment:

The current analysis of {total_stocks} stocks over the {period} period reveals a **{market_sentiment.lower()}** bias in technical indicators. With an average technical score of {avg_score:.1f} and {bullish_stocks/total_stocks*100:.1f}% of stocks showing bullish signals, the market environment {'favors long positions with selective stock picking' if market_sentiment == 'BULLISH' else 'suggests caution with defensive positioning' if market_sentiment == 'BEARISH' else 'requires patience and selective opportunities'}.

**Strategy Effectiveness:** Multiple technical approaches show varying degrees of success, with mean reversion and momentum strategies providing complementary signals for optimal decision-making.

**Risk Assessment:** Current market conditions present {'moderate to high opportunity with manageable risks' if market_sentiment == 'BULLISH' else 'elevated risks requiring defensive measures' if market_sentiment == 'BEARISH' else 'mixed risk-reward scenarios requiring careful analysis'}.

"""
    
    return conclusion

def generate_enhanced_summary(results: List[Dict], failed_symbols: List[str], analysis_date: str, period: str) -> str:
    """Generate enhanced summary report"""
    
    results.sort(key=lambda x: x['overall_score'], reverse=True)
    
    strong_buys = [r for r in results if r['overall_signal'] == 'STRONG_BUY']
    buys = [r for r in results if r['overall_signal'] == 'BUY']
    sells = [r for r in results if r['overall_signal'] == 'SELL']
    strong_sells = [r for r in results if r['overall_signal'] == 'STRONG_SELL']
    
    avg_buy_hold = np.mean([r['buy_hold_return'] for r in results])
    avg_score = np.mean([r['overall_score'] for r in results])
    
    summary = f"""ENHANCED MARKET SCANNER SUMMARY - {analysis_date}
{'='*60}

PERIOD: {period} | ANALYZED: {len(results)} | FAILED: {len(failed_symbols)}
AVERAGE BUY & HOLD RETURN: {avg_buy_hold:+.1f}%
AVERAGE TECHNICAL SCORE: {avg_score:.1f}/100

SIGNAL DISTRIBUTION:
• Strong Buy: {len(strong_buys)} ({len(strong_buys)/len(results)*100:.1f}%)
• Buy: {len(buys)} ({len(buys)/len(results)*100:.1f}%)  
• Neutral: {len(results) - len(strong_buys) - len(buys) - len(sells) - len(strong_sells)} ({(len(results) - len(strong_buys) - len(buys) - len(sells) - len(strong_sells))/len(results)*100:.1f}%)
• Sell: {len(sells)} ({len(sells)/len(results)*100:.1f}%)
• Strong Sell: {len(strong_sells)} ({len(strong_sells)/len(results)*100:.1f}%)

TOP 10 OPPORTUNITIES:
"""
    
    for i, result in enumerate(results[:10], 1):
        best_excess = max([result['performance_metrics'].get(s, {}).get('excess_return', -999) 
                          for s in result['performance_metrics']])
        summary += f"{i:2d}. {result['symbol']:6s} | ${result['current_price']:7.2f} | Score: {result['overall_score']:5.1f} | B&H: {result['buy_hold_return']:+5.1f}% | Best: {best_excess:+5.1f}% | {result['overall_signal']}\n"
    
    if strong_buys:
        summary += f"\nSTRONG BUY RECOMMENDATIONS:\n"
        for stock in strong_buys[:5]:
            summary += f"• {stock['symbol']} - {stock['recommendation_reasoning']}\n"
    
    bullish_count = len(strong_buys) + len(buys)
    bearish_count = len(sells) + len(strong_sells)
    market_sentiment = 'BULLISH' if bullish_count > bearish_count else 'BEARISH' if bearish_count > bullish_count else 'NEUTRAL'
    
    summary += f"\nMARKET SENTIMENT: {market_sentiment}"
    summary += f"\nRECOMMENDATION: {'SELECTIVE BUYING OPPORTUNITIES' if market_sentiment == 'BULLISH' else 'DEFENSIVE POSITIONING ADVISED' if market_sentiment == 'BEARISH' else 'WAIT FOR CLEARER SIGNALS'}"
    
    return summary

def generate_performance_focused_report(results: List[Dict], failed_symbols: List[str], analysis_date: str, period: str) -> str:
    """Generate performance-focused report"""
    
    results.sort(key=lambda x: x['overall_score'], reverse=True)
    
    report = f"""# Performance-Focused Market Analysis
*Date: {analysis_date} | Period: {period}*

## Performance Summary

| Symbol | Buy & Hold | Best Strategy | Excess Return | Overall Signal | Reasoning |
|--------|------------|---------------|---------------|----------------|-----------|
"""
    
    for result in results:
        best_strategy = max(result['performance_metrics'].items(), 
                           key=lambda x: x[1].get('excess_return', -999))
        best_excess = best_strategy[1].get('excess_return', 0)
        
        report += f"| {result['symbol']} | {result['buy_hold_return']:+.1f}% | {best_strategy[0].replace('_', ' ').title()} | {best_excess:+.1f}% | {result['overall_signal']} | {result['recommendation_reasoning'][:50]}... |\n"
    
    return report