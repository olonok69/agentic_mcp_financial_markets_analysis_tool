"""
Unified Market Scanner Tool for MCP Server
This replaces both comprehensive_market_scanner and enhanced_market_scanner
with a single, well-structured analysis tool.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import warnings
import sys
import os

# Suppress warnings
warnings.filterwarnings('ignore')
os.environ['YFINANCE_SUPPRESS_WARNINGS'] = 'True'

def add_unified_market_scanner_tool(mcp):
    """Add unified market scanner that combines performance analysis with current signals"""
    
    @mcp.tool()
    def market_scanner(
        symbols,
        period: str = "1y",
        output_format: str = "detailed"
    ) -> str:
        """
        market scanner with comprehensive analysis, performance metrics, and structured recommendations.
        
        Features:
        1. Executive Summary with key market insights
        2. Detailed individual stock analysis with all 5 strategies
        3. Performance comparison vs buy-and-hold
        4. Current signal analysis and strength
        5. Structured recommendations with reasoning
        6. Risk assessment and position sizing guidance
        
        Parameters:
        symbols: List of stock ticker symbols (comma-separated string or list)
        period (str): Data period - 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max (default: 1y)
        output_format (str): "detailed", "summary", or "executive" (default: detailed)
        
        Returns:
        str: Market analysis report with structured recommendations
        """
        
        try:
            # Handle input symbols
            if isinstance(symbols, str):
                symbol_list = [s.strip().upper() for s in symbols.replace('"', '').replace("'", "").split(',')]
                symbol_list = [s for s in symbol_list if s and s.replace('.', '').replace('-', '').isalnum()]
            elif isinstance(symbols, list):
                symbol_list = [str(s).strip().upper() for s in symbols if str(s).strip()]
            else:
                return "Error: Symbols must be provided as a list or comma-separated string"

            if not symbol_list:
                return "Error: No valid symbols provided for scanning"

            # Limit for performance
            if len(symbol_list) > 15:
                symbol_list = symbol_list[:15]
                
            analysis_date = datetime.now().strftime("%B %d, %Y")
            
            # Analyze all symbols
            results = []
            failed_symbols = []
            
            print(f"Analyzing {len(symbol_list)} symbols...", file=sys.stderr)
            
            for symbol in symbol_list:
                try:
                    result = analyze_symbol_unified(symbol, period)
                    if result:
                        results.append(result)
                    else:
                        failed_symbols.append(symbol)
                except Exception as e:
                    print(f"Error analyzing {symbol}: {str(e)}", file=sys.stderr)
                    failed_symbols.append(symbol)
            
            if not results:
                return f"Error: No valid analysis results for symbols: {symbol_list}"
            
            # Generate report based on format
            if output_format.lower() == "summary":
                return generate_summary_report(results, failed_symbols, analysis_date, period)
            elif output_format.lower() == "executive":
                return generate_executive_report(results, failed_symbols, analysis_date, period)
            else:
                return generate_detailed_unified_report(results, failed_symbols, analysis_date, period)
                
        except Exception as e:
            print(f"Critical error in unified scanner: {str(e)}", file=sys.stderr)
            return f"Error: Critical failure in unified scanner - {str(e)}"

def analyze_symbol_unified(symbol: str, period: str) -> Optional[Dict]:
    """Unified analysis of a single symbol combining performance and signals"""
    
    try:
        # Download data
        data = yf.download(symbol, period=period, progress=False, multi_level_index=False)
        if data.empty:
            return None
            
        # Basic price metrics
        current_price = float(data['Close'].iloc[-1])
        start_price = float(data['Close'].iloc[0])
        price_change_1d = float((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2] * 100) if len(data) > 1 else 0.0
        buy_hold_return = float((current_price - start_price) / start_price * 100)
        
        result = {
            'symbol': symbol,
            'current_price': current_price,
            'price_change_1d': price_change_1d,
            'buy_hold_return': buy_hold_return,
            'strategies': {},
            'performance_summary': {},
            'current_signals': {},
            'risk_metrics': {},
            'recommendation': {}
        }
        
        # Analyze all 5 strategies with both performance and current signals
        strategy_analyses = {
            'bollinger_zscore': analyze_bollinger_zscore_unified(data, symbol, period),
            'bollinger_fibonacci': analyze_bollinger_fibonacci_unified(data, symbol, period),
            'macd_donchian': analyze_macd_donchian_unified(data, symbol, period),
            'connors_zscore': analyze_connors_zscore_unified(data, symbol, period),
            'dual_ma': analyze_dual_ma_unified(data, symbol, period)
        }
        
        # Process strategy results
        outperforming_strategies = 0
        total_excess_return = 0
        signal_scores = []
        
        for strategy_name, analysis in strategy_analyses.items():
            if analysis and analysis.get('success', False):
                result['strategies'][strategy_name] = analysis
                
                # Performance tracking
                excess_return = analysis.get('excess_return', 0)
                if excess_return > 0:
                    outperforming_strategies += 1
                total_excess_return += excess_return
                
                # Signal tracking
                signal_score = analysis.get('signal_score', 0)
                signal_scores.append(signal_score)
        
        # Calculate unified metrics
        avg_excess_return = total_excess_return / len(strategy_analyses) if strategy_analyses else 0
        avg_signal_score = np.mean(signal_scores) if signal_scores else 0
        success_rate = outperforming_strategies / len(strategy_analyses) if strategy_analyses else 0
        
        # Performance summary
        result['performance_summary'] = {
            'outperforming_strategies': outperforming_strategies,
            'total_strategies': len(strategy_analyses),
            'success_rate': success_rate,
            'avg_excess_return': avg_excess_return,
            'best_strategy': get_best_strategy(strategy_analyses),
            'best_excess_return': max([s.get('excess_return', -999) for s in strategy_analyses.values() if s and s.get('success')] + [-999])
        }
        
        # Current signals summary
        signals = [s.get('current_signal', 'NEUTRAL') for s in strategy_analyses.values() if s and s.get('success')]
        buy_signals = len([s for s in signals if 'BUY' in s])
        sell_signals = len([s for s in signals if 'SELL' in s])
        
        result['current_signals'] = {
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'neutral_signals': len(signals) - buy_signals - sell_signals,
            'signal_consensus': determine_signal_consensus(buy_signals, sell_signals, len(signals)),
            'avg_signal_score': avg_signal_score
        }
        
        # Risk assessment
        result['risk_metrics'] = calculate_risk_metrics(strategy_analyses, data)
        
        # Final recommendation
        result['recommendation'] = generate_unified_recommendation(result)
        
        return result
        
    except Exception as e:
        print(f"Error in unified analysis for {symbol}: {e}", file=sys.stderr)
        return None

def analyze_bollinger_zscore_unified(data: pd.DataFrame, symbol: str, period: str) -> Dict:
    """Unified Bollinger Z-Score analysis with performance and signals"""
    try:
        window = 20
        closes = data["Close"]
        rolling_mean = closes.rolling(window=window).mean()
        rolling_std = closes.rolling(window=window).std()
        z_score = (closes - rolling_mean) / rolling_std
        
        # Performance calculation
        data_copy = data.copy()
        data_copy['position'] = 0
        data_copy.loc[z_score < -2, 'position'] = 1  # Buy oversold
        data_copy.loc[z_score > 2, 'position'] = -1  # Sell overbought
        data_copy['position'] = data_copy['position'].replace(0, np.nan).ffill().fillna(0)
        
        performance = calculate_strategy_performance(data_copy)
        
        # Current signal
        current_zscore = float(z_score.iloc[-1])
        if current_zscore < -2:
            signal = "STRONG_BUY"
            signal_score = 80
        elif current_zscore < -1:
            signal = "BUY"
            signal_score = 40
        elif current_zscore > 2:
            signal = "STRONG_SELL"
            signal_score = -80
        elif current_zscore > 1:
            signal = "SELL"
            signal_score = -40
        else:
            signal = "NEUTRAL"
            signal_score = current_zscore * 20
        
        return {
            'success': True,
            'name': 'Bollinger Z-Score',
            'current_signal': signal,
            'signal_score': signal_score,
            'signal_strength': min(abs(current_zscore) * 30, 100),
            'current_zscore': current_zscore,
            'strategy_return': performance['strategy_return'],
            'excess_return': performance['excess_return'],
            'sharpe_ratio': performance['sharpe_ratio'],
            'win_rate': performance['win_rate'],
            'interpretation': f"Z-Score: {current_zscore:.2f} - {'Oversold' if current_zscore < -1 else 'Overbought' if current_zscore > 1 else 'Normal'}"
        }
    except Exception:
        return {'success': False, 'name': 'Bollinger Z-Score'}

def analyze_bollinger_fibonacci_unified(data: pd.DataFrame, symbol: str, period: str) -> Dict:
    """Unified Bollinger-Fibonacci analysis"""
    try:
        from utils.yahoo_finance_tools import calculate_bollinger_bands
        
        window = 20
        calculate_bollinger_bands(data, symbol, period, window, 2)
        
        # Performance calculation
        data_copy = data.copy()
        if "%B" in data_copy.columns:
            bb_score = (0.5 - data_copy["%B"]) * 100
            data_copy['position'] = 0
            data_copy.loc[bb_score > 25, 'position'] = 1
            data_copy.loc[bb_score < -25, 'position'] = -1
            data_copy['position'] = data_copy['position'].replace(0, np.nan).ffill().fillna(0)
            
            performance = calculate_strategy_performance(data_copy)
            
            current_bb_score = float(bb_score.iloc[-1]) if not bb_score.isna().iloc[-1] else 0
            current_percent_b = float(data_copy["%B"].iloc[-1]) if "%B" in data_copy.columns else 0.5
        else:
            performance = {'strategy_return': 0, 'excess_return': 0, 'sharpe_ratio': 0, 'win_rate': 0}
            current_bb_score = 0
            current_percent_b = 0.5
        
        # Signal determination
        if current_bb_score > 25:
            signal = "BUY"
            signal_score = current_bb_score
        elif current_bb_score < -25:
            signal = "SELL"
            signal_score = current_bb_score
        else:
            signal = "NEUTRAL"
            signal_score = current_bb_score
        
        return {
            'success': True,
            'name': 'Bollinger-Fibonacci',
            'current_signal': signal,
            'signal_score': signal_score,
            'signal_strength': min(abs(current_bb_score) * 2, 100),
            'current_bb_score': current_bb_score,
            'strategy_return': performance['strategy_return'],
            'excess_return': performance['excess_return'],
            'sharpe_ratio': performance['sharpe_ratio'],
            'win_rate': performance['win_rate'],
            'interpretation': f"BB Score: {current_bb_score:.1f}, %B: {current_percent_b:.2f}"
        }
    except Exception:
        return {'success': False, 'name': 'Bollinger-Fibonacci'}

def analyze_macd_donchian_unified(data: pd.DataFrame, symbol: str, period: str) -> Dict:
    """Unified MACD-Donchian analysis"""
    try:
        from utils.yahoo_finance_tools import calculate_macd_score, calculate_donchian_channel_score
        
        macd_score = calculate_macd_score(symbol, period)
        donchian_score = calculate_donchian_channel_score(symbol, period)
        combined_score = (float(macd_score) + float(donchian_score)) / 2
        
        # Performance calculation
        data_copy = data.copy()
        data_copy['position'] = 0
        data_copy.loc[combined_score > 25, 'position'] = 1
        data_copy.loc[combined_score < -25, 'position'] = -1
        data_copy['position'] = data_copy['position'].replace(0, np.nan).ffill().fillna(0)
        
        performance = calculate_strategy_performance(data_copy)
        
        # Signal determination
        if combined_score > 25:
            signal = "BUY"
        elif combined_score < -25:
            signal = "SELL"
        else:
            signal = "NEUTRAL"
        
        return {
            'success': True,
            'name': 'MACD-Donchian',
            'current_signal': signal,
            'signal_score': combined_score,
            'signal_strength': min(abs(combined_score) * 2, 100),
            'macd_score': float(macd_score),
            'donchian_score': float(donchian_score),
            'strategy_return': performance['strategy_return'],
            'excess_return': performance['excess_return'],
            'sharpe_ratio': performance['sharpe_ratio'],
            'win_rate': performance['win_rate'],
            'interpretation': f"MACD: {macd_score:.1f}, Donchian: {donchian_score:.1f}, Combined: {combined_score:.1f}"
        }
    except Exception:
        return {'success': False, 'name': 'MACD-Donchian'}

def analyze_connors_zscore_unified(data: pd.DataFrame, symbol: str, period: str) -> Dict:
    """Unified Connors RSI-Z Score analysis"""
    try:
        from utils.yahoo_finance_tools import calculate_connors_rsi_score, calculate_zscore_indicator
        
        current_crsi, connors_score, _, _, _ = calculate_connors_rsi_score(symbol, period)
        current_zscore, zscore_score, _, _, _ = calculate_zscore_indicator(symbol, period)
        combined_score = (float(connors_score) * 0.7) + (float(zscore_score) * 0.3)
        
        # Performance calculation
        data_copy = data.copy()
        data_copy['position'] = 0
        data_copy.loc[combined_score > 25, 'position'] = 1
        data_copy.loc[combined_score < -25, 'position'] = -1
        data_copy['position'] = data_copy['position'].replace(0, np.nan).ffill().fillna(0)
        
        performance = calculate_strategy_performance(data_copy)
        
        # Signal determination
        if combined_score > 25:
            signal = "BUY"
        elif combined_score < -25:
            signal = "SELL"
        else:
            signal = "NEUTRAL"
        
        return {
            'success': True,
            'name': 'Connors RSI+Z-Score',
            'current_signal': signal,
            'signal_score': combined_score,
            'signal_strength': min(abs(combined_score) * 2, 100),
            'connors_rsi': float(current_crsi),
            'z_score': float(current_zscore),
            'strategy_return': performance['strategy_return'],
            'excess_return': performance['excess_return'],
            'sharpe_ratio': performance['sharpe_ratio'],
            'win_rate': performance['win_rate'],
            'interpretation': f"Connors RSI: {current_crsi:.1f}, Z-Score: {current_zscore:.2f}"
        }
    except Exception:
        return {'success': False, 'name': 'Connors RSI+Z-Score'}

def analyze_dual_ma_unified(data: pd.DataFrame, symbol: str, period: str) -> Dict:
    """Unified Dual Moving Average analysis"""
    try:
        short_period, long_period = 50, 200
        ema_short = data['Close'].ewm(span=short_period).mean()
        ema_long = data['Close'].ewm(span=long_period).mean()
        
        # Performance calculation
        data_copy = data.copy()
        data_copy['position'] = 0
        
        short_above = ema_short > ema_long
        golden_cross = short_above & ~short_above.shift(1).fillna(False)
        death_cross = ~short_above & short_above.shift(1).fillna(True)
        
        data_copy.loc[golden_cross, 'position'] = 1
        data_copy.loc[death_cross, 'position'] = -1
        data_copy['position'] = data_copy['position'].replace(0, np.nan).ffill().fillna(0)
        
        performance = calculate_strategy_performance(data_copy)
        
        # Current metrics
        current_short = float(ema_short.iloc[-1])
        current_long = float(ema_long.iloc[-1])
        ma_separation = (current_short - current_long) / current_long * 100
        
        # Signal determination
        if ma_separation > 2:
            signal = "BUY"
            signal_score = min(ma_separation * 10, 100)
        elif ma_separation < -2:
            signal = "SELL"
            signal_score = max(ma_separation * 10, -100)
        else:
            signal = "NEUTRAL"
            signal_score = ma_separation * 10
        
        return {
            'success': True,
            'name': 'Dual Moving Average',
            'current_signal': signal,
            'signal_score': signal_score,
            'signal_strength': min(abs(ma_separation) * 10, 100),
            'ma_separation': ma_separation,
            'trend': "BULLISH" if current_short > current_long else "BEARISH",
            'strategy_return': performance['strategy_return'],
            'excess_return': performance['excess_return'],
            'sharpe_ratio': performance['sharpe_ratio'],
            'win_rate': performance['win_rate'],
            'interpretation': f"MA Separation: {ma_separation:.2f}%, Trend: {'Bullish' if current_short > current_long else 'Bearish'}"
        }
    except Exception:
        return {'success': False, 'name': 'Dual Moving Average'}

def calculate_strategy_performance(data: pd.DataFrame) -> Dict:
    """Calculate strategy performance metrics"""
    try:
        data_copy = data.copy()
        data_copy['returns'] = data_copy['Close'].pct_change()
        data_copy['strategy_returns'] = data_copy['position'].shift(1) * data_copy['returns']
        
        strategy_return = float((1 + data_copy['strategy_returns']).prod() - 1) * 100
        buy_hold_return = float((data_copy['Close'].iloc[-1] / data_copy['Close'].iloc[0] - 1)) * 100
        excess_return = strategy_return - buy_hold_return
        
        strategy_vol = data_copy['strategy_returns'].std() * np.sqrt(252)
        sharpe_ratio = float((data_copy['strategy_returns'].mean() * 252) / strategy_vol) if strategy_vol > 0 else 0
        
        # Simple win rate calculation
        positive_returns = (data_copy['strategy_returns'] > 0).sum()
        total_periods = len(data_copy['strategy_returns'].dropna())
        win_rate = float(positive_returns / total_periods * 100) if total_periods > 0 else 0
        
        return {
            'strategy_return': strategy_return,
            'buy_hold_return': buy_hold_return,
            'excess_return': excess_return,
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate
        }
    except Exception:
        return {'strategy_return': 0, 'buy_hold_return': 0, 'excess_return': 0, 'sharpe_ratio': 0, 'win_rate': 0}

def get_best_strategy(strategy_analyses: Dict) -> str:
    """Get the best performing strategy"""
    best_strategy = ""
    best_excess = -999
    
    for name, analysis in strategy_analyses.items():
        if analysis and analysis.get('success') and analysis.get('excess_return', -999) > best_excess:
            best_excess = analysis['excess_return']
            best_strategy = analysis['name']
    
    return best_strategy

def determine_signal_consensus(buy_signals: int, sell_signals: int, total_signals: int) -> str:
    """Determine overall signal consensus"""
    if total_signals == 0:
        return "NO_SIGNALS"
    
    buy_pct = buy_signals / total_signals
    sell_pct = sell_signals / total_signals
    
    if buy_pct >= 0.6:
        return "BULLISH_CONSENSUS"
    elif sell_pct >= 0.6:
        return "BEARISH_CONSENSUS"
    elif buy_pct > sell_pct:
        return "MILD_BULLISH"
    elif sell_pct > buy_pct:
        return "MILD_BEARISH"
    else:
        return "MIXED_SIGNALS"

def calculate_risk_metrics(strategy_analyses: Dict, data: pd.DataFrame) -> Dict:
    """Calculate unified risk metrics"""
    try:
        # Volatility
        returns = data['Close'].pct_change()
        volatility = float(returns.std() * np.sqrt(252) * 100)
        
        # Average strategy volatility
        strategy_vols = [s.get('sharpe_ratio', 0) for s in strategy_analyses.values() if s and s.get('success')]
        avg_strategy_performance = np.mean(strategy_vols) if strategy_vols else 0
        
        # Risk level
        if volatility > 40:
            risk_level = "HIGH"
        elif volatility > 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            'volatility': volatility,
            'risk_level': risk_level,
            'avg_strategy_performance': avg_strategy_performance
        }
    except Exception:
        return {'volatility': 20, 'risk_level': 'MEDIUM', 'avg_strategy_performance': 0}

def generate_unified_recommendation(result: Dict) -> Dict:
    """Generate unified recommendation based on all analysis"""
    
    performance = result['performance_summary']
    signals = result['current_signals']
    risk = result['risk_metrics']
    
    # Recommendation logic
    success_rate = performance['success_rate']
    avg_excess = performance['avg_excess_return']
    signal_consensus = signals['signal_consensus']
    
    if success_rate >= 0.6 and avg_excess > 10:
        action = "STRONG_BUY"
        confidence = "HIGH"
    elif success_rate >= 0.4 and avg_excess > 5:
        action = "BUY"
        confidence = "MEDIUM"
    elif success_rate < 0.3 or avg_excess < -10:
        action = "AVOID"
        confidence = "HIGH"
    elif "BEARISH" in signal_consensus:
        action = "SELL"
        confidence = "MEDIUM"
    else:
        action = "HOLD"
        confidence = "LOW"
    
    # Position sizing
    if risk['risk_level'] == "HIGH":
        position_size = "SMALL (1-2%)"
    elif risk['risk_level'] == "MEDIUM":
        position_size = "MEDIUM (3-5%)"
    else:
        position_size = "NORMAL (5-8%)"
    
    # Reasoning
    reasoning_parts = []
    
    if performance['outperforming_strategies'] > 0:
        reasoning_parts.append(f"{performance['outperforming_strategies']}/{performance['total_strategies']} strategies outperform buy-hold")
    
    if avg_excess != 0:
        reasoning_parts.append(f"Average excess return: {avg_excess:+.1f}%")
    
    if signal_consensus != "MIXED_SIGNALS":
        reasoning_parts.append(f"Signal consensus: {signal_consensus.replace('_', ' ').lower()}")
    
    reasoning_parts.append(f"Risk level: {risk['risk_level'].lower()}")
    
    reasoning = ". ".join(reasoning_parts) + "."
    
    return {
        'action': action,
        'confidence': confidence,
        'position_size': position_size,
        'reasoning': reasoning,
        'best_strategy': performance['best_strategy']
    }

def generate_detailed_unified_report(results: List[Dict], failed_symbols: List[str], analysis_date: str, period: str) -> str:
    """Generate detailed unified report with proper structure"""
    
    # Sort by recommendation strength and performance
    results.sort(key=lambda x: (
        x['recommendation']['action'] in ['STRONG_BUY', 'BUY'],
        x['performance_summary']['avg_excess_return']
    ), reverse=True)
    
    # Market overview metrics
    total_stocks = len(results)
    strong_buys = len([r for r in results if r['recommendation']['action'] == 'STRONG_BUY'])
    buys = len([r for r in results if r['recommendation']['action'] == 'BUY'])
    sells = len([r for r in results if r['recommendation']['action'] == 'SELL'])
    avoids = len([r for r in results if r['recommendation']['action'] == 'AVOID'])
    
    avg_buy_hold = np.mean([r['buy_hold_return'] for r in results])
    avg_excess = np.mean([r['performance_summary']['avg_excess_return'] for r in results])
    
    report = f"""# Unified Market Analysis Report
