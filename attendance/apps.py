from django.apps import AppConfig


class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'
    verbose_name = 'Gestion de Présence'
    
    def ready(self):
        """
        Méthode appelée quand l'application est prête.
        Utilisée pour enregistrer les signaux.
        """
        import attendance.overtime_signals