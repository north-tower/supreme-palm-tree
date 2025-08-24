#!/usr/bin/env python3
"""
Test script to verify order block detection fixes
"""

import pandas as pd
import numpy as np
from SignalGenerator import SignalGenerator

def create_test_data():
    """Create test data with known order block patterns"""
    # Create a dataset that should have clear order blocks
    timestamps = pd.date_range('2024-01-01', periods=50, freq='1min')
    
    # Create a price series with a clear bullish order block pattern
    # Price goes down (bearish move), then breaks up (bullish BOS)
    prices = []
    
    # Start at 100
    current_price = 100.0
    
    # First 10 candles: sideways movement
    for i in range(10):
        prices.append(current_price + np.random.uniform(-0.1, 0.1))
        current_price = prices[-1]
    
    # Next 5 candles: strong bearish move (this should be the order block)
    for i in range(5):
        prices.append(current_price - np.random.uniform(0.2, 0.5))
        current_price = prices[-1]
    
    # Next 5 candles: consolidation around the low
    for i in range(5):
        prices.append(current_price + np.random.uniform(-0.1, 0.1))
        current_price = prices[-1]
    
    # Next 10 candles: strong bullish move (break of structure)
    for i in range(10):
        prices.append(current_price + np.random.uniform(0.3, 0.8))
        current_price = prices[-1]
    
    # Remaining candles: continuation
    for i in range(20):
        prices.append(current_price + np.random.uniform(-0.1, 0.3))
        current_price = prices[-1]
    
    # Create DataFrame
    df = pd.DataFrame({
        'Timestamp': timestamps,
        'Value': prices
    })
    
    return df

def test_order_block_detection():
    """Test the order block detection logic"""
    print("🧪 Testing Order Block Detection Fixes")
    print("=" * 50)
    
    # Create test data
    test_df = create_test_data()
    print(f"📊 Created test data with {len(test_df)} candles")
    print(f"📈 Price range: {test_df['Value'].min():.4f} - {test_df['Value'].max():.4f}")
    
    # Create signal generator
    sg = SignalGenerator()
    
    # Test BOS detection
    print("\n🔍 Testing Break of Structure Detection")
    swing_highs, swing_lows = sg.detect_swing_points(test_df, lookback=5)
    print(f"📊 Swing points detected: {len(swing_highs)} highs, {len(swing_lows)} lows")
    
    current_price = test_df['Value'].iloc[-1]
    bos_type, bos_price = sg.detect_break_of_structure(swing_highs, swing_lows, current_price)
    print(f"🎯 BOS detected: {bos_type} at {bos_price}")
    
    if bos_type and bos_price:
        # Test order block detection
        print("\n🔍 Testing Order Block Detection")
        order_block = sg.find_order_block(test_df, bos_type, bos_price, lookback=20)
        
        if order_block:
            print(f"✅ Order block found:")
            print(f"   Type: {order_block['type']}")
            print(f"   Index: {order_block['index']}")
            print(f"   Price (mid): {order_block['price']:.4f}")
            
            if order_block.get('zone', False):
                print(f"   Zone: {order_block['low']:.4f} - {order_block['high']:.4f}")
                print(f"   Zone size: {order_block['high'] - order_block['low']:.4f}")
            
            # Test if current price is in order block
            in_ob = sg.is_price_in_order_block(current_price, order_block, tolerance=0.005)
            print(f"   Current price in OB: {in_ob}")
            
        else:
            print("❌ No order block found")
    else:
        print("❌ No BOS detected - cannot test order block detection")
    
    # Test SMC signal generation
    print("\n🔍 Testing SMC Signal Generation")
    try:
        smc_signal = sg.generate_smc_pure_signal("TEST", test_df.values.tolist(), 5)
        print(f"📊 SMC Signal: {smc_signal}")
    except Exception as e:
        print(f"❌ Error generating SMC signal: {e}")
    
    print("\n✅ Order Block Detection Test Complete")

if __name__ == "__main__":
    test_order_block_detection()






