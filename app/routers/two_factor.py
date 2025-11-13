"""
Two-Factor Authentication API Routes for Enhanced Marzban
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Optional
from app.services.two_factor_auth import two_factor_service
from app.db import get_db
from app.models.admin import Admin
from config import TWO_FACTOR_AUTH_ENABLED


router = APIRouter(prefix="/api/2fa", tags=["Two-Factor Authentication"])
security = HTTPBearer()


# Pydantic models
class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: List[str]
    message: str


class TwoFactorVerifyRequest(BaseModel):
    token: str


class TwoFactorStatusResponse(BaseModel):
    enabled: bool
    backup_codes_remaining: int


class TwoFactorBackupCodesResponse(BaseModel):
    backup_codes: List[str]
    message: str


# Dependency to check if 2FA is enabled globally
def check_2fa_enabled():
    if not TWO_FACTOR_AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Two-Factor Authentication is disabled"
        )


@router.get("/status")
async def get_2fa_status(
    current_admin: Admin = Depends(Admin.get_current),
    _: None = Depends(check_2fa_enabled)
):
    """
    Get 2FA status for current admin
    """
    is_enabled = two_factor_service.is_2fa_enabled(admin_id=current_admin.id)
    backup_codes = two_factor_service.get_backup_codes(admin_id=current_admin.id)
    
    return TwoFactorStatusResponse(
        enabled=is_enabled,
        backup_codes_remaining=len(backup_codes)
    )


@router.post("/setup", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    current_admin: Admin = Depends(Admin.get_current),
    _: None = Depends(check_2fa_enabled)
):
    """
    Setup 2FA for current admin
    Returns secret key, QR code, and backup codes
    """
    try:
        secret, qr_code, backup_codes = two_factor_service.setup_2fa(admin_id=current_admin.id)
        
        return TwoFactorSetupResponse(
            secret=secret,
            qr_code=qr_code,
            backup_codes=backup_codes,
            message="2FA setup initiated. Please verify with your authenticator app to enable."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup 2FA: {str(e)}"
        )


@router.post("/verify-setup")
async def verify_setup(
    request: TwoFactorVerifyRequest,
    current_admin: Admin = Depends(Admin.get_current),
    _: None = Depends(check_2fa_enabled)
):
    """
    Verify setup token and enable 2FA
    """
    success = two_factor_service.verify_and_enable_2fa(
        admin_id=current_admin.id,
        token=request.token
    )
    
    if success:
        return {"message": "2FA enabled successfully", "enabled": True}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )


@router.post("/disable")
async def disable_2fa(
    request: TwoFactorVerifyRequest,
    current_admin: Admin = Depends(Admin.get_current),
    _: None = Depends(check_2fa_enabled)
):
    """
    Disable 2FA for current admin
    Requires current 2FA token for security
    """
    # Verify current token before disabling
    if not two_factor_service.verify_token(current_admin.id, request.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA token"
        )
    
    success = two_factor_service.disable_2fa(admin_id=current_admin.id)
    
    if success:
        return {"message": "2FA disabled successfully", "enabled": False}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable 2FA"
        )


@router.get("/backup-codes", response_model=TwoFactorBackupCodesResponse)
async def get_backup_codes(
    current_admin: Admin = Depends(Admin.get_current),
    _: None = Depends(check_2fa_enabled)
):
    """
    Get remaining backup codes for current admin
    """
    if not two_factor_service.is_2fa_enabled(admin_id=current_admin.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled"
        )
    
    backup_codes = two_factor_service.get_backup_codes(admin_id=current_admin.id)
    
    return TwoFactorBackupCodesResponse(
        backup_codes=backup_codes,
        message=f"You have {len(backup_codes)} backup codes remaining"
    )


@router.post("/regenerate-backup-codes", response_model=TwoFactorBackupCodesResponse)
async def regenerate_backup_codes(
    request: TwoFactorVerifyRequest,
    current_admin: Admin = Depends(Admin.get_current),
    _: None = Depends(check_2fa_enabled)
):
    """
    Regenerate backup codes for current admin
    Requires current 2FA token for security
    """
    if not two_factor_service.is_2fa_enabled(admin_id=current_admin.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled"
        )
    
    # Verify current token before regenerating
    if not two_factor_service.verify_token(current_admin.id, request.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA token"
        )
    
    backup_codes = two_factor_service.regenerate_backup_codes(admin_id=current_admin.id)
    
    if backup_codes:
        return TwoFactorBackupCodesResponse(
            backup_codes=backup_codes,
            message="New backup codes generated. Please save them securely."
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate backup codes"
        )


@router.post("/verify-login")
async def verify_login_token(
    request: TwoFactorVerifyRequest,
    current_admin: Admin = Depends(Admin.get_current)
):
    """
    Verify 2FA token during login process
    """
    if not two_factor_service.is_2fa_enabled(admin_id=current_admin.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled for this user"
        )
    
    success = two_factor_service.verify_token(
        admin_id=current_admin.id,
        token=request.token
    )
    
    if success:
        return {"message": "2FA verification successful", "verified": True}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA token or backup code"
        )


# Admin-only endpoints for managing other users' 2FA
@router.get("/admin/users/{user_id}/status")
async def get_user_2fa_status(
    user_id: int,
    current_admin: Admin = Depends(Admin.check_sudo_admin),
    _: None = Depends(check_2fa_enabled)
):
    """
    Get 2FA status for a specific admin user (sudo admin only)
    """
    is_enabled = two_factor_service.is_2fa_enabled(admin_id=user_id)
    backup_codes = two_factor_service.get_backup_codes(admin_id=user_id)
    
    return TwoFactorStatusResponse(
        enabled=is_enabled,
        backup_codes_remaining=len(backup_codes)
    )


@router.post("/admin/users/{user_id}/disable")
async def admin_disable_user_2fa(
    user_id: int,
    current_admin: Admin = Depends(Admin.check_sudo_admin),
    _: None = Depends(check_2fa_enabled)
):
    """
    Disable 2FA for a specific admin user (sudo admin only)
    Emergency function for account recovery
    """
    success = two_factor_service.disable_2fa(admin_id=user_id)
    
    if success:
        return {"message": f"2FA disabled for user {user_id}", "enabled": False}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable 2FA"
        )


@router.get("/admin/stats")
async def get_2fa_statistics(
    current_admin: Admin = Depends(Admin.check_sudo_admin),
    _: None = Depends(check_2fa_enabled)
):
    """
    Get 2FA usage statistics (sudo admin only)
    """
    try:
        with two_factor_service.get_db_session() as db:
            from app.db.models_enhanced import AdminTwoFactor
            from app.db.models import Admin
            
            total_admins = db.query(Admin).count()
            enabled_2fa = db.query(AdminTwoFactor).filter(
                AdminTwoFactor.is_enabled == True
            ).count()
            setup_but_not_enabled = db.query(AdminTwoFactor).filter(
                AdminTwoFactor.is_enabled == False
            ).count()
            
            return {
                "total_admins": total_admins,
                "enabled_2fa": enabled_2fa,
                "setup_but_not_enabled": setup_but_not_enabled,
                "adoption_rate": round((enabled_2fa / total_admins * 100), 2) if total_admins > 0 else 0
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get 2FA statistics: {str(e)}"
        )
