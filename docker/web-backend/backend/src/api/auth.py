from fastapi import APIRouter, Body, Cookie, Depends, Header, HTTPException, Response
from sqlalchemy.orm import Session

from infrastructure.database import get_session
from models.user import User
from schemas.auth import AuthRequest, AuthResponse, RegisterRequest, UserProfile
from services.auth_service import AuthError, AuthService

router = APIRouter(prefix="/api/auth")
SESSION_COOKIE_NAME = "vitam_session"


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )


def current_user(
    authorization: str | None = Header(default=None),
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    session: Session = Depends(get_session),
) -> User:
    token = session_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    if not token:
        raise HTTPException(status_code=401, detail="authentication required")

    user = AuthService(session).user_from_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="invalid or expired token")
    return user


@router.post("/register", response_model=AuthResponse)
def register(
    response: Response,
    body: RegisterRequest = Body(...),
    session: Session = Depends(get_session),
) -> AuthResponse:
    try:
        auth_response = AuthService(session).register(body.username, body.password, body.display_name)
        _set_session_cookie(response, auth_response.access_token)
        return auth_response
    except AuthError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/login", response_model=AuthResponse)
def login(
    response: Response,
    body: AuthRequest = Body(...),
    session: Session = Depends(get_session),
) -> AuthResponse:
    try:
        auth_response = AuthService(session).login(body.username, body.password)
        _set_session_cookie(response, auth_response.access_token)
        return auth_response
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me", response_model=UserProfile)
def me(user: User = Depends(current_user)) -> UserProfile:
    return UserProfile(id=user.id, username=user.username, display_name=user.display_name)


@router.post("/logout")
def logout(
    response: Response,
    authorization: str | None = Header(default=None),
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    session: Session = Depends(get_session),
) -> dict[str, bool]:
    token = session_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if token:
        AuthService(session).revoke_token(token)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"ok": True}
