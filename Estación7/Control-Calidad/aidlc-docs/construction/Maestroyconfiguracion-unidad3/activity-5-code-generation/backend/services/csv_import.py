# backend/app/services/csv_import.py
# CSV import service with validation, preview, and async execution

import csv
import io
import json
import uuid
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Session

from app.models import ImportJob, Defect, Machine, Fabric, AuditLog
from app.schemas import (
    CsvValidationResponse, CsvImportPreview, CsvImportResult,
    DefectCreate, MachineCreate, FabricCreate
)
from app.services import (
    MastersService, DuplicateError, ValidationError, NotFoundError
)
import structlog

logger = structlog.get_logger(__name__)


class ImportMode(str, Enum):
    """CSV import mode"""
    INSERT = "INSERT"           # Create new only
    UPDATE = "UPDATE"           # Update existing by name
    UPSERT = "UPSERT"          # Create or update
    SKIP_DUPLICATES = "SKIP"   # Create, skip if name exists


class CsvImportService:
    """Service for CSV import operations"""

    def __init__(self, db: Session):
        self.db = db
        self.service = MastersService(db)

    def validate_csv(
        self,
        file_content: bytes,
        master_type: str
    ) -> CsvValidationResponse:
        """
        Validate CSV structure and content.
        Returns validation result with error details if invalid.
        """
        trace_id = str(uuid.uuid4())
        logger.info(
            "csv_validation_started",
            master_type=master_type,
            trace_id=trace_id
        )

        try:
            # Parse CSV
            text_content = file_content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(text_content))
            rows = list(reader)

            if not rows:
                return CsvValidationResponse(
                    valid=False,
                    error_count=1,
                    errors=["CSV is empty"]
                )

            # Get expected headers per master type
            expected_headers = self._get_expected_headers(master_type)
            actual_headers = reader.fieldnames or []

            # Validate headers
            missing_headers = set(expected_headers) - set(actual_headers)
            if missing_headers:
                return CsvValidationResponse(
                    valid=False,
                    error_count=1,
                    errors=[f"Missing headers: {', '.join(missing_headers)}"]
                )

            # Validate rows
            errors = []
            valid_rows = []

            for idx, row in enumerate(rows, start=2):  # Start at 2 (header is 1)
                row_errors = self._validate_row(row, master_type, idx)
                if row_errors:
                    errors.extend(row_errors)
                else:
                    valid_rows.append((idx, row))

            valid = len(errors) == 0

            logger.info(
                "csv_validation_completed",
                master_type=master_type,
                total_rows=len(rows),
                valid_rows=len(valid_rows),
                error_count=len(errors),
                valid=valid,
                trace_id=trace_id
            )

            return CsvValidationResponse(
                valid=valid,
                total_rows=len(rows),
                valid_rows=len(valid_rows),
                error_count=len(errors),
                errors=errors[:100]  # Limit errors to first 100
            )

        except UnicodeDecodeError:
            logger.error("csv_decode_error", trace_id=trace_id)
            return CsvValidationResponse(
                valid=False,
                error_count=1,
                errors=["Invalid file encoding (must be UTF-8)"]
            )
        except Exception as e:
            logger.error("csv_validation_error", error=str(e), trace_id=trace_id)
            return CsvValidationResponse(
                valid=False,
                error_count=1,
                errors=[f"Validation failed: {str(e)}"]
            )

    def preview_csv(
        self,
        file_content: bytes,
        master_type: str,
        import_mode: ImportMode
    ) -> CsvImportPreview:
        """
        Generate preview of CSV import showing what will be created/updated.
        Detects duplicates and conflicts.
        """
        trace_id = str(uuid.uuid4())
        logger.info(
            "csv_preview_started",
            master_type=master_type,
            import_mode=import_mode,
            trace_id=trace_id
        )

        try:
            text_content = file_content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(text_content))
            rows = list(reader)

            preview_items = []
            duplicates = []
            conflicts = []
            to_create = 0
            to_update = 0

            seen_names = set()

            for row in rows:
                name = row.get("name", "").strip()

                # Check for duplicates within file
                if name in seen_names:
                    duplicates.append({
                        "name": name,
                        "reason": "Duplicate in CSV file"
                    })
                    continue

                seen_names.add(name)

                # Check for existing in database
                exists = self._entity_exists(name, master_type)

                action = self._determine_action(
                    exists=exists,
                    import_mode=import_mode
                )

                if action == "SKIP":
                    continue
                elif action == "CREATE":
                    to_create += 1
                elif action == "UPDATE":
                    to_update += 1

                preview_items.append({
                    "name": name,
                    "action": action,
                    "data": {k: v for k, v in row.items() if k != "name"}
                })

            logger.info(
                "csv_preview_completed",
                master_type=master_type,
                total_rows=len(rows),
                to_create=to_create,
                to_update=to_update,
                duplicates=len(duplicates),
                trace_id=trace_id
            )

            return CsvImportPreview(
                master_type=master_type,
                import_mode=import_mode,
                total_rows=len(rows),
                preview_items=preview_items,
                to_create=to_create,
                to_update=to_update,
                duplicates=duplicates,
                conflicts=conflicts,
                can_proceed=len(duplicates) == 0
            )

        except Exception as e:
            logger.error("csv_preview_error", error=str(e), trace_id=trace_id)
            raise

    def execute_import(
        self,
        job_id: str,
        file_content: bytes,
        master_type: str,
        import_mode: ImportMode,
        user_id: str
    ) -> Tuple[CsvImportResult, ImportJob]:
        """
        Execute CSV import with full transactional semantics.
        Returns result and updated job record.
        """
        trace_id = str(uuid.uuid4())
        logger.info(
            "csv_import_started",
            job_id=job_id,
            master_type=master_type,
            import_mode=import_mode,
            user_id=user_id,
            trace_id=trace_id
        )

        job = self.db.query(ImportJob).filter(ImportJob.id == job_id).first()
        if not job:
            raise NotFoundError(f"Import job '{job_id}' not found")

        job.status = "PROCESSING"
        job.started_at = datetime.utcnow()
        self.db.commit()

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_details = []

        try:
            text_content = file_content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(text_content))
            rows = list(reader)

            for idx, row in enumerate(rows, start=2):
                try:
                    name = row.get("name", "").strip()
                    if not name:
                        error_details.append({
                            "row": idx,
                            "name": "Unknown",
                            "error": "Name is required"
                        })
                        continue

                    exists = self._entity_exists(name, master_type)
                    action = self._determine_action(exists, import_mode)

                    if action == "SKIP":
                        skipped_count += 1
                        continue

                    if action == "CREATE":
                        self._create_entity(row, master_type, user_id, trace_id)
                        created_count += 1
                    elif action == "UPDATE":
                        self._update_entity(row, master_type, user_id, trace_id)
                        updated_count += 1

                except ValidationError as e:
                    error_details.append({
                        "row": idx,
                        "name": row.get("name", "Unknown"),
                        "error": str(e)
                    })
                except DuplicateError as e:
                    error_details.append({
                        "row": idx,
                        "name": row.get("name", "Unknown"),
                        "error": str(e)
                    })
                except Exception as e:
                    error_details.append({
                        "row": idx,
                        "name": row.get("name", "Unknown"),
                        "error": f"Unexpected error: {str(e)}"
                    })

            # Update job record
            job.status = "COMPLETED"
            job.processed_rows = created_count + updated_count + skipped_count
            job.error_count = len(error_details)
            job.error_details = json.dumps(error_details)
            job.completed_at = datetime.utcnow()
            self.db.commit()

            logger.info(
                "csv_import_completed",
                job_id=job_id,
                created=created_count,
                updated=updated_count,
                skipped=skipped_count,
                errors=len(error_details),
                trace_id=trace_id
            )

            result = CsvImportResult(
                job_id=job_id,
                status="COMPLETED",
                created_count=created_count,
                updated_count=updated_count,
                skipped_count=skipped_count,
                error_count=len(error_details),
                error_details=error_details,
                completed_at=datetime.utcnow()
            )

            return result, job

        except Exception as e:
            logger.error(
                "csv_import_failed",
                job_id=job_id,
                error=str(e),
                trace_id=trace_id
            )

            job.status = "FAILED"
            job.error_count = 1
            job.error_details = json.dumps([{"error": str(e)}])
            job.completed_at = datetime.utcnow()
            self.db.commit()

            raise

    # ==================== PRIVATE HELPERS ====================

    def _get_expected_headers(self, master_type: str) -> List[str]:
        """Get required CSV headers per master type"""
        headers_map = {
            "DEFECT": ["name", "description", "typical_process", "typical_machine_id"],
            "MACHINE": ["name", "process", "manufacturer", "model"],
            "FABRIC": ["name", "composition", "width_cm", "weight_gsm"]
        }
        return headers_map.get(master_type, [])

    def _validate_row(
        self,
        row: Dict[str, str],
        master_type: str,
        row_num: int
    ) -> List[str]:
        """Validate a single CSV row"""
        errors = []

        name = row.get("name", "").strip()
        if not name:
            errors.append(f"Row {row_num}: Name is required")
            return errors

        if master_type == "DEFECT":
            process = row.get("typical_process", "").strip()
            if process and process not in ["LAVADO", "TEÑIDO", "SECADO", "PLANCHADO"]:
                errors.append(f"Row {row_num}: Invalid process '{process}'")

        elif master_type == "MACHINE":
            process = row.get("process", "").strip()
            if process and process not in ["LAVADO", "TEÑIDO", "SECADO", "PLANCHADO"]:
                errors.append(f"Row {row_num}: Invalid process '{process}'")

        elif master_type == "FABRIC":
            try:
                width = float(row.get("width_cm", 0))
                if width < 10 or width > 500:
                    errors.append(f"Row {row_num}: Width must be 10-500 cm")
            except ValueError:
                errors.append(f"Row {row_num}: Width must be a valid number")

            try:
                weight = float(row.get("weight_gsm", 0))
                if weight < 10 or weight > 2000:
                    errors.append(f"Row {row_num}: Weight must be 10-2000 gsm")
            except ValueError:
                errors.append(f"Row {row_num}: Weight must be a valid number")

        return errors

    def _entity_exists(self, name: str, master_type: str) -> bool:
        """Check if entity with given name exists"""
        if master_type == "DEFECT":
            return self.db.query(Defect).filter(
                Defect.name.ilike(name)
            ).first() is not None
        elif master_type == "MACHINE":
            return self.db.query(Machine).filter(
                Machine.name.ilike(name)
            ).first() is not None
        elif master_type == "FABRIC":
            return self.db.query(Fabric).filter(
                Fabric.name.ilike(name)
            ).first() is not None
        return False

    def _determine_action(self, exists: bool, import_mode: ImportMode) -> str:
        """Determine action (CREATE, UPDATE, SKIP) based on mode"""
        if import_mode == ImportMode.INSERT:
            return "SKIP" if exists else "CREATE"
        elif import_mode == ImportMode.UPDATE:
            return "UPDATE" if exists else "SKIP"
        elif import_mode == ImportMode.UPSERT:
            return "UPDATE" if exists else "CREATE"
        elif import_mode == ImportMode.SKIP_DUPLICATES:
            return "SKIP" if exists else "CREATE"
        return "SKIP"

    def _create_entity(
        self,
        row: Dict[str, str],
        master_type: str,
        user_id: str,
        trace_id: str
    ):
        """Create entity from CSV row"""
        name = row.get("name", "").strip()

        if master_type == "DEFECT":
            payload = DefectCreate(
                name=name,
                description=row.get("description", "").strip(),
                typical_process=row.get("typical_process", "").strip(),
                typical_machine_id=row.get("typical_machine_id") or None
            )
            self.service.create_defect(payload, user_id=user_id, trace_id=trace_id)

        elif master_type == "MACHINE":
            payload = MachineCreate(
                name=name,
                process=row.get("process", "").strip(),
                manufacturer=row.get("manufacturer", "").strip(),
                model=row.get("model", "").strip()
            )
            self.service.create_machine(payload, user_id=user_id, trace_id=trace_id)

        elif master_type == "FABRIC":
            payload = FabricCreate(
                name=name,
                composition=row.get("composition", "").strip(),
                width_cm=float(row.get("width_cm", 0)),
                weight_gsm=float(row.get("weight_gsm", 0))
            )
            self.service.create_fabric(payload, user_id=user_id, trace_id=trace_id)

    def _update_entity(
        self,
        row: Dict[str, str],
        master_type: str,
        user_id: str,
        trace_id: str
    ):
        """Update entity from CSV row (by name)"""
        name = row.get("name", "").strip()

        if master_type == "DEFECT":
            entity = self.db.query(Defect).filter(
                Defect.name.ilike(name)
            ).first()
            if not entity:
                raise NotFoundError(f"Defect '{name}' not found")

            from app.schemas import DefectUpdate
            payload = DefectUpdate(
                name=name,
                description=row.get("description") or None,
                typical_process=row.get("typical_process") or None,
                typical_machine_id=row.get("typical_machine_id") or None,
                version=entity.version
            )
            self.service.update_defect(
                entity.id,
                payload,
                user_id=user_id,
                trace_id=trace_id
            )

        elif master_type == "MACHINE":
            entity = self.db.query(Machine).filter(
                Machine.name.ilike(name)
            ).first()
            if not entity:
                raise NotFoundError(f"Machine '{name}' not found")

            from app.schemas import MachineUpdate
            payload = MachineUpdate(
                name=name,
                process=row.get("process") or None,
                manufacturer=row.get("manufacturer") or None,
                model=row.get("model") or None,
                version=entity.version
            )
            self.service.update_machine(
                entity.id,
                payload,
                user_id=user_id,
                trace_id=trace_id
            )

        elif master_type == "FABRIC":
            entity = self.db.query(Fabric).filter(
                Fabric.name.ilike(name)
            ).first()
            if not entity:
                raise NotFoundError(f"Fabric '{name}' not found")

            from app.schemas import FabricUpdate
            payload = FabricUpdate(
                name=name,
                composition=row.get("composition") or None,
                width_cm=float(row.get("width_cm", entity.width_cm)) if row.get("width_cm") else None,
                weight_gsm=float(row.get("weight_gsm", entity.weight_gsm)) if row.get("weight_gsm") else None,
                version=entity.version
            )
            self.service.update_fabric(
                entity.id,
                payload,
                user_id=user_id,
                trace_id=trace_id
            )
