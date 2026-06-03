"""Bulk import CSV/Excel for masters data"""
import csv
import io
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from loguru import logger

from app.auth.dependencies import require_role
from app.database import get_db_session
from app.repositories.masters_repository import DefectRepository, MachineRepository, FabricRepository
from app.domain.services.masters_service import MastersService

router = APIRouter(prefix="/api/import", tags=["import"])


@router.post("/defects/csv")
async def import_defects_csv(
    file: UploadFile = File(...),
    user: dict = Depends(require_role("ADMIN")),
    session=Depends(get_db_session),
):
    """Import defects from CSV — columns: defect_id, name, category, severity"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Solo se aceptan archivos .csv")

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    rows = list(reader)

    if not rows:
        raise HTTPException(400, "CSV vacío")

    async with session() as db:
        repo = DefectRepository(db)
        svc = MastersService(repo, MachineRepository(db), FabricRepository(db))
        result = await svc.bulk_import_defects(rows)
        await db.commit()

    logger.info("CSV import completed", **result)
    return result
