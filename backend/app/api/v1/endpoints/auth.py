"""Authentication Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta

from app.db.session import get_db
from app.models.user import User
from app.models.invitation import Invitation
from app.models.password_reset import PasswordResetToken
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, verify_token
from app.core.deps import get_current_user
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, RefreshRequest
from app.schemas.user import User as UserSchema
from app.schemas.password_reset import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse
)
from app.services.email import send_password_reset_email

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password"""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id)
    )


@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register new user with invitation token"""
    # Verify invitation
    result = await db.execute(
        select(Invitation).where(Invitation.token == data.invitation_token)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invitation token"
        )

    if not invitation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired or already been used"
        )

    # Check if invitation is for specific email
    if invitation.email and invitation.email != data.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation is for a different email"
        )

    # Check if user already exists
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        role=invitation.role,
        is_active=True,
        is_verified=True
    )
    db.add(user)
    await db.flush()

    # Mark invitation as used
    invitation.used_by_id = user.id
    invitation.used_at = datetime.utcnow()

    await db.commit()
    await db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token"""
    user_id = verify_token(data.refresh_token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id)
    )


@router.get("/me", response_model=UserSchema)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Request password reset link

    Note: Always returns success message for security (don't reveal if email exists)
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        # Generate reset token
        token = PasswordResetToken.generate_token()

        # Create password reset record
        reset_token = PasswordResetToken(
            token=token,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        db.add(reset_token)
        await db.commit()

        # Send email with reset link
        await send_password_reset_email(user.email, token)

    # Always return success message (security best practice)
    return ForgotPasswordResponse()


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using token from email"""
    # Find token
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token == data.token)
    )
    reset_token = result.scalar_one_or_none()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid reset token"
        )

    if not reset_token.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired or already been used"
        )

    # Get user
    result = await db.execute(select(User).where(User.id == reset_token.user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or inactive"
        )

    # Update password
    user.hashed_password = get_password_hash(data.new_password)

    # Mark token as used
    reset_token.used_at = datetime.now(timezone.utc)

    await db.commit()

    return ResetPasswordResponse()
