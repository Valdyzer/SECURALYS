"""
SECURALYS - API Notifications
Endpoints pour gérer le système de notifications automatiques.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..models import get_db, Emprunt, Ouvrier, Outil
from ..services.notification_service import get_notification_service

router = APIRouter()


class NotificationConfigUpdate(BaseModel):
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_responsable: Optional[str] = None
    heure_fin_journee: Optional[str] = None  # Format "HH:MM"
    actif: Optional[bool] = None


def get_emprunts_for_notification(db: Session) -> list:
    """Récupère les emprunts actifs formatés pour les notifications."""
    emprunts = db.query(Emprunt).all()
    result = []
    
    for e in emprunts:
        ouvrier = db.query(Ouvrier).filter(Ouvrier.id == e.ouvrier_id).first()
        outil = db.query(Outil).filter(Outil.id == e.outil_id).first()
        
        result.append({
            "id": e.id,
            "outil_nom": outil.nom if outil else "Inconnu",
            "ouvrier_nom": f"{ouvrier.prenom} {ouvrier.nom}" if ouvrier else "Inconnu",
            "heure_sortie": e.heure_sortie.strftime("%H:%M") if e.heure_sortie else "N/A"
        })
    
    return result


@router.get("/status")
def notification_status():
    """Retourne l'état du service de notifications."""
    service = get_notification_service()
    return {
        "actif": service.config.actif,
        "heure_fin_journee": service.config.heure_fin_journee.strftime("%H:%M"),
        "email_responsable": service.config.email_responsable or "Non configuré",
        "smtp_configured": bool(service.config.smtp_user),
        "last_check": service.last_check.isoformat() if service.last_check else None,
        "running": service.running
    }


@router.get("/config")
def get_notification_config():
    """Retourne la configuration actuelle des notifications."""
    service = get_notification_service()
    return {
        "email_responsable": service.config.email_responsable or "",
        "heure_fin_journee": service.config.heure_fin_journee.strftime("%H:%M"),
        "actif": service.config.actif,
        "smtp_server": service.config.smtp_server,
        "smtp_port": service.config.smtp_port
    }


@router.put("/config")
def update_notification_config(config: NotificationConfigUpdate):
    """Met à jour la configuration des notifications."""
    service = get_notification_service()
    service.update_config(**config.dict(exclude_none=True))
    return {"status": "updated"}


@router.post("/start")
def start_notifications(db: Session = Depends(get_db)):
    """Démarre le service de notifications."""
    service = get_notification_service()
    
    # Configurer le callback pour récupérer les emprunts
    def get_emprunts():
        from ..models.base import SessionLocal
        session = SessionLocal()
        try:
            return get_emprunts_for_notification(session)
        finally:
            session.close()
    
    service.set_emprunts_callback(get_emprunts)
    service.start()
    
    return {"status": "started"}


@router.post("/stop")
def stop_notifications():
    """Arrête le service de notifications."""
    service = get_notification_service()
    service.stop()
    return {"status": "stopped"}


@router.post("/test")
def test_notifications(db: Session = Depends(get_db)):
    """
    Force une vérification immédiate et envoie une notification de test.
    Utile pour tester la configuration email.
    """
    service = get_notification_service()
    
    # Configurer le callback si pas fait
    def get_emprunts():
        return get_emprunts_for_notification(db)
    
    service.set_emprunts_callback(get_emprunts)
    
    result = service.force_check()
    return result


@router.get("/preview")
def preview_notification(db: Session = Depends(get_db)):
    """
    Prévisualise ce que contiendrait la notification actuelle
    sans l'envoyer.
    """
    emprunts = get_emprunts_for_notification(db)
    
    return {
        "emprunts_count": len(emprunts),
        "emprunts": emprunts,
        "message": "Tous les outils sont rendus ✓" if not emprunts else f"{len(emprunts)} outil(s) non rendu(s)"
    }
