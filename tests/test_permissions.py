"""
Tests unitaires pour les mixins de permissions.

Ce module teste :
- EmployeeRequiredMixin
- ManagerRequiredMixin
- RHRequiredMixin
- Gestion des permissions par rôle

Auteur: Système de Gestion de Présence
Date: 22 octobre 2025
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponse
from django.views.generic import View
from accounts.models import EmployeeProfile, Department
from common.mixins import (
    EmployeeRequiredMixin,
    ManagerRequiredMixin,
    RHRequiredMixin
)


class PermissionMixinTestBase(TestCase):
    """Classe de base pour tester les mixins de permissions."""
    
    def add_messages_to_request(self, request):
        """Ajoute le stockage de messages à une requête RequestFactory."""
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return request


class EmployeeRequiredMixinTest(PermissionMixinTestBase):
    """Tests pour EmployeeRequiredMixin."""
    
    def setUp(self):
        """Configuration initiale."""
        self.factory = RequestFactory()
        self.dept = Department.objects.create(name='Test Dept')
        
        # Créer un employé actif
        self.employee_user = User.objects.create_user(
            username='employee',
            password='password'
        )
        self.employee_profile = self.employee_user.employee_profile
        self.employee_profile.employee_id = 'EMP001'
        self.employee_profile.department = self.dept
        self.employee_profile.role = 'employee'
        self.employee_profile.is_active = True
        self.employee_profile.save()
        
        # Créer un employé inactif
        self.inactive_user = User.objects.create_user(
            username='inactive',
            password='password'
        )
        self.inactive_profile = self.inactive_user.employee_profile
        self.inactive_profile.employee_id = 'EMP002'
        self.inactive_profile.department = self.dept
        self.inactive_profile.role = 'employee'
        self.inactive_profile.is_active = False
        self.inactive_profile.save()
        
        # Créer un utilisateur sans profil (admin)
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='password',
            email='admin@test.com'
        )
        # Supprimer le profil auto-créé pour tester le cas sans profil
        EmployeeProfile.objects.filter(user=self.admin_user).delete()
        # Recharger l'utilisateur pour vider le cache de la relation
        self.admin_user = User.objects.get(pk=self.admin_user.pk)
    
    def test_authenticated_active_employee(self):
        """Employé actif authentifié doit passer."""
        
        class TestView(EmployeeRequiredMixin, View):
            def get(self, request):
                return HttpResponse("OK")
        
        request = self.factory.get('/test/')
        request.user = self.employee_user
        
        view = TestView.as_view()
        response = view(request)
        
        # Devrait passer
        self.assertEqual(response.status_code, 200)
    
    def test_inactive_employee(self):
        """Employé inactif ne doit pas passer."""
        
        class TestView(EmployeeRequiredMixin, View):
            def get(self, request):
                return HttpResponse("OK")
        
        request = self.factory.get('/test/')
        request.user = self.inactive_user
        request = self.add_messages_to_request(request)
        
        view = TestView.as_view()
        response = view(request)
        
        # Devrait rediriger (302)
        self.assertEqual(response.status_code, 302)
    
    def test_user_without_profile(self):
        """Utilisateur sans profil (admin) ne doit pas passer."""
        
        # Vérifier que le profil a bien été supprimé
        self.assertFalse(hasattr(self.admin_user, 'employee_profile'))
        
        class TestView(EmployeeRequiredMixin, View):
            def get(self, request):
                return HttpResponse("OK")
        
        request = self.factory.get('/test/')
        request.user = self.admin_user
        request = self.add_messages_to_request(request)
        
        view = TestView.as_view()
        response = view(request)
        
        # Devrait rediriger car pas de profil employé
        self.assertEqual(response.status_code, 302)
    
    def test_anonymous_user(self):
        """Utilisateur anonyme ne doit pas passer."""
        
        class TestView(EmployeeRequiredMixin, View):
            def get(self, request):
                return HttpResponse("OK")
        
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        view = TestView.as_view()
        response = view(request)
        
        # Devrait rediriger
        self.assertEqual(response.status_code, 302)


class ManagerRequiredMixinTest(PermissionMixinTestBase):
    """Tests pour ManagerRequiredMixin."""
    
    def setUp(self):
        """Configuration initiale."""
        self.factory = RequestFactory()
        self.dept = Department.objects.create(name='Test Dept')
        
        # Créer un manager
        self.manager_user = User.objects.create_user(
            username='manager',
            password='password'
        )
        self.manager_profile = self.manager_user.employee_profile
        self.manager_profile.employee_id = 'EMP100'
        self.manager_profile.department = self.dept
        self.manager_profile.role = 'manager'
        self.manager_profile.is_active = True
        self.manager_profile.save()
        
        # Créer un employé simple
        self.employee_user = User.objects.create_user(
            username='employee',
            password='password'
        )
        self.employee_profile = self.employee_user.employee_profile
        self.employee_profile.employee_id = 'EMP001'
        self.employee_profile.department = self.dept
        self.employee_profile.role = 'employee'
        self.employee_profile.is_active = True
        self.employee_profile.save()
    
    def test_manager_can_access(self):
        """Manager doit pouvoir accéder."""
        
        class TestView(ManagerRequiredMixin, View):
            def get(self, request):
                return HttpResponse("OK")
        
        request = self.factory.get('/test/')
        request.user = self.manager_user
        
        view = TestView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_employee_cannot_access(self):
        """Employé simple ne peut pas accéder."""
        
        class TestView(ManagerRequiredMixin, View):
            def get(self, request):
                return HttpResponse("OK")
        
        request = self.factory.get('/test/')
        request.user = self.employee_user
        request = self.add_messages_to_request(request)
        
        view = TestView.as_view()
        response = view(request)
        
        # Devrait rediriger
        self.assertEqual(response.status_code, 302)


class RHRequiredMixinTest(PermissionMixinTestBase):
    """Tests pour RHRequiredMixin."""
    
    def setUp(self):
        """Configuration initiale."""
        self.factory = RequestFactory()
        self.dept = Department.objects.create(name='Test Dept')
        
        # Créer un RH
        self.rh_user = User.objects.create_user(
            username='rh',
            password='password'
        )
        self.rh_profile = self.rh_user.employee_profile
        self.rh_profile.employee_id = 'EMP200'
        self.rh_profile.department = self.dept
        self.rh_profile.role = 'rh'
        self.rh_profile.is_active = True
        self.rh_profile.save()
        
        # Créer un manager
        self.manager_user = User.objects.create_user(
            username='manager',
            password='password'
        )
        self.manager_profile = self.manager_user.employee_profile
        self.manager_profile.employee_id = 'EMP100'
        self.manager_profile.department = self.dept
        self.manager_profile.role = 'manager'
        self.manager_profile.is_active = True
        self.manager_profile.save()
        
        # Créer un employé
        self.employee_user = User.objects.create_user(
            username='employee',
            password='password'
        )
        self.employee_profile = self.employee_user.employee_profile
        self.employee_profile.employee_id = 'EMP001'
        self.employee_profile.department = self.dept
        self.employee_profile.role = 'employee'
        self.employee_profile.is_active = True
        self.employee_profile.save()
    
    def test_rh_can_access(self):
        """RH doit pouvoir accéder."""
        
        class TestView(RHRequiredMixin, View):
            def get(self, request):
                return HttpResponse("OK")
        
        request = self.factory.get('/test/')
        request.user = self.rh_user
        
        view = TestView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_manager_cannot_access(self):
        """Manager ne peut pas accéder aux fonctions RH."""
        
        class TestView(RHRequiredMixin, View):
            def get(self, request):
                return HttpResponse("OK")
        
        request = self.factory.get('/test/')
        request.user = self.manager_user
        request = self.add_messages_to_request(request)
        
        view = TestView.as_view()
        response = view(request)
        
        # Devrait rediriger
        self.assertEqual(response.status_code, 302)
    
    def test_employee_cannot_access(self):
        """Employé ne peut pas accéder aux fonctions RH."""
        
        class TestView(RHRequiredMixin, View):
            def get(self, request):
                return HttpResponse("OK")
        
        request = self.factory.get('/test/')
        request.user = self.employee_user
        request = self.add_messages_to_request(request)
        
        view = TestView.as_view()
        response = view(request)
        
        # Devrait rediriger
        self.assertEqual(response.status_code, 302)


class PermissionHierarchyRequiredMixinTest(PermissionMixinTestBase):
    """Tests pour la hiérarchie des permissions."""
    
    def setUp(self):
        """Configuration initiale."""
        self.dept = Department.objects.create(name='Test Dept')
        
        # Créer tous les rôles
        self.employee_user = User.objects.create_user(username='employee', password='pwd')
        employee_profile = self.employee_user.employee_profile
        employee_profile.employee_id = 'EMP001'
        employee_profile.department = self.dept
        employee_profile.role = 'employee'
        employee_profile.is_active = True
        employee_profile.save()
        
        self.manager_user = User.objects.create_user(username='manager', password='pwd')
        manager_profile = self.manager_user.employee_profile
        manager_profile.employee_id = 'EMP100'
        manager_profile.department = self.dept
        manager_profile.role = 'manager'
        manager_profile.is_active = True
        manager_profile.save()
        
        self.rh_user = User.objects.create_user(username='rh', password='pwd')
        rh_profile = self.rh_user.employee_profile
        rh_profile.employee_id = 'EMP200'
        rh_profile.department = self.dept
        rh_profile.role = 'rh'
        rh_profile.is_active = True
        rh_profile.save()
    
    def test_employee_is_not_manager(self):
        """Employé n'est pas manager."""
        self.assertFalse(self.employee_user.employee_profile.is_manager())
    
    def test_employee_is_not_rh(self):
        """Employé n'est pas RH."""
        self.assertFalse(self.employee_user.employee_profile.is_rh())
    
    def test_manager_is_manager(self):
        """Manager est bien manager."""
        self.assertTrue(self.manager_user.employee_profile.is_manager())
    
    def test_manager_is_not_rh(self):
        """Manager n'est pas RH."""
        self.assertFalse(self.manager_user.employee_profile.is_rh())
    
    def test_rh_is_not_manager(self):
        """RH n'est pas manager."""
        self.assertFalse(self.rh_user.employee_profile.is_manager())
    
    def test_rh_is_rh(self):
        """RH est bien RH."""
        self.assertTrue(self.rh_user.employee_profile.is_rh())
