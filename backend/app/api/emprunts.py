"""API pour la gestion des emprunts d'outils."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.models import get_db, Emprunt, Outil, Ouvrier, Historique
from app.schemas import EmpruntCreate, EmpruntResponse

router = APIRouter()


@router.get("/", response_model=List[EmpruntResponse])
def list_emprunts(en_cours_only: bool = True, db: Session = Depends(get_db)):
    """Liste les emprunts (par défaut, uniquement ceux en cours)."""
    query = db.query(Emprunt)
    if en_cours_only:
        query = query.filter(Emprunt.statut == "en_cours")
    
    emprunts = query.all()
    
    # Enrichir avec les noms
    result = []
    for e in emprunts:
        outil = db.query(Outil).filter(Outil.id == e.outil_id).first()
        ouvrier = db.query(Ouvrier).filter(Ouvrier.id == e.ouvrier_id).first()
        
        result.append(EmpruntResponse(
            id=e.id,
            outil_id=e.outil_id,
            ouvrier_id=e.ouvrier_id,
            heure_sortie=e.heure_sortie,
            heure_retour=e.heure_retour,
            statut=e.statut,
            outil_nom=outil.nom if outil else None,
            ouvrier_nom=f"{ouvrier.prenom} {ouvrier.nom}" if ouvrier else None
        ))
    
    return result


@router.get("/{emprunt_id}", response_model=EmpruntResponse)
def get_emprunt(emprunt_id: int, db: Session = Depends(get_db)):
    """Récupère un emprunt par son ID."""
    emprunt = db.query(Emprunt).filter(Emprunt.id == emprunt_id).first()
    if not emprunt:
        raise HTTPException(status_code=404, detail="Emprunt non trouvé")
    
    outil = db.query(Outil).filter(Outil.id == emprunt.outil_id).first()
    ouvrier = db.query(Ouvrier).filter(Ouvrier.id == emprunt.ouvrier_id).first()
    
    return EmpruntResponse(
        id=emprunt.id,
        outil_id=emprunt.outil_id,
        ouvrier_id=emprunt.ouvrier_id,
        heure_sortie=emprunt.heure_sortie,
        heure_retour=emprunt.heure_retour,
        statut=emprunt.statut,
        outil_nom=outil.nom if outil else None,
        ouvrier_nom=f"{ouvrier.prenom} {ouvrier.nom}" if ouvrier else None
    )


@router.post("/", response_model=EmpruntResponse, status_code=201)
def create_emprunt(emprunt: EmpruntCreate, db: Session = Depends(get_db)):
    """Crée un nouvel emprunt (sortie d'outil)."""
    # Vérifier que l'outil existe
    outil = db.query(Outil).filter(Outil.id == emprunt.outil_id).first()
    if not outil:
        raise HTTPException(status_code=404, detail="Outil non trouvé")
    
    # Vérifier que l'ouvrier existe
    ouvrier = db.query(Ouvrier).filter(Ouvrier.id == emprunt.ouvrier_id).first()
    if not ouvrier:
        raise HTTPException(status_code=404, detail="Ouvrier non trouvé")
    
    # Vérifier que l'outil n'est pas déjà emprunté
    emprunt_existant = db.query(Emprunt).filter(
        Emprunt.outil_id == emprunt.outil_id,
        Emprunt.statut == "en_cours"
    ).first()
    if emprunt_existant:
        raise HTTPException(status_code=400, detail="Cet outil est déjà emprunté")
    
    # Créer l'emprunt
    db_emprunt = Emprunt(
        outil_id=emprunt.outil_id,
        ouvrier_id=emprunt.ouvrier_id
    )
    db.add(db_emprunt)
    db.commit()
    db.refresh(db_emprunt)
    
    return EmpruntResponse(
        id=db_emprunt.id,
        outil_id=db_emprunt.outil_id,
        ouvrier_id=db_emprunt.ouvrier_id,
        heure_sortie=db_emprunt.heure_sortie,
        heure_retour=db_emprunt.heure_retour,
        statut=db_emprunt.statut,
        outil_nom=outil.nom,
        ouvrier_nom=f"{ouvrier.prenom} {ouvrier.nom}"
    )


@router.put("/{emprunt_id}/retour", response_model=EmpruntResponse)
def retour_emprunt(emprunt_id: int, db: Session = Depends(get_db)):
    """Marque un emprunt comme terminé (retour de l'outil)."""
    emprunt = db.query(Emprunt).filter(Emprunt.id == emprunt_id).first()
    if not emprunt:
        raise HTTPException(status_code=404, detail="Emprunt non trouvé")
    
    if emprunt.statut == "termine":
        raise HTTPException(status_code=400, detail="Cet emprunt est déjà terminé")
    
    # Marquer comme terminé
    emprunt.heure_retour = datetime.utcnow()
    emprunt.statut = "termine"
    
    # Calculer la durée et créer l'historique
    duree = int((emprunt.heure_retour - emprunt.heure_sortie).total_seconds() / 60)
    historique = Historique(
        outil_id=emprunt.outil_id,
        ouvrier_id=emprunt.ouvrier_id,
        heure_sortie=emprunt.heure_sortie,
        heure_retour=emprunt.heure_retour,
        duree_minutes=duree
    )
    db.add(historique)
    db.commit()
    db.refresh(emprunt)
    
    outil = db.query(Outil).filter(Outil.id == emprunt.outil_id).first()
    ouvrier = db.query(Ouvrier).filter(Ouvrier.id == emprunt.ouvrier_id).first()
    
    return EmpruntResponse(
        id=emprunt.id,
        outil_id=emprunt.outil_id,
        ouvrier_id=emprunt.ouvrier_id,
        heure_sortie=emprunt.heure_sortie,
        heure_retour=emprunt.heure_retour,
        statut=emprunt.statut,
        outil_nom=outil.nom if outil else None,
        ouvrier_nom=f"{ouvrier.prenom} {ouvrier.nom}" if ouvrier else None
    )
