from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


# -----------------------------
# Agent Schemas
# -----------------------------
class AgentBase(BaseModel):
    name: str
    description: str
    endpoint_url: str
    capabilities: List[str] = Field(default_factory=list)
    reputation_score: int = 100
    is_active: bool = True


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    endpoint_url: Optional[str] = None
    capabilities: Optional[List[str]] = None
    reputation_score: Optional[int] = None
    is_active: Optional[bool] = None


class AgentRead(AgentBase):
    id: str
    created_at: Optional[datetime] = None  # useful if you extend Agent table later

    class Config:
        orm_mode = True


# -----------------------------
# Subtask Schemas
# -----------------------------
class SubtaskBase(BaseModel):
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    status: str = "PENDING"
    error_message: Optional[str] = None


class SubtaskCreate(SubtaskBase):
    orchestration_id: str
    agent_id: Optional[str] = None


class SubtaskUpdate(BaseModel):
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    agent_id: Optional[str] = None


class SubtaskRead(SubtaskBase):
    id: str
    orchestration_id: str
    agent_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Nested agent info
    agent: Optional[AgentRead] = None

    class Config:
        orm_mode = True


# -----------------------------
# Orchestration Schemas
# -----------------------------
class OrchestrationBase(BaseModel):
    user_input: str
    current_status: str = "PARSING"
    workflow_type: Optional[str] = None
    results: Optional[Any] = None
    subtasks: Optional[Any] = None  # legacy JSON subtasks field


class OrchestrationCreate(OrchestrationBase):
    pass


class OrchestrationUpdate(BaseModel):
    user_input: Optional[str] = None
    current_status: Optional[str] = None
    workflow_type: Optional[str] = None
    results: Optional[Any] = None
    subtasks: Optional[Any] = None


class OrchestrationRead(OrchestrationBase):
    id: str
    created_at: datetime
    updated_at: datetime

    # Nested subtasks
    subtasks_list: List[SubtaskRead] = []

    class Config:
        orm_mode = True
