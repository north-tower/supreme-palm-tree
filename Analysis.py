import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import random

class HistorySummary:
    def __init__(self, history_data, time_minutes=3):
        self.history_df = pd.DataFrame(history_data, columns=["Timestamp", "Value"])
        self.time_minutes = time_minutes
     

    def filter_recent_data(self):
        try:
            if not self.history_df.empty:
                self.history_df["Timestamp"] = pd.to_datetime(self.history_df["Timestamp"], unit='s')
                end_time = self.history_df["Timestamp"].max()
                start_time = end_time - pd.Timedelta(minutes=self.time_minutes)
                self.history_df = self.history_df[self.history_df["Timestamp"] >= start_time]
        except Exception as e:
            print(f"Error filtering recent data: {e}")
    def get_summary(self):
            try:
                self.filter_recent_data()

                if self.history_df.empty:
                
                    return {
                        "Open": None,
                        "High": None,
                        "Low": None,
                        "Close": None,
                        "Volume": 0,
                        "Start Time": None,
                        "End Time": None,
                        "Top Value Time": None,
                        "Bottom Value Time": None,
                    }

                # Summary calculations
                open_value = self.history_df["Value"].iloc[0]
                high_value = self.history_df["Value"].max()
                low_value = self.history_df["Value"].min()
                close_value = self.history_df["Value"].iloc[-1]
                volume = len(self.history_df)  # Number of data points

                # Time calculations
                start_time = self.history_df["Timestamp"].iloc[0]
                end_time = self.history_df["Timestamp"].iloc[-1]
                top_value_time = self.history_df.loc[self.history_df["Value"].idxmax(), "Timestamp"]
                bottom_value_time = self.history_df.loc[self.history_df["Value"].idxmin(), "Timestamp"]

                return {
                    "Open": open_value,
                    "High": high_value,
                    "Low": low_value,
                    "Close": close_value,
                    "Volume": volume,
                    "Start Time": start_time,
                    "End Time": end_time,
                    "Top Value Time": top_value_time,
                    "Bottom Value Time": bottom_value_time,
                }
            except Exception as e:
                print(f"Error getting summary: {e}")
                return {
                    "Open": None,
                    "High": None,
                    "Low": None,
                    "Close": None,
                    "Volume": 0,
                    "Start Time": None,
                    "End Time": None,
                    "Top Value Time": None,
                    "Bottom Value Time": None,
                    "error": str(e)
                }

    def calculate_rsi(self, periods=14):
        try:
            self.filter_recent_data()

            if self.history_df.empty or len(self.history_df) < periods:
                return None

            # Check if all prices are the same (flat market)
            unique_prices = self.history_df["Value"].unique()
            if len(unique_prices) == 1:
                # Flat market - return neutral RSI (50)
                print(f"[DEBUG] Flat market detected - returning neutral RSI (50)")
                return 50.0

            self.history_df["Change"] = self.history_df["Value"].diff()
            self.history_df["Gain"] = self.history_df["Change"].apply(lambda x: x if x > 0 else 0)
            self.history_df["Loss"] = self.history_df["Change"].apply(lambda x: -x if x < 0 else 0)

            avg_gain = self.history_df["Gain"].rolling(window=periods, min_periods=periods).mean()
            avg_loss = self.history_df["Loss"].rolling(window=periods, min_periods=periods).mean()

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            self.history_df["RSI"] = rsi

            return self.history_df["RSI"].iloc[-1] if not self.history_df["RSI"].isnull().all() else None
        except Exception as e:
            print(f"Error calculating RSI: {e}")
            return {"error": str(e)}

    def calculate_ema(self, span):
        try:
            self.filter_recent_data()

            if self.history_df.empty or len(self.history_df) < span:
                return None

            self.history_df["EMA"] = self.history_df["Value"].ewm(span=span, adjust=False).mean()
            return self.history_df["EMA"].iloc[-1] if not self.history_df["EMA"].isnull().all() else None
        except Exception as e:
            print(f"Error calculating EMA: {e}")
            return {"error": str(e)}

    def calculate_bullish_bearish_strength(self):
        try:
            self.filter_recent_data()

            if self.history_df.empty:
                return None

            # Calculate the difference between the high and low values in the selected timeframe
            high_value = self.history_df["Value"].max()
            low_value = self.history_df["Value"].min()
            close_value = self.history_df["Value"].iloc[-1]
            
            # Bullish/Bearish Strength Calculation
            # Positive strength indicates bullish, negative indicates bearish
            strength = (close_value - low_value) / (high_value - low_value) if high_value != low_value else 0

            return round(strength, 2)  # Round to two decimal places
        except Exception as e:
            print(f"Error calculating Bullish/Bearish Strength: {e}")
            return {"error": str(e)}

    def calculate_macd(self, short_span=12, long_span=26, signal_span=9):
        try:
            self.filter_recent_data()

            if self.history_df.empty or len(self.history_df) < long_span:
                return None

            short_ema = self.history_df["Value"].ewm(span=short_span, adjust=False).mean()
            long_ema = self.history_df["Value"].ewm(span=long_span, adjust=False).mean()

            self.history_df["MACD"] = short_ema - long_ema
            self.history_df["Signal"] = self.history_df["MACD"].ewm(span=signal_span, adjust=False).mean()

            macd_value = self.history_df["MACD"].iloc[-1]
            signal_value = self.history_df["Signal"].iloc[-1]

            return {
                "MACD": macd_value,
                "Signal": signal_value
            }
        except Exception as e:
            print(f"Error calculating MACD: {e}")
            return {"error": str(e)}

    def calculate_bollinger_bands(self, periods=20, k=2):
        try:
            self.filter_recent_data()

            if self.history_df.empty or len(self.history_df) < periods:
                return None

            self.history_df["SMA"] = self.history_df["Value"].rolling(window=periods).mean()
            self.history_df["STD_DEV"] = self.history_df["Value"].rolling(window=periods).std()

            self.history_df["Upper Band"] = self.history_df["SMA"] + (k * self.history_df["STD_DEV"])
            self.history_df["Lower Band"] = self.history_df["SMA"] - (k * self.history_df["STD_DEV"])

            return {
                "Upper Band": self.history_df["Upper Band"].iloc[-1],
                "Lower Band": self.history_df["Lower Band"].iloc[-1],
                "Middle Band": self.history_df["SMA"].iloc[-1]
            }
        except Exception as e:
            print(f"Error calculating Bollinger Bands: {e}")
            return {"error": str(e)}

    def calculate_stochastic_oscillator(self, periods=14):
        try:
            self.filter_recent_data()

            if self.history_df.empty or len(self.history_df) < periods:
                return None

            self.history_df["Lowest Low"] = self.history_df["Value"].rolling(window=periods).min()
            self.history_df["Highest High"] = self.history_df["Value"].rolling(window=periods).max()

            self.history_df["%K"] = ((self.history_df["Value"] - self.history_df["Lowest Low"]) / \
                                     (self.history_df["Highest High"] - self.history_df["Lowest Low"])) * 100

            self.history_df["%D"] = self.history_df["%K"].rolling(window=3).mean()

            return {
                "%K": self.history_df["%K"].iloc[-1],
                "%D": self.history_df["%D"].iloc[-1]
            }
        except Exception as e:
            print(f"Error calculating Stochastic Oscillator: {e}")
            return {"error": str(e)}

    def calculate_support_resistance(self):
        try:
            self.filter_recent_data()

            if self.history_df.empty:
                return None

            # Check if all prices are the same (flat market)
            unique_prices = self.history_df["Value"].unique()
            if len(unique_prices) == 1:
                # Flat market - create artificial levels around the current price
                current_price = unique_prices[0]
                price_range = current_price * 0.001  # 0.1% range
                support = current_price - price_range
                resistance = current_price + price_range
                print(f"[DEBUG] Flat market detected - creating artificial levels around {current_price}")
            else:
                # Normal market with price variation
                support = self.history_df["Value"][self.history_df["Value"] < self.history_df["Value"].shift(1)].min()
                resistance = self.history_df["Value"][self.history_df["Value"] > self.history_df["Value"].shift(1)].max()
                
                # If no support/resistance found, use min/max of the data
                if pd.isna(support):
                    support = self.history_df["Value"].min()
                if pd.isna(resistance):
                    resistance = self.history_df["Value"].max()

            return {
                "Support": support,
                "Resistance": resistance
            }
        except Exception as e:
            print(f"Error calculating Support and Resistance: {e}")
            return {"error": str(e)}

    def calculate_keltner_channels(self, periods=20, multiplier=2):
        try:
            self.filter_recent_data()

            if self.history_df.empty or len(self.history_df) < periods:
                return None

            self.history_df["EMA"] = self.history_df["Value"].ewm(span=periods, adjust=False).mean()
            self.history_df["True Range"] = self.history_df["Value"].diff().abs()
            self.history_df["ATR"] = self.history_df["True Range"].rolling(window=periods).mean()

            self.history_df["Upper Band"] = self.history_df["EMA"] + (self.history_df["ATR"] * multiplier)
            self.history_df["Lower Band"] = self.history_df["EMA"] - (self.history_df["ATR"] * multiplier)

            return {
                "Upper Band": self.history_df["Upper Band"].iloc[-1],
                "Lower Band": self.history_df["Lower Band"].iloc[-1],
                "Middle Line": self.history_df["EMA"].iloc[-1]
            }
        except Exception as e:
            print(f"Error calculating Keltner Channels: {e}")
            return {"error": str(e)}

    def calculate_parabolic_sar(self, af_start=0.02, af_increment=0.02, af_max=0.2):
        try:
            self.filter_recent_data()

            if self.history_df.empty or len(self.history_df) < 2:
                return None

            psar = []
            af = af_start
            ep = self.history_df["Value"].iloc[0]
            prev_psar = self.history_df["Value"].iloc[0]
            uptrend = True

            for i in range(1, len(self.history_df)):
                high = self.history_df["Value"].iloc[i]
                low = self.history_df["Value"].iloc[i]

                if uptrend:
                    psar.append(prev_psar + af * (ep - prev_psar))
                    if high > ep:
                        ep = high
                        af = min(af + af_increment, af_max)
                    if low < psar[-1]:
                        uptrend = False
                        ep = low
                        af = af_start
                else:
                    psar.append(prev_psar + af * (ep - prev_psar))
                    if low < ep:
                        ep = low
                        af = min(af + af_increment, af_max)
                    if high > psar[-1]:
                        uptrend = True
                        ep = high
                        af = af_start

                prev_psar = psar[-1]

            return psar[-1]
        except Exception as e:
            print(f"Error calculating Parabolic SAR: {e}")
            return {"error": str(e)}

    def calculate_fibonacci_retracement(self):
        try:
            self.filter_recent_data()

            if self.history_df.empty:
                return None

            high = self.history_df["Value"].max()
            low = self.history_df["Value"].min()
            diff = high - low

            retracements = {
                "0%": high,
                "23.6%": high - (0.236 * diff),
                "38.2%": high - (0.382 * diff),
                "50%": high - (0.5 * diff),
                "61.8%": high - (0.618 * diff),
                "100%": low
            }

            return retracements
        except Exception as e:
            print(f"Error calculating Fibonacci Retracement: {e}")
            return {"error": str(e)}

    def get_all_indicators(self):
        try:
            summary = self.get_summary()

            indicators = {
                "RSI": self.calculate_rsi(),
                "EMA": self.calculate_ema(span=14),
                "MACD": self.calculate_macd(),
                "Bollinger Bands": self.calculate_bollinger_bands(),
                "Stochastic Oscillator": self.calculate_stochastic_oscillator(),
                "Support and Resistance": self.calculate_support_resistance(),
                "Keltner Channels": self.calculate_keltner_channels(),
                "Parabolic SAR": self.calculate_parabolic_sar(),
                "Fibonacci Retracement": self.calculate_fibonacci_retracement()
            }

            return {
                "Summary": summary,
                "Indicators": indicators
            }
        except Exception as e:
            print(f"Error getting all indicators: {e}")
            return {"Summary": {"error": str(e)}, "Indicators": {"error": str(e)}}
        
    def generate_signal(self, currency_pair, expiration_time):
        try:
            self.filter_recent_data()
            print("[INFO] Recent data filtered successfully.")

            # Fetch all indicators
            indicators_data = self.get_all_indicators().get("Indicators", {})
            print(f"[INFO] Retrieved indicators: {indicators_data}")

            # Initialize signal and variables
            signal = "❌ НЕТ СИГНАЛА"
            support_level = None
            resistance_level = None
            used_indicators = []

            # Sequentially check indicators
            def process_rsi():
                rsi = indicators_data.get("RSI", None)
                if isinstance(rsi, (int, float)):
                    if rsi > 70:
                        return "🟩 КУПИТЬ", f"RSI: {rsi} → Перекуплен (Сигнал на покупку)"
                    elif rsi < 50:
                        return "🟥 ПРОДАТЬ", f"RSI: {rsi} → Перепродан (Сигнал на продажу)"
                return None, None

            def process_ema():
                ema = indicators_data.get("EMA", None)
                if isinstance(ema, (int, float)):
                    if ema > 0:
                        return "🟩 КУПИТЬ", f"EMA: {ema} → Положительная тенденция (Сигнал на покупку)"
                    elif ema < 0:
                        return "🟥 ПРОДАТЬ", f"EMA: {ema} → Отрицательная тенденция (Сигнал на продажу)"
                return None, None

            def process_macd():
                macd_data = indicators_data.get("MACD", None)
                if macd_data:
                    macd_line, signal_line = macd_data
                    if isinstance(macd_line, (int, float)) and isinstance(signal_line, (int, float)):
                        if macd_line > signal_line:
                            return "🟩 КУПИТЬ", f"MACD: {macd_line} > {signal_line} → Бычи (Сигнал на покупку)"
                        elif macd_line < signal_line:
                            return "🟥 ПРОДАТЬ", f"MACD: {macd_line} < {signal_line} → Медвежий (Сигнал на продажу)"
                return None, None

            def process_bollinger():
                bollinger = indicators_data.get("Bollinger Bands", None)
                if bollinger:
                    lower_band, upper_band = bollinger
                    if isinstance(lower_band, (int, float)) and isinstance(upper_band, (int, float)):
                        if lower_band < 0:
                            return "🟩 КУПИТЬ", f"Bollinger Bands: Lower: {lower_band}, Upper: {upper_band} → Прорыв волатильности (Сигнал на покупку)"
                        elif upper_band > 0:
                            return "🟥 ПРОДАТЬ", f"Bollinger Bands: Lower: {lower_band}, Upper: {upper_band} → Сопротивление цены (Сигнал на продажу)"
                return None, None

            def process_stochastic():
                stochastic = indicators_data.get("Stochastic Oscillator", None)
                if isinstance(stochastic, (int, float)):
                    if stochastic > 80:
                        return "🟥 ПРОДАТЬ", f"Stochastic Oscillator: {stochastic} → Перекуплен (Сигнал на продажу)"
                    elif stochastic < 20:
                        return "🟩 КУПИТЬ", f"Stochastic Oscillator: {stochastic} → Перепродан (Сигнал на покупку)"
                return None, None

            # List of processing functions
            processing_functions = [
                process_rsi,
                process_ema,
                process_macd,
                process_bollinger,
                process_stochastic
            ]

            # Iterate over processing functions
            for process_function in processing_functions:
                signal_result, description = process_function()
                if signal_result:
                    signal = signal_result
                    used_indicators.append(description)
                    break  # Stop checking further indicators if a signal is found

           
            support_level, resistance_level = self.get_alternate_support_resistance(indicators_data)

            # Prepare result
            result = f"""📊🔮 *Ваш магический сигнал готов!* 🔮📊  
            - 💹 **Сигнал:** {signal}  
            - 📈 **Уровень поддержки:** {support_level or 'N/A'} 🔻  
            - 📉 **Уровень сопротивления:** {resistance_level or 'N/A'} 🔺  

            ✨💡 *Магия рынка на вашей стороне! Удачных сделок!* ✨  

            🔁 Нажмите кнопку ниже, чтобы получить новый сигнал! 🔁
            """
            print(f"[INFO] Final result prepared: {result}")
            return result

        except Exception as e:
            print(f"[ERROR] Critical error in generate_signal: {e}")
            return {"error": str(e)}



    def get_alternate_support_resistance(self, indicators_data):
        """
        Dynamically calculate support and resistance levels from available indicators.
        If no valid values are found, generate random levels.
        :param indicators_data: Dictionary containing the calculated indicators
        :return: A tuple with support and resistance levels (support, resistance)
        """
        indicator_order = [
            "Support and Resistance",  # Direct levels
            "Fibonacci Retracement",  # Derived levels
            "Bollinger Bands",        # Price channels
            "Keltner Channels",       # Price channels
            "Parabolic SAR",          # Trend-based levels
            "EMA",                    # Dynamic levels
            "MACD",                   # Directional hints
            "RSI",                    # Overbought/Oversold zones
            "Stochastic Oscillator"   # Overbought/Oversold zones
        ]
        
        # Loop through each indicator and try to extract support and resistance
        for indicator in indicator_order:
            print(f"Checking indicator: {indicator}")
            indicator_data = indicators_data.get(indicator)
            
            if indicator_data:
                print(f"Data found for {indicator}: {indicator_data}")
                # Extract support and resistance from indicators
                if indicator in ["Support and Resistance", "Parabolic SAR"]:
                    support = indicator_data.get("Support")
                    resistance = indicator_data.get("Resistance")
                    print(f"Extracted support and resistance from {indicator}: Support = {support}, Resistance = {resistance}")
                    if support is not None and resistance is not None:
                        print("[INFO] Successfully retrieved alternate Support and Resistance levels.")
                        print(f"[DEBUG] Alternate Support Level: {support}, Alternate Resistance Level: {resistance}")
                        return support, resistance
                
                elif indicator == "Fibonacci Retracement":
                    support = indicator_data.get("support")
                    resistance = indicator_data.get("resistance")
                    print(f"Extracted support and resistance from {indicator}: Support = {support}, Resistance = {resistance}")
                    if support is not None and resistance is not None:
                        print("[INFO] Successfully retrieved alternate Support and Resistance levels.")
                        print(f"[DEBUG] Alternate Support Level: {support}, Alternate Resistance Level: {resistance}")
                        return support, resistance
                
                elif indicator in ["Bollinger Bands", "Keltner Channels"]:
                    support = indicator_data.get("lower_band")
                    resistance = indicator_data.get("upper_band")
                    print(f"Extracted support and resistance from {indicator}: Lower Band = {support}, Upper Band = {resistance}")
                    if support is not None and resistance is not None:
                        print("[INFO] Successfully retrieved alternate Support and Resistance levels.")
                        print(f"[DEBUG] Alternate Support Level: {support}, Alternate Resistance Level: {resistance}")
                        return support, resistance
                
                elif indicator == "EMA":
                    ema = indicator_data
                    print(f"Extracted EMA value: {ema}")
                    if ema is not None:
                        support = ema - random.uniform(5, 15)  # Dynamically adjust around EMA
                        resistance = ema + random.uniform(5, 15)
                        print(f"Generated support and resistance around EMA: Support = {support}, Resistance = {resistance}")
                        print("[INFO] Successfully retrieved alternate Support and Resistance levels.")
                        print(f"[DEBUG] Alternate Support Level: {support}, Alternate Resistance Level: {resistance}")
                        return support, resistance
                
                elif indicator == "MACD":
                    macd = indicator_data
                    print(f"Extracted MACD values: {macd}")
                    if macd:
                        support = min(macd)
                        resistance = max(macd)
                        print(f"Generated support and resistance from MACD: Support = {support}, Resistance = {resistance}")
                        print("[INFO] Successfully retrieved alternate Support and Resistance levels.")
                        print(f"[DEBUG] Alternate Support Level: {support}, Alternate Resistance Level: {resistance}")
                        return support, resistance
            else:
                print(f"No data found for {indicator}")
        
        # If no valid support/resistance found, generate random values
        print("No valid support/resistance found in any indicator. Generating random levels.")
        random_support = random.uniform(100, 120)  # Logical random range
        random_resistance = random.uniform(random_support + 5, random_support + 20)  # Ensure support < resistance
        print(f"Generated random support: {round(random_support, 2)}, random resistance: {round(random_resistance, 2)}")
        print("[INFO] Successfully generated fallback Support and Resistance levels.")
        print(f"[DEBUG] Fallback Support Level: {round(random_support, 2)}, Fallback Resistance Level: {round(random_resistance, 2)}")
        
        return round(random_support, 2), round(random_resistance, 2)

    # Example of helper methods to determine the trend based on indicator value

    def rsi_trend(self, rsi):
        try:
            if rsi is None:
                print("RSI value is None. Returning 'N/A'.")
                return 'N/A'
            elif rsi > 60:
                print(f"RSI value {rsi} is greater than 60. Indicating 'Overbought'.")
                return 'Overbought'
            elif rsi < 30:
                print(f"RSI value {rsi} is less than 30. Indicating 'Oversold'.")
                return 'Oversold'
            else:
                print(f"RSI value {rsi} is between 30 and 60. Indicating 'Neutral'.")
                return 'Neutral'
        except Exception as e:
            print(f"Error processing RSI: {e}")
            return 'Error'

    def macd_trend(self, macd_line, signal_line):
        try:
            if macd_line is None or signal_line is None:
                print("MACD or Signal Line value is None. Returning 'N/A'.")
                return 'N/A'
            elif macd_line > signal_line:
                print(f"MACD Line ({macd_line}) is greater than Signal Line ({signal_line}). Indicating 'Bullish'.")
                return 'Bullish'
            elif macd_line < signal_line:
                print(f"MACD Line ({macd_line}) is less than Signal Line ({signal_line}). Indicating 'Bearish'.")
                return 'Bearish'
            else:
                print(f"MACD Line ({macd_line}) is equal to Signal Line ({signal_line}). Indicating 'Neutral'.")
                return 'Neutral'
        except Exception as e:
            print(f"Error processing MACD: {e}")
            return 'Error'

    def bullish_bearish_trend(self, strength):
        try:
            if strength is None:
                print("Bullish/Bearish Strength is None. Returning 'N/A'.")
                return 'N/A'
            elif strength > 0:
                print(f"Bullish/Bearish Strength ({strength}) is greater than 0. Indicating 'Bullish'.")
                return 'Bullish'
            elif strength < 0:
                print(f"Bullish/Bearish Strength ({strength}) is less than 0. Indicating 'Bearish'.")
                return 'Bearish'
            else:
                print(f"Bullish/Bearish Strength is 0. Indicating 'Neutral'.")
                return 'Neutral'
        except Exception as e:
            print(f"Error processing Bullish/Bearish Strength: {e}")
            return 'Error'

    def ema_trend(self, ema_value):
        try:
            if ema_value > 0:
                print(f"EMA value ({ema_value}) is greater than 0. Indicating 'Bullish'.")
                return "Bullish - Price above EMA"
            elif ema_value < 0:
                print(f"EMA value ({ema_value}) is less than 0. Indicating 'Bearish'.")
                return "Bearish - Price below EMA"
            else:
                print(f"EMA value is 0. Indicating 'Neutral'.")
                return "Neutral - EMA is flat"
        except Exception as e:
            print(f"Error processing EMA: {e}")
            return 'Error'
    def bollinger_bands_trend(self, bollinger_data):
        try:
            # Ensure bollinger_data is a tuple or list of 3 elements
            if not isinstance(bollinger_data, (tuple, list)) or len(bollinger_data) != 3:
                print(f"Error: Invalid Bollinger Bands data: {bollinger_data}. Expected a tuple or list with 3 values.")
                return "N/A"
            
            upper_band, lower_band, middle_band = bollinger_data

            # Check if upper_band and lower_band are numbers (int or float)
            if not isinstance(upper_band, (int, float)) or not isinstance(lower_band, (int, float)):
                print(f"Error: Invalid data type for Bollinger Bands: upper_band={upper_band}, lower_band={lower_band}")
                return "N/A"

            if upper_band < 0:
                print(f"Upper Bollinger Band ({upper_band}) is less than 0. Indicating 'Price above upper band - Overbought'.")
                return "Price above upper band - Overbought"
            elif lower_band > 0:
                print(f"Lower Bollinger Band ({lower_band}) is greater than 0. Indicating 'Price below lower band - Oversold'.")
                return "Price below lower band - Oversold"
            else:
                print("Price is within Bollinger Bands. Indicating 'Normal range'.")
                return "Price within bands - Normal range"
        except Exception as e:
            print(f"Error processing Bollinger Bands: {e}")
            return 'N/A'

    def stochastic_oscillator_trend(self, stochastic_value):
        try:
            # Ensure the stochastic value is a number (int or float)
            if not isinstance(stochastic_value, (int, float)):
                print(f"Error: Invalid Stochastic Oscillator value: {stochastic_value}. Expected a number.")
                return "N/A"

            if stochastic_value > 80:
                print(f"Stochastic Oscillator value ({stochastic_value}) is greater than 80. Indicating 'Overbought'.")
                return "Overbought - Price might reverse downward"
            elif stochastic_value < 20:
                print(f"Stochastic Oscillator value ({stochastic_value}) is less than 20. Indicating 'Oversold'.")
                return "Oversold - Price might reverse upward"
            else:
                print(f"Stochastic Oscillator value ({stochastic_value}) is between 20 and 80. Indicating 'Neutral'.")
                return "Neutral - Normal price action"
        except Exception as e:
            print(f"Error processing Stochastic Oscillator: {e}")
            return "N/A"

    def support_resistance_trend(self, support_resistance):
        try:
            if support_resistance:
                print("Support and Resistance levels identified. Indicating 'Key levels identified - Possible price reversal zones'.")
                return "Key levels identified - Possible price reversal zones"
            else:
                print("No significant support or resistance levels identified. Indicating 'No significant levels identified'.")
                return "No significant levels identified"
        except Exception as e:
            print(f"Error processing Support and Resistance: {e}")
            return 'Error'

    def keltner_channels_trend(self, keltner_data):
        try:
            # Ensure keltner_data is a tuple or list of 3 elements
            if not isinstance(keltner_data, (tuple, list)) or len(keltner_data) != 3:
                print(f"Error: Invalid Keltner Channels data: {keltner_data}. Expected a tuple or list with 3 values.")
                return "N/A"
            
            upper, lower, middle = keltner_data

            # Check if upper and lower values are numbers (int or float)
            if not isinstance(upper, (int, float)) or not isinstance(lower, (int, float)):
                print(f"Error: Invalid data type for Keltner Channels: upper={upper}, lower={lower}")
                return "N/A"

            if upper < 0:
                print(f"Upper Keltner Channel ({upper}) is less than 0. Indicating 'Price above upper band - Overbought'.")
                return "Price above upper band - Overbought"
            elif lower > 0:
                print(f"Lower Keltner Channel ({lower}) is greater than 0. Indicating 'Price below lower band - Oversold'.")
                return "Price below lower band - Oversold"
            else:
                print("Price is within Keltner Channels. Indicating 'Normal volatility'.")
                return "Price within channels - Normal volatility"
        except Exception as e:
            print(f"Error processing Keltner Channels: {e}")
            return 'N/A'

    def parabolic_sar_trend(self, parabolic_sar):
        try:
            # Ensure parabolic_sar is a number (int or float)
            if not isinstance(parabolic_sar, (int, float)):
                print(f"Error: Invalid Parabolic SAR value: {parabolic_sar}. Expected a number.")
                return "N/A"

            if parabolic_sar > 0:
                print(f"Parabolic SAR value ({parabolic_sar}) is greater than 0. Indicating 'Bullish'.")
                return "Bullish - Possible upward trend"
            elif parabolic_sar < 0:
                print(f"Parabolic SAR value ({parabolic_sar}) is less than 0. Indicating 'Bearish'.")
                return "Bearish - Possible downward trend"
            else:
                print("Parabolic SAR value is 0. Indicating 'Neutral'.")
                return "Neutral - No trend detected"
        except Exception as e:
            print(f"Error processing Parabolic SAR: {e}")
            return 'N/A'


    def fibonacci_retracement_trend(self, fibonacci_data):
        try:
            # Ensure fibonacci_data is a valid boolean or valid data structure
            if not isinstance(fibonacci_data, bool) and not fibonacci_data:
                print(f"Error: Invalid Fibonacci Retracement data: {fibonacci_data}. Expected a valid data structure.")
                return "N/A"

            print("Fibonacci levels identified. Indicating 'Potential reversal points'.")
            return "Fibonacci levels identified - Potential reversal points"
        except Exception as e:
            print(f"Error processing Fibonacci Retracement: {e}")
            return 'N/A'