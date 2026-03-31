"""
SECURALYS - API RFID
Endpoints pour contrôler le service RFID et le mode nuit.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..models import get_db, Ouvrier, Outil, Emprunt
from ..services.rfid_service import get_rfid_service, init_rfid_service

router = APIRouter()


class ModeNuitRequest(BaseModel):
    actif: bool


class RFIDConnectRequest(BaseModel):
    port: str = "/dev/tty.usbmodem13301"


# ═══════════════════════════════════════════════════════════════════════════
# CALLBACKS POUR LE SERVICE RFID
# ═══════════════════════════════════════════════════════════════════════════

def create_emprunt_callback(ouvrier_id: int, outil_id: int) -> None:
    """Callback appelé par le service RFID lors d'un emprunt."""
    from ..models.base import SessionLocal
    from datetime import datetime
    
    db = SessionLocal()
    try:
        # Créer l'emprunt
        emprunt = Emprunt(
            ouvrier_id=ouvrier_id,
            outil_id=outil_id,
            heure_sortie=datetime.now()
        )
        db.add(emprunt)
        db.commit()
        
        # Mettre à jour le mapping dans le service RFID
        outil = db.query(Outil).filter(Outil.id == outil_id).first()
        if outil:
            service = get_rfid_service()
            service.outils_empruntes[outil.tag_rfid] = emprunt.id
    finally:
        db.close()


def retour_emprunt_callback(emprunt_id: int) -> None:
    """Callback appelé par le service RFID lors d'un retour."""
    from ..models.base import SessionLocal
    from ..models.historique import Historique
    from datetime import datetime
    
    db = SessionLocal()
    try:
        emprunt = db.query(Emprunt).filter(Emprunt.id == emprunt_id).first()
        if emprunt:
            # Créer l'entrée historique
            heure_retour = datetime.now()
            duree = int((heure_retour - emprunt.heure_sortie).total_seconds() / 60)
            
            historique = Historique(
                ouvrier_id=emprunt.ouvrier_id,
                outil_id=emprunt.outil_id,
                heure_sortie=emprunt.heure_sortie,
                heure_retour=heure_retour,
                duree_minutes=duree
            )
            db.add(historique)
            
            # Supprimer l'emprunt
            db.delete(emprunt)
            db.commit()
    finally:
        db.close()


def alarme_callback(type_alarme: str, message: str) -> None:
    """Callback appelé par le service RFID lors d'une alarme."""
    import logging
    logger = logging.getLogger("ALARME")
    logger.warning(f"[{type_alarme}] {message}")
    # TODO: Envoyer notification (email, push, etc.)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/status")
def rfid_status():
    """Retourne l'état du service RFID."""
    service = get_rfid_service()
    return service.get_status()


@router.post("/connect")
def rfid_connect(request: RFIDConnectRequest, db: Session = Depends(get_db)):
    """
    Connecte le service RFID au port série spécifié.
    Charge automatiquement les mappings depuis la base de données.
    """
    # Initialiser le service avec les callbacks
    service = init_rfid_service(
        port=request.port,
        on_emprunt=create_emprunt_callback,
        on_retour=retour_emprunt_callback,
        on_alarme=alarme_callback
    )
    
    # Charger les mappings badges → ouvriers
    ouvriers = db.query(Ouvrier).filter(Ouvrier.actif == True).all()
    badges = {o.badge_rfid: o.id for o in ouvriers}
    
    # Charger les mappings tags → outils
    outils = db.query(Outil).all()
    tags = {o.tag_rfid: o.id for o in outils}
    
    service.charger_mappings(badges, tags)
    
    # Charger les emprunts actifs
    emprunts = db.query(Emprunt).all()
    emprunts_actifs = {}
    for e in emprunts:
        outil = db.query(Outil).filter(Outil.id == e.outil_id).first()
        if outil:
            emprunts_actifs[outil.tag_rfid] = e.id
    service.charger_emprunts_actifs(emprunts_actifs)
    
    # Démarrer le service
    if service.start():
        return {"status": "connected", "port": request.port}
    else:
        raise HTTPException(status_code=500, detail=f"Impossible de se connecter au port {request.port}")


@router.post("/disconnect")
def rfid_disconnect():
    """Déconnecte le service RFID."""
    service = get_rfid_service()
    service.stop()
    return {"status": "disconnected"}


@router.post("/mode-nuit")
def set_mode_nuit(request: ModeNuitRequest):
    """Active ou désactive le mode nuit."""
    service = get_rfid_service()
    service.set_mode_nuit(request.actif)
    return {"mode_nuit": request.actif}


@router.get("/presences")
def get_presences():
    """Retourne la liste des ouvriers actuellement dans le conteneur."""
    service = get_rfid_service()
    presences = []
    for badge_uid, ouvrier in service.ouvriers_presents.items():
        presences.append({
            "ouvrier_id": ouvrier.ouvrier_id,
            "badge_uid": badge_uid,
            "entree": ouvrier.entree.isoformat()
        })
    return presences


@router.post("/simulate/badge/{badge_uid}")
def simulate_badge(badge_uid: str):
    """
    Simule la détection d'un badge (pour tests sans Arduino).
    """
    service = get_rfid_service()
    
    # Vérifier si l'ouvrier est présent
    was_present = badge_uid in service.ouvriers_presents
    
    service._handle_badge(badge_uid)
    
    # Déterminer l'action effectuée
    is_present_now = badge_uid in service.ouvriers_presents
    action = "Entrée dans le conteneur" if is_present_now else "Sortie du conteneur"
    
    return {"simulated": "badge", "uid": badge_uid, "action": action}


@router.post("/simulate/outil/{tag_uid}")
def simulate_outil(tag_uid: str):
    """
    Simule la détection d'un outil (pour tests sans Arduino).
    """
    service = get_rfid_service()
    
    # Vérifier si l'outil est déjà emprunté
    was_borrowed = tag_uid in service.outils_empruntes
    
    service._handle_outil(tag_uid)
    
    # Déterminer le résultat
    is_borrowed_now = tag_uid in service.outils_empruntes
    if was_borrowed and not is_borrowed_now:
        result = "Retour enregistré"
    elif not was_borrowed and is_borrowed_now:
        result = "Emprunt créé"
    elif not was_borrowed:
        result = "Alarme déclenchée (pas d'ouvrier détecté)"
    else:
        result = "Aucune action"
    
    return {"simulated": "outil", "uid": tag_uid, "result": result}
