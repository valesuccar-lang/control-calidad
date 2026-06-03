"""Structured audit logging with JSON output"""
import json
from datetime import datetime
from typing import Optional, Any
from loguru import logger
from app.settings import app_settings


class AuditLogger:
    """Structured audit event logger"""

    @staticmethod
    def log_inspection_created(
        user_id: str,
        inspection_id: str,
        lote_id: str,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Log inspection creation event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "inspection.created",
            "user_id": user_id,
            "entity_type": "inspection",
            "entity_id": inspection_id,
            "details": {"lote_id": lote_id},
            "ip_address": ip_address,
            "status": "SUCCESS"
        }
        logger.info("Audit", **event)

    @staticmethod
    def log_inspection_approved(
        user_id: str,
        approval_id: str,
        inspection_id: str,
        decision: str,
        ip_address: str = None
    ):
        """Log inspection approval event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "inspection.approved",
            "user_id": user_id,
            "entity_type": "approval",
            "entity_id": approval_id,
            "details": {"inspection_id": inspection_id, "decision": decision},
            "ip_address": ip_address,
            "status": "SUCCESS"
        }
        logger.info("Audit", **event)

    @staticmethod
    def log_inspection_synced(
        inspection_id: str,
        sync_attempts: int,
        ip_address: str = None
    ):
        """Log inspection sync event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "inspection.synced",
            "entity_type": "inspection",
            "entity_id": inspection_id,
            "details": {"sync_attempts": sync_attempts},
            "ip_address": ip_address,
            "status": "SUCCESS"
        }
        logger.info("Audit", **event)

    @staticmethod
    def log_sync_failed(
        inspection_id: str,
        error_message: str,
        retry_count: int,
        ip_address: str = None
    ):
        """Log sync failure event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "inspection.sync_failed",
            "entity_type": "inspection",
            "entity_id": inspection_id,
            "details": {"error": error_message, "retry_count": retry_count},
            "ip_address": ip_address,
            "status": "FAILED",
            "error_message": error_message
        }
        logger.warning("Audit", **event)

    @staticmethod
    def log_masters_imported(
        user_id: str,
        entity_type: str,
        created_count: int,
        skipped_count: int,
        ip_address: str = None
    ):
        """Log masters data import event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": f"{entity_type}.imported",
            "user_id": user_id,
            "entity_type": entity_type,
            "details": {"created": created_count, "skipped": skipped_count},
            "ip_address": ip_address,
            "status": "SUCCESS"
        }
        logger.info("Audit", **event)

    @staticmethod
    def log_user_login(
        user_id: str,
        email: str,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Log user login event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "user.login",
            "user_id": user_id,
            "entity_type": "user",
            "entity_id": user_id,
            "details": {"email": email},
            "ip_address": ip_address,
            "user_agent": user_agent,
            "status": "SUCCESS"
        }
        logger.info("Audit", **event)

    @staticmethod
    def log_auth_failure(
        email: str,
        reason: str,
        ip_address: str = None
    ):
        """Log authentication failure"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "user.login_failed",
            "entity_type": "user",
            "details": {"email": email},
            "ip_address": ip_address,
            "status": "FAILED",
            "error_message": reason
        }
        logger.warning("Audit", **event)

    @staticmethod
    def log_api_request(
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: str = None,
        ip_address: str = None
    ):
        """Log API request"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "api.request",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "user_id": user_id,
            "ip_address": ip_address
        }
        if status_code >= 400:
            logger.warning("Audit", **event)
        else:
            logger.info("Audit", **event)

    @staticmethod
    def log_error(
        error_type: str,
        error_message: str,
        context: dict = None,
        user_id: str = None
    ):
        """Log error event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "error",
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
            "user_id": user_id,
            "status": "FAILED"
        }
        logger.error("Audit", **event)


audit_logger = AuditLogger()
