# backend/services/conflict_resolution_service.py
# Service for resolving sync conflicts with 3-way merge algorithm

from sqlalchemy.orm import Session
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import structlog
import json

from app.models.sync_models import ConflictRecord, SyncQueueItem, ResolutionStrategy, SyncStatus
from app.repositories.sync_repositories import ConflictRepository, SyncQueueRepository

logger = structlog.get_logger(__name__)


class ConflictResolutionService:
    def __init__(self, db: Session):
        self.db = db
        self.conflict_repo = ConflictRepository(db)
        self.queue_repo = SyncQueueRepository(db)

    def resolve_conflict(
        self,
        conflict_id: str,
        resolution_strategy: ResolutionStrategy,
        resolved_data: Optional[Dict] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Resolve a conflict using specified strategy"""
        conflict = self.conflict_repo.get_by_id(conflict_id)
        if not conflict:
            return False, 'Conflict not found'

        logger.info(
            'resolving_conflict',
            conflict_id=conflict_id,
            strategy=resolution_strategy.value,
        )

        try:
            if resolution_strategy == ResolutionStrategy.AUTO_MERGE:
                merged_data = self.perform_3way_merge(conflict)
                if merged_data is None:
                    return False, 'Cannot auto-merge: overlapping fields detected'
                resolved_data = merged_data

            elif resolution_strategy == ResolutionStrategy.KEEP_LOCAL:
                resolved_data = conflict.our_data

            elif resolution_strategy == ResolutionStrategy.USE_SERVER:
                resolved_data = conflict.server_data

            elif resolution_strategy == ResolutionStrategy.MANUAL_MERGE:
                if not resolved_data:
                    return False, 'Manual merge requires resolved_data'

            # Update conflict record
            self.conflict_repo.resolve(conflict_id, resolution_strategy, resolved_data)

            # Update sync queue item with resolved data
            queue_item = self.queue_repo.get_by_id(conflict.sync_queue_item_id)
            if queue_item:
                queue_item.payload = resolved_data
                queue_item.status = SyncStatus.RETRY_PENDING
                queue_item.next_retry_at = datetime.utcnow()
                self.db.commit()

            logger.info(
                'conflict_resolved_successfully',
                conflict_id=conflict_id,
                strategy=resolution_strategy.value,
            )

            return True, None

        except Exception as e:
            error_msg = str(e)
            logger.error(
                'conflict_resolution_failed',
                conflict_id=conflict_id,
                error=error_msg,
            )
            return False, error_msg

    def perform_3way_merge(self, conflict: ConflictRecord) -> Optional[Dict]:
        """Implement 3-way merge algorithm (ours, base, theirs)"""
        base = conflict.base_data or {}
        ours = conflict.our_data or {}
        theirs = conflict.server_data or {}

        # Get all keys from all three versions
        all_keys = set()
        all_keys.update(base.keys())
        all_keys.update(ours.keys())
        all_keys.update(theirs.keys())

        merged = {}
        conflicting_fields = []

        for key in all_keys:
            base_val = base.get(key)
            our_val = ours.get(key)
            their_val = theirs.get(key)

            # If no change in any version, include base value
            if base_val == our_val == their_val:
                merged[key] = base_val
                continue

            # If only we changed, include our value
            if our_val != base_val and their_val == base_val:
                merged[key] = our_val
                continue

            # If only they changed, include their value
            if their_val != base_val and our_val == base_val:
                merged[key] = their_val
                continue

            # If both changed to same value, use that value
            if our_val == their_val:
                merged[key] = our_val
                continue

            # Both changed to different values - conflict!
            conflicting_fields.append(key)

        # If there are conflicting fields, we can't auto-merge
        if conflicting_fields:
            conflict.overlapping_fields = conflicting_fields
            self.db.commit()
            logger.info(
                'auto_merge_failed_overlapping_fields',
                conflict_id=conflict.id,
                fields=conflicting_fields,
            )
            return None

        # Update conflict with merge info
        conflict.can_auto_merge = True
        conflict.overlapping_fields = []
        self.db.commit()

        logger.info(
            'auto_merge_successful',
            conflict_id=conflict.id,
            merged_keys=list(merged.keys()),
        )

        return merged

    def analyze_conflicts(self) -> Dict:
        """Analyze all unresolved conflicts for patterns"""
        conflicts = self.conflict_repo.get_unresolved()

        analysis = {
            'total_unresolved': len(conflicts),
            'can_auto_merge': 0,
            'requires_manual_merge': 0,
            'by_entity_type': {},
            'overlapping_field_patterns': {},
        }

        for conflict in conflicts:
            if conflict.can_auto_merge:
                analysis['can_auto_merge'] += 1
            else:
                analysis['requires_manual_merge'] += 1

            # Count by entity type
            entity_type = conflict.entity_type
            if entity_type not in analysis['by_entity_type']:
                analysis['by_entity_type'][entity_type] = 0
            analysis['by_entity_type'][entity_type] += 1

            # Track overlapping field patterns
            for field in conflict.overlapping_fields:
                if field not in analysis['overlapping_field_patterns']:
                    analysis['overlapping_field_patterns'][field] = 0
                analysis['overlapping_field_patterns'][field] += 1

        return analysis

    def suggest_resolution(self, conflict: ConflictRecord) -> Optional[ResolutionStrategy]:
        """Suggest resolution strategy based on conflict analysis"""
        if conflict.can_auto_merge:
            return ResolutionStrategy.AUTO_MERGE

        # If our version is newer and we made fewer changes, prefer ours
        our_changes = self.count_changes(conflict.base_data or {}, conflict.our_data)
        their_changes = self.count_changes(conflict.base_data or {}, conflict.server_data)

        if our_changes <= their_changes:
            return ResolutionStrategy.KEEP_LOCAL
        else:
            return ResolutionStrategy.USE_SERVER

    def count_changes(self, base: Dict, version: Dict) -> int:
        """Count number of fields changed from base"""
        count = 0
        all_keys = set()
        all_keys.update(base.keys())
        all_keys.update(version.keys())

        for key in all_keys:
            if base.get(key) != version.get(key):
                count += 1

        return count

    def batch_resolve_auto_mergeable(self) -> Tuple[int, int]:
        """Automatically resolve all conflicts that can be auto-merged"""
        conflicts = self.conflict_repo.get_unresolved()
        success_count = 0
        failure_count = 0

        for conflict in conflicts:
            if not conflict.can_auto_merge:
                continue

            merged = self.perform_3way_merge(conflict)
            if merged is not None:
                success, error = self.resolve_conflict(
                    conflict.id,
                    ResolutionStrategy.AUTO_MERGE,
                    merged,
                )
                if success:
                    success_count += 1
                else:
                    failure_count += 1
            else:
                failure_count += 1

        logger.info(
            'batch_auto_merge_completed',
            success_count=success_count,
            failure_count=failure_count,
        )

        return success_count, failure_count

    def get_conflict_diff(self, conflict: ConflictRecord) -> Dict:
        """Get detailed diff for conflict visualization"""
        base = conflict.base_data or {}
        ours = conflict.our_data or {}
        theirs = conflict.server_data or {}

        diff = {
            'added_by_us': {},
            'added_by_them': {},
            'modified_by_us': {},
            'modified_by_them': {},
            'deleted_by_us': {},
            'deleted_by_them': {},
            'conflicting_modifications': {},
        }

        all_keys = set()
        all_keys.update(base.keys())
        all_keys.update(ours.keys())
        all_keys.update(theirs.keys())

        for key in all_keys:
            base_val = base.get(key)
            our_val = ours.get(key)
            their_val = theirs.get(key)

            # Added by us
            if key not in base and our_val is not None and (key not in theirs or their_val is None):
                diff['added_by_us'][key] = our_val

            # Added by them
            if key not in base and their_val is not None and (key not in ours or our_val is None):
                diff['added_by_them'][key] = their_val

            # Modified by us
            if key in base and our_val != base_val and their_val == base_val:
                diff['modified_by_us'][key] = {'before': base_val, 'after': our_val}

            # Modified by them
            if key in base and their_val != base_val and our_val == base_val:
                diff['modified_by_them'][key] = {'before': base_val, 'after': their_val}

            # Deleted by us
            if key in base and our_val is None and their_val is not None:
                diff['deleted_by_us'][key] = {'was': base_val}

            # Deleted by them
            if key in base and their_val is None and our_val is not None:
                diff['deleted_by_them'][key] = {'was': base_val}

            # Conflicting modifications
            if (key in base and our_val != base_val and their_val != base_val and
                our_val != their_val):
                diff['conflicting_modifications'][key] = {
                    'base': base_val,
                    'ours': our_val,
                    'theirs': their_val,
                }

        return diff