**Analysis Date:** {analysis_date}  
**Period:** {period} | **Stocks Analyzed:** {total_stocks} | **Failed:** {len(failed_symbols)}

---

## 📊 Executive Summary

### Market Performance Overview
- **Average Buy & Hold Return:** {avg_buy_hold:+.1f}%
- **Average Strategy Excess Return:** {avg_excess:+.1f}%
- **Technical Analysis Success Rate:** {len([r for r in results if r['performance_summary']['avg_excess_return'] > 0]) / total_stocks * 100:.1f}%

### Recommendation Distribution
- **🟢 Strong Buy:** {strong_buys} stocks ({strong_buys/total_stocks*100:.1f}%)
- **🔵 Buy:** {buys} stocks ({buys/total_stocks*100:.1f}%)
- **⚪ Hold:** {total_stocks - strong_buys - buys - sells - avoids} stocks
- **🔴 Sell:** {sells} stocks ({sells/total_stocks*100:.1f}%)
- **❌ Avoid:** {avoids} stocks ({avoids/total_stocks*100:.1f}%)

### Key Market Insights
{'🟢 **Bullish Environment:** Multiple stocks showing strong technical outperformance' if strong_buys + buys > total_stocks * 0.5 else '🔴 **Bearish Environment:** Limited technical opportunities, defensive positioning recommended' if avoids + sells > total_stocks * 0.4 else '⚪ **Mixed Environment:** Selective opportunities require careful analysis'}

