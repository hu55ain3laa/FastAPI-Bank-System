import os
import uuid
import base64
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.models.database import get_session
from app.models.models import User
from app.schemas.auth import Token, UserLogin, UserCreate
from app.utils.security import hash_password, verify_password, create_access_token, get_encryption_key, encrypt_data

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    # Get user from database
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    
    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=60 * 24)  # 24 hours
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login")
async def login(
    login_data: UserLogin,
    response: Response,
    session: Session = Depends(get_session)
):
    # Get user from database
    user = session.exec(select(User).where(User.username == login_data.username)).first()
    
    # Verify user exists and password is correct
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create access token with longer expiration if remember_me is True
    access_token_expires = timedelta(minutes=60 * 24 * 7) if login_data.remember_me else timedelta(minutes=60 * 24)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # Set cookie if remember_me is True
    if login_data.remember_me:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=60 * 60 * 24 * 7,  # 7 days
            expires=60 * 60 * 24 * 7,
            samesite="lax",
            secure=True
        )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    session: Session = Depends(get_session)
):
    # Check if username already exists
    existing_user = session.exec(select(User).where(User.username == user_data.username)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Generate IV for encryption
    iv = os.urandom(16)
    
    # Create new user with encrypted balance
    new_user = User(
        id=str(uuid.uuid4()),
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        iv=base64.b64encode(iv).decode(),
        balance=encrypt_data("1000", iv),  # Initial balance of $1000
        is_admin=False
    )
    
    session.add(new_user)
    session.commit()
    
    return {"message": "User created successfully"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"} 