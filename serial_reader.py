import threading
import serial

from config import SERIAL_PORT, BAUD_RATE, TIMEOUT
from database import save_alarm


class SerialReader:
    """
    Lit en continu le port série dans un thread dédié.
    Appelle `on_event(code)` à chaque message reçu :
        1  → MOUVEMENT DETECTE
        2  → PRESENCE (alarme)
        3  → CALME / FAUSSE ALERTE
    """

    def __init__(self, on_event):
        self.on_event  = on_event
        self.running   = False
        self.ser       = None
        self.thread    = None

    def start(self) -> None:
        """Ouvre le port série et démarre le thread de lecture."""
        self.ser     = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
        self.running = True
        self.thread  = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Arrête proprement la lecture et ferme le port."""
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()

    def _read_loop(self) -> None:
        while self.running:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode("utf-8").strip()
                print(f"[SERIAL] Reçu : '{line}' | Longueur : {len(line)}")
                self._dispatch(line)

    def _dispatch(self, line: str) -> None:
        """Identifie le message et déclenche la sauvegarde + callback UI."""
        if line == "MOUVEMENT DETECTE":
            save_alarm("MOUVEMENT DETECTE")
            self.on_event(1)
        elif line == "PRESENCE":
            save_alarm("ALARME - PRESENCE")
            self.on_event(2)
        elif line in ("CALME", "FAUSSE ALERTE"):
            self.on_event(3)
