from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from orchastrator.models import database as models
from orchastrator.models import schemas
from orchastrator.config.database import get_db

router = APIRouter(prefix="/subtasks", tags=["subtasks"])


@router.post("/", response_model=schemas.SubtaskRead)
def create_subtask(subtask: schemas.SubtaskCreate, db: Session = Depends(get_db)):
    db_subtask = models.Subtask(**subtask.dict())
    db.add(db_subtask)
    db.commit()
    db.refresh(db_subtask)
    return db_subtask


@router.get("/", response_model=List[schemas.SubtaskRead])
def list_subtasks(db: Session = Depends(get_db)):
    return db.query(models.Subtask).all()


@router.get("/{subtask_id}", response_model=schemas.SubtaskRead)
def get_subtask(subtask_id: str, db: Session = Depends(get_db)):
    subtask = db.query(models.Subtask).filter(models.Subtask.id == subtask_id).first()
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return subtask


@router.put("/{subtask_id}", response_model=schemas.SubtaskRead)
def update_subtask(subtask_id: str, update: schemas.SubtaskUpdate, db: Session = Depends(get_db)):
    db_subtask = db.query(models.Subtask).filter(models.Subtask.id == subtask_id).first()
    if not db_subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")

    for field, value in update.dict(exclude_unset=True).items():
        setattr(db_subtask, field, value)

    db.commit()
    db.refresh(db_subtask)
    return db_subtask


@router.delete("/{subtask_id}")
def delete_subtask(subtask_id: str, db: Session = Depends(get_db)):
    db_subtask = db.query(models.Subtask).filter(models.Subtask.id == subtask_id).first()
    if not db_subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    db.delete(db_subtask)
    db.commit()
    return {"detail": "Subtask deleted successfully"}
