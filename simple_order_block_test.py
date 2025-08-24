#!/usr/bin/env python3
"""
Simple test script to verify order block detection fixes
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_simple_test_data():
    """Create simple test data with clear order block patterns"""
    # Create timestamps
    timestamps = [datetime.now() - timedelta(minutes=i) for i in range(30, 0, -1)]
    
    # Create price data with a clear bullish order block pattern
    prices = []
    
    # Start at 100
    current_price = 100.0
    
    # First 10 candles: sideways movement
    for i in range(10):
        prices.append(current_price + np.random.uniform(-0.05, 0.05))
        current_price = prices[-1]
    
    # Next 5 candles: strong bearish move (this should be the order block)
    for i in range(5):
        prices.append(current_price - np.random.uniform(0.1, 0.3))
        current_price = prices[-1]
    
    # Next 5 candles: consolidation around the low
    for i in range(5):
        prices.append(current_price + np.random.uniform(-0.05, 0.05))
        current_price = prices[-1]
    
    # Next 10 candles: strong bullish move (break of structure)
    for i in range(10):
        prices.append(current_price + np.random.uniform(0.2, 0.5))
        current_price = prices[-1]
    
    # Create DataFrame
    df = pd.DataFrame({
        'Timestamp': timestamps,
        'Value': prices
    })
    
    return df

def test_order_block_logic():
    """Test the order block detection logic manually"""
    print("🧪 Testing Order Block Detection Logic")
    print("=" * 50)
    
    # Create test data
    test_df = create_simple_test_data()
    print(f"📊 Created test data with {len(test_df)} candles")
    print(f"📈 Price range: {test_df['Value'].min():.4f} - {test_df['Value'].max():.4f}")
    
    # Print the price pattern
    print("\n📊 Price Pattern Analysis:")
    print("Candles 1-10: Sideways movement")
    print("Candles 11-15: Strong bearish move (Order Block)")
    print("Candles 16-20: Consolidation")
    print("Candles 21-30: Strong bullish move (Break of Structure)")
    
    # Analyze the order block area manually
    ob_start = 10  # Index where bearish move starts
    ob_end = 15    # Index where bearish move ends
    
    ob_high = test_df['Value'].iloc[ob_start]
    ob_low = test_df['Value'].iloc[ob_end]
    
    print(f"\n🔍 Manual Order Block Analysis:")
    print(f"Order Block High: {ob_high:.4f}")
    print(f"Order Block Low: {ob_low:.4f}")
    print(f"Order Block Zone Size: {ob_high - ob_low:.4f}")
    print(f"Zone Percentage: {((ob_high - ob_low) / ob_low * 100):.2f}%")
    
    # Check if current price is in the order block zone
    current_price = test_df['Value'].iloc[-1]
    in_zone = ob_low <= current_price <= ob_high
    
    print(f"\n🎯 Current Price Analysis:")
    print(f"Current Price: {current_price:.4f}")
    print(f"Price in Order Block Zone: {in_zone}")
    
    if in_zone:
        print("✅ Current price is within the order block zone - this is correct!")
    else:
        print("❌ Current price is outside the order block zone")
        # Calculate distance to zone
        if current_price > ob_high:
            distance = current_price - ob_high
            print(f"Price is {distance:.4f} above the order block zone")
        else:
            distance = ob_low - current_price
            print(f"Price is {distance:.4f} below the order block zone")
    
    # Test the zone-based logic
    print(f"\n🧮 Zone-Based Logic Test:")
    print(f"Zone boundaries: [{ob_low:.4f}, {ob_high:.4f}]")
    print(f"Current price: {current_price:.4f}")
    
    # Check if price is near the zone with tolerance
    tolerance = 0.003  # 0.3%
    
    if ob_low <= current_price <= ob_high:
        print("✅ Price is directly within the zone")
    else:
        # Calculate relative distance to zone
        distance_to_zone = min(abs(current_price - ob_high), abs(current_price - ob_low))
        zone_size = ob_high - ob_low
        relative_distance = distance_to_zone / zone_size if zone_size > 0 else 0
        
        print(f"Distance to zone: {distance_to_zone:.6f}")
        print(f"Relative distance: {relative_distance:.6f}")
        print(f"Tolerance: {tolerance}")
        
        if relative_distance <= tolerance:
            print("✅ Price is near the zone (within tolerance)")
        else:
            print("❌ Price is not near the zone")
    
    print("\n✅ Order Block Logic Test Complete")

if __name__ == "__main__":
    test_order_block_logic()
