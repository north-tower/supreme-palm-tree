import pandas as pd
import numpy as np
import math
from Analysis import HistorySummary

class SignalGenerator:
    def __init__(self):
        self.timeframe_mapping = {
            1: "15s",
            3: "30s", 
            5: "1m",
            15: "5m"
        }
    
    def get_timeframe_for_expiration(self, minutes: int):
        """Choose the most appropriate timeframe based on expiration time"""
        return self.timeframe_mapping.get(minutes, "1m")  # default fallback
    
    async def fetch_candles(self, asset, timeframe="1m", limit=200, fetch_function=None):
        """Fetch historical candle data with proper timeframe"""
        try:
            # Convert timeframe to period (minutes)
            timeframe_to_period = {
                "15s": 1,   # 15 seconds = 1 minute period
                "30s": 1,   # 30 seconds = 1 minute period  
                "1m": 1,    # 1 minute = 1 minute period
                "5m": 5,    # 5 minutes = 5 minute period
            }
            period = timeframe_to_period.get(timeframe, 1)
            
            # Use the provided fetch function or fallback
            if fetch_function:
                results, data = await fetch_function(asset, period, "cZoCQNWriz")
            else:
                # Fallback: import here to avoid circular imports
                from demo_test import fetch_summary
                results, data = await fetch_summary(asset, period, "cZoCQNWriz")
            
            if not data or len(data) < 10:
                print(f"[WARNING] Insufficient data for {asset} with timeframe {timeframe}")
                return None
                
            return data
            
        except Exception as e:
            print(f"[ERROR] Failed to fetch candles for {asset}: {e}")
            return None
    
    def detect_market_structure(self, history_df):
        """Detect if market structure is bullish, bearish, or neutral"""
        try:
            if history_df is None or len(history_df) < 20:
                return "neutral"
            
            # Calculate recent trend using EMA
            ema_short = history_df["Value"].ewm(span=10).mean()
            ema_long = history_df["Value"].ewm(span=20).mean()
            
            current_price = history_df["Value"].iloc[-1]
            ema_short_current = ema_short.iloc[-1]
            ema_long_current = ema_long.iloc[-1]
            
            # Determine structure based on price vs EMAs
            if current_price > ema_short_current > ema_long_current:
                return "bullish"
            elif current_price < ema_short_current < ema_long_current:
                return "bearish"
            else:
                return "neutral"
                
        except Exception as e:
            print(f"[ERROR] Error detecting market structure: {e}")
            return "neutral"
    
    def detect_candlestick_pattern(self, last_candle, prev_candle):
        """Detect common candlestick patterns"""
        try:
            if not last_candle or not prev_candle:
                return "none"
            
            # Extract OHLC values (assuming Value column represents Close)
            current_close = last_candle.get("Value", 0)
            current_open = prev_candle.get("Value", 0)  # Approximate open as previous close
            prev_close = prev_candle.get("Value", 0)
            prev_open = current_open  # Approximate previous open
            
            # Calculate body and shadow sizes
            current_body = abs(current_close - current_open)
            prev_body = abs(prev_close - prev_open)
            
            # Detect patterns
            if current_close > current_open:  # Bullish candle
                if prev_close < prev_open:  # Previous was bearish
                    if current_close > prev_open and current_open < prev_close:
                        return "bullish_engulfing"
                    elif current_body > prev_body * 1.5:
                        return "bullish_engulfing"
                        
            elif current_close < current_open:  # Bearish candle
                if prev_close > prev_open:  # Previous was bullish
                    if current_close < prev_open and current_open > prev_close:
                        return "bearish_engulfing"
                    elif current_body > prev_body * 1.5:
                        return "bearish_engulfing"
            
            # Detect pin bars (hammer/shooting star)
            if current_body < (current_close + current_open) * 0.1:  # Small body
                return "pin_bar"
                
            return "none"
            
        except Exception as e:
            print(f"[ERROR] Error detecting candlestick pattern: {e}")
            return "none"
    
    def is_support_zone(self, current_price, support_levels, tolerance=0.002):
        """Check if current price is near support levels"""
        if not support_levels:
            return False
        return any(abs(current_price - level) / level <= tolerance for level in support_levels)
    
    def is_resistance_zone(self, current_price, resistance_levels, tolerance=0.002):
        """Check if current price is near resistance levels"""
        if not resistance_levels:
            return False
        return any(abs(current_price - level) / level <= tolerance for level in resistance_levels)
    
    def format_signal(self, signal_type, asset, price, zone_price, expiration_min):
        """Format signal output in clean, Telegram-friendly format"""
        try:
            signal_emoji = {
                "BUY": "🟩",
                "SELL": "🟥", 
                "HOLD": "⬜"
            }.get(signal_type, "❔")
            
            # Determine zone label based on signal type
            if signal_type == "BUY":
                zone_label = "Support Zone"
            elif signal_type == "SELL":
                zone_label = "Resistance Zone"
            else:  # HOLD
                zone_label = "Nearest Level"
            
            # Handle None or NaN zone_price
            if zone_price is None or (isinstance(zone_price, float) and math.isnan(zone_price)):
                zone_line = f"📉 {zone_label}: N/A"
            else:
                zone_line = f"📉 {zone_label}: {zone_price:.5f}"
            
            return (
                f"📊 Asset: {asset}\n"
                f"{signal_emoji} Signal: *{signal_type}*\n"
                f"📈 Entry Price: {price:.5f}\n"
                f"{zone_line}\n"
                f"⏳ Expiration: {expiration_min} minute{'s' if expiration_min != 1 else ''}"
            )
            
        except Exception as e:
            print(f"[ERROR] Error formatting signal: {e}")
            return f"❌ Error formatting signal: {e}"
    
    async def generate_signal(self, asset, expiration_time_minutes, fetch_function=None):
        """Complete signal generation with proper timeframe selection and analysis"""
        try:
            print(f"[INFO] Generating signal for {asset} with {expiration_time_minutes} minute expiration")
            
            # Step 1: Choose correct timeframe
            timeframe = self.get_timeframe_for_expiration(expiration_time_minutes)
            print(f"[INFO] Selected timeframe: {timeframe}")
            
            # Step 2: Fetch historical data
            history_data = await self.fetch_candles(asset, timeframe=timeframe, limit=200, fetch_function=fetch_function)
            print(f"[DEBUG] History data received: {len(history_data) if history_data else 0} points")
            if history_data:
                print(f"[DEBUG] Sample history data: {history_data[:3]}")
                print(f"[DEBUG] Last data point: {history_data[-1] if history_data else 'None'}")
            
            if not history_data:
                print(f"[WARNING] No history data received for {asset}")
                return self.format_signal("HOLD", asset, 0, None, expiration_time_minutes)
            
            # Step 3: Create analysis object
            analysis = HistorySummary(history_data, time_minutes=expiration_time_minutes)
            
            # Step 4: Calculate indicators
            indicators_data = analysis.get_all_indicators()
            if not indicators_data or "Indicators" not in indicators_data:
                print(f"[WARNING] No indicators data for {asset}")
                return self.format_signal("HOLD", asset, 0, None, expiration_time_minutes)
            
            indicators = indicators_data["Indicators"]
            
            # Step 5: Get current price and RSI
            current_price = history_data[-1][1] if history_data else 0  # Value column
            print(f"[DEBUG] Current price extracted: {current_price}")
            rsi = indicators.get("RSI")
            
            # Step 6: Detect market structure
            history_df = pd.DataFrame(history_data, columns=["Timestamp", "Value"])
            structure = self.detect_market_structure(history_df)
            
            # Step 7: Detect candlestick patterns
            if len(history_data) >= 2:
                last_candle = {"Value": history_data[-1][1]}
                prev_candle = {"Value": history_data[-2][1]}
                pattern = self.detect_candlestick_pattern(last_candle, prev_candle)
            else:
                pattern = "none"
            
            # Step 8: Get support/resistance levels
            support_resistance = indicators.get("Support and Resistance", {})
            support_levels = [support_resistance.get("Support")] if support_resistance else []
            resistance_levels = [support_resistance.get("Resistance")] if support_resistance else []
            
            # Filter out None values
            support_levels = [s for s in support_levels if s is not None]
            resistance_levels = [r for r in resistance_levels if r is not None]
            
            print(f"[DEBUG] Analysis results:")
            print(f"  - Structure: {structure}")
            print(f"  - Pattern: {pattern}")
            print(f"  - RSI: {rsi}")
            print(f"  - Support levels: {support_levels}")
            print(f"  - Resistance levels: {resistance_levels}")
            print(f"  - Current price: {current_price}")
            
            # Step 9: Signal conditions (more flexible)
            # BUY Signal conditions - need at least 3 out of 4 conditions
            buy_conditions = [
                self.is_support_zone(current_price, support_levels),
                structure in ["bullish", "neutral"],  # Allow neutral structure
                pattern in ["bullish_engulfing", "pin_bar"],
                rsi is not None and rsi < 40  # More flexible RSI (was 30)
            ]
            buy_score = sum(buy_conditions)
            
            # SELL Signal conditions - need at least 3 out of 4 conditions
            sell_conditions = [
                self.is_resistance_zone(current_price, resistance_levels),
                structure in ["bearish", "neutral"],  # Allow neutral structure
                pattern in ["bearish_engulfing", "pin_bar"],
                rsi is not None and rsi > 60  # More flexible RSI (was 70)
            ]
            sell_score = sum(sell_conditions)
            
            print(f"[DEBUG] Signal scores - BUY: {buy_score}/4, SELL: {sell_score}/4")
            
            # Generate signals based on scores
            if buy_score >= 3:
                zone_price = support_levels[0] if support_levels else None
                print(f"[DEBUG] BUY signal generated (score: {buy_score}/4)")
                return self.format_signal("BUY", asset, current_price, zone_price, expiration_time_minutes)
            
            elif sell_score >= 3:
                zone_price = resistance_levels[0] if resistance_levels else None
                print(f"[DEBUG] SELL signal generated (score: {sell_score}/4)")
                return self.format_signal("SELL", asset, current_price, zone_price, expiration_time_minutes)
            
            # HOLD Signal (no clear signal)
            print(f"[DEBUG] HOLD signal - insufficient conditions (BUY: {buy_score}/4, SELL: {sell_score}/4)")
            # Show the nearest support or resistance level for context
            nearest_zone = None
            if support_levels and resistance_levels:
                # Find which level is closer to current price
                nearest_support = min(support_levels, key=lambda x: abs(current_price - x))
                nearest_resistance = min(resistance_levels, key=lambda x: abs(current_price - x))
                
                if abs(current_price - nearest_support) < abs(current_price - nearest_resistance):
                    nearest_zone = nearest_support
                else:
                    nearest_zone = nearest_resistance
            elif support_levels:
                nearest_zone = min(support_levels, key=lambda x: abs(current_price - x))
            elif resistance_levels:
                nearest_zone = min(resistance_levels, key=lambda x: abs(current_price - x))
            
            return self.format_signal("HOLD", asset, current_price, nearest_zone, expiration_time_minutes)
            
        except Exception as e:
            print(f"[ERROR] Critical error in generate_signal: {e}")
            return self.format_signal("HOLD", asset, 0, None, expiration_time_minutes)
