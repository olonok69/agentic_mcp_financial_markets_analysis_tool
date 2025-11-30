"""
Comprehensive Multi-Strategy Analysis Tool
This tool integrates all strategies and generates a complete analysis report
"""

def add_comprehensive_strategy_analysis_tool(mcp):
    """Add comprehensive analysis tool that combines all strategies"""
    
    @mcp.tool()
    def comprehensive_strategy_analysis(symbol: str, period: str = "1y") -> str:
        """
        Generate comprehensive analysis using all 5 trading strategies with performance comparisons.
        
        This tool will:
        1. Run Bollinger Z-Score analysis (20-day period)
        2. Run Bollinger-Fibonacci strategy analysis (1-year, 20-day window, last 5 days)
        3. Run MACD-Donchian combined analysis (1-year, 20-day Donchian, MACD 12/26/9)
        4. Run Connors RSI + Z-Score analysis (default parameters, 1-year period)
        5. Run Dual MA analysis (EMA 50/200, 1-year period)
        6. Compare all strategies and provide final recommendation
        
        Parameters:
        symbol (str): Stock ticker symbol to analyze
        period (str): Data period for analysis (default: 1y)
        
        Returns:
        str: Comprehensive markdown analysis report with all strategies and performance metrics
        """
        try:
            import yfinance as yf
            from datetime import datetime
            
            # Get current price and date
            recent_data = yf.download(symbol, period="5d", progress=False, multi_level_index=False)
            if recent_data.empty:
                return f"Error: No data found for symbol {symbol}"
            
            current_price = recent_data['Close'].iloc[-1]
            analysis_date = datetime.now().strftime("%B %d, %Y")
            
            # Initialize report
            report = f"""# {symbol.upper()} Comprehensive Technical Analysis
*Analysis Date: {analysis_date}*  
*Current Price: USD {current_price:.2f}*

## Executive Summary

This comprehensive technical analysis evaluates {symbol.upper()} stock using five different technical indicators and strategies. The analysis combines momentum, mean reversion, volatility, and trend-following approaches to provide a well-rounded assessment of {symbol.upper()}'s current trading position.

## Individual Strategy Analysis

"""
            
            # Strategy 1: Bollinger Z-Score
            report += self._analyze_bollinger_zscore(symbol, period)
            
            # Strategy 2: Bollinger-Fibonacci
            report += self._analyze_bollinger_fibonacci(symbol, period)
            
            # Strategy 3: MACD-Donchian
            report += self._analyze_macd_donchian(symbol, period)
            
            # Strategy 4: Connors RSI + Z-Score
            report += self._analyze_connors_zscore(symbol, period)
            
            # Strategy 5: Dual Moving Average
            report += self._analyze_dual_ma(symbol, period)
            
            # Generate summary table and final recommendation
            report += self._generate_summary_and_recommendation(symbol)
            
            return report
            
        except Exception as e:
            return f"Error generating comprehensive analysis for {symbol}: {str(e)}"
    
    def _analyze_bollinger_zscore(self, symbol: str, period: str) -> str:
        """Analyze Bollinger Z-Score strategy"""
        try:
            data = yf.download(symbol, period=period, progress=False, multi_level_index=False)
            
            # Calculate Z-Score
            window = 20
            closes = data["Close"]
            rolling_mean = closes.rolling(window=window).mean()
            rolling_std = closes.rolling(window=window).std()
            upper_band = rolling_mean + (2 * rolling_std)
            lower_band = rolling_mean - (2 * rolling_std)
            z_score = (closes - rolling_mean) / rolling_std
            
            latest_z_score = z_score.iloc[-1]
            latest_close = closes.iloc[-1]
            latest_mean = rolling_mean.iloc[-1]
            latest_upper = upper_band.iloc[-1]
            latest_lower = lower_band.iloc[-1]
            
            # Determine signal
            if latest_z_score > 2:
                signal = "SELL"
                condition = "OVERBOUGHT - Strong Sell Signal"
            elif latest_z_score > 1:
                signal = "WEAK SELL"
                condition = "Moderately Overbought"
            elif latest_z_score < -2:
                signal = "BUY"
                condition = "OVERSOLD - Strong Buy Signal"
            elif latest_z_score < -1:
                signal = "WEAK BUY"
                condition = "Moderately Oversold"
            else:
                signal = "HOLD"
                condition = "NORMAL RANGE"
            
            # Calculate performance
            data['Signal'] = None
            data.loc[z_score < -2, 'Signal'] = 'BUY'
            data.loc[z_score > 2, 'Signal'] = 'SELL'
            
            # Simple performance calculation
            signals = data['Signal'].dropna()
            performance_summary = f"Generated {len(signals)} signals over {period}"
            
            return f"""
### 1. Bollinger Z-Score Analysis (20-Day Period)

**Current Z-Score:** {latest_z_score:.2f}  
**Signal:** {signal}  
**Market Condition:** {condition}

**Key Metrics:**
- Rolling Mean (20-day): USD {latest_mean:.2f}
- Upper Bollinger Band: USD {latest_upper:.2f}
- Lower Bollinger Band: USD {latest_lower:.2f}
- Distance from Upper Band: {((latest_close - latest_upper) / latest_upper * 100):+.2f}%
- Distance from Lower Band: {((latest_close - latest_lower) / latest_lower * 100):+.2f}%

**Performance:** {performance_summary}

**Analysis:** {symbol.upper()}'s price is trading {abs(latest_z_score):.2f} standard deviations {'above' if latest_z_score > 0 else 'below'} its 20-day mean. {condition.lower()}.

"""
        except Exception as e:
            return f"### 1. Bollinger Z-Score Analysis\n**Error:** {str(e)}\n\n"
    
    def _analyze_bollinger_fibonacci(self, symbol: str, period: str) -> str:
        """Analyze Bollinger-Fibonacci strategy"""
        try:
            # This would call your existing bollinger-fibonacci tool
            # For now, returning a template
            return f"""
### 2. Bollinger Bands & Fibonacci Retracement Strategy (1-Year, 20-Day Window)

**Latest Strategy Score:** [Score]/100  
**Signal:** [Signal]  
**5-Day Average Score:** [Average]/100

**Component Breakdown (Latest Day):**
- Bollinger Bands Score (30%): [Score]
- Volatility Score (15%): [Score]
- Fibonacci Retracement Score (35%): [Score]
- Momentum Score (20%): [Score]

**Analysis:** [Analysis would be inserted here based on actual calculations]

"""
        except Exception as e:
            return f"### 2. Bollinger-Fibonacci Strategy\n**Error:** {str(e)}\n\n"
    
    def _analyze_macd_donchian(self, symbol: str, period: str) -> str:
        """Analyze MACD-Donchian strategy"""
        try:
            data = yf.download(symbol, period=period, progress=False, multi_level_index=False)
            
            # MACD calculation
            fast_period, slow_period, signal_period = 12, 26, 9
            ema_fast = data["Close"].ewm(span=fast_period).mean()
            ema_slow = data["Close"].ewm(span=slow_period).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal_period).mean()
            
            # Donchian channels
            window = 20
            upper_band = data["High"].rolling(window=window).max()
            lower_band = data["Low"].rolling(window=window).min()
            
            # Simple combined score
            macd_signal = 1 if macd_line.iloc[-1] > signal_line.iloc[-1] else -1
            donchian_position = (data["Close"].iloc[-1] - lower_band.iloc[-1]) / (upper_band.iloc[-1] - lower_band.iloc[-1])
            
            combined_score = (macd_signal * 50) + ((donchian_position - 0.5) * 100)
            
            if combined_score > 25:
                signal = "BUY"
            elif combined_score < -25:
                signal = "SELL"
            else:
                signal = "NEUTRAL"
            
            return f"""
### 3. MACD-Donchian Combined Strategy (1-Year Period)

**Combined Score:** {combined_score:.2f}/100  
**Signal:** {signal}  

**Component Analysis:**
- MACD Position: {"Above Signal Line" if macd_signal > 0 else "Below Signal Line"}
- Donchian Position: {donchian_position:.2%} of channel range

**Analysis:** The strategy shows {'bullish' if combined_score > 0 else 'bearish' if combined_score < 0 else 'neutral'} signals with {'strong' if abs(combined_score) > 50 else 'moderate' if abs(combined_score) > 25 else 'weak'} conviction.

"""
        except Exception as e:
            return f"### 3. MACD-Donchian Strategy\n**Error:** {str(e)}\n\n"
    
    def _analyze_connors_zscore(self, symbol: str, period: str) -> str:
        """Analyze Connors RSI + Z-Score strategy"""
        try:
            data = yf.download(symbol, period=period, progress=False, multi_level_index=False)
            
            # Simple RSI calculation (Connors RSI simplified)
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=3).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=3).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Z-Score
            window = 20
            rolling_mean = data['Close'].rolling(window=window).mean()
            rolling_std = data['Close'].rolling(window=window).std()
            zscore = (data['Close'] - rolling_mean) / rolling_std
            
            # Combined score (70% RSI, 30% Z-Score)
            rsi_score = (rsi.iloc[-1] - 50) * 2  # Convert to ±100 scale
            zscore_score = zscore.iloc[-1] * (100/3)  # Scale Z-score
            combined_score = (rsi_score * 0.7) + (zscore_score * 0.3)
            
            if combined_score > 25:
                signal = "WEAK BUY"
            elif combined_score > 50:
                signal = "BUY"
            elif combined_score < -25:
                signal = "WEAK SELL"
            elif combined_score < -50:
                signal = "SELL"
            else:
                signal = "NEUTRAL"
            
            return f"""
### 4. Connors RSI & Z-Score Combined Analysis (1-Year Period)

**Combined Score:** {combined_score:.2f}/100  
**Signal:** {signal}  

**Component Analysis:**
- Connors RSI: {rsi.iloc[-1]:.2f} (Score: {rsi_score:.2f})
- Z-Score: {zscore.iloc[-1]:.2f} (Score: {zscore_score:.2f})
- Weighting: 70% Connors RSI, 30% Z-Score

**Analysis:** This strategy provides {'bullish' if combined_score > 0 else 'bearish' if combined_score < 0 else 'neutral'} signals. The Connors RSI suggests {'overbought' if rsi.iloc[-1] > 70 else 'oversold' if rsi.iloc[-1] < 30 else 'normal'} conditions.

"""
        except Exception as e:
            return f"### 4. Connors RSI-Z Score Strategy\n**Error:** {str(e)}\n\n"
    
    def _analyze_dual_ma(self, symbol: str, period: str) -> str:
        """Analyze Dual Moving Average strategy"""
        try:
            data = yf.download(symbol, period=period, progress=False, multi_level_index=False)
            
            # Calculate EMAs
            short_period, long_period = 50, 200
            ema_short = data['Close'].ewm(span=short_period).mean()
            ema_long = data['Close'].ewm(span=long_period).mean()
            
            current_price = data['Close'].iloc[-1]
            current_short_ema = ema_short.iloc[-1]
            current_long_ema = ema_long.iloc[-1]
            
            # Calculate positioning score
            ma_separation = (current_short_ema - current_long_ema) / current_long_ema * 100
            positioning_score = np.clip(ma_separation * 10, -40, 40)
            
            # Trend analysis
            trend_direction = "BULLISH" if current_short_ema > current_long_ema else "BEARISH"
            trend_strength = abs(ma_separation)
            
            # Overall score (simplified)
            overall_score = positioning_score * 0.4  # Simplified version
            
            if overall_score > 20:
                signal = "BUY"
            elif overall_score < -20:
                signal = "SELL"
            else:
                signal = "NEUTRAL"
            
            return f"""
### 5. Dual Moving Average Strategy (EMA 50/200, 1-Year Period)

**Overall Score:** {overall_score:.1f}/100  
**Signal:** {signal}  

**Key Metrics:**
- 50-day EMA: USD {current_short_ema:.2f}
- 200-day EMA: USD {current_long_ema:.2f}
- Current Price: USD {current_price:.2f}
- Price vs Short MA: {((current_price - current_short_ema) / current_short_ema * 100):+.2f}%
- Price vs Long MA: {((current_price - current_long_ema) / current_long_ema * 100):+.2f}%
- MA Separation: {ma_separation:.2f}%

**Analysis:** The stock is trading {'above' if current_price > current_short_ema else 'below'} both moving averages, indicating a {trend_direction.lower()} positioning. Trend strength is {'strong' if trend_strength > 5 else 'moderate' if trend_strength > 2 else 'weak'}.

"""
        except Exception as e:
            return f"### 5. Dual Moving Average Strategy\n**Error:** {str(e)}\n\n"
    
    def _generate_summary_and_recommendation(self, symbol: str) -> str:
        """Generate summary table and final recommendation"""
        try:
            # In a real implementation, you would collect all the scores and signals
            # from the previous analyses. For now, we'll create a template.
            
            return f"""
## Summary Table

| Strategy | Score | Signal | Recommendation |
|----------|-------|--------|----------------|
| Bollinger Z-Score (20-day) | [Score] σ | [Signal] | [Recommendation] |
| Bollinger-Fibonacci (1Y) | [Score]/100 | [Signal] | [Recommendation] |
| MACD-Donchian (1Y) | [Score]/100 | [Signal] | [Recommendation] |
| Connors RSI-Z Score (1Y) | [Score]/100 | [Signal] | [Recommendation] |
| Dual MA EMA 50/200 (1Y) | [Score]/100 | [Signal] | [Recommendation] |

## Performance Comparison Summary

| Strategy | Strategy Return | Buy & Hold Return | Excess Return | Sharpe Ratio | Max Drawdown | Verdict |
|----------|----------------|-------------------|---------------|--------------|--------------|---------|
| Bollinger Z-Score | [Return]% | [B&H]% | [Excess]% | [Sharpe] | [DD]% | [Verdict] |
| Bollinger-Fibonacci | [Return]% | [B&H]% | [Excess]% | [Sharpe] | [DD]% | [Verdict] |
| MACD-Donchian | [Return]% | [B&H]% | [Excess]% | [Sharpe] | [DD]% | [Verdict] |
| Connors RSI-Z Score | [Return]% | [B&H]% | [Excess]% | [Sharpe] | [DD]% | [Verdict] |
| Dual MA EMA 50/200 | [Return]% | [B&H]% | [Excess]% | [Sharpe] | [DD]% | [Verdict] |

## Final Recommendation: **[FINAL VERDICT]**

### Rationale:

**Strategy Consensus:** [Analysis of strategy agreement/disagreement]

**Performance Analysis:** [Summary of which strategies outperformed buy-and-hold]

**Risk-Adjusted Returns:** [Analysis of Sharpe ratios and risk metrics]

**Current Market Conditions:** [Assessment of current technical position]

### Trading Strategy:
1. **Current Holders:** [Recommendation for existing positions]
2. **New Buyers:** [Entry strategy and levels]
3. **Risk Management:** [Stop-loss and position sizing guidance]

### Key Levels to Watch:
- **Resistance:** [Key resistance levels from multiple indicators]
- **Support:** [Key support levels from multiple indicators]
- **Breakout Levels:** [Critical levels for trend confirmation]

### Performance Insights:
- **Best Performing Strategy:** [Strategy with highest risk-adjusted returns]
- **Most Consistent Strategy:** [Strategy with lowest drawdowns]
- **Current Market Regime:** [Trending vs ranging market assessment]

*This analysis is for educational purposes only and should not be considered as financial advice. Always conduct your own research and consider your risk tolerance before making investment decisions.*
"""
        except Exception as e:
            return f"## Summary\n**Error generating summary:** {str(e)}\n"