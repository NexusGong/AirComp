from datetime import datetime
from app.database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=False, index=True)
    password = Column(String(128), nullable=False)
    avatar_img = Column(String(256), default="/static/asset/default_avatar.jpg", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", back_populates="author")
    machine_clients = relationship("MachineClient", back_populates="user")
    machine_suppliers = relationship("MachineSupplier", back_populates="user")
    machine_compares = relationship("MachineCompare", back_populates="user")

    def __repr__(self):
        return f"<User {self.username}>"


class Post(Base):
    __tablename__ = "post"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    body = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    author = relationship("User", back_populates="posts")

    def __repr__(self):
        return f"<Post {self.body[:30]}>"
