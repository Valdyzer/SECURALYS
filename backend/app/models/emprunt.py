from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class Emprunt(Base):
    """Table des emprunts en cours (outils sortis du conteneur)."""
    
    __tablename__ = "emprunts"

    id = Column(Integer, primary_key=True, index=True)
    outil_id = Column(Integer, ForeignKey("outils.id"), nullable=False)
    ouvrier_id = Column(Integer, ForeignKey("ouvriers.id"), nullable=False)
    heure_sortie = Column(DateTime, default=datetime.utcnow, nullable=False)
    heure_retour = Column(DateTime, nullable=True)
    statut = Column(String(20), default="en_cours")  # en_cours, termine
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    outil = relationship("Outil", back_populates="emprunts")
    ouvrier = relationship("Ouvrier", back_populates="emprunts")

    def __repr__(self):
        return f"<Emprunt {self.outil.nom} -> {self.ouvrier.nom_complet}>"
    
    @property
    def duree(self):
        """Calcule la durée de l'emprunt en minutes."""
        fin = self.heure_retour or datetime.utcnow()
        delta = fin - self.heure_sortie
        return int(delta.total_seconds() / 60)
