"""Unit tests for domain services"""
import pytest
from datetime import datetime

from app.domain.services.inspection_service import InspectionService
from app.domain.services.approval_service import ApprovalService
from app.domain.services.masters_service import MastersService
from app.domain.entities import Comment, Photograph
from app.repositories.inspection_repository import InspectionRepository
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.masters_repository import DefectRepository, MachineRepository, FabricRepository


@pytest.mark.asyncio
async def test_inspection_service_register(db_session, test_inspection_data):
    """Test registering a new inspection"""
    repo = InspectionRepository(db_session)
    service = InspectionService(repo)

    inspection = await service.register_inspection(
        lote_id=test_inspection_data["lote_id"],
        analista_id=test_inspection_data["analista_id"],
        defect_id=test_inspection_data["defect_id"],
        comment_text=test_inspection_data["comment_text"],
        photo_path=test_inspection_data["photo_path"],
        photo_checksum=test_inspection_data["photo_checksum"],
        photo_size_kb=test_inspection_data["photo_size_kb"],
        machine_id=test_inspection_data["machine_id"],
        check_in=datetime.now()
    )

    assert inspection.inspection_id is not None
    assert inspection.lote_id == test_inspection_data["lote_id"]
    assert inspection.comment.text == test_inspection_data["comment_text"]


@pytest.mark.asyncio
async def test_inspection_service_invalid_comment(db_session, test_inspection_data):
    """Test that short comments are rejected"""
    repo = InspectionRepository(db_session)
    service = InspectionService(repo)

    with pytest.raises(ValueError):
        await service.register_inspection(
            lote_id=test_inspection_data["lote_id"],
            analista_id=test_inspection_data["analista_id"],
            defect_id=test_inspection_data["defect_id"],
            comment_text="short",  # Less than 10 chars
            photo_path=test_inspection_data["photo_path"],
            photo_checksum=test_inspection_data["photo_checksum"],
            photo_size_kb=test_inspection_data["photo_size_kb"],
            machine_id=test_inspection_data["machine_id"],
            check_in=datetime.now()
        )


@pytest.mark.asyncio
async def test_photo_value_object_validation():
    """Test photo validation"""
    # Valid photo
    photo = Photograph(
        file_path="/path/to/photo.jpg",
        checksum="a" * 64,
        size_kb=250
    )
    assert photo.size_kb == 250

    # Invalid size
    with pytest.raises(ValueError):
        Photograph(
            file_path="/path/to/photo.jpg",
            checksum="a" * 64,
            size_kb=600  # Exceeds 500KB limit
        )


@pytest.mark.asyncio
async def test_comment_value_object_validation():
    """Test comment validation"""
    # Valid comment
    comment = Comment(text="This is a valid comment with more than 10 chars")
    assert len(comment.text) > 10

    # Invalid comment
    with pytest.raises(ValueError):
        Comment(text="short")  # Less than 10 chars


@pytest.mark.asyncio
async def test_approval_service_approve(db_session, test_inspection_data):
    """Test approving an inspection"""
    inspection_repo = InspectionRepository(db_session)
    approval_repo = ApprovalRepository(db_session)
    approval_service = ApprovalService(approval_repo, inspection_repo)

    # Create inspection first
    inspection_service = InspectionService(inspection_repo)
    inspection = await inspection_service.register_inspection(
        lote_id=test_inspection_data["lote_id"],
        analista_id=test_inspection_data["analista_id"],
        defect_id=test_inspection_data["defect_id"],
        comment_text=test_inspection_data["comment_text"],
        photo_path=test_inspection_data["photo_path"],
        photo_checksum=test_inspection_data["photo_checksum"],
        photo_size_kb=test_inspection_data["photo_size_kb"],
        machine_id=test_inspection_data["machine_id"],
        check_in=datetime.now()
    )

    # Approve it
    approval = await approval_service.approve_inspection(
        inspection_id=inspection.inspection_id,
        jefe_qa_id="jefe_qa_001",
        notes="Looks good"
    )

    assert approval.decision == "APPROVED"
    assert approval.jefe_qa_id == "jefe_qa_001"


@pytest.mark.asyncio
async def test_approval_service_reject(db_session, test_inspection_data):
    """Test rejecting an inspection"""
    inspection_repo = InspectionRepository(db_session)
    approval_repo = ApprovalRepository(db_session)
    approval_service = ApprovalService(approval_repo, inspection_repo)

    # Create inspection
    inspection_service = InspectionService(inspection_repo)
    inspection = await inspection_service.register_inspection(
        lote_id=test_inspection_data["lote_id"],
        analista_id=test_inspection_data["analista_id"],
        defect_id=test_inspection_data["defect_id"],
        comment_text=test_inspection_data["comment_text"],
        photo_path=test_inspection_data["photo_path"],
        photo_checksum=test_inspection_data["photo_checksum"],
        photo_size_kb=test_inspection_data["photo_size_kb"],
        machine_id=test_inspection_data["machine_id"],
        check_in=datetime.now()
    )

    # Reject with reason
    approval = await approval_service.reject_inspection(
        inspection_id=inspection.inspection_id,
        jefe_qa_id="jefe_qa_001",
        rejection_reason="Quality does not meet standards",
        notes="Please review again"
    )

    assert approval.decision == "REJECTED"
    assert approval.rejection_reason == "Quality does not meet standards"


@pytest.mark.asyncio
async def test_masters_service_bulk_import_defects(db_session):
    """Test bulk importing defects"""
    defect_repo = DefectRepository(db_session)
    machine_repo = MachineRepository(db_session)
    fabric_repo = FabricRepository(db_session)
    service = MastersService(defect_repo, machine_repo, fabric_repo)

    defects_data = [
        {"defect_id": "DEF_001", "name": "Tear", "category": "Physical", "severity": "HIGH"},
        {"defect_id": "DEF_002", "name": "Stain", "category": "Visible", "severity": "MEDIUM"},
        {"defect_id": "DEF_001", "name": "Tear", "category": "Physical", "severity": "HIGH"},  # Duplicate
    ]

    result = await service.bulk_import_defects(defects_data)

    assert result["created"] == 2
    assert result["skipped"] == 1
