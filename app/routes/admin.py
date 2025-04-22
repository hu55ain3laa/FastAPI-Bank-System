from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session
from pydantic import BaseModel
from typing import List, Optional

from app.models.database import get_session
from app.utils.security import get_admin_user
from app.services.banner import (
    get_active_banners, get_all_banners, get_banner,
    create_banner, update_banner, delete_banner, toggle_banner_status,
    get_next_order_number
)
from app.models.models import User, Banner

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Banner schema for requests
class BannerCreate(BaseModel):
    title: str
    subtitle: str
    background_color: str
    text_color: str
    is_active: bool = True
    order: int = 0

class BannerUpdate(BannerCreate):
    pass

class BannerResponse(BannerCreate):
    id: str
    created_at: str
    updated_at: Optional[str] = None

# Banner routes
@router.get("/banners", response_model=List[BannerResponse])
async def admin_get_banners(
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get all banners (admin only)"""
    return get_all_banners(session)

@router.post("/banners", response_model=BannerResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_banner(
    banner_data: BannerCreate,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Create a new banner (admin only)"""
    # If order is 0 (default), assign the next available order number
    if banner_data.order == 0:
        banner_data.order = get_next_order_number(session)
        
    return create_banner(
        title=banner_data.title,
        subtitle=banner_data.subtitle,
        background_color=banner_data.background_color,
        text_color=banner_data.text_color,
        is_active=banner_data.is_active,
        order=banner_data.order,
        session=session
    )

@router.get("/banners/{banner_id}", response_model=BannerResponse)
async def admin_get_banner(
    banner_id: str,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get a banner by ID (admin only)"""
    banner = get_banner(banner_id, session)
    if not banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner not found"
        )
    return banner

@router.put("/banners/{banner_id}", response_model=BannerResponse)
async def admin_update_banner(
    banner_id: str,
    banner_data: BannerUpdate,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update a banner (admin only)"""
    updated_banner = update_banner(
        banner_id=banner_id,
        title=banner_data.title,
        subtitle=banner_data.subtitle,
        background_color=banner_data.background_color,
        text_color=banner_data.text_color,
        is_active=banner_data.is_active,
        order=banner_data.order,
        session=session
    )
    
    if not updated_banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner not found"
        )
    
    return updated_banner

@router.delete("/banners/{banner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_banner(
    banner_id: str,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Delete a banner (admin only)"""
    success = delete_banner(banner_id, session)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner not found"
        )

@router.post("/banners/{banner_id}/toggle", response_model=BannerResponse)
async def admin_toggle_banner(
    banner_id: str,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Toggle a banner's active status (admin only)"""
    banner = toggle_banner_status(banner_id, session)
    
    if not banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner not found"
        )
    
    return banner 