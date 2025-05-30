"""
Fail2ban integration API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.db import get_db, Session
from app.models.admin import Admin
from app.services.fail2ban_logger import fail2ban_logger
from app.services.connection_tracker import connection_tracker
from app.db.models import User
from app.db.models_enhanced import TrafficViolation
from config import FAIL2BAN_ENABLED


router = APIRouter(prefix="/api/fail2ban", tags=["Fail2ban Integration"])


# Pydantic models
class Fail2banActionRequest(BaseModel):
    action: str  # ban, unban
    ip_address: str
    username: str
    reason: str
    duration: Optional[int] = 3600  # seconds


class TrafficViolationResponse(BaseModel):
    id: int
    user_id: int
    username: str
    violation_type: str
    ip_address: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime
    resolved: bool
    resolved_at: Optional[datetime] = None


class Fail2banStatsResponse(BaseModel):
    enabled: bool
    total_violations: int
    violations_last_24h: int
    violations_last_7d: int
    top_violators: List[Dict[str, Any]]
    violation_types: Dict[str, int]


class Fail2banConfigResponse(BaseModel):
    jail_config: str
    filter_config: str
    log_path: str
    max_violations: int


# Dependency to check if Fail2ban is enabled
def check_fail2ban_enabled():
    if not FAIL2BAN_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Fail2ban integration is disabled"
        )


@router.get("/status")
async def get_fail2ban_status(
    admin: Admin = Depends(Admin.get_current),
    _: None = Depends(check_fail2ban_enabled)
):
    """Get Fail2ban service status"""
    return {
        "enabled": fail2ban_logger.enabled,
        "initialized": fail2ban_logger.initialized,
        "torrent_detection": fail2ban_logger.torrent_detection,
        "traffic_analysis": fail2ban_logger.traffic_analysis,
        "log_file_path": fail2ban_logger.log_file_path,
        "max_violations": fail2ban_logger.max_violations
    }


@router.get("/statistics", response_model=Fail2banStatsResponse)
async def get_fail2ban_statistics(
    admin: Admin = Depends(Admin.get_current),
    db: Session = Depends(get_db),
    _: None = Depends(check_fail2ban_enabled)
):
    """Get Fail2ban statistics"""
    try:
        # Get violation counts
        total_violations = db.query(TrafficViolation).count()
        
        # Violations in last 24 hours
        last_24h = datetime.utcnow() - timedelta(hours=24)
        violations_24h = db.query(TrafficViolation).filter(
            TrafficViolation.created_at >= last_24h
        ).count()
        
        # Violations in last 7 days
        last_7d = datetime.utcnow() - timedelta(days=7)
        violations_7d = db.query(TrafficViolation).filter(
            TrafficViolation.created_at >= last_7d
        ).count()
        
        # Top violators (users with most violations)
        top_violators_query = db.query(
            User.username,
            User.fail2ban_violations,
            User.last_violation_at
        ).filter(
            User.fail2ban_violations > 0
        ).order_by(
            User.fail2ban_violations.desc()
        ).limit(10).all()
        
        top_violators = [
            {
                "username": username,
                "violation_count": violations,
                "last_violation": last_violation
            }
            for username, violations, last_violation in top_violators_query
        ]
        
        # Violation types breakdown
        violation_types_query = db.query(
            TrafficViolation.violation_type,
            db.func.count(TrafficViolation.id).label('count')
        ).group_by(TrafficViolation.violation_type).all()
        
        violation_types = {
            violation_type: count
            for violation_type, count in violation_types_query
        }
        
        return Fail2banStatsResponse(
            enabled=fail2ban_logger.enabled,
            total_violations=total_violations,
            violations_last_24h=violations_24h,
            violations_last_7d=violations_7d,
            top_violators=top_violators,
            violation_types=violation_types
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/violations", response_model=List[TrafficViolationResponse])
async def get_violations(
    limit: int = 100,
    offset: int = 0,
    user_id: Optional[int] = None,
    violation_type: Optional[str] = None,
    resolved: Optional[bool] = None,
    admin: Admin = Depends(Admin.get_current),
    db: Session = Depends(get_db),
    _: None = Depends(check_fail2ban_enabled)
):
    """Get traffic violations with filtering"""
    try:
        query = db.query(TrafficViolation).join(User)
        
        # Apply filters
        if user_id:
            query = query.filter(TrafficViolation.user_id == user_id)
        
        if violation_type:
            query = query.filter(TrafficViolation.violation_type == violation_type)
        
        if resolved is not None:
            query = query.filter(TrafficViolation.resolved == resolved)
        
        # Order by creation time (newest first)
        query = query.order_by(TrafficViolation.created_at.desc())
        
        # Apply pagination
        violations = query.offset(offset).limit(limit).all()
        
        # Convert to response format
        result = []
        for violation in violations:
            details = None
            if violation.details:
                try:
                    import json
                    details = json.loads(violation.details)
                except:
                    details = {"raw": violation.details}
            
            result.append(TrafficViolationResponse(
                id=violation.id,
                user_id=violation.user_id,
                username=violation.user.username,
                violation_type=violation.violation_type,
                ip_address=violation.ip_address,
                details=details,
                created_at=violation.created_at,
                resolved=violation.resolved,
                resolved_at=violation.resolved_at
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get violations: {str(e)}"
        )


@router.post("/action")
async def handle_fail2ban_action(
    action: Fail2banActionRequest,
    admin: Admin = Depends(Admin.check_sudo_admin),
    db: Session = Depends(get_db),
    _: None = Depends(check_fail2ban_enabled)
):
    """Handle Fail2ban action (ban/unban user)"""
    try:
        # Find user by username
        user = db.query(User).filter(User.username == action.username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {action.username} not found"
            )
        
        if action.action == "ban":
            # Record violation
            violation = TrafficViolation(
                user_id=user.id,
                violation_type="fail2ban_ban",
                ip_address=action.ip_address,
                details=json.dumps({
                    "reason": action.reason,
                    "duration": action.duration
                })
            )
            db.add(violation)
            
            # Increment violation count
            user.fail2ban_violations += 1
            user.last_violation_at = datetime.utcnow()
            
            # Force disconnect user connections
            connection_tracker.force_disconnect_user(user.id, "fail2ban_ban")
            
            fail2ban_logger.log_user_suspended(action.ip_address, user.username, action.reason)
            
        elif action.action == "unban":
            # Log unban action
            fail2ban_logger.log_info(f"User {user.username} unbanned from {action.ip_address}")
        
        db.commit()
        
        return {
            "status": "success",
            "action": action.action,
            "username": action.username,
            "ip_address": action.ip_address,
            "message": f"User {action.action}ned successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle action: {str(e)}"
        )


@router.post("/violations/{violation_id}/resolve")
async def resolve_violation(
    violation_id: int,
    admin: Admin = Depends(Admin.get_current),
    db: Session = Depends(get_db),
    _: None = Depends(check_fail2ban_enabled)
):
    """Mark a violation as resolved"""
    try:
        violation = db.query(TrafficViolation).filter(
            TrafficViolation.id == violation_id
        ).first()
        
        if not violation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Violation not found"
            )
        
        violation.resolved = True
        violation.resolved_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": "success",
            "message": "Violation marked as resolved",
            "violation_id": violation_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve violation: {str(e)}"
        )


@router.get("/config", response_model=Fail2banConfigResponse)
async def get_fail2ban_config(
    admin: Admin = Depends(Admin.check_sudo_admin),
    _: None = Depends(check_fail2ban_enabled)
):
    """Get Fail2ban configuration files"""
    try:
        jail_config = fail2ban_logger.create_fail2ban_config()
        filter_config = fail2ban_logger.create_fail2ban_filter()
        
        return Fail2banConfigResponse(
            jail_config=jail_config,
            filter_config=filter_config,
            log_path=fail2ban_logger.log_file_path,
            max_violations=fail2ban_logger.max_violations
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.post("/test-detection")
async def test_torrent_detection(
    test_data: str,
    admin: Admin = Depends(Admin.check_sudo_admin),
    _: None = Depends(check_fail2ban_enabled)
):
    """Test torrent detection with sample data"""
    try:
        # Convert hex string to bytes for testing
        if test_data.startswith('0x'):
            test_data = test_data[2:]
        
        try:
            data_bytes = bytes.fromhex(test_data)
        except ValueError:
            data_bytes = test_data.encode('utf-8')
        
        is_torrent = fail2ban_logger.detect_torrent_traffic(data_bytes)
        
        return {
            "is_torrent_traffic": is_torrent,
            "data_length": len(data_bytes),
            "detection_enabled": fail2ban_logger.torrent_detection
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test detection: {str(e)}"
        )


@router.get("/logs/tail")
async def tail_fail2ban_logs(
    lines: int = 100,
    admin: Admin = Depends(Admin.check_sudo_admin),
    _: None = Depends(check_fail2ban_enabled)
):
    """Get last N lines from Fail2ban log file"""
    try:
        import os
        
        if not os.path.exists(fail2ban_logger.log_file_path):
            return {"lines": [], "message": "Log file not found"}
        
        with open(fail2ban_logger.log_file_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            tail_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "lines": [line.strip() for line in tail_lines],
            "total_lines": len(all_lines),
            "showing_lines": len(tail_lines)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read log file: {str(e)}"
        )
