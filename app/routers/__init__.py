from fastapi import APIRouter
from . import (
    admin,
    core,
    node,
    subscription,
    system,
    user_template,
    user,
    home,
    # Enhanced features
    enhanced,
    two_factor,
    fail2ban,
    dns,
    adblock,
)

api_router = APIRouter()

routers = [
    admin.router,
    core.router,
    node.router,
    subscription.router,
    system.router,
    user_template.router,
    user.router,
    home.router,
    # Enhanced features routers
    enhanced.router,
    two_factor.router,
    fail2ban.router,
    dns.router,
    adblock.router,
]

for router in routers:
    api_router.include_router(router)

__all__ = ["api_router"]