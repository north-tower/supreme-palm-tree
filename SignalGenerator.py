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
            
            print(f"[DEBUG] Fetching candles for {asset} with period {period}")
            
            # Use the provided fetch function or fallback
            if fetch_function:
                results, data = await fetch_function(asset, period, "cZoCQNWriz")
            else:
                # Fallback: import here to avoid circular imports
                from demo_test import fetch_summary
                results, data = await fetch_summary(asset, period, "cZoCQNWriz")
            
            print(f"[DEBUG] Fetch results: {type(results)}")
            print(f"[DEBUG] Fetch data: {type(data)}")
            print(f"[DEBUG] Data length: {len(data) if data else 0}")
            
            if not data or len(data) < 10:
                print(f"[WARNING] Insufficient data for {asset} with timeframe {timeframe}")
                return None
            
            # Validate data structure
            if data and len(data) > 0:
                sample_point = data[0]
                print(f"[DEBUG] Sample data point: {sample_point}")
                print(f"[DEBUG] Sample point type: {type(sample_point)}")
                if isinstance(sample_point, (list, tuple)):
                    print(f"[DEBUG] Sample point length: {len(sample_point)}")
                    for i, val in enumerate(sample_point):
                        print(f"[DEBUG] Index {i}: {val} (type: {type(val)})")
                
                # Check if data has valid prices
                valid_prices = 0
                for point in data:
                    if isinstance(point, (list, tuple)) and len(point) >= 2:
                        price = point[1]
                        if isinstance(price, (int, float)) and price > 0:
                            valid_prices += 1
                
                print(f"[DEBUG] Valid prices found: {valid_prices}/{len(data)}")
                
                if valid_prices < 5:
                    print(f"[WARNING] Too few valid prices in data")
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
    
    async def generate_signal(self, asset, expiration_time_minutes, fetch_function=None, lang_manager=None, mode='standard'):
        """Complete signal generation with proper timeframe selection and analysis. Mode can be 'standard' or 'smc'."""
        try:
            print(f"[INFO] Generating signal for {asset} with {expiration_time_minutes} minute expiration (mode={mode})")
            
            # Step 1: Choose correct timeframe
            timeframe = self.get_timeframe_for_expiration(expiration_time_minutes)
            print(f"[INFO] Selected timeframe: {timeframe}")
            
            # Step 2: Fetch historical data
            history_data = await self.fetch_candles(asset, timeframe=timeframe, limit=200, fetch_function=fetch_function)
            print(f"[DEBUG] History data received: {len(history_data) if history_data else 0} points")
            if history_data:
                print(f"[DEBUG] Sample history data: {history_data[:3]}")
                print(f"[DEBUG] Last data point: {history_data[-1] if history_data else 'None'}")
            
            # Step 2.5: Fallback - try to get data from the main bot's fetch function
            if not history_data or len(history_data) < 10:
                print(f"[WARNING] Insufficient data from primary fetch, trying fallback...")
                try:
                    # Try to get data using the main bot's fetch function directly
                    if fetch_function:
                        results, fallback_data = await fetch_function(asset, 1, "cZoCQNWriz")
                        if fallback_data and len(fallback_data) >= 10:
                            print(f"[DEBUG] Fallback data received: {len(fallback_data)} points")
                            history_data = fallback_data
                        else:
                            print(f"[WARNING] Fallback data also insufficient")
                except Exception as e:
                    print(f"[ERROR] Fallback fetch failed: {e}")
            
            if not history_data or len(history_data) < 10:
                print(f"[WARNING] Insufficient history data for {asset}")
                return self.format_smc_signal("HOLD", asset, 0, None, None, expiration_time_minutes, lang_manager=lang_manager)
            
            # SMC Mode: Use pure SMC logic if requested
            if mode == 'smc':
                print(f"[INFO] Running pure SMC logic for {asset}")
                return self.generate_smc_pure_signal(asset, history_data, expiration_time_minutes, lang_manager)
            
            # --- Standard (retail TA + SMC hybrid) logic below ---
            # Step 3: Validate current price
            current_price = history_data[-1][1] if history_data else 0  # Value column
            print(f"[DEBUG] Current price extracted: {current_price}")
            print(f"[DEBUG] History data structure: {type(history_data)}")
            print(f"[DEBUG] Last data point: {history_data[-1] if history_data else 'None'}")
            print(f"[DEBUG] Data sample: {history_data[:3] if history_data else 'None'}")
            
            # Validate current price is not zero or invalid
            if current_price <= 0 or math.isnan(current_price):
                print(f"[WARNING] Invalid current price: {current_price}")
                # Try alternative extraction methods
                if history_data and len(history_data) > 0:
                    last_point = history_data[-1]
                    print(f"[DEBUG] Last point structure: {last_point}")
                    if isinstance(last_point, (list, tuple)) and len(last_point) >= 2:
                        # Try different indices
                        for i in range(len(last_point)):
                            potential_price = last_point[i]
                            if isinstance(potential_price, (int, float)) and potential_price > 0:
                                print(f"[DEBUG] Found valid price at index {i}: {potential_price}")
                                current_price = potential_price
                                break
                
                if current_price <= 0 or math.isnan(current_price):
                    print(f"[WARNING] Still invalid current price after fallback: {current_price}")
                    return self.format_smc_signal("HOLD", asset, 0, None, None, expiration_time_minutes, lang_manager=lang_manager)
            
            # Step 4: Create analysis object
            analysis = HistorySummary(history_data, time_minutes=expiration_time_minutes)
            
            # Step 5: Calculate indicators
            indicators_data = analysis.get_all_indicators()
            if not indicators_data or "Indicators" not in indicators_data:
                print(f"[WARNING] No indicators data for {asset}")
                return self.format_smc_signal("HOLD", asset, current_price, None, None, expiration_time_minutes, lang_manager=lang_manager)
            
            indicators = indicators_data["Indicators"]
            
            # Step 6: Get RSI
            rsi = indicators.get("RSI")
            print(f"[DEBUG] RSI: {rsi}")
            
            # Step 6.5: Enhanced Standard Mode Indicators
            if mode == 'standard':
                # Calculate additional indicators for standard mode
                macd_signal = self.calculate_macd(history_data)
                bb_signal = self.calculate_bollinger_bands(history_data)
                ma_signal = self.calculate_moving_averages(history_data)
                
                print(f"[DEBUG] Enhanced Standard Mode Indicators:")
                print(f"  - MACD: {macd_signal}")
                print(f"  - Bollinger Bands: {bb_signal}")
                print(f"  - Moving Averages: {ma_signal}")
            
            # Step 7: Detect market structure
            history_df = pd.DataFrame(history_data, columns=["Timestamp", "Value"])
            structure = self.detect_market_structure(history_df)
            
            # Step 8: Detect candlestick patterns
            if len(history_data) >= 2:
                last_candle = {"Value": history_data[-1][1]}
                prev_candle = {"Value": history_data[-2][1]}
                pattern = self.detect_candlestick_pattern(last_candle, prev_candle)
            else:
                pattern = "none"
            
            # Step 9: Get support/resistance levels
            support_resistance = indicators.get("Support and Resistance", {})
            support_levels = [support_resistance.get("Support")] if support_resistance else []
            resistance_levels = [support_resistance.get("Resistance")] if support_resistance else []
            
            # Filter out None values
            support_levels = [s for s in support_levels if s is not None and not math.isnan(s)]
            resistance_levels = [r for r in resistance_levels if r is not None and not math.isnan(r)]
            
            # Step 10: SMC Analysis (Smart Money Concepts)
            print(f"[DEBUG] Starting SMC analysis...")
            swing_highs, swing_lows = self.detect_swing_points(history_df, lookback=5)
            bos_type, bos_price = self.detect_break_of_structure(swing_highs, swing_lows, current_price)
            order_block = self.find_best_order_block(history_df, bos_type, bos_price, lookback=20)
            smc_signal = self.generate_smc_signal(asset, current_price, bos_type, bos_price, order_block, rsi, swing_highs, swing_lows)
            
            print(f"[DEBUG] SMC Analysis results:")
            print(f"  - Swing Highs: {len(swing_highs)}")
            print(f"  - Swing Lows: {len(swing_lows)}")
            print(f"  - BOS Type: {bos_type}")
            print(f"  - BOS Price: {bos_price}")
            print(f"  - Order Block: {order_block}")
            print(f"  - SMC Signal: {smc_signal}")
            
            print(f"[DEBUG] Analysis results:")
            print(f"  - Structure: {structure}")
            print(f"  - Pattern: {pattern}")
            print(f"  - RSI: {rsi}")
            print(f"  - Support levels: {support_levels}")
            print(f"  - Resistance levels: {resistance_levels}")
            print(f"  - Current price: {current_price}")
            
            # Step 11: Signal Generation (Prioritize SMC over traditional TA)
            if smc_signal:
                # SMC signal takes priority
                signal_type = smc_signal["type"]
                zone_price = smc_signal["order_block_price"]
                print(f"[DEBUG] SMC signal generated: {signal_type} - {smc_signal['reason']}")
                return self.format_smc_signal(signal_type, asset, current_price, zone_price, 
                                            smc_signal["bos_price"], expiration_time_minutes, lang_manager=lang_manager)
            
            # Step 12: Enhanced Traditional TA Signal conditions for Standard Mode
            if mode == 'standard':
                # Use enhanced indicators for standard mode
                unique_prices = set(history_df["Value"].unique())
                is_flat_market = len(unique_prices) == 1
                
                if is_flat_market:
                    print(f"[DEBUG] Flat market detected - using flexible conditions")
                    threshold = 2  # Lower threshold for flat markets
                else:
                    threshold = 3  # Higher threshold for trending markets
                
                # Enhanced buy conditions for standard mode
                buy_conditions = [
                    self.is_support_zone(current_price, support_levels, tolerance=0.003),
                    structure in ["bullish", "neutral"],
                    pattern in ["bullish_engulfing", "pin_bar"],
                    rsi is not None and rsi < 55,
                    macd_signal == "bullish" if macd_signal else False,
                    bb_signal == "oversold" if bb_signal else False,
                    ma_signal == "bullish" if ma_signal else False
                ]
                
                # Enhanced sell conditions for standard mode
                sell_conditions = [
                    self.is_resistance_zone(current_price, resistance_levels, tolerance=0.002),
                    structure in ["bearish", "neutral"],
                    pattern in ["bearish_engulfing", "pin_bar"],
                    rsi is not None and rsi > 55,
                    macd_signal == "bearish" if macd_signal else False,
                    bb_signal == "overbought" if bb_signal else False,
                    ma_signal == "bearish" if ma_signal else False
                ]
                
                buy_score = sum(buy_conditions)
                sell_score = sum(sell_conditions)
                
                print(f"[DEBUG] Enhanced Standard Mode Signal scores - BUY: {buy_score}/{threshold}, SELL: {sell_score}/{threshold}")
                print(f"[DEBUG] Buy conditions: {buy_conditions}")
                print(f"[DEBUG] Sell conditions: {sell_conditions}")
                
                if buy_score >= threshold:
                    zone_price = support_levels[0] if support_levels else None
                    print(f"[DEBUG] BUY signal generated (score: {buy_score}/{threshold})")
                    return self.format_smc_signal("BUY", asset, current_price, zone_price, zone_price, expiration_time_minutes, lang_manager=lang_manager)
                elif sell_score >= threshold:
                    zone_price = resistance_levels[0] if resistance_levels else None
                    print(f"[DEBUG] SELL signal generated (score: {sell_score}/{threshold})")
                    return self.format_smc_signal("SELL", asset, current_price, zone_price, zone_price, expiration_time_minutes, lang_manager=lang_manager)
            else:
                # Original logic for other modes
                unique_prices = set(history_df["Value"].unique())
                is_flat_market = len(unique_prices) == 1
                if is_flat_market:
                    print(f"[DEBUG] Flat market detected - using flexible conditions")
                    threshold = 1
                    buy_rsi_condition = rsi is not None and rsi < 75  # More flexible for BUY
                    sell_rsi_condition = rsi is not None and rsi > 25
                else:
                    threshold = 2
                    buy_rsi_condition = rsi is not None and rsi < 55  # More flexible for BUY
                    sell_rsi_condition = rsi is not None and rsi > 55
                buy_conditions = [
                    self.is_support_zone(current_price, support_levels, tolerance=0.003),  # Slightly more tolerant
                    structure in ["bullish", "neutral"],
                    pattern in ["bullish_engulfing", "pin_bar"],
                    buy_rsi_condition
                ]
                buy_score = sum(buy_conditions)
                sell_conditions = [
                    self.is_resistance_zone(current_price, resistance_levels, tolerance=0.002),
                    structure in ["bearish", "neutral"],
                    pattern in ["bearish_engulfing", "pin_bar"],
                    sell_rsi_condition
                ]
                sell_score = sum(sell_conditions)
                print(f"[DEBUG] Traditional TA Signal scores - BUY: {buy_score}/{threshold}, SELL: {sell_score}/{threshold}")
                print(f"[DEBUG] Buy conditions: {buy_conditions}")
                print(f"[DEBUG] Sell conditions: {sell_conditions}")
                if buy_score >= threshold:
                    zone_price = support_levels[0] if support_levels else None
                    print(f"[DEBUG] BUY signal generated (score: {buy_score}/{threshold})")
                    return self.format_smc_signal("BUY", asset, current_price, zone_price, zone_price, expiration_time_minutes, lang_manager=lang_manager)
                elif sell_score >= threshold:
                    zone_price = resistance_levels[0] if resistance_levels else None
                    print(f"[DEBUG] SELL signal generated (score: {buy_score}/{threshold})")
                    return self.format_smc_signal("SELL", asset, current_price, zone_price, zone_price, expiration_time_minutes, lang_manager=lang_manager)
            
            # Final fallback: Generate signal based on RSI only if no other conditions met
            print(f"[DEBUG] No traditional TA signal - trying RSI-only fallback")
            if rsi is not None:
                if rsi < 30:  # Oversold
                    print(f"[DEBUG] RSI-only BUY signal (RSI: {rsi})")
                    return self.format_smc_signal("BUY", asset, current_price, current_price, 
                                                current_price, expiration_time_minutes, lang_manager=lang_manager)
                elif rsi > 70:  # Overbought
                    print(f"[DEBUG] RSI-only SELL signal (RSI: {rsi})")
                    return self.format_smc_signal("SELL", asset, current_price, current_price, 
                                                current_price, expiration_time_minutes, lang_manager=lang_manager)
            
            # HOLD Signal (no clear signal)
            print(f"[DEBUG] HOLD signal - insufficient conditions")
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
            
            # Force SMC format for HOLD signals too
            return self.format_smc_signal("HOLD", asset, current_price, nearest_zone, 
                                        nearest_zone, expiration_time_minutes, lang_manager=lang_manager)
            
        except Exception as e:
            print(f"[ERROR] Critical error in generate_signal: {e}")
            return self.format_smc_signal("HOLD", asset, 0, None, None, expiration_time_minutes, lang_manager=lang_manager)

    def detect_swing_points(self, history_df, lookback=5):
        """Detect swing highs and lows for SMC analysis"""
        try:
            if history_df is None or len(history_df) < lookback * 2:
                print(f"[DEBUG] Insufficient data for swing point detection: {len(history_df) if history_df is not None else 0} points")
                return [], []
            
            swing_highs = []
            swing_lows = []
            
            # Use a more flexible lookback for smaller datasets
            actual_lookback = min(lookback, len(history_df) // 4)
            if actual_lookback < 2:
                actual_lookback = 2
            
            print(f"[DEBUG] Using lookback of {actual_lookback} for swing point detection")
            
            for i in range(actual_lookback, len(history_df) - actual_lookback):
                current_price = history_df["Value"].iloc[i]
                
                # Skip invalid prices
                if current_price <= 0 or math.isnan(current_price):
                    continue
                
                # Check if current point is a swing high
                left_prices = history_df["Value"].iloc[i-actual_lookback:i]
                right_prices = history_df["Value"].iloc[i+1:i+actual_lookback+1]
                
                # Filter out invalid prices
                left_prices = left_prices[left_prices > 0]
                right_prices = right_prices[right_prices > 0]
                
                if len(left_prices) > 0 and len(right_prices) > 0:
                    if current_price > left_prices.max() and current_price > right_prices.max():
                        swing_highs.append({
                            "index": i,
                            "price": current_price,
                            "timestamp": history_df["Timestamp"].iloc[i]
                        })
                    
                    # Check if current point is a swing low
                    if current_price < left_prices.min() and current_price < right_prices.min():
                        swing_lows.append({
                            "index": i,
                            "price": current_price,
                            "timestamp": history_df["Timestamp"].iloc[i]
                        })
            
            print(f"[DEBUG] Detected {len(swing_highs)} swing highs and {len(swing_lows)} swing lows")
            return swing_highs, swing_lows
            
        except Exception as e:
            print(f"[ERROR] Error detecting swing points: {e}")
            return [], []
    
    def detect_break_of_structure(self, swing_highs, swing_lows, current_price):
        """Detect Break of Structure (BOS) for SMC analysis"""
        try:
            if not swing_highs and not swing_lows:
                print(f"[DEBUG] No swing points available for BOS detection")
                return None, None
            
            if current_price <= 0 or math.isnan(current_price):
                print(f"[DEBUG] Invalid current price for BOS detection: {current_price}")
                return None, None
            
            bos_type = None
            bos_price = None
            
            # Check for bullish BOS (break above recent swing high)
            if swing_highs:
                # Get the most recent swing high (highest index)
                recent_swing_high = max(swing_highs, key=lambda x: x["index"])
                swing_high_price = recent_swing_high["price"]
                
                # Check if current price is above the swing high (with small tolerance)
                if current_price > swing_high_price * 0.999:  # Allow small tolerance
                    bos_type = "bullish"
                    bos_price = swing_high_price
                    print(f"[DEBUG] Bullish BOS detected: current price {current_price} > swing high {swing_high_price}")
            
            # Check for bearish BOS (break below recent swing low)
            if swing_lows:
                # Get the most recent swing low (highest index)
                recent_swing_low = max(swing_lows, key=lambda x: x["index"])
                swing_low_price = recent_swing_low["price"]
                
                # Check if current price is below the swing low (with small tolerance)
                if current_price < swing_low_price * 1.001:  # Allow small tolerance
                    bos_type = "bearish"
                    bos_price = swing_low_price
                    print(f"[DEBUG] Bearish BOS detected: current price {current_price} < swing low {swing_low_price}")
            
            if bos_type:
                print(f"[DEBUG] BOS detected: {bos_type} at {bos_price}")
            else:
                print(f"[DEBUG] No BOS detected")
            
            return bos_type, bos_price
            
        except Exception as e:
            print(f"[ERROR] Error detecting BOS: {e}")
            return None, None
    
    def validate_order_block_quality(self, order_block, history_df, bos_type):
        """Validate the quality of an order block based on SMC principles"""
        try:
            if not order_block or not history_df:
                return False
            
            if not order_block.get("zone", False):
                return True  # Skip validation for old single-price format
            
            ob_high = order_block.get("high")
            ob_low = order_block.get("low")
            ob_index = order_block.get("index")
            
            if ob_high is None or ob_low is None or ob_index is None:
                return False
            
            # Check if the order block has a reasonable size
            zone_size = ob_high - ob_low
            if zone_size <= 0:
                return False
            
            # Calculate the percentage size of the zone
            zone_percentage = zone_size / ob_low
            if zone_percentage < 0.0005:  # Zone too small (less than 0.05%)
                print(f"[DEBUG] Order block zone too small: {zone_percentage:.6f}")
                return False
            
            if zone_percentage > 0.05:  # Zone too large (more than 5%)
                print(f"[DEBUG] Order block zone too large: {zone_percentage:.6f}")
                return False
            
            # Check if the order block is followed by a significant move in the expected direction
            if ob_index + 5 < len(history_df):
                # Look at the next few candles after the order block
                next_prices = history_df["Value"].iloc[ob_index+1:ob_index+6].values
                if len(next_prices) > 0:
                    if bos_type == "bullish":
                        # For bullish order block, check if price moved up significantly
                        max_move = max(next_prices) - ob_high
                        move_percentage = max_move / ob_high if ob_high > 0 else 0
                        if move_percentage < 0.001:  # Less than 0.1% move
                            print(f"[DEBUG] Bullish order block followed by weak move: {move_percentage:.6f}")
                            return False
                    elif bos_type == "bearish":
                        # For bearish order block, check if price moved down significantly
                        max_move = ob_low - min(next_prices)
                        move_percentage = max_move / ob_low if ob_low > 0 else 0
                        if move_percentage < 0.001:  # Less than 0.1% move
                            print(f"[DEBUG] Bearish order block followed by weak move: {move_percentage:.6f}")
                            return False
            
            print(f"[DEBUG] Order block quality validation passed: size={zone_percentage:.6f}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error validating order block quality: {e}")
            return False

    def find_best_order_block(self, history_df, bos_type, bos_price, lookback=20):
        """Find the best order block by evaluating multiple candidates"""
        try:
            if not bos_type or not bos_price:
                print(f"[DEBUG] No BOS information available for order block detection")
                return None
            
            if history_df is None or len(history_df) < lookback + 1:
                print(f"[DEBUG] Insufficient data for order block detection")
                return None
            
            # Use a more flexible lookback for smaller datasets
            actual_lookback = min(lookback, len(history_df) - 1)
            if actual_lookback < 5:
                actual_lookback = 5
            
            print(f"[DEBUG] Looking for best order block with lookback {actual_lookback}")
            
            # Find multiple order block candidates
            candidates = []
            
            if bos_type == "bullish":
                # For bullish BOS, look for bearish moves before the break
                for i in range(len(history_df) - actual_lookback, len(history_df) - 2):
                    current_price = history_df["Value"].iloc[i]
                    next_price = history_df["Value"].iloc[i + 1]
                    
                    # Skip invalid prices
                    if current_price <= 0 or next_price <= 0 or math.isnan(current_price) or math.isnan(next_price):
                        continue
                    
                    # Look for bearish moves (price going down)
                    if current_price > next_price:  # Bearish candle
                        # Check if this is a significant move
                        price_change = (current_price - next_price) / current_price
                        if price_change > 0.0005:  # 0.05% minimum move
                            # Find the range of this potential order block
                            ob_high = current_price
                            ob_low = next_price
                            
                            # Look for additional candles in the same direction
                            for j in range(i + 2, min(i + 5, len(history_df))):
                                if j < len(history_df):
                                    j_price = history_df["Value"].iloc[j]
                                    if j_price > 0 and not math.isnan(j_price):
                                        if j_price < ob_low:
                                            ob_low = j_price
                                        elif j_price > ob_high:
                                            break
                            
                            # Calculate quality metrics
                            zone_size = ob_high - ob_low
                            zone_percentage = zone_size / ob_low if ob_low > 0 else 0
                            
                            # Score the candidate (higher score = better)
                            score = 0
                            if 0.001 <= zone_percentage <= 0.02:  # Optimal zone size
                                score += 3
                            elif 0.0005 <= zone_percentage <= 0.05:  # Acceptable zone size
                                score += 1
                            
                            if price_change > 0.002:  # Strong move
                                score += 2
                            elif price_change > 0.001:  # Moderate move
                                score += 1
                            
                            # Prefer order blocks closer to the BOS
                            distance_to_bos = len(history_df) - 1 - i
                            if distance_to_bos <= 10:
                                score += 2
                            elif distance_to_bos <= 20:
                                score += 1
                            
                            candidate = {
                                "index": i,
                                "high": ob_high,
                                "low": ob_low,
                                "price": (ob_high + ob_low) / 2,
                                "type": "bullish_ob",
                                "timestamp": history_df["Timestamp"].iloc[i],
                                "zone": True,
                                "score": score,
                                "price_change": price_change,
                                "zone_percentage": zone_percentage,
                                "distance_to_bos": distance_to_bos
                            }
                            
                            candidates.append(candidate)
                            print(f"[DEBUG] Bullish OB candidate: score={score}, price_change={price_change:.6f}, zone_size={zone_percentage:.6f}, distance={distance_to_bos}")
                
            elif bos_type == "bearish":
                # For bearish BOS, look for bullish moves before the break
                for i in range(len(history_df) - actual_lookback, len(history_df) - 2):
                    current_price = history_df["Value"].iloc[i]
                    next_price = history_df["Value"].iloc[i + 1]
                    
                    # Skip invalid prices
                    if current_price <= 0 or next_price <= 0 or math.isnan(current_price) or math.isnan(next_price):
                        continue
                    
                    # Look for bullish moves (price going up)
                    if current_price < next_price:  # Bullish candle
                        # Check if this is a significant move
                        price_change = (next_price - current_price) / current_price
                        if price_change > 0.0005:  # 0.05% minimum move
                            # Find the range of this potential order block
                            ob_low = current_price
                            ob_high = next_price
                            
                            # Look for additional candles in the same direction
                            for j in range(i + 2, min(i + 5, len(history_df))):
                                if j < len(history_df):
                                    j_price = history_df["Value"].iloc[j]
                                    if j_price > 0 and not math.isnan(j_price):
                                        if j_price > ob_high:
                                            ob_high = j_price
                                        elif j_price < ob_low:
                                            break
                            
                            # Calculate quality metrics
                            zone_size = ob_high - ob_low
                            zone_percentage = zone_size / ob_low if ob_low > 0 else 0
                            
                            # Score the candidate (higher score = better)
                            score = 0
                            if 0.001 <= zone_percentage <= 0.02:  # Optimal zone size
                                score += 3
                            elif 0.0005 <= zone_percentage <= 0.05:  # Acceptable zone size
                                score += 1
                            
                            if price_change > 0.002:  # Strong move
                                score += 2
                            elif price_change > 0.001:  # Moderate move
                                score += 1
                            
                            # Prefer order blocks closer to the BOS
                            distance_to_bos = len(history_df) - 1 - i
                            if distance_to_bos <= 10:
                                score += 2
                            elif distance_to_bos <= 20:
                                score += 1
                            
                            candidate = {
                                "index": i,
                                "high": ob_high,
                                "low": ob_low,
                                "price": (ob_high + ob_low) / 2,
                                "type": "bearish_ob",
                                "timestamp": history_df["Timestamp"].iloc[i],
                                "zone": True,
                                "score": score,
                                "price_change": price_change,
                                "zone_percentage": zone_percentage,
                                "distance_to_bos": distance_to_bos
                            }
                            
                            candidates.append(candidate)
                            print(f"[DEBUG] Bearish OB candidate: score={score}, price_change={price_change:.6f}, zone_size={zone_percentage:.6f}, distance={distance_to_bos}")
            
            # Select the best candidate
            if candidates:
                # Sort by score (highest first), then by distance (closest first)
                candidates.sort(key=lambda x: (-x["score"], x["distance_to_bos"]))
                best_candidate = candidates[0]
                
                print(f"[DEBUG] Selected best order block: score={best_candidate['score']}, type={best_candidate['type']}")
                print(f"[DEBUG] Order block zone: {best_candidate['low']:.6f} - {best_candidate['high']:.6f}")
                
                return best_candidate
            else:
                print(f"[DEBUG] No order block candidates found")
                return None
            
        except Exception as e:
            print(f"[ERROR] Error finding best order block: {e}")
            return None

    def find_order_block(self, history_df, bos_type, bos_price, lookback=20):
        """Find Order Block based on SMC principles - looks for strong moves followed by retracements"""
        try:
            if not bos_type or not bos_price:
                print(f"[DEBUG] No BOS information available for order block detection")
                return None
            
            if history_df is None or len(history_df) < lookback + 1:
                print(f"[DEBUG] Insufficient data for order block detection")
                return None
            
            # Use a more flexible lookback for smaller datasets
            actual_lookback = min(lookback, len(history_df) - 1)
            if actual_lookback < 5:
                actual_lookback = 5
            
            print(f"[DEBUG] Looking for order block with lookback {actual_lookback}")
            
            # Find the order block zone based on SMC principles
            order_block = None
            
            if bos_type == "bullish":
                # For bullish BOS, look for the last strong bearish move before the break
                # This creates a bullish order block (buyers waiting to enter)
                for i in range(len(history_df) - actual_lookback, len(history_df) - 2):
                    current_price = history_df["Value"].iloc[i]
                    next_price = history_df["Value"].iloc[i + 1]
                    
                    # Skip invalid prices
                    if current_price <= 0 or next_price <= 0 or math.isnan(current_price) or math.isnan(next_price):
                        continue
                    
                    # Look for a strong bearish move (price going down significantly)
                    if current_price > next_price:  # Bearish candle (price going down)
                        # Check if this is a significant move (at least 0.1% drop)
                        price_change = (current_price - next_price) / current_price
                        if price_change > 0.001:  # 0.1% minimum move
                            # Find the range of this order block (look for the high and low)
                            ob_high = current_price
                            ob_low = next_price
                            
                            # Look for additional candles in the same direction to establish the zone
                            for j in range(i + 2, min(i + 5, len(history_df))):
                                if j < len(history_df):
                                    j_price = history_df["Value"].iloc[j]
                                    if j_price > 0 and not math.isnan(j_price):
                                        if j_price < ob_low:
                                            ob_low = j_price
                                        elif j_price > ob_high:
                                            # If price goes above the high, this might be the end of the order block
                                            break
                            
                            order_block = {
                                "index": i,
                                "high": ob_high,
                                "low": ob_low,
                                "price": (ob_high + ob_low) / 2,  # Mid-point for compatibility
                                "type": "bullish_ob",
                                "timestamp": history_df["Timestamp"].iloc[i],
                                "zone": True
                            }
                            print(f"[DEBUG] Found bullish order block zone: high={ob_high}, low={ob_low}, mid={order_block['price']}")
                            break
                
            elif bos_type == "bearish":
                # For bearish BOS, look for the last strong bullish move before the break
                # This creates a bearish order block (sellers waiting to enter)
                for i in range(len(history_df) - actual_lookback, len(history_df) - 2):
                    current_price = history_df["Value"].iloc[i]
                    next_price = history_df["Value"].iloc[i + 1]
                    
                    # Skip invalid prices
                    if current_price <= 0 or next_price <= 0 or math.isnan(current_price) or math.isnan(next_price):
                        continue
                    
                    # Look for a strong bullish move (price going up significantly)
                    if current_price < next_price:  # Bullish candle (price going up)
                        # Check if this is a significant move (at least 0.1% rise)
                        price_change = (next_price - current_price) / current_price
                        if price_change > 0.001:  # 0.1% minimum move
                            # Find the range of this order block (look for the high and low)
                            ob_low = current_price
                            ob_high = next_price
                            
                            # Look for additional candles in the same direction to establish the zone
                            for j in range(i + 2, min(i + 5, len(history_df))):
                                if j < len(history_df):
                                    j_price = history_df["Value"].iloc[j]
                                    if j_price > 0 and not math.isnan(j_price):
                                        if j_price > ob_high:
                                            ob_high = j_price
                                        elif j_price < ob_low:
                                            # If price goes below the low, this might be the end of the order block
                                            break
                            
                            order_block = {
                                "index": i,
                                "high": ob_high,
                                "low": ob_low,
                                "price": (ob_high + ob_low) / 2,  # Mid-point for compatibility
                                "type": "bearish_ob",
                                "timestamp": history_df["Timestamp"].iloc[i],
                                "zone": True
                            }
                            print(f"[DEBUG] Found bearish order block zone: high={ob_high}, low={ob_low}, mid={order_block['price']}")
                            break
            
            if order_block:
                # Validate the quality of the order block
                if self.validate_order_block_quality(order_block, history_df, bos_type):
                    print(f"[DEBUG] Order block zone found and validated: {order_block['type']} at {order_block['price']} (range: {order_block['low']} - {order_block['high']})")
                    return order_block  # Return the validated order block
                else:
                    print(f"[DEBUG] Order block found but failed quality validation")
                    return None  # Return None if validation fails
            else:
                print(f"[DEBUG] No order block found")
                return None
            
        except Exception as e:
            print(f"[ERROR] Error finding order block: {e}")
            return None
    
    def is_price_in_order_block(self, current_price, order_block, tolerance=0.001):
        """Check if current price is in the order block area"""
        try:
            if not order_block:
                return False
            
            if current_price <= 0 or math.isnan(current_price):
                return False
            
            # Check if this is a zone-based order block
            if order_block.get("zone", False) and "high" in order_block and "low" in order_block:
                ob_high = order_block["high"]
                ob_low = order_block["low"]
                
                # Check if current price is within the order block zone
                if ob_low <= current_price <= ob_high:
                    print(f"[DEBUG] Order block zone check: current={current_price}, ob_range=[{ob_low}, {ob_high}] - PRICE IN ZONE")
                    return True
                else:
                    # Check if price is near the zone boundaries with tolerance
                    distance_to_zone = min(abs(current_price - ob_high), abs(current_price - ob_low))
                    zone_size = ob_high - ob_low
                    relative_distance = distance_to_zone / zone_size if zone_size > 0 else 0
                    
                    print(f"[DEBUG] Order block zone check: current={current_price}, ob_range=[{ob_low}, {ob_high}], distance_to_zone={distance_to_zone:.6f}, relative_distance={relative_distance:.6f}, tolerance={tolerance}")
                    
                    return relative_distance <= tolerance
            
            else:
                # Fallback to old single-price logic for compatibility
                ob_price = order_block["price"]
                if ob_price <= 0 or math.isnan(ob_price):
                    return False
                
                price_diff = abs(current_price - ob_price) / ob_price
                
                print(f"[DEBUG] Order block single-price check: current={current_price}, ob_price={ob_price}, diff={price_diff:.6f}, tolerance={tolerance}")
                
                return price_diff <= tolerance
            
        except Exception as e:
            print(f"[ERROR] Error checking order block: {e}")
            return False
    
    def generate_smc_signal(self, asset, current_price, bos_type, bos_price, order_block, rsi=None, swing_highs=None, swing_lows=None):
        """Generate SMC-based trading signal"""
        try:
            print(f"[DEBUG] SMC Signal Generation:")
            print(f"  - BOS Type: {bos_type}")
            print(f"  - BOS Price: {bos_price}")
            print(f"  - Order Block: {order_block}")
            print(f"  - Current Price: {current_price}")
            print(f"  - RSI: {rsi}")
            
            # Primary SMC signal generation with BOS and Order Block
            if bos_type and order_block:
                # Check if price is in order block area (more flexible)
                if self.is_price_in_order_block(current_price, order_block, tolerance=0.005):  # Increased tolerance
                    print(f"[DEBUG] Price is in Order Block area")
                    
                    # Generate signal based on BOS type and order block
                    if bos_type == "bullish" and order_block["type"] == "bullish_ob":
                        # Bullish BOS with bullish order block = BUY signal
                        if rsi is None or rsi < 80:  # More flexible RSI (was 70)
                            print(f"[DEBUG] SMC BUY signal conditions met")
                            return {
                                "type": "BUY",
                                "reason": "Bullish BOS + Order Block",
                                "bos_price": bos_price,
                                "order_block_price": order_block["price"]
                            }
                    
                    elif bos_type == "bearish" and order_block["type"] == "bearish_ob":
                        # Bearish BOS with bearish order block = SELL signal
                        if rsi is None or rsi > 20:  # More flexible RSI (was 30)
                            print(f"[DEBUG] SMC SELL signal conditions met")
                            return {
                                "type": "SELL",
                                "reason": "Bearish BOS + Order Block",
                                "bos_price": bos_price,
                                "order_block_price": order_block["price"]
                            }
                else:
                    print(f"[DEBUG] Price is NOT in Order Block area")
            
            # Secondary SMC: Generate signals based on swing points proximity (even without BOS)
            if swing_highs and swing_lows:
                print(f"[DEBUG] Attempting swing point-based SMC signal generation")
                
                # Find nearest swing points
                nearest_high = min(swing_highs, key=lambda x: abs(current_price - x["price"]))
                nearest_low = min(swing_lows, key=lambda x: abs(current_price - x["price"]))
                
                # Check if price is near swing levels
                high_distance = abs(current_price - nearest_high["price"]) / current_price
                low_distance = abs(current_price - nearest_low["price"]) / current_price
                
                print(f"[DEBUG] Distance to nearest swing high: {high_distance:.4f}")
                print(f"[DEBUG] Distance to nearest swing low: {low_distance:.4f}")
                
                # Generate signals based on proximity to swing levels with RSI confirmation
                if low_distance < 0.003 and rsi is not None and rsi < 65:  # Near swing low, more flexible
                    print(f"[DEBUG] SMC BUY signal - near swing low with RSI confirmation")
                    return {
                        "type": "BUY",
                        "reason": "Near Swing Low + RSI",
                        "bos_price": nearest_low["price"],
                        "order_block_price": nearest_low["price"]
                    }
                
                elif high_distance < 0.003 and rsi is not None and rsi > 35:  # Near swing high, more flexible
                    print(f"[DEBUG] SMC SELL signal - near swing high with RSI confirmation")
                    return {
                        "type": "SELL",
                        "reason": "Near Swing High + RSI",
                        "bos_price": nearest_high["price"],
                        "order_block_price": nearest_high["price"]
                    }
            
            # Tertiary SMC: Generate signals based on RSI extremes with swing context
            if rsi is not None:
                print(f"[DEBUG] Attempting RSI-based SMC signal generation")
                
                if rsi < 25:  # Oversold with swing context
                    if swing_lows:
                        nearest_low = min(swing_lows, key=lambda x: abs(current_price - x["price"]))
                        print(f"[DEBUG] SMC BUY signal - oversold RSI with swing context")
                        return {
                            "type": "BUY",
                            "reason": "Oversold RSI + Swing Context",
                            "bos_price": nearest_low["price"],
                            "order_block_price": nearest_low["price"]
                        }
                
                elif rsi > 75:  # Overbought with swing context
                    if swing_highs:
                        nearest_high = min(swing_highs, key=lambda x: abs(current_price - x["price"]))
                        print(f"[DEBUG] SMC SELL signal - overbought RSI with swing context")
                        return {
                            "type": "SELL",
                            "reason": "Overbought RSI + Swing Context",
                            "bos_price": nearest_high["price"],
                            "order_block_price": nearest_high["price"]
                        }
            
            print(f"[DEBUG] No SMC signal generated - falling back to traditional TA")
            return None
            
        except Exception as e:
            print(f"[ERROR] Error generating SMC signal: {e}")
            return None

    def format_smc_signal(self, signal_type, asset, price, order_block_price, bos_price, expiration_min, lang_manager=None):
        """Format SMC signal output with BOS and Order Block information"""
        try:
            if lang_manager is None:
                from language_manager import LanguageManager
                lang_manager = LanguageManager()
                print(f"[DEBUG] Created new language manager with language: {lang_manager.current_language}")
            else:
                print(f"[DEBUG] Using provided language manager with language: {lang_manager.current_language}")
            signal_emoji = {
                "BUY": "🟩",
                "SELL": "🟥", 
                "HOLD": "⬜"
            }.get(signal_type, "❔")
            
            # Handle None or NaN values
            if order_block_price is None or (isinstance(order_block_price, float) and math.isnan(order_block_price)):
                ob_line = f"📉 {lang_manager.get_text('order_block', 'Order Block')}: N/A"
            else:
                ob_line = f"📉 {lang_manager.get_text('order_block', 'Order Block')}: {order_block_price:.5f}"
            
            if bos_price is None or (isinstance(bos_price, float) and math.isnan(bos_price)):
                bos_line = f"📏 {lang_manager.get_text('bos_confirmed', 'BOS Confirmed at')}: N/A"
            else:
                bos_line = f"📏 {lang_manager.get_text('bos_confirmed', 'BOS Confirmed at')}: {bos_price:.5f}"
            
            # Get translated text for signal components
            asset_text = lang_manager.get_text('asset', 'Asset')
            signal_text = lang_manager.get_text('signal', 'Signal')
            entry_price_text = lang_manager.get_text('entry_price', 'Entry Price')
            expiration_text = lang_manager.get_text('expiration', 'Expiration')
            mode_text = lang_manager.get_text('mode', 'Mode')
            smc_analysis_text = lang_manager.get_text('smc_analysis', 'SMC Analysis')
            
            # Handle pluralization for expiration
            if expiration_min == 1:
                time_text = lang_manager.get_text('minute', 'minute')
            else:
                time_text = lang_manager.get_text('minutes', 'minutes')
            
            return (
                f"📊 {asset_text}: {asset}\n"
                f"{signal_emoji} {signal_text}: *{signal_type}*\n"
                f"📈 {entry_price_text}: {price:.5f}\n"
                f"{ob_line}\n"
                f"{bos_line}\n"
                f"⏳ {expiration_text}: {expiration_min} {time_text}\n"
                f"🧠 {mode_text}: {smc_analysis_text}"
            )
            
        except Exception as e:
            print(f"[ERROR] Error formatting SMC signal: {e}")
            # Fallback to English if translation fails
            signal_emoji = {
                "BUY": "🟩",
                "SELL": "🟥", 
                "HOLD": "⬜"
            }.get(signal_type, "❔")
            
            # Handle None or NaN values
            if order_block_price is None or (isinstance(order_block_price, float) and math.isnan(order_block_price)):
                ob_line = "📉 Order Block: N/A"
            else:
                ob_line = f"📉 Order Block: {order_block_price:.5f}"
            
            if bos_price is None or (isinstance(bos_price, float) and math.isnan(bos_price)):
                bos_line = "📏 BOS Confirmed at: N/A"
            else:
                bos_line = f"📏 BOS Confirmed at: {bos_price:.5f}"
            
            return (
                f"📊 Asset: {asset}\n"
                f"{signal_emoji} Signal: *{signal_type}*\n"
                f"📈 Entry Price: {price:.5f}\n"
                f"{ob_line}\n"
                f"{bos_line}\n"
                f"⏳ Expiration: {expiration_min} minute{'s' if expiration_min != 1 else ''}\n"
                f"🧠 Mode: SMC Analysis"
            )

    def generate_smc_pure_signal(self, asset, history_data, expiration_time_minutes, lang_manager=None):
        """Pure SMC logic: swing labeling, strict BOS, order block, confirmation. Returns formatted SMC signal."""
        import pandas as pd
        print(f"[SMC] [DEBUG] Running pure SMC logic for {asset}")
        if not history_data or len(history_data) < 20:
            print(f"[SMC] [WARNING] Not enough data for SMC analysis")
            return self.format_smc_signal("HOLD", asset, 0, None, None, expiration_time_minutes, lang_manager=lang_manager)

        # Convert to DataFrame for easier processing
        df = pd.DataFrame(history_data, columns=["Timestamp", "Value"])
        prices = df["Value"].values
        timestamps = df["Timestamp"].values
        current_price = prices[-1]

        # --- 1. Find swing highs/lows ---
        swing_points = []  # List of dicts: {index, price, type}
        lookback = 3
        for i in range(lookback, len(prices) - lookback):
            window = prices[i-lookback:i+lookback+1]
            if prices[i] == max(window):
                swing_points.append({"index": i, "price": prices[i], "type": "high"})
            elif prices[i] == min(window):
                swing_points.append({"index": i, "price": prices[i], "type": "low"})

        # --- 2. Label swing points (HH, LL, HL, LH) ---
        labeled_swings = []
        for idx, pt in enumerate(swing_points):
            if pt["type"] == "high":
                # Compare to previous high
                prev_highs = [p for p in swing_points[:idx] if p["type"] == "high"]
                if prev_highs:
                    label = "HH" if pt["price"] > prev_highs[-1]["price"] else "LH"
                else:
                    label = "HH"
            else:
                prev_lows = [p for p in swing_points[:idx] if p["type"] == "low"]
                if prev_lows:
                    label = "LL" if pt["price"] < prev_lows[-1]["price"] else "HL"
                else:
                    label = "LL"
            labeled_swings.append({**pt, "label": label})

        # --- 3. Detect strict BOS ---
        bos_type = None
        bos_price = None
        bos_index = None
        # Look for the most recent BOS
        for idx in range(len(labeled_swings)-1, 0, -1):
            pt = labeled_swings[idx]
            if pt["label"] == "HH" and current_price > pt["price"]:
                bos_type = "bullish"
                bos_price = pt["price"]
                bos_index = pt["index"]
                break
            elif pt["label"] == "LL" and current_price < pt["price"]:
                bos_type = "bearish"
                bos_price = pt["price"]
                bos_index = pt["index"]
                break

        if not bos_type:
            print(f"[SMC] [INFO] No BOS detected")
            return self.format_smc_signal("HOLD", asset, current_price, None, None, expiration_time_minutes, lang_manager=lang_manager)

        # --- 4. Find order block using improved SMC logic ---
        order_block = None
        if bos_type == "bullish":
            # For bullish BOS, look for the last strong bearish move before the break
            # This creates a bullish order block (buyers waiting to enter)
            for i in range(bos_index-1, max(0, bos_index-20), -1):
                if i > 0 and i < len(prices) - 1:
                    current_price_ob = prices[i]
                    next_price_ob = prices[i + 1]
                    
                    # Look for a strong bearish move (price going down significantly)
                    if current_price_ob > next_price_ob:  # Bearish candle (price going down)
                        # Check if this is a significant move (at least 0.1% drop)
                        price_change = (current_price_ob - next_price_ob) / current_price_ob
                        if price_change > 0.001:  # 0.1% minimum move
                            # Find the range of this order block
                            ob_high = current_price_ob
                            ob_low = next_price_ob
                            
                            # Look for additional candles in the same direction
                            for j in range(i + 2, min(i + 5, len(prices))):
                                if j < len(prices):
                                    j_price = prices[j]
                                    if j_price < ob_low:
                                        ob_low = j_price
                                    elif j_price > ob_high:
                                        break
                            
                            order_block = {
                                "index": i,
                                "high": ob_high,
                                "low": ob_low,
                                "price": (ob_high + ob_low) / 2,
                                "type": "bullish_ob",
                                "zone": True
                            }
                            print(f"[SMC] [INFO] Found bullish order block zone: high={ob_high}, low={ob_low}")
                            break
                            
        elif bos_type == "bearish":
            # For bearish BOS, look for the last strong bullish move before the break
            # This creates a bearish order block (sellers waiting to enter)
            for i in range(bos_index-1, max(0, bos_index-20), -1):
                if i > 0 and i < len(prices) - 1:
                    current_price_ob = prices[i]
                    next_price_ob = prices[i + 1]
                    
                    # Look for a strong bullish move (price going up significantly)
                    if current_price_ob < next_price_ob:  # Bullish candle (price going up)
                        # Check if this is a significant move (at least 0.1% rise)
                        price_change = (next_price_ob - current_price_ob) / current_price_ob
                        if price_change > 0.001:  # 0.1% minimum move
                            # Find the range of this order block
                            ob_low = current_price_ob
                            ob_high = next_price_ob
                            
                            # Look for additional candles in the same direction
                            for j in range(i + 2, min(i + 5, len(prices))):
                                if j < len(prices):
                                    j_price = prices[j]
                                    if j_price > ob_high:
                                        ob_high = j_price
                                    elif j_price < ob_low:
                                        break
                            
                            order_block = {
                                "index": i,
                                "high": ob_high,
                                "low": ob_low,
                                "price": (ob_high + ob_low) / 2,
                                "type": "bearish_ob",
                                "zone": True
                            }
                            print(f"[SMC] [INFO] Found bearish order block zone: high={ob_high}, low={ob_low}")
                            break

        # --- 5. Detect Fair Value Gaps (FVG) ---
        fvg = self.detect_fair_value_gap(prices, timestamps)
        if fvg:
            print(f"[SMC] [INFO] Found FVG: {fvg}")

        # --- 6. Detect Liquidity Levels ---
        liquidity_levels = self.detect_liquidity_levels(prices, timestamps)
        if liquidity_levels:
            print(f"[SMC] [INFO] Found liquidity levels: {liquidity_levels}")

        if not order_block:
            print(f"[SMC] [INFO] No order block found")
            return self.format_smc_signal("HOLD", asset, current_price, None, bos_price, expiration_time_minutes, lang_manager=lang_manager)

        # --- 7. Wait for price to return to OB zone (use zone-based logic) ---
        tolerance = 0.003  # Increased to 0.3%
        
        # Use zone-based order block check if available
        if order_block.get("zone", False) and "high" in order_block and "low" in order_block:
            ob_high = order_block["high"]
            ob_low = order_block["low"]
            
            # Check if current price is within the order block zone
            if ob_low <= current_price <= ob_high:
                price_in_ob = True
                print(f"[SMC] [INFO] Price is within order block zone: current={current_price}, ob_range=[{ob_low}, {ob_high}]")
            else:
                # Check if price is near the zone boundaries with tolerance
                distance_to_zone = min(abs(current_price - ob_high), abs(current_price - ob_low))
                zone_size = ob_high - ob_low
                relative_distance = distance_to_zone / zone_size if zone_size > 0 else 0
                price_in_ob = relative_distance <= tolerance
                
                print(f"[SMC] [INFO] Price near order block zone: current={current_price}, ob_range=[{ob_low}, {ob_high}], distance={distance_to_zone:.6f}, relative={relative_distance:.6f}, tolerance={tolerance}")
        else:
            # Fallback to single price logic
            ob_price = order_block["price"]
            price_in_ob = abs(current_price - ob_price) / ob_price <= tolerance
            print(f"[SMC] [INFO] Using single price order block check: current={current_price}, ob_price={ob_price}")
        
        if not price_in_ob:
            ob_info = f"zone [{order_block.get('low', 'N/A')}, {order_block.get('high', 'N/A')}]" if order_block.get("zone", False) else f"price {order_block.get('price', 'N/A')}"
            print(f"[SMC] [INFO] Price not in order block area (current: {current_price}, OB: {ob_info})")
            return self.format_smc_signal("HOLD", asset, current_price, order_block.get("price"), bos_price, expiration_time_minutes, lang_manager=lang_manager)

        # --- 8. Relaxed confirmation for bullish SMC ---
        confirmation = False
        if len(prices) >= 3:
            if bos_type == "bullish":
                # Relaxed: allow upward momentum or a single bullish candle
                if prices[-1] > prices[-2] or prices[-1] > prices[-3]:
                    confirmation = True
            elif bos_type == "bearish":
                if prices[-1] < prices[-2] and prices[-2] < prices[-3]:
                    confirmation = True
        if confirmation:
            signal_type = "BUY" if bos_type == "bullish" else "SELL"
            print(f"[SMC] [INFO] SMC {signal_type} signal confirmed!")
            return self.format_smc_signal(signal_type, asset, current_price, order_block.get("price"), bos_price, expiration_time_minutes, lang_manager=lang_manager)
        else:
            print(f"[SMC] [INFO] No confirmation for SMC signal")
            return self.format_smc_signal("HOLD", asset, current_price, order_block.get("price"), bos_price, expiration_time_minutes, lang_manager=lang_manager)

    def detect_fair_value_gap(self, prices, timestamps):
        """Detect Fair Value Gaps (FVG) in price data"""
        fvgs = []
        for i in range(1, len(prices) - 1):
            # Bullish FVG: gap between high of previous candle and low of next candle
            if prices[i-1] < prices[i+1]:  # Gap exists
                gap_high = prices[i-1]  # High of previous candle
                gap_low = prices[i+1]   # Low of next candle
                
                # Check if gap is significant (at least 0.05%)
                gap_size = (gap_high - gap_low) / gap_low
                if gap_size > 0.0005:
                    fvgs.append({
                        "type": "bullish",
                        "index": i,
                        "high": gap_high,
                        "low": gap_low,
                        "size": gap_size,
                        "timestamp": timestamps[i] if i < len(timestamps) else None
                    })
        
        return fvgs[0] if fvgs else None  # Return first FVG found

    def detect_liquidity_levels(self, prices, timestamps):
        """Detect potential liquidity levels (equal highs/lows)"""
        liquidity_levels = []
        
        # Look for equal highs (potential resistance)
        for i in range(1, len(prices) - 1):
            if abs(prices[i] - prices[i-1]) < 0.0001:  # Equal within 0.01%
                liquidity_levels.append({
                    "type": "resistance",
                    "price": prices[i],
                    "index": i,
                    "timestamp": timestamps[i] if i < len(timestamps) else None
                })
        
        # Look for equal lows (potential support)
        for i in range(1, len(prices) - 1):
            if abs(prices[i] - prices[i-1]) < 0.0001:  # Equal within 0.01%
                liquidity_levels.append({
                    "type": "support",
                    "price": prices[i],
                    "index": i,
                    "timestamp": timestamps[i] if i < len(timestamps) else None
                })
        
        return liquidity_levels[:3] if liquidity_levels else None  # Return first 3 levels

    def calculate_macd(self, history_data, fast=12, slow=26, signal=9):
        """Calculate MACD signal for enhanced standard mode"""
        try:
            if len(history_data) < slow:
                return None
            
            # Extract prices
            prices = [float(point[1]) for point in history_data]
            
            # Calculate EMAs
            def ema(data, period):
                alpha = 2 / (period + 1)
                ema_values = [data[0]]
                for price in data[1:]:
                    ema_values.append(alpha * price + (1 - alpha) * ema_values[-1])
                return ema_values
            
            ema_fast = ema(prices, fast)
            ema_slow = ema(prices, slow)
            
            # Calculate MACD line
            macd_line = [fast_val - slow_val for fast_val, slow_val in zip(ema_fast, ema_slow)]
            
            # Calculate signal line
            signal_line = ema(macd_line, signal)
            
            # Get current values
            current_macd = macd_line[-1]
            current_signal = signal_line[-1]
            prev_macd = macd_line[-2] if len(macd_line) > 1 else current_macd
            prev_signal = signal_line[-2] if len(signal_line) > 1 else current_signal
            
            # Determine signal
            if current_macd > current_signal and prev_macd <= prev_signal:
                return "bullish"  # MACD crossed above signal line
            elif current_macd < current_signal and prev_macd >= prev_signal:
                return "bearish"  # MACD crossed below signal line
            else:
                return "neutral"
                
        except Exception as e:
            print(f"[ERROR] MACD calculation failed: {e}")
            return None

    def calculate_bollinger_bands(self, history_data, period=20, std_dev=2):
        """Calculate Bollinger Bands signal for enhanced standard mode"""
        try:
            if len(history_data) < period:
                return None
            
            # Extract prices
            prices = [float(point[1]) for point in history_data]
            current_price = prices[-1]
            
            # Calculate SMA
            sma = sum(prices[-period:]) / period
            
            # Calculate standard deviation
            variance = sum((price - sma) ** 2 for price in prices[-period:]) / period
            std = variance ** 0.5
            
            # Calculate bands
            upper_band = sma + (std_dev * std)
            lower_band = sma - (std_dev * std)
            
            # Determine signal
            if current_price <= lower_band:
                return "oversold"  # Price at or below lower band
            elif current_price >= upper_band:
                return "overbought"  # Price at or above upper band
            else:
                return "neutral"  # Price within bands
                
        except Exception as e:
            print(f"[ERROR] Bollinger Bands calculation failed: {e}")
            return None

    def calculate_moving_averages(self, history_data, short_period=10, long_period=20):
        """Calculate Moving Averages signal for enhanced standard mode"""
        try:
            if len(history_data) < long_period:
                return None
            
            # Extract prices
            prices = [float(point[1]) for point in history_data]
            
            # Calculate SMAs
            short_sma = sum(prices[-short_period:]) / short_period
            long_sma = sum(prices[-long_period:]) / long_period
            
            # Get previous values for trend detection
            if len(prices) >= long_period + 1:
                prev_short_sma = sum(prices[-(short_period+1):-1]) / short_period
                prev_long_sma = sum(prices[-(long_period+1):-1]) / long_period
                
                # Determine signal based on crossover
                if short_sma > long_sma and prev_short_sma <= prev_long_sma:
                    return "bullish"  # Golden cross
                elif short_sma < long_sma and prev_short_sma >= prev_long_sma:
                    return "bearish"  # Death cross
                else:
                    return "neutral"  # No crossover
            else:
                # Simple comparison if not enough data for crossover
                if short_sma > long_sma:
                    return "bullish"
                elif short_sma < long_sma:
                    return "bearish"
                else:
                    return "neutral"
                    
        except Exception as e:
            print(f"[ERROR] Moving Averages calculation failed: {e}")
            return None
