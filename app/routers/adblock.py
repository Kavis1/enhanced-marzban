"""
Ad-blocking management API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.db import get_db, Session
from app.models.admin import Admin
from app.services.adblock_manager import adblock_manager
from app.db import crud
from app.db.models import User, Node
from app.db.models_enhanced import AdBlockList, AdBlockDomain
from config import ADBLOCK_ENABLED


router = APIRouter(prefix="/api/adblock", tags=["Ad-blocking"])


# Pydantic models
class AdBlockListCreate(BaseModel):
    name: str
    url: str
    description: Optional[str] = None
    is_enabled: bool = True


class AdBlockListResponse(BaseModel):
    id: int
    name: str
    url: str
    description: Optional[str] = None
    is_enabled: bool
    last_updated: Optional[datetime] = None
    domain_count: int
    created_at: datetime


class UserAdBlockSettings(BaseModel):
    adblock_enabled: bool
    custom_blocked_domains: Optional[List[str]] = None


class NodeAdBlockSettings(BaseModel):
    enabled: bool
    adblock_lists: Optional[List[int]] = None


class AdBlockStatsResponse(BaseModel):
    enabled: bool
    total_lists: int
    enabled_lists: int
    total_blocked_domains: int
    cached_domains: int
    users_with_custom_domains: int
    nodes_with_adblock: int
    last_cache_update: Optional[datetime] = None


class DomainCheckRequest(BaseModel):
    domain: str
    user_id: Optional[int] = None
    node_id: Optional[int] = None


class DomainCheckResponse(BaseModel):
    domain: str
    is_blocked: bool
    blocked_by: Optional[str] = None  # global, user, node


# Dependency to check if ad-blocking is enabled
def check_adblock_enabled():
    if not ADBLOCK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ad-blocking is disabled"
        )


@router.get("/status")
async def get_adblock_status(
    admin: Admin = Depends(Admin.get_current),
    _: None = Depends(check_adblock_enabled)
):
    """Get ad-blocking service status"""
    return {
        "enabled": adblock_manager.enabled,
        "initialized": adblock_manager.initialized,
        "update_interval": adblock_manager.update_interval,
        "default_lists": adblock_manager.default_lists,
        "blocked_domains_count": len(adblock_manager.blocked_domains),
        "last_cache_update": adblock_manager.last_cache_update
    }


@router.get("/statistics", response_model=AdBlockStatsResponse)
async def get_adblock_statistics(
    admin: Admin = Depends(Admin.get_current),
    _: None = Depends(check_adblock_enabled)
):
    """Get ad-blocking statistics"""
    try:
        stats = adblock_manager.get_statistics()
        return AdBlockStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.post("/check-domain", response_model=DomainCheckResponse)
async def check_domain_blocked(
    request: DomainCheckRequest,
    admin: Admin = Depends(Admin.get_current),
    _: None = Depends(check_adblock_enabled)
):
    """Check if a domain is blocked"""
    try:
        is_blocked = adblock_manager.is_domain_blocked(
            request.domain, request.user_id, request.node_id
        )
        
        blocked_by = None
        if is_blocked:
            # Determine what blocked it
            if adblock_manager._domain_in_set(request.domain.lower(), adblock_manager.blocked_domains):
                blocked_by = "global"
            elif (request.user_id and request.user_id in adblock_manager.user_blocked_domains and
                  adblock_manager._domain_in_set(request.domain.lower(), 
                                                adblock_manager.user_blocked_domains[request.user_id])):
                blocked_by = "user"
            elif (request.node_id and request.node_id in adblock_manager.node_blocked_domains and
                  adblock_manager._domain_in_set(request.domain.lower(), 
                                                adblock_manager.node_blocked_domains[request.node_id])):
                blocked_by = "node"
        
        return DomainCheckResponse(
            domain=request.domain,
            is_blocked=is_blocked,
            blocked_by=blocked_by
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check domain: {str(e)}"
        )


# Ad-block Lists Management
@router.get("/lists", response_model=List[AdBlockListResponse])
async def get_adblock_lists(
    admin: Admin = Depends(Admin.get_current),
    db: Session = Depends(get_db),
    _: None = Depends(check_adblock_enabled)
):
    """Get all ad-block lists"""
    try:
        lists = db.query(AdBlockList).order_by(AdBlockList.name).all()
        return [
            AdBlockListResponse(
                id=lst.id,
                name=lst.name,
                url=lst.url,
                description=lst.description,
                is_enabled=lst.is_enabled,
                last_updated=lst.last_updated,
                domain_count=lst.domain_count or 0,
                created_at=lst.created_at
            )
            for lst in lists
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ad-block lists: {str(e)}"
        )


@router.post("/lists", response_model=AdBlockListResponse)
async def create_adblock_list(
    list_data: AdBlockListCreate,
    background_tasks: BackgroundTasks,
    admin: Admin = Depends(Admin.check_sudo_admin),
    db: Session = Depends(get_db),
    _: None = Depends(check_adblock_enabled)
):
    """Create a new ad-block list"""
    try:
        # Check if list with same name exists
        existing = db.query(AdBlockList).filter(AdBlockList.name == list_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ad-block list with this name already exists"
            )
        
        # Create new list
        adblock_list = AdBlockList(
            name=list_data.name,
            url=list_data.url,
            description=list_data.description,
            is_enabled=list_data.is_enabled
        )
        db.add(adblock_list)
        db.commit()
        db.refresh(adblock_list)
        
        # Schedule list update in background
        if list_data.is_enabled:
            background_tasks.add_task(adblock_manager.update_list, adblock_list.id)
        
        return AdBlockListResponse(
            id=adblock_list.id,
            name=adblock_list.name,
            url=adblock_list.url,
            description=adblock_list.description,
            is_enabled=adblock_list.is_enabled,
            last_updated=adblock_list.last_updated,
            domain_count=adblock_list.domain_count or 0,
            created_at=adblock_list.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ad-block list: {str(e)}"
        )


@router.put("/lists/{list_id}")
async def update_adblock_list(
    list_id: int,
    list_data: AdBlockListCreate,
    admin: Admin = Depends(Admin.check_sudo_admin),
    db: Session = Depends(get_db),
    _: None = Depends(check_adblock_enabled)
):
    """Update an ad-block list"""
    try:
        adblock_list = db.query(AdBlockList).filter(AdBlockList.id == list_id).first()
        if not adblock_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ad-block list not found"
            )
        
        # Update fields
        adblock_list.name = list_data.name
        adblock_list.url = list_data.url
        adblock_list.description = list_data.description
        adblock_list.is_enabled = list_data.is_enabled
        
        db.commit()
        
        # Refresh cache if enabled status changed
        adblock_manager._refresh_blocked_domains_cache()
        
        return {"status": "success", "message": "Ad-block list updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update ad-block list: {str(e)}"
        )


@router.delete("/lists/{list_id}")
async def delete_adblock_list(
    list_id: int,
    admin: Admin = Depends(Admin.check_sudo_admin),
    db: Session = Depends(get_db),
    _: None = Depends(check_adblock_enabled)
):
    """Delete an ad-block list"""
    try:
        adblock_list = db.query(AdBlockList).filter(AdBlockList.id == list_id).first()
        if not adblock_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ad-block list not found"
            )
        
        # Delete associated domains
        db.query(AdBlockDomain).filter(AdBlockDomain.list_id == list_id).delete()
        
        # Delete list
        db.delete(adblock_list)
        db.commit()
        
        # Refresh cache
        adblock_manager._refresh_blocked_domains_cache()
        
        return {"status": "success", "message": "Ad-block list deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete ad-block list: {str(e)}"
        )


@router.post("/lists/{list_id}/update")
async def update_adblock_list_domains(
    list_id: int,
    background_tasks: BackgroundTasks,
    admin: Admin = Depends(Admin.check_sudo_admin),
    db: Session = Depends(get_db),
    _: None = Depends(check_adblock_enabled)
):
    """Update domains for a specific ad-block list"""
    try:
        adblock_list = db.query(AdBlockList).filter(AdBlockList.id == list_id).first()
        if not adblock_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ad-block list not found"
            )
        
        # Schedule update in background
        background_tasks.add_task(adblock_manager.update_list, list_id)
        
        return {
            "status": "success",
            "message": f"Update scheduled for ad-block list: {adblock_list.name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule list update: {str(e)}"
        )


# User Ad-block Settings
@router.get("/users/{user_id}/settings")
async def get_user_adblock_settings(
    user_id: int,
    admin: Admin = Depends(Admin.get_current),
    db: Session = Depends(get_db),
    _: None = Depends(check_adblock_enabled)
):
    """Get ad-block settings for a user"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    custom_domains = []
    if user.custom_blocked_domains:
        try:
            import json
            custom_domains = json.loads(user.custom_blocked_domains)
        except:
            custom_domains = []
    
    return UserAdBlockSettings(
        adblock_enabled=user.adblock_enabled,
        custom_blocked_domains=custom_domains
    )


