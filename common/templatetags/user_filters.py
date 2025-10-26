from django import template

register = template.Library()

@register.filter
def has_group(user, group_name):
    """
    Vérifie si l'utilisateur appartient à un groupe spécifique.
    """
    return user.groups.filter(name=group_name).exists()

@register.filter
def has_role(user, roles):
    """
    Vérifie si l'utilisateur a un rôle spécifique.
    """
    if not hasattr(user, 'employeeprofile'):
        return False
    
    user_role = user.employeeprofile.role
    if isinstance(roles, str):
        roles = [roles]
    
    return user_role in roles