---

## 🎯 Top Investment Opportunities

| Rank | Symbol | Price | 1D % | Action | Best Strategy | Excess Return | Risk Level |
|------|--------|-------|------|--------|---------------|---------------|------------|
"""
    
    # Top 10 opportunities
    for i, result in enumerate(results[:10], 1):
        price_emoji = "🟢" if result['price_change_1d'] > 0 else "🔴" if result['price_change_1d'] < 0 else "⚪"
        action_emoji = {"STRONG_BUY": "🟢", "BUY": "🔵", "HOLD": "⚪", "SELL": "🔴", "AVOID": "❌"}.get(result['recommendation']['action'], "⚪")
        
        report += f"| {i} | {result['symbol']} | USD {result['current_price']:.2f} | {price_emoji} {result['price_change_1d']:+.1f}% | {action_emoji} {result['recommendation']['action']} | {result['performance_summary']['best_strategy']} | {result['performance_summary']['best_excess_return']:+.1f}% | {result['risk_metrics']['risk_level']} |\n"
    
    report += "\n---\n\n## 📈 Detailed Individual Analysis\n\n"
    
    # Detailed analysis for top picks
    for result in results[:5]:  # Top 5 detailed analysis
        report += generate_individual_stock_report(result)
    
    # Strategy effectiveness summary
    report += generate_strategy_effectiveness_summary(results)
    
    # Final recommendations
    report += generate_final_recommendations(results, period)
    
    if failed_symbols:
        report += f"\n**⚠️ Analysis Failures:** {', '.join(failed_symbols)}\n"
    
    report += "\n---\n*This analysis combines technical indicators with performance backtesting. Past performance does not guarantee future results. Always conduct your own research and consider your risk tolerance.*"
    
    return report

def generate_individual_stock_report(result: Dict) -> str:
    """Generate detailed individual stock analysis"""
    
    stock = result['symbol']
    rec = result['recommendation']
    perf = result['performance_summary']
    signals = result['current_signals']
    
    report = f"""
