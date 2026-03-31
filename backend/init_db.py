"""
Script d'initialisation de la base de données SECURALYS.
Crée les tables et insère des données de test.
"""
from app.models import Base, engine, SessionLocal, Ouvrier, Outil


def init_db():
    """Crée toutes les tables dans la base de données."""
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées avec succès")


def seed_data():
    """Insère des données de test."""
    db = SessionLocal()
    
    # Vérifier si des données existent déjà
    if db.query(Ouvrier).count() > 0:
        print("⚠️  Données déjà présentes, skip seed")
        db.close()
        return
    
    # Ouvriers de test
    ouvriers = [
        Ouvrier(nom="Dupont", prenom="Jean", badge_rfid="BADGE001", role="ouvrier"),
        Ouvrier(nom="Martin", prenom="Pierre", badge_rfid="BADGE002", role="ouvrier"),
        Ouvrier(nom="Bernard", prenom="Sophie", badge_rfid="BADGE003", role="chef"),
        Ouvrier(nom="Petit", prenom="Marc", badge_rfid="BADGE004", role="conduc", 
                email="marc.petit@chantier.fr"),
    ]
    
    # Outils de test
    outils = [
        Outil(nom="Perceuse Bosch", tag_rfid="OUTIL001", categorie="électroportatif"),
        Outil(nom="Visseuse Makita", tag_rfid="OUTIL002", categorie="électroportatif"),
        Outil(nom="Marteau", tag_rfid="OUTIL003", categorie="manuel"),
        Outil(nom="Niveau laser", tag_rfid="OUTIL004", categorie="mesure"),
        Outil(nom="Scie circulaire", tag_rfid="OUTIL005", categorie="électroportatif"),
        Outil(nom="Mètre ruban 5m", tag_rfid="OUTIL006", categorie="mesure"),
        Outil(nom="Pince multiprise", tag_rfid="OUTIL007", categorie="manuel"),
        Outil(nom="Disqueuse", tag_rfid="OUTIL008", categorie="électroportatif"),
    ]
    
    db.add_all(ouvriers)
    db.add_all(outils)
    db.commit()
    db.close()
    
    print(f"✅ Données de test insérées : {len(ouvriers)} ouvriers, {len(outils)} outils")


if __name__ == "__main__":
    print("🔧 Initialisation de la base de données SECURALYS...")
    init_db()
    seed_data()
    print("🎉 Terminé !")
