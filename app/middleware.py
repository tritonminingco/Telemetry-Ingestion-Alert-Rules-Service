import time
from typing import Dict, List, Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.routes.auth import is_valid_token

# Rate limiting storage (in production, use Redis)
rate_limit_storage: Dict[str, List[float]] = {}


class AuthMiddleware:
    """Authentication middleware."""
    
    def __init__(self):
        self.security = HTTPBearer()
    
    async def __call__(self, request: Request):
        """Validate authentication token."""
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authorization header required",
                )
            
            token = auth_header.replace("Bearer ", "")
            # Check both the original token and temporary tokens
            if token != settings.auth_token and not is_valid_token(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                )
            
            # Add user info to request state
            request.state.user = {
                "id": "system",
                "type": "service",
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
            )


class RateLimitMiddleware:
    """Rate limiting middleware."""
    
    def __init__(self):
        self.max_requests = settings.rate_limit_max
        self.window_seconds = settings.rate_limit_window_seconds
    
    async def __call__(self, request: Request):
        """Apply rate limiting."""
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old entries
        if client_ip in rate_limit_storage:
            rate_limit_storage[client_ip] = [
                timestamp for timestamp in rate_limit_storage[client_ip]
                if current_time - timestamp < self.window_seconds
            ]
        else:
            rate_limit_storage[client_ip] = []
        
        # Check rate limit
        if len(rate_limit_storage[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )
        
        # Add current request
        rate_limit_storage[client_ip].append(current_time)


# Global middleware instances
auth_middleware = AuthMiddleware()
rate_limit_middleware = RateLimitMiddleware()


async def get_current_user(request: Request) -> Dict[str, str]:
    """Get current user from request state."""
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return request.state.user
