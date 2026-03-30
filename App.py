import customtkinter as ctk
from datetime import datetime

from config import WINDOW_TITLE, WINDOW_GEOMETRY
from serial_reader import SerialReader

# ─── Palette ──────────────────────────────────────────────────────────────────
COLOR = {
    "bg":       "#0d0f14",
    "surface":  "#151820",
    "border":   "#252a3a",
    "green":    "#2ed573",
    "orange":   "#ff8c42",
    "red":      "#ff4757",
    "text":     "#e8eaf0",
    "muted":    "#6b7280",
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class PirApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(WINDOW_TITLE)
        self.geometry("480x600")
        self.resizable(False, False)
        self.configure(fg_color=COLOR["bg"])

        self._detection_count = 0
        self._alarm_count     = 0
        self._log_entries     = []

        self._build_ui()

        self.reader = SerialReader(on_event=self.update_ui)
        try:
            self.reader.start()
            self._set_connected(True)
        except Exception as e:
            self._set_connected(False)
            print(f"[APP] Erreur de port : {e}")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Construction de l'interface ───────────────────────────────────────────

    def _build_ui(self):
        # Barre de titre
        header = ctk.CTkFrame(self, fg_color=COLOR["bg"], corner_radius=0, height=48)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="PIR MONITOR",
            font=("Courier New", 13, "bold"),
            text_color=COLOR["muted"],
        ).pack(side="left", padx=20)

        self.lbl_badge = ctk.CTkLabel(
            header, text="  EN VEILLE  ",
            font=("Courier New", 10),
            text_color=COLOR["green"],
            fg_color="#0d2214", corner_radius=6,
        )
        self.lbl_badge.pack(side="right", padx=20)

        ctk.CTkFrame(self, height=1, fg_color=COLOR["border"]).pack(fill="x")

        body = ctk.CTkFrame(self, fg_color=COLOR["bg"], corner_radius=0)
        body.pack(fill="both", expand=True, padx=24, pady=20)

        # ── Orbe centrale ─────────────────────────────────────────────────────
        orb_container = ctk.CTkFrame(body, fg_color=COLOR["bg"], height=160)
        orb_container.pack(fill="x", pady=(0, 24))
        orb_container.pack_propagate(False)

        self.orb = ctk.CTkFrame(
            orb_container, width=90, height=90, corner_radius=45,
            fg_color=COLOR["surface"], border_width=1, border_color=COLOR["green"],
        )
        self.orb.place(relx=0.5, rely=0.42, anchor="center")

        self.orb_dot = ctk.CTkFrame(
            self.orb, width=22, height=22, corner_radius=11, fg_color=COLOR["green"],
        )
        self.orb_dot.place(relx=0.5, rely=0.5, anchor="center")

        self.lbl_status = ctk.CTkLabel(
            orb_container, text="Pas de mouvement",
            font=("Helvetica Neue", 19, "bold"),
            text_color=COLOR["green"],
        )
        self.lbl_status.place(relx=0.5, rely=0.78, anchor="center")

        self.lbl_sub = ctk.CTkLabel(
            orb_container, text="SYSTÈME OPÉRATIONNEL",
            font=("Courier New", 10), text_color=COLOR["muted"],
        )
        self.lbl_sub.place(relx=0.5, rely=0.95, anchor="center")

        # ── Séparateur ────────────────────────────────────────────────────────
        ctk.CTkFrame(body, height=1, fg_color=COLOR["border"]).pack(fill="x", pady=(0, 16))

        # ── Compteurs ─────────────────────────────────────────────────────────
        counters = ctk.CTkFrame(body, fg_color=COLOR["bg"])
        counters.pack(fill="x", pady=(0, 14))
        counters.columnconfigure((0, 1), weight=1, uniform="col")

        self.card_detect = self._stat_card(counters, "Détections", "0", COLOR["orange"], 0)
        self.card_alarm  = self._stat_card(counters, "Alarmes",    "0", COLOR["red"],    1)

        # ── Journal ───────────────────────────────────────────────────────────
        log_frame = ctk.CTkFrame(
            body, fg_color=COLOR["surface"], corner_radius=10,
            border_width=1, border_color=COLOR["border"],
        )
        log_frame.pack(fill="both", expand=True)

        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.pack(fill="x", padx=14, pady=(12, 6))

        ctk.CTkLabel(
            log_header, text="JOURNAL",
            font=("Courier New", 10), text_color=COLOR["muted"],
        ).pack(side="left")

        self.lbl_log_count = ctk.CTkLabel(
            log_header, text="0 entrée",
            font=("Courier New", 10), text_color=COLOR["muted"],
        )
        self.lbl_log_count.pack(side="right")

        ctk.CTkFrame(log_frame, height=1, fg_color=COLOR["border"]).pack(fill="x")

        self.log_scroll = ctk.CTkScrollableFrame(
            log_frame, fg_color="transparent",
            scrollbar_button_color=COLOR["border"],
        )
        self.log_scroll.pack(fill="both", expand=True, padx=8, pady=8)

        # ── Pied de page ──────────────────────────────────────────────────────
        footer = ctk.CTkFrame(body, fg_color="transparent", height=32)
        footer.pack(fill="x", pady=(12, 0))
        footer.pack_propagate(False)

        self.lbl_port = ctk.CTkLabel(
            footer, text="PORT: non connecté",
            font=("Courier New", 10), text_color=COLOR["muted"],
        )
        self.lbl_port.pack(side="left")

        self.lbl_live = ctk.CTkLabel(
            footer, text="● HORS LIGNE",
            font=("Courier New", 10), text_color=COLOR["red"],
        )
        self.lbl_live.pack(side="right")

    def _stat_card(self, parent, label, value, color, col):
        frame = ctk.CTkFrame(
            parent, fg_color=COLOR["bg"], corner_radius=10,
            border_width=1, border_color=COLOR["border"],
        )
        frame.grid(row=0, column=col,
                   padx=(0, 6) if col == 0 else (6, 0), sticky="ew")

        ctk.CTkLabel(
            frame, text=label.upper(),
            font=("Courier New", 10), text_color=COLOR["muted"],
        ).pack(pady=(12, 2))

        val_lbl = ctk.CTkLabel(
            frame, text=value,
            font=("Helvetica Neue", 28, "bold"), text_color=color,
        )
        val_lbl.pack(pady=(0, 12))
        return val_lbl

    # ── Connexion ─────────────────────────────────────────────────────────────

    def _set_connected(self, ok: bool):
        from config import SERIAL_PORT, BAUD_RATE
        if ok:
            self.lbl_port.configure(text=f"PORT: {SERIAL_PORT} · {BAUD_RATE} baud")
            self.lbl_live.configure(text="● LIVE", text_color=COLOR["green"])
        else:
            self.lbl_port.configure(text="PORT: Arduino non trouvé")
            self.lbl_live.configure(text="● HORS LIGNE", text_color=COLOR["red"])
            self.lbl_badge.configure(
                text="  ERREUR  ", text_color=COLOR["red"], fg_color="#2a0d0e")
            self.lbl_status.configure(
                text="Arduino non détecté", text_color=COLOR["muted"])

    # ── Mise à jour UI ────────────────────────────────────────────────────────

    def update_ui(self, motion: int) -> None:
        now = datetime.now().strftime("%H:%M:%S")

        if motion == 1:
            self._detection_count += 1
            self.card_detect.configure(text=str(self._detection_count))
            self._push_log(now, "MOUVEMENT DÉTECTÉ", COLOR["orange"])
            self._set_state(
                "MOUVEMENT DÉTECTÉ !", "ACTIVITÉ DÉTECTÉE",
                COLOR["orange"], "#2a1600",
                "  MOUVEMENT  ", "#2a1600",
            )
        elif motion == 2:
            self._alarm_count += 1
            self.card_alarm.configure(text=str(self._alarm_count))
            self._push_log(now, "ALARME — PRÉSENCE", COLOR["red"])
            self._set_state(
                "ALARME !", "PRÉSENCE CONFIRMÉE",
                COLOR["red"], "#2a0d0e",
                "  ALARME  ", "#2a0d0e",
            )
        else:
            self._set_state(
                "Pas de mouvement", "SYSTÈME OPÉRATIONNEL",
                COLOR["green"], COLOR["surface"],
                "  EN VEILLE  ", "#0d2214",
            )

    def _set_state(self, main, sub, color, orb_bg, badge_text, badge_bg):
        self.lbl_status.configure(text=main, text_color=color)
        self.lbl_sub.configure(text=sub)
        self.orb.configure(fg_color=orb_bg, border_color=color)
        self.orb_dot.configure(fg_color=color)
        self.lbl_badge.configure(
            text=badge_text, text_color=color, fg_color=badge_bg)

    def _push_log(self, time_str: str, message: str, color: str):
        row = ctk.CTkFrame(self.log_scroll, fg_color="transparent", height=32)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        ctk.CTkLabel(
            row, text=time_str,
            font=("Courier New", 10), text_color=COLOR["muted"], width=52,
        ).pack(side="left", padx=(4, 8))

        ctk.CTkFrame(
            row, width=7, height=7, corner_radius=4, fg_color=color,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            row, text=message,
            font=("Courier New", 11), text_color=color,
        ).pack(side="left")

        self._log_entries.append(message)
        n = len(self._log_entries)
        self.lbl_log_count.configure(text=f"{n} entrée{'s' if n > 1 else ''}")

    # ── Fermeture ─────────────────────────────────────────────────────────────

    def _on_close(self):
        self.reader.stop()
        self.destroy()