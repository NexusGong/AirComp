import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models import User, EnergyReport

router = APIRouter(prefix="/reports", tags=["reports"])

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app", "reports")


@router.get("")
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出当前用户的能耗计算报告，按创建时间倒序。"""
    rows = (
        db.query(EnergyReport)
        .filter(EnergyReport.user_id == current_user.id)
        .order_by(EnergyReport.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "title": r.title,
            "company_name": r.company_name,
            "source": r.source,
            "energy_savings_kwh": r.energy_savings_kwh,
            "energy_savings_cost": float(r.energy_savings_cost) if r.energy_savings_cost is not None else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "filename": r.filename,
        }
        for r in rows
    ]


@router.get("/{report_id}")
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """单条报告详情。"""
    report = (
        db.query(EnergyReport)
        .filter(EnergyReport.id == report_id, EnergyReport.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return {
        "id": report.id,
        "title": report.title,
        "company_name": report.company_name,
        "source": report.source,
        "energy_savings_kwh": report.energy_savings_kwh,
        "energy_savings_cost": float(report.energy_savings_cost) if report.energy_savings_cost is not None else None,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "filename": report.filename,
    }


@router.get("/{report_id}/download")
def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """下载报告 Excel 文件。"""
    report = (
        db.query(EnergyReport)
        .filter(EnergyReport.id == report_id, EnergyReport.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    filepath = os.path.join(REPORTS_DIR, report.filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    download_name = (report.company_name or report.title or "节能量计算").strip()
    if not download_name:
        download_name = "节能量计算"
    safe_name = "".join(c for c in download_name if c not in r'\/:*?"<>|').strip() or "节能量计算"
    return FileResponse(
        filepath,
        filename=f"{safe_name}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.delete("/{report_id}")
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除报告及对应文件。"""
    report = (
        db.query(EnergyReport)
        .filter(EnergyReport.id == report_id, EnergyReport.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    filepath = os.path.join(REPORTS_DIR, report.filename)
    try:
        if os.path.isfile(filepath):
            os.remove(filepath)
    except OSError:
        pass
    db.delete(report)
    db.commit()
    return {"message": "已删除"}
