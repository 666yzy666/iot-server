from pydantic import BaseModel, Field


class AuthRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class RegisterRequest(AuthRequest):
    display_name: str = Field(default="", max_length=128)


class UserProfile(BaseModel):
    id: int
    username: str
    display_name: str = ""


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
