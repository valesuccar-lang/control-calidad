"""Masters data API routes (defects, machines, fabrics)"""
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.database import get_db_session
from app.auth.dependencies import require_role
from app.repositories.masters_repository import DefectRepository, MachineRepository, FabricRepository
from app.domain.services.masters_service import MastersService
from app.schemas.masters_schemas import DefectResponse, MachineResponse, FabricResponse
from app.monitoring.audit_logger import audit_logger

router = APIRouter()


@router.get("/defects", response_model=dict)
async def get_defects(
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(require_role("ANALISTA", "JEFE_QA", "ADMIN")),
    session = Depends(get_db_session)
):
    """Get list of defect types"""
    try:
        async with session() as db:
            repo = DefectRepository(db)
            defects = await repo.get_active()

            return {
                "total": len(defects),
                "items": [
                    {
                        "defect_id": d.defect_id,
                        "name": d.name,
                        "category": d.category,
                        "severity": d.severity,
                        "status": d.status
                    }
                    for d in defects
                ]
            }

    except Exception as e:
        logger.error("Error getting defects", error=str(e))
        raise HTTPException(status_code=500, detail="Error getting defects")


@router.get("/machines", response_model=dict)
async def get_machines(
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(require_role("ANALISTA", "JEFE_QA", "ADMIN")),
    session = Depends(get_db_session)
):
    """Get list of machines"""
    try:
        async with session() as db:
            repo = MachineRepository(db)
            machines = await repo.get_active()

            return {
                "total": len(machines),
                "items": [
                    {
                        "machine_id": m.machine_id,
                        "name": m.name,
                        "model": m.model,
                        "status": m.status
                    }
                    for m in machines
                ]
            }

    except Exception as e:
        logger.error("Error getting machines", error=str(e))
        raise HTTPException(status_code=500, detail="Error getting machines")


@router.get("/fabrics", response_model=dict)
async def get_fabrics(
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(require_role("ANALISTA", "JEFE_QA", "ADMIN")),
    session = Depends(get_db_session)
):
    """Get list of fabrics"""
    try:
        async with session() as db:
            repo = FabricRepository(db)
            fabrics = await repo.get_active()

            return {
                "total": len(fabrics),
                "items": [
                    {
                        "fabric_id": f.fabric_id,
                        "name": f.name,
                        "description": f.description,
                        "status": f.status
                    }
                    for f in fabrics
                ]
            }

    except Exception as e:
        logger.error("Error getting fabrics", error=str(e))
        raise HTTPException(status_code=500, detail="Error getting fabrics")


@router.post("/import-csv", response_model=dict, status_code=201)
async def import_csv(
    data: dict,
    user: dict = Depends(require_role("ADMIN")),
    session = Depends(get_db_session)
):
    """Bulk import masters data from CSV (ADMIN role required)"""
    try:
        async with session() as db:
            defect_repo = DefectRepository(db)
            machine_repo = MachineRepository(db)
            fabric_repo = FabricRepository(db)
            service = MastersService(defect_repo, machine_repo, fabric_repo)

            results = {}

            # Import defects if provided
            if "defects" in data:
                result = await service.bulk_import_defects(data["defects"])
                results["defects"] = result
                audit_logger.log_masters_imported(
                    user_id=user.get("sub"),
                    entity_type="defect",
                    created_count=result["created"],
                    skipped_count=result["skipped"]
                )

            # Import machines if provided
            if "machines" in data:
                result = await service.bulk_import_machines(data["machines"])
                results["machines"] = result
                audit_logger.log_masters_imported(
                    user_id=user.get("sub"),
                    entity_type="machine",
                    created_count=result["created"],
                    skipped_count=result["skipped"]
                )

            # Import fabrics if provided
            if "fabrics" in data:
                result = await service.bulk_import_fabrics(data["fabrics"])
                results["fabrics"] = result
                audit_logger.log_masters_imported(
                    user_id=user.get("sub"),
                    entity_type="fabric",
                    created_count=result["created"],
                    skipped_count=result["skipped"]
                )

            await db.commit()

            return results

    except Exception as e:
        logger.error("Error importing masters", error=str(e), exc_info=e)
        raise HTTPException(status_code=500, detail="Error importing masters")
