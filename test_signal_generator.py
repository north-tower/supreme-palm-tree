import pytest
import pandas as pd
from SignalGenerator import SignalGenerator

# Helper to create dummy candle data

def make_candles(prices, bullish=True):
    candles = []
    for i, price in enumerate(prices):
        if bullish:
            candles.append({
                'open': price - 0.5,
                'close': price + 0.5,
                'high': price + 1,
                'low': price - 1,
            })
        else:
            candles.append({
                'open': price + 0.5,
                'close': price - 0.5,
                'high': price + 1,
                'low': price - 1,
            })
    return candles

def make_history_df(prices, bullish=True):
    candles = make_candles(prices, bullish)
    df = pd.DataFrame(candles)
    df['Value'] = df['close']
    return df

def test_not_enough_data():
    sg = SignalGenerator([])
    sg.history_df = pd.DataFrame()
    assert sg.generate_signal() == "No data to analyze."

def test_invalid_price_data():
    sg = SignalGenerator([])
    df = pd.DataFrame([{'open': 1, 'close': float('nan'), 'high': 2, 'low': 0, 'Value': float('nan')} for _ in range(10)])
    sg.history_df = df
    assert sg.generate_signal() == "Invalid price data."

def test_is_support_zone():
    sg = SignalGenerator([])
    assert sg.is_support_zone(10, [9.999, 10.001], tolerance=0.01)
    assert not sg.is_support_zone(10, [11, 12], tolerance=0.01)

def test_is_resistance_zone():
    sg = SignalGenerator([])
    assert sg.is_resistance_zone(20, [19.999, 20.001], tolerance=0.01)
    assert not sg.is_resistance_zone(20, [21, 22], tolerance=0.01)

def test_detect_market_structure_bullish():
    sg = SignalGenerator([])
    candles = make_candles([10, 11, 12])
    assert sg.detect_market_structure(candles) == "bullish"

def test_detect_market_structure_bearish():
    sg = SignalGenerator([])
    candles = make_candles([12, 11, 10])
    assert sg.detect_market_structure(candles) == "bearish"

def test_detect_market_structure_range():
    sg = SignalGenerator([])
    candles = make_candles([10, 12, 11])
    assert sg.detect_market_structure(candles) == "range"

def test_detect_candlestick_pattern_bullish_engulfing():
    sg = SignalGenerator([])
    prev = {'open': 10, 'close': 9, 'high': 10.5, 'low': 8.5}
    curr = {'open': 9, 'close': 11, 'high': 11.5, 'low': 8.5}
    assert sg.detect_candlestick_pattern(curr, prev) == "bullish_engulfing"

def test_detect_candlestick_pattern_bearish_engulfing():
    sg = SignalGenerator([])
    prev = {'open': 9, 'close': 11, 'high': 11.5, 'low': 8.5}
    curr = {'open': 11, 'close': 9, 'high': 11.5, 'low': 8.5}
    assert sg.detect_candlestick_pattern(curr, prev) == "bearish_engulfing"

def test_detect_candlestick_pattern_pin_bar():
    sg = SignalGenerator([])
    prev = {'open': 10, 'close': 10, 'high': 11, 'low': 9}
    curr = {'open': 10, 'close': 10.1, 'high': 11, 'low': 9}
    assert sg.detect_candlestick_pattern(curr, prev) == "pin_bar"

def test_detect_candlestick_pattern_none():
    sg = SignalGenerator([])
    prev = {'open': 10, 'close': 10, 'high': 11, 'low': 9}
    curr = {'open': 10, 'close': 11, 'high': 11, 'low': 10}
    assert sg.detect_candlestick_pattern(curr, prev) is None

def test_generate_signal_buy():
    prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    sg = SignalGenerator([])
    sg.history_df = make_history_df(prices)
    sg.get_all_indicators = lambda: {"Indicators": {"RSI": 25, "Support and Resistance": {"Support": 19}}}
    assert sg.generate_signal() == "BUY"

def test_generate_signal_sell():
    prices = [20, 19, 18, 17, 16, 15, 14, 13, 12, 11]
    sg = SignalGenerator([])
    sg.history_df = make_history_df(prices, bullish=False)
    sg.get_all_indicators = lambda: {"Indicators": {"RSI": 75, "Support and Resistance": {"Resistance": 11}}}
    assert sg.generate_signal() == "SELL"

def test_generate_signal_hold():
    prices = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
    sg = SignalGenerator([])
    sg.history_df = make_history_df(prices)
    sg.get_all_indicators = lambda: {"Indicators": {"RSI": 50}}
    assert sg.generate_signal() == "HOLD" 