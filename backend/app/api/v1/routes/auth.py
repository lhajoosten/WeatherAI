from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    check_rate_limit,
    get_auth_service,
    get_optional_current_user,
)
from app.application.dto.dto import TokenResponse, UserCreate, UserLogin, UserResponse
from app.infrastructure.external.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
    current_user = Depends(get_optional_current_user)
):
    """Register a new user and return access token."""
    await check_rate_limit("register", current_user)

    # Create user
    user = await auth_service.register_user(
        email=user_data.email,
        password=user_data.password,
        timezone=user_data.timezone
    )

    # Generate token
    access_token = auth_service.create_access_token(user.id, user.email)

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.from_orm(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
    current_user = Depends(get_optional_current_user)
):
    """Authenticate user and return access token."""
    await check_rate_limit("login", current_user)

    # Authenticate user
    user = await auth_service.authenticate_user(
        email=login_data.email,
        password=login_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Generate token
    access_token = auth_service.create_access_token(user.id, user.email)

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.from_orm(user)
    )
