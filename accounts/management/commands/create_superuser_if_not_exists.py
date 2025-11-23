"""
Commande Django pour créer un superutilisateur s'il n'existe pas déjà.

Cette commande est utilisée lors du déploiement pour créer automatiquement
un compte administrateur sans interaction.

Usage:
    python manage.py create_superuser_if_not_exists
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os


class Command(BaseCommand):
    help = 'Crée un superutilisateur par défaut s\'il n\'existe pas déjà'

    def handle(self, *args, **options):
        username = os.environ.get('ADMIN_USERNAME', 'admin')
        email = os.environ.get('ADMIN_EMAIL', 'admin@presencepro.com')
        password = os.environ.get('ADMIN_PASSWORD', 'admin123')

        # Vérifier si un superutilisateur existe déjà
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.SUCCESS(f'✓ Un superutilisateur existe déjà. Aucune action nécessaire.')
            )
            return

        # Vérifier si l'utilisateur existe déjà (même sans être superuser)
        if User.objects.filter(username=username).exists():
            # Mettre à jour l'utilisateur existant pour en faire un superuser
            user = User.objects.get(username=username)
            user.is_superuser = True
            user.is_staff = True
            user.set_password(password)
            user.email = email
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Utilisateur "{username}" mis à jour en superutilisateur.'
                )
            )
        else:
            # Créer un nouveau superutilisateur
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Superutilisateur créé avec succès:\n'
                    f'  Username: {username}\n'
                    f'  Email: {email}\n'
                    f'  Password: {password}\n'
                    f'  ⚠️  IMPORTANT: Changez le mot de passe après la première connexion!'
                )
            )

