"""
Two-Factor Authentication Service for Enhanced Marzban
Provides Google Authenticator compatible TOTP authentication
"""

import pyotp
import qrcode
import io
import base64
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.db.models_enhanced import AdminTwoFactor, AdminLoginAttempt, AdminSession
from app.db import get_db
from app.services.base_service import ConfigurableService
from config import TWO_FACTOR_ISSUER_NAME, TWO_FACTOR_BACKUP_CODES_COUNT


class TwoFactorAuthService(ConfigurableService):
    """Service for managing Two-Factor Authentication"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.issuer_name = self.get_config('issuer_name', TWO_FACTOR_ISSUER_NAME)
        self.backup_codes_count = self.get_config('backup_codes_count', TWO_FACTOR_BACKUP_CODES_COUNT)
    
    def initialize(self) -> bool:
        """Initialize the 2FA service"""
        try:
            self.log_info("Initializing Two-Factor Authentication service")
            self._initialized = True
            return True
        except Exception as e:
            self.log_error(f"Failed to initialize 2FA service: {str(e)}")
            return False
    
    def cleanup(self) -> bool:
        """Cleanup 2FA service resources"""
        try:
            self.log_info("Cleaning up Two-Factor Authentication service")
            return True
        except Exception as e:
            self.log_error(f"Failed to cleanup 2FA service: {str(e)}")
            return False
    
    def generate_secret(self) -> str:
        """Generate a new TOTP secret key"""
        return pyotp.random_base32()
    
    def generate_backup_codes(self) -> List[str]:
        """Generate backup codes for 2FA"""
        codes = []
        for _ in range(self.backup_codes_count):
            # Generate 8-character alphanumeric codes
            code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
            codes.append(code)
        return codes
    
    def generate_qr_code(self, secret: str, username: str) -> str:
        """Generate QR code for Google Authenticator setup"""
        try:
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=username,
                issuer_name=self.issuer_name
            )
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64 string
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            self.log_error(f"Failed to generate QR code: {str(e)}")
            return ""
    
    def setup_2fa(self, admin_id: int) -> Tuple[str, str, List[str]]:
        """Setup 2FA for an admin user"""
        try:
            with self.get_db_session() as db:
                # Check if 2FA already exists
                existing_2fa = db.query(AdminTwoFactor).filter(
                    AdminTwoFactor.admin_id == admin_id
                ).first()
                
                if existing_2fa:
                    # Update existing setup
                    secret = self.generate_secret()
                    backup_codes = self.generate_backup_codes()
                    
                    existing_2fa.secret_key = secret
                    existing_2fa.backup_codes = json.dumps(backup_codes)
                    existing_2fa.is_enabled = False  # Require verification to enable
                    
                else:
                    # Create new 2FA setup
                    secret = self.generate_secret()
                    backup_codes = self.generate_backup_codes()
                    
                    two_fa = AdminTwoFactor(
                        admin_id=admin_id,
                        secret_key=secret,
                        backup_codes=json.dumps(backup_codes),
                        is_enabled=False
                    )
                    db.add(two_fa)
                
                db.commit()
                
                # Get admin username for QR code
                from app.db.models import Admin
                admin = db.query(Admin).filter(Admin.id == admin_id).first()
                username = admin.username if admin else f"admin_{admin_id}"
                
                qr_code = self.generate_qr_code(secret, username)
                
                self.log_info(f"2FA setup initiated for admin {username}")
                return secret, qr_code, backup_codes
                
        except Exception as e:
            self.log_error(f"Failed to setup 2FA: {str(e)}")
            raise
    
    def verify_and_enable_2fa(self, admin_id: int, token: str) -> bool:
        """Verify setup token and enable 2FA"""
        try:
            with self.get_db_session() as db:
                two_fa = db.query(AdminTwoFactor).filter(
                    AdminTwoFactor.admin_id == admin_id
                ).first()
                
                if not two_fa:
                    return False
                
                # Verify token
                totp = pyotp.TOTP(two_fa.secret_key)
                if totp.verify(token, valid_window=1):
                    two_fa.is_enabled = True
                    db.commit()
                    
                    self.log_info(f"2FA enabled for admin {admin_id}")
                    return True
                
                return False
                
        except Exception as e:
            self.log_error(f"Failed to verify and enable 2FA: {str(e)}")
            return False
    
    def disable_2fa(self, admin_id: int) -> bool:
        """Disable 2FA for an admin"""
        try:
            with self.get_db_session() as db:
                two_fa = db.query(AdminTwoFactor).filter(
                    AdminTwoFactor.admin_id == admin_id
                ).first()
                
                if two_fa:
                    two_fa.is_enabled = False
                    db.commit()
                    
                    self.log_info(f"2FA disabled for admin {admin_id}")
                    return True
                
                return False
                
        except Exception as e:
            self.log_error(f"Failed to disable 2FA: {str(e)}")
            return False
    
    def is_2fa_enabled(self, admin_id: int) -> bool:
        """Check if 2FA is enabled for an admin"""
        try:
            with self.get_db_session() as db:
                two_fa = db.query(AdminTwoFactor).filter(
                    AdminTwoFactor.admin_id == admin_id,
                    AdminTwoFactor.is_enabled == True
                ).first()
                
                return two_fa is not None
                
        except Exception as e:
            self.log_error(f"Failed to check 2FA status: {str(e)}")
            return False
    
    def verify_token(self, admin_id: int, token: str) -> bool:
        """Verify TOTP token for login"""
        try:
            with self.get_db_session() as db:
                two_fa = db.query(AdminTwoFactor).filter(
                    AdminTwoFactor.admin_id == admin_id,
                    AdminTwoFactor.is_enabled == True
                ).first()
                
                if not two_fa:
                    return False
                
                # Check if it's a backup code
                if len(token) == 8 and token.isalnum():
                    return self._verify_backup_code(db, two_fa, token)
                
                # Verify TOTP token
                totp = pyotp.TOTP(two_fa.secret_key)
                if totp.verify(token, valid_window=1):
                    two_fa.last_used = datetime.utcnow()
                    db.commit()
                    return True
                
                return False
                
        except Exception as e:
            self.log_error(f"Failed to verify token: {str(e)}")
            return False
    
    def _verify_backup_code(self, db: Session, two_fa: AdminTwoFactor, code: str) -> bool:
        """Verify and consume a backup code"""
        try:
            backup_codes = json.loads(two_fa.backup_codes or '[]')
            
            if code.upper() in backup_codes:
                # Remove used backup code
                backup_codes.remove(code.upper())
                two_fa.backup_codes = json.dumps(backup_codes)
                two_fa.last_used = datetime.utcnow()
                db.commit()
                
                self.log_info(f"Backup code used for admin {two_fa.admin_id}")
                return True
            
            return False
            
        except Exception as e:
            self.log_error(f"Failed to verify backup code: {str(e)}")
            return False
    
    def get_backup_codes(self, admin_id: int) -> List[str]:
        """Get remaining backup codes for an admin"""
        try:
            with self.get_db_session() as db:
                two_fa = db.query(AdminTwoFactor).filter(
                    AdminTwoFactor.admin_id == admin_id,
                    AdminTwoFactor.is_enabled == True
                ).first()
                
                if two_fa and two_fa.backup_codes:
                    return json.loads(two_fa.backup_codes)
                
                return []
                
        except Exception as e:
            self.log_error(f"Failed to get backup codes: {str(e)}")
            return []
    
    def regenerate_backup_codes(self, admin_id: int) -> List[str]:
        """Regenerate backup codes for an admin"""
        try:
            with self.get_db_session() as db:
                two_fa = db.query(AdminTwoFactor).filter(
                    AdminTwoFactor.admin_id == admin_id,
                    AdminTwoFactor.is_enabled == True
                ).first()
                
                if two_fa:
                    backup_codes = self.generate_backup_codes()
                    two_fa.backup_codes = json.dumps(backup_codes)
                    db.commit()
                    
                    self.log_info(f"Backup codes regenerated for admin {admin_id}")
                    return backup_codes
                
                return []
                
        except Exception as e:
            self.log_error(f"Failed to regenerate backup codes: {str(e)}")
            return []


    def get_statistics(self) -> dict:
        """Get 2FA usage statistics"""
        try:
            with self.get_db_session() as db:
                from app.db.models import Admin

                total_admins = db.query(Admin).count()
                enabled_2fa = db.query(AdminTwoFactor).filter(
                    AdminTwoFactor.is_enabled == True
                ).count()

                return {
                    "total_admins": total_admins,
                    "enabled_2fa": enabled_2fa,
                    "adoption_rate": round((enabled_2fa / total_admins * 100), 2) if total_admins > 0 else 0
                }
        except Exception as e:
            self.log_error(f"Failed to get 2FA statistics: {str(e)}")
            return {
                "total_admins": 0,
                "enabled_2fa": 0,
                "adoption_rate": 0,
                "error": str(e)
            }

# Global instance
two_factor_service = TwoFactorAuthService()
