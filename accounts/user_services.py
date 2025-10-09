"""
Services pour la gestion des utilisateurs.

Ce module contient les services pour :
- Génération automatique d'ID employé
- Génération de mot de passe aléatoire sécurisé
- Envoi d'email de bienvenue avec credentials

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

import random
import string
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import EmployeeProfile


class UserService:
    """
    Service pour la gestion des utilisateurs et employés.
    """
    
    @staticmethod
    def generate_employee_id(role='employee'):
        """
        Génère un ID employé unique au format EMP001, EMP002, etc.
        Format unique pour tous les rôles (conforme aux standards internationaux).
        
        Args:
            role (str): Le rôle de l'employé (non utilisé, gardé pour compatibilité)
        
        Returns:
            str: ID employé unique (ex: EMP001, EMP002, EMP003)
        """
        # Format unique pour tous : EMP001, EMP002, etc.
        prefix = 'EMP'
        
        # Récupérer le dernier ID
        last_profile = EmployeeProfile.objects.filter(
            employee_id__startswith=prefix
        ).order_by('-employee_id').first()
        
        if last_profile and last_profile.employee_id:
            # Extraire le numéro et incrémenter
            try:
                last_number = int(last_profile.employee_id.replace(prefix, ''))
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1
        
        # Format: EMP001, EMP002, EMP003, etc.
        return f'{prefix}{new_number:03d}'
    
    @staticmethod
    def generate_random_password(length=12):
        """
        Génère un mot de passe aléatoire sécurisé.
        
        Le mot de passe contient :
        - Au moins une majuscule
        - Au moins une minuscule
        - Au moins un chiffre
        - Au moins un caractère spécial
        
        Args:
            length (int): Longueur du mot de passe (défaut: 12)
            
        Returns:
            str: Mot de passe aléatoire
        """
        # Caractères à utiliser
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = '!@#$%*'
        
        # Assurer au moins un de chaque type
        password = [
            random.choice(uppercase),
            random.choice(lowercase),
            random.choice(digits),
            random.choice(special),
        ]
        
        # Compléter avec des caractères aléatoires
        all_chars = lowercase + uppercase + digits + special
        password.extend(random.choice(all_chars) for _ in range(length - 4))
        
        # Mélanger les caractères
        random.shuffle(password)
        
        return ''.join(password)
    
    @staticmethod
    def send_welcome_email(user, employee_id, temporary_password):
        """
        Envoie un email de bienvenue avec les credentials à l'employé.
        
        Args:
            user (User): L'utilisateur Django
            employee_id (str): L'ID employé généré
            temporary_password (str): Le mot de passe temporaire
            
        Returns:
            bool: True si l'email a été envoyé, False sinon
        """
        try:
            subject = 'Bienvenue - Vos accès au système de gestion de présence'
            
            # Contexte pour le template
            context = {
                'user': user,
                'employee_id': employee_id,
                'username': user.username,
                'temporary_password': temporary_password,
                'login_url': f'{settings.SITE_URL}/accounts/login/' if hasattr(settings, 'SITE_URL') else 'http://localhost:8000/accounts/login/',
            }
            
            # Générer le contenu HTML
            html_message = render_to_string('accounts/welcome_email.html', context)
            plain_message = strip_tags(html_message)
            
            # Envoyer l'email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            print(f'Erreur lors de l\'envoi de l\'email: {str(e)}')
            return False
    
    @staticmethod
    def generate_username_from_email(email):
        """Génère un username à partir de l'email (partie avant @)."""
        base_username = email.split('@')[0].lower()
        username = base_username
        counter = 1
        
        # Si le username existe déjà, ajouter un numéro
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        return username
    
    @staticmethod
    def create_employee_with_credentials(user_data, profile_data):
        """
        Crée un employé avec génération automatique des credentials.
        
        Args:
            user_data (dict): Données de l'utilisateur (first_name, last_name, email)
            profile_data (dict): Données du profil (department, manager, role, phone)
            
        Returns:
            tuple: (user, employee_id, password) ou (None, None, None) en cas d'erreur
        """
        try:
            # Récupérer le rôle
            role = profile_data.get('role', 'employee')
            
            # Générer les credentials
            employee_id = UserService.generate_employee_id(role)
            temporary_password = UserService.generate_random_password()
            
            # Générer le username automatiquement à partir de l'email
            username = UserService.generate_username_from_email(user_data['email'])
            
            # Créer l'utilisateur
            user = User.objects.create_user(
                username=username,
                email=user_data['email'],
                password=temporary_password,
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
            )
            
            # Mettre à jour le profil employé (créé automatiquement par le signal)
            profile = user.employee_profile
            profile.employee_id = employee_id
            profile.department = profile_data.get('department')
            profile.manager = profile_data.get('manager')
            profile.role = profile_data.get('role', 'employee')
            profile.phone = profile_data.get('phone', '')
            profile.force_password_change = True  # Changement obligatoire à la première connexion
            profile.is_active = True
            profile.can_punch = True if profile.role in ['employee', 'manager'] else False
            profile.save()
            
            return user, employee_id, temporary_password
            
        except Exception as e:
            print(f'Erreur lors de la création de l\'employé: {str(e)}')
            return None, None, None

