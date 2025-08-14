#!/usr/bin/env python3
"""
Ad Blocker and Security Monitor for Trading Bot
"""

import os
import re
import subprocess
import time
from pathlib import Path

class AdBlocker:
    def __init__(self):
        self.suspicious_patterns = [
            r'Jetacas',
            r'casino',
            r'bonus',
            r'promo',
            r'\$1000',
            r'WELCOME1K',
            r'jetacas\.com',
            r'online casino',
            r'launch bonus',
            r'no strings attached',
            r'no ID required',
            r'instant bonus'
        ]
        
        self.shell_files = [
            '~/.bashrc',
            '~/.bash_profile', 
            '~/.profile',
            '~/.zshrc',
            '~/.bash_aliases'
        ]
        
        self.system_files = [
            '/etc/motd',
            '/etc/issue',
            '/etc/issue.net'
        ]
    
    def scan_file(self, file_path):
        """Scan a file for suspicious content"""
        try:
            expanded_path = os.path.expanduser(file_path)
            if not os.path.exists(expanded_path):
                return None
            
            with open(expanded_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            suspicious_lines = []
            for i, line in enumerate(content.split('\n'), 1):
                for pattern in self.suspicious_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        suspicious_lines.append((i, line.strip(), pattern))
                        break
            
            return suspicious_lines if suspicious_lines else None
            
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
            return None
    
    def scan_shell_configs(self):
        """Scan shell configuration files"""
        print("🔍 Scanning shell configuration files...")
        found_suspicious = False
        
        for file_path in self.shell_files:
            suspicious = self.scan_file(file_path)
            if suspicious:
                found_suspicious = True
                print(f"\n❌ Suspicious content found in {file_path}:")
                for line_num, line_content, pattern in suspicious:
                    print(f"   Line {line_num}: {line_content}")
                    print(f"   Matches pattern: {pattern}")
        
        if not found_suspicious:
            print("✅ No suspicious content found in shell configs")
        
        return found_suspicious
    
    def scan_system_files(self):
        """Scan system message files"""
        print("\n🔍 Scanning system message files...")
        found_suspicious = False
        
        for file_path in self.system_files:
            suspicious = self.scan_file(file_path)
            if suspicious:
                found_suspicious = True
                print(f"\n❌ Suspicious content found in {file_path}:")
                for line_num, line_content, pattern in suspicious:
                    print(f"   Line {line_num}: {line_content}")
                    print(f"   Matches pattern: {pattern}")
        
        if not found_suspicious:
            print("✅ No suspicious content found in system files")
        
        return found_suspicious
    
    def check_processes(self):
        """Check for suspicious processes"""
        print("\n🔍 Checking for suspicious processes...")
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                suspicious_processes = []
                
                for line in lines:
                    for pattern in self.suspicious_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            suspicious_processes.append(line.strip())
                            break
                
                if suspicious_processes:
                    print("❌ Suspicious processes found:")
                    for proc in suspicious_processes:
                        print(f"   {proc}")
                else:
                    print("✅ No suspicious processes found")
                
                return bool(suspicious_processes)
            else:
                print("⚠️ Could not check processes")
                return False
                
        except Exception as e:
            print(f"Error checking processes: {e}")
            return False
    
    def check_cron_jobs(self):
        """Check for suspicious cron jobs"""
        print("\n🔍 Checking cron jobs...")
        found_suspicious = False
        
        try:
            # Check user cron jobs
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                cron_lines = result.stdout.split('\n')
                for line in cron_lines:
                    for pattern in self.suspicious_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            print(f"❌ Suspicious user cron job: {line}")
                            found_suspicious = True
                            break
            
            # Check system cron jobs
            result = subprocess.run(['sudo', 'crontab', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                cron_lines = result.stdout.split('\n')
                for line in cron_lines:
                    for pattern in self.suspicious_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            print(f"❌ Suspicious system cron job: {line}")
                            found_suspicious = True
                            break
            
            if not found_suspicious:
                print("✅ No suspicious cron jobs found")
                
        except Exception as e:
            print(f"Error checking cron jobs: {e}")
        
        return found_suspicious
    
    def create_clean_shell_config(self):
        """Create a clean shell configuration backup and replacement"""
        print("\n🛡️ Creating clean shell configuration...")
        
        for file_path in self.shell_files:
            expanded_path = os.path.expanduser(file_path)
            if os.path.exists(expanded_path):
                # Create backup
                backup_path = f"{expanded_path}.backup.{int(time.time())}"
                try:
                    with open(expanded_path, 'r') as f:
                        content = f.read()
                    
                    # Remove suspicious content
                    clean_content = content
                    for pattern in self.suspicious_patterns:
                        clean_content = re.sub(pattern, '', clean_content, flags=re.IGNORECASE)
                    
                    # Create backup
                    with open(backup_path, 'w') as f:
                        f.write(content)
                    
                    # Write clean content
                    with open(expanded_path, 'w') as f:
                        f.write(clean_content)
                    
                    print(f"✅ Cleaned {file_path} (backup: {backup_path})")
                    
                except Exception as e:
                    print(f"Error cleaning {file_path}: {e}")
    
    def monitor_terminal(self):
        """Monitor terminal for suspicious output"""
        print("\n👀 Starting terminal monitoring...")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                # Check for suspicious content in recent terminal output
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n✅ Monitoring stopped")
    
    def run_full_scan(self):
        """Run a full security scan"""
        print("🚀 Starting full security scan...")
        print("=" * 50)
        
        shell_suspicious = self.scan_shell_configs()
        system_suspicious = self.scan_system_files()
        process_suspicious = self.check_processes()
        cron_suspicious = self.check_cron_jobs()
        
        print("\n" + "=" * 50)
        print("📊 SCAN RESULTS:")
        print(f"Shell configs: {'❌ Suspicious' if shell_suspicious else '✅ Clean'}")
        print(f"System files: {'❌ Suspicious' if system_suspicious else '✅ Clean'}")
        print(f"Processes: {'❌ Suspicious' if process_suspicious else '✅ Clean'}")
        print(f"Cron jobs: {'❌ Suspicious' if cron_suspicious else '✅ Clean'}")
        
        if any([shell_suspicious, system_suspicious, process_suspicious, cron_suspicious]):
            print("\n⚠️ Suspicious content detected!")
            print("💡 Run create_clean_shell_config() to clean up")
        else:
            print("\n🎉 All systems clean!")
    
    def install_security_tools(self):
        """Install security tools to help prevent future infections"""
        print("\n🔧 Installing security tools...")
        
        try:
            # Install ClamAV for malware scanning
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run(['sudo', 'apt', 'install', '-y', 'clamav'], check=True)
            subprocess.run(['sudo', 'freshclam'], check=True)
            print("✅ ClamAV installed successfully")
            
            # Install fail2ban for SSH protection
            subprocess.run(['sudo', 'apt', 'install', '-y', 'fail2ban'], check=True)
            print("✅ Fail2ban installed successfully")
            
            # Install rkhunter for rootkit detection
            subprocess.run(['sudo', 'apt', 'install', '-y', 'rkhunter'], check=True)
            print("✅ Rkhunter installed successfully")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing security tools: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

def main():
    blocker = AdBlocker()
    
    print("🛡️ Ad Blocker and Security Monitor")
    print("=" * 40)
    
    while True:
        print("\n📋 Available actions:")
        print("1. Run full security scan")
        print("2. Scan shell configurations only")
        print("3. Scan system files only")
        print("4. Check processes")
        print("5. Check cron jobs")
        print("6. Clean shell configurations")
        print("7. Install security tools")
        print("8. Monitor terminal")
        print("9. Exit")
        
        choice = input("\nEnter your choice (1-9): ").strip()
        
        if choice == '1':
            blocker.run_full_scan()
        elif choice == '2':
            blocker.scan_shell_configs()
        elif choice == '3':
            blocker.scan_system_files()
        elif choice == '4':
            blocker.check_processes()
        elif choice == '5':
            blocker.check_cron_jobs()
        elif choice == '6':
            blocker.create_clean_shell_config()
        elif choice == '7':
            blocker.install_security_tools()
        elif choice == '8':
            blocker.monitor_terminal()
        elif choice == '9':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
