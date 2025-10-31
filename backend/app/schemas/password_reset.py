"""
Password Reset Schemas
"""
from pydantic import BaseModel, EmailStr, field_validator


class ForgotPasswordRequest(BaseModel):
    """Request schema for forgot password endpoint"""
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Response schema for forgot password endpoint"""
    message: str = "If the email exists, a password reset link has been sent"


class ResetPasswordRequest(BaseModel):
    """Request schema for reset password endpoint"""
    token: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class ResetPasswordResponse(BaseModel):
    """Response schema for reset password endpoint"""
    message: str = "Password has been reset successfully"
