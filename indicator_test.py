import pandas as pd
import numpy as np

def calculate_indicators(history_data, expiration_time):
    try:
       
        if expiration_time not in [1, 3, 5, 15]:
            raise ValueError("Invalid expiration time. Supported values are 1, 3, 5, and 15 minutes.")

        # Convert history_data to a DataFrame
        df = pd.DataFrame(history_data)
        if 'Timestamp' not in df.columns or 'Value' not in df.columns:
            raise ValueError("Each dictionary in history_data must contain 'Timestamp' and 'Value' keys.")
        
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
        df.set_index('Timestamp', inplace=True)

        # Resample based on expiration time
        if expiration_time == 1:
            df_resampled = df.resample('15s').last()
        elif expiration_time == 3:
            df_resampled = df.resample('30s').last()
        elif expiration_time == 5:
            df_resampled = df.resample('1T').last()
        elif expiration_time == 15:
            df_resampled = df.resample('3T').last()

        df_resampled.dropna(inplace=True)

        if df_resampled.empty:
            raise ValueError("Resampled data is empty. Please provide sufficient historical data.")

        # Calculate indicators
        indicators = {}

        # CCI (Commodity Channel Index)
        try:
            typical_price = df_resampled['Value']
            moving_avg = typical_price.rolling(window=14).mean()
            mean_deviation = typical_price.rolling(window=14).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
            cci = (typical_price - moving_avg) / (0.015 * mean_deviation)
            indicators['CCI'] = cci.iloc[-1] if not cci.empty else None
        except Exception as e:
            indicators['CCI'] = None

        # RSI (Relative Strength Index)
        try:
            delta = df_resampled['Value'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            indicators['RSI'] = rsi.iloc[-1] if not rsi.empty else None
        except Exception as e:
            indicators['RSI'] = None

        # Stochastic Oscillator
        try:
            low_14 = df_resampled['Value'].rolling(window=14).min()
            high_14 = df_resampled['Value'].rolling(window=14).max()
            stochastic = 100 * ((df_resampled['Value'] - low_14) / (high_14 - low_14))
            indicators['Stochastic Oscillator'] = stochastic.iloc[-1] if not stochastic.empty else None
        except Exception as e:
            indicators['Stochastic Oscillator'] = None

        # ADX (Average Directional Index)
        try:
            high = df_resampled['Value']
            low = df_resampled['Value']
            close = df_resampled['Value']

            plus_dm = high.diff()
            minus_dm = low.diff()
            tr = np.maximum((high - low), np.maximum(abs(high - close.shift()), abs(low - close.shift())))
            tr_smooth = tr.rolling(window=14).mean()
            plus_di = 100 * (plus_dm.where(plus_dm > minus_dm, 0)).rolling(window=14).sum() / tr_smooth
            minus_di = 100 * (minus_dm.where(minus_dm > plus_dm, 0)).rolling(window=14).sum() / tr_smooth
            dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
            adx = dx.rolling(window=14).mean()
            indicators['ADX'] = adx.iloc[-1] if not adx.empty else None
        except Exception as e:
            indicators['ADX'] = None

        # Bullish/Bearish Strength
        try:
            bullish_bearish_strength = (df_resampled['Value'].diff().sum() / len(df_resampled)) if len(df_resampled) > 0 else 0
            indicators['Bullish/Bearish Strength'] = bullish_bearish_strength
        except Exception as e:
            indicators['Bullish/Bearish Strength'] = None

        # Generate trading signal
        def generate_signal(indicators):
            if indicators['RSI'] is not None and indicators['RSI'] > 70:
                return "Sell Signal: RSI indicates overbought conditions."
            elif indicators['RSI'] is not None and indicators['RSI'] < 30:
                return "Buy Signal: RSI indicates oversold conditions."
            elif indicators['CCI'] is not None and indicators['CCI'] > 100:
                return "Buy Signal: CCI indicates strong bullish conditions."
            elif indicators['CCI'] is not None and indicators['CCI'] < -100:
                return "Sell Signal: CCI indicates strong bearish conditions."
            else:
                return "No clear signal."

        signal = generate_signal(indicators)

        # Format the message
        message = (f"\n\U0001F48E GPT 4.5 CCI: {indicators['CCI']:.2f}" if indicators['CCI'] is not None else "\n\U0001F48E GPT 4.5 CCI: N/A")
        message += (f"\n\U0001F48E GPT 4.5 RSI: {indicators['RSI']:.2f}" if indicators['RSI'] is not None else "\n\U0001F48E GPT 4.5 RSI: N/A")
        message += (f"\n\U0001F48E AI Stochastic Oscillator: {indicators['Stochastic Oscillator']:.2f}" if indicators['Stochastic Oscillator'] is not None else "\n\U0001F48E AI Stochastic Oscillator: N/A")
        message += (f"\n\U0001F48E GPT 4.5 ADX: {indicators['ADX']:.2f}" if indicators['ADX'] is not None else "\n\U0001F48E GPT 4.5 ADX: N/A")
        message += (f"\n\U0001F402 Bullish/Bearish Strength: {indicators['Bullish/Bearish Strength']:.2f}" if indicators['Bullish/Bearish Strength'] is not None else "\n\U0001F402 Bullish/Bearish Strength: N/A")
        message += f"\nSignal: {signal}"

        return message

    except Exception as e:
        return f"Error: {str(e)}"

