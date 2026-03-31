"""API CRUD pour les outils."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models import get_db, Outil, Emprunt
from app.schemas import OutilCreate, OutilUpdate, OutilResponse

router = APIRouter()


def _check_disponible(outil_id: int, db: Session) -> bool:
    """Vérifie si un outil est disponible."""
    emprunt = db.query(Emprunt).filter(
        Emprunt.outil_id == outil_id,
        Emprunt.statut == "en_cours"
    ).first()
    return emprunt is None


@router.get("/", response_model=List[dict])
def list_outils(
    disponible: Optional[bool] = None,
    categorie: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Liste tous les outils avec filtres optionnels."""
    query = db.query(Outil)
    
    if categorie:
        query = query.filter(Outil.categorie == categorie)
    
    outils = query.all()
    result = []
    
    for outil in outils:
        est_dispo = _check_disponible(outil.id, db)
        
        # Filtrer par disponibilité si demandé
        if disponible is not None and disponible != est_dispo:
            continue
        
        result.append({
            "id": outil.id,
            "nom": outil.nom,
            "description": outil.description,
            "tag_rfid": outil.tag_rfid,
            "categorie": outil.categorie,
            "created_at": outil.created_at,
            "est_disponible": est_dispo
        })
    
    return result


@router.get("/{outil_id}", response_model=dict)
def get_outil(outil_id: int, db: Session = Depends(get_db)):
    """Récupère un outil par son ID."""
    outil = db.query(Outil).filter(Outil.id == outil_id).first()
    if not outil:
        raise HTTPException(status_code=404, detail="Outil non trouvé")
    
    return {
        "id": outil.id,
        "nom": outil.nom,
        "description": outil.description,
        "tag_rfid": outil.tag_rfid,
        "categorie": outil.categorie,
        "created_at": outil.created_at,
        "est_disponible": _check_disponible(outil.id, db)
    }


@router.get("/tag/{tag_rfid}", response_model=dict)
def get_outil_by_tag(tag_rfid: str, db: Session = Depends(get_db)):
    """Récupère un outil par son tag RFID."""
    outil = db.query(Outil).filter(Outil.tag_rfid == tag_rfid).first()
    if not outil:
        raise HTTPException(status_code=404, detail="Tag RFID non reconnu")
    
    return {
        "id": outil.id,
        "nom": outil.nom,
        "description": outil.description,
        "tag_rfid": outil.tag_rfid,
        "categorie": outil.categorie,
        "created_at": outil.created_at,
        "est_disponible": _check_disponible(outil.id, db)
    }


@router.post("/", response_model=dict, status_code=201)
def create_outil(outil: OutilCreate, db: Session = Depends(get_db)):
    """Crée un nouvel outil."""
    existing = db.query(Outil).filter(Outil.tag_rfid == outil.tag_rfid).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce tag RFID est déjà attribué")
    
    db_outil = Outil(**outil.model_dump())
    db.add(db_outil)
    db.commit()
    db.refresh(db_outil)
    
    return {
        "id": db_outil.id,
        "nom": db_outil.nom,
        "description": db_outil.description,
        "tag_rfid": db_outil.tag_rfid,
        "categorie": db_outil.categorie,
        "created_at": db_outil.created_at,
        "est_disponible": True
    }


@router.put("/{outil_id}", response_model=OutilResponse)
def update_outil(outil_id: int, outil: OutilUpdate, db: Session = Depends(get_db)):
    """Met à jour un outil."""
    db_outil = db.query(Outil).filter(Outil.id == outil_id).first()
    if not db_outil:
        raise HTTPException(status_code=404, detail="Outil non trouvé")
    
    update_data = outil.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_outil, field, value)
    
    db.commit()
    db.refresh(db_outil)
    return db_outil


@router.delete("/{outil_id}", status_code=204)
def delete_outil(outil_id: int, db: Session = Depends(get_db)):
    """Supprime un outil."""
    db_outil = db.query(Outil).filter(Outil.id == outil_id).first()
    if not db_outil:
        raise HTTPException(status_code=404, detail="Outil non trouvé")
    
    db.delete(db_outil)
    db.commit()
