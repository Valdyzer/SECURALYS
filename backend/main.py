"""
SECURALYS - API Backend
Serveur FastAPI pour la gestion du conteneur connecté.
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.models import Base, engine, SessionLocal, Ouvrier, Outil, Emprunt
from app.api import ouvriers, outils, emprunts, dashboard, rfid, notifications
from app.services.rfid_service import get_rfid_service

# Créer les tables au démarrage
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SECURALYS API",
    description="API de gestion du conteneur connecté - Traçabilité outils & ouvriers",
    version="1.0.0"
)

# CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrer les routes API
app.include_router(ouvriers.router, prefix="/api/ouvriers", tags=["Ouvriers"])
app.include_router(outils.router, prefix="/api/outils", tags=["Outils"])
app.include_router(emprunts.router, prefix="/api/emprunts", tags=["Emprunts"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(rfid.router, prefix="/api/rfid", tags=["RFID"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])

# Servir les fichiers statiques du frontend
# Utiliser le chemin absolu pour éviter les problèmes avec le working directory
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.on_event("startup")
def load_rfid_mappings():
    """Charge les mappings RFID au démarrage pour permettre la simulation."""
    from app.api.rfid import create_emprunt_callback, retour_emprunt_callback, alarme_callback
    
    db = SessionLocal()
    try:
        service = get_rfid_service()
        
        # Configurer les callbacks
        service.on_emprunt = create_emprunt_callback
        service.on_retour = retour_emprunt_callback
        service.on_alarme = alarme_callback
        
        # Charger les mappings badges → ouvriers
        ouvriers_db = db.query(Ouvrier).filter(Ouvrier.actif == True).all()
        badges = {o.badge_rfid: o.id for o in ouvriers_db}
        
        # Charger les mappings tags → outils
        outils_db = db.query(Outil).all()
        tags = {o.tag_rfid: o.id for o in outils_db}
        
        service.charger_mappings(badges, tags)
        
        # Charger les emprunts actifs
        emprunts_db = db.query(Emprunt).all()
        emprunts_actifs = {}
        for e in emprunts_db:
            outil = db.query(Outil).filter(Outil.id == e.outil_id).first()
            if outil:
                emprunts_actifs[outil.tag_rfid] = e.id
        service.charger_emprunts_actifs(emprunts_actifs)
        
    finally:
        db.close()


@app.get("/")
def root():
    """Sert la page principale du frontend."""
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/styles.css")
def serve_css():
    """Sert le fichier CSS."""
    return FileResponse(FRONTEND_DIR / "styles.css", media_type="text/css")


@app.get("/app.js")
def serve_js():
    """Sert le fichier JavaScript."""
    return FileResponse(FRONTEND_DIR / "app.js", media_type="application/javascript")


@app.get("/api/status")
def api_status():
    """Retourne le statut général de l'API et de la connexion Arduino."""
    service = get_rfid_service()
    status = service.get_status()
    return {
        "api": "online",
        "arduino_connected": status["connected"],
        "mode_nuit": status["mode_nuit"],
        "ouvriers_presents": status["ouvriers_presents"]
    }
