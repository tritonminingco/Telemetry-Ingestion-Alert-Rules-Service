from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel
import secrets

router = APIRouter(prefix="/auth", tags=["authentication"])

# Simple in-memory token storage (in production, use Redis or database)
temporary_tokens = {}

class TokenRequest(BaseModel):
    username: str = "test_user"
    password: str = "test_password"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    expires_at: datetime

@router.post("/token", response_model=TokenResponse)
async def create_token(request: TokenRequest):
    """Create a temporary access token for testing."""
    # Simple validation (in production, validate against database)
    if request.username == "test_user" and request.password == "test_password":
        # Generate a random token
        token = secrets.token_urlsafe(32)
        expires_in = 3600  # 1 hour
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Store token
        temporary_tokens[token] = {
            "username": request.username,
            "expires_at": expires_at
        }
        
        return TokenResponse(
            access_token=token,
            expires_in=expires_in,
            expires_at=expires_at
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

@router.get("/validate")
async def validate_token(token: str):
    """Validate a token (for testing)."""
    if token in temporary_tokens:
        token_data = temporary_tokens[token]
        if datetime.utcnow() < token_data["expires_at"]:
            return {"valid": True, "username": token_data["username"]}
        else:
            # Remove expired token
            del temporary_tokens[token]
            return {"valid": False, "reason": "Token expired"}
    return {"valid": False, "reason": "Invalid token"}

# Function to validate tokens (used by middleware)
def is_valid_token(token: str) -> bool:
    """Check if a token is valid."""
    if token in temporary_tokens:
        token_data = temporary_tokens[token]
        if datetime.utcnow() < token_data["expires_at"]:
            return True
        else:
            # Remove expired token
            del temporary_tokens[token]
    return False
