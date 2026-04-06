"""
Domain exception hierarchy.

These exceptions are raised by the service layer and translated
to HTTP responses by FastAPI exception handlers in app/main.py.
"""


class AuthenticationError(Exception):
    """Raised when a token is invalid, expired, or blacklisted,
    or when login credentials do not match."""


class ConflictError(Exception):
    """Raised when a unique constraint is violated (e.g., duplicate email)."""


class NotFoundError(Exception):
    """Raised when a requested resource does not exist."""


class ForbiddenError(Exception):
    """Raised when the authenticated user does not own the requested resource."""


class ValidationError(Exception):
    """Raised when business-level validation fails (e.g., empty task title)."""
