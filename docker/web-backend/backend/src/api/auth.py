from fastapi import APIRouter, Body, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from infrastructure.database import get_session
from models.user import User
from schemas.auth import AuthRequest, AuthResponse, RegisterRequest, UserProfile
from services.auth_service import AuthError, AuthService

router = APIRouter(prefix="/api/auth")


def current_user(
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="authentication required")

    token = authorization.split(" ", 1)[1].strip()
    user = AuthService(session).user_from_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="invalid or expired token")
    return user


@router.post("/register", response_model=AuthResponse)
def register(body: RegisterRequest = Body(...), session: Session = Depends(get_session)) -> AuthResponse:
    try:
        return AuthService(session).register(body.username, body.password, body.display_name)
    except AuthError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/login", response_model=AuthResponse)
def login(body: AuthRequest = Body(...), session: Session = Depends(get_session)) -> AuthResponse:
    try:
        return AuthService(session).login(body.username, body.password)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me", response_model=UserProfile)
def me(user: User = Depends(current_user)) -> UserProfile:
    return UserProfile(id=user.id, username=user.username, display_name=user.display_name)
