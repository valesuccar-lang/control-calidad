"""SQLAlchemy Base model with common columns"""
from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class BaseModel(Base):
    """Base model with common audit columns"""
    __abstract__ = True

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
        }
