from Analysis import HistorySummary


class SignalGenerator:
    def __init__(self, history_data, time_minutes=3):
        self.history_summary = HistorySummary(history_data, time_minutes)
        self.indicators = self.history_summary.calculate_indicators()

    def generate_signal(self, lang='en'):
        """Generate trading signal based on technical indicators"""
        try:
            # Get support and resistance levels
            support_resistance = self.indicators.get('Support and Resistance', {})
            support = support_resistance.get('Support')
            resistance = support_resistance.get('Resistance')
            
            if support is None or resistance is None:
                # Try to get alternate support/resistance levels
                support, resistance = self.history_summary.get_alternate_support_resistance(self.indicators)
            
            # Get current price
            current_price = self.history_summary.history_df["Value"].iloc[-1]
            
            # Determine signal based on price position
            if current_price > resistance:
                signal = "🟥 SELL" if lang == 'en' else "🟥 ПРОДАТЬ" if lang == 'ru' else "🟥 VENDER"
            elif current_price < support:
                signal = "🟩 BUY" if lang == 'en' else "🟩 КУПИТЬ" if lang == 'ru' else "🟩 COMPRAR"
            else:
                signal = "⚪ WAIT" if lang == 'en' else "⚪ ЖДАТЬ" if lang == 'ru' else "⚪ ESPERAR"
            
            return {
                'signal': signal,
                'support': support,
                'resistance': resistance,
                'current_price': current_price
            }
            
        except Exception as e:
            print(f"Error generating signal: {e}")
            return None
