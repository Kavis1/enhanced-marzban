"""
Enhanced features management API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.models.admin import Admin
from app.services.service_manager import service_manager


router = APIRouter(prefix="/api/enhanced", tags=["Enhanced Features"])


# Pydantic models
class ServiceStatusResponse(BaseModel):
    name: str
    enabled: bool
    running: bool
    initialized: bool
    status: str
    error: Optional[str] = None


class AllServicesStatusResponse(BaseModel):
    manager_initialized: bool
    services: Dict[str, ServiceStatusResponse]
    total_services: int
    running_services: int
    last_check: datetime


class HealthCheckResponse(BaseModel):
    overall_health: str
    manager_status: str
    services: Dict[str, Dict[str, Any]]
    issues: List[str]
    timestamp: datetime


class ServiceMetricsResponse(BaseModel):
    timestamp: datetime
    services: Dict[str, Dict[str, Any]]


@router.get("/status", response_model=AllServicesStatusResponse)
async def get_enhanced_services_status(
    admin: Admin = Depends(Admin.get_current)
):
    """Get status of all enhanced services"""
    try:
        status_data = service_manager.get_all_services_status()

        # Convert services dict to proper response format
        services_response = {}
        for service_name, service_status in status_data['services'].items():
            services_response[service_name] = ServiceStatusResponse(**service_status)

        return AllServicesStatusResponse(
            manager_initialized=status_data['manager_initialized'],
            services=services_response,
            total_services=status_data['total_services'],
            running_services=status_data['running_services'],
            last_check=status_data['last_check']
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get services status: {str(e)}"
        )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check_enhanced_services(
    admin: Admin = Depends(Admin.get_current)
):
    """Perform health check on all enhanced services"""
    try:
        health_data = await service_manager.health_check()
        return HealthCheckResponse(**health_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform health check: {str(e)}"
        )


@router.get("/metrics", response_model=ServiceMetricsResponse)
async def get_enhanced_services_metrics(
    admin: Admin = Depends(Admin.get_current)
):
    """Get metrics from all enhanced services"""
    try:
        metrics_data = service_manager.get_service_metrics()
        return ServiceMetricsResponse(**metrics_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get services metrics: {str(e)}"
        )


@router.get("/services/{service_name}/status")
async def get_service_status(
    service_name: str,
    admin: Admin = Depends(Admin.get_current)
):
    """Get status of a specific service"""
    try:
        status_data = service_manager.get_service_status(service_name)
        return ServiceStatusResponse(**status_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service status: {str(e)}"
        )


@router.post("/services/{service_name}/restart")
async def restart_service(
    service_name: str,
    admin: Admin = Depends(Admin.check_sudo_admin)
):
    """Restart a specific enhanced service"""
    try:
        # Validate service name
        valid_services = [
            'two_factor_auth', 'fail2ban_logger', 'connection_tracker',
            'dns_manager', 'adblock_manager'
        ]

        if service_name not in valid_services:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid service name. Valid services: {', '.join(valid_services)}"
            )

        success = await service_manager.restart_service(service_name)

        if success:
            return {
                "status": "success",
                "message": f"Service {service_name} restarted successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to restart service {service_name}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error restarting service: {str(e)}"
        )


@router.post("/initialize")
async def initialize_enhanced_services(
    admin: Admin = Depends(Admin.check_sudo_admin)
):
    """Initialize all enhanced services"""
    try:
        success = await service_manager.initialize_services()

        if success:
            return {
                "status": "success",
                "message": "Enhanced services initialized successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize enhanced services"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing services: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_enhanced_services(
    admin: Admin = Depends(Admin.check_sudo_admin)
):
    """Cleanup all enhanced services"""
    try:
        success = await service_manager.cleanup_services()

        if success:
            return {
                "status": "success",
                "message": "Enhanced services cleaned up successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cleanup enhanced services"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up services: {str(e)}"
        )


@router.get("/config")
async def get_enhanced_features_config(
    admin: Admin = Depends(Admin.get_current)
):
    """Get configuration status of all enhanced features"""
    try:
        from config import (
            TWO_FACTOR_AUTH_ENABLED, FAIL2BAN_ENABLED, CONNECTION_LIMIT_ENABLED,
            DNS_OVERRIDE_ENABLED, ADBLOCK_ENABLED, DEFAULT_MAX_CONNECTIONS,
            FAIL2BAN_LOG_PATH, FAIL2BAN_MAX_VIOLATIONS, DNS_OVERRIDE_SERVERS,
            ADBLOCK_UPDATE_INTERVAL
        )

        config_data = {
            "two_factor_auth": {
                "enabled": TWO_FACTOR_AUTH_ENABLED,
                "description": "Two-Factor Authentication for admin accounts"
            },
            "fail2ban_integration": {
                "enabled": FAIL2BAN_ENABLED,
                "log_path": FAIL2BAN_LOG_PATH,
                "max_violations": FAIL2BAN_MAX_VIOLATIONS,
                "description": "Traffic monitoring and automatic user suspension"
            },
            "connection_limiting": {
                "enabled": CONNECTION_LIMIT_ENABLED,
                "default_max_connections": DEFAULT_MAX_CONNECTIONS,
                "description": "Limit simultaneous connections per user"
            },
            "dns_override": {
                "enabled": DNS_OVERRIDE_ENABLED,
                "dns_servers": DNS_OVERRIDE_SERVERS,
                "description": "Custom DNS rules and domain redirection"
            },
            "ad_blocking": {
                "enabled": ADBLOCK_ENABLED,
                "update_interval": ADBLOCK_UPDATE_INTERVAL,
                "description": "Ad-blocking for users and nodes"
            }
        }

        return {
            "enhanced_features": config_data,
            "manager_initialized": service_manager.initialized,
            "total_features": len(config_data),
            "enabled_features": sum(1 for feature in config_data.values() if feature["enabled"])
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.get("/stats")
async def get_enhanced_stats():
    """Get Enhanced Marzban statistics for dashboard - public endpoint"""
    try:
        from app.db import GetDB
        from app.db.models import User
        from app.db.models_enhanced import AdminLoginAttempt, TrafficViolation

        with GetDB() as db:
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.status == "active").count()

            from datetime import timedelta
            yesterday = datetime.utcnow() - timedelta(days=1)
            try:
                recent_attempts = db.query(AdminLoginAttempt).filter(
                    AdminLoginAttempt.timestamp >= yesterday
                ).count()
            except Exception:
                recent_attempts = 0

            try:
                fail2ban_bans = db.query(TrafficViolation).filter(
                    TrafficViolation.violation_type == "fail2ban_ban",
                    TrafficViolation.created_at >= yesterday
                ).count()
            except Exception:
                fail2ban_bans = 0

            metrics = service_manager.get_service_metrics()
            adblock_stats = metrics.get("services", {}).get("adblock_manager", {})
            blocked_threats = adblock_stats.get("total_blocked_domains", 0)

            health = await service_manager.health_check()
            performance_score = 100 - (len(health.get("issues", [])) * 10)

            return {
                "blocked_threats": blocked_threats,
                "active_connections": active_users,
                "fail2ban_bans": fail2ban_bans,
                "performance_score": performance_score,
                "total_users": total_users,
                "active_users": active_users,
                "recent_login_attempts": recent_attempts
            }

    except Exception as e:
        return {
            "blocked_threats": 0,
            "active_connections": 0,
            "fail2ban_bans": 0,
            "performance_score": 0,
            "total_users": 0,
            "active_users": 0,
            "recent_login_attempts": 0,
            "error": str(e)
        }




@router.get("/overview")
async def get_enhanced_features_overview(
    admin: Admin = Depends(Admin.get_current)
):
    """Get overview of all enhanced features"""
    try:
        # Get service status
        services_status = service_manager.get_all_services_status()

        # Get health check
        health_data = await service_manager.health_check()

        # Get basic metrics
        metrics_data = service_manager.get_service_metrics()

        overview = {
            "summary": {
                "total_services": services_status['total_services'],
                "running_services": services_status['running_services'],
                "overall_health": health_data['overall_health'],
                "manager_initialized": services_status['manager_initialized']
            },
            "services": services_status['services'],
            "health": {
                "status": health_data['overall_health'],
                "issues_count": len(health_data['issues']),
                "issues": health_data['issues'][:5]  # Show only first 5 issues
            },
            "last_updated": datetime.utcnow()
        }

        return overview

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get overview: {str(e)}"
        )
