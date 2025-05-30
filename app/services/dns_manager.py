"""
DNS override and management service
"""

import ipaddress
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .base_service import ScheduledService
from app.db.models import User
from app.db.models_enhanced import DNSRule, UserDNSRule, DNSCache
from config import DNS_OVERRIDE_ENABLED, DNS_OVERRIDE_SERVERS, DNS_CACHE_TTL


class DNSManager(ScheduledService):
    """Service for managing DNS overrides and rules"""
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.enabled = self.get_config('enabled', DNS_OVERRIDE_ENABLED)
        self.dns_servers = self.get_config('dns_servers', DNS_OVERRIDE_SERVERS)
        self.cache_ttl = self.get_config('cache_ttl', DNS_CACHE_TTL)
        
        # DNS cache for performance
        self.dns_cache: Dict[str, Dict] = {}  # domain -> {ip, expires_at, rule_id}
        self.user_dns_cache: Dict[Tuple[int, str], Dict] = {}  # (user_id, domain) -> {ip, expires_at}
        
        # Rule priority cache
        self.global_rules_cache: List[DNSRule] = []
        self.user_rules_cache: Dict[int, List[UserDNSRule]] = {}
        self.cache_expires_at = datetime.utcnow()
    
    def initialize(self) -> bool:
        """Initialize the DNS manager"""
        try:
            if not self.enabled:
                self.log_info("DNS override is disabled")
                self._initialized = True
                return True
            
            # Load DNS rules into cache
            self._refresh_rules_cache()
            
            # Start cache cleanup scheduler (every hour)
            self.start_scheduler(3600)
            
            self.log_info("DNS manager initialized")
            self._initialized = True
            return True
            
        except Exception as e:
            self.log_error(f"Failed to initialize DNS manager: {str(e)}")
            return False
    
    def cleanup(self) -> bool:
        """Cleanup DNS manager resources"""
        try:
            self.stop_scheduler()
            self.dns_cache.clear()
            self.user_dns_cache.clear()
            self.log_info("DNS manager cleaned up")
            return True
        except Exception as e:
            self.log_error(f"Failed to cleanup DNS manager: {str(e)}")
            return False
    
    def run_scheduled_task(self):
        """Run scheduled cache cleanup and rule refresh"""
        try:
            self._cleanup_expired_cache()
            self._refresh_rules_cache()
        except Exception as e:
            self.log_error(f"Scheduled task failed: {str(e)}")
    
    def _refresh_rules_cache(self):
        """Refresh DNS rules cache from database"""
        try:
            with self.get_db_session() as db:
                # Load global rules
                self.global_rules_cache = db.query(DNSRule).filter(
                    DNSRule.is_enabled == True
                ).order_by(DNSRule.priority.desc(), DNSRule.id).all()
                
                # Load user-specific rules
                user_rules = db.query(UserDNSRule).filter(
                    UserDNSRule.is_enabled == True
                ).order_by(UserDNSRule.priority.desc(), UserDNSRule.id).all()
                
                self.user_rules_cache.clear()
                for rule in user_rules:
                    if rule.user_id not in self.user_rules_cache:
                        self.user_rules_cache[rule.user_id] = []
                    self.user_rules_cache[rule.user_id].append(rule)
                
                self.cache_expires_at = datetime.utcnow() + timedelta(minutes=10)
                self.log_debug(f"Refreshed DNS rules cache: {len(self.global_rules_cache)} global, "
                              f"{len(user_rules)} user rules")
                
        except Exception as e:
            self.log_error(f"Failed to refresh rules cache: {str(e)}")
    
    def _cleanup_expired_cache(self):
        """Clean up expired DNS cache entries"""
        current_time = datetime.utcnow()
        
        # Clean global DNS cache
        expired_domains = [
            domain for domain, data in self.dns_cache.items()
            if data['expires_at'] <= current_time
        ]
        for domain in expired_domains:
            del self.dns_cache[domain]
        
        # Clean user DNS cache
        expired_user_domains = [
            key for key, data in self.user_dns_cache.items()
            if data['expires_at'] <= current_time
        ]
        for key in expired_user_domains:
            del self.user_dns_cache[key]
        
        if expired_domains or expired_user_domains:
            self.log_debug(f"Cleaned up {len(expired_domains)} global and "
                          f"{len(expired_user_domains)} user DNS cache entries")
    
    def resolve_domain(self, domain: str, user_id: Optional[int] = None) -> Optional[str]:
        """Resolve domain using DNS rules"""
        if not self.enabled:
            return None
        
        # Check user-specific rules first
        if user_id:
            ip = self._resolve_user_domain(domain, user_id)
            if ip:
                return ip
        
        # Check global rules
        return self._resolve_global_domain(domain)
    
    def _resolve_user_domain(self, domain: str, user_id: int) -> Optional[str]:
        """Resolve domain using user-specific rules"""
        cache_key = (user_id, domain.lower())
        
        # Check cache first
        if cache_key in self.user_dns_cache:
            cache_data = self.user_dns_cache[cache_key]
            if cache_data['expires_at'] > datetime.utcnow():
                return cache_data['ip']
            else:
                del self.user_dns_cache[cache_key]
        
        # Check user rules
        if user_id in self.user_rules_cache:
            for rule in self.user_rules_cache[user_id]:
                if self._domain_matches(domain, rule.domain):
                    # Cache the result
                    self.user_dns_cache[cache_key] = {
                        'ip': rule.target_ip,
                        'expires_at': datetime.utcnow() + timedelta(seconds=self.cache_ttl)
                    }
                    return rule.target_ip
        
        return None
    
    def _resolve_global_domain(self, domain: str) -> Optional[str]:
        """Resolve domain using global rules"""
        domain_lower = domain.lower()
        
        # Check cache first
        if domain_lower in self.dns_cache:
            cache_data = self.dns_cache[domain_lower]
            if cache_data['expires_at'] > datetime.utcnow():
                return cache_data['ip']
            else:
                del self.dns_cache[domain_lower]
        
        # Check global rules
        for rule in self.global_rules_cache:
            if self._domain_matches(domain, rule.domain):
                # Cache the result
                self.dns_cache[domain_lower] = {
                    'ip': rule.target_ip,
                    'expires_at': datetime.utcnow() + timedelta(seconds=self.cache_ttl),
                    'rule_id': rule.id
                }
                return rule.target_ip
        
        return None
    
    def _domain_matches(self, domain: str, pattern: str) -> bool:
        """Check if domain matches pattern (supports wildcards)"""
        domain = domain.lower()
        pattern = pattern.lower()
        
        if pattern == domain:
            return True
        
        # Wildcard matching
        if pattern.startswith('*.'):
            pattern_suffix = pattern[2:]
            return domain.endswith('.' + pattern_suffix) or domain == pattern_suffix
        
        return False
    
    def add_global_rule(self, domain: str, target_ip: str, priority: int = 100,
                       description: str = None) -> bool:
        """Add a global DNS rule"""
        try:
            # Validate IP address
            ipaddress.ip_address(target_ip)
            
            with self.get_db_session() as db:
                rule = DNSRule(
                    domain=domain.lower(),
                    target_ip=target_ip,
                    priority=priority,
                    description=description
                )
                db.add(rule)
                db.commit()
                
                # Refresh cache
                self._refresh_rules_cache()
                
                self.log_info(f"Added global DNS rule: {domain} -> {target_ip}")
                return True
                
        except Exception as e:
            self.log_error(f"Failed to add global DNS rule: {str(e)}")
            return False
    
    def add_user_rule(self, user_id: int, domain: str, target_ip: str,
                     priority: int = 100) -> bool:
        """Add a user-specific DNS rule"""
        try:
            # Validate IP address
            ipaddress.ip_address(target_ip)
            
            with self.get_db_session() as db:
                # Check if user exists
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    self.log_error(f"User {user_id} not found")
                    return False
                
                rule = UserDNSRule(
                    user_id=user_id,
                    domain=domain.lower(),
                    target_ip=target_ip,
                    priority=priority
                )
                db.add(rule)
                db.commit()
                
                # Refresh cache
                self._refresh_rules_cache()
                
                self.log_info(f"Added user DNS rule: {domain} -> {target_ip} (user {user.username})")
                return True
                
        except Exception as e:
            self.log_error(f"Failed to add user DNS rule: {str(e)}")
            return False
    
    def remove_global_rule(self, rule_id: int) -> bool:
        """Remove a global DNS rule"""
        try:
            with self.get_db_session() as db:
                rule = db.query(DNSRule).filter(DNSRule.id == rule_id).first()
                if rule:
                    db.delete(rule)
                    db.commit()
                    
                    # Refresh cache
                    self._refresh_rules_cache()
                    
                    self.log_info(f"Removed global DNS rule: {rule.domain}")
                    return True
                
                return False
                
        except Exception as e:
            self.log_error(f"Failed to remove global DNS rule: {str(e)}")
            return False
    
    def remove_user_rule(self, rule_id: int) -> bool:
        """Remove a user-specific DNS rule"""
        try:
            with self.get_db_session() as db:
                rule = db.query(UserDNSRule).filter(UserDNSRule.id == rule_id).first()
                if rule:
                    db.delete(rule)
                    db.commit()
                    
                    # Refresh cache
                    self._refresh_rules_cache()
                    
                    self.log_info(f"Removed user DNS rule: {rule.domain} (user {rule.user_id})")
                    return True
                
                return False
                
        except Exception as e:
            self.log_error(f"Failed to remove user DNS rule: {str(e)}")
            return False
    
    def get_global_rules(self) -> List[Dict]:
        """Get all global DNS rules"""
        return [
            {
                'id': rule.id,
                'domain': rule.domain,
                'target_ip': rule.target_ip,
                'priority': rule.priority,
                'is_enabled': rule.is_enabled,
                'description': rule.description,
                'created_at': rule.created_at,
                'updated_at': rule.updated_at
            }
            for rule in self.global_rules_cache
        ]
    
    def get_user_rules(self, user_id: int) -> List[Dict]:
        """Get DNS rules for a specific user"""
        user_rules = self.user_rules_cache.get(user_id, [])
        return [
            {
                'id': rule.id,
                'domain': rule.domain,
                'target_ip': rule.target_ip,
                'priority': rule.priority,
                'is_enabled': rule.is_enabled,
                'created_at': rule.created_at,
                'updated_at': rule.updated_at
            }
            for rule in user_rules
        ]
    
    def generate_xray_dns_config(self, user_id: Optional[int] = None) -> Dict:
        """Generate XRay DNS configuration with rules"""
        dns_config = {
            "servers": [
                {
                    "address": server,
                    "domains": []
                }
                for server in self.dns_servers
            ],
            "hosts": {}
        }
        
        # Add global rules
        for rule in self.global_rules_cache:
            dns_config["hosts"][rule.domain] = rule.target_ip
        
        # Add user-specific rules
        if user_id and user_id in self.user_rules_cache:
            for rule in self.user_rules_cache[user_id]:
                dns_config["hosts"][rule.domain] = rule.target_ip
        
        return dns_config


# Global instance
dns_manager = DNSManager()
