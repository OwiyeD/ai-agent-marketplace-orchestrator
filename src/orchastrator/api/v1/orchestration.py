from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from orchastrator.models import database as models
from orchastrator.models import schemas
from orchastrator.config.database import get_db

router = APIRouter(prefix="/orchestrations", tags=["orchestrations"])


@router.post("/", response_model=schemas.OrchestrationRead)
def create_orchestration(orchestration: schemas.OrchestrationCreate, db: Session = Depends(get_db)):
    db_orch = models.Orchestration(**orchestration.dict())
    db.add(db_orch)
    db.commit()
    db.refresh(db_orch)
    return db_orch


@router.get("/", response_model=List[schemas.OrchestrationRead])
def list_orchestrations(db: Session = Depends(get_db)):
    return db.query(models.Orchestration).all()


@router.get("/{orch_id}", response_model=schemas.OrchestrationRead)
def get_orchestration(orch_id: str, db: Session = Depends(get_db)):
    orch = db.query(models.Orchestration).filter(models.Orchestration.id == orch_id).first()
    if not orch:
        raise HTTPException(status_code=404, detail="Orchestration not found")
    return orch


@router.put("/{orch_id}", response_model=schemas.OrchestrationRead)
def update_orchestration(orch_id: str, update: schemas.OrchestrationUpdate, db: Session = Depends(get_db)):
    db_orch = db.query(models.Orchestration).filter(models.Orchestration.id == orch_id).first()
    if not db_orch:
        raise HTTPException(status_code=404, detail="Orchestration not found")

    for field, value in update.dict(exclude_unset=True).items():
        setattr(db_orch, field, value)

    db.commit()
    db.refresh(db_orch)
    return db_orch


@router.delete("/{orch_id}")
def delete_orchestration(orch_id: str, db: Session = Depends(get_db)):
    db_orch = db.query(models.Orchestration).filter(models.Orchestration.id == orch_id).first()
    if not db_orch:
        raise HTTPException(status_code=404, detail="Orchestration not found")
    db.delete(db_orch)
    db.commit()
    return {"detail": "Orchestration deleted successfully"}
