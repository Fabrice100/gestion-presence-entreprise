"""
Vues pour le workflow de validation des congés.

Ce module contient les vues pour :
- Création de demandes de congés
- Validation par les managers
- Validation finale par RH/DG
- Gestion des soldes de congés
- Notifications et alertes

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Sum, F
from django.http import JsonResponse, HttpResponseRedirect
from django.utils import timezone
from datetime import date, timedelta
from django.db import transaction

from .models import LeaveRequest, LeaveType, LeaveBalance
from .forms import LeaveRequestForm, LeaveApprovalForm
from accounts.models import EmployeeProfile
from accounts.notification_service import NotificationService


class LeaveRequestListView(LoginRequiredMixin, ListView):
    """
    Liste des demandes de congés pour l'utilisateur connecté.
    """
    model = LeaveRequest
    template_name = 'leave/leave_request_list_ultra_modern.html'
    context_object_name = 'leave_requests'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        return LeaveRequest.objects.filter(
            employee=user
        ).select_related('leave_type').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Utiliser get_queryset() au lieu du queryset paginé
        all_requests = LeaveRequest.objects.filter(employee=self.request.user)
        
        # Compter les différents statuts
        context['pending_count'] = all_requests.filter(status='pending').count()
        context['approved_count'] = all_requests.filter(status__in=['approved_manager', 'approved_rh']).count()
        context['rejected_count'] = all_requests.filter(status__in=['rejected_manager', 'rejected_rh']).count()
        
        return context


class LeaveRequestCreateView(LoginRequiredMixin, CreateView):
    """
    Création d'une nouvelle demande de congé.
    """
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'leave/leave_request_create_ultra_modern.html'
    success_url = reverse_lazy('leave:leave_request_list')
    
    def get_context_data(self, **kwargs):
        """Ajoute le solde de congés au contexte."""
        context = super().get_context_data(**kwargs)
        
        # Calculer le solde total de congés
        from django.utils import timezone
        year = timezone.now().year
        total_balance = LeaveBalance.objects.filter(
            employee=self.request.user,
            year=year
        ).aggregate(
            total=Sum(F('allocated_balance') - F('taken_balance'))
        )['total'] or 25
        
        context['leave_balance'] = total_balance
        return context
    
    def get_form_kwargs(self):
        """Passe l'utilisateur au formulaire."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        # Initialiser les soldes si nécessaire
        from .leave_balance_service import leave_balance_service
        from django.utils import timezone
        leave_balance_service.initialize_employee_balance(self.request.user, timezone.now().year)
        
        return kwargs
    
    def form_valid(self, form):
        """
        Traite la soumission d'une demande de congé.
        
        Transaction atomique pour garantir la cohérence :
        - Vérification du solde
        - Création de la demande
        - Envoi des notifications
        """
        # Vérifier que l'utilisateur a un profil
        if not hasattr(self.request.user, 'employee_profile'):
            form.add_error(None, 'Erreur: Votre compte n\'a pas de profil employé. Contactez l\'administrateur.')
            return self.form_invalid(form)
        
        # Vérifier le solde de congés
        leave_type = form.cleaned_data['leave_type']
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        
        # Calculer le nombre de jours demandés
        days_requested = (end_date - start_date).days + 1
        
        # Vérifier le solde disponible
        balance, created = LeaveBalance.objects.get_or_create(
            employee=self.request.user,
            leave_type=leave_type,
            year=start_date.year,
            defaults={'allocated_balance': leave_type.allocation_amount, 'taken_balance': 0}
        )
        
        if balance.remaining_balance < days_requested:
            form.add_error(None, f'Solde insuffisant. Disponible: {balance.remaining_balance} jours, Demandé: {days_requested} jours')
            return self.form_invalid(form)
        
        # Vérifier les chevauchements
        overlapping_requests = LeaveRequest.objects.filter(
            employee=self.request.user,
            status__in=['pending', 'approved_manager', 'approved_rh'],
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        
        if overlapping_requests.exists():
            form.add_error(None, 'Vous avez déjà une demande de congé sur cette période')
            return self.form_invalid(form)
        
        # TRANSACTION ATOMIQUE pour la création
        with transaction.atomic():
            # Créer la demande
            leave_request = form.save(commit=False)
            leave_request.employee = self.request.user
            leave_request.status = 'pending'
            
            # Calculer la durée
            leave_request.duration_days = days_requested
            
            # Déterminer le niveau de validation nécessaire (BUG CORRIGÉ)
            profile = self.request.user.employee_profile
            if profile.role == 'employee':
                # Employé : validation par manager puis RH/DG (workflow complet)
                leave_request.status = 'pending'
                leave_request.manager = profile.manager
            elif profile.role == 'manager':
                # Manager : Passe DIRECTEMENT au RH sans pré-validation par un autre manager
                # Le statut 'approved_manager' indique que c'est prêt pour validation RH
                # sans avoir besoin d'une pré-validation par un autre manager
                leave_request.status = 'approved_manager'
            elif profile.role == 'rh_dg':
                # RH/DG : auto-approbation
                leave_request.status = 'approved_rh'
            
            leave_request.save()
            self.object = leave_request  # Important pour get_success_url()
        
        # Envoyer notification au validateur (HORS TRANSACTION)
        if leave_request.status == 'pending' and leave_request.manager:
            # Notifier le manager
            NotificationService.send_leave_pending_notification(leave_request, leave_request.manager)
        elif leave_request.status == 'approved_manager':
            # Notifier les RH/DG
            rh_users = User.objects.filter(employee_profile__role='rh_dg', employee_profile__is_active=True)
            for rh_user in rh_users:
                NotificationService.send_leave_pending_notification(leave_request, rh_user)
        
        messages.success(self.request, f'Demande de congé créée avec succès ! ({days_requested} jours)')
        return HttpResponseRedirect(reverse('leave:leave_request_list'))


class LeaveApprovalListView(LoginRequiredMixin, ListView):
    """
    Liste des demandes de congés à valider pour les managers et RH/DG.
    """
    model = LeaveRequest
    template_name = 'leave/leave_approval_list.html'
    context_object_name = 'leave_requests'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        profile = user.employee_profile
        
        if profile.role == 'manager':
            # Manager : voir les demandes de ses employés
            managed_employees = User.objects.filter(
                employee_profile__manager=user
            )
            queryset = LeaveRequest.objects.filter(
                employee__in=managed_employees,
                status='pending'
            ).select_related('employee', 'leave_type', 'employee__employee_profile')
        elif profile.role == 'rh_dg':
            # RH/DG : voir toutes les demandes en attente de validation finale
            queryset = LeaveRequest.objects.filter(
                status='approved_manager'
            ).select_related('employee', 'leave_type', 'employee__employee_profile')
        else:
            queryset = LeaveRequest.objects.none()
        
        return queryset.order_by('-created_at')


class LeaveApprovalDetailView(LoginRequiredMixin, DetailView):
    """
    Détail d'une demande de congé pour validation.
    """
    model = LeaveRequest
    template_name = 'leave/leave_approval_detail.html'
    context_object_name = 'leave_request'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['approval_form'] = LeaveApprovalForm()
        context['remaining_days'] = self.get_remaining_balance(self.object.employee)
        return context
    
    def post(self, request, *args, **kwargs):
        """Redirige vers la vue de traitement."""
        leave_request = self.get_object()
        return redirect('leave:leave_approval_process', pk=leave_request.pk)
    
    def get_remaining_balance(self, user):
        """Calcule le solde restant de l'employé."""
        from .leave_balance_service import leave_balance_service
        return leave_balance_service.get_remaining_balance(user)


class LeaveApprovalUpdateView(LoginRequiredMixin, DetailView):
    """
    Traitement d'une demande de congé (approbation/rejet).
    """
    model = LeaveRequest
    template_name = 'leave/leave_approval_process.html'
    context_object_name = 'leave_request'
    
    def get(self, request, *args, **kwargs):
        """Affiche le formulaire de traitement d'approbation."""
        leave_request = self.get_object()
        context = self.get_context_data(object=leave_request)
        context['remaining_days'] = self.get_remaining_balance(leave_request.employee)
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        leave_request = self.get_object()
        form = LeaveApprovalForm(request.POST)
        
        if form.is_valid():
            return self.process_approval(leave_request, form)
        else:
            return self.form_invalid(leave_request, form)
    
    def get_remaining_balance(self, user):
        """Calcule le solde restant de l'employé."""
        from .leave_balance_service import leave_balance_service
        return leave_balance_service.get_remaining_balance(user)
    
    def process_approval(self, leave_request, form):
        user = self.request.user
        
        # Vérifier que l'utilisateur a un profil
        if not hasattr(user, 'employee_profile'):
            messages.error(self.request, 'Erreur: Votre compte n\'a pas de profil employé.')
            return redirect('leave:leave_approval_list')
        
        profile = user.employee_profile
        action = form.cleaned_data['action']
        comment = form.cleaned_data.get('comment', '')
        
        with transaction.atomic():
            if profile.role == 'manager':
                # Validation manager
                if action == 'approve':
                    leave_request.manager_decision = 'approved_manager'
                    leave_request.manager_comment = comment
                    leave_request.manager_decision_at = timezone.now()
                    leave_request.status = 'approved_manager'
                    
                else:  # reject
                    leave_request.manager_decision = 'rejected_manager'
                    leave_request.manager_comment = comment
                    leave_request.manager_decision_at = timezone.now()
                    leave_request.status = 'rejected_manager'
            
            elif profile.role == 'rh_dg':
                # Validation RH/DG
                if action == 'approve':
                    leave_request.rh_decision = 'approved_rh'
                    leave_request.rh_comment = comment
                    leave_request.rh_decision_at = timezone.now()
                    leave_request.status = 'approved_rh'
                    
                    # Déduire du solde
                    self._deduct_leave_balance(leave_request)
                else:  # reject
                    leave_request.rh_decision = 'rejected_rh'
                    leave_request.rh_comment = comment
                    leave_request.rh_decision_at = timezone.now()
                    leave_request.status = 'rejected_rh'
            
            leave_request.save()
        
        # Envoyer notification à l'employé
        if action == 'approve':
            NotificationService.send_leave_approved_notification(leave_request, user)
            messages.success(self.request, 'Demande de congé approuvée avec succès.')
            
            # Si c'est un manager qui approuve, notifier les RH/DG
            if profile.role == 'manager':
                rh_users = User.objects.filter(employee_profile__role='rh_dg', employee_profile__is_active=True)
                for rh_user in rh_users:
                    NotificationService.send_leave_pending_notification(leave_request, rh_user)
        else:
            NotificationService.send_leave_rejected_notification(leave_request, user, comment)
            messages.success(self.request, 'Demande de congé rejetée.')
        
        return redirect('leave:leave_approval_list')
    
    def form_invalid(self, leave_request, form):
        """Gère les erreurs de formulaire."""
        context = self.get_context_data(object=leave_request)
        context['approval_form'] = form
        return render(self.request, self.template_name, context)
    
    def _needs_rh_approval(self, leave_request):
        """Détermine si une validation RH/DG est nécessaire."""
        # Logique métier : validation RH/DG requise pour certains types de congés
        return leave_request.leave_type.requires_rh_approval
    
    def _deduct_leave_balance(self, leave_request):
        """
        Déduit les jours de congé du solde de l'employé.
        
        BUG CORRIGÉ : Exclut automatiquement les jours fériés pour conformité légale.
        """
        from leave.holiday_service import HolidayService
        holiday_service = HolidayService()
        
        # Calculer jours OUVRABLES (excluant automatiquement jours fériés)
        working_days = holiday_service.get_working_days_in_period(
            leave_request.start_date,
            leave_request.end_date
        )
        
        balance, created = LeaveBalance.objects.get_or_create(
            employee=leave_request.employee,
            leave_type=leave_request.leave_type,
            year=leave_request.start_date.year,
            defaults={'allocated_balance': leave_request.leave_type.allocation_amount, 'taken_balance': 0}
        )
        
        # Déduire seulement les jours OUVRABLES (jours fériés exclus)
        balance.taken_balance += working_days
        balance.save()


class LeaveBalanceListView(LoginRequiredMixin, ListView):
    """
    Liste des soldes de congés pour l'utilisateur connecté.
    """
    model = LeaveBalance
    template_name = 'leave/leave_balance_list.html'
    context_object_name = 'leave_balances'
    
    def get_queryset(self):
        current_year = date.today().year
        return LeaveBalance.objects.filter(
            employee=self.request.user,
            year=current_year
        ).select_related('leave_type')


def leave_statistics_api(request):
    """
    API pour les statistiques de congés (pour les dashboards).
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Non authentifié'}, status=401)
    
    user = request.user
    profile = user.employee_profile
    current_year = date.today().year
    
    stats = {
        'total_requests': 0,
        'pending_requests': 0,
        'approved_requests': 0,
        'rejected_requests': 0,
        'available_days': 0,
        'used_days': 0,
    }
    
    if profile.role == 'employee':
        # Statistiques pour un employé
        leave_requests = LeaveRequest.objects.filter(employee=user)
        stats['total_requests'] = leave_requests.count()
        stats['pending_requests'] = leave_requests.filter(status='pending').count()
        stats['approved_requests'] = leave_requests.filter(status__in=['approved_manager', 'approved_rh']).count()
        stats['rejected_requests'] = leave_requests.filter(status__in=['rejected_manager', 'rejected_rh']).count()
        
        # Soldes
        balances = LeaveBalance.objects.filter(
            employee=user,
            year=current_year
        )
        stats['available_days'] = sum(b.remaining_balance for b in balances)
        stats['used_days'] = sum(b.taken_balance for b in balances)
    
    elif profile.role == 'manager':
        # Statistiques pour un manager (son équipe)
        managed_employees = User.objects.filter(
            employee_profile__manager=user
        )
        
        leave_requests = LeaveRequest.objects.filter(
            employee__in=managed_employees
        )
        stats['total_requests'] = leave_requests.count()
        stats['pending_requests'] = leave_requests.filter(status='pending').count()
        stats['approved_requests'] = leave_requests.filter(status__in=['approved_manager', 'approved_rh']).count()
        stats['rejected_requests'] = leave_requests.filter(status__in=['rejected_manager', 'rejected_rh']).count()
    
    elif profile.role == 'rh_dg':
        # Statistiques pour RH/DG (toute l'entreprise)
        leave_requests = LeaveRequest.objects.all()
        stats['total_requests'] = leave_requests.count()
        stats['pending_requests'] = leave_requests.filter(status='approved_manager').count()
        stats['approved_requests'] = leave_requests.filter(status='approved_rh').count()
        stats['rejected_requests'] = leave_requests.filter(status__in=['rejected_manager', 'rejected_rh']).count()
    
    return JsonResponse(stats)


# =====================================
# VUE UNIFIÉE DES CONGÉS (3 en 1)
# =====================================
class LeaveUnifiedView(LoginRequiredMixin, TemplateView):
    """
    Vue unifiée pour la gestion des congés employé
    Regroupe en un seul endroit:
    - Liste des demandes récentes (5 dernières)
    - Soldes de congés par type
    - Lien vers le calendrier complet
    
    Inspiré de Clockify/BambooHR: une seule page, plusieurs onglets
    """
    template_name = 'leave/leave_unified.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Demandes récentes (5 dernières)
        context['recent_leave_requests'] = LeaveRequest.objects.filter(
            employee=self.request.user
        ).select_related('leave_type').order_by('-created_at')[:5]
        
        # Soldes de congés
        current_year = timezone.now().year
        context['leave_balances'] = LeaveBalance.objects.filter(
            employee=self.request.user,
            year=current_year
        ).select_related('leave_type')
        
        return context
