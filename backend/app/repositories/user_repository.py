"""
UserRepository -- persistence operations for the users table.

Operations:
- find_by_email(email) -> User | None
- find_by_id(user_id)  -> User | None
- create(email, hashed_password) -> User
- update_password(user_id, new_hashed_password) -> User

Raises ConflictError on duplicate email (wraps SQLAlchemy IntegrityError).
Raises NotFoundError when find_by_id returns None in update_password.
"""
import uuid
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_by_email(self, email: str) -> Optional[User]:
        """Return the User with the given email, or None if not found."""
        return self.db.query(User).filter(User.email == email).first()

    def find_by_id(self, user_id: str) -> Optional[User]:
        """Return the User with the given id, or None if not found."""
        return self.db.get(User, user_id)

    def update_password(self, user_id: str, new_hashed_password: str) -> User:
        """Update the hashed_password for the given user and return the updated User.

        Raises NotFoundError if no user exists with the given user_id.
        """
        user = self.db.get(User, user_id)
        if user is None:
            raise NotFoundError(f"User with id '{user_id}' not found.")
        user.hashed_password = new_hashed_password
        self.db.commit()
        self.db.refresh(user)
        return user

    def create(self, email: str, hashed_password: str) -> User:
        """Persist a new User and return it.

        Raises ConflictError if the email is already taken.
        """
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            hashed_password=hashed_password,
        )
        self.db.add(user)
        try:
            self.db.commit()
            self.db.refresh(user)
        except IntegrityError:
            self.db.rollback()
            raise ConflictError(f"Email '{email}' is already in use.")
        return user
