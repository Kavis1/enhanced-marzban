"""
Enhanced services manager for coordinating all enhanced features
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .two_factor_auth import two_factor_service
from .fail2ban_logger import fail2ban_logger
from .connection_tracker import connection_tracker
from .dns_manager import dns_manager
from .adblock_manager import adblock_manager
from config import (
    TWO_FACTOR_AUTH_ENABLED, FAIL2BAN_ENABLED, CONNECTION_LIMIT_ENABLED,
    DNS_OVERRIDE_ENABLED, ADBLOCK_ENABLED
)

logger = logging.getLogger(__name__)


class ServiceManager:
    """Manager for all enhanced services"""
    
    def __init__(self):
        self.services: Dict[str, Any] = {}
        self.initialized = False
        self.startup_order = [
            'two_factor_auth',
            'fail2ban_logger', 
            'connection_tracker',
            'dns_manager',
            'adblock_manager'
        ]
    
    async def initialize_services(self) -> bool:
        """Initialize all enabled services"""
        try:
            logger.info("Initializing enhanced services...")
            
            # Initialize services in order
            for service_name in self.startup_order:
                if await self._initialize_service(service_name):
                    logger.info(f"✓ {service_name} initialized successfully")
                else:
                    logger.warning(f"✗ {service_name} initialization failed")
            
            self.initialized = True
            logger.info("Enhanced services initialization completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            return False
    
    async def _initialize_service(self, service_name: str) -> bool:
        """Initialize a specific service"""
        try:
            if service_name == 'two_factor_auth' and TWO_FACTOR_AUTH_ENABLED:
                success = two_factor_service.initialize()
                if success:
                    self.services['two_factor_auth'] = two_factor_service
                return success
            
            elif service_name == 'fail2ban_logger' and FAIL2BAN_ENABLED:
                success = fail2ban_logger.initialize()
                if success:
                    self.services['fail2ban_logger'] = fail2ban_logger
                return success
            
            elif service_name == 'connection_tracker' and CONNECTION_LIMIT_ENABLED:
                success = connection_tracker.initialize()
                if success:
                    self.services['connection_tracker'] = connection_tracker
                return success
            
            elif service_name == 'dns_manager' and DNS_OVERRIDE_ENABLED:
                success = dns_manager.initialize()
                if success:
                    self.services['dns_manager'] = dns_manager
                return success
            
            elif service_name == 'adblock_manager' and ADBLOCK_ENABLED:
                success = adblock_manager.initialize()
                if success:
                    self.services['adblock_manager'] = adblock_manager
                return success
            
            else:
                # Service is disabled
                logger.info(f"Service {service_name} is disabled")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize {service_name}: {e}")
            return False
    
    async def cleanup_services(self) -> bool:
        """Cleanup all services"""
        try:
            logger.info("Cleaning up enhanced services...")
            
            # Cleanup in reverse order
            for service_name in reversed(self.startup_order):
                if service_name in self.services:
                    service = self.services[service_name]
                    if hasattr(service, 'cleanup'):
                        try:
                            service.cleanup()
                            logger.info(f"✓ {service_name} cleaned up")
                        except Exception as e:
                            logger.error(f"✗ Failed to cleanup {service_name}: {e}")
            
            self.services.clear()
            self.initialized = False
            logger.info("Enhanced services cleanup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup services: {e}")
            return False
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """Get a specific service instance"""
        return self.services.get(service_name)
    
    def is_service_running(self, service_name: str) -> bool:
        """Check if a service is running"""
        service = self.services.get(service_name)
        if service and hasattr(service, 'initialized'):
            return service.initialized
        return False
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get status of a specific service"""
        service = self.services.get(service_name)
        
        if not service:
            return {
                'name': service_name,
                'enabled': False,
                'running': False,
                'initialized': False,
                'status': 'not_loaded'
            }
        
        status = {
            'name': service_name,
            'enabled': True,
            'running': hasattr(service, 'initialized') and service.initialized,
            'initialized': hasattr(service, 'initialized') and service.initialized,
            'status': 'running' if (hasattr(service, 'initialized') and service.initialized) else 'stopped'
        }
        
        # Add service-specific status if available
        if hasattr(service, 'get_status'):
            try:
                service_status = service.get_status()
                status.update(service_status)
            except Exception as e:
                status['error'] = str(e)
        
        return status
    
    def get_all_services_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        services_status = {}
        
        for service_name in self.startup_order:
            services_status[service_name] = self.get_service_status(service_name)
        
        return {
            'manager_initialized': self.initialized,
            'services': services_status,
            'total_services': len(self.startup_order),
            'running_services': sum(1 for status in services_status.values() if status['running']),
            'last_check': datetime.utcnow()
        }
    
    async def restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        try:
            logger.info(f"Restarting service: {service_name}")
            
            # Cleanup existing service
            if service_name in self.services:
                service = self.services[service_name]
                if hasattr(service, 'cleanup'):
                    service.cleanup()
                del self.services[service_name]
            
            # Reinitialize service
            success = await self._initialize_service(service_name)
            
            if success:
                logger.info(f"Service {service_name} restarted successfully")
            else:
                logger.error(f"Failed to restart service {service_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error restarting service {service_name}: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services"""
        health_status = {
            'overall_health': 'healthy',
            'manager_status': 'running' if self.initialized else 'stopped',
            'services': {},
            'issues': [],
            'timestamp': datetime.utcnow()
        }
        
        unhealthy_count = 0
        
        for service_name in self.startup_order:
            service = self.services.get(service_name)
            service_health = {
                'status': 'unknown',
                'enabled': False,
                'last_check': datetime.utcnow()
            }
            
            try:
                # Check if service is enabled
                enabled_map = {
                    'two_factor_auth': TWO_FACTOR_AUTH_ENABLED,
                    'fail2ban_logger': FAIL2BAN_ENABLED,
                    'connection_tracker': CONNECTION_LIMIT_ENABLED,
                    'dns_manager': DNS_OVERRIDE_ENABLED,
                    'adblock_manager': ADBLOCK_ENABLED
                }
                
                service_health['enabled'] = enabled_map.get(service_name, False)
                
                if not service_health['enabled']:
                    service_health['status'] = 'disabled'
                elif not service:
                    service_health['status'] = 'not_loaded'
                    health_status['issues'].append(f"Service {service_name} is not loaded")
                    unhealthy_count += 1
                elif hasattr(service, 'health_check'):
                    # Service has its own health check
                    is_healthy = service.health_check()
                    service_health['status'] = 'healthy' if is_healthy else 'unhealthy'
                    if not is_healthy:
                        health_status['issues'].append(f"Service {service_name} failed health check")
                        unhealthy_count += 1
                elif hasattr(service, 'initialized'):
                    # Check if service is initialized
                    service_health['status'] = 'healthy' if service.initialized else 'unhealthy'
                    if not service.initialized:
                        health_status['issues'].append(f"Service {service_name} is not initialized")
                        unhealthy_count += 1
                else:
                    service_health['status'] = 'unknown'
                    health_status['issues'].append(f"Service {service_name} status unknown")
                
            except Exception as e:
                service_health['status'] = 'error'
                service_health['error'] = str(e)
                health_status['issues'].append(f"Service {service_name} health check error: {str(e)}")
                unhealthy_count += 1
            
            health_status['services'][service_name] = service_health
        
        # Determine overall health
        if unhealthy_count == 0:
            health_status['overall_health'] = 'healthy'
        elif unhealthy_count <= 2:
            health_status['overall_health'] = 'degraded'
        else:
            health_status['overall_health'] = 'unhealthy'
        
        return health_status
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Get metrics from all services"""
        metrics = {
            'timestamp': datetime.utcnow(),
            'services': {}
        }
        
        for service_name, service in self.services.items():
            service_metrics = {}
            
            try:
                if hasattr(service, 'get_metrics'):
                    service_metrics = service.get_metrics()
                elif hasattr(service, 'get_statistics'):
                    service_metrics = service.get_statistics()
                
                metrics['services'][service_name] = service_metrics
                
            except Exception as e:
                metrics['services'][service_name] = {'error': str(e)}
        
        return metrics


# Global service manager instance
service_manager = ServiceManager()
