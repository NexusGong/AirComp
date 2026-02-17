from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError

from app.api.deps import get_db, get_current_user
from app.core.security import get_password_hash, create_access_token, verify_password
from app.models import User
from app.schemas import (
    UserResponse, Token, UserCreate, AccountLogin, SetPasswordRequest,
    UpdateProfileRequest, SmsSendRequest, SmsSendResponse, SmsLoginRequest, SmsRegisterRequest,
)
from app.services.sms import is_valid_phone, send_verification_code, verify_code, get_remaining_time

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(data: UpdateProfileRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新用户名、头像等个人资料"""
    u = data.username.strip()
    if len(u) < 3 or len(u) > 20:
        raise HTTPException(status_code=400, detail="用户名需 3–20 个字符")
    other = db.query(User).filter(User.username == u, User.id != current_user.id).first()
    if other:
        raise HTTPException(status_code=400, detail="用户名已被占用")
    current_user.username = u
    if data.avatar_img is not None:
        if len(data.avatar_img) > 256:
            raise HTTPException(status_code=400, detail="头像路径过长")
        current_user.avatar_img = data.avatar_img.strip() or current_user.avatar_img
    db.commit()
    db.refresh(current_user)
    return current_user


# ---------- 用户名/密码登录与注册 ----------

def _normalize_phone(s: str) -> str:
    return s.strip().replace(" ", "").replace("-", "")


def _is_phone(account: str) -> bool:
    p = _normalize_phone(account)
    return len(p) == 11 and p.isdigit() and p.startswith("1")


@router.post("/login", response_model=Token)
def login(data: AccountLogin, db: Session = Depends(get_db)):
    """手机号或用户名 + 密码登录"""
    account = data.account.strip()
    if not account or not data.password:
        raise HTTPException(status_code=400, detail="请输入手机号或用户名和密码")
    if _is_phone(account):
        phone = _normalize_phone(account)
        user = db.query(User).filter(User.phone == phone).first()
    else:
        user = db.query(User).filter(User.username == account).first()
    if not user or not user.password or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="手机号/用户名或密码错误")
    access_token = create_access_token(user.id)
    return Token(access_token=access_token, user=UserResponse.model_validate(user))


@router.post("/set-password")
def set_password(data: SetPasswordRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """注册后设置登录密码（可选同时修改用户名）"""
    if len(data.password) < 4:
        raise HTTPException(status_code=400, detail="密码至少 4 位")
    if data.username is not None:
        u = data.username.strip()
        if len(u) < 3 or len(u) > 20:
            raise HTTPException(status_code=400, detail="用户名需 3–20 个字符")
        other = db.query(User).filter(User.username == u, User.id != current_user.id).first()
        if other:
            raise HTTPException(status_code=400, detail="用户名已被占用")
        current_user.username = u
    current_user.password = get_password_hash(data.password)
    db.commit()
    return {"message": "设置成功"}


@router.post("/register", response_model=Token)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if len(data.username) < 3 or len(data.username) > 20:
        raise HTTPException(status_code=400, detail="用户名需 3–20 个字符")
    user = User(
        username=data.username.strip(),
        password=get_password_hash(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = create_access_token(user.id)
    return Token(access_token=access_token, user=UserResponse.model_validate(user))


# ---------- 手机号验证码登录/注册 ----------

@router.post("/sms/send", response_model=SmsSendResponse)
async def sms_send(data: SmsSendRequest, db: Session = Depends(get_db)):
    phone = data.phone.strip().replace(" ", "").replace("-", "")
    if not is_valid_phone(phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确，请输入以1开头的11位数字")
    remaining = get_remaining_time(phone)
    if remaining > 0:
        raise HTTPException(status_code=429, detail=f"发送过于频繁，请{remaining}秒后再试")
    success = await send_verification_code(phone)
    if not success:
        raise HTTPException(status_code=500, detail="验证码发送失败，请稍后重试")
    user_exists = db.query(User).filter(User.phone == phone).first() is not None
    return SmsSendResponse(message="验证码已发送", phone=phone, expire_minutes=5, user_exists=user_exists)


@router.post("/sms/login", response_model=Token)
def sms_login(data: SmsLoginRequest, db: Session = Depends(get_db)):
    if not verify_code(data.phone, data.code):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")
    phone = data.phone.strip().replace(" ", "").replace("-", "")
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="该手机号未注册，请先注册")
    access_token = create_access_token(user.id)
    return Token(access_token=access_token, user=UserResponse.model_validate(user))


@router.post("/sms/register", response_model=Token)
def sms_register(data: SmsRegisterRequest, db: Session = Depends(get_db)):
    if not verify_code(data.phone, data.code):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")
    phone = data.phone.strip().replace(" ", "").replace("-", "")
    if db.query(User).filter(User.phone == phone).first():
        raise HTTPException(status_code=400, detail="该手机号已注册")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if len(data.username) < 3 or len(data.username) > 20:
        raise HTTPException(status_code=400, detail="用户名需 3–20 个字符")
    # 随机占位密码（bcrypt 最多 72 字节）；用户后续可设置真实密码
    raw = __import__("secrets").token_hex(16)
    # 旧表可能 email NOT NULL：用唯一占位符，避免 INSERT 违反约束被误报为“已存在”
    email_placeholder = f"__phone_{phone}__"
    user = User(
        username=data.username.strip(),
        password=get_password_hash(raw[:72] if len(raw) > 72 else raw),
        phone=phone,
        email=email_placeholder,
    )
    try:
        db.add(user)
        db.commit()
        # 不调用 refresh()，commit 后 id 已回填，避免 refresh 异常导致“已提交却返回 500、下次请求报已存在”
    except IntegrityError as e:
        db.rollback()
        msg = str(e).lower()
        if "not null" in msg or "email" in msg:
            raise HTTPException(
                status_code=500,
                detail="数据库 user 表结构需与模型一致（email 允许为空），请执行: python scripts/fix_user_email_nullable.py",
            ) from e
        raise HTTPException(status_code=400, detail="该手机号或用户名已存在") from e
    except OperationalError as e:
        db.rollback()
        if "no such column" in str(e).lower():
            raise HTTPException(
                status_code=500,
                detail="数据库缺少 user.phone 列，请在 backend 目录执行: python scripts/add_phone_column.py",
            ) from e
        raise HTTPException(status_code=500, detail="数据库操作失败，请稍后重试") from e
    except Exception as e:
        db.rollback()
        raise
    # commit 后 user.id 已由 SQLite 回填，可直接用于 token 和响应
    access_token = create_access_token(user.id)
    return Token(access_token=access_token, user=UserResponse.model_validate(user))
