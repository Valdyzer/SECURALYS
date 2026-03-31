"""API CRUD pour les ouvriers."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models import get_db, Ouvrier
from app.schemas import OuvrierCreate, OuvrierUpdate, OuvrierResponse

router = APIRouter()


@router.get("/", response_model=List[OuvrierResponse])
def list_ouvriers(actif_only: bool = False, db: Session = Depends(get_db)):
    """Liste tous les ouvriers."""
    query = db.query(Ouvrier)
    if actif_only:
        query = query.filter(Ouvrier.actif == True)
    return query.all()


@router.get("/{ouvrier_id}", response_model=OuvrierResponse)
def get_ouvrier(ouvrier_id: int, db: Session = Depends(get_db)):
    """Récupère un ouvrier par son ID."""
    ouvrier = db.query(Ouvrier).filter(Ouvrier.id == ouvrier_id).first()
    if not ouvrier:
        raise HTTPException(status_code=404, detail="Ouvrier non trouvé")
    return ouvrier


@router.get("/badge/{badge_rfid}", response_model=OuvrierResponse)
def get_ouvrier_by_badge(badge_rfid: str, db: Session = Depends(get_db)):
    """Récupère un ouvrier par son badge RFID."""
    ouvrier = db.query(Ouvrier).filter(Ouvrier.badge_rfid == badge_rfid).first()
    if not ouvrier:
        raise HTTPException(status_code=404, detail="Badge non reconnu")
    return ouvrier


@router.post("/", response_model=OuvrierResponse, status_code=201)
def create_ouvrier(ouvrier: OuvrierCreate, db: Session = Depends(get_db)):
    """Crée un nouvel ouvrier."""
    # Vérifier unicité du badge
    existing = db.query(Ouvrier).filter(Ouvrier.badge_rfid == ouvrier.badge_rfid).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce badge RFID est déjà attribué")
    
    db_ouvrier = Ouvrier(**ouvrier.model_dump())
    db.add(db_ouvrier)
    db.commit()
    db.refresh(db_ouvrier)
    return db_ouvrier


@router.put("/{ouvrier_id}", response_model=OuvrierResponse)
def update_ouvrier(ouvrier_id: int, ouvrier: OuvrierUpdate, db: Session = Depends(get_db)):
    """Met à jour un ouvrier."""
    db_ouvrier = db.query(Ouvrier).filter(Ouvrier.id == ouvrier_id).first()
    if not db_ouvrier:
        raise HTTPException(status_code=404, detail="Ouvrier non trouvé")
    
    update_data = ouvrier.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ouvrier, field, value)
    
    db.commit()
    db.refresh(db_ouvrier)
    return db_ouvrier


@router.delete("/{ouvrier_id}", status_code=204)
def delete_ouvrier(ouvrier_id: int, db: Session = Depends(get_db)):
    """Supprime un ouvrier."""
    db_ouvrier = db.query(Ouvrier).filter(Ouvrier.id == ouvrier_id).first()
    if not db_ouvrier:
        raise HTTPException(status_code=404, detail="Ouvrier non trouvé")
    
    db.delete(db_ouvrier)
    db.commit()
