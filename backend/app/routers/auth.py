"""
Auth router — HTTP endpoints for registration, login, logout, change-password, and me.

Endpoints:
  POST  /api/v1/auth/register         -> 201 TokenResponse
  POST  /api/v1/auth/login            -> 200 TokenResponse
  POST  /api/v1/auth/logout           -> 200 MessageResponse (requires Bearer token)
  PATCH /api/v1/auth/change-password  -> 200 TokenResponse (requires Bearer token)
  GET   /api/v1/auth/me               -> 200 UserProfileResponse (requires Bearer token)

All business logic is delegated to AuthService.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, field_validator

from app.core.exceptions import AuthenticationError
from app.dependencies import UserContext, get_auth_service, get_current_user
from app.schemas.auth import LoginRequest, MessageResponse, RegisterRequest, TokenResponse

router = APIRouter()

# Re-use the same scheme that get_current_user uses so that the raw token string
# can be extracted for the logout and change-password endpoints.
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ---------------------------------------------------------------------------
# Request / Response models specific to this router
# ---------------------------------------------------------------------------

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def new_password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


class UserProfileResponse(BaseModel):
    email: str


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


# ---------------------------------------------------------------------------
# PATCH /change-password
# ---------------------------------------------------------------------------

@router.patch("/change-password", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def change_password(
    body: ChangePasswordRequest,
    raw_token: str = Depends(_oauth2_scheme),
    current_user: UserContext = Depends(get_current_user),
    auth_service=Depends(get_auth_service),
) -> TokenResponse:
    """Change the authenticated user's password and return a new access token.

    The old JWT is blacklisted immediately on success so it can no longer be used.
    Requires a valid Bearer token.

    Raises 401 if the token is missing, invalid, expired, or blacklisted.
    Raises 401 if the current password is incorrect.
    Raises 422 if the new password fails the minimum-length policy.
    """
    try:
        payload = auth_service.decode_token(raw_token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    result = auth_service.change_password(
        user_id=current_user.user_id,
        jti=current_user.jti,
        expires_at=expires_at,
        current_password=body.current_password,
        new_password=body.new_password,
    )
    return TokenResponse(**result)


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
def get_me(
    current_user: UserContext = Depends(get_current_user),
    auth_service=Depends(get_auth_service),
) -> UserProfileResponse:
    """Return the authenticated user's profile (email only).

    Requires a valid Bearer token.
    Raises 401 if the token is missing, invalid, expired, or blacklisted.
    """
    email = auth_service.get_user_email(current_user.user_id)
    return UserProfileResponse(email=email)
