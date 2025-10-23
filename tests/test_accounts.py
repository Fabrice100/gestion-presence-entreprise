"""
Tests pour l'application accounts (authentification et profils).

Tests respectant les principes SOLID avec une séparation claire
des responsabilités pour chaque fonctionnalité.
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from accounts.models import EmployeeProfile, Department
# from accounts.forms import CustomAuthenticationForm  # Form n'existe plus
from accounts.auth_backend import EmployeeIDBackend
from common.mixins import EmployeeRequiredMixin
from tests.base import BaseTestCase, AuthenticatedTestCase, FormTestCase, ModelTestCase
from tests.factories import UserFactory, EmployeeProfileFactory, DepartmentFactory
import unittest


class EmployeeProfileModelTest(ModelTestCase):
    """Tests pour le modèle EmployeeProfile."""
    
    def test_employee_profile_creation(self):
        """Test de création d'un profil employé."""
        user = UserFactory()
        department = DepartmentFactory()
        
        profile = user.employee_profile
    def test_employee_profile_creation(self):
        """Test de création d'un profil employé."""
        department = DepartmentFactory()
        user = UserFactory()
        
        # Utiliser le profil auto-créé et le mettre à jour
        profile = user.employee_profile
        profile.employee_id = "EMP001"
        profile.department = department
        profile.save()
        
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.employee_id, "EMP001")
        # Note: can_approve_leave n'existe plus dans le modèle
        # self.assertFalse(profile.can_approve_leave)
    
    def test_employee_id_unique(self):
        """Test que l'ID employé est unique."""
        dept = DepartmentFactory()
        
        # Créer premier employé
        user1 = UserFactory()
        profile1 = user1.employee_profile
        profile1.employee_id = "EMP001"
        profile1.department = dept
        profile1.save()
        
        # Tenter de créer un second avec le même ID
        user2 = UserFactory()
        profile2 = user2.employee_profile
        profile2.employee_id = "EMP001"  # Même ID
        profile2.department = dept
        
        with self.assertRaises(Exception):
            profile2.save()  # Doit échouer
    
    def test_str_representation(self):
        """Test de la représentation string."""
        user = UserFactory()
        profile = user.employee_profile
        profile.employee_id = "EMP001"
        profile.save()
        
        expected = f"EMP001 - {profile.user.username}"
        self.assert_model_str_representation(profile, expected)


class DepartmentModelTest(ModelTestCase):
    """Tests pour le modèle Department."""
    
    def test_department_creation(self):
        """Test de création d'un département."""
        dept = Department.objects.create(
            name="IT",
            description="Département Informatique"
        )
        
        self.assertEqual(dept.name, "IT")
        self.assertTrue(dept.is_active)
    
    def test_department_str(self):
        """Test de la représentation string du département."""
        dept = DepartmentFactory(name="Ressources Humaines")
        self.assert_model_str_representation(dept, "Ressources Humaines")


class EmployeeIDBackendTest(TestCase):
    """Tests pour le backend d'authentification par ID employé."""
    
    def setUp(self):
        """Configuration des tests."""
        self.backend = EmployeeIDBackend()
        self.user = UserFactory()
        # Utiliser le profil auto-créé
        self.profile = self.user.employee_profile
        self.profile.employee_id = "EMP001"
        self.profile.save()
    
    def test_authenticate_with_employee_id(self):
        """Test d'authentification avec ID employé."""
        user = self.backend.authenticate(
            request=None,
            username="EMP001",
            password="mot_de_passe"
        )
        
        self.assertEqual(user, self.user)
    
    def test_authenticate_with_username(self):
        """Test d'authentification avec nom d'utilisateur."""
        user = self.backend.authenticate(
            request=None,
            username=self.user.username,
            password="mot_de_passe"
        )
        
        self.assertEqual(user, self.user)
    
    def test_authenticate_invalid_credentials(self):
        """Test avec identifiants invalides."""
        user = self.backend.authenticate(
            request=None,
            username="INVALID",
            password="wrong_password"
        )
        
        self.assertIsNone(user)
    
    def test_get_user(self):
        """Test de récupération d'utilisateur par ID."""
        retrieved_user = self.backend.get_user(self.user.id)
        self.assertEqual(retrieved_user, self.user)
        
        # Test avec ID inexistant
        self.assertIsNone(self.backend.get_user(99999))


