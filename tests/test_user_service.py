"""
Tests unitaires pour UserService.

Ce module teste :
- Génération d'employee_id unique
- Génération de username depuis email
- Génération de mot de passe sécurisé
- Création d'employé avec credentials

Auteur: Système de Gestion de Présence
Date: 22 octobre 2025
"""

from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import EmployeeProfile, Department
from accounts.user_services import UserService


class UserServiceEmployeeIDTest(TestCase):
    """Tests pour la génération d'employee_id."""
    
    def setUp(self):
        """Configuration initiale des tests."""
        self.dept = Department.objects.create(
            name='Test Department',
            description='Département de test'
        )
    
    def test_generate_employee_id_format(self):
        """Vérifie que l'ID généré respecte le format EMPXXX."""
        employee_id = UserService.generate_employee_id()
        
        self.assertTrue(employee_id.startswith('EMP'))
        self.assertEqual(len(employee_id), 6)  # EMP + 3 chiffres
        self.assertTrue(employee_id[3:].isdigit())
    
    def test_generate_employee_id_unique(self):
        """Vérifie que les IDs générés sont uniques."""
        # Créer un utilisateur avec un ID
        user1 = User.objects.create_user(username='test1', password='password')
        profile1 = EmployeeProfile.objects.create(
            user=user1,
            employee_id='EMP123',
            department=self.dept
        )
        
        # Générer 10 nouveaux IDs
        generated_ids = set()
        for _ in range(10):
            new_id = UserService.generate_employee_id()
            generated_ids.add(new_id)
        
        # Vérifier unicité
        self.assertEqual(len(generated_ids), 10)
        self.assertNotIn('EMP123', generated_ids)
    
    def test_generate_employee_id_random(self):
        """Vérifie que les IDs sont aléatoires (non séquentiels)."""
        id1 = UserService.generate_employee_id()
        id2 = UserService.generate_employee_id()
        
        # Les IDs ne doivent pas être consécutifs
        num1 = int(id1[3:])
        num2 = int(id2[3:])
        self.assertNotEqual(abs(num1 - num2), 1)


class UserServiceUsernameTest(TestCase):
    """Tests pour la génération de username."""
    
    def test_generate_username_from_email(self):
        """Vérifie la génération de username depuis l'email."""
        username = UserService.generate_username_from_email('jean.dupont@example.com')
        self.assertEqual(username, 'jean.dupont')
    
    def test_generate_username_lowercase(self):
        """Vérifie que le username est en minuscules."""
        username = UserService.generate_username_from_email('JEAN.DUPONT@example.com')
        self.assertEqual(username, 'jean.dupont')
    
    def test_generate_username_conflict(self):
        """Vérifie la gestion des conflits de username."""
        # Créer un utilisateur existant
        User.objects.create_user(username='jean.dupont', password='password')
        
        # Générer un username qui devrait être différent
        username = UserService.generate_username_from_email('jean.dupont@example.com')
        self.assertEqual(username, 'jean.dupont1')
    
    def test_generate_username_multiple_conflicts(self):
        """Vérifie la gestion de multiples conflits."""
        User.objects.create_user(username='test', password='password')
        User.objects.create_user(username='test1', password='password')
        User.objects.create_user(username='test2', password='password')
        
        username = UserService.generate_username_from_email('test@example.com')
        self.assertEqual(username, 'test3')


