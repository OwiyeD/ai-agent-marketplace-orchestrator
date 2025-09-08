from sqlalchemy import create_engine, Column, String, Text, JSON, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY  # 👈 Use PG-specific ARRAY
import uuid
from config import settings

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

# Models
class Orchestration(Base):
    __tablename__ = "orchestrations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_input = Column(Text, nullable=False)
    current_status = Column(String, nullable=False, default="PARSING")
    results = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    workflow_type = Column(String, nullable=True)  # e.g., "ecommerce_onboarding"
    subtasks = Column(JSON, nullable=True)        # Keep as JSON for flexibility

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    endpoint_url = Column(String, nullable=False)
    capabilities = Column(ARRAY(String), nullable=False)  # ✅ PG ARRAY now
    reputation_score = Column(Integer, default=100)
    is_active = Column(String, default="active")

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)