### {stock} - USD {result['current_price']:.2f} ({result['price_change_1d']:+.1f}%)

**🎯 Recommendation:** {rec['action']} | **📊 Confidence:** {rec['confidence']} | **💰 Position Size:** {rec['position_size']}

**📈 Performance Summary:**
- Buy & Hold Return: {result['buy_hold_return']:+.1f}%
- Best Strategy: {perf['best_strategy']} ({perf['best_excess_return']:+.1f}% excess)
- Success Rate: {perf['outperforming_strategies']}/{perf['total_strategies']} strategies outperform
- Risk Level: {result['risk_metrics']['risk_level']}

**🔍 Current Signals:**
- Signal Consensus: {signals['signal_consensus'].replace('_', ' ')}
- Buy Signals: {signals['buy_signals']}/5 | Sell Signals: {signals['sell_signals']}/5

**💡 Analysis Reasoning:** {rec['reasoning']}

**📊 Strategy Breakdown:**

| Strategy | Signal | Score | Excess Return | Win Rate | Interpretation |
|----------|--------|-------|---------------|----------|----------------|
"""
    
    for strategy_name, strategy_data in result['strategies'].items():
        if strategy_data.get('success'):
            report += f"| {strategy_data['name']} | {strategy_data['current_signal']} | {strategy_data['signal_score']:+.1f} | {strategy_data['excess_return']:+.1f}% | {strategy_data['win_rate']:.0f}% | {strategy_data['interpretation']} |\n"
    
    report += "\n"
    return report

def generate_strategy_effectiveness_summary(results: List[Dict]) -> str:
    """Generate strategy effectiveness summary"""
    
    strategy_names = ['bollinger_zscore', 'bollinger_fibonacci', 'macd_donchian', 'connors_zscore', 'dual_ma']
    
    report = "## 🔬 Strategy Effectiveness Analysis\n\n"
    report += "| Strategy | Success Rate | Avg Excess Return | Best For | Reliability |\n"
    report += "|----------|--------------|-------------------|----------|--------------|\n"
    
    for strategy_key in strategy_names:
        strategy_results = []
        outperformers = 0
        
        for result in results:
            if strategy_key in result['strategies'] and result['strategies'][strategy_key].get('success'):
                strategy_data = result['strategies'][strategy_key]
                strategy_results.append(strategy_data)
                if strategy_data.get('excess_return', 0) > 0:
                    outperformers += 1
        
        if strategy_results:
            success_rate = outperformers / len(strategy_results)
            avg_excess = np.mean([s['excess_return'] for s in strategy_results])
            avg_win_rate = np.mean([s['win_rate'] for s in strategy_results])
            strategy_name = strategy_results[0]['name']
            
            # Determine what strategy is best for
            best_for = {
                'bollinger_zscore': 'Mean Reversion',
                'bollinger_fibonacci': 'Support/Resistance',
                'macd_donchian': 'Trend Momentum',
                'connors_zscore': 'Short-term Timing',
                'dual_ma': 'Trend Following'
            }.get(strategy_key, 'General')
            
            reliability = "High" if avg_win_rate > 60 else "Medium" if avg_win_rate > 50 else "Low"
            
            report += f"| {strategy_name} | {success_rate:.1%} | {avg_excess:+.1f}% | {best_for} | {reliability} |\n"
    
    return report + "\n"

def generate_final_recommendations(results: List[Dict], period: str) -> str:
    """Generate final recommendations and market outlook"""
    
    strong_buys = [r for r in results if r['recommendation']['action'] == 'STRONG_BUY']
    buys = [r for r in results if r['recommendation']['action'] == 'BUY']
    avoids = [r for r in results if r['recommendation']['action'] == 'AVOID']
    
    avg_excess = np.mean([r['performance_summary']['avg_excess_return'] for r in results])
    
    report = "## 🎯 Final Investment Strategy\n\n"
    
    if len(strong_buys) > 0:
        report += f"### 🟢 Priority Investments ({len(strong_buys)} stocks)\n"
        for stock in strong_buys[:3]:
            report += f"- **{stock['symbol']}**: {stock['recommendation']['reasoning']}\n"
        report += "\n"
    
    if len(buys) > 0:
        report += f"### 🔵 Secondary Opportunities ({len(buys)} stocks)\n"
        for stock in buys[:3]:
            report += f"- **{stock['symbol']}**: {stock['recommendation']['reasoning']}\n"
        report += "\n"
    
    if len(avoids) > 0:
        report += f"### ❌ Stocks to Avoid ({len(avoids)} stocks)\n"
        avoid_list = [stock['symbol'] for stock in avoids[:5]]
        report += f"- Avoid: {', '.join(avoid_list)} - Poor technical performance across strategies\n\n"
    
    # Market outlook
    if avg_excess > 5:
        outlook = "**🟢 BULLISH MARKET OUTLOOK**"
        strategy = "Focus on technical analysis signals, increase position sizes on strong buy signals"
    elif avg_excess < -5:
        outlook = "**🔴 BEARISH MARKET OUTLOOK**"
        strategy = "Defensive positioning, prefer buy-and-hold over technical strategies"
    else:
        outlook = "**⚪ NEUTRAL MARKET OUTLOOK**"
        strategy = "Selective approach, focus only on highest-confidence opportunities"
    
    report += f"### 📈 Market Outlook for {period} Period\n\n"
    report += f"{outlook}\n\n"
    report += f"**Recommended Strategy:** {strategy}\n\n"
    
    # Risk management
    report += "### ⚠️ Risk Management Guidelines\n\n"
    report += "- **Position Sizing:** Follow recommended position sizes based on risk levels\n"
    report += "- **Diversification:** Don't concentrate more than 25% in any single strategy\n"
    report += "- **Stop Losses:** Use 7-10% stop losses below technical support levels\n"
    report += "- **Profit Taking:** Consider taking partial profits at 15-20% gains\n\n"
    
    return report

def generate_summary_report(results: List[Dict], failed_symbols: List[str], analysis_date: str, period: str) -> str:
    """Generate summary report"""
    
    results.sort(key=lambda x: x['performance_summary']['avg_excess_return'], reverse=True)
    
    total_stocks = len(results)
    avg_excess = np.mean([r['performance_summary']['avg_excess_return'] for r in results])
    
    summary = f"""UNIFIED MARKET SCANNER SUMMARY - {analysis_date}
{'='*60}

