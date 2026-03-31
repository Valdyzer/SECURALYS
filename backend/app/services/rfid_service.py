"""
SECURALYS - Service RFID
Gère la communication série avec l'Arduino et la logique métier RFID.

Architecture :
- Lecture en continu du port série dans un thread dédié
- Fenêtre temporelle de ±5 secondes pour associer badge + outil
- Callbacks vers l'API pour créer/retourner les emprunts
- Gestion du mode nuit
"""
import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Optional
from dataclasses import dataclass, field
from collections import deque
import serial
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RFID")


@dataclass
class Detection:
    """Représente une détection RFID."""
    type: str           # "BADGE" ou "OUTIL"
    uid: str            # Identifiant RFID
    timestamp: datetime # Moment de la détection


@dataclass 
class OuvrierPresent:
    """Ouvrier actuellement dans le conteneur."""
    ouvrier_id: int
    badge_uid: str
    entree: datetime


class RFIDService:
    """
    Service principal de gestion RFID.
    
    Logique métier :
    1. Badge détecté → toggle présence ouvrier (entrée/sortie)
    2. Outil détecté + ouvrier présent dans fenêtre ±5s → création emprunt
    3. Outil détecté sans ouvrier → alarme
    4. Mode nuit + mouvement PIR → alarme intrusion
    """
    
    FENETRE_ASSOCIATION = 5  # secondes
    
    def __init__(
        self,
        port: str = "/dev/tty.usbmodem13301",
        baud_rate: int = 9600,
        on_emprunt: Optional[Callable[[int, int], None]] = None,
        on_retour: Optional[Callable[[int], None]] = None,
        on_alarme: Optional[Callable[[str, str], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialise le service RFID.
        
        Args:
            port: Port série (ex: COM3 sur Windows, /dev/ttyUSB0 sur Linux)
            baud_rate: Vitesse de communication (9600 par défaut)
            on_emprunt: Callback(ouvrier_id, outil_id) lors d'un emprunt
            on_retour: Callback(outil_id) lors d'un retour
            on_alarme: Callback(type, message) lors d'une alarme
            on_status: Callback(status) pour les changements d'état
        """
        self.port = port
        self.baud_rate = baud_rate
        self.serial: Optional[serial.Serial] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.on_emprunt = on_emprunt
        self.on_retour = on_retour
        self.on_alarme = on_alarme
        self.on_status = on_status
        
        # État du conteneur
        self.ouvriers_presents: dict[str, OuvrierPresent] = {}  # badge_uid → OuvrierPresent
        self.detections_recentes: deque[Detection] = deque(maxlen=100)
        self.mode_nuit = False
        self.connected = False
        
        # Mapping RFID → IDs base de données (à charger depuis l'API)
        self.badge_to_ouvrier: dict[str, int] = {}
        self.tag_to_outil: dict[str, int] = {}
        self.outils_empruntes: dict[str, int] = {}  # tag_uid → emprunt_id
        
        # Lock pour thread-safety
        self.lock = threading.Lock()
    
    def charger_mappings(self, badges: dict[str, int], outils: dict[str, int]) -> None:
        """
        Charge les mappings RFID depuis la base de données.
        
        Args:
            badges: {badge_rfid: ouvrier_id}
            outils: {tag_rfid: outil_id}
        """
        with self.lock:
            self.badge_to_ouvrier = badges
            self.tag_to_outil = outils
        logger.info(f"Mappings chargés: {len(badges)} badges, {len(outils)} outils")
    
    def charger_emprunts_actifs(self, emprunts: dict[str, int]) -> None:
        """
        Charge les emprunts actifs au démarrage.
        
        Args:
            emprunts: {tag_rfid: emprunt_id}
        """
        with self.lock:
            self.outils_empruntes = emprunts
        logger.info(f"Emprunts actifs chargés: {len(emprunts)}")
    
    def start(self) -> bool:
        """Démarre le service RFID."""
        try:
            self.serial = serial.Serial(self.port, self.baud_rate, timeout=1)
            self.running = True
            self.connected = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            logger.info(f"Service RFID démarré sur {self.port}")
            return True
        except serial.SerialException as e:
            logger.error(f"Impossible d'ouvrir le port série: {e}")
            self.connected = False
            return False
    
    def stop(self) -> None:
        """Arrête proprement le service."""
        self.running = False
        if self.serial and self.serial.is_open:
            self.serial.close()
        logger.info("Service RFID arrêté")
    
    def set_mode_nuit(self, actif: bool) -> None:
        """Active ou désactive le mode nuit."""
        self.mode_nuit = actif
        if self.serial and self.serial.is_open:
            command = "NUIT:ON\n" if actif else "NUIT:OFF\n"
            self.serial.write(command.encode())
        logger.info(f"Mode nuit: {'activé' if actif else 'désactivé'}")
    
    def _read_loop(self) -> None:
        """Boucle de lecture série (thread dédié)."""
        while self.running:
            try:
                if self.serial and self.serial.in_waiting > 0:
                    line = self.serial.readline().decode("utf-8").strip()
                    if line:
                        self._process_message(line)
            except Exception as e:
                logger.error(f"Erreur lecture série: {e}")
                time.sleep(1)
    
    def _process_message(self, message: str) -> None:
        """Traite un message reçu de l'Arduino."""
        logger.info(f"[RFID] Reçu: {message}")
        
        if message.startswith("BADGE:"):
            uid = message[6:]
            self._handle_badge(uid)
        
        elif message.startswith("OUTIL:"):
            uid = message[6:]
            self._handle_outil(uid)
        
        elif message.startswith("ALARME:"):
            reason = message[7:]
            self._handle_alarme(reason)
        
        elif message.startswith("STATUS:"):
            status = message[7:]
            if self.on_status:
                self.on_status(status)
    
    def _handle_badge(self, badge_uid: str) -> None:
        """Gère la détection d'un badge ouvrier."""
        now = datetime.now()
        
        # Enregistrer la détection
        detection = Detection(type="BADGE", uid=badge_uid, timestamp=now)
        self.detections_recentes.append(detection)
        
        with self.lock:
            # Vérifier si le badge est connu
            if badge_uid not in self.badge_to_ouvrier:
                logger.warning(f"Badge inconnu: {badge_uid}")
                if self.on_alarme:
                    self.on_alarme("BADGE_INCONNU", f"Badge non enregistré: {badge_uid}")
                return
            
            ouvrier_id = self.badge_to_ouvrier[badge_uid]
            
            # Toggle présence : si déjà présent → sortie, sinon → entrée
            if badge_uid in self.ouvriers_presents:
                # Sortie du conteneur
                del self.ouvriers_presents[badge_uid]
                logger.info(f"Ouvrier {ouvrier_id} sorti du conteneur")
            else:
                # Entrée dans le conteneur
                self.ouvriers_presents[badge_uid] = OuvrierPresent(
                    ouvrier_id=ouvrier_id,
                    badge_uid=badge_uid,
                    entree=now
                )
                logger.info(f"Ouvrier {ouvrier_id} entré dans le conteneur")
    
    def _handle_outil(self, tag_uid: str) -> None:
        """Gère la détection d'un tag outil."""
        now = datetime.now()
        
        # Enregistrer la détection
        detection = Detection(type="OUTIL", uid=tag_uid, timestamp=now)
        self.detections_recentes.append(detection)
        
        with self.lock:
            # Vérifier si l'outil est connu
            if tag_uid not in self.tag_to_outil:
                logger.warning(f"Outil inconnu: {tag_uid}")
                if self.on_alarme:
                    self.on_alarme("OUTIL_INCONNU", f"Tag outil non enregistré: {tag_uid}")
                return
            
            outil_id = self.tag_to_outil[tag_uid]
            
            # Cas 1 : L'outil est actuellement emprunté → RETOUR
            if tag_uid in self.outils_empruntes:
                emprunt_id = self.outils_empruntes[tag_uid]
                del self.outils_empruntes[tag_uid]
                logger.info(f"Outil {outil_id} retourné (emprunt {emprunt_id})")
                if self.on_retour:
                    self.on_retour(emprunt_id)
                return
            
            # Cas 2 : L'outil sort → chercher un ouvrier dans la fenêtre temporelle
            ouvrier = self._trouver_ouvrier_associe(now)
            
            if ouvrier:
                # Créer l'emprunt
                logger.info(f"Outil {outil_id} emprunté par ouvrier {ouvrier.ouvrier_id}")
                if self.on_emprunt:
                    self.on_emprunt(ouvrier.ouvrier_id, outil_id)
                    # Note: l'emprunt_id sera ajouté au mapping via charger_emprunts_actifs
            else:
                # ALARME : outil sans ouvrier associé !
                logger.warning(f"ALARME: Outil {outil_id} sort sans ouvrier associé!")
                if self.on_alarme:
                    self.on_alarme("OUTIL_SANS_OUVRIER", f"Outil {outil_id} sorti sans badge détecté")
                # Envoyer commande alarme à l'Arduino
                if self.serial and self.serial.is_open:
                    self.serial.write(b"ALARM:OUTIL\n")
    
    def _trouver_ouvrier_associe(self, timestamp: datetime) -> Optional[OuvrierPresent]:
        """
        Trouve un ouvrier dans la fenêtre temporelle ±5 secondes.
        
        Priorité :
        1. Ouvrier actuellement présent dans le conteneur
        2. Badge détecté dans les 5 dernières secondes
        """
        # D'abord, vérifier les ouvriers présents
        if self.ouvriers_presents:
            # Prendre le premier ouvrier présent (ou le plus récent)
            return list(self.ouvriers_presents.values())[0]
        
        # Sinon, chercher un badge récent dans la fenêtre
        fenetre_debut = timestamp - timedelta(seconds=self.FENETRE_ASSOCIATION)
        
        for detection in reversed(self.detections_recentes):
            if detection.type != "BADGE":
                continue
            if detection.timestamp < fenetre_debut:
                break  # Trop vieux
            if detection.uid in self.badge_to_ouvrier:
                ouvrier_id = self.badge_to_ouvrier[detection.uid]
                return OuvrierPresent(
                    ouvrier_id=ouvrier_id,
                    badge_uid=detection.uid,
                    entree=detection.timestamp
                )
        
        return None
    
    def _handle_alarme(self, reason: str) -> None:
        """Gère une alarme déclenchée par l'Arduino."""
        logger.warning(f"ALARME reçue: {reason}")
        if self.on_alarme:
            self.on_alarme(reason, f"Alarme Arduino: {reason}")
    
    def get_status(self) -> dict:
        """Retourne l'état actuel du service."""
        with self.lock:
            return {
                "connected": self.connected,
                "mode_nuit": self.mode_nuit,
                "ouvriers_presents": len(self.ouvriers_presents),
                "outils_empruntes": len(self.outils_empruntes),
                "port": self.port
            }


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON POUR L'APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

_rfid_service: Optional[RFIDService] = None


def get_rfid_service() -> RFIDService:
    """Retourne l'instance singleton du service RFID."""
    global _rfid_service
    if _rfid_service is None:
        _rfid_service = RFIDService()
    return _rfid_service


def init_rfid_service(port: str = "COM3", **callbacks) -> RFIDService:
    """Initialise le service RFID avec la configuration."""
    global _rfid_service
    _rfid_service = RFIDService(port=port, **callbacks)
    return _rfid_service
