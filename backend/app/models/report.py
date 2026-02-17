"""能耗计算历史报告"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from app.db.session import Base


class EnergyReport(Base):
    __tablename__ = "energy_report"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    title = Column(String(200), nullable=True)  # 如「XX公司 节能量计算」
    source = Column(String(20), nullable=False)  # "manual" | "dialogue"
    company_name = Column(String(140), nullable=True)
    filename = Column(String(120), nullable=False)  # 存储文件名，如 report_{uuid}.xlsx
    energy_savings_kwh = Column(Integer, nullable=True)  # 年总节电量 kWh
    energy_savings_cost = Column(DECIMAL(20, 2), nullable=True)  # 年节约电费
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="energy_reports")
