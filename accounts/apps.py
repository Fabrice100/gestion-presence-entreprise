from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Comptes Utilisateurs'
    
    def ready(self):
        """
        Méthode appelée au démarrage de l'application.
        Enregistre les signals pour l'envoi automatique d'emails.
        """
        import accounts.signals  # Import pour enregistrer les signals
