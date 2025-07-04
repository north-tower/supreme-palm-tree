from Analysis import HistorySummary
import pandas as pd


class SignalGenerator(HistorySummary):
    def is_support_zone(self, price, support_levels, tolerance=0.001):
        for level in support_levels:
            if abs(price - level) < tolerance:
                return True
        return False

    def is_resistance_zone(self, price, resistance_levels, tolerance=0.001):
        for level in resistance_levels:
            if abs(price - level) < tolerance:
                return True
        return False

    def detect_market_structure(self, candles):
        # Placeholder: implement real pivot logic for HH/HL/LL/LH
        closes = [c['close'] for c in candles]
        if len(closes) < 3:
            return "range"
        if closes[-1] > closes[-2] > closes[-3]:
            return "bullish"
        elif closes[-1] < closes[-2] < closes[-3]:
            return "bearish"
        else:
            return "range"

    def detect_candlestick_pattern(self, candle, prev_candle):
        # Bullish Engulfing
        if (
            prev_candle['close'] < prev_candle['open'] and  # previous bearish
            candle['close'] > candle['open'] and            # current bullish
            candle['open'] <= prev_candle['close'] and
            candle['close'] >= prev_candle['open']
        ):
            return "bullish_engulfing"
        # Bearish Engulfing
        if (
            prev_candle['close'] > prev_candle['open'] and  # previous bullish
            candle['close'] < candle['open'] and            # current bearish
            candle['open'] >= prev_candle['close'] and
            candle['close'] <= prev_candle['open']
        ):
            return "bearish_engulfing"
        # Pin Bar (unchanged)
        if abs(candle['close'] - candle['open']) < (candle['high'] - candle['low']) * 0.2:
            return "pin_bar"
        return None

    def generate_signal(self):
        try:
            indicators = self.get_all_indicators()
            if not indicators or self.history_df is None or len(self.history_df) < 10:
                return "No data to analyze."
            price = self.history_df["Value"].iloc[-1]
            if pd.isna(price):
                return "Invalid price data."
            candles = self.history_df.tail(10).to_dict('records')
            support_levels = []
            resistance_levels = []
            # Try to get support/resistance from indicators
            sr = indicators["Indicators"].get("Support and Resistance")
            if sr:
                if 'Support' in sr:
                    support_levels.append(sr['Support'])
                if 'Resistance' in sr:
                    resistance_levels.append(sr['Resistance'])
            # Fallback: use min/max of recent closes
            closes = [c['close'] for c in candles]
            support_levels.append(min(closes))
            resistance_levels.append(max(closes))
            # Market structure
            structure = self.detect_market_structure(candles)
            # Candlestick pattern
            if len(candles) < 2:
                return "Not enough candle data."
            last_candle = candles[-1]
            prev_candle = candles[-2]
            pattern = self.detect_candlestick_pattern(last_candle, prev_candle)
            # RSI
            rsi = indicators["Indicators"].get("RSI")
            # BUY logic
            if self.is_support_zone(price, support_levels) and structure == "bullish" and pattern in ["bullish_engulfing", "pin_bar"] and rsi is not None and rsi < 30:
                return "BUY"
            # SELL logic
            if self.is_resistance_zone(price, resistance_levels) and structure == "bearish" and pattern in ["bearish_engulfing", "pin_bar"] and rsi is not None and rsi > 70:
                return "SELL"
            return "HOLD"
        except Exception as e:
            print(f"Error generating signal: {e}")
            return "Error"
