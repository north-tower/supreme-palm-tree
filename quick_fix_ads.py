#!/usr/bin/env python3
"""
Quick fix for casino ads - run this immediately
"""

import os
import re
import subprocess

def quick_check():
    """Quick check for common ad sources"""
    print("🚀 Quick ad source check...")
    
    # Check .bashrc
    bashrc_path = os.path.expanduser("~/.bashrc")
    if os.path.exists(bashrc_path):
        with open(bashrc_path, 'r') as f:
            content = f.read()
        
        suspicious_patterns = [
            'Jetacas', 'casino', 'bonus', 'promo', '$1000', 
            'WELCOME1K', 'jetacas.com', 'online casino'
        ]
        
        found_suspicious = False
        for pattern in suspicious_patterns:
            if pattern.lower() in content.lower():
                print(f"❌ Found suspicious content: {pattern}")
                found_suspicious = True
        
        if found_suspicious:
            print(f"\n🔧 Creating backup and cleaning {bashrc_path}...")
            
            # Create backup
            backup_path = f"{bashrc_path}.backup"
            with open(backup_path, 'w') as f:
                f.write(content)
            print(f"✅ Backup created: {backup_path}")
            
            # Clean content
            clean_content = content
            for pattern in suspicious_patterns:
                clean_content = re.sub(pattern, '', clean_content, flags=re.IGNORECASE)
            
            with open(bashrc_path, 'w') as f:
                f.write(clean_content)
            print(f"✅ {bashrc_path} cleaned")
            
            print("\n💡 You may need to restart your terminal or run: source ~/.bashrc")
        else:
            print("✅ .bashrc looks clean")
    
    # Check .profile
    profile_path = os.path.expanduser("~/.profile")
    if os.path.exists(profile_path):
        with open(profile_path, 'r') as f:
            content = f.read()
        
        if any(pattern.lower() in content.lower() for pattern in ['Jetacas', 'casino', 'bonus']):
            print(f"❌ Found suspicious content in {profile_path}")
            print("🔧 Please check this file manually")
        else:
            print("✅ .profile looks clean")
    
    # Check for suspicious aliases
    try:
        result = subprocess.run(['alias'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            aliases = result.stdout
            if any(pattern.lower() in aliases.lower() for pattern in ['Jetacas', 'casino', 'bonus']):
                print("❌ Found suspicious aliases")
                print("🔧 Run 'unalias' to remove them")
            else:
                print("✅ No suspicious aliases found")
    except:
        print("⚠️ Could not check aliases")
    
    # Check for suspicious functions
    try:
        result = subprocess.run(['declare', '-f'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            functions = result.stdout
            if any(pattern.lower() in functions.lower() for pattern in ['Jetacas', 'casino', 'bonus']):
                print("❌ Found suspicious functions")
                print("🔧 Check your shell configuration files")
            else:
                print("✅ No suspicious functions found")
    except:
        print("⚠️ Could not check functions")

def immediate_fixes():
    """Apply immediate fixes"""
    print("\n🛡️ Applying immediate fixes...")
    
    # Remove any suspicious aliases
    try:
        subprocess.run(['unalias', 'Jetacas'], shell=True, stderr=subprocess.DEVNULL)
        subprocess.run(['unalias', 'casino'], shell=True, stderr=subprocess.DEVNULL)
        subprocess.run(['unalias', 'bonus'], shell=True, stderr=subprocess.DEVNULL)
        print("✅ Removed suspicious aliases")
    except:
        pass
    
    # Check if we need to restart shell
    print("\n💡 If ads persist, try these steps:")
    print("1. Close all terminal windows")
    print("2. Open a new terminal")
    print("3. Run: source ~/.bashrc")
    print("4. If still showing ads, run the full ad_blocker.py script")

if __name__ == "__main__":
    print("🛡️ Quick Casino Ad Fix")
    print("=" * 30)
    
    quick_check()
    immediate_fixes()
    
    print("\n✅ Quick fix complete!")
    print("🔍 For comprehensive scanning, run: python ad_blocker.py")
