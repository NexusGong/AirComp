"""分析会话与消息（可选持久化）"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base


class AnalysisSession(Base):
    __tablename__ = "analysis_session"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    title = Column(String(200), default="新建分析")
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="analysis_sessions")
    messages = relationship("AnalysisMessage", back_populates="session", order_by="AnalysisMessage.id")


class AnalysisMessage(Base):
    __tablename__ = "analysis_message"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("analysis_session.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user | assistant
    content = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)

    session = relationship("AnalysisSession", back_populates="messages")
