from django.apps import AppConfig


class LeaveConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'leave'
    verbose_name = 'Gestion des Congés'
    
    def ready(self):
        """
        Importation des signaux lors du démarrage de l'application.
        """
        import leave.signals