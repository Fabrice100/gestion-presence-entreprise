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
from django.http import HttpResponse
from django.views.generic import View
from accounts.models import EmployeeProfile, Department
from common.mixins import (
    EmployeeRequiredMixin,
    ManagerRequiredMixin,
    RHRequiredMixin
)


class EmployeeRequiredMixinTest(TestCase):
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
        self.employee_profile = EmployeeProfile.objects.create(
            user=self.employee_user,
            employee_id='EMP001',
            department=self.dept,
            role='employee',
            is_active=True
        )
        
        # Créer un employé inactif
        self.inactive_user = User.objects.create_user(
            username='inactive',
            password='password'
        )
        self.inactive_profile = EmployeeProfile.objects.create(
            user=self.inactive_user,
            employee_id='EMP002',
            department=self.dept,
            role='employee',
            is_active=False
        )
        
        # Créer un utilisateur sans profil (admin)
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='password',
            email='admin@test.com'
        )
    
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
        
        view = TestView.as_view()
        response = view(request)
        
        # Devrait rediriger (302)
        self.assertEqual(response.status_code, 302)
    
    def test_user_without_profile(self):
        """Utilisateur sans profil (admin) ne doit pas passer."""
        
        class TestView(EmployeeRequiredMixin, View):
            def get(self, request):
                return HttpResponse("OK")
        
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        view = TestView.as_view()
        response = view(request)
        
        # Devrait rediriger
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


class ManagerRequiredMixinTest(TestCase):
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
        self.manager_profile = EmployeeProfile.objects.create(
            user=self.manager_user,
            employee_id='EMP100',
            department=self.dept,
            role='manager',
            is_active=True
        )
        
        # Créer un employé simple
        self.employee_user = User.objects.create_user(
            username='employee',
            password='password'
        )
        self.employee_profile = EmployeeProfile.objects.create(
            user=self.employee_user,
            employee_id='EMP001',
            department=self.dept,
            role='employee',
            is_active=True
        )
    
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
        
        view = TestView.as_view()
        response = view(request)
        
        # Devrait rediriger
        self.assertEqual(response.status_code, 302)


class RHRequiredMixinTest(TestCase):
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
        self.rh_profile = EmployeeProfile.objects.create(
            user=self.rh_user,
            employee_id='EMP200',
            department=self.dept,
            role='rh_dg',
            is_active=True
        )
        
        # Créer un manager
        self.manager_user = User.objects.create_user(
            username='manager',
            password='password'
        )
        self.manager_profile = EmployeeProfile.objects.create(
            user=self.manager_user,
            employee_id='EMP100',
            department=self.dept,
            role='manager',
            is_active=True
        )
        
        # Créer un employé
        self.employee_user = User.objects.create_user(
            username='employee',
            password='password'
        )
        self.employee_profile = EmployeeProfile.objects.create(
            user=self.employee_user,
            employee_id='EMP001',
            department=self.dept,
            role='employee',
            is_active=True
        )
    
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
        
        view = TestView.as_view()
        response = view(request)
        
        # Devrait rediriger
        self.assertEqual(response.status_code, 302)


class PermissionHierarchyTest(TestCase):
    """Tests pour la hiérarchie des permissions."""
    
    def setUp(self):
        """Configuration initiale."""
        self.dept = Department.objects.create(name='Test Dept')
        
        # Créer tous les rôles
        self.employee_user = User.objects.create_user(username='employee', password='pwd')
        EmployeeProfile.objects.create(
            user=self.employee_user,
            employee_id='EMP001',
            department=self.dept,
            role='employee',
            is_active=True
        )
        
        self.manager_user = User.objects.create_user(username='manager', password='pwd')
        EmployeeProfile.objects.create(
            user=self.manager_user,
            employee_id='EMP100',
            department=self.dept,
            role='manager',
            is_active=True
        )
        
        self.rh_user = User.objects.create_user(username='rh', password='pwd')
        EmployeeProfile.objects.create(
            user=self.rh_user,
            employee_id='EMP200',
            department=self.dept,
            role='rh_dg',
            is_active=True
        )
    
    def test_employee_is_not_manager(self):
        """Employé n'est pas manager."""
        self.assertFalse(self.employee_user.employee_profile.is_manager())
    
    def test_employee_is_not_rh(self):
        """Employé n'est pas RH."""
        self.assertFalse(self.employee_user.employee_profile.is_rh_dg())
    
    def test_manager_is_manager(self):
        """Manager est bien manager."""
        self.assertTrue(self.manager_user.employee_profile.is_manager())
    
    def test_manager_is_not_rh(self):
        """Manager n'est pas RH."""
        self.assertFalse(self.manager_user.employee_profile.is_rh_dg())
    
    def test_rh_is_not_manager(self):
        """RH n'est pas manager."""
        self.assertFalse(self.rh_user.employee_profile.is_manager())
    
    def test_rh_is_rh(self):
        """RH est bien RH."""
        self.assertTrue(self.rh_user.employee_profile.is_rh_dg())
