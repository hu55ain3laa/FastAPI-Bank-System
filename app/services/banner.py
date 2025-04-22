from datetime import datetime
from sqlmodel import Session, select, func
from app.models.models import Banner

def get_active_banners(session: Session, limit: int = 10):
    """Get all active banners, ordered by the order field"""
    return session.exec(
        select(Banner)
        .where(Banner.is_active == True)
        .order_by(Banner.order)
        .limit(limit)
    ).all()

def get_all_banners(session: Session):
    """Get all banners"""
    return session.exec(select(Banner).order_by(Banner.order)).all()

def get_banner(banner_id: str, session: Session):
    """Get a banner by ID"""
    return session.exec(select(Banner).where(Banner.id == banner_id)).first()

def get_next_order_number(session: Session) -> int:
    """Get the next available order number (max order + 1)"""
    result = session.exec(select(func.max(Banner.order))).first()
    # If no banners exist yet or max is None, start with 1
    return (result or 0) + 1

def create_banner(
    title: str, 
    subtitle: str, 
    background_color: str, 
    text_color: str, 
    is_active: bool,
    order: int,
    session: Session
):
    """Create a new banner"""
    banner = Banner(
        title=title,
        subtitle=subtitle,
        background_color=background_color,
        text_color=text_color,
        is_active=is_active,
        order=order,
        created_at=datetime.now().isoformat()
    )
    
    session.add(banner)
    session.commit()
    session.refresh(banner)
    return banner

def update_banner(
    banner_id: str,
    title: str,
    subtitle: str,
    background_color: str,
    text_color: str,
    is_active: bool,
    order: int,
    session: Session
):
    """Update an existing banner"""
    banner = get_banner(banner_id, session)
    
    if not banner:
        return None
    
    banner.title = title
    banner.subtitle = subtitle
    banner.background_color = background_color
    banner.text_color = text_color
    banner.is_active = is_active
    banner.order = order
    banner.updated_at = datetime.now().isoformat()
    
    session.add(banner)
    session.commit()
    session.refresh(banner)
    return banner

def delete_banner(banner_id: str, session: Session):
    """Delete a banner"""
    banner = get_banner(banner_id, session)
    
    if not banner:
        return False
    
    session.delete(banner)
    session.commit()
    return True

def toggle_banner_status(banner_id: str, session: Session):
    """Toggle a banner's active status"""
    banner = get_banner(banner_id, session)
    
    if not banner:
        return None
    
    banner.is_active = not banner.is_active
    banner.updated_at = datetime.now().isoformat()
    
    session.add(banner)
    session.commit()
    session.refresh(banner)
    return banner 