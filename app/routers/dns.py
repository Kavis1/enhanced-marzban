"""
DNS override and management API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import ipaddress

from app.db import get_db, Session
from app.models.admin import Admin
from app.services.dns_manager import dns_manager
from app.db import crud
from app.db.models_enhanced import DNSRule, UserDNSRule
from config import DNS_OVERRIDE_ENABLED


router = APIRouter(prefix="/api/dns", tags=["DNS Management"])


# Pydantic models
class DNSRuleCreate(BaseModel):
    domain: str
    target_ip: str
    priority: int = 100
    description: Optional[str] = None
    
    @validator('target_ip')
    def validate_ip(cls, v):
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError('Invalid IP address')
    
    @validator('domain')
    def validate_domain(cls, v):
        if not v or len(v) > 253:
            raise ValueError('Invalid domain name')
        return v.lower()


class UserDNSRuleCreate(BaseModel):
    domain: str
    target_ip: str
    priority: int = 100
    
    @validator('target_ip')
    def validate_ip(cls, v):
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError('Invalid IP address')
    
    @validator('domain')
    def validate_domain(cls, v):
        if not v or len(v) > 253:
            raise ValueError('Invalid domain name')
        return v.lower()


class DNSRuleResponse(BaseModel):
    id: int
    domain: str
    target_ip: str
    priority: int
    is_enabled: bool
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserDNSRuleResponse(BaseModel):
    id: int
    user_id: int
    domain: str
    target_ip: str
    priority: int
    is_enabled: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class DNSResolveRequest(BaseModel):
    domain: str
    user_id: Optional[int] = None


class DNSResolveResponse(BaseModel):
    domain: str
    resolved_ip: Optional[str]
    rule_type: Optional[str]  # global, user, none
    cached: bool


# Dependency to check if DNS override is enabled
def check_dns_enabled():
    if not DNS_OVERRIDE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DNS override is disabled"
        )


@router.get("/status")
async def get_dns_status(
    admin: Admin = Depends(Admin.get_current),
    _: None = Depends(check_dns_enabled)
):
    """Get DNS service status"""
    return {
        "enabled": dns_manager.enabled,
        "initialized": dns_manager.initialized,
        "dns_servers": dns_manager.dns_servers,
        "cache_ttl": dns_manager.cache_ttl,
        "global_rules_count": len(dns_manager.global_rules_cache),
        "user_rules_count": sum(len(rules) for rules in dns_manager.user_rules_cache.values()),
        "cache_entries": len(dns_manager.dns_cache),
        "user_cache_entries": len(dns_manager.user_dns_cache)
    }


@router.post("/resolve", response_model=DNSResolveResponse)
async def resolve_domain(
    request: DNSResolveRequest,
    admin: Admin = Depends(Admin.get_current),
    _: None = Depends(check_dns_enabled)
):
    """Resolve a domain using DNS rules"""
    try:
        resolved_ip = dns_manager.resolve_domain(request.domain, request.user_id)
        
        # Determine rule type
        rule_type = None
        cached = False
        
        if resolved_ip:
            # Check if it's from user rules
            if request.user_id and request.user_id in dns_manager.user_rules_cache:
                for rule in dns_manager.user_rules_cache[request.user_id]:
                    if dns_manager._domain_matches(request.domain, rule.domain):
                        rule_type = "user"
                        break
            
            # Check if it's from global rules
            if not rule_type:
                for rule in dns_manager.global_rules_cache:
                    if dns_manager._domain_matches(request.domain, rule.domain):
                        rule_type = "global"
                        break
            
            # Check if it's cached
            domain_lower = request.domain.lower()
            if domain_lower in dns_manager.dns_cache:
                cached = True
            elif request.user_id and (request.user_id, domain_lower) in dns_manager.user_dns_cache:
                cached = True
        
        return DNSResolveResponse(
            domain=request.domain,
            resolved_ip=resolved_ip,
            rule_type=rule_type,
            cached=cached
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve domain: {str(e)}"
        )


# Global DNS Rules
@router.get("/rules", response_model=List[DNSRuleResponse])
async def get_global_dns_rules(
    admin: Admin = Depends(Admin.get_current),
    _: None = Depends(check_dns_enabled)
):
    """Get all global DNS rules"""
    rules = dns_manager.get_global_rules()
    return [DNSRuleResponse(**rule) for rule in rules]


@router.post("/rules", response_model=DNSRuleResponse)
async def create_global_dns_rule(
    rule_data: DNSRuleCreate,
    admin: Admin = Depends(Admin.check_sudo_admin),
    db: Session = Depends(get_db),
    _: None = Depends(check_dns_enabled)
):
    """Create a global DNS rule"""
    success = dns_manager.add_global_rule(
        domain=rule_data.domain,
        target_ip=rule_data.target_ip,
        priority=rule_data.priority,
        description=rule_data.description
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create DNS rule"
        )
    
    # Get the created rule
    with db:
        rule = db.query(DNSRule).filter(
            DNSRule.domain == rule_data.domain,
            DNSRule.target_ip == rule_data.target_ip
        ).order_by(DNSRule.id.desc()).first()
        
        if rule:
            return DNSRuleResponse(
                id=rule.id,
                domain=rule.domain,
                target_ip=rule.target_ip,
                priority=rule.priority,
                is_enabled=rule.is_enabled,
                description=rule.description,
                created_at=rule.created_at,
                updated_at=rule.updated_at
            )
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Rule created but could not retrieve details"
    )


@router.delete("/rules/{rule_id}")
async def delete_global_dns_rule(
    rule_id: int,
    admin: Admin = Depends(Admin.check_sudo_admin),
    _: None = Depends(check_dns_enabled)
):
    """Delete a global DNS rule"""
    success = dns_manager.remove_global_rule(rule_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DNS rule not found"
        )
    
    return {"status": "success", "message": "DNS rule deleted"}


# User-specific DNS Rules
@router.get("/users/{user_id}/rules", response_model=List[UserDNSRuleResponse])
async def get_user_dns_rules(
    user_id: int,
    admin: Admin = Depends(Admin.get_current),
    db: Session = Depends(get_db),
    _: None = Depends(check_dns_enabled)
):
    """Get DNS rules for a specific user"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    rules = dns_manager.get_user_rules(user_id)
    return [UserDNSRuleResponse(**rule) for rule in rules]