@unittest.skip("CustomAuthenticationForm n'existe plus - à remplacer par le formulaire actuel")
class CustomAuthenticationFormTest(FormTestCase):
    """Tests pour le formulaire d'authentification personnalisé."""
    
    def setUp(self):
        """Configuration des tests."""
        self.user = UserFactory()
        self.profile = EmployeeProfileFactory(user=self.user, employee_id="EMP001")
    
    def test_valid_form_with_employee_id(self):
        """Test formulaire valide avec ID employé."""
        form = CustomAuthenticationForm(data={
            'username': 'EMP001',
            'password': 'mot_de_passe'
        })
        
        self.assert_form_valid(form)
    
    def test_valid_form_with_username(self):
        """Test formulaire valide avec nom d'utilisateur."""
        form = CustomAuthenticationForm(data={
            'username': self.user.username,
            'password': 'mot_de_passe'
        })
        
        self.assert_form_valid(form)
    
    def test_invalid_credentials(self):
        """Test avec identifiants invalides."""
        form = CustomAuthenticationForm(data={
            'username': 'INVALID',
            'password': 'wrong_password'
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)


class LoginViewTest(BaseTestCase):
    """Tests pour la vue de connexion."""
    
    def test_login_page_accessible(self):
        """Test que la page de connexion est accessible."""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'connexion')
    
    def test_login_with_employee_id(self):
        """Test connexion avec ID employé."""
        response = self.client.post(reverse('accounts:login'), {
            'username': self.test_profile.employee_id,
            'password': 'mot_de_passe'
        })
        
        # Doit rediriger après connexion réussie
        self.assertEqual(response.status_code, 302)
    
    def test_login_redirect_authenticated_user(self):
        """Test redirection d'un utilisateur déjà connecté."""
        self.login_user()
        
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 302)


class ProfileViewTest(AuthenticatedTestCase):
    """Tests pour les vues de profil."""
    
    def test_profile_view_accessible(self):
        """Test que la vue profil est accessible."""
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.test_user.get_full_name())
    
    def test_profile_view_requires_login(self):
        """Test que la vue profil nécessite une connexion."""
        self.client.logout()
        self.assert_permission_required(reverse('accounts:profile'))


class EmployeeRequiredMixinTest(AuthenticatedTestCase):
    """Tests pour le mixin EmployeeRequiredMixin."""
    
    def test_mixin_allows_employee(self):
        """Test que le mixin autorise un employé."""
        # Simuler une vue avec le mixin
        from django.views.generic import TemplateView
        from django.http import HttpResponse
        
        class TestView(EmployeeRequiredMixin, TemplateView):
            def get(self, request, *args, **kwargs):
                return HttpResponse("OK")
        
        view = TestView.as_view()
        request = self.client.request().wsgi_request
        request.user = self.test_user
        
        response = view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_mixin_rejects_user_without_profile(self):
        """Test que le mixin rejette un utilisateur sans profil."""
        # Créer un utilisateur sans profil employé
        user = UserFactory()
        self.login_user(user)
        
        # Tenter d'accéder à une vue protégée
        response = self.client.get(reverse('accounts:profile'))
        # Doit rediriger ou retourner 403
        self.assertIn(response.status_code, [302, 403])


class PasswordChangeTest(AuthenticatedTestCase):
    """Tests pour le changement de mot de passe."""
    
    def test_password_change_view_accessible(self):
        """Test que la vue de changement de mot de passe est accessible."""
        response = self.client.get(reverse('accounts:password_change'))
        self.assertEqual(response.status_code, 200)
    
    def test_password_change_requires_login(self):
        """Test que le changement de mot de passe nécessite une connexion."""
        self.client.logout()
        self.assert_permission_required(reverse('accounts:password_change'))
    
    def test_successful_password_change(self):
        """Test de changement de mot de passe réussi."""
        response = self.client.post(reverse('accounts:password_change'), {
            'old_password': 'mot_de_passe',
            'new_password1': 'nouveau_mot_de_passe_123',
            'new_password2': 'nouveau_mot_de_passe_123'
        })
        
        # Doit rediriger vers la page de confirmation
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:password_change_done'))


class IntegrationTest(BaseTestCase):
    """Tests d'intégration pour le workflow complet d'authentification."""
    
    def test_complete_login_workflow(self):
        """Test du workflow complet de connexion."""
        # 1. Accéder à la page de connexion
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        
        # 2. Se connecter avec ID employé
        response = self.client.post(reverse('accounts:login'), {
            'username': self.test_profile.employee_id,
            'password': 'mot_de_passe'
        })
        
        # 3. Vérifier la redirection
        self.assertEqual(response.status_code, 302)
        
        # 4. Accéder au profil
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        
        # 5. Se déconnecter
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)
    
    def test_unauthorized_access_protection(self):
        """Test de protection contre l'accès non autorisé."""
        protected_urls = [
            'accounts:profile',
            'accounts:password_change'
        ]
        
        for url_name in protected_urls:
            with self.subTest(url=url_name):
                self.assert_permission_required(reverse(url_name))