PERIOD: {period} | ANALYZED: {total_stocks} | FAILED: {len(failed_symbols)}
AVERAGE EXCESS RETURN: {avg_excess:+.1f}%

TOP 10 OPPORTUNITIES:
"""
    
    for i, result in enumerate(results[:10], 1):
        summary += f"{i:2d}. {result['symbol']:6s} | USD {result['current_price']:7.2f} | {result['recommendation']['action']:12s} | Best: {result['performance_summary']['best_strategy'][:15]:15s} | {result['performance_summary']['best_excess_return']:+5.1f}%\n"
    
    return summary

def generate_executive_report(results: List[Dict], failed_symbols: List[str], analysis_date: str, period: str) -> str:
    """Generate executive summary report"""
    
    total_stocks = len(results)
    strong_buys = len([r for r in results if r['recommendation']['action'] == 'STRONG_BUY'])
    avg_excess = np.mean([r['performance_summary']['avg_excess_return'] for r in results])
    
    # Get top 3 opportunities
    top_3 = sorted(results, key=lambda x: x['performance_summary']['avg_excess_return'], reverse=True)[:3]
    
    report = f"""EXECUTIVE MARKET SUMMARY - {analysis_date}
{'='*50}

KEY METRICS:
• Market Period: {period}
• Stocks Analyzed: {total_stocks}
• Strong Buy Opportunities: {strong_buys}
• Average Strategy Excess Return: {avg_excess:+.1f}%

TOP 3 OPPORTUNITIES:
"""
    
    for i, stock in enumerate(top_3, 1):
        report += f"{i}. {stock['symbol']} - {stock['recommendation']['action']} ({stock['performance_summary']['best_excess_return']:+.1f}% excess)\n"
    
    market_sentiment = "BULLISH" if avg_excess > 2 else "BEARISH" if avg_excess < -2 else "NEUTRAL"
    report += f"\nMARKET SENTIMENT: {market_sentiment}"
    report += f"\nRECOMMENDATION: {'ACTIVE TECHNICAL TRADING' if market_sentiment == 'BULLISH' else 'DEFENSIVE POSITIONING' if market_sentiment == 'BEARISH' else 'SELECTIVE OPPORTUNITIES'}"
    
    return report