"""
AuthService — business logic for authentication.

Responsibilities:
- Password hashing (bcrypt via passlib CryptContext)
- JWT token creation with sub, exp, iat, jti claims
- JWT token decoding with expiry and blacklist validation
- User registration and login
- Logout with token blacklist management
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from jose import JWTError, jwt as jose_jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError, ValidationError
from app.models.token_blacklist import TokenBlacklist
from app.repositories.user_repository import UserRepository

# ---------------------------------------------------------------------------
# Password context
# ---------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: Session, user_repo: UserRepository) -> None:
        self.db = db
        self.user_repo = user_repo

    # -----------------------------------------------------------------------
    # Password helpers
    # -----------------------------------------------------------------------

    def hash_password(self, password: str) -> str:
        """Return a bcrypt hash of the plaintext password."""
        return _pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        """Return True if plain matches hashed; uses constant-time comparison."""
        return _pwd_context.verify(plain, hashed)

    # -----------------------------------------------------------------------
    # JWT helpers
    # -----------------------------------------------------------------------

    def create_access_token(self, user_id: str) -> str:
        """Issue a signed JWT with sub, exp, iat, and jti claims."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        claims: Dict[str, Any] = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
        }
        return jose_jwt.encode(claims, settings.SECRET_KEY, algorithm="HS256")

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate a JWT.

        Returns the payload dict.
        Raises AuthenticationError if the token is expired, malformed, or
        its jti has been blacklisted.
        """
        try:
            payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except JWTError:
            raise AuthenticationError("Invalid or expired token.")

        jti = payload.get("jti")
        if jti and self._is_blacklisted(jti):
            raise AuthenticationError("Token has been revoked.")

        return payload

    # -----------------------------------------------------------------------
    # Registration / Login
    # -----------------------------------------------------------------------

    def register(self, email: str, password: str):
        """Register a new user and return a TokenResponse.

        Raises ConflictError if the email is already taken.
        Raises ValidationError if the password is shorter than 8 characters.
        """
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")

        hashed = self.hash_password(password)
        # UserRepository.create raises ConflictError on duplicate email.
        user = self.user_repo.create(email=email, hashed_password=hashed)
        token = self.create_access_token(user_id=user.id)
        return _build_token_response(token)

    def login(self, email: str, password: str):
        """Authenticate an existing user and return a TokenResponse.

        Raises AuthenticationError for any mismatch — never discloses whether
        the email or the password was incorrect.
        """
        user = self.user_repo.find_by_email(email)
        if user is None or not self.verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid credentials.")

        token = self.create_access_token(user_id=user.id)
        return _build_token_response(token)

    # -----------------------------------------------------------------------
    # Logout / Blacklist
    # -----------------------------------------------------------------------

    def logout(self, jti: str, expires_at: datetime) -> None:
        """Blacklist the given jti and prune expired entries lazily."""
        entry = TokenBlacklist(jti=jti, expires_at=expires_at)
        self.db.add(entry)
        self.db.commit()
        self._prune_expired_blacklist()

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _is_blacklisted(self, jti: str) -> bool:
        return (
            self.db.query(TokenBlacklist)
            .filter(TokenBlacklist.jti == jti)
            .first()
        ) is not None

    def _prune_expired_blacklist(self) -> None:
        """Remove expired token_blacklist entries to prevent unbounded growth."""
        now = datetime.now(timezone.utc)
        self.db.query(TokenBlacklist).filter(
            TokenBlacklist.expires_at < now
        ).delete(synchronize_session=False)
        self.db.commit()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _build_token_response(token: str) -> Dict[str, str]:
    return {"access_token": token, "token_type": "bearer"}
