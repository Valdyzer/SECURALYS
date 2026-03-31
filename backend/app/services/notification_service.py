"""
SECURALYS - Service de Notifications
Gère les alertes automatiques en fin de journée pour les outils non rendus.

Fonctionnalités :
- Scheduler configurable (heure de fin de journée)
- Email au responsable avec liste des outils manquants
- Logs des notifications envoyées
"""
import smtplib
import threading
import time
import logging
from datetime import datetime, time as dtime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Callable
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NOTIFICATIONS")


@dataclass
class NotificationConfig:
    """Configuration du service de notifications."""
    # Email SMTP
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    
    # Destinataires
    email_responsable: str = ""
    
    # Horaires
    heure_fin_journee: dtime = dtime(18, 0)  # 18h00 par défaut
    
    # Options
    actif: bool = True


class NotificationService:
    """
    Service de notifications automatiques.
    
    Vérifie en fin de journée si des outils sont encore empruntés
    et envoie un email récapitulatif au responsable.
    """
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or NotificationConfig()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_check: Optional[datetime] = None
        self.on_get_emprunts: Optional[Callable[[], list]] = None
    
    def set_emprunts_callback(self, callback: Callable[[], list]) -> None:
        """Définit la fonction pour récupérer les emprunts en cours."""
        self.on_get_emprunts = callback
    
    def start(self) -> None:
        """Démarre le scheduler de vérification."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
        logger.info(f"Service de notifications démarré (vérification à {self.config.heure_fin_journee})")
    
    def stop(self) -> None:
        """Arrête le scheduler."""
        self.running = False
        logger.info("Service de notifications arrêté")
    
    def _scheduler_loop(self) -> None:
        """Boucle principale du scheduler."""
        while self.running:
            now = datetime.now()
            
            # Vérifier si c'est l'heure de fin de journée
            if self._is_check_time(now):
                self._check_and_notify()
                self.last_check = now
            
            # Attendre 1 minute avant la prochaine vérification
            time.sleep(60)
    
    def _is_check_time(self, now: datetime) -> bool:
        """Vérifie si c'est le moment de faire la vérification quotidienne."""
        if not self.config.actif:
            return False
        
        # Vérifier l'heure
        current_time = now.time()
        target_time = self.config.heure_fin_journee
        
        # Tolérance de 1 minute
        if (current_time.hour == target_time.hour and 
            current_time.minute == target_time.minute):
            
            # Éviter de vérifier plusieurs fois dans la même minute
            if self.last_check and self.last_check.date() == now.date():
                return False
            
            return True
        
        return False
    
    def _check_and_notify(self) -> None:
        """Vérifie les emprunts et envoie les notifications si nécessaire."""
        logger.info("Vérification des outils non rendus...")
        
        if not self.on_get_emprunts:
            logger.warning("Pas de callback pour récupérer les emprunts")
            return
        
        emprunts = self.on_get_emprunts()
        
        if not emprunts:
            logger.info("Tous les outils ont été rendus ✓")
            return
        
        logger.warning(f"{len(emprunts)} outil(s) non rendu(s) !")
        
        # Envoyer l'email
        if self.config.email_responsable and self.config.smtp_user:
            self._send_email_alert(emprunts)
        else:
            logger.warning("Email non configuré - notification non envoyée")
            # Afficher dans les logs à la place
            self._log_alert(emprunts)
    
    def _send_email_alert(self, emprunts: list) -> None:
        """Envoie un email d'alerte au responsable."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"⚠️ SECURALYS - {len(emprunts)} outil(s) non rendu(s)"
            msg['From'] = self.config.smtp_user
            msg['To'] = self.config.email_responsable
            
            # Corps du message en texte brut
            text_content = self._format_alert_text(emprunts)
            
            # Corps du message en HTML
            html_content = self._format_alert_html(emprunts)
            
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Connexion SMTP
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_user, self.config.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email envoyé à {self.config.email_responsable}")
            
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
    
    def _format_alert_text(self, emprunts: list) -> str:
        """Formate l'alerte en texte brut."""
        lines = [
            "ALERTE SECURALYS - Outils non rendus",
            "=" * 40,
            f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            f"Nombre d'outils: {len(emprunts)}",
            "",
            "Liste des outils manquants:",
            "-" * 40,
        ]
        
        for e in emprunts:
            lines.append(f"• {e.get('outil_nom', 'Outil inconnu')}")
            lines.append(f"  Emprunté par: {e.get('ouvrier_nom', 'Inconnu')}")
            lines.append(f"  Depuis: {e.get('heure_sortie', 'N/A')}")
            lines.append("")
        
        lines.append("-" * 40)
        lines.append("Merci de contacter les ouvriers concernés.")
        
        return "\n".join(lines)
    
    def _format_alert_html(self, emprunts: list) -> str:
        """Formate l'alerte en HTML."""
        rows = ""
        for e in emprunts:
            rows += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">{e.get('outil_nom', 'Outil inconnu')}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">{e.get('ouvrier_nom', 'Inconnu')}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">{e.get('heure_sortie', 'N/A')}</td>
            </tr>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background: #6B4423; color: white; padding: 20px; text-align: center;">
                    <h1 style="margin: 0;">⚠️ SECURALYS</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Alerte outils non rendus</p>
                </div>
                
                <div style="padding: 20px;">
                    <p style="color: #333;">
                        <strong>{len(emprunts)} outil(s)</strong> n'ont pas été rendus à la fin de la journée.
                    </p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <thead>
                            <tr style="background: #f8f8f8;">
                                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #6B4423;">Outil</th>
                                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #6B4423;">Ouvrier</th>
                                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #6B4423;">Sortie</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows}
                        </tbody>
                    </table>
                    
                    <p style="color: #666; font-size: 14px;">
                        Merci de contacter les ouvriers concernés pour récupérer le matériel.
                    </p>
                </div>
                
                <div style="background: #f8f8f8; padding: 15px; text-align: center; color: #888; font-size: 12px;">
                    Généré automatiquement par SECURALYS le {datetime.now().strftime('%d/%m/%Y à %H:%M')}
                </div>
            </div>
        </body>
        </html>
        """
    
    def _log_alert(self, emprunts: list) -> None:
        """Affiche l'alerte dans les logs (fallback si email non configuré)."""
        logger.warning("=" * 50)
        logger.warning("ALERTE: Outils non rendus en fin de journée")
        logger.warning("=" * 50)
        for e in emprunts:
            logger.warning(f"  • {e.get('outil_nom')} - {e.get('ouvrier_nom')}")
        logger.warning("=" * 50)
    
    def force_check(self) -> dict:
        """Force une vérification immédiate (pour tests)."""
        if not self.on_get_emprunts:
            return {"error": "Pas de callback configuré"}
        
        emprunts = self.on_get_emprunts()
        
        if not emprunts:
            return {"status": "ok", "message": "Tous les outils sont rendus"}
        
        # Log l'alerte
        self._log_alert(emprunts)
        
        # Envoyer email si configuré
        if self.config.email_responsable and self.config.smtp_user:
            self._send_email_alert(emprunts)
            return {"status": "alert", "count": len(emprunts), "email_sent": True}
        
        return {"status": "alert", "count": len(emprunts), "email_sent": False}
    
    def update_config(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        email_responsable: Optional[str] = None,
        heure_fin_journee: Optional[str] = None,
        actif: Optional[bool] = None
    ) -> None:
        """Met à jour la configuration."""
        if smtp_server:
            self.config.smtp_server = smtp_server
        if smtp_port:
            self.config.smtp_port = smtp_port
        if smtp_user:
            self.config.smtp_user = smtp_user
        if smtp_password:
            self.config.smtp_password = smtp_password
        if email_responsable:
            self.config.email_responsable = email_responsable
        if heure_fin_journee:
            h, m = map(int, heure_fin_journee.split(":"))
            self.config.heure_fin_journee = dtime(h, m)
        if actif is not None:
            self.config.actif = actif
        
        logger.info("Configuration mise à jour")


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Retourne l'instance singleton du service de notifications."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