@router.put("/users/{user_id}/settings")
async def update_user_adblock_settings(
    user_id: int,
    settings: UserAdBlockSettings,
    admin: Admin = Depends(Admin.get_current),
    db: Session = Depends(get_db),
    _: None = Depends(check_adblock_enabled)
):
    """Update ad-block settings for a user"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        user.adblock_enabled = settings.adblock_enabled
        
        if settings.custom_blocked_domains is not None:
            import json
            user.custom_blocked_domains = json.dumps(settings.custom_blocked_domains)
        
        db.commit()
        
        # Refresh ad-block manager cache
        adblock_manager._refresh_blocked_domains_cache()
        
        return {
            "status": "success",
            "message": f"Ad-block settings updated for user {user.username}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user settings: {str(e)}"
        )


# Node Ad-block Settings
@router.get("/nodes/{node_id}/settings")
async def get_node_adblock_settings(
    node_id: int,
    admin: Admin = Depends(Admin.get_current),
    db: Session = Depends(get_db),
    _: None = Depends(check_adblock_enabled)
):
    """Get ad-block settings for a node"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    adblock_lists = []
    if node.adblock_lists:
        try:
            import json
            adblock_lists = json.loads(node.adblock_lists)
        except:
            adblock_lists = []
    
    return NodeAdBlockSettings(
        enabled=node.adblock_enabled,
        adblock_lists=adblock_lists
    )


@router.put("/nodes/{node_id}/settings")
async def update_node_adblock_settings(
    node_id: int,
    settings: NodeAdBlockSettings,
    admin: Admin = Depends(Admin.get_current),
    db: Session = Depends(get_db),
    _: None = Depends(check_adblock_enabled)
):
    """Update ad-block settings for a node"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    try:
        node.adblock_enabled = settings.enabled
        
        if settings.adblock_lists is not None:
            import json
            node.adblock_lists = json.dumps(settings.adblock_lists)
        
        db.commit()
        
        # Refresh ad-block manager cache
        adblock_manager._refresh_blocked_domains_cache()
        
        return {
            "status": "success",
            "message": f"Ad-block settings updated for node {node.name}",
            "node_id": node.id,
            "enabled": node.adblock_enabled
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update node settings: {str(e)}"
        )
