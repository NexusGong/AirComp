import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user

logger = logging.getLogger(__name__)
from app.models import User, MachineClient, MachineSupplier, MachineCompare
from app.schemas import (
    MachineClientCreate,
    MachineClientUpdate,
    MachineClientResponse,
    SmartParseRequest,
    BatchClientsCreate,
    BatchClientsResponse,
    BatchSuppliersCreate,
    BatchSuppliersResponse,
    MachineSupplierCreate,
    MachineSupplierUpdate,
    MachineSupplierResponse,
    MachineCompareCreate,
    MachineCompareResponse,
)
from app.services.doubao import parse_equipment_text, parse_equipment_text_supplier

router = APIRouter(prefix="/machines", tags=["machines"])
ADMIN_ID = 999


def _client_query(db: Session, user: User):
    if user.id == ADMIN_ID:
        return db.query(MachineClient).filter()
    return db.query(MachineClient).filter(MachineClient.user_id == user.id)


def _supplier_query(db: Session):
    return db.query(MachineSupplier).filter()


def _compare_query(db: Session, user: User):
    return db.query(MachineCompare).filter(MachineCompare.user_id == user.id)


# ---------- Client ----------
@router.get("/clients", response_model=list[MachineClientResponse])
def list_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _client_query(db, current_user).all()


@router.post("/smart-parse")
async def smart_parse_clients(
    body: SmartParseRequest,
    current_user: User = Depends(get_current_user),
):
    """智能录入：用豆包大模型从粘贴文本/表格中解析出多条客户设备记录"""
    print(f"[AirComp] smart-parse 收到请求, text_len={len(body.text or '')}", flush=True)
    logger.info("smart-parse: 收到请求, text_len=%d", len(body.text or ""))
    try:
        records = await parse_equipment_text(body.text)
        logger.info("smart-parse: 解析完成, records=%d", len(records))
    except ValueError as e:
        logger.warning("smart-parse: 解析失败: %s", e)
        raise HTTPException(status_code=502, detail=str(e))
    return {"records": records}


@router.post("/smart-parse-supplier")
async def smart_parse_suppliers(
    body: SmartParseRequest,
    current_user: User = Depends(get_current_user),
):
    """智能录入：用豆包大模型从粘贴文本/表格中解析出多条供应商设备记录"""
    print(f"[AirComp] smart-parse-supplier 收到请求, text_len={len(body.text or '')}", flush=True)
    logger.info("smart-parse-supplier: 收到请求, text_len=%d", len(body.text or ""))
    try:
        records = await parse_equipment_text_supplier(body.text)
        logger.info("smart-parse-supplier: 解析完成, records=%d", len(records))
    except ValueError as e:
        logger.warning("smart-parse-supplier: 解析失败: %s", e)
        raise HTTPException(status_code=502, detail=str(e))
    return {"records": records}


