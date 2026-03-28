"""
Integration tests for authentication endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
import uuid

from app.models.user import User, UserRole
from app.models.invitation import Invitation
from app.models.password_reset import PasswordResetToken
from app.core.security import hash_password, create_refresh_token, decode_token
from app.config import settings


@pytest.mark.asyncio
class TestLoginEndpoint:
    """Test /auth/login endpoint"""

    async def test_login_success(self, async_client: AsyncClient, async_db: AsyncSession):
        """Test successful login"""
        # Create test user
        user = User(
            email="test@example.com",
            hashed_password=hash_password("password123"),
            full_name="Test User",
            role=UserRole.TRADER,
            is_active=True,
            is_verified=True
        )
        async_db.add(user)
        await async_db.commit()

        # Login
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Verify tokens
        access_payload = decode_token(data["access_token"])
        refresh_payload = decode_token(data["refresh_token"])
        assert access_payload["sub"] == str(user.id)
        assert refresh_payload["sub"] == str(user.id)
        assert refresh_payload["type"] == "refresh"

    async def test_login_invalid_email(self, async_client: AsyncClient):
        """Test login with non-existent email"""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "password123"}
        )

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    async def test_login_wrong_password(self, async_client: AsyncClient, async_db: AsyncSession):
        """Test login with wrong password"""
        # Create test user
        user = User(
            email="test2@example.com",
            hashed_password=hash_password("correctpassword"),
            is_active=True
        )
        async_db.add(user)
        await async_db.commit()

        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "test2@example.com", "password": "wrongpassword"}
        )

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    async def test_login_inactive_user(self, async_client: AsyncClient, async_db: AsyncSession):
        """Test login with inactive user"""
        # Create inactive user
        user = User(
            email="inactive@example.com",
            hashed_password=hash_password("password123"),
            is_active=False
        )
        async_db.add(user)
        await async_db.commit()

        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "password123"}
        )

        assert response.status_code == 403
        assert "Inactive user" in response.json()["detail"]

    async def test_login_updates_last_login(self, async_client: AsyncClient, async_db: AsyncSession):
        """Test that login updates last_login field"""
        # Create test user
        user = User(
            email="test3@example.com",
            hashed_password=hash_password("password123"),
            is_active=True,
            last_login=None
        )
        async_db.add(user)
        await async_db.commit()

        # Login
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "test3@example.com", "password": "password123"}
        )

        assert response.status_code == 200

        # Check last_login was updated
        await async_db.refresh(user)
        assert user.last_login is not None


@pytest.mark.asyncio
class TestRegisterEndpoint:
    """Test /auth/register endpoint"""

    async def test_register_success(self, async_client: AsyncClient, async_db: AsyncSession):
        """Test successful registration with invitation"""
        # Create invitation
        invitation = Invitation(
            token=str(uuid.uuid4()),
            role=UserRole.TRADER,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        async_db.add(invitation)
        await async_db.commit()

        # Register
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepass123",
                "full_name": "New User",
                "invitation_token": invitation.token
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

        # Verify user was created
        result = await async_db.execute(
            select(User).where(User.email == "newuser@example.com")
        )
        user = result.scalar_one()
        assert user.full_name == "New User"
        assert user.role == UserRole.TRADER
        assert user.is_active is True
        assert user.is_verified is True

        # Verify invitation was marked as used
        await async_db.refresh(invitation)
        assert invitation.used_by_id == user.id
        assert invitation.used_at is not None

    async def test_register_invalid_invitation(self, async_client: AsyncClient):
        """Test registration with invalid invitation token"""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "invitation_token": "invalid-token"
            }
        )

        assert response.status_code == 404
        assert "Invalid invitation token" in response.json()["detail"]

    async def test_register_expired_invitation(self, async_client: AsyncClient, async_db: AsyncSession):
        """Test registration with expired invitation"""
        # Create expired invitation
        invitation = Invitation(
            token=str(uuid.uuid4()),
            role=UserRole.TRADER,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        async_db.add(invitation)
        await async_db.commit()

        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "invitation_token": invitation.token
            }
        )

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    async def test_register_duplicate_email(self, async_client: AsyncClient, async_db: AsyncSession):
        """Test registration with already registered email"""
        # Create existing user
        user = User(
            email="existing@example.com",
            hashed_password=hash_password("password"),
            is_active=True
        )
        async_db.add(user)

        # Create invitation
        invitation = Invitation(
            token=str(uuid.uuid4()),
            role=UserRole.TRADER,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        async_db.add(invitation)
        await async_db.commit()

        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "existing@example.com",
                "password": "password123",
                "invitation_token": invitation.token
            }
        )

        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]


@pytest.mark.asyncio
class TestRefreshEndpoint:
    """Test /auth/refresh endpoint"""

    async def test_refresh_success(self, async_client: AsyncClient, async_db: AsyncSession):
        """Test successful token refresh"""
        # Create test user
        user = User(
            email="refresh@example.com",
            hashed_password=hash_password("password123"),
            is_active=True
        )
        async_db.add(user)
        await async_db.commit()

        # Create refresh token
        refresh_token = create_refresh_token(str(user.id))

        # Refresh
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

        # New tokens should be different
        assert data["refresh_token"] != refresh_token

    async def test_refresh_invalid_token(self, async_client: AsyncClient):
        """Test refresh with invalid token"""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    async def test_refresh_inactive_user(self, async_client: AsyncClient, async_db: AsyncSession):
        """Test refresh with inactive user"""
        # Create inactive user
        user = User(
            email="inactive_refresh@example.com",
            hashed_password=hash_password("password123"),
            is_active=False
        )
        async_db.add(user)
        await async_db.commit()

        refresh_token = create_refresh_token(str(user.id))

        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 401
        assert "User not found or inactive" in response.json()["detail"]


@pytest.mark.asyncio
class TestMeEndpoint:
    """Test /auth/me endpoint"""

    async def test_me_success(self, async_client: AsyncClient, async_db: AsyncSession, auth_headers):
        """Test getting current user info"""
        # auth_headers fixture should provide authenticated user
        response = await async_client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "id" in data
        assert "role" in data

    async def test_me_unauthorized(self, async_client: AsyncClient):
        """Test accessing /me without authentication"""
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 403  # HTTPBearer returns 403 when no token

    async def test_me_invalid_token(self, async_client: AsyncClient):
        """Test accessing /me with invalid token"""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestForgotPasswordEndpoint:
    """Test /auth/forgot-password endpoint"""

    async def test_forgot_password_success(self, async_client: AsyncClient, async_db: AsyncSession):
        """Test password reset request for existing user"""
        # Create test user
        user = User(
            email="forgot@example.com",
            hashed_password=hash_password("oldpassword"),
            is_active=True
        )
        async_db.add(user)
        await async_db.commit()

        response = await async_client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "forgot@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "If the email exists, a password reset link has been sent"

        # Verify token was created
        result = await async_db.execute(
            select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
        )
        token = result.scalar_one()
        assert token is not None
        assert token.used_at is None

    async def test_forgot_password_nonexistent_email(self, async_client: AsyncClient):
        """Test password reset for non-existent email (should still return 200)"""
        response = await async_client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"}
        )

        # Should return success for security (don't reveal if email exists)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "If the email exists, a password reset link has been sent"


@pytest.mark.asyncio
class TestResetPasswordEndpoint:
    """Test /auth/reset-password endpoint"""

    async def test_reset_password_success(self, async_client: AsyncClient, async_db: AsyncSession):
        """Test successful password reset"""
        # Create test user
        user = User(
            email="reset@example.com",
            hashed_password=hash_password("oldpassword"),
            is_active=True
        )
        async_db.add(user)
        await async_db.flush()

        # Create reset token
        reset_token = PasswordResetToken(
            token=str(uuid.uuid4()),
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        async_db.add(reset_token)
        await async_db.commit()

        # Reset password
        response = await async_client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": reset_token.token,
                "new_password": "newpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Password has been reset successfully"

        # Verify token was marked as used
        await async_db.refresh(reset_token)
        assert reset_token.used_at is not None

    async def test_reset_password_invalid_token(self, async_client: AsyncClient):
        """Test password reset with invalid token"""
        response = await async_client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "invalid-token",
                "new_password": "newpassword123"
            }
        )

        assert response.status_code == 404
        assert "Invalid reset token" in response.json()["detail"]

    async def test_reset_password_expired_token(self, async_client: AsyncClient, async_db: AsyncSession):
        """Test password reset with expired token"""
        # Create test user
        user = User(
            email="expired@example.com",
            hashed_password=hash_password("oldpassword"),
            is_active=True
        )
        async_db.add(user)
        await async_db.flush()

        # Create expired token
        reset_token = PasswordResetToken(
            token=str(uuid.uuid4()),
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        async_db.add(reset_token)
        await async_db.commit()

        response = await async_client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": reset_token.token,
                "new_password": "newpassword123"
            }
        )

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestADR018Compliance:
    """Test ADR-018 compliance for endpoints"""

    async def test_token_expiration_times(self, async_client: AsyncClient, async_db: AsyncSession):
        """Test that tokens have correct expiration times"""
        # Create test user
        user = User(
            email="expiry@example.com",
            hashed_password=hash_password("password123"),
            is_active=True
        )
        async_db.add(user)
        await async_db.commit()

        # Login
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "expiry@example.com", "password": "password123"}
        )

        data = response.json()

        # Check access token expiry (should be ~60 minutes)
        access_payload = decode_token(data["access_token"])
        access_exp = access_payload["exp"]
        current_time = datetime.utcnow().timestamp()
        access_diff_minutes = (access_exp - current_time) / 60
        assert 59 <= access_diff_minutes <= 61  # Allow for small timing differences

        # Check refresh token expiry (should be ~30 days)
        refresh_payload = decode_token(data["refresh_token"])
        refresh_exp = refresh_payload["exp"]
        refresh_diff_days = (refresh_exp - current_time) / (60 * 60 * 24)
        assert 29 <= refresh_diff_days <= 31  # Allow for small timing differences

    async def test_all_endpoints_exist(self, async_client: AsyncClient):
        """Test that all required endpoints exist"""
        endpoints = [
            ("/api/v1/auth/login", "POST"),
            ("/api/v1/auth/register", "POST"),
            ("/api/v1/auth/refresh", "POST"),
            ("/api/v1/auth/me", "GET"),
            ("/api/v1/auth/forgot-password", "POST"),
            ("/api/v1/auth/reset-password", "POST"),
        ]

        # We can't directly test endpoint existence without making requests,
        # but we can verify the router is properly configured
        from app.api.v1.endpoints.auth import router
        routes = [route.path for route in router.routes]

        for endpoint, _ in endpoints:
            path = endpoint.replace("/api/v1/auth", "")
            assert any(path in route for route in routes)