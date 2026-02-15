from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel


class MachineClientCreate(BaseModel):
    name: str
    no: int
    model: str
    run_time: int
    load_time: int
    ori_power: float
    air: float
    brand: str
    is_FC: bool  # True=变频
    origin_pre: float
    actual_pre: float
    collect_time: date


class MachineClientUpdate(BaseModel):
    name: str | None = None
    no: int | None = None
    model: str | None = None
    run_time: int | None = None
    load_time: int | None = None
    ori_power: float | None = None
    air: float | None = None
    brand: str | None = None
    is_FC: bool | None = None
    origin_pre: float | None = None
    actual_pre: float | None = None
    collect_time: date | None = None


class MachineClientResponse(BaseModel):
    id: int
    user_id: int | None
    name: str | None
    no: int | None
    model: str | None
    run_time: int | None
    load_time: int | None
    ori_power: Decimal | None
    air: Decimal | None
    brand: str | None
    is_FC: int | None
    origin_pre: Decimal | None
    actual_pre: Decimal | None
    collect_time: date | None
    timestamp: datetime | None

    class Config:
        from_attributes = True


class MachineSupplierCreate(BaseModel):
    name: str
    no: int
    model: str
    ori_power: float
    air: float
    brand: str
    is_FC: bool
    origin_pre: float
    energy_con: float
    collect_time: date


class MachineSupplierUpdate(BaseModel):
    name: str | None = None
    no: int | None = None
    model: str | None = None
    ori_power: float | None = None
    air: float | None = None
    brand: str | None = None
    is_FC: bool | None = None
    origin_pre: float | None = None
    energy_con: float | None = None
    energy_con_min: float | None = None
    collect_time: date | None = None


class MachineSupplierResponse(BaseModel):
    id: int
    user_id: int | None
    name: str | None
    no: int | None
    model: str | None
    ori_power: Decimal | None
    air: Decimal | None
    brand: str | None
    is_FC: int | None
    origin_pre: Decimal | None
    energy_con: Decimal | None
    energy_con_min: Decimal | None
    collect_time: date | None
    timestamp: datetime | None

    class Config:
        from_attributes = True


class SmartParseRequest(BaseModel):
    """智能录入：粘贴文本或表格文本"""
    text: str


class SmartParseRecord(BaseModel):
    """智能解析出的单条客户设备（与 MachineClientCreate 字段一致）"""
    name: str
    no: int
    model: str
    run_time: int = 0
    load_time: int = 0
    ori_power: float = 0
    air: float = 0
    brand: str = "其他"
    is_FC: bool = False
    origin_pre: float = 0.8
    actual_pre: float = 0.8
    collect_time: date


class BatchClientsCreate(BaseModel):
    """批量创建客户设备"""
    items: list[MachineClientCreate]


class BatchClientsResponse(BaseModel):
    created: int
    skipped: int
    results: list[dict]  # [{ "name", "no", "status": "created"|"skipped", "detail"? }]


class BatchSuppliersCreate(BaseModel):
    """批量创建供应商设备"""
    items: list[MachineSupplierCreate]


class BatchSuppliersResponse(BaseModel):
    created: int
    skipped: int
    results: list[dict]


class MachineCompareCreate(BaseModel):
    company_name: str
    client_no: int
    client_brand: str
    client_model: str
    supplier_name: str
    supplier_no: int
    supplier_brand: str
    supplier_model: str


class MachineCompareResponse(BaseModel):
    id: int
    company_name: str | None
    client_no: int | None
    client_brand: str | None
    client_model: str | None
    supplier_name: str | None
    supplier_no: int | None
    supplier_brand: str | None
    supplier_model: str | None
    timestamp: datetime | None
    user_id: int | None

    class Config:
        from_attributes = True
