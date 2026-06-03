# backend/routes/sync_routes.py
# FastAPI routes for sync operations, conflict resolution, and queue management

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import structlog

from app.database import get_db
from app.auth import get_current_user
from app.models.sync_models import (
    SyncQueueItem,
    ConflictRecord,
    SyncStatus,
    ResolutionStrategy,
)
from app.services.sync_service import SyncService
from app.services.conflict_resolution_service import ConflictResolutionService
from app.repositories.sync_repositories import SyncQueueRepository, ConflictRepository
from app.schemas.sync_schemas import (
    SyncItemRequest,
    SyncItemResponse,
    ConflictResponse,
    SyncStatusResponse,
    ResolveConflictRequest,
    ResolveConflictResponse,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix='/api/v1/sync', tags=['sync'])


@router.post('/items', response_model=SyncItemResponse)
async def sync_item(
    request: SyncItemRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Submit a sync item for processing.
    Validates payload, detects conflicts, applies changes.
    """
    logger.info(
        'sync_item_submitted',
        operation_type=request.operation_type,
        entity_id=request.entity_id,
        user_id=current_user.id,
    )

    try:
        queue_repo = SyncQueueRepository(db)

        # Create queue item
        item = queue_repo.create(
            operation_type=request.operation_type,
            entity_type=request.entity_type or 'INSPECTION',
            entity_id=request.entity_id,
            payload=request.payload,
            user_id=current_user.id,
            device_id=request.device_id,
        )

        # Process sync asynchronously
        sync_service = SyncService(db)
        background_tasks.add_task(sync_service.process_sync_item, item)

        return SyncItemResponse(
            id=item.id,
            sync_status='PENDING',
            synced_at=None,
        )

    except ValueError as e:
        logger.error('sync_validation_error', error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'message': str(e), 'fields': {}},
        )
    except Exception as e:
        logger.error('sync_item_error', error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to process sync item',
        )


@router.get('/status', response_model=SyncStatusResponse)
async def get_sync_status(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get current sync queue status for user"""
    logger.info('sync_status_requested', user_id=current_user.id)

    try:
        sync_service = SyncService(db)
        queue_status = sync_service.get_queue_status(current_user.id)
        conflict_status = sync_service.get_conflict_status(current_user.id)

        return SyncStatusResponse(
            online=True,
            queue_status=queue_status,
            conflict_status=conflict_status,
        )

    except Exception as e:
        logger.error('sync_status_error', error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to get sync status',
        )


@router.get('/queue', response_model=List[SyncItemResponse])
async def get_queue_items(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get sync queue items for user, optionally filtered by status"""
    try:
        queue_repo = SyncQueueRepository(db)

        if status:
            try:
                sync_status = SyncStatus[status]
                items = queue_repo.get_by_status(sync_status, current_user.id)
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Invalid status: {status}',
                )
        else:
            items = queue_repo.get_pending_and_retry(current_user.id)

        return [
            SyncItemResponse(
                id=item.id,
                sync_status=item.status.value,
                synced_at=item.synced_at.isoformat() if item.synced_at else None,
            )
            for item in items
        ]

    except Exception as e:
        logger.error('get_queue_error', error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to get queue items',
        )


@router.delete('/queue/{item_id}')
async def delete_queue_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Remove item from sync queue"""
    try:
        queue_repo = SyncQueueRepository(db)
        item = queue_repo.get_by_id(item_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Queue item not found',
            )

        if item.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Cannot delete queue item of another user',
            )

        queue_repo.delete(item_id)
        logger.info('queue_item_deleted', item_id=item_id, user_id=current_user.id)

        return {'message': 'Queue item deleted'}

    except HTTPException:
        raise
    except Exception as e:
        logger.error('delete_queue_error', error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to delete queue item',
        )


@router.get('/conflicts', response_model=List[ConflictResponse])
async def get_conflicts(
    unresolved_only: bool = True,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get conflicts for user"""
    try:
        conflict_repo = ConflictRepository(db)

        if unresolved_only:
            conflicts = conflict_repo.get_unresolved(current_user.id)
        else:
            # Get all non-expired conflicts
            all_conflicts = conflict_repo.db.query(ConflictRecord).filter(
                ConflictRecord.user_id == current_user.id
            ).all()
            conflicts = [c for c in all_conflicts if c.expires_at > datetime.utcnow()]

        return [
            ConflictResponse(
                id=conflict.id,
                entity_type=conflict.entity_type,
                entity_id=conflict.entity_id,
                conflict_type=conflict.conflict_type.value,
                our_version=conflict.our_version,
                server_version=conflict.server_version,
                can_auto_merge=conflict.can_auto_merge,
            )
            for conflict in conflicts
        ]

    except Exception as e:
        logger.error('get_conflicts_error', error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to get conflicts',
        )


@router.post('/resolve-conflict', response_model=ResolveConflictResponse)
async def resolve_conflict(
    request: ResolveConflictRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Resolve a sync conflict using specified strategy"""
    logger.info(
        'conflict_resolution_requested',
        conflict_id=request.conflict_id,
        strategy=request.resolution_strategy,
        user_id=current_user.id,
    )

    try:
        conflict_repo = ConflictRepository(db)
        conflict = conflict_repo.get_by_id(request.conflict_id)

        if not conflict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Conflict not found',
            )

        if conflict.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Cannot resolve conflict of another user',
            )

        # Resolve in background
        conflict_service = ConflictResolutionService(db)

        try:
            resolution_strategy = ResolutionStrategy[request.resolution_strategy]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Invalid resolution strategy: {request.resolution_strategy}',
            )

        success, error = conflict_service.resolve_conflict(
            request.conflict_id,
            resolution_strategy,
            request.resolved_data,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or 'Failed to resolve conflict',
            )

        return ResolveConflictResponse(
            message='Conflict resolved successfully',
            retry_in_seconds=2,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error('conflict_resolution_error', error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to resolve conflict',
        )


@router.get('/conflicts/{conflict_id}/analysis')
async def analyze_conflict(
    conflict_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Analyze conflict for resolution suggestions"""
    try:
        conflict_repo = ConflictRepository(db)
        conflict = conflict_repo.get_by_id(conflict_id)

        if not conflict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Conflict not found',
            )

        if conflict.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Cannot analyze conflict of another user',
            )

        conflict_service = ConflictResolutionService(db)
        diff = conflict_service.get_conflict_diff(conflict)
        suggestion = conflict_service.suggest_resolution(conflict)

        return {
            'conflict_id': conflict_id,
            'diff': diff,
            'suggested_strategy': suggestion.value if suggestion else None,
            'can_auto_merge': conflict.can_auto_merge,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error('conflict_analysis_error', error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to analyze conflict',
        )
