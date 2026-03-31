from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class Ouvrier(Base):
    """Table des ouvriers habilités à emprunter des outils."""
    
    __tablename__ = "ouvriers"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    badge_rfid = Column(String(50), unique=True, nullable=False, index=True)
    role = Column(String(50), default="ouvrier")  # ouvrier, chef, conduc
    email = Column(String(100), nullable=True)
    actif = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    emprunts = relationship("Emprunt", back_populates="ouvrier")
    historiques = relationship("Historique", back_populates="ouvrier")

    def __repr__(self):
        return f"<Ouvrier {self.prenom} {self.nom} ({self.badge_rfid})>"
    
    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"
