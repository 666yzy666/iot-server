from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from config.settings import Settings
from models.device import utc_now
from models.user import User, UserSession
from schemas.auth import AuthResponse, UserProfile
from utils.security import hash_password, hash_token, new_salt, new_token, verify_password


class AuthError(ValueError):
    pass


class AuthService:
    def __init__(self, session: Session, settings: Settings | None = None):
        self.session = session
        self.settings = settings or Settings.from_env()

    def register(self, username: str, password: str, display_name: str = "") -> AuthResponse:
        username = username.strip()
        if not username:
            raise AuthError("username is required")
        if self._get_user(username) is not None:
            raise AuthError("username already exists")

        salt = new_salt()
        user = User(
            username=username,
            display_name=display_name.strip(),
            password_salt=salt,
            password_hash=hash_password(password, salt),
        )
        self.session.add(user)
        self.session.flush()
        response = self._issue_token(user)
        self.session.commit()
        return response

    def login(self, username: str, password: str) -> AuthResponse:
        user = self._get_user(username.strip())
        if user is None or not verify_password(password, user.password_salt, user.password_hash):
            raise AuthError("invalid username or password")

        response = self._issue_token(user)
        self.session.commit()
        return response

    def user_from_token(self, token: str) -> User | None:
        row = self.session.execute(
            select(UserSession).where(UserSession.token_hash == hash_token(token))
        ).scalar_one_or_none()
        if row is None:
            return None
        now = utc_now()
        expires_at = row.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=now.tzinfo)
        if expires_at <= now:
            return None
        return self.session.get(User, row.user_id)

    def _get_user(self, username: str) -> User | None:
        return self.session.execute(select(User).where(User.username == username)).scalar_one_or_none()

    def _issue_token(self, user: User) -> AuthResponse:
        token = new_token()
        self.session.add(
            UserSession(
                user_id=user.id,
                token_hash=hash_token(token),
                expires_at=utc_now() + timedelta(days=self.settings.auth_token_ttl_days),
            )
        )
        return AuthResponse(
            access_token=token,
            user=UserProfile(id=user.id, username=user.username, display_name=user.display_name),
        )
