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
        Génère un ID employé unique au format EMPXXX avec numéro aléatoire.
        Format unique pour tous les rôles avec sécurité renforcée (non successif).
        
        Args:
            role (str): Le rôle de l'employé (non utilisé, gardé pour compatibilité)
        
        Returns:
            str: ID employé unique (ex: EMP472, EMP819, EMP156)
        """
        # Format unique pour tous : EMPXXX avec XXX aléatoire
        prefix = 'EMP'
        
        # Récupérer tous les IDs existants
        existing_ids = set(
            EmployeeProfile.objects.filter(
                employee_id__startswith=prefix
            ).values_list('employee_id', flat=True)
        )
        
        # Générer un ID aléatoire unique
        max_attempts = 100  # Éviter boucle infinie
        for _ in range(max_attempts):
            # Générer un nombre aléatoire entre 100 et 999
            random_number = random.randint(100, 999)
            new_id = f'{prefix}{random_number}'
            
            # Vérifier que l'ID n'existe pas déjà
            if new_id not in existing_ids:
                return new_id
        
        # Si tous les IDs 100-999 sont pris, utiliser 001-099
        for _ in range(max_attempts):
            random_number = random.randint(1, 99)
            new_id = f'{prefix}{random_number:03d}'
            
            if new_id not in existing_ids:
                return new_id
        
        # En dernier recours (très improbable), lever une exception
        raise ValueError('Impossible de générer un ID unique. Base de données pleine.')
    
    @staticmethod
    def generate_random_password(length=8):
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
        Utilise le NotificationService centralisé.
        
        Args:
            user (User): L'utilisateur Django
            employee_id (str): L'ID employé généré
            temporary_password (str): Le mot de passe temporaire
            
        Returns:
            bool: True si l'email a été envoyé, False sinon
        """
        from .notification_service import NotificationService
        return NotificationService.send_welcome_email(user, employee_id, temporary_password)
    
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
        
        Transaction atomique pour garantir la cohérence des données.
        Si une erreur survient, toutes les modifications sont annulées.
        
        Args:
            user_data (dict): Données de l'utilisateur (first_name, last_name, email)
            profile_data (dict): Données du profil (department, manager, role, phone)
            
        Returns:
            tuple: (user, employee_id, password) ou (None, None, None) en cas d'erreur
        """
        from django.db import transaction
        
        try:
            with transaction.atomic():
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
                profile.force_password_change = True  # Changement obligatoire à la première connexion
                profile.is_active = True
                profile.can_punch = True if profile.role in ['employee', 'manager'] else False
                profile.save()
                
                return user, employee_id, temporary_password
            
        except Exception as e:
            print(f'Erreur lors de la création de l\'employé: {str(e)}')
            return None, None, None

