# ─── Configuration générale ───────────────────────────────────────────────────

# Port série de l'Arduino (à ajuster selon votre système)
# Windows  : "COM3", "COM4", ...
# Linux    : "/dev/ttyACM0", "/dev/ttyUSB0"
# macOS    : "/dev/cu.usbmodem13301"
SERIAL_PORT = "/dev/cu.usbmodem13301"
BAUD_RATE   = 9600
TIMEOUT     = 0.1

# Base de données JSON
DB_FILE = "alarmes.json"

# Interface
WINDOW_TITLE    = "Moniteur Capteur PIR - Arduino Due"
WINDOW_GEOMETRY = "400x300"
