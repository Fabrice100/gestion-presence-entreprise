from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def format_days(value):
    """
    Formate un nombre de jours en supprimant les décimales inutiles.
    Exemple: 3.00 -> 3, 2.50 -> 2.5
    """
    if value is None:
        return "0"
    
    try:
        # Convertir en Decimal pour une manipulation précise
        if isinstance(value, str):
            value = Decimal(value)
        elif isinstance(value, (int, float)):
            value = Decimal(str(value))
        
        # Si c'est un nombre entier, retourner sans décimales
        if value == value.to_integral():
            return str(int(value))
        else:
            # Sinon, retourner avec les décimales nécessaires
            return str(value.normalize())
    except (ValueError, TypeError, AttributeError):
        return str(value)

@register.filter
def format_balance(value):
    """
    Formate un solde de congés de manière lisible.
    """
    if value is None:
        return "0 jour"
    
    try:
        days = format_days(value)
        if days == "1":
            return "1 jour"
        else:
            return f"{days} jours"
    except:
        return f"{value} jours"


