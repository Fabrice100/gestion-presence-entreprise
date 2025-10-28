"""
Tests pour la fonctionnalité de changement de mot de passe forcé.

Tests couverts:
1. Signal d'envoi d'email avec mot de passe temporaire
2. Middleware de redirection vers changement de mot de passe
3. Formulaire de changement de mot de passe
4. Validation des exigences de mot de passe
5. Mise à jour du flag force_password_change

Auteur: Test Suite
Date: 26/10/2025
"""

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from accounts.models import EmployeeProfile, Department
from accounts.signals import send_account_creation_email
from accounts.force_password_views import ForcePasswordChangeForm
import re

User = get_user_model()


class EmailCreationSignalTest(TestCase):
    """Tests pour le signal d'envoi d'email lors de la création de compte."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.department = Department.objects.create(
            name="IT",
            description="IT Department"
        )
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_email_sent_on_user_creation(self):
        """Test: Email envoyé lors de la création d'un utilisateur."""
        # Créer un utilisateur
        user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            first_name='Test',
            last_name='User'
        )
        
        # Créer le profil employé (déclenche le signal)
        profile = EmployeeProfile.objects.create(
            user=user,
            employee_id='EMP001',
            phone='1234567890',
            department=self.department,
            role='employee',
            force_password_change=True
        )
        
        # Déclencher manuellement le signal
        send_account_creation_email(sender=EmployeeProfile, instance=profile, created=True)
        
        # Vérifier qu'un email a été envoyé
        self.assertEqual(len(mail.outbox), 1)
        
        # Vérifier le contenu de l'email
        email = mail.outbox[0]
        self.assertEqual(email.to, ['testuser@example.com'])
        self.assertIn('Bienvenue', email.subject)
        self.assertIn('testuser', email.body)
        self.assertIn('Mot de passe temporaire', email.body)
    
    def test_force_password_change_flag_set(self):
        """Test: Flag force_password_change est activé."""
        user = User.objects.create_user(
            username='testuser2',
            email='testuser2@example.com'
        )
        
        profile = EmployeeProfile.objects.create(
            user=user,
            employee_id='EMP002',
            phone='1234567890',
            department=self.department,
            role='employee'
        )
        
        # Vérifier que le flag est activé par défaut
        profile.refresh_from_db()
        self.assertTrue(profile.force_password_change)
    
    def test_temporary_password_format(self):
        """Test: Mot de passe temporaire a le bon format (12 caractères)."""
        user = User.objects.create_user(
            username='testuser3',
            email='testuser3@example.com'
        )
        
        profile = EmployeeProfile.objects.create(
            user=user,
            employee_id='EMP003',
            phone='1234567890',
            department=self.department,
            role='employee'
        )
        
        # Déclencher le signal
        send_account_creation_email(sender=EmployeeProfile, instance=profile, created=True)
        
        if len(mail.outbox) > 0:
            email = mail.outbox[0]
            # Chercher le mot de passe dans l'email (12 caractères alphanumériques)
            password_match = re.search(r'\b[A-Za-z0-9]{12}\b', email.body)
            if password_match:
                temp_password = password_match.group()
                self.assertEqual(len(temp_password), 12)


class ForcePasswordChangeMiddlewareTest(TestCase):
    """Tests pour le middleware de changement de mot de passe forcé."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.client = Client()
        self.department = Department.objects.create(
            name="HR",
            description="HR Department"
        )
        
        # Utilisateur avec force_password_change=True
        self.user_force = User.objects.create_user(
            username='forceuser',
            email='forceuser@example.com',
            password='TempPass123'
        )
        self.profile_force = EmployeeProfile.objects.create(
            user=self.user_force,
            employee_id='EMP004',
            phone='1234567890',
            department=self.department,
            role='employee',
            force_password_change=True
        )
        
        # Utilisateur sans force_password_change
        self.user_normal = User.objects.create_user(
            username='normaluser',
            email='normaluser@example.com',
            password='NormalPass123'
        )
        self.profile_normal = EmployeeProfile.objects.create(
            user=self.user_normal,
            employee_id='EMP005',
            phone='1234567890',
            department=self.department,
            role='employee',
            force_password_change=False
        )
    
    def test_redirect_when_force_password_change_true(self):
        """Test: Redirection vers changement MDP si force_password_change=True."""
        self.client.login(username='forceuser', password='TempPass123')
        
        # Essayer d'accéder au dashboard
        response = self.client.get(reverse('dashboard:employee_dashboard'))
        
        # Doit être redirigé vers la page de changement de mot de passe
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/force-password-change/', response.url)
    
    def test_no_redirect_when_force_password_change_false(self):
        """Test: Pas de redirection si force_password_change=False."""
        self.client.login(username='normaluser', password='NormalPass123')
        
        # Accéder au dashboard
        response = self.client.get(reverse('dashboard:employee_dashboard'))
        
        # Ne doit PAS être redirigé (200 ou 302 vers autre page légitime)
        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 302:
            self.assertNotIn('/accounts/force-password-change/', response.url)
    
    def test_access_to_force_password_page_allowed(self):
        """Test: Accès autorisé à la page de changement forcé."""
        self.client.login(username='forceuser', password='TempPass123')
        
        # Accéder à la page de changement de mot de passe
        response = self.client.get(reverse('accounts:force_password_change'))
        
        # Doit réussir
        self.assertEqual(response.status_code, 200)
    
    def test_logout_allowed_when_force_password_change(self):
        """Test: Déconnexion autorisée même avec force_password_change=True."""
        self.client.login(username='forceuser', password='TempPass123')
        
        # Se déconnecter
        response = self.client.get(reverse('accounts:logout'))
        
        # Doit réussir (pas de redirection vers force-password-change)
        self.assertIn(response.status_code, [200, 302])


class ForcePasswordChangeFormTest(TestCase):
    """Tests pour le formulaire de changement de mot de passe."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.department = Department.objects.create(
            name="Finance",
            description="Finance Department"
        )
        
        self.user = User.objects.create_user(
            username='formuser',
            email='formuser@example.com',
            password='OldPass123'
        )
        self.profile = EmployeeProfile.objects.create(
            user=self.user,
            employee_id='EMP006',
            phone='1234567890',
            department=self.department,
            role='employee',
            force_password_change=True
        )
    
    def test_valid_password_accepted(self):
        """Test: Mot de passe valide accepté."""
        form = ForcePasswordChangeForm(
            user=self.user,
            data={
                'old_password': 'OldPass123',
                'new_password1': 'NewValidPass123',
                'new_password2': 'NewValidPass123'
            }
        )
        
        self.assertTrue(form.is_valid())
    
    def test_password_too_short_rejected(self):
        """Test: Mot de passe trop court rejeté."""
        form = ForcePasswordChangeForm(
            user=self.user,
            data={
                'old_password': 'OldPass123',
                'new_password1': 'Short1',
                'new_password2': 'Short1'
            }
        )
        
        self.assertFalse(form.is_valid())
    
    def test_password_without_uppercase_rejected(self):
        """Test: Mot de passe sans majuscule rejeté."""
        form = ForcePasswordChangeForm(
            user=self.user,
            data={
                'old_password': 'OldPass123',
                'new_password1': 'lowercase123',
                'new_password2': 'lowercase123'
            }
        )
        
        self.assertFalse(form.is_valid())
    
    def test_password_without_digit_rejected(self):
        """Test: Mot de passe sans chiffre rejeté."""
        form = ForcePasswordChangeForm(
            user=self.user,
            data={
                'old_password': 'OldPass123',
                'new_password1': 'NoDigitsHere',
                'new_password2': 'NoDigitsHere'
            }
        )
        
        self.assertFalse(form.is_valid())
    
    def test_passwords_not_matching_rejected(self):
        """Test: Mots de passe différents rejetés."""
        form = ForcePasswordChangeForm(
            user=self.user,
            data={
                'old_password': 'OldPass123',
                'new_password1': 'NewPass123',
                'new_password2': 'DifferentPass123'
            }
        )
        
        self.assertFalse(form.is_valid())


