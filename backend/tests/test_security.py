"""
Tests for security module
"""
import pytest
from datetime import timedelta
from jose import jwt

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    decode_token,
    verify_password,
    get_password_hash,
    hash_password
)
from app.config import settings


class TestPasswordHashing:
    """Test password hashing functions"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_get_password_hash_compatibility(self):
        """Test that get_password_hash still works (backward compatibility)"""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 50
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """Test verifying correct password"""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_hashes_for_same_password(self):
        """Test that same password generates different hashes (salt)"""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation and verification"""

    def test_create_access_token(self):
        """Test access token creation"""
        user_id = "123"
        token = create_access_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 50

        # Decode and verify
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == user_id
        assert "exp" in payload

    def test_create_access_token_with_custom_expiry(self):
        """Test access token with custom expiry"""
        user_id = "123"
        expires_delta = timedelta(minutes=5)
        token = create_access_token(user_id, expires_delta)

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == user_id

    def test_create_refresh_token(self):
        """Test refresh token creation"""
        user_id = "123"
        token = create_refresh_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 50

        # Decode and verify
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_verify_token_valid(self):
        """Test verifying valid token"""
        user_id = "123"
        token = create_access_token(user_id)

        result = verify_token(token)
        assert result == user_id

    def test_verify_token_invalid(self):
        """Test verifying invalid token"""
        invalid_token = "invalid.token.here"

        result = verify_token(invalid_token)
        assert result is None

    def test_verify_token_expired(self):
        """Test verifying expired token"""
        user_id = "123"
        # Create token that expires immediately
        token = create_access_token(user_id, timedelta(seconds=-1))

        result = verify_token(token)
        assert result is None

    def test_decode_token_valid(self):
        """Test decoding valid token"""
        user_id = "123"
        token = create_access_token(user_id)

        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert "exp" in payload

    def test_decode_token_invalid(self):
        """Test decoding invalid token"""
        invalid_token = "invalid.token.here"

        payload = decode_token(invalid_token)
        assert payload is None

    def test_decode_refresh_token(self):
        """Test decoding refresh token"""
        user_id = "456"
        token = create_refresh_token(user_id)

        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_token_expiration_settings(self):
        """Test that token expiration matches ADR-018 requirements"""
        # Access token should expire in 60 minutes
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60

        # Refresh token should expire in 30 days
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 30


class TestSecurityIntegration:
    """Integration tests for security functions"""

    def test_full_auth_flow(self):
        """Test complete authentication flow"""
        # 1. Hash password
        password = "mysecurepassword"
        hashed = hash_password(password)

        # 2. Verify password
        assert verify_password(password, hashed) is True

        # 3. Create tokens
        user_id = "789"
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        # 4. Verify tokens
        assert verify_token(access_token) == user_id
        assert verify_token(refresh_token) == user_id

        # 5. Decode tokens
        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)

        assert access_payload["sub"] == user_id
        assert refresh_payload["sub"] == user_id
        assert refresh_payload["type"] == "refresh"

    def test_token_refresh_flow(self):
        """Test token refresh flow"""
        user_id = "999"

        # Create initial tokens
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        # Verify refresh token
        refresh_user_id = verify_token(refresh_token)
        assert refresh_user_id == user_id

        # Create new access token (simulating refresh)
        new_access_token = create_access_token(refresh_user_id)

        # Verify new access token works correctly
        assert verify_token(new_access_token) == user_id

        # Verify refresh token payload has correct type
        refresh_payload = decode_token(refresh_token)
        assert refresh_payload["type"] == "refresh"

        # Verify access token doesn't have refresh type
        access_payload = decode_token(access_token)
        assert "type" not in access_payload or access_payload.get("type") != "refresh"


class TestADR018Compliance:
    """Test ADR-018 compliance"""

    def test_required_functions_exist(self):
        """Test that all ADR-018 required functions exist"""
        # Required functions per ADR-018
        from app.core.security import (
            hash_password,
            verify_password,
            create_access_token,
            create_refresh_token,
            decode_token
        )

        assert callable(hash_password)
        assert callable(verify_password)
        assert callable(create_access_token)
        assert callable(create_refresh_token)
        assert callable(decode_token)

    def test_token_expiration_values(self):
        """Test that token expiration values match ADR-018"""
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 30

    def test_algorithm_is_hs256(self):
        """Test that JWT algorithm is HS256 as per ADR-018"""
        assert settings.ALGORITHM == "HS256"

    def test_bcrypt_is_used(self):
        """Test that bcrypt is used for password hashing"""
        from app.core.security import pwd_context
        assert "bcrypt" in pwd_context.schemes()