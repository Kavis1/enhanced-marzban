"""
Ad-blocking management service
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from collections import defaultdict

from .base_service import ScheduledService
from app.db.models import User, Node
from app.db.models_enhanced import AdBlockList, AdBlockDomain
from config import ADBLOCK_ENABLED, ADBLOCK_UPDATE_INTERVAL, ADBLOCK_DEFAULT_LISTS


class AdBlockManager(ScheduledService):
    """Service for managing ad-blocking functionality"""
    
    # Default ad-block lists
    DEFAULT_LISTS = {
        'easylist': {
            'name': 'EasyList',
            'url': 'https://easylist.to/easylist/easylist.txt',
            'description': 'Primary ad-blocking filter list'
        },
        'easyprivacy': {
            'name': 'EasyPrivacy',
            'url': 'https://easylist.to/easylist/easyprivacy.txt',
            'description': 'Privacy protection filter list'
        },
        'malware': {
            'name': 'Malware Domains',
            'url': 'https://malware-filter.gitlab.io/malware-filter/urlhaus-filter-hosts.txt',
            'description': 'Malware and phishing protection'
        },
        'social': {
            'name': 'Fanboy Social',
            'url': 'https://easylist.to/easylist/fanboy-social.txt',
            'description': 'Social media widgets blocking'
        }
    }
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.enabled = self.get_config('enabled', ADBLOCK_ENABLED)
        self.update_interval = self.get_config('update_interval', ADBLOCK_UPDATE_INTERVAL)
        self.default_lists = self.get_config('default_lists', ADBLOCK_DEFAULT_LISTS)
        
        # In-memory blocked domains cache
        self.blocked_domains: Set[str] = set()
        self.user_blocked_domains: Dict[int, Set[str]] = defaultdict(set)
        self.node_blocked_domains: Dict[int, Set[str]] = defaultdict(set)
        self.last_cache_update = datetime.min
    
    def initialize(self) -> bool:
        """Initialize the ad-block manager"""
        try:
            if not self.enabled:
                self.log_info("Ad-blocking is disabled")
                self._initialized = True
                return True
            
            # Initialize default lists
            self._initialize_default_lists()
            
            # Load blocked domains into cache
            self._refresh_blocked_domains_cache()
            
            # Start update scheduler
            self.start_scheduler(self.update_interval)
            
            self.log_info("Ad-block manager initialized")
            self._initialized = True
            return True
            
        except Exception as e:
            self.log_error(f"Failed to initialize ad-block manager: {str(e)}")
            return False
    
    def cleanup(self) -> bool:
        """Cleanup ad-block manager resources"""
        try:
            self.stop_scheduler()
            self.blocked_domains.clear()
            self.user_blocked_domains.clear()
            self.node_blocked_domains.clear()
            self.log_info("Ad-block manager cleaned up")
            return True
        except Exception as e:
            self.log_error(f"Failed to cleanup ad-block manager: {str(e)}")
            return False
    
    def run_scheduled_task(self):
        """Run scheduled ad-block list updates"""
        try:
            self._update_all_lists()
            self._refresh_blocked_domains_cache()
        except Exception as e:
            self.log_error(f"Scheduled task failed: {str(e)}")
    
    def _initialize_default_lists(self):
        """Initialize default ad-block lists in database"""
        try:
            with self.get_db_session() as db:
                for list_key, list_info in self.DEFAULT_LISTS.items():
                    existing_list = db.query(AdBlockList).filter(
                        AdBlockList.name == list_info['name']
                    ).first()
                    
                    if not existing_list:
                        adblock_list = AdBlockList(
                            name=list_info['name'],
                            url=list_info['url'],
                            description=list_info['description'],
                            is_enabled=list_key in self.default_lists
                        )
                        db.add(adblock_list)
                
                db.commit()
                self.log_info("Default ad-block lists initialized")
                
        except Exception as e:
            self.log_error(f"Failed to initialize default lists: {str(e)}")
    
    def _refresh_blocked_domains_cache(self):
        """Refresh blocked domains cache from database"""
        try:
            with self.get_db_session() as db:
                # Load global blocked domains
                enabled_lists = db.query(AdBlockList).filter(
                    AdBlockList.is_enabled == True
                ).all()
                
                self.blocked_domains.clear()
                for adblock_list in enabled_lists:
                    domains = db.query(AdBlockDomain).filter(
                        AdBlockDomain.list_id == adblock_list.id,
                        AdBlockDomain.is_active == True
                    ).all()
                    
                    for domain in domains:
                        self.blocked_domains.add(domain.domain.lower())
                
                # Load user-specific blocked domains
                self.user_blocked_domains.clear()
                users_with_custom_domains = db.query(User).filter(
                    User.custom_blocked_domains.isnot(None)
                ).all()
                
                for user in users_with_custom_domains:
                    try:
                        custom_domains = json.loads(user.custom_blocked_domains or '[]')
                        self.user_blocked_domains[user.id] = set(
                            domain.lower() for domain in custom_domains
                        )
                    except json.JSONDecodeError:
                        self.log_warning(f"Invalid custom blocked domains for user {user.id}")
                
                # Load node-specific blocked domains
                self.node_blocked_domains.clear()
                nodes_with_adblock = db.query(Node).filter(
                    Node.adblock_enabled == True
                ).all()
                
                for node in nodes_with_adblock:
                    if node.adblock_lists:
                        try:
                            list_ids = json.loads(node.adblock_lists)
                            node_domains = set()
                            
                            for list_id in list_ids:
                                domains = db.query(AdBlockDomain).filter(
                                    AdBlockDomain.list_id == list_id,
                                    AdBlockDomain.is_active == True
                                ).all()
                                
                                for domain in domains:
                                    node_domains.add(domain.domain.lower())
                            
                            self.node_blocked_domains[node.id] = node_domains
                            
                        except json.JSONDecodeError:
                            self.log_warning(f"Invalid ad-block lists for node {node.id}")
                
                self.last_cache_update = datetime.utcnow()
                self.log_debug(f"Refreshed blocked domains cache: {len(self.blocked_domains)} global domains")
                
        except Exception as e:
            self.log_error(f"Failed to refresh blocked domains cache: {str(e)}")
    
    def is_domain_blocked(self, domain: str, user_id: Optional[int] = None,
                         node_id: Optional[int] = None) -> bool:
        """Check if a domain is blocked"""
        if not self.enabled:
            return False
        
        domain = domain.lower()
        
        # Check global blocked domains
        if self._domain_in_set(domain, self.blocked_domains):
            return True
        
        # Check user-specific blocked domains
        if user_id and user_id in self.user_blocked_domains:
            if self._domain_in_set(domain, self.user_blocked_domains[user_id]):
                return True
        
        # Check node-specific blocked domains
        if node_id and node_id in self.node_blocked_domains:
            if self._domain_in_set(domain, self.node_blocked_domains[node_id]):
                return True
        
        return False
    
    def _domain_in_set(self, domain: str, domain_set: Set[str]) -> bool:
        """Check if domain matches any domain in set (supports wildcards)"""
        if domain in domain_set:
            return True
        
        # Check for wildcard matches
        domain_parts = domain.split('.')
        for i in range(len(domain_parts)):
            wildcard_domain = '*.' + '.'.join(domain_parts[i:])
            if wildcard_domain in domain_set:
                return True
        
        return False
    
    def add_custom_user_domain(self, user_id: int, domain: str) -> bool:
        """Add a custom blocked domain for a user"""
        try:
            with self.get_db_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                custom_domains = json.loads(user.custom_blocked_domains or '[]')
                domain_lower = domain.lower()
                
                if domain_lower not in custom_domains:
                    custom_domains.append(domain_lower)
                    user.custom_blocked_domains = json.dumps(custom_domains)
                    db.commit()
                    
                    # Update cache
                    self.user_blocked_domains[user_id].add(domain_lower)
                    
                    self.log_info(f"Added custom blocked domain {domain} for user {user.username}")
                    return True
                
                return False
                
        except Exception as e:
            self.log_error(f"Failed to add custom user domain: {str(e)}")
            return False
    
    def remove_custom_user_domain(self, user_id: int, domain: str) -> bool:
        """Remove a custom blocked domain for a user"""
        try:
            with self.get_db_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                custom_domains = json.loads(user.custom_blocked_domains or '[]')
                domain_lower = domain.lower()
                
                if domain_lower in custom_domains:
                    custom_domains.remove(domain_lower)
                    user.custom_blocked_domains = json.dumps(custom_domains)
                    db.commit()
                    
                    # Update cache
                    self.user_blocked_domains[user_id].discard(domain_lower)
                    
                    self.log_info(f"Removed custom blocked domain {domain} for user {user.username}")
                    return True
                
                return False
                
        except Exception as e:
            self.log_error(f"Failed to remove custom user domain: {str(e)}")
            return False
    
    def update_list(self, list_id: int) -> bool:
        """Update a specific ad-block list"""
        try:
            with self.get_db_session() as db:
                adblock_list = db.query(AdBlockList).filter(
                    AdBlockList.id == list_id
                ).first()
                
                if not adblock_list:
                    return False
                
                self.log_info(f"Updating ad-block list: {adblock_list.name}")
                
                # Download list content
                response = requests.get(adblock_list.url, timeout=30)
                response.raise_for_status()
                
                # Parse domains from content
                domains = self._parse_adblock_list(response.text)
                
                # Remove old domains
                db.query(AdBlockDomain).filter(
                    AdBlockDomain.list_id == list_id
                ).delete()
                
                # Add new domains
                for domain in domains:
                    adblock_domain = AdBlockDomain(
                        domain=domain.lower(),
                        list_id=list_id
                    )
                    db.add(adblock_domain)
                
                # Update list metadata
                adblock_list.last_updated = datetime.utcnow()
                adblock_list.domain_count = len(domains)
                
                db.commit()
                
                self.log_info(f"Updated ad-block list {adblock_list.name} with {len(domains)} domains")
                return True
                
        except Exception as e:
            self.log_error(f"Failed to update ad-block list {list_id}: {str(e)}")
            return False
    
    def _update_all_lists(self):
        """Update all enabled ad-block lists"""
        try:
            with self.get_db_session() as db:
                enabled_lists = db.query(AdBlockList).filter(
                    AdBlockList.is_enabled == True
                ).all()
                
                for adblock_list in enabled_lists:
                    # Check if list needs updating (older than update interval)
                    if (adblock_list.last_updated is None or 
                        datetime.utcnow() - adblock_list.last_updated > timedelta(seconds=self.update_interval)):
                        self.update_list(adblock_list.id)
                
        except Exception as e:
            self.log_error(f"Failed to update all lists: {str(e)}")
    
    def _parse_adblock_list(self, content: str) -> List[str]:
        """Parse domains from ad-block list content"""
        domains = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#') or line.startswith('!'):
                continue
            
            # Handle different formats
            if line.startswith('||') and line.endswith('^'):
                # AdBlock Plus format: ||example.com^
                domain = line[2:-1]
                if self._is_valid_domain(domain):
                    domains.append(domain)
            
            elif line.startswith('0.0.0.0 '):
                # Hosts file format: 0.0.0.0 example.com
                domain = line[8:].strip()
                if self._is_valid_domain(domain):
                    domains.append(domain)
            
            elif line.startswith('127.0.0.1 '):
                # Hosts file format: 127.0.0.1 example.com
                domain = line[10:].strip()
                if self._is_valid_domain(domain):
                    domains.append(domain)
            
            elif '.' in line and not ' ' in line:
                # Plain domain format
                if self._is_valid_domain(line):
                    domains.append(line)
        
        return list(set(domains))  # Remove duplicates
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Check if domain is valid"""
        if not domain or len(domain) > 253:
            return False
        
        # Basic domain validation
        if domain.startswith('.') or domain.endswith('.'):
            return False
        
        # Check for invalid characters
        invalid_chars = ['/', '\\', '?', '#', '[', ']', '@']
        if any(char in domain for char in invalid_chars):
            return False
        
        return True
    
    def get_statistics(self) -> Dict:
        """Get ad-blocking statistics"""
        try:
            with self.get_db_session() as db:
                total_lists = db.query(AdBlockList).count()
                enabled_lists = db.query(AdBlockList).filter(
                    AdBlockList.is_enabled == True
                ).count()
                total_domains = db.query(AdBlockDomain).filter(
                    AdBlockDomain.is_active == True
                ).count()
                
                return {
                    'enabled': self.enabled,
                    'total_lists': total_lists,
                    'enabled_lists': enabled_lists,
                    'total_blocked_domains': total_domains,
                    'cached_domains': len(self.blocked_domains),
                    'users_with_custom_domains': len(self.user_blocked_domains),
                    'nodes_with_adblock': len(self.node_blocked_domains),
                    'last_cache_update': self.last_cache_update
                }
                
        except Exception as e:
            self.log_error(f"Failed to get statistics: {str(e)}")
            return {'enabled': self.enabled, 'error': str(e)}


    def health_check(self) -> bool:
        """Perform health check for adblock manager"""
        try:
            # Check database connectivity
            with self.get_db_session() as db:
                db.query(AdBlockList).first()

            # Check if default adblock lists are accessible
            for list_key, list_info in self.DEFAULT_LISTS.items():
                if list_key in self.default_lists:
                    response = requests.head(list_info['url'], timeout=10)
                    if response.status_code != 200:
                        self.log_warning(f"Adblock list {list_info['name']} is not accessible (status code: {response.status_code})")
                        return False
            return True
        except Exception as e:
            self.log_error(f"Adblock manager health check failed: {str(e)}")
            return False

# Global instance
adblock_manager = AdBlockManager()
