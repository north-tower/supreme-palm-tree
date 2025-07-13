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
            order_block = self.find_order_block(history_df, bos_type, bos_price, lookback=10)
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
            
            # Step 12: Traditional TA Signal conditions (more flexible)
            # Check if this is a flat market
            unique_prices = set(history_df["Value"].unique())
            is_flat_market = len(unique_prices) == 1
            
            if is_flat_market:
                print(f"[DEBUG] Flat market detected - using flexible conditions")
                # For flat markets, use more flexible conditions
                threshold = 1  # Only need 1 out of 4 conditions (very flexible)
                buy_rsi_condition = rsi is not None and rsi < 70  # Very flexible RSI
                sell_rsi_condition = rsi is not None and rsi > 30  # Very flexible RSI
            else:
                # Normal market conditions - more flexible
                threshold = 2  # Need 2 out of 4 conditions (more flexible)
                buy_rsi_condition = rsi is not None and rsi < 50  # More flexible RSI
                sell_rsi_condition = rsi is not None and rsi > 50  # More flexible RSI
            
            # BUY Signal conditions
            buy_conditions = [
                self.is_support_zone(current_price, support_levels),
                structure in ["bullish", "neutral"],  # Allow neutral structure
                pattern in ["bullish_engulfing", "pin_bar"],
                buy_rsi_condition
            ]
            buy_score = sum(buy_conditions)
            
            # SELL Signal conditions
            sell_conditions = [
                self.is_resistance_zone(current_price, resistance_levels),
                structure in ["bearish", "neutral"],  # Allow neutral structure
                pattern in ["bearish_engulfing", "pin_bar"],
                sell_rsi_condition
            ]
            sell_score = sum(sell_conditions)
            
            print(f"[DEBUG] Traditional TA Signal scores - BUY: {buy_score}/{threshold}, SELL: {sell_score}/{threshold}")
            print(f"[DEBUG] Buy conditions: {buy_conditions}")
            print(f"[DEBUG] Sell conditions: {sell_conditions}")
            
            # Generate signals based on scores
            if buy_score >= threshold:
                zone_price = support_levels[0] if support_levels else None
                print(f"[DEBUG] BUY signal generated (score: {buy_score}/{threshold})")
                # Force SMC format for traditional TA signals
                return self.format_smc_signal("BUY", asset, current_price, zone_price, 
                                            zone_price, expiration_time_minutes, lang_manager=lang_manager)  # Use zone_price as BOS price
            
            elif sell_score >= threshold:
                zone_price = resistance_levels[0] if resistance_levels else None
                print(f"[DEBUG] SELL signal generated (score: {sell_score}/{threshold})")
                # Force SMC format for traditional TA signals
                return self.format_smc_signal("SELL", asset, current_price, zone_price, 
                                            zone_price, expiration_time_minutes, lang_manager=lang_manager)  # Use zone_price as BOS price
            
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
            print(f"[DEBUG] HOLD signal - insufficient conditions (BUY: {buy_score}/{threshold}, SELL: {sell_score}/{threshold})")
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
    
    def find_order_block(self, history_df, bos_type, bos_price, lookback=10):
        """Find Order Block based on BOS direction"""
        try:
            if not bos_type or not bos_price:
                print(f"[DEBUG] No BOS information available for order block detection")
                return None
            
            if history_df is None or len(history_df) < lookback + 1:
                print(f"[DEBUG] Insufficient data for order block detection")
                return None
            
            # Use a more flexible lookback for smaller datasets
            actual_lookback = min(lookback, len(history_df) - 1)
            if actual_lookback < 3:
                actual_lookback = 3
            
            print(f"[DEBUG] Looking for order block with lookback {actual_lookback}")
            
            # Find the last opposite candle before BOS
            order_block = None
            
            for i in range(len(history_df) - actual_lookback, len(history_df) - 1):
                current_price = history_df["Value"].iloc[i]
                next_price = history_df["Value"].iloc[i + 1]
                
                # Skip invalid prices
                if current_price <= 0 or next_price <= 0 or math.isnan(current_price) or math.isnan(next_price):
                    continue
                
                if bos_type == "bullish":
                    # For bullish BOS, look for bearish candle before the break
                    if current_price < next_price:  # Bearish candle (price going down)
                        order_block = {
                            "index": i,
                            "price": current_price,
                            "type": "bullish_ob",
                            "timestamp": history_df["Timestamp"].iloc[i]
                        }
                        print(f"[DEBUG] Found bullish order block at price {current_price}")
                        break
                
                elif bos_type == "bearish":
                    # For bearish BOS, look for bullish candle before the break
                    if current_price > next_price:  # Bullish candle (price going up)
                        order_block = {
                            "index": i,
                            "price": current_price,
                            "type": "bearish_ob",
                            "timestamp": history_df["Timestamp"].iloc[i]
                        }
                        print(f"[DEBUG] Found bearish order block at price {current_price}")
                        break
            
            if order_block:
                print(f"[DEBUG] Order block found: {order_block['type']} at {order_block['price']}")
            else:
                print(f"[DEBUG] No order block found")
            
            return order_block
            
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
            
            ob_price = order_block["price"]
            if ob_price <= 0 or math.isnan(ob_price):
                return False
            
            price_diff = abs(current_price - ob_price) / ob_price
            
            print(f"[DEBUG] Order block check: current={current_price}, ob_price={ob_price}, diff={price_diff:.6f}, tolerance={tolerance}")
            
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

        # --- 4. Find order block (last opposite candle before BOS) ---
        order_block = None
        if bos_type == "bullish":
            # Find last bearish candle before BOS
            for i in range(bos_index-1, 0, -1):
                if prices[i] < prices[i-1]:  # Bearish candle
                    order_block = {"index": i, "price": prices[i], "type": "bullish_ob"}
                    break
        elif bos_type == "bearish":
            # Find last bullish candle before BOS
            for i in range(bos_index-1, 0, -1):
                if prices[i] > prices[i-1]:  # Bullish candle
                    order_block = {"index": i, "price": prices[i], "type": "bearish_ob"}
                    break

        if not order_block:
            print(f"[SMC] [INFO] No order block found")
            return self.format_smc_signal("HOLD", asset, current_price, None, bos_price, expiration_time_minutes, lang_manager=lang_manager)

        # --- 5. Wait for price to return to OB ---
        tolerance = 0.0015  # 0.15%
        ob_price = order_block["price"]
        price_in_ob = abs(current_price - ob_price) / ob_price <= tolerance
        if not price_in_ob:
            print(f"[SMC] [INFO] Price not in order block area (current: {current_price}, OB: {ob_price})")
            return self.format_smc_signal("HOLD", asset, current_price, ob_price, bos_price, expiration_time_minutes, lang_manager=lang_manager)

        # --- 6. Confirmation (engulfing or RSI) ---
        # Simple confirmation: check if last candle is engulfing or RSI is in the right zone
        # For now, use price momentum as a proxy for engulfing
        confirmation = False
        if len(prices) >= 3:
            if bos_type == "bullish" and prices[-1] > prices[-2] > prices[-3]:
                confirmation = True
            elif bos_type == "bearish" and prices[-1] < prices[-2] < prices[-3]:
                confirmation = True
        # Optionally, add RSI confirmation if you have indicator data
        # (for now, skip RSI for pure SMC)

        if confirmation:
            signal_type = "BUY" if bos_type == "bullish" else "SELL"
            print(f"[SMC] [INFO] SMC {signal_type} signal confirmed!")
            return self.format_smc_signal(signal_type, asset, current_price, ob_price, bos_price, expiration_time_minutes, lang_manager=lang_manager)
        else:
            print(f"[SMC] [INFO] No confirmation for SMC signal")
            return self.format_smc_signal("HOLD", asset, current_price, ob_price, bos_price, expiration_time_minutes, lang_manager=lang_manager)
