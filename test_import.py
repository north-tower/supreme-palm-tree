#!/usr/bin/env python3
"""
Simple test to verify SignalGenerator can be imported
"""

try:
    print("🔄 Testing SignalGenerator import...")
    from SignalGenerator import SignalGenerator
    print("✅ SignalGenerator imported successfully!")
    
    # Test basic instantiation
    print("🔄 Testing SignalGenerator instantiation...")
    sg = SignalGenerator()
    print("✅ SignalGenerator instantiated successfully!")
    
    print("\n🎉 All tests passed! The syntax errors have been fixed.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")





