"""Batch sync with gzip compression support"""
import gzip
import json
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import Response
from loguru import logger

from app.auth.dependencies import require_role
from app.database import get_db_session
from app.repositories.inspection_repository import InspectionRepository
from app.domain.services.inspection_service import InspectionService

router = APIRouter(prefix="/api/sync", tags=["sync"])

MAX_BATCH = 100


@router.post("/batch")
async def batch_sync(
    request: Request,
    user: dict = Depends(require_role("ANALISTA")),
    session=Depends(get_db_session),
):
    """Accept gzip-compressed JSON batch of inspections"""
    content_encoding = request.headers.get("Content-Encoding", "")
    body = await request.body()

    if "gzip" in content_encoding:
        body = gzip.decompress(body)

    try:
        payload = json.loads(body)
    except Exception:
        raise HTTPException(400, "Invalid JSON payload")

    inspections = payload.get("inspections", [])
    if len(inspections) > MAX_BATCH:
        raise HTTPException(400, f"Batch too large — max {MAX_BATCH}")

    from datetime import datetime

    synced, failed, details = 0, 0, []
    async with session() as db:
        repo = InspectionRepository(db)
        svc = InspectionService(repo)
        for item in inspections:
            try:
                insp = await svc.register_inspection(
                    lote_id=item["lote_id"],
                    analista_id=user["sub"],
                    defect_id=item["defect_id"],
                    comment_text=item["comment_text"],
                    photo_path=item["photo_path"],
                    photo_checksum=item["photo_checksum"],
                    photo_size_kb=item["photo_size_kb"],
                    machine_id=item["machine_id"],
                    check_in=datetime.fromisoformat(item["check_in"]),
                )
                synced += 1
                details.append({"id": str(insp.inspection_id), "status": "ok"})
            except Exception as e:
                failed += 1
                details.append({"status": "error", "reason": str(e)})
        await db.commit()

    result = json.dumps({"synced": synced, "failed": failed, "details": details}).encode()
    if "gzip" in request.headers.get("Accept-Encoding", ""):
        result = gzip.compress(result)
        return Response(content=result, media_type="application/json",
                        headers={"Content-Encoding": "gzip"})
    return Response(content=result, media_type="application/json")