class UserServicePasswordTest(TestCase):
    """Tests pour la génération de mot de passe."""
    
    def test_generate_password_length(self):
        """Vérifie la longueur du mot de passe."""
        password = UserService.generate_random_password(length=12)
        self.assertEqual(len(password), 12)
    
    def test_generate_password_default_length(self):
        """Vérifie la longueur par défaut."""
        password = UserService.generate_random_password()
        self.assertEqual(len(password), 8)
    
    def test_generate_password_contains_uppercase(self):
        """Vérifie la présence de majuscules."""
        password = UserService.generate_random_password()
        self.assertTrue(any(c.isupper() for c in password))
    
    def test_generate_password_contains_lowercase(self):
        """Vérifie la présence de minuscules."""
        password = UserService.generate_random_password()
        self.assertTrue(any(c.islower() for c in password))
    
    def test_generate_password_contains_digit(self):
        """Vérifie la présence de chiffres."""
        password = UserService.generate_random_password()
        self.assertTrue(any(c.isdigit() for c in password))
    
    def test_generate_password_contains_special(self):
        """Vérifie la présence de caractères spéciaux."""
        password = UserService.generate_random_password()
        special_chars = '!@#$%*'
        self.assertTrue(any(c in special_chars for c in password))
    
    def test_generate_password_unique(self):
        """Vérifie que les mots de passe générés sont différents."""
        passwords = {UserService.generate_random_password() for _ in range(10)}
        self.assertEqual(len(passwords), 10)


class UserServiceCreateEmployeeTest(TestCase):
    """Tests pour la création d'employé avec credentials."""
    
    def setUp(self):
        """Configuration initiale des tests."""
        self.dept = Department.objects.create(
            name='IT Department',
            description='Département IT'
        )
    
    def test_create_employee_success(self):
        """Vérifie la création réussie d'un employé."""
        user_data = {
            'email': 'marie.martin@example.com',
            'first_name': 'Marie',
            'last_name': 'Martin'
        }
        
        profile_data = {
            'department': self.dept,
            'manager': None,
            'role': 'employee'
        }
        
        user, employee_id, password = UserService.create_employee_with_credentials(
            user_data, profile_data
        )
        
        # Vérifications
        self.assertIsNotNone(user)
        self.assertIsNotNone(employee_id)
        self.assertIsNotNone(password)
        
        self.assertEqual(user.email, 'marie.martin@example.com')
        self.assertEqual(user.first_name, 'Marie')
        self.assertEqual(user.last_name, 'Martin')
        self.assertEqual(user.username, 'marie.martin')
        
        # Vérifier le profil
        self.assertTrue(hasattr(user, 'employee_profile'))
        self.assertEqual(user.employee_profile.employee_id, employee_id)
        self.assertEqual(user.employee_profile.role, 'employee')
        self.assertEqual(user.employee_profile.department, self.dept)
        self.assertTrue(user.employee_profile.force_password_change)
        self.assertTrue(user.employee_profile.can_punch)
    
    def test_create_manager_no_punch(self):
        """Vérifie que le RH n'a pas de pointage."""
        user_data = {
            'email': 'rh@example.com',
            'first_name': 'RH',
            'last_name': 'Direction'
        }
        
        profile_data = {
            'department': self.dept,
            'manager': None,
            'role': 'rh_dg'
        }
        
        user, employee_id, password = UserService.create_employee_with_credentials(
            user_data, profile_data
        )
        
        # RH ne peut pas pointer
        self.assertFalse(user.employee_profile.can_punch)
    
    def test_create_employee_password_valid(self):
        """Vérifie que le mot de passe généré fonctionne."""
        user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        profile_data = {
            'department': self.dept,
            'manager': None,
            'role': 'employee'
        }
        
        user, employee_id, password = UserService.create_employee_with_credentials(
            user_data, profile_data
        )
        
        # Vérifier que le mot de passe fonctionne
        self.assertTrue(user.check_password(password))
    
    def test_create_employee_employee_id_format(self):
        """Vérifie le format de l'employee_id créé."""
        user_data = {
            'email': 'test2@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        profile_data = {
            'department': self.dept,
            'manager': None,
            'role': 'employee'
        }
        
        user, employee_id, password = UserService.create_employee_with_credentials(
            user_data, profile_data
        )
        
        # Vérifier le format EMPXXX
        self.assertTrue(employee_id.startswith('EMP'))
        self.assertEqual(len(employee_id), 6)
