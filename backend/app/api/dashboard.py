"""API Dashboard - Stats et alertes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.models import get_db, Outil, Ouvrier, Emprunt, Historique
from app.schemas import DashboardStats, EmpruntResponse, HistoriqueResponse

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)):
    """Récupère les statistiques du dashboard."""
    total_outils = db.query(Outil).count()
    total_ouvriers = db.query(Ouvrier).count()
    ouvriers_actifs = db.query(Ouvrier).filter(Ouvrier.actif == True).count()
    emprunts_en_cours = db.query(Emprunt).filter(Emprunt.statut == "en_cours").count()
    
    return DashboardStats(
        total_outils=total_outils,
        outils_disponibles=total_outils - emprunts_en_cours,
        outils_empruntes=emprunts_en_cours,
        emprunts_en_cours=emprunts_en_cours,
        total_ouvriers=total_ouvriers,
        ouvriers_actifs=ouvriers_actifs
    )


@router.get("/alertes", response_model=List[EmpruntResponse])
def get_alertes(db: Session = Depends(get_db)):
    """Récupère les emprunts en cours (outils non rendus)."""
    emprunts = db.query(Emprunt).filter(Emprunt.statut == "en_cours").all()
    
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


@router.get("/historique", response_model=List[HistoriqueResponse])
def get_historique(
    limit: int = 50,
    outil_id: int = None,
    ouvrier_id: int = None,
    db: Session = Depends(get_db)
):
    """Récupère l'historique des utilisations."""
    query = db.query(Historique)
    
    if outil_id:
        query = query.filter(Historique.outil_id == outil_id)
    if ouvrier_id:
        query = query.filter(Historique.ouvrier_id == ouvrier_id)
    
    historiques = query.order_by(Historique.created_at.desc()).limit(limit).all()
    
    result = []
    for h in historiques:
        outil = db.query(Outil).filter(Outil.id == h.outil_id).first()
        ouvrier = db.query(Ouvrier).filter(Ouvrier.id == h.ouvrier_id).first()
        
        result.append(HistoriqueResponse(
            id=h.id,
            outil_id=h.outil_id,
            ouvrier_id=h.ouvrier_id,
            heure_sortie=h.heure_sortie,
            heure_retour=h.heure_retour,
            duree_minutes=h.duree_minutes,
            outil_nom=outil.nom if outil else None,
            ouvrier_nom=f"{ouvrier.prenom} {ouvrier.nom}" if ouvrier else None
        ))
    
    return result