@router.post("/clients/batch", response_model=BatchClientsResponse)
def batch_create_clients(
    body: BatchClientsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量创建客户设备，已存在的（同公司同编号）跳过"""
    created = 0
    skipped = 0
    results = []
    for data in body.items:
        existing = db.query(MachineClient).filter(
            MachineClient.name == data.name,
            MachineClient.no == data.no,
        ).first()
        if existing:
            skipped += 1
            results.append({"name": data.name, "no": data.no, "status": "skipped", "detail": "该客户该编号已存在"})
            continue
        row = MachineClient(
            user_id=current_user.id,
            name=data.name,
            no=data.no,
            model=data.model,
            run_time=data.run_time,
            load_time=data.load_time,
            ori_power=data.ori_power,
            air=data.air,
            brand=data.brand,
            is_FC=1 if data.is_FC else 0,
            origin_pre=data.origin_pre,
            actual_pre=data.actual_pre,
            collect_time=data.collect_time,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        created += 1
        results.append({"name": data.name, "no": data.no, "status": "created", "id": row.id})
    return BatchClientsResponse(created=created, skipped=skipped, results=results)


@router.post("/clients", response_model=MachineClientResponse)
def create_client(
    data: MachineClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(MachineClient).filter(
        MachineClient.name == data.name,
        MachineClient.no == data.no,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该客户该编号已存在")
    row = MachineClient(
        user_id=current_user.id,
        name=data.name,
        no=data.no,
        model=data.model,
        run_time=data.run_time,
        load_time=data.load_time,
        ori_power=data.ori_power,
        air=data.air,
        brand=data.brand,
        is_FC=1 if data.is_FC else 0,
        origin_pre=data.origin_pre,
        actual_pre=data.actual_pre,
        collect_time=data.collect_time,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/clients/{record_id}", response_model=MachineClientResponse)
def get_client(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = _client_query(db, current_user).filter(MachineClient.id == record_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="记录不存在")
    return row


@router.put("/clients/{record_id}", response_model=MachineClientResponse)
def update_client(
  record_id: int,
  data: MachineClientUpdate,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user),
):
    row = _client_query(db, current_user).filter(MachineClient.id == record_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="记录不存在")
    d = data.model_dump(exclude_unset=True)
    if "is_FC" in d and isinstance(d["is_FC"], bool):
        d["is_FC"] = 1 if d["is_FC"] else 0
    for k, v in d.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/clients/{record_id}")
def delete_client(
  record_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user),
):
    row = _client_query(db, current_user).filter(MachineClient.id == record_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(row)
    db.commit()
    return {"message": "已删除"}


# ---------- Supplier ----------
@router.get("/suppliers", response_model=list[MachineSupplierResponse])
def list_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _supplier_query(db).all()


@router.post("/suppliers/batch", response_model=BatchSuppliersResponse)
def batch_create_suppliers(
    body: BatchSuppliersCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量创建供应商设备，已存在的（同供应商同型号）跳过"""
    created = 0
    skipped = 0
    results = []
    for data in body.items:
        existing = db.query(MachineSupplier).filter(
            MachineSupplier.name == data.name,
            MachineSupplier.model == data.model,
        ).first()
        if existing:
            skipped += 1
            results.append({"name": data.name, "model": data.model, "status": "skipped", "detail": "该供应商该型号已存在"})
            continue
        energy_con_min = data.energy_con / 60
        row = MachineSupplier(
            user_id=current_user.id,
            name=data.name,
            no=data.no,
            model=data.model,
            ori_power=data.ori_power,
            air=data.air,
            brand=data.brand,
            is_FC=1 if data.is_FC else 0,
            origin_pre=data.origin_pre,
            energy_con=data.energy_con,
            energy_con_min=energy_con_min,
            collect_time=data.collect_time,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        created += 1
        results.append({"name": data.name, "model": data.model, "status": "created", "id": row.id})
    return BatchSuppliersResponse(created=created, skipped=skipped, results=results)


@router.post("/suppliers", response_model=MachineSupplierResponse)
def create_supplier(
  data: MachineSupplierCreate,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user),
):
    existing = db.query(MachineSupplier).filter(
        MachineSupplier.name == data.name,
        MachineSupplier.model == data.model,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该供应商该型号已存在")
    energy_con_min = data.energy_con / 60
    row = MachineSupplier(
        user_id=current_user.id,
        name=data.name,
        no=data.no,
        model=data.model,
        ori_power=data.ori_power,
        air=data.air,
        brand=data.brand,
        is_FC=1 if data.is_FC else 0,
        origin_pre=data.origin_pre,
        energy_con=data.energy_con,
        energy_con_min=energy_con_min,
        collect_time=data.collect_time,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/suppliers/{record_id}", response_model=MachineSupplierResponse)
def get_supplier(
  record_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user),
):
    row = _supplier_query(db).filter(MachineSupplier.id == record_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="记录不存在")
    return row


@router.put("/suppliers/{record_id}", response_model=MachineSupplierResponse)
def update_supplier(
  record_id: int,
  data: MachineSupplierUpdate,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user),
):
    row = _supplier_query(db).filter(MachineSupplier.id == record_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="记录不存在")
    d = data.model_dump(exclude_unset=True)
    if "is_FC" in d and isinstance(d["is_FC"], bool):
        d["is_FC"] = 1 if d["is_FC"] else 0
    if "energy_con" in d and "energy_con_min" not in d:
        d["energy_con_min"] = d["energy_con"] / 60
    for k, v in d.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/suppliers/{record_id}")
def delete_supplier(
  record_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user),
):
    row = _supplier_query(db).filter(MachineSupplier.id == record_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(row)
    db.commit()
    return {"message": "已删除"}


# ---------- Compare ----------
@router.get("/compare", response_model=list[MachineCompareResponse])
def list_compare(
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user),
):
    return _compare_query(db, current_user).all()


@router.post("/compare", response_model=MachineCompareResponse)
def create_compare(
  data: MachineCompareCreate,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user),
):
    row = MachineCompare(
        user_id=current_user.id,
        company_name=data.company_name,
        client_no=data.client_no,
        client_brand=data.client_brand,
        client_model=data.client_model,
        supplier_name=data.supplier_name,
        supplier_no=data.supplier_no,
        supplier_brand=data.supplier_brand,
        supplier_model=data.supplier_model,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/compare/{record_id}")
def delete_compare(
  record_id: int,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user),
):
    row = _compare_query(db, current_user).filter(MachineCompare.id == record_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(row)
    db.commit()
    return {"message": "已删除"}


# ---------- Options for forms ----------
@router.get("/options")
def get_options(
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user),
):
    clients = _client_query(db, current_user).all()
    suppliers = _supplier_query(db).all()
    return {
        "company_name": list({c.name for c in clients if c.name}),
        "client_no": list({c.no for c in clients if c.no is not None}),
        "client_brand": list({c.brand for c in clients if c.brand}),
        "client_model": list({c.model for c in clients if c.model}),
        "supplier_name": list({s.name for s in suppliers if s.name}),
        "supplier_no": list({s.no for s in suppliers if s.no is not None}),
        "supplier_brand": list({s.brand for s in suppliers if s.brand}),
        "supplier_model": list({s.model for s in suppliers if s.model}),
    }
