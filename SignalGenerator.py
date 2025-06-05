from Analysis import HistorySummary


class SignalGenerator(HistorySummary):
    def generate_signal(self):
        try:
            indicators = self.get_all_indicators()

            if not indicators:
                return "No data to analyze."

            # Get individual indicators
            rsi = indicators["Indicators"].get("RSI")
            macd = indicators["Indicators"].get("MACD")
            bollinger = indicators["Indicators"].get("Bollinger Bands")
            stochastic = indicators["Indicators"].get("Stochastic Oscillator")
            support_resistance = indicators["Indicators"].get("Support and Resistance")

            # Initialize signal weights
            buy_signals = 0
            sell_signals = 0

            # RSI analysis
            if rsi:
                if rsi < 30:
                    buy_signals += 1
                elif rsi > 70:
                    sell_signals += 1

            # MACD analysis
            if macd:
                if macd["MACD"] > macd["Signal"]:
                    buy_signals += 1
                elif macd["MACD"] < macd["Signal"]:
                    sell_signals += 1

            # Bollinger Bands analysis
            if bollinger:
                last_value = self.history_df["Value"].iloc[-1]
                if last_value <= bollinger["Lower Band"]:
                    buy_signals += 1
                elif last_value >= bollinger["Upper Band"]:
                    sell_signals += 1

            # Stochastic Oscillator analysis
            if stochastic:
                if stochastic["%K"] < 20 and stochastic["%K"] > stochastic["%D"]:
                    buy_signals += 1
                elif stochastic["%K"] > 80 and stochastic["%K"] < stochastic["%D"]:
                    sell_signals += 1

            # Support and Resistance analysis
            if support_resistance:
                last_value = self.history_df["Value"].iloc[-1]
                if last_value <= support_resistance["Support"]:
                    buy_signals += 1
                elif last_value >= support_resistance["Resistance"]:
                    sell_signals += 1

            # Final Signal
            if buy_signals > sell_signals:
                return "BUY"
            elif sell_signals > buy_signals:
                return "SELL"
            else:
                return "HOLD"
        except Exception as e:
            print(f"Error generating signal: {e}")
            return "Error"
