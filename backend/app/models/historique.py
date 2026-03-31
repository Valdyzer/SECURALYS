from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class Historique(Base):
    """Table d'historique des utilisations d'outils (emprunts terminés)."""
    
    __tablename__ = "historique"

    id = Column(Integer, primary_key=True, index=True)
    outil_id = Column(Integer, ForeignKey("outils.id"), nullable=False)
    ouvrier_id = Column(Integer, ForeignKey("ouvriers.id"), nullable=False)
    heure_sortie = Column(DateTime, nullable=False)
    heure_retour = Column(DateTime, nullable=False)
    duree_minutes = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    outil = relationship("Outil", back_populates="historiques")
    ouvrier = relationship("Ouvrier", back_populates="historiques")

    def __repr__(self):
        return f"<Historique {self.outil.nom} par {self.ouvrier.nom_complet} ({self.duree_minutes}min)>"
    
    @classmethod
    def from_emprunt(cls, emprunt):
        """Crée une entrée historique à partir d'un emprunt terminé."""
        return cls(
            outil_id=emprunt.outil_id,
            ouvrier_id=emprunt.ouvrier_id,
            heure_sortie=emprunt.heure_sortie,
            heure_retour=emprunt.heure_retour,
            duree_minutes=emprunt.duree
        )
