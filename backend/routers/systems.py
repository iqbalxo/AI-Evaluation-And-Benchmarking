from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import AISystem
from schemas import AISystemCreate, AISystemOut, ModelPresetOut
from services.model_catalog import get_model_preset, list_model_presets

router = APIRouter(prefix="/api/systems", tags=["AI Systems"])


@router.post("/", response_model=AISystemOut)
def create_system(payload: AISystemCreate, db: Session = Depends(get_db)):
    preset = get_model_preset(payload.api_endpoint or "")
    system = AISystem(
        name=payload.name,
        model_type=payload.model_type,
        provider=payload.provider or (preset.provider if preset else None),
        tier=payload.tier or (preset.tier if preset else None),
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


@router.get("/model-presets", response_model=List[ModelPresetOut])
def get_model_presets():
    return list_model_presets()


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
