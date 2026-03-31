from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class Outil(Base):
    """Table des outils stockés dans le conteneur."""
    
    __tablename__ = "outils"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    tag_rfid = Column(String(50), unique=True, nullable=False, index=True)
    categorie = Column(String(50), nullable=True)  # électroportatif, manuel, mesure...
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    emprunts = relationship("Emprunt", back_populates="outil")
    historiques = relationship("Historique", back_populates="outil")

    def __repr__(self):
        return f"<Outil {self.nom} ({self.tag_rfid})>"
    
    @property
    def est_disponible(self):
        """Retourne True si l'outil n'a pas d'emprunt en cours."""
        return not any(e.statut == "en_cours" for e in self.emprunts)
