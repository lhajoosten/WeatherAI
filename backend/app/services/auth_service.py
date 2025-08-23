from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.core.config import settings
from app.db.models import User
from app.db.repositories import UserRepository

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for authentication and JWT token management."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, user_id: int, email: str) -> str:
        """Create JWT access token."""
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        to_encode = {
            "sub": str(user_id),
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    def decode_token(self, token: str) -> dict:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )

    async def register_user(self, email: str, password: str, timezone: str = "UTC") -> User:
        """Register a new user."""
        # Check if user already exists
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash password and create user
        password_hash = self.hash_password(password)
        user = await self.user_repo.create(
            email=email,
            password_hash=password_hash,
            timezone=timezone
        )
        return user

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate user with email and password."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None

        if not self.verify_password(password, user.password_hash):
            return None

        return user

    async def get_current_user(self, token: str) -> User:
        """Get current user from JWT token."""
        payload = self.decode_token(token)
        user_id = int(payload.get("sub"))

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return user