@router.post("/users/{user_id}/rules", response_model=UserDNSRuleResponse)
async def create_user_dns_rule(
    user_id: int,
    rule_data: UserDNSRuleCreate,
    admin: Admin = Depends(Admin.get_current),
    db: Session = Depends(get_db),
    _: None = Depends(check_dns_enabled)
):
    """Create a user-specific DNS rule"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = dns_manager.add_user_rule(
        user_id=user_id,
        domain=rule_data.domain,
        target_ip=rule_data.target_ip,
        priority=rule_data.priority
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user DNS rule"
        )
    
    # Get the created rule
    with db:
        rule = db.query(UserDNSRule).filter(
            UserDNSRule.user_id == user_id,
            UserDNSRule.domain == rule_data.domain,
            UserDNSRule.target_ip == rule_data.target_ip
        ).order_by(UserDNSRule.id.desc()).first()
        
        if rule:
            return UserDNSRuleResponse(
                id=rule.id,
                user_id=rule.user_id,
                domain=rule.domain,
                target_ip=rule.target_ip,
                priority=rule.priority,
                is_enabled=rule.is_enabled,
                created_at=rule.created_at,
                updated_at=rule.updated_at
            )
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Rule created but could not retrieve details"
    )


@router.delete("/users/{user_id}/rules/{rule_id}")
async def delete_user_dns_rule(
    user_id: int,
    rule_id: int,
    admin: Admin = Depends(Admin.get_current),
    db: Session = Depends(get_db),
    _: None = Depends(check_dns_enabled)
):
    """Delete a user-specific DNS rule"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = dns_manager.remove_user_rule(rule_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DNS rule not found"
        )
    
    return {"status": "success", "message": "User DNS rule deleted"}


@router.post("/cache/clear")
async def clear_dns_cache(admin: Admin = Depends(Admin.check_sudo_admin)):
    """Clear DNS cache"""
    dns_manager.dns_cache.clear()
    dns_manager.user_dns_cache.clear()
    dns_manager._refresh_rules_cache()
    
    return {"status": "success", "message": "DNS cache cleared"}


@router.get("/config/xray")
async def get_xray_dns_config(
    user_id: Optional[int] = None,
    admin: Admin = Depends(Admin.get_current)
):
    """Get XRay DNS configuration with rules"""
    if not DNS_OVERRIDE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DNS override is disabled"
        )
    
    config = dns_manager.generate_xray_dns_config(user_id)
    
    return {
        "user_id": user_id,
        "dns_config": config,
        "rules_count": len(config.get("hosts", {}))
    }
