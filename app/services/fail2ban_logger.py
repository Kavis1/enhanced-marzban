"""
Fail2ban integration logger for traffic monitoring
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from .base_service import ConfigurableService
from config import (
    FAIL2BAN_ENABLED, FAIL2BAN_LOG_PATH, TORRENT_DETECTION_ENABLED,
    TRAFFIC_ANALYSIS_ENABLED, FAIL2BAN_MAX_VIOLATIONS
)


class Fail2banLogger(ConfigurableService):
    """Service for logging traffic violations for fail2ban integration"""
    
    # BitTorrent protocol signatures
    TORRENT_SIGNATURES = [
        b'\x13BitTorrent protocol',  # BitTorrent handshake
        b'announce',  # Tracker announce
        b'info_hash',  # Torrent info hash
        b'd8:announce',  # Bencode announce
        b'BitTorrent',  # General BitTorrent string
    ]
    
    # Suspicious patterns
    SUSPICIOUS_PATTERNS = {
        'high_bandwidth': {'threshold': 100 * 1024 * 1024, 'window': 300},  # 100MB in 5 minutes
        'rapid_connections': {'threshold': 50, 'window': 60},  # 50 connections in 1 minute
        'port_scanning': {'threshold': 20, 'window': 30},  # 20 different ports in 30 seconds
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.log_file_path = self.get_config('log_path', FAIL2BAN_LOG_PATH)
        self.enabled = self.get_config('enabled', FAIL2BAN_ENABLED)
        self.torrent_detection = self.get_config('torrent_detection', TORRENT_DETECTION_ENABLED)
        self.traffic_analysis = self.get_config('traffic_analysis', TRAFFIC_ANALYSIS_ENABLED)
        self.max_violations = self.get_config('max_violations', FAIL2BAN_MAX_VIOLATIONS)
        
        # Ensure log directory exists
        if self.enabled:
            self._ensure_log_directory()
    
    def initialize(self) -> bool:
        """Initialize the fail2ban logger service"""
        try:
            if not self.enabled:
                self.log_info("Fail2ban integration is disabled")
                self._initialized = True
                return True
            
            self._ensure_log_directory()
            self._test_log_writing()
            
            self.log_info("Fail2ban logger service initialized")
            self._initialized = True
            return True
            
        except Exception as e:
            self.log_error(f"Failed to initialize fail2ban logger: {str(e)}")
            return False
    
    def cleanup(self) -> bool:
        """Cleanup fail2ban logger resources"""
        try:
            self.log_info("Cleaning up fail2ban logger service")
            return True
        except Exception as e:
            self.log_error(f"Failed to cleanup fail2ban logger: {str(e)}")
            return False
    
    def _ensure_log_directory(self):
        """Ensure log directory exists"""
        try:
            log_dir = Path(self.log_file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Set appropriate permissions
            os.chmod(log_dir, 0o755)
            
        except Exception as e:
            self.log_error(f"Failed to create log directory: {str(e)}")
            raise
    
    def _test_log_writing(self):
        """Test if we can write to the log file"""
        try:
            test_entry = self._format_log_entry(
                "TEST", "127.0.0.1", "test_user", "initialized", {"test": True}
            )
            self._write_log_entry(test_entry)
            
        except Exception as e:
            self.log_error(f"Failed to write test log entry: {str(e)}")
            raise
    
    def _format_log_entry(self, violation_type: str, ip_address: str, 
                         username: str, action: str, details: Dict[str, Any] = None) -> str:
        """Format log entry for fail2ban"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        details = details or {}
        
        log_entry = {
            'timestamp': timestamp,
            'violation_type': violation_type,
            'ip_address': ip_address,
            'username': username,
            'action': action,
            'details': details
        }
        
        # Format for fail2ban parsing
        # Pattern: [TIMESTAMP] MARZBAN_VIOLATION: TYPE=violation_type IP=ip_address USER=username ACTION=action
        formatted_entry = (
            f"[{timestamp}] MARZBAN_VIOLATION: "
            f"TYPE={violation_type} IP={ip_address} USER={username} ACTION={action}"
        )
        
        if details:
            details_str = json.dumps(details, separators=(',', ':'))
            formatted_entry += f" DETAILS={details_str}"
        
        return formatted_entry
    
    def _write_log_entry(self, log_entry: str):
        """Write log entry to file"""
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"{log_entry}\n")
                f.flush()
        except Exception as e:
            self.log_error(f"Failed to write log entry: {str(e)}")
    
    def log_torrent_violation(self, ip_address: str, username: str, 
                            details: Dict[str, Any] = None):
        """Log torrent traffic violation"""
        if not self.enabled or not self.torrent_detection:
            return
        
        details = details or {}
        log_entry = self._format_log_entry(
            "TORRENT", ip_address, username, "detected", details
        )
        self._write_log_entry(log_entry)
        self.log_warning(f"Torrent violation detected for user {username} from {ip_address}")
    
    def log_suspicious_activity(self, ip_address: str, username: str, 
                              activity_type: str, details: Dict[str, Any] = None):
        """Log suspicious activity violation"""
        if not self.enabled or not self.traffic_analysis:
            return
        
        details = details or {}
        log_entry = self._format_log_entry(
            f"SUSPICIOUS_{activity_type.upper()}", ip_address, username, "detected", details
        )
        self._write_log_entry(log_entry)
        self.log_warning(f"Suspicious activity ({activity_type}) detected for user {username} from {ip_address}")
    
    def log_connection_limit_violation(self, ip_address: str, username: str, 
                                     current_connections: int, max_connections: int):
        """Log connection limit violation"""
        if not self.enabled:
            return
        
        details = {
            'current_connections': current_connections,
            'max_connections': max_connections
        }
        log_entry = self._format_log_entry(
            "CONNECTION_LIMIT", ip_address, username, "blocked", details
        )
        self._write_log_entry(log_entry)
        self.log_warning(f"Connection limit violation for user {username} from {ip_address}")
    
    def log_user_suspended(self, ip_address: str, username: str, reason: str):
        """Log user suspension"""
        if not self.enabled:
            return
        
        details = {'reason': reason}
        log_entry = self._format_log_entry(
            "USER_SUSPENDED", ip_address, username, "suspended", details
        )
        self._write_log_entry(log_entry)
        self.log_warning(f"User {username} suspended from {ip_address}: {reason}")
    
    def detect_torrent_traffic(self, data: bytes) -> bool:
        """Detect BitTorrent traffic in data"""
        if not self.torrent_detection:
            return False
        
        # Check for BitTorrent protocol signatures
        for signature in self.TORRENT_SIGNATURES:
            if signature in data:
                return True
        
        # Check for DHT (Distributed Hash Table) traffic
        if self._is_dht_traffic(data):
            return True
        
        # Check for tracker communication
        if self._is_tracker_communication(data):
            return True
        
        return False
    
    def _is_dht_traffic(self, data: bytes) -> bool:
        """Check if data contains DHT traffic"""
        try:
            # DHT queries typically contain 'd1:' at the beginning (bencode)
            if data.startswith(b'd1:'):
                # Look for DHT-specific keys
                dht_keys = [b'ping', b'find_node', b'get_peers', b'announce_peer']
                return any(key in data for key in dht_keys)
        except:
            pass
        return False
    
    def _is_tracker_communication(self, data: bytes) -> bool:
        """Check if data contains tracker communication"""
        try:
            # HTTP tracker requests
            if b'GET /' in data and b'announce' in data:
                return True
            
            # UDP tracker protocol
            if len(data) >= 16:
                # Check for UDP tracker connection ID
                connection_id = data[:8]
                if connection_id == b'\x00\x00\x04\x17\x27\x10\x19\x80':
                    return True
        except:
            pass
        return False
    
    def analyze_traffic_pattern(self, user_id: int, ip_address: str, 
                              bytes_transferred: int, connection_count: int,
                              time_window: int) -> List[str]:
        """Analyze traffic patterns for suspicious activity"""
        violations = []
        
        if not self.traffic_analysis:
            return violations
        
        # High bandwidth usage
        if bytes_transferred > self.SUSPICIOUS_PATTERNS['high_bandwidth']['threshold']:
            if time_window <= self.SUSPICIOUS_PATTERNS['high_bandwidth']['window']:
                violations.append('high_bandwidth')
        
        # Rapid connections
        if connection_count > self.SUSPICIOUS_PATTERNS['rapid_connections']['threshold']:
            if time_window <= self.SUSPICIOUS_PATTERNS['rapid_connections']['window']:
                violations.append('rapid_connections')
        
        return violations
    
    def get_violation_count(self, username: str, hours: int = 24) -> int:
        """Get violation count for a user in the last N hours"""
        if not self.enabled or not os.path.exists(self.log_file_path):
            return 0
        
        try:
            count = 0
            cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
            
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if f"USER={username}" in line:
                        # Extract timestamp and check if within time window
                        timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', line)
                        if timestamp_match:
                            timestamp_str = timestamp_match.group(1)
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S').timestamp()
                            if timestamp >= cutoff_time:
                                count += 1
            
            return count
            
        except Exception as e:
            self.log_error(f"Failed to get violation count: {str(e)}")
            return 0
    
    def create_fail2ban_config(self) -> str:
        """Generate fail2ban jail configuration"""
        config = f"""
[marzban-violations]
enabled = true
port = all
filter = marzban-violations
logpath = {self.log_file_path}
maxretry = {self.max_violations}
findtime = 3600
bantime = 3600
action = marzban-ban[name=%(__name__)s, port="%(port)s", protocol="%(protocol)s"]

[marzban-torrent]
enabled = true
port = all
filter = marzban-torrent
logpath = {self.log_file_path}
maxretry = 1
findtime = 3600
bantime = 7200
action = marzban-ban[name=%(__name__)s, port="%(port)s", protocol="%(protocol)s"]
"""
        return config
    
    def create_fail2ban_filter(self) -> str:
        """Generate fail2ban filter configuration"""
        filter_config = """
[Definition]
failregex = ^\\[.*\\] MARZBAN_VIOLATION: TYPE=.* IP=<HOST> USER=.* ACTION=.*$

[marzban-torrent]
failregex = ^\\[.*\\] MARZBAN_VIOLATION: TYPE=TORRENT IP=<HOST> USER=.* ACTION=detected.*$

[marzban-violations]
failregex = ^\\[.*\\] MARZBAN_VIOLATION: TYPE=(?:SUSPICIOUS_.*|CONNECTION_LIMIT) IP=<HOST> USER=.* ACTION=.*$
"""
        return filter_config


# Global instance
fail2ban_logger = Fail2banLogger()
