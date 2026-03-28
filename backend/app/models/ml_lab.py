"""
ML Lab Models

SQLAlchemy ORM models for model registry and dataset registry.
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, DateTime, Text, BigInteger,
    Index, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.session import Base
import uuid


class ModelRegistry(Base):
    """Machine learning models registry"""
    __tablename__ = "model_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    version = Column(String(50), nullable=False)
    type = Column(String(50), nullable=False)  # onnx, pytorch, sklearn
    huggingface_repo = Column(String(200), nullable=True)
    wandb_run_id = Column(String(200), nullable=True)
    metrics = Column(JSONB, server_default='{}')
    status = Column(String(50), server_default='staging')  # staging, production, archived
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_model_registry_name_version', 'name', 'version'),
        Index('idx_model_registry_status', 'status'),
        Index('idx_model_registry_type', 'type'),
    )

    def __repr__(self):
        return f"<Model {self.name} v{self.version} ({self.type})>"


class DatasetRegistry(Base):
    """Datasets registry for ML training and evaluation"""
    __tablename__ = "dataset_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    gcs_path = Column(String(500), nullable=True)
    size_mb = Column(Float, nullable=True)
    row_count = Column(BigInteger, nullable=True)
    schema = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_dataset_registry_name', 'name'),
        Index('idx_dataset_registry_created', 'created_at'),
    )

    def __repr__(self):
        return f"<Dataset {self.name} rows={self.row_count}>"