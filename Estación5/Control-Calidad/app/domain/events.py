"""Domain events for event sourcing"""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class DomainEvent:
    """Base domain event"""
    event_id: str = field(default_factory=lambda: str(UUID))
    aggregate_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: str = ""

    def __post_init__(self):
        if not self.event_type:
            self.event_type = self.__class__.__name__


@dataclass
class InspectionCreated(DomainEvent):
    """Raised when inspection is created"""
    lote_id: str = ""
    analista_id: str = ""
    defect_id: str = ""


@dataclass
class InspectionSynced(DomainEvent):
    """Raised when inspection is synced to server"""
    sync_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class InspectionSyncFailed(DomainEvent):
    """Raised when inspection sync fails"""
    error_message: str = ""
    retry_count: int = 0


@dataclass
class ApprovalApproved(DomainEvent):
    """Raised when inspection is approved"""
    jefe_qa_id: str = ""
    approved_at: datetime = field(default_factory=datetime.now)


@dataclass
class ApprovalRejected(DomainEvent):
    """Raised when inspection is rejected"""
    jefe_qa_id: str = ""
    rejection_reason: str = ""
    rejected_at: datetime = field(default_factory=datetime.now)


@dataclass
class MastersImported(DomainEvent):
    """Raised when masters data is bulk imported"""
    entity_type: str = ""  # defects, machines, fabrics
    count: int = 0


@dataclass
class UserCreated(DomainEvent):
    """Raised when user is created"""
    email: str = ""
    roles: list = field(default_factory=list)


@dataclass
class UserDeactivated(DomainEvent):
    """Raised when user is deactivated"""
    reason: str = ""
