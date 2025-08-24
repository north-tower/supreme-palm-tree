#!/usr/bin/env python3
"""
Test script to verify main modules can be imported without syntax errors
"""

try:
    print("🔄 Testing Helpers import...")
    from Helpers import *
    print("✅ Helpers imported successfully!")
    
    print("🔄 Testing SignalGenerator import...")
    from SignalGenerator import SignalGenerator
    print("✅ SignalGenerator imported successfully!")
    
    print("🔄 Testing demo_test import...")
    from demo_test import fetch_summary
    print("✅ demo_test imported successfully!")
    
    print("🔄 Testing main import...")
    import main
    print("✅ main imported successfully!")
    
    print("\n🎉 All imports successful! The syntax errors have been fixed.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")





