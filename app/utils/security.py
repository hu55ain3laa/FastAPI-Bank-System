import os
import base64
import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer as BaseOAuth2PasswordBearer
from sqlmodel import Session, select
from dotenv import load_dotenv

from app.models.models import User
from app.models.database import get_session

# Load environment variables
load_dotenv()

# OAuth2 scheme with cookie support
class OAuth2PasswordBearerWithCookie(BaseOAuth2PasswordBearer):
    async def __call__(self, request: Request) -> str:
        # First try to get token from cookies
        cookie_authorization = request.cookies.get("access_token")
        if cookie_authorization and cookie_authorization.startswith("Bearer "):
            return cookie_authorization.replace("Bearer ", "")
        
        # Then try the header (this might raise an exception)
        try:
            return await super().__call__(request)
        except HTTPException:
            # If not in header, and not in cookies, let the parent class handle it
            # (will raise appropriate exception)
            if not cookie_authorization:
                raise
            
            # If we have a cookie but it's not properly formatted, try to fix it
            if not cookie_authorization.startswith("Bearer "):
                return cookie_authorization
                
            # This shouldn't happen given our checks above
            raise

# Use the custom OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="auth/token")

# Get secrets from environment variables
jwt_secret = os.getenv("JWT_SECRET")
if jwt_secret is None:
    raise ValueError("JWT_SECRET environment variable is not set")
JWT_SECRET = jwt_secret

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
try:
    token_expire_str = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    print(f"Raw ACCESS_TOKEN_EXPIRE_MINUTES value: '{token_expire_str}'")
    # Strip any comments (anything after #)
    if '#' in token_expire_str:
        token_expire_str = token_expire_str.split('#')[0].strip()
        print(f"After stripping comments: '{token_expire_str}'")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(token_expire_str)
    print(f"Final ACCESS_TOKEN_EXPIRE_MINUTES: {ACCESS_TOKEN_EXPIRE_MINUTES}")
except ValueError as e:
    print(f"Error parsing ACCESS_TOKEN_EXPIRE_MINUTES: {e}")
    # Fallback to a default value
    ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Get encryption key
encryption_key_str = os.getenv("ENCRYPTION_KEY")
if encryption_key_str is None:
    raise ValueError("ENCRYPTION_KEY environment variable is not set")
ENCRYPTION_KEY = encryption_key_str.strip().encode()  # Strip any trailing whitespace

# Password functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

# Token functions
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# Dependency for routes
async def get_current_user_dependency(
    token: str = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if token is None:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception
    
    return user

# Function for direct calls
async def get_current_user(
    request: Request, 
    session: Session = Depends(get_session)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = None
    
    # Try to extract from cookie
    cookie_authorization = request.cookies.get("access_token")
    if cookie_authorization and cookie_authorization.startswith("Bearer "):
        token = cookie_authorization.replace("Bearer ", "")
    # Try from authorization header
    elif "authorization" in request.headers:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
    
    if token is None:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception
    
    return user

# Encryption/Decryption functions
def get_encryption_key():
    key_length = len(ENCRYPTION_KEY)
    if key_length == 16 or key_length == 24 or key_length == 32:
        return ENCRYPTION_KEY
    else:
        raise ValueError(f"Invalid key size: {key_length}. AES key must be 16, 24, or 32 bytes.")

def encrypt_data(data: str, iv: bytes) -> str:
    cipher = Cipher(
        algorithms.AES(get_encryption_key()),
        modes.CBC(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data.encode()) + padder.finalize()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(encrypted).decode()

def decrypt_data(encrypted_data: str, iv: bytes) -> str:
    cipher = Cipher(
        algorithms.AES(get_encryption_key()),
        modes.CBC(iv),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    unpadder = padding.PKCS7(128).unpadder()
    decrypted_padded = decryptor.update(base64.b64decode(encrypted_data)) + decryptor.finalize()
    decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
    return decrypted.decode()

# Function to check if user is admin
def get_admin_user(current_user: User = Depends(get_current_user_dependency)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user 