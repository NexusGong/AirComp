import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.api.deps import get_db, get_current_user
from app.models import User, MachineClient, MachineSupplier, MachineCompare, EnergyReport
from app.services.cal_func import final_results_excel
from app.services.device_match import (
    client_orm_to_dict,
    recommend_suppliers_multi,
)

router = APIRouter(prefix="/calculate", tags=["calculate"])

# 生成文件存放目录（相对于 backend 根目录）
_BACKEND_APP = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DOWNLOAD_DIR = os.path.join(_BACKEND_APP, "app", "download")
REPORTS_DIR = os.path.join(_BACKEND_APP, "app", "reports")

ADMIN_ID = 999


def _save_report(
    db: Session,
    user_id: int,
    source: str,
    filepath: str,
    company_name: str,
    energy_savings_kwh: int,
    energy_savings_cost: float | None = None,
) -> EnergyReport:
    """将生成的 Excel 复制到 reports 目录并创建报告记录。"""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    unique_name = f"report_{uuid.uuid4().hex}.xlsx"
    dest_path = os.path.join(REPORTS_DIR, unique_name)
    shutil.copy2(filepath, dest_path)
    title = f"{company_name} 节能量计算" if company_name else "节能量计算"
    report = EnergyReport(
        user_id=user_id,
        title=title,
        source=source,
        company_name=company_name or None,
        filename=unique_name,
        energy_savings_kwh=energy_savings_kwh,
        energy_savings_cost=float(energy_savings_cost) if energy_savings_cost is not None else None,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


class CalculateRequest(BaseModel):
    compare_ids: list[int]
    running_hours_per_year: int | None = 8000
    electricity_price: float | None = None
    default_ser_p: float | None = None
    default_por: float | None = None
    empty_waste_ratio: float | None = None
    pressure_drop_ratio: float | None = None


class RecommendRequest(BaseModel):
    company_name: str
    client_nos: list[int] | None = None  # 空则该公司下全部客户机
    margin_ratio: float = 1.1
    strategy: str = "efficiency"  # "efficiency" | "capacity"
    use_actual_flow: bool = True  # True=按实际用气量推荐，False=按额定用气量推荐（二者为组合上限口径）
    schemes_only: bool = False  # True=仅返回选型方案不生成 Excel；False=生成 Excel 并返回节能量


class RunWithParamsRequest(BaseModel):
    """确认参数后提交计算：原有设备、选型设备及计算参数均可修改。"""
    company_name: str
    machines: list[dict]  # 原有设备
    new_eq: list[dict]    # 选型设备
    running_hours_per_year: int = 8000  # 年运行时间（小时）
    electricity_price: float | None = None  # 电费 元/kWh
    default_ser_p: float | None = None   # 服务系数默认值（未设则按品牌）
    default_por: float | None = None     # 变频加载比例默认值（未设则按品牌）
    empty_waste_ratio: float | None = None   # 空载浪费系数，默认 0.4
    pressure_drop_ratio: float | None = None  # 压降浪费系数，默认 0.07


@router.post("")
def run_calculate(
    body: CalculateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    compare_ids = body.compare_ids
    if not compare_ids:
        raise HTTPException(status_code=400, detail="请至少选择一条对比数据")
    machines = []
    new_eq = []
    company_name = None
    for data_id in compare_ids:
        comp = db.query(MachineCompare).filter(
            MachineCompare.id == data_id,
            MachineCompare.user_id == current_user.id,
        ).first()
        if not comp:
            raise HTTPException(status_code=404, detail=f"对比记录 {data_id} 不存在")
        client = db.query(MachineClient).filter(
            and_(
                MachineClient.name == comp.company_name,
                MachineClient.no == comp.client_no,
            ),
        ).first()
        if not client:
            raise HTTPException(status_code=404, detail=f"未找到客户机: {comp.company_name} / {comp.client_no}")
        company_name = client.name
        machines.append({
            "no": client.no,
            "model": client.model,
            "run_time": client.run_time,
            "load_time": client.load_time,
            "ori_power": int(client.ori_power),
            "air": float(client.air),
            "brand": client.brand,
            "isFC": bool(client.is_FC),
            "origin_pre": float(client.origin_pre),
            "actucal_pre": float(client.actual_pre),
        })
    for data_id in compare_ids:
        comp = db.query(MachineCompare).filter(
            MachineCompare.id == data_id,
            MachineCompare.user_id == current_user.id,
        ).first()
        if not comp:
            continue
        supp = db.query(MachineSupplier).filter(
            and_(
                MachineSupplier.name == comp.supplier_name,
                MachineSupplier.no == comp.supplier_no,
            ),
        ).first()
        if not supp:
            raise HTTPException(status_code=404, detail=f"未找到供应商机: {comp.supplier_name} / {comp.supplier_no}")
        new_eq.append({
            "brand": supp.brand,
            "model": supp.model,
            "ori_power": int(supp.ori_power),
            "air": float(supp.air),
            "isFC": bool(supp.is_FC),
            "energy_con": float(supp.energy_con),
            "energy_con_min": float(supp.energy_con_min),
        })
    safe_name = "".join(c for c in str(company_name or "未命名") if c not in r'\/:*?"<>|').strip() or "未命名"
    running_hours = body.running_hours_per_year if body.running_hours_per_year is not None else 8000
    calc_params = {}
    if body.default_ser_p is not None:
        calc_params["default_ser_p"] = body.default_ser_p
    if body.default_por is not None:
        calc_params["default_por"] = body.default_por
    if body.empty_waste_ratio is not None:
        calc_params["empty_waste_ratio"] = body.empty_waste_ratio
    if body.pressure_drop_ratio is not None:
        calc_params["pressure_drop_ratio"] = body.pressure_drop_ratio
    filepath, energy_savings_kwh = final_results_excel(
        company_name or "未命名",
        machines,
        new_eq,
        DOWNLOAD_DIR,
        running_hours_per_year=running_hours,
        calc_params=calc_params if calc_params else None,
    )
    energy_savings_cost = None
    if body.electricity_price is not None and body.electricity_price >= 0:
        energy_savings_cost = round(energy_savings_kwh * body.electricity_price, 2)
    report = _save_report(
        db, current_user.id, "manual", filepath, safe_name,
        energy_savings_kwh, energy_savings_cost,
    )
    filename = os.path.basename(filepath)
    result = {
        "message": "生成成功，已加入历史报告",
        "filename": filename,
        "company_name": safe_name,
        "report_id": report.id,
        "energy_savings_kwh": energy_savings_kwh,
    }
    if energy_savings_cost is not None:
        result["energy_savings_cost"] = energy_savings_cost
    return result


def _client_query_by_user(db: Session, user: User):
    if user.id == ADMIN_ID:
        return db.query(MachineClient)
    return db.query(MachineClient).filter(MachineClient.user_id == user.id)


@router.post("/recommend")
def run_recommend(
    body: RecommendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """根据客户公司及机器编号，自动推荐供应商机型并生成节能计算 Excel。"""
    q = _client_query_by_user(db, current_user).filter(MachineClient.name == body.company_name)
    if body.client_nos is not None and len(body.client_nos) > 0:
        q = q.filter(MachineClient.no.in_(body.client_nos))
    clients = q.order_by(MachineClient.no).all()
    if not clients:
        raise HTTPException(
            status_code=404,
            detail=f"未找到客户设备：公司「{body.company_name}」" + (
                f"、编号 {body.client_nos}" if body.client_nos else ""
            ),
        )
    suppliers = db.query(MachineSupplier).filter(MachineSupplier.name.isnot(None)).all()
    if not suppliers:
        raise HTTPException(status_code=404, detail="暂无供应商设备数据，请先录入供应商设备")

    machines = [client_orm_to_dict(c) for c in clients]
    new_eq, scheme_primary, schemes_all, summary = recommend_suppliers_multi(
        machines,
        suppliers,
        margin_ratio=body.margin_ratio,
        max_units=getattr(body, "max_units", 6),
        use_caliber_a=body.use_actual_flow,
    )
    if not new_eq:
        raise HTTPException(status_code=400, detail=summary or "无法生成推荐方案")

    safe_name = "".join(c for c in str(body.company_name) if c not in r'\/:*?"<>|').strip() or "未命名"
    recommended_scheme = [
        {"brand": s.get("brand"), "model": s.get("model"), "count": cnt}
        for s, cnt in scheme_primary
    ]
    def _clean_new_eq_item(u):
        return {
            "brand": u.get("brand"),
            "model": u.get("model"),
            "ori_power": int(u.get("ori_power") or 0),
            "air": float(u.get("_air") or u.get("air") or 0),
            "isFC": bool(u.get("isFC")),
            "energy_con": float(u.get("energy_con") or 0),
            "energy_con_min": float(u.get("energy_con_min") or 0),
        }
    new_eq_serializable = [_clean_new_eq_item(u) for u in new_eq]
    base = {
        "message": "生成成功",
        "company_name": safe_name,
        "summary": summary,
        "recommended_scheme": recommended_scheme,
        "recommended_schemes": schemes_all,
        "machines": machines,
        "new_eq": new_eq_serializable,
    }
    if body.schemes_only:
        return base

    company_name = body.company_name or "未命名"
    filepath, energy_savings_kwh = final_results_excel(company_name, machines, new_eq, DOWNLOAD_DIR)
    report = _save_report(
        db, current_user.id, "dialogue", filepath, safe_name,
        energy_savings_kwh, None,
    )
    filename = os.path.basename(filepath)
    return {
        **base,
        "filename": filename,
        "report_id": report.id,
        "energy_savings_kwh": energy_savings_kwh,
    }


@router.post("/run-with-params")
def run_with_params(
    body: RunWithParamsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """按弹窗中确认的参数（可修改的原有设备、选型设备、年运行时间、电费）执行节能计算并生成 Excel。"""
    company_name = body.company_name or "未命名"
    safe_name = "".join(c for c in str(company_name) if c not in r'\/:*?"<>|').strip() or "未命名"
    machines = _normalize_machines(body.machines)
    new_eq = _normalize_new_eq(body.new_eq)
    if len(machines) != len(new_eq):
        raise HTTPException(status_code=400, detail="原有设备与选型设备数量须一致")
    calc_params = {}
    if body.default_ser_p is not None:
        calc_params["default_ser_p"] = body.default_ser_p
    if body.default_por is not None:
        calc_params["default_por"] = body.default_por
    if body.empty_waste_ratio is not None:
        calc_params["empty_waste_ratio"] = body.empty_waste_ratio
    if body.pressure_drop_ratio is not None:
        calc_params["pressure_drop_ratio"] = body.pressure_drop_ratio
    filepath, energy_savings_kwh = final_results_excel(
        company_name,
        machines,
        new_eq,
        DOWNLOAD_DIR,
        running_hours_per_year=body.running_hours_per_year,
        calc_params=calc_params if calc_params else None,
    )
    energy_savings_cost = None
    if body.electricity_price is not None and body.electricity_price >= 0:
        energy_savings_cost = round(energy_savings_kwh * body.electricity_price, 2)
    report = _save_report(
        db, current_user.id, "dialogue", filepath, safe_name,
        energy_savings_kwh, energy_savings_cost,
    )
    filename = os.path.basename(filepath)
    result = {
        "message": "生成成功，已加入历史报告",
        "filename": filename,
        "report_id": report.id,
        "energy_savings_kwh": energy_savings_kwh,
    }
    if energy_savings_cost is not None:
        result["energy_savings_cost"] = energy_savings_cost
    return result


def _normalize_machines(machines: list[dict]) -> list[dict]:
    out = []
    for m in machines:
        out.append({
            "no": int(m.get("no") or 0),
            "model": str(m.get("model") or ""),
            "run_time": int(m.get("run_time") or 0),
            "load_time": int(m.get("load_time") or 0),
            "ori_power": int(m.get("ori_power") or 0),
            "air": float(m.get("air") or 0),
            "brand": str(m.get("brand") or ""),
            "isFC": bool(m.get("isFC")),
            "origin_pre": float(m.get("origin_pre") or 0),
            "actucal_pre": float(m.get("actucal_pre") or m.get("actual_pre") or 0),
        })
    return out


def _normalize_new_eq(new_eq: list[dict]) -> list[dict]:
    out = []
    for e in new_eq:
        out.append({
            "brand": str(e.get("brand") or ""),
            "model": str(e.get("model") or ""),
            "ori_power": int(e.get("ori_power") or 0),
            "air": float(e.get("air") or 0),
            "isFC": bool(e.get("isFC")),
            "energy_con": float(e.get("energy_con") or 0),
            "energy_con_min": float(e.get("energy_con_min") or 0),
        })
    return out


@router.get("/download")
def download_file(
    filename: str,
    current_user: User = Depends(get_current_user),
):
    if not filename or ".." in filename or filename.startswith("/"):
        raise HTTPException(status_code=400, detail="无效文件名")
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(filepath, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
