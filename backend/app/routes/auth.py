"""Authentication and user management routes (SEC-02).

Includes register/login with rate limiting and password strength validation.
"""

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.core import security
from app.core.audit import AuditLogger
from app.utils.rate_limiter import limiter
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with password strength and breach checks."""
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
        full_name=user_in.full_name,
        role="analyst"
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Audit log
    AuditLogger.log(db, user.id, "REGISTER", "user", {"email": user.email}, request.client.host)
    
    return {"message": "User registered successfully"}


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Secure login with audit logging."""
    user = db.query(security.User).filter(security.User.email == form_data.username).first()
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        # Audit failed attempt (ID is None)
        AuditLogger.log(db, None, "LOGIN_FAILED", "auth", {"email": form_data.username}, request.client.host)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
        
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
        
    access_token = security.create_access_token(data={"sub": user.email})
    refresh_token = security.create_refresh_token(data={"sub": user.email})
    
    AuditLogger.log(db, user.id, "LOGIN_SUCCESS", "auth", {}, request.client.host)
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {"email": user.email, "full_name": user.full_name, "role": user.role}
    }


@router.get("/me")
async def get_me(current_user: security.User = Depends(security.get_current_user)):
    """Get current user's profile."""
    return {
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "id": current_user.id
    }
