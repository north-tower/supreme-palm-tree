#!/bin/bash

echo "🔍 Scanning for potential ad sources..."

echo -e "\n📋 Checking shell configuration files..."
echo "=== ~/.bashrc ==="
if [ -f ~/.bashrc ]; then
    grep -n "Jetacas\|casino\|bonus\|promo" ~/.bashrc 2>/dev/null || echo "No suspicious content found"
else
    echo "~/.bashrc not found"
fi

echo -e "\n=== ~/.bash_profile ==="
if [ -f ~/.bash_profile ]; then
    grep -n "Jetacas\|casino\|bonus\|promo" ~/.bash_profile 2>/dev/null || echo "No suspicious content found"
else
    echo "~/.bash_profile not found"
fi

echo -e "\n=== ~/.profile ==="
if [ -f ~/.profile ]; then
    grep -n "Jetacas\|casino\|bonus\|promo" ~/.profile 2>/dev/null || echo "No suspicious content found"
else
    echo "~/.profile not found"
fi

echo -e "\n📋 Checking for suspicious processes..."
ps aux | grep -i "casino\|jetacas\|bonus\|promo" | grep -v grep || echo "No suspicious processes found"

echo -e "\n📋 Checking cron jobs..."
echo "=== User cron jobs ==="
crontab -l 2>/dev/null | grep -i "casino\|jetacas\|bonus\|promo" || echo "No suspicious cron jobs found"

echo -e "\n=== System cron jobs ==="
sudo crontab -l 2>/dev/null | grep -i "casino\|jetacas\|bonus\|promo" || echo "No suspicious system cron jobs found"

echo -e "\n📋 Checking system message files..."
echo "=== /etc/motd ==="
if [ -f /etc/motd ]; then
    grep -i "casino\|jetacas\|bonus\|promo" /etc/motd 2>/dev/null || echo "No suspicious content found"
else
    echo "/etc/motd not found"
fi

echo -e "\n=== /etc/issue ==="
if [ -f /etc/issue ]; then
    grep -i "casino\|jetacas\|bonus\|promo" /etc/issue 2>/dev/null || echo "No suspicious content found"
else
    echo "/etc/issue not found"
fi

echo -e "\n📋 Checking for suspicious aliases..."
alias | grep -i "casino\|jetacas\|bonus\|promo" || echo "No suspicious aliases found"

echo -e "\n📋 Checking for suspicious functions..."
declare -f | grep -A 10 -B 10 "casino\|jetacas\|bonus\|promo" || echo "No suspicious functions found"

echo -e "\n📋 Checking for suspicious environment variables..."
env | grep -i "casino\|jetacas\|bonus\|promo" || echo "No suspicious environment variables found"

echo -e "\n✅ Scan complete!"
echo -e "\n💡 If suspicious content is found, you can:"
echo "1. Remove it from the respective files"
echo "2. Comment out suspicious lines"
echo "3. Rename suspicious files to .bak extension"
echo "4. Check for malware using: sudo apt install clamav && sudo freshclam && sudo clamscan -r /home/$USER"
