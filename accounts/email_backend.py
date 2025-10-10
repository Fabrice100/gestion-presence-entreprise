"""
Backend email personnalisé pour affichage console amélioré.

Ce backend affiche les emails dans le terminal avec un format
très visible et professionnel pour les démonstrations.
"""

from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend
import sys


class EnhancedConsoleEmailBackend(ConsoleEmailBackend):
    """
    Backend email qui affiche les emails dans le terminal
    avec un format amélioré et très visible.
    """
    
    def write_message(self, message):
        """Affiche le message avec un format amélioré."""
        msg_data = message.message()
        
        # Séparateur visible
        separator = "=" * 80
        
        # En-tête coloré (si le terminal supporte les couleurs)
        header = f"\n{separator}\n"
        header += "📧 NOUVEL EMAIL ENVOYÉ\n"
        header += f"{separator}\n"
        
        # Informations principales
        header += f"De      : {msg_data.get('From', 'N/A')}\n"
        header += f"À       : {msg_data.get('To', 'N/A')}\n"
        header += f"Sujet   : {msg_data.get('Subject', 'N/A')}\n"
        header += f"{separator}\n\n"
        
        # Contenu
        content = ""
        if message.body:
            content += "CONTENU (Texte):\n"
            content += "-" * 80 + "\n"
            content += message.body
            content += "\n" + "-" * 80 + "\n"
        
        # Pied de page
        footer = f"\n{separator}\n"
        footer += "✅ Email envoyé avec succès (mode console)\n"
        footer += f"{separator}\n\n"
        
        # Écrire dans le terminal
        msg_string = header + content + footer
        
        # Utiliser stderr pour que ce soit visible même avec du buffering
        stream = getattr(self, 'stream', sys.stdout)
        stream.write(msg_string)
        
        if hasattr(stream, 'flush'):
            stream.flush()

