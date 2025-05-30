"""
Base service class for enhanced features
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.db import get_db

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """Base class for all enhanced services"""
    
    def __init__(self):
        self.logger = logger
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the service"""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """Cleanup service resources"""
        pass
    
    def get_db_session(self) -> Session:
        """Get database session"""
        return get_db()
    
    def log_info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(f"[{self.__class__.__name__}] {message}", extra=kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(f"[{self.__class__.__name__}] {message}", extra=kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(f"[{self.__class__.__name__}] {message}", extra=kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(f"[{self.__class__.__name__}] {message}", extra=kwargs)
    
    @property
    def initialized(self) -> bool:
        """Check if service is initialized"""
        return self._initialized
    
    def safe_execute(self, func, *args, **kwargs) -> Optional[Any]:
        """Safely execute a function with error handling"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.log_error(f"Error executing {func.__name__}: {str(e)}")
            return None


class ConfigurableService(BaseService):
    """Base class for services with configuration"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__()
        self.config = config or {}
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
    
    def update_config(self, config: Dict[str, Any]):
        """Update configuration"""
        self.config.update(config)


class ScheduledService(ConfigurableService):
    """Base class for services that run on schedule"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.scheduler = None
        self.job_id = None
    
    @abstractmethod
    def run_scheduled_task(self):
        """Run the scheduled task"""
        pass
    
    def start_scheduler(self, interval: int):
        """Start the scheduler"""
        from app import scheduler
        self.scheduler = scheduler
        
        if self.job_id:
            self.stop_scheduler()
        
        self.job_id = f"{self.__class__.__name__}_job"
        self.scheduler.add_job(
            self.run_scheduled_task,
            'interval',
            seconds=interval,
            id=self.job_id,
            coalesce=True,
            max_instances=1
        )
        self.log_info(f"Scheduler started with {interval}s interval")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if self.scheduler and self.job_id:
            try:
                self.scheduler.remove_job(self.job_id)
                self.log_info("Scheduler stopped")
            except Exception as e:
                self.log_error(f"Failed to stop scheduler: {str(e)}")
            finally:
                self.job_id = None


class DatabaseService(ConfigurableService):
    """Base class for services that work with database"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
    
    def execute_query(self, query_func, *args, **kwargs):
        """Execute a database query with error handling"""
        try:
            with self.get_db_session() as db:
                return query_func(db, *args, **kwargs)
        except Exception as e:
            self.log_error(f"Database query failed: {str(e)}")
            return None
    
    def execute_transaction(self, transaction_func, *args, **kwargs):
        """Execute a database transaction with error handling"""
        try:
            with self.get_db_session() as db:
                result = transaction_func(db, *args, **kwargs)
                db.commit()
                return result
        except Exception as e:
            self.log_error(f"Database transaction failed: {str(e)}")
            return None


class CacheableService(ConfigurableService):
    """Base class for services with caching capabilities"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.cache = {}
        self.cache_ttl = self.get_config('cache_ttl', 300)  # 5 minutes default
    
    def get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            value, expires_at = self.cache[key]
            if expires_at > self._get_current_timestamp():
                return value
            else:
                del self.cache[key]
        return None
    
    def set_cache(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        ttl = ttl or self.cache_ttl
        expires_at = self._get_current_timestamp() + ttl
        self.cache[key] = (value, expires_at)
    
    def clear_cache(self, pattern: Optional[str] = None):
        """Clear cache entries"""
        if pattern:
            keys_to_remove = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.cache[key]
        else:
            self.cache.clear()
    
    def cleanup_expired_cache(self):
        """Remove expired cache entries"""
        current_time = self._get_current_timestamp()
        expired_keys = [
            key for key, (_, expires_at) in self.cache.items()
            if expires_at <= current_time
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def _get_current_timestamp(self) -> int:
        """Get current timestamp"""
        from datetime import datetime
        return int(datetime.utcnow().timestamp())


class MonitoredService(ConfigurableService):
    """Base class for services with monitoring capabilities"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.metrics = {}
        self.last_health_check = None
        self.health_status = "unknown"
    
    def record_metric(self, name: str, value: float, unit: str = None):
        """Record a performance metric"""
        from datetime import datetime
        self.metrics[name] = {
            'value': value,
            'unit': unit,
            'timestamp': datetime.utcnow()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all recorded metrics"""
        return self.metrics.copy()
    
    def health_check(self) -> bool:
        """Perform health check"""
        try:
            from datetime import datetime
            self.last_health_check = datetime.utcnow()
            
            # Override in subclasses for specific health checks
            is_healthy = self._perform_health_check()
            self.health_status = "healthy" if is_healthy else "unhealthy"
            
            return is_healthy
        except Exception as e:
            self.log_error(f"Health check failed: {str(e)}")
            self.health_status = "error"
            return False
    
    def _perform_health_check(self) -> bool:
        """Override in subclasses for specific health checks"""
        return self._initialized
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'initialized': self._initialized,
            'health_status': self.health_status,
            'last_health_check': self.last_health_check,
            'metrics': self.get_metrics()
        }
