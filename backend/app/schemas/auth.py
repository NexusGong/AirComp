from pydantic import BaseModel


class UserLogin(BaseModel):
    username: str
    password: str
    remember: bool = True


class AccountLogin(BaseModel):
    """手机号或用户名 + 密码登录"""
    account: str
    password: str


class SetPasswordRequest(BaseModel):
    """注册后设置用户名与密码（用户名可选，不传则保留当前）"""
    username: str | None = None
    password: str


class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    phone: str | None = None
    avatar_img: str | None = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    sub: int
    exp: int
    type: str = "access"


# 手机号验证码登录/注册
class SmsSendRequest(BaseModel):
    phone: str


class SmsSendResponse(BaseModel):
    message: str
    phone: str
    expire_minutes: int = 5
    user_exists: bool


class SmsLoginRequest(BaseModel):
    phone: str
    code: str


class SmsRegisterRequest(BaseModel):
    phone: str
    code: str
    username: str
