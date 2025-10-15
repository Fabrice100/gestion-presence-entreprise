"""
Classe de base pour tous les tests, respectant les principes SOLID.

Fournit des fonctionnalités communes et une structure cohérente
pour tous les tests du projet.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from accounts.models import EmployeeProfile
from attendance.admin_models import CompanySettings
from .factories import (
    UserFactory, EmployeeProfileFactory, DepartmentFactory,
    CompanySettingsFactory, TestDataHelper
)


class BaseTestCase(TestCase):
    """
    Classe de base pour tous les tests suivant le principe DRY.
    
    Fournit des méthodes communes et une configuration de base
    réutilisable dans tous les tests.
    """
    
    @classmethod
    def setUpClass(cls):
        """Configuration commune à tous les tests de la classe."""
        super().setUpClass()
        cls.client = Client()
    
    def setUp(self):
        """Configuration exécutée avant chaque test."""
        super().setUp()
        
        # Configuration d'entreprise par défaut
        self.company_settings = CompanySettingsFactory()
        
        # Créer un utilisateur de test standard
        self.test_user, self.test_profile = TestDataHelper.create_employee_with_profile()
        
        # Créer un manager de test
        self.manager_user, self.manager_profile, self.department = (
            TestDataHelper.create_manager_with_department()
        )
    
    def login_user(self, user: User = None) -> User:
        """
        Connecte un utilisateur pour les tests nécessitant une authentification.
        
        Args:
            user: Utilisateur à connecter (self.test_user par défaut)
            
        Returns:
            User: L'utilisateur connecté
        """
        if user is None:
            user = self.test_user
        
        self.client.force_login(user)
        return user
    
    def assert_redirects_to_login(self, response):
        """Vérifie qu'une réponse redirige vers la page de connexion."""
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def assert_permission_required(self, url: str, method: str = 'GET'):
        """
        Teste qu'une URL nécessite une authentification.
        
        Args:
            url: URL à tester
            method: Méthode HTTP ('GET', 'POST', etc.)
        """
        if method.upper() == 'GET':
            response = self.client.get(url)
        elif method.upper() == 'POST':
            response = self.client.post(url)
        else:
            raise ValueError(f"Méthode {method} non supportée")
        
        self.assert_redirects_to_login(response)
    
    def create_test_data(self, **kwargs):
        """
        Méthode à surcharger dans les classes filles.
        Crée des données spécifiques au test.
        """
        pass


class AuthenticatedTestCase(BaseTestCase):
    """
    Classe de base pour les tests nécessitant une authentification.
    
    Hérite de BaseTestCase et ajoute l'authentification automatique.
    """
    
    def setUp(self):
        """Configuration avec utilisateur authentifié."""
        super().setUp()
        self.login_user(self.test_user)


class ManagerTestCase(AuthenticatedTestCase):
    """
    Classe de base pour les tests nécessitant des permissions de manager.
    """
    
    def setUp(self):
        """Configuration avec manager authentifié."""
        super().setUp()
        # Remplacer l'utilisateur par défaut par le manager
        self.login_user(self.manager_user)
        self.current_user = self.manager_user
        self.current_profile = self.manager_profile


class APITestCase(BaseTestCase):
    """
    Classe de base pour les tests d'API.
    
    Fournit des méthodes utiles pour tester les endpoints JSON.
    """
    
    def assert_json_response(self, response, expected_status=200):
        """
        Vérifie qu'une réponse est du JSON valide avec le bon statut.
        
        Args:
            response: Réponse Django
            expected_status: Code de statut attendu
            
        Returns:
            dict: Données JSON décodées
        """
        self.assertEqual(response.status_code, expected_status)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        try:
            return response.json()
        except ValueError:
            self.fail("La réponse n'est pas du JSON valide")
    
    def assert_json_error(self, response, expected_status=400):
        """
        Vérifie qu'une réponse JSON contient une erreur.
        
        Args:
            response: Réponse Django
            expected_status: Code de statut d'erreur attendu
            
        Returns:
            dict: Données d'erreur JSON
        """
        data = self.assert_json_response(response, expected_status)
        self.assertIn('error', data, "La réponse d'erreur doit contenir un champ 'error'")
        return data


class FormTestCase(BaseTestCase):
    """
    Classe de base pour les tests de formulaires.
    
    Fournit des méthodes utiles pour tester la validation des formulaires.
    """
    
    def assert_form_error(self, form, field, error_code):
        """
        Vérifie qu'un formulaire a une erreur sur un champ spécifique.
        
        Args:
            form: Instance de formulaire Django
            field: Nom du champ
            error_code: Code d'erreur attendu
        """
        self.assertFalse(form.is_valid())
        self.assertIn(field, form.errors)
        # Optionnel: vérifier le code d'erreur spécifique
        if error_code:
            field_errors = form.errors[field]
            error_codes = [error.code for error in field_errors if hasattr(error, 'code')]
            self.assertIn(error_code, error_codes)
    
    def assert_form_valid(self, form):
        """Vérifie qu'un formulaire est valide."""
        if not form.is_valid():
            self.fail(f"Le formulaire devrait être valide. Erreurs: {form.errors}")


class ModelTestCase(BaseTestCase):
    """
    Classe de base pour les tests de modèles.
    
    Fournit des méthodes utiles pour tester les modèles Django.
    """
    
    def assert_model_field_required(self, model_class, field_name, **field_kwargs):
        """
        Teste qu'un champ de modèle est obligatoire.
        
        Args:
            model_class: Classe du modèle
            field_name: Nom du champ à tester
            **field_kwargs: Autres champs requis pour créer l'instance
        """
        # Tenter de créer une instance sans le champ requis
        with self.assertRaises(Exception):  # ValidationError ou IntegrityError
            instance = model_class(**field_kwargs)
            instance.full_clean()  # Déclenche la validation
            instance.save()
    
    def assert_model_str_representation(self, instance, expected_str):
        """
        Teste la représentation string d'un modèle.
        
        Args:
            instance: Instance du modèle
            expected_str: Représentation string attendue
        """
        self.assertEqual(str(instance), expected_str)