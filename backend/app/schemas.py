"""Schémas Pydantic pour validation des données."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# ─── Ouvriers ──────────────────────────────────────────────────────────────────

class OuvrierBase(BaseModel):
    nom: str
    prenom: str
    badge_rfid: str
    role: str = "ouvrier"
    email: Optional[str] = None
    actif: bool = True

class OuvrierCreate(OuvrierBase):
    pass

class OuvrierUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    badge_rfid: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    actif: Optional[bool] = None

class OuvrierResponse(OuvrierBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ─── Outils ────────────────────────────────────────────────────────────────────

class OutilBase(BaseModel):
    nom: str
    tag_rfid: str
    description: Optional[str] = None
    categorie: Optional[str] = None

class OutilCreate(OutilBase):
    pass

class OutilUpdate(BaseModel):
    nom: Optional[str] = None
    tag_rfid: Optional[str] = None
    description: Optional[str] = None
    categorie: Optional[str] = None

class OutilResponse(OutilBase):
    id: int
    created_at: datetime
    est_disponible: bool = True
    
    class Config:
        from_attributes = True


# ─── Emprunts ──────────────────────────────────────────────────────────────────

class EmpruntCreate(BaseModel):
    outil_id: int
    ouvrier_id: int

class EmpruntResponse(BaseModel):
    id: int
    outil_id: int
    ouvrier_id: int
    heure_sortie: datetime
    heure_retour: Optional[datetime] = None
    statut: str
    outil_nom: Optional[str] = None
    ouvrier_nom: Optional[str] = None
    
    class Config:
        from_attributes = True


# ─── Historique ────────────────────────────────────────────────────────────────

class HistoriqueResponse(BaseModel):
    id: int
    outil_id: int
    ouvrier_id: int
    heure_sortie: datetime
    heure_retour: datetime
    duree_minutes: int
    outil_nom: Optional[str] = None
    ouvrier_nom: Optional[str] = None
    
    class Config:
        from_attributes = True


# ─── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_outils: int
    outils_disponibles: int
    outils_empruntes: int
    emprunts_en_cours: int
    total_ouvriers: int
    ouvriers_actifs: int
