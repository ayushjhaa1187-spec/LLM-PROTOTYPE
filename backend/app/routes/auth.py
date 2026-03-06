"""Authentication and user management routes (SEC-02).

Includes register/login with rate limiting and password strength validation.
"""

from datetime import timedelta
from typing import Any, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.core import security
from app.core.audit import AuditLogger
from app.utils.rate_limiter import limiter
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/auth", tags=["auth"])


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class TokenResponse(BaseModel):
    token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: Dict[str, Any]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user and return a session token immediately."""
    # Check if exists
    if db.query(security.User).filter(security.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Validate strength
    is_strong, msg = security.validate_password_strength(user_in.password)
    if not is_strong:
        raise HTTPException(status_code=400, detail=msg)
    
    # Check breach (HIBP)
    if await security.check_password_breach(user_in.password):
        raise HTTPException(status_code=400, detail="This password has been pwned. Use a different one.")
        
    hashed_pwd = security.get_password_hash(user_in.password)
    user = security.User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        full_name=user_in.name,
        role="analyst"
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Audit log
    AuditLogger.log(db, user.id, "REGISTER", "user", {"email": user.email}, request.client.host)
    
    # Generate tokens immediately (Auto-login)
    access_token = security.create_access_token(data={"sub": user.email})
    refresh_token = security.create_refresh_token(data={"sub": user.email})
    
    return {
        "token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {"email": user.email, "name": user.full_name, "role": user.role}
    }


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Secure login with JSON body and audit logging."""
    user = db.query(security.User).filter(security.User.email == login_data.email).first()
    
    if not user or not security.verify_password(login_data.password, user.hashed_password):
        # Audit failed attempt (ID is None)
        AuditLogger.log(db, None, "LOGIN_FAILED", "auth", {"email": login_data.email}, request.client.host)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
        
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
        
    # Generate tokens
    access_token = security.create_access_token(data={"sub": user.email})
    refresh_token = security.create_refresh_token(data={"sub": user.email})
    
    AuditLogger.log(db, user.id, "LOGIN_SUCCESS", "auth", {}, request.client.host)
    
    return {
        "token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {"email": user.email, "name": user.full_name, "role": user.role}
    }


@router.get("/me")
async def get_me(current_user: security.User = Depends(security.get_current_user)):
    """Get current user's profile."""
    return {
        "email": current_user.email,
        "name": current_user.full_name,
        "role": current_user.role,
        "id": current_user.id
    }
