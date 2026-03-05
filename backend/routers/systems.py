from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import AISystem
from schemas import AISystemCreate, AISystemOut

router = APIRouter(prefix="/api/systems", tags=["AI Systems"])


@router.post("/", response_model=AISystemOut)
def create_system(payload: AISystemCreate, db: Session = Depends(get_db)):
    system = AISystem(
        name=payload.name,
        model_type=payload.model_type,
        api_endpoint=payload.api_endpoint,
        config_json=payload.config_json,
    )
    db.add(system)
    db.commit()
    db.refresh(system)
    return system


@router.get("/", response_model=List[AISystemOut])
def list_systems(db: Session = Depends(get_db)):
    return db.query(AISystem).order_by(AISystem.created_at.desc()).all()


@router.get("/{system_id}", response_model=AISystemOut)
def get_system(system_id: int, db: Session = Depends(get_db)):
    system = db.query(AISystem).filter(AISystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    return system


@router.delete("/{system_id}")
def delete_system(system_id: int, db: Session = Depends(get_db)):
    system = db.query(AISystem).filter(AISystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    db.delete(system)
    db.commit()
    return {"detail": "System deleted"}
