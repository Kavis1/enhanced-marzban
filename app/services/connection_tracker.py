"""
Connection tracking service for user connection limits
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Set, Optional, Tuple
from collections import defaultdict

from .base_service import ScheduledService
from app.db.models import User
from app.db.models_enhanced import ConnectionLog
from config import (
    CONNECTION_LIMIT_ENABLED, DEFAULT_MAX_CONNECTIONS, 
    CONNECTION_TRACKING_INTERVAL
)


class ConnectionTracker(ScheduledService):
    """Service for tracking and limiting user connections"""
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.enabled = self.get_config('enabled', CONNECTION_LIMIT_ENABLED)
        self.default_max_connections = self.get_config('default_max_connections', DEFAULT_MAX_CONNECTIONS)
        self.tracking_interval = self.get_config('tracking_interval', CONNECTION_TRACKING_INTERVAL)
        
        # In-memory connection tracking
        self.active_connections: Dict[int, Set[str]] = defaultdict(set)  # user_id -> set of IP addresses
        self.connection_timestamps: Dict[Tuple[int, str], datetime] = {}  # (user_id, ip) -> timestamp
        self.connection_details: Dict[str, Dict] = {}  # connection_id -> details
    
    def initialize(self) -> bool:
        """Initialize the connection tracker"""
        try:
            if not self.enabled:
                self.log_info("Connection tracking is disabled")
                self._initialized = True
                return True
            
            # Load existing active connections from database
            self._load_active_connections()
            
            # Start cleanup scheduler
            self.start_scheduler(self.tracking_interval)
            
            self.log_info("Connection tracker initialized")
            self._initialized = True
            return True
            
        except Exception as e:
            self.log_error(f"Failed to initialize connection tracker: {str(e)}")
            return False
    
    def cleanup(self) -> bool:
        """Cleanup connection tracker resources"""
        try:
            self.stop_scheduler()
            self.log_info("Connection tracker cleaned up")
            return True
        except Exception as e:
            self.log_error(f"Failed to cleanup connection tracker: {str(e)}")
            return False
    
    def run_scheduled_task(self):
        """Run scheduled cleanup and maintenance tasks"""
        try:
            self._cleanup_stale_connections()
            self._update_user_connection_counts()
            self._cleanup_old_logs()
        except Exception as e:
            self.log_error(f"Scheduled task failed: {str(e)}")
    
    def _load_active_connections(self):
        """Load active connections from database"""
        try:
            with self.get_db_session() as db:
                # Get connections from last hour that are still active
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                active_logs = db.query(ConnectionLog).filter(
                    ConnectionLog.connected_at >= cutoff_time,
                    ConnectionLog.is_active == True
                ).all()
                
                for log in active_logs:
                    self.active_connections[log.user_id].add(log.ip_address)
                    self.connection_timestamps[(log.user_id, log.ip_address)] = log.last_activity
                    self.connection_details[log.connection_id] = {
                        'user_id': log.user_id,
                        'ip_address': log.ip_address,
                        'protocol': log.protocol,
                        'inbound_tag': log.inbound_tag,
                        'connected_at': log.connected_at,
                        'node_id': log.node_id
                    }
                
                self.log_info(f"Loaded {len(active_logs)} active connections")
                
        except Exception as e:
            self.log_error(f"Failed to load active connections: {str(e)}")
    
    def _cleanup_stale_connections(self):
        """Remove stale connections that haven't been active"""
        try:
            current_time = datetime.utcnow()
            stale_threshold = timedelta(minutes=5)  # Consider connections stale after 5 minutes
            
            stale_connections = []
            for (user_id, ip_address), last_activity in self.connection_timestamps.items():
                if current_time - last_activity > stale_threshold:
                    stale_connections.append((user_id, ip_address))
            
            for user_id, ip_address in stale_connections:
                self._remove_connection(user_id, ip_address, "stale")
            
            if stale_connections:
                self.log_debug(f"Cleaned up {len(stale_connections)} stale connections")
                
        except Exception as e:
            self.log_error(f"Failed to cleanup stale connections: {str(e)}")
    
    def _update_user_connection_counts(self):
        """Update user connection counts in database"""
        try:
            with self.get_db_session() as db:
                for user_id, ips in self.active_connections.items():
                    db.query(User).filter(User.id == user_id).update({
                        'current_connections': len(ips)
                    })
                db.commit()
        except Exception as e:
            self.log_error(f"Failed to update user connection counts: {str(e)}")
    
    def add_connection(self, user_id: int, ip_address: str, node_id: Optional[int] = None,
                      user_agent: Optional[str] = None) -> bool:
        """Add a new connection and check limits"""
        if not self.enabled:
            return True
        
        try:
            with self.get_db_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    self.log_error(f"User {user_id} not found")
                    return False
                
                max_connections = user.max_connections or self.default_max_connections
                current_connections = len(self.active_connections.get(user_id, set()))
                
                # Allow if IP is already connected (reconnection)
                if ip_address in self.active_connections.get(user_id, set()):
                    self._update_connection_activity(user_id, ip_address)
                    return True
                
                # Check connection limit
                if current_connections >= max_connections:
                    self.log_warning(
                        f"Connection limit exceeded for user {user.username} "
                        f"({current_connections}/{max_connections}) from {ip_address}"
                    )
                    
                    # Log violation for fail2ban
                    from .fail2ban_logger import fail2ban_logger
                    fail2ban_logger.log_connection_limit_violation(
                        ip_address, user.username, current_connections, max_connections
                    )
                    
                    return False
                
                # Add connection
                self.active_connections[user_id].add(ip_address)
                self.connection_timestamps[(user_id, ip_address)] = datetime.utcnow()
                
                # Log to database
                connection_log = ConnectionLog(
                    user_id=user_id,
                    ip_address=ip_address,
                    node_id=node_id,
                    user_agent=user_agent,
                    connected_at=datetime.utcnow()
                )
                db.add(connection_log)
                
                # Update user's current connection count
                user.current_connections = len(self.active_connections[user_id])
                db.commit()
                
                self.log_info(
                    f"Connection added for user {user.username} from {ip_address} "
                    f"({user.current_connections}/{max_connections})"
                )
                
                return True
                
        except Exception as e:
            self.log_error(f"Failed to add connection: {str(e)}")
            return False
    
    def remove_connection(self, user_id: int, ip_address: str, reason: str = "disconnect") -> bool:
        """Remove a connection"""
        return self._remove_connection(user_id, ip_address, reason)
    
    def _remove_connection(self, user_id: int, ip_address: str, reason: str = "disconnect") -> bool:
        """Internal method to remove a connection"""
        if not self.enabled:
            return True
        
        try:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(ip_address)
                
                # Remove from timestamps
                self.connection_timestamps.pop((user_id, ip_address), None)
                
                # Update database
                with self.get_db_session() as db:
                    # Mark connection as inactive
                    db.query(ConnectionLog).filter(
                        ConnectionLog.user_id == user_id,
                        ConnectionLog.ip_address == ip_address,
                        ConnectionLog.is_active == True
                    ).update({
                        'is_active': False,
                        'disconnected_at': datetime.utcnow(),
                        'disconnect_reason': reason
                    })
                    
                    # Update user's current connection count
                    user = db.query(User).filter(User.id == user_id).first()
                    if user:
                        user.current_connections = len(self.active_connections[user_id])
                    
                    db.commit()
                
                self.log_debug(f"Connection removed for user {user_id} from {ip_address} ({reason})")
                return True
                
        except Exception as e:
            self.log_error(f"Failed to remove connection: {str(e)}")
            return False
    
    def _update_connection_activity(self, user_id: int, ip_address: str):
        """Update last activity timestamp for a connection"""
        self.connection_timestamps[(user_id, ip_address)] = datetime.utcnow()
        
        try:
            with self.get_db_session() as db:
                db.query(ConnectionLog).filter(
                    ConnectionLog.user_id == user_id,
                    ConnectionLog.ip_address == ip_address,
                    ConnectionLog.is_active == True
                ).update({'last_activity': datetime.utcnow()})
                db.commit()
        except Exception as e:
            self.log_error(f"Failed to update connection activity: {str(e)}")
    
    def check_connection_allowed(self, user_id: int, ip_address: str) -> Tuple[bool, str]:
        """Check if a connection is allowed for a user"""
        if not self.enabled:
            return True, "Connection tracking disabled"
        
        try:
            with self.get_db_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return False, "User not found"
                
                max_connections = user.max_connections or self.default_max_connections
                current_connections = len(self.active_connections.get(user_id, set()))
                
                # Allow if IP is already connected
                if ip_address in self.active_connections.get(user_id, set()):
                    return True, "IP already connected"
                
                # Check limit
                if current_connections >= max_connections:
                    return False, f"Connection limit exceeded ({current_connections}/{max_connections})"
                
                return True, f"Connection allowed ({current_connections}/{max_connections})"
                
        except Exception as e:
            self.log_error(f"Failed to check connection allowance: {str(e)}")
            return False, "Internal error"
    
    def get_user_connections(self, user_id: int) -> Dict:
        """Get current connections for a user"""
        connections = self.active_connections.get(user_id, set())
        return {
            'user_id': user_id,
            'active_connections': len(connections),
            'ip_addresses': list(connections),
            'connection_details': [
                {
                    'ip_address': ip,
                    'last_activity': self.connection_timestamps.get((user_id, ip))
                }
                for ip in connections
            ]
        }
    
    def force_disconnect_user(self, user_id: int, reason: str = "forced"):
        """Force disconnect all connections for a user"""
        if user_id in self.active_connections:
            ip_addresses = list(self.active_connections[user_id])
            for ip_address in ip_addresses:
                self._remove_connection(user_id, ip_address, reason)
            
            self.log_info(f"Force disconnected {len(ip_addresses)} connections for user {user_id}")
    
    def _cleanup_old_logs(self):
        """Clean up old connection logs"""
        try:
            with self.get_db_session() as db:
                # Remove logs older than 30 days
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                deleted_count = db.query(ConnectionLog).filter(
                    ConnectionLog.connected_at < cutoff_date
                ).delete()
                
                if deleted_count > 0:
                    db.commit()
                    self.log_debug(f"Cleaned up {deleted_count} old connection logs")
                    
        except Exception as e:
            self.log_error(f"Failed to cleanup old logs: {str(e)}")
    
    def get_statistics(self) -> Dict:
        """Get connection tracking statistics"""
        total_active = sum(len(ips) for ips in self.active_connections.values())
        active_users = len(self.active_connections)
        
        return {
            'enabled': self.enabled,
            'total_active_connections': total_active,
            'active_users': active_users,
            'default_max_connections': self.default_max_connections,
            'tracking_interval': self.tracking_interval
        }


# Global instance
connection_tracker = ConnectionTracker()
