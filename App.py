import serial
import threading
import customtkinter as ctk

# Configuration de l'apparence
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class PirApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Moniteur Capteur PIR - Arduino Due")
        self.geometry("400x300")

        # Label de statut
        self.label_status = ctk.CTkLabel(self, text="Système en attente...", font=("Roboto", 20))
        self.label_status.pack(pady=40)

        # Indicateur visuel (Cercle ou Carré)
        self.indicator = ctk.CTkFrame(self, width=100, height=100, corner_radius=50, fg_color="gray")
        self.indicator.pack(pady=20)

        # Configuration de la liaison Série (À AJUSTER : "COM3" ou "/dev/ttyACM0")
        try:
            self.ser = serial.Serial('COM3', 9600, timeout=0.1) 
            self.running = True
            # Lancer la lecture dans un thread séparé pour ne pas figer l'interface
            self.thread = threading.Thread(target=self.read_serial, daemon=True)
            self.thread.start()
        except Exception as e:
            self.label_status.configure(text="Erreur: Arduino non trouvé", text_color="red")
            print(f"Erreur de port : {e}")

    def read_serial(self):
        while self.running:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8').strip()
                
                if line == "MOTION_DETECTED":
                    self.update_ui(True)
                elif line == "STILL":
                    self.update_ui(False)

    def update_ui(self, motion):
        if motion:
            self.label_status.configure(text="MOUVEMENT DÉTECTÉ !", text_color="#FF5555")
            self.indicator.configure(fg_color="#FF5555")
        else:
            self.label_status.configure(text="Pas de mouvement", text_color="white")
            self.indicator.configure(fg_color="gray")

if __name__ == "__main__":
    app = PirApp()
    app.mainloop()