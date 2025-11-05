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

@register.filter
def format_hours(value):
    """
    Formate les heures en format lisible "XhYYmin" au lieu de "X.YYh".
    
    Exemples:
        4.5 -> "4h30min"
        8.0 -> "8h"
        7.25 -> "7h15min"
        0.5 -> "30min"
    """
    if value is None:
        return "-"
    
    try:
        # Gérer les chaînes comme "4.50h"
        if isinstance(value, str):
            # Retirer "h" à la fin si présent
            value_str = value.replace('h', '').strip()
            hours_decimal = Decimal(value_str)
        elif isinstance(value, (int, float)):
            hours_decimal = Decimal(str(value))
        elif isinstance(value, Decimal):
            hours_decimal = value
        else:
            return str(value)
        
        # Extraire heures et minutes
        hours = int(hours_decimal)
        minutes_decimal = (hours_decimal - Decimal(hours)) * Decimal('60')
        minutes = int(minutes_decimal.quantize(Decimal('1'), rounding='ROUND_HALF_UP'))
        
        # Ajuster si minutes >= 60
        if minutes >= 60:
            hours += 1
            minutes = 0
        
        # Formatage
        if hours == 0 and minutes == 0:
            return "0h"
        elif hours == 0:
            return f"{minutes}min"
        elif minutes == 0:
            return f"{hours}h"
        else:
            return f"{hours}h{minutes}min"
    except (ValueError, TypeError, AttributeError):
        return str(value)





