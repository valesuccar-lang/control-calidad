"""Unit tests for domain entities — 100% business rule coverage"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.domain.entities import (
    Comment, Photograph, InspectionTime, Inspection,
    Approval, Lote, SyncStatus
)

VALID_CHECKSUM = "a" * 64
NOW = datetime(2026, 6, 2, 10, 0, 0)
LATER = datetime(2026, 6, 2, 10, 5, 0)


# ── Comment ──────────────────────────────────────────────────────────────────

class TestComment:
    def test_valid_comment(self):
        c = Comment("Este es un comentario válido")
        assert c.text == "Este es un comentario válido"

    def test_too_short(self):
        with pytest.raises(ValueError, match="10 and 500"):
            Comment("short")

    def test_exact_10(self):
        Comment("1234567890")

    def test_too_long(self):
        with pytest.raises(ValueError):
            Comment("x" * 501)

    def test_exact_500(self):
        Comment("x" * 500)

    def test_immutable(self):
        c = Comment("valid comment here")
        with pytest.raises(Exception):
            c.text = "other"


# ── Photograph ───────────────────────────────────────────────────────────────

class TestPhotograph:
    def test_valid(self):
        p = Photograph("/path/img.jpg", VALID_CHECKSUM, 100)
        assert p.size_kb == 100

    def test_exact_500kb(self):
        Photograph("/path/img.jpg", VALID_CHECKSUM, 500)

    def test_over_500kb(self):
        with pytest.raises(ValueError, match="500 KB"):
            Photograph("/path/img.jpg", VALID_CHECKSUM, 501)

    def test_wrong_checksum_length(self):
        with pytest.raises(ValueError, match="SHA256"):
            Photograph("/path/img.jpg", "abc123", 100)

    def test_immutable(self):
        p = Photograph("/path/img.jpg", VALID_CHECKSUM, 100)
        with pytest.raises(Exception):
            p.size_kb = 200


# ── InspectionTime ────────────────────────────────────────────────────────────

class TestInspectionTime:
    def test_elapsed_with_checkout(self):
        t = InspectionTime(check_in=NOW, check_out=LATER)
        assert t.elapsed_seconds == 300

    def test_elapsed_without_checkout(self):
        t = InspectionTime(check_in=NOW)
        assert t.elapsed_seconds == 0


# ── Inspection ───────────────────────────────────────────────────────────────

def make_inspection(**kwargs):
    defaults = dict(
        inspection_id=uuid4(),
        lote_id="L-001",
        analista_id="U-001",
        defect_id="D-001",
        comment=Comment("Defecto encontrado en tejido"),
        photograph=Photograph("/photos/img.jpg", VALID_CHECKSUM, 100),
        machine_id="M-001",
        inspection_time=InspectionTime(check_in=NOW, check_out=LATER),
    )
    defaults.update(kwargs)
    return Inspection(**defaults)


class TestInspection:
    def test_default_sync_status(self):
        i = make_inspection()
        assert i.sync_status == SyncStatus.PENDING

    def test_mark_synced(self):
        i = make_inspection()
        i.mark_synced()
        assert i.sync_status == SyncStatus.SYNCED

    def test_mark_sync_failed(self):
        i = make_inspection()
        i.mark_sync_failed()
        assert i.sync_status == SyncStatus.SYNC_FAILED

    def test_to_dict_keys(self):
        i = make_inspection()
        d = i.to_dict()
        assert "inspection_id" in d
        assert "elapsed_seconds" in d
        assert d["elapsed_seconds"] == 300


# ── Approval ─────────────────────────────────────────────────────────────────

class TestApproval:
    def test_valid_approved(self):
        a = Approval(uuid4(), uuid4(), "U-002", "APPROVED", approved_at=NOW)
        a.validate()

    def test_valid_rejected_with_reason(self):
        a = Approval(uuid4(), uuid4(), "U-002", "REJECTED",
                     rejection_reason="Defecto grave en tejido", approved_at=NOW)
        a.validate()

    def test_rejected_without_reason_raises(self):
        a = Approval(uuid4(), uuid4(), "U-002", "REJECTED")
        with pytest.raises(ValueError, match="Rejection reason"):
            a.validate()

    def test_invalid_decision_raises(self):
        a = Approval(uuid4(), uuid4(), "U-002", "PENDING")
        with pytest.raises(ValueError, match="Decision must be"):
            a.validate()

    def test_to_dict(self):
        a = Approval(uuid4(), uuid4(), "U-002", "APPROVED", approved_at=NOW)
        d = a.to_dict()
        assert d["decision"] == "APPROVED"


# ── Lote ──────────────────────────────────────────────────────────────────────

class TestLote:
    def test_valid_lote(self):
        l = Lote("L-001", "F-001", 100)
        l.validate()

    def test_zero_quantity_raises(self):
        l = Lote("L-001", "F-001", 0)
        with pytest.raises(ValueError, match="positive"):
            l.validate()

    def test_negative_quantity_raises(self):
        l = Lote("L-001", "F-001", -5)
        with pytest.raises(ValueError):
            l.validate()

    def test_invalid_status_raises(self):
        l = Lote("L-001", "F-001", 10, status="UNKNOWN")
        with pytest.raises(ValueError, match="Invalid status"):
            l.validate()

    def test_all_valid_statuses(self):
        for s in ("PENDING", "IN_PROCESS", "INSPECTED", "APPROVED", "REJECTED"):
            Lote("L-001", "F-001", 10, status=s).validate()
