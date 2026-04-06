"""
Auth router — HTTP endpoints for registration, login, and logout.

Endpoints:
  POST /api/v1/auth/register  → 201 TokenResponse
  POST /api/v1/auth/login     → 200 TokenResponse
  POST /api/v1/auth/logout    → 200 MessageResponse (requires Bearer token)

All business logic is delegated to AuthService.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.exceptions import AuthenticationError
from app.dependencies import UserContext, get_auth_service, get_current_user
from app.schemas.auth import LoginRequest, MessageResponse, RegisterRequest, TokenResponse

router = APIRouter()

# Re-use the same scheme that get_current_user uses so that the raw token string
# can be extracted for the logout endpoint.
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterRequest,
    auth_service=Depends(get_auth_service),
) -> TokenResponse:
    """Register a new user account and return an access token.

    Raises 409 if the email is already in use.
    Raises 422 if the request body fails Pydantic validation.
    """
    result = auth_service.register(email=body.email, password=body.password)
    return TokenResponse(**result)


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(
    body: LoginRequest,
    auth_service=Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate an existing user and return an access token.

    Raises 401 for any invalid credentials (never discloses which field was wrong).
    """
    result = auth_service.login(email=body.email, password=body.password)
    return TokenResponse(**result)


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------

@router.post("/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def logout(
    raw_token: str = Depends(_oauth2_scheme),
    current_user: UserContext = Depends(get_current_user),
    auth_service=Depends(get_auth_service),
) -> MessageResponse:
    """Invalidate the current session by blacklisting the JWT jti claim.

    Requires a valid Bearer token.  Returns 401 if the token is missing,
    invalid, expired, or already blacklisted.
    """
    # Decode the token to extract the exp claim so we can store it in the
    # blacklist.  get_current_user already validated the token, so this second
    # decode is safe and cheap (no blacklist re-check needed for the exp claim).
    try:
        payload = auth_service.decode_token(raw_token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    auth_service.logout(jti=current_user.jti, expires_at=expires_at)
    return MessageResponse(message="Successfully logged out.")
