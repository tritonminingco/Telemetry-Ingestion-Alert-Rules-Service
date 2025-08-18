import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.middleware import AuthMiddleware, RateLimitMiddleware, get_current_user


@pytest.fixture
def mock_request():
    """Mock request object."""
    request = MagicMock()
    request.headers = {}
    request.client.host = "127.0.0.1"
    return request


@pytest.fixture
def auth_middleware():
    """Create auth middleware instance."""
    return AuthMiddleware()


@pytest.fixture
def rate_limit_middleware():
    """Create rate limit middleware instance."""
    return RateLimitMiddleware()


class TestAuthMiddleware:
    """Test cases for authentication middleware."""
    
    @pytest.mark.asyncio
    async def test_valid_token(self, auth_middleware, mock_request):
        """Test authentication with valid token."""
        # Mock settings
        with patch('app.middleware.settings') as mock_settings:
            mock_settings.auth_token = "valid-token-123"
            
            # Set valid authorization header
            mock_request.headers["Authorization"] = "Bearer valid-token-123"
            
            # Call middleware
            await auth_middleware(mock_request)
            
            # Verify user info was added to request state
            assert hasattr(mock_request.state, "user")
            assert mock_request.state.user["id"] == "system"
            assert mock_request.state.user["type"] == "service"
    
    @pytest.mark.asyncio
    async def test_missing_authorization_header(self, auth_middleware, mock_request):
        """Test authentication with missing authorization header."""
        # Mock settings
        with patch('app.middleware.settings') as mock_settings:
            mock_settings.auth_token = "valid-token-123"
            
            # No authorization header
            mock_request.headers = {}
            
            # Should raise HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await auth_middleware(mock_request)
            
            assert exc_info.value.status_code == 401
            assert "Authorization header required" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_invalid_token(self, auth_middleware, mock_request):
        """Test authentication with invalid token."""
        # Mock settings
        with patch('app.middleware.settings') as mock_settings:
            mock_settings.auth_token = "valid-token-123"
            
            # Set invalid authorization header
            mock_request.headers["Authorization"] = "Bearer invalid-token"
            
            # Should raise HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await auth_middleware(mock_request)
            
            assert exc_info.value.status_code == 401
            assert "Invalid token" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_malformed_authorization_header(self, auth_middleware, mock_request):
        """Test authentication with malformed authorization header."""
        # Mock settings
        with patch('app.middleware.settings') as mock_settings:
            mock_settings.auth_token = "valid-token-123"
            
            # Malformed authorization header
            mock_request.headers["Authorization"] = "InvalidFormat valid-token-123"
            
            # Should raise HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await auth_middleware(mock_request)
            
            assert exc_info.value.status_code == 401
            assert "Invalid token" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_empty_token(self, auth_middleware, mock_request):
        """Test authentication with empty token."""
        # Mock settings
        with patch('app.middleware.settings') as mock_settings:
            mock_settings.auth_token = "valid-token-123"
            
            # Empty token
            mock_request.headers["Authorization"] = "Bearer "
            
            # Should raise HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await auth_middleware(mock_request)
            
            assert exc_info.value.status_code == 401
            assert "Invalid token" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_case_insensitive_bearer(self, auth_middleware, mock_request):
        """Test authentication with case insensitive bearer."""
        # Mock settings
        with patch('app.middleware.settings') as mock_settings:
            mock_settings.auth_token = "valid-token-123"
            
            # Case insensitive bearer
            mock_request.headers["Authorization"] = "bearer valid-token-123"
            
            # Should work
            await auth_middleware(mock_request)
            
            # Verify user info was added to request state
            assert hasattr(mock_request.state, "user")
            assert mock_request.state.user["id"] == "system"


