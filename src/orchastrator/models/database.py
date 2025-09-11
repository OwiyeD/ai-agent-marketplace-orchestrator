from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    JSON,
    DateTime,
    Integer,
    Boolean,
    ForeignKey,
    Enum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
import uuid

from config.settings import settings


# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# Models
# -----------------------------
class Orchestration(Base):
    __tablename__ = "orchestrations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_input = Column(Text, nullable=False)
    current_status = Column(String, nullable=False, default="PARSING")
    results = Column(JSON, nullable=True)
    workflow_type = Column(String, nullable=True)  # e.g., "ecommerce_onboarding"

    # Keep JSON subtasks for quick serialization, but we add Subtask table for granularity
    subtasks = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    subtasks_list = relationship(
        "Subtask",
        back_populates="orchestration",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    endpoint_url = Column(String, nullable=False)
    capabilities = Column(ARRAY(String), nullable=False)
    reputation_score = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)

    # Relationships
    subtasks = relationship("Subtask", back_populates="agent")


class Subtask(Base):
    __tablename__ = "subtasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    orchestration_id = Column(
        String, ForeignKey("orchestrations.id", ondelete="CASCADE"), nullable=False
    )
    agent_id = Column(
        String, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )

    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    status = Column(String, default="PENDING")  # could normalize into Enum if strict
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    orchestration = relationship("Orchestration", back_populates="subtasks_list")
    agent = relationship("Agent", back_populates="subtasks")


# -----------------------------
# Create tables
# -----------------------------
def create_tables():
    Base.metadata.create_all(bind=engine)