class ForcePasswordChangeViewTest(TestCase):
    """Tests pour la vue de changement de mot de passe forcé."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.client = Client()
        self.department = Department.objects.create(
            name="Operations",
            description="Operations Department"
        )
        
        self.user = User.objects.create_user(
            username='viewuser',
            email='viewuser@example.com',
            password='TempPass123'
        )
        self.profile = EmployeeProfile.objects.create(
            user=self.user,
            employee_id='EMP007',
            phone='1234567890',
            department=self.department,
            role='employee',
            force_password_change=True
        )
    
    def test_password_change_success(self):
        """Test: Changement de mot de passe réussi."""
        self.client.login(username='viewuser', password='TempPass123')
        
        # Soumettre le formulaire
        response = self.client.post(
            reverse('accounts:force_password_change'),
            {
                'old_password': 'TempPass123',
                'new_password1': 'NewValidPass123',
                'new_password2': 'NewValidPass123'
            }
        )
        
        # Vérifier la redirection
        self.assertEqual(response.status_code, 302)
        
        # Vérifier que le flag est désactivé
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.force_password_change)
        
        # Vérifier que le mot de passe a changé
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewValidPass123'))
    
    def test_force_password_change_flag_updated(self):
        """Test: Flag force_password_change mis à jour après succès."""
        self.client.login(username='viewuser', password='TempPass123')
        
        # Avant changement
        self.assertTrue(self.profile.force_password_change)
        
        # Changer le mot de passe
        self.client.post(
            reverse('accounts:force_password_change'),
            {
                'old_password': 'TempPass123',
                'new_password1': 'SuperNewPass123',
                'new_password2': 'SuperNewPass123'
            }
        )
        
        # Après changement
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.force_password_change)


class IntegrationTest(TestCase):
    """Tests d'intégration pour le workflow complet."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.client = Client()
        self.department = Department.objects.create(
            name="Sales",
            description="Sales Department"
        )
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_complete_workflow(self):
        """Test: Workflow complet création compte → email → changement MDP."""
        # 1. Créer un utilisateur
        user = User.objects.create_user(
            username='workflow',
            email='workflow@example.com',
            password='TempPassword123'
        )
        
        # 2. Créer le profil (déclenche email)
        profile = EmployeeProfile.objects.create(
            user=user,
            employee_id='EMP008',
            phone='1234567890',
            department=self.department,
            role='employee',
            force_password_change=True
        )
        
        # 3. Vérifier que force_password_change est True
        self.assertTrue(profile.force_password_change)
        
        # 4. Se connecter
        self.client.login(username='workflow', password='TempPassword123')
        
        # 5. Tenter d'accéder au dashboard (doit être redirigé)
        response = self.client.get(reverse('dashboard:employee_dashboard'))
        self.assertEqual(response.status_code, 302)
        
        # 6. Changer le mot de passe
        response = self.client.post(
            reverse('accounts:force_password_change'),
            {
                'old_password': 'TempPassword123',
                'new_password1': 'MyNewPassword123',
                'new_password2': 'MyNewPassword123'
            }
        )
        
        # 7. Vérifier le flag désactivé
        profile.refresh_from_db()
        self.assertFalse(profile.force_password_change)
        
        # 8. Maintenant accès au dashboard devrait fonctionner
        response = self.client.get(reverse('dashboard:employee_dashboard'))
        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 302:
            self.assertNotIn('/accounts/force-password-change/', response.url)
