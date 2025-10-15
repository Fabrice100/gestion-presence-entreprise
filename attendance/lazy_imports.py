"""
Imports tardifs pour éviter les imports circulaires.

Ce module contient les imports qui sont chargés à la demande
pour éviter les problèmes d'imports circulaires.
"""

def get_overtime_models():
    """Import tardif des modèles d'heures supplémentaires."""
    from .overtime_models import OvertimeConfiguration, OvertimeRecord
    return OvertimeConfiguration, OvertimeRecord


def get_admin_models():
    """Import tardif des modèles d'administration."""
    from .admin_models import CompanySettings
    return CompanySettings


def get_leave_models():
    """Import tardif des modèles de congés."""
    from leave.models import Holiday
    return Holiday
