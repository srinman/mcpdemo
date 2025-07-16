#!/usr/bin/env python3
"""
Network traffic sniffer for Memento MCP system
Monitors Azure OpenAI and MCP server communications
"""

import subprocess
import sys
import threading
import time
import json
import re
from datetime import datetime
from pathlib import Path

class MementoNetworkSniffer:
    """Network traffic sniffer for Memento system"""
    
    def __init__(self):
        self.running = False
        self.capture_thread = None
        self.stats = {
            'azure_requests': 0,
            'mcp_requests': 0,
            'total_packets': 0,
            'start_time': None
        }
    
    def check_requirements(self):
        """Check if required tools are available"""
        try:
            # Check if tcpdump is available
            subprocess.run(['which', 'tcpdump'], check=True, capture_output=True)
            print("✅ tcpdump found")
            return True
        except subprocess.CalledProcessError:
            print("❌ tcpdump not found. Install with: sudo apt install tcpdump")
            return False
    
    def get_network_interfaces(self):
        """Get available network interfaces"""
        try:
            result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True)
            interfaces = []
            for line in result.stdout.split('\n'):
                if ': ' in line and 'mtu' in line:
                    interface = line.split(':')[1].strip().split('@')[0]
                    if interface not in ['lo']:  # Skip loopback
                        interfaces.append(interface)
            return interfaces
        except:
            return ['eth0', 'wlan0']  # Default fallback
    
    def test_connectivity(self):
        """Test connectivity to Azure OpenAI"""
        print("🔍 Testing network connectivity...")
        
        # Test basic connectivity
        try:
            result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ Basic internet connectivity: OK")
            else:
                print("❌ Basic internet connectivity: FAILED")
        except:
            print("❌ Basic internet connectivity: FAILED")
        
        # Test Azure OpenAI connectivity
        try:
            result = subprocess.run(['curl', '-I', '--max-time', '5', 'https://api.openai.com'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ OpenAI API connectivity: OK")
            else:
                print("⚠️  OpenAI API connectivity: Limited")
        except:
            print("⚠️  OpenAI API connectivity: Limited")
        
        # Show available interfaces
        interfaces = self.get_network_interfaces()
        print(f"📡 Available network interfaces: {', '.join(interfaces)}")
        
        return True
    
    def parse_traffic_line(self, line: str) -> dict:
        """Parse a line of network traffic"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        traffic_info = {
            'timestamp': timestamp,
            'raw_line': line,
            'service': 'UNKNOWN',
            'direction': 'UNKNOWN',
            'details': {}
        }
        
        # Detect Azure OpenAI traffic
        if 'openai.azure.com' in line or '.443' in line:
            traffic_info['service'] = 'AZURE_OPENAI'
            self.stats['azure_requests'] += 1
            
            # Parse HTTP details
            if 'POST' in line:
                traffic_info['direction'] = 'REQUEST'
                traffic_info['details']['method'] = 'POST'
            elif 'HTTP' in line:
                traffic_info['direction'] = 'RESPONSE'
        
        # Detect MCP server traffic
        elif '.8000' in line or '8000' in line:
            traffic_info['service'] = 'MCP_SERVER'
            self.stats['mcp_requests'] += 1
            
            if 'localhost' in line or '127.0.0.1' in line:
                traffic_info['direction'] = 'LOCAL'
        
        self.stats['total_packets'] += 1
        return traffic_info
    
    def format_traffic_output(self, traffic_info: dict) -> str:
        """Format traffic information for display"""
        timestamp = traffic_info['timestamp']
        service = traffic_info['service']
        direction = traffic_info['direction']
        
        # Color coding
        if service == 'AZURE_OPENAI':
            service_emoji = '🧠'
            color = '\033[94m'  # Blue
        elif service == 'MCP_SERVER':
            service_emoji = '🔌'
            color = '\033[92m'  # Green
        else:
            service_emoji = '❓'
            color = '\033[93m'  # Yellow
        
        reset_color = '\033[0m'
        
        # Format direction
        if direction == 'REQUEST':
            direction_emoji = '📤'
        elif direction == 'RESPONSE':
            direction_emoji = '📥'
        else:
            direction_emoji = '🔄'
        
        formatted = f"{color}[{timestamp}] {service_emoji} {service} {direction_emoji} {direction}{reset_color}"
        
        # Add details if available
        if traffic_info['details']:
            details_str = ', '.join(f"{k}: {v}" for k, v in traffic_info['details'].items())
            formatted += f" ({details_str})"
        
        return formatted
    
    def monitor_traffic_realtime(self):
        """Monitor network traffic in real-time"""
        print(f"🔍 Starting real-time network monitoring...")
        print(f"📡 Monitoring Azure OpenAI (port 443) and MCP server (port 8000)")
        print(f"🔄 Press Ctrl+C to stop\n")
        
        # Test connectivity first
        self.test_connectivity()
        print()
        
        # Get available interfaces
        interfaces = self.get_network_interfaces()
        primary_interface = interfaces[0] if interfaces else 'any'
        
        # More general tcpdump command that captures more traffic
        cmd = [
            'sudo', 'tcpdump', '-i', primary_interface, '-n', '-l', '-s', '0',
            '-v',  # Verbose output
            '(port 443 or port 8000 or port 80)'
        ]
        
        print(f"🔍 Running command: {' '.join(cmd)}")
        print(f"📡 Monitoring interface: {primary_interface}")
        print(f"🔄 Capturing HTTP (80), HTTPS (443), and MCP (8000) traffic")
        print(f"⏱️  Waiting for traffic... (try running the MCP client in another terminal)")
        print()
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            self.running = True
            self.stats['start_time'] = time.time()
            
            # Add a timeout to show that we're waiting
            last_activity = time.time()
            
            for line in iter(process.stdout.readline, ''):
                if not self.running:
                    break
                
                line = line.strip()
                if line:
                    last_activity = time.time()
                    traffic_info = self.parse_traffic_line(line)
                    formatted_output = self.format_traffic_output(traffic_info)
                    print(formatted_output)
                    
                    # Print raw line for debugging if verbose
                    if '--verbose' in sys.argv:
                        print(f"   Raw: {line}")
                
                # Show "waiting" message every 10 seconds
                current_time = time.time()
                if current_time - last_activity > 10:
                    print(f"⏳ Still waiting for traffic... ({int(current_time - self.stats['start_time'])}s elapsed)")
                    last_activity = current_time
            
            process.terminate()
            
        except KeyboardInterrupt:
            print(f"\n🛑 Stopping network monitoring...")
            self.running = False
        except subprocess.CalledProcessError as e:
            print(f"❌ Error running tcpdump: {e}")
            print("💡 Make sure you have sudo privileges")
    
    def monitor_traffic_to_file(self, filename: str):
        """Monitor traffic and save to file"""
        print(f"📝 Saving traffic to {filename}...")
        
        cmd = [
            'sudo', 'tcpdump', '-i', 'any', '-n', '-s', '0',
            '(host openai.azure.com or dst port 443) or (port 8000)',
            '-w', filename
        ]
        
        try:
            process = subprocess.Popen(cmd)
            print(f"✅ Traffic capture started. Press Ctrl+C to stop.")
            process.wait()
        except KeyboardInterrupt:
            print(f"\n🛑 Stopping capture...")
            process.terminate()
    
    def show_network_stats(self):
        """Show current network statistics"""
        print(f"\n📊 Network Statistics:")
        print(f"=" * 40)
        
        # Show active connections
        print("🔌 Active connections:")
        try:
            result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
            connections = result.stdout.split('\n')
            
            relevant_connections = [
                line for line in connections 
                if '8000' in line or '443' in line
            ]
            
            for conn in relevant_connections[:10]:  # Show first 10
                if conn.strip():
                    print(f"   {conn}")
        except:
            print("   Could not retrieve connection info")
        
        # Show process info
        print(f"\n🐍 Python processes:")
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout.split('\n')
            
            python_processes = [
                line for line in processes 
                if 'python' in line and ('memento' in line or 'mcp' in line)
            ]
            
            for proc in python_processes:
                if proc.strip():
                    # Extract relevant info
                    parts = proc.split()
                    if len(parts) >= 11:
                        user = parts[0]
                        pid = parts[1]
                        cpu = parts[2]
                        mem = parts[3]
                        command = ' '.join(parts[10:])
                        print(f"   PID: {pid}, CPU: {cpu}%, MEM: {mem}%, CMD: {command}")
        except:
            print("   Could not retrieve process info")
        
        # Show traffic stats if monitoring
        if self.stats['start_time']:
            uptime = time.time() - self.stats['start_time']
            print(f"\n📈 Traffic Statistics:")
            print(f"   Total packets: {self.stats['total_packets']}")
            print(f"   Azure OpenAI packets: {self.stats['azure_requests']}")
            print(f"   MCP server packets: {self.stats['mcp_requests']}")
            print(f"   Monitoring uptime: {uptime:.1f}s")
    
    def show_menu(self):
        """Show main menu"""
        print(f"\n🔍 Memento Network Traffic Sniffer")
        print(f"=" * 40)
        print(f"1. Real-time traffic monitoring")
        print(f"2. Save traffic to file (.pcap)")
        print(f"3. Show network statistics")
        print(f"4. Monitor specific port")
        print(f"5. Exit")
    
    def monitor_specific_port(self):
        """Monitor traffic on a specific port"""
        port = input("Enter port number (e.g., 8000, 443): ").strip()
        
        if not port.isdigit():
            print("❌ Invalid port number")
            return
        
        print(f"🔍 Monitoring port {port}...")
        
        cmd = [
            'sudo', 'tcpdump', '-i', 'any', '-n', '-l', '-s', '0',
            f'port {port}'
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            print(f"📡 Monitoring port {port}. Press Ctrl+C to stop.\n")
            
            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                if line:
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    print(f"[{timestamp}] {line}")
            
            process.terminate()
            
        except KeyboardInterrupt:
            print(f"\n🛑 Stopping port monitoring...")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: {e}")
    
    def run(self):
        """Main run loop"""
        if not self.check_requirements():
            return
        
        print(f"🚀 Memento Network Traffic Sniffer")
        print(f"=" * 40)
        print(f"🔍 Monitor Azure OpenAI and MCP server traffic")
        print(f"📡 Real-time packet analysis and statistics")
        
        while True:
            self.show_menu()
            choice = input("\nEnter choice (1-5): ").strip()
            
            if choice == '1':
                self.monitor_traffic_realtime()
            elif choice == '2':
                filename = input("Enter filename (e.g., traffic.pcap): ").strip()
                if not filename:
                    filename = f"memento_traffic_{int(time.time())}.pcap"
                self.monitor_traffic_to_file(filename)
            elif choice == '3':
                self.show_network_stats()
            elif choice == '4':
                self.monitor_specific_port()
            elif choice == '5':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-5.")
            
            if choice != '5':
                input("\nPress Enter to continue...")

def main():
    """Main function"""
    sniffer = MementoNetworkSniffer()
    sniffer.run()

if __name__ == "__main__":
    main()