class TestRateLimitMiddleware:
    """Test cases for rate limiting middleware."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_within_bounds(self, rate_limit_middleware, mock_request):
        """Test rate limiting within allowed bounds."""
        # Mock settings
        with patch('app.middleware.settings') as mock_settings:
            mock_settings.rate_limit_max = 10
            mock_settings.rate_limit_window_seconds = 60
            
            # Make requests within limit
            for i in range(5):
                await rate_limit_middleware(mock_request)
            
            # Should not raise exception
            # (If it did, this test would fail)
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, rate_limit_middleware, mock_request):
        """Test rate limiting when limit is exceeded."""
        # Mock settings
        with patch('app.middleware.settings') as mock_settings:
            mock_settings.rate_limit_max = 3
            mock_settings.rate_limit_window_seconds = 60
            
            # Make requests up to limit
            for i in range(3):
                await rate_limit_middleware(mock_request)
            
            # Next request should exceed limit
            with pytest.raises(HTTPException) as exc_info:
                await rate_limit_middleware(mock_request)
            
            assert exc_info.value.status_code == 429
            assert "Rate limit exceeded" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_rate_limit_window_expiry(self, rate_limit_middleware, mock_request):
        """Test rate limiting window expiry."""
        # Mock settings
        with patch('app.middleware.settings') as mock_settings:
            mock_settings.rate_limit_max = 2
            mock_settings.rate_limit_window_seconds = 1  # 1 second window
            
            # Make requests up to limit
            await rate_limit_middleware(mock_request)
            await rate_limit_middleware(mock_request)
            
            # Next request should exceed limit
            with pytest.raises(HTTPException):
                await rate_limit_middleware(mock_request)
            
            # Wait for window to expire
            time.sleep(1.1)
            
            # Should be able to make requests again
            await rate_limit_middleware(mock_request)
            await rate_limit_middleware(mock_request)
    
    @pytest.mark.asyncio
    async def test_rate_limit_different_clients(self, rate_limit_middleware):
        """Test rate limiting for different client IPs."""
        # Mock settings
        with patch('app.middleware.settings') as mock_settings:
            mock_settings.rate_limit_max = 2
            mock_settings.rate_limit_window_seconds = 60
            
            # Create requests from different clients
            request1 = MagicMock()
            request1.client.host = "127.0.0.1"
            
            request2 = MagicMock()
            request2.client.host = "192.168.1.1"
            
            # Each client should have their own limit
            await rate_limit_middleware(request1)
            await rate_limit_middleware(request1)
            
            await rate_limit_middleware(request2)
            await rate_limit_middleware(request2)
            
            # Both should be at their limit
            with pytest.raises(HTTPException):
                await rate_limit_middleware(request1)
            
            with pytest.raises(HTTPException):
                await rate_limit_middleware(request2)
    
    @pytest.mark.asyncio
    async def test_rate_limit_storage_cleanup(self, rate_limit_middleware, mock_request):
        """Test rate limit storage cleanup of old entries."""
        # Mock settings
        with patch('app.middleware.settings') as mock_settings:
            mock_settings.rate_limit_max = 5
            mock_settings.rate_limit_window_seconds = 1
            
            # Mock time to control timing
            with patch('app.middleware.time') as mock_time:
                mock_time.time.return_value = 1000.0
                
                # Make some requests
                await rate_limit_middleware(mock_request)
                await rate_limit_middleware(mock_request)
                
                # Advance time beyond window
                mock_time.time.return_value = 1062.0  # 62 seconds later
                
                # Should be able to make requests again (old entries cleaned up)
                await rate_limit_middleware(mock_request)
                await rate_limit_middleware(mock_request)
                await rate_limit_middleware(mock_request)
                await rate_limit_middleware(mock_request)
                await rate_limit_middleware(mock_request)
                
                # Next request should exceed limit
                with pytest.raises(HTTPException):
                    await rate_limit_middleware(mock_request)


class TestGetCurrentUser:
    """Test cases for get_current_user function."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_request):
        """Test getting current user when user exists in request state."""
        # Set user in request state
        mock_request.state.user = {"id": "test-user", "type": "service"}
        
        # Get current user
        user = await get_current_user(mock_request)
        
        assert user["id"] == "test-user"
        assert user["type"] == "service"
    
    @pytest.mark.asyncio
    async def test_get_current_user_missing(self, mock_request):
        """Test getting current user when user doesn't exist in request state."""
        # No user in request state
        mock_request.state = MagicMock()
        delattr(mock_request.state, 'user')
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request)
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_user_none_state(self, mock_request):
        """Test getting current user when request state is None."""
        # No request state
        mock_request.state = None
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request)
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in str(exc_info.value.detail)


class TestMiddlewareIntegration:
    """Test cases for middleware integration."""
    
    @pytest.mark.asyncio
    async def test_auth_and_rate_limit_together(self, auth_middleware, rate_limit_middleware, mock_request):
        """Test authentication and rate limiting working together."""
        # Mock settings
        with patch('app.middleware.settings') as mock_settings:
            mock_settings.auth_token = "valid-token-123"
            mock_settings.rate_limit_max = 5
            mock_settings.rate_limit_window_seconds = 60
            
            # Set valid authorization header
            mock_request.headers["Authorization"] = "Bearer valid-token-123"
            
            # Apply both middlewares
            await auth_middleware(mock_request)
            await rate_limit_middleware(mock_request)
            
            # Verify both worked
            assert hasattr(mock_request.state, "user")
            assert mock_request.state.user["id"] == "system"
    
    @pytest.mark.asyncio
    async def test_middleware_order_matters(self, auth_middleware, rate_limit_middleware, mock_request):
        """Test that middleware order affects behavior."""
        # Mock settings
        with patch('app.middleware.settings') as mock_settings:
            mock_settings.auth_token = "valid-token-123"
            mock_settings.rate_limit_max = 5
            mock_settings.rate_limit_window_seconds = 60
            
            # Set valid authorization header
            mock_request.headers["Authorization"] = "Bearer valid-token-123"
            
            # Apply rate limit first, then auth
            await rate_limit_middleware(mock_request)
            await auth_middleware(mock_request)
            
            # Should still work
            assert hasattr(mock_request.state, "user")
            assert mock_request.state.user["id"] == "system"
