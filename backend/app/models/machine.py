from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from app.db.session import Base


class MachineClient(Base):
    __tablename__ = "machine_client"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    name = Column(String(140))
    no = Column(Integer)
    model = Column(String(140))
    run_time = Column(Integer)
    load_time = Column(Integer)
    ori_power = Column(DECIMAL(20, 5))
    air = Column(DECIMAL(20, 2))
    brand = Column(String(10))
    is_FC = Column(Integer)
    origin_pre = Column(DECIMAL(20, 2))
    actual_pre = Column(DECIMAL(20, 2))
    collect_time = Column(Date, default=datetime.now)
    timestamp = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="machine_clients")

    col_names = [
        "id", "user_id", "name", "no", "model", "run_time", "load_time",
        "ori_power", "air", "brand", "is_FC", "origin_pre", "actual_pre",
        "collect_time", "timestamp",
    ]


class MachineSupplier(Base):
    __tablename__ = "machine_supplier"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    name = Column(String(140))
    no = Column(Integer)
    model = Column(String(140))
    ori_power = Column(DECIMAL(20, 5))
    air = Column(DECIMAL(20, 2))
    brand = Column(String(10))
    is_FC = Column(Integer)
    origin_pre = Column(DECIMAL(20, 2))
    energy_con = Column(DECIMAL(20, 2))
    energy_con_min = Column(DECIMAL(20, 4))
    collect_time = Column(Date, default=datetime.now)
    timestamp = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="machine_suppliers")


class MachineCompare(Base):
    __tablename__ = "machine_compare"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    company_name = Column(String(140))
    client_no = Column(Integer)
    client_brand = Column(String(140))
    client_model = Column(String(140))
    supplier_name = Column(String(140))
    supplier_no = Column(Integer)
    supplier_brand = Column(String(140))
    supplier_model = Column(String(140))
    timestamp = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="machine_compare")
