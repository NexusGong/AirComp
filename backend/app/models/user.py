from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(100), nullable=True)  # 手机号注册占位哈希，不用于登录
    phone = Column(String(20), unique=True, nullable=True, index=True)
    # 保留列以兼容旧库，不再使用
    email = Column(String(50), unique=True, nullable=True, index=True)
    avatar_img = Column(String(120), default="/static/asset/default_avatar.jpg", nullable=False)
    posts = relationship("Post", back_populates="author")
    machine_clients = relationship("MachineClient", back_populates="user")
    machine_suppliers = relationship("MachineSupplier", back_populates="user")
    machine_compare = relationship("MachineCompare", back_populates="user")
    analysis_sessions = relationship("AnalysisSession", back_populates="user")

    def __repr__(self):
        return f"<User {self.username}>"


class Post(Base):
    __tablename__ = "post"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    body = Column(String(140), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

    author = relationship("User", back_populates="posts")

    def __repr__(self):
        return f"<Post {self.body}>"
