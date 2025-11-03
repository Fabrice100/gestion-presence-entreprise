"""
Vues pour le workflow de validation des congés.

Ce module contient les vues pour :
- Création de demandes de congés
- Validation par les managers
- Validation finale par RH
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
from accounts.models import Department
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Sum, F
from django.http import JsonResponse, HttpResponseRedirect
from django.utils import timezone
from datetime import date, timedelta
from django.db import transaction, connection

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
        queryset = LeaveRequest.objects.filter(
            employee=user
        ).select_related('leave_type').order_by('-created_at')
        
        # Debug temporaire
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"LeaveRequestListView: User {user.username} (id={user.id}) has {queryset.count()} requests")
        for req in queryset[:5]:
            logger.info(f"  - Request {req.id}: {req.leave_type.name}, status={req.status}, created={req.created_at}")
        
        return queryset
    
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
        # Bypass BDD en GET pour éviter toute erreur d'affichage
        context['leave_balance'] = 0
        return context
    
    def get_form_kwargs(self):
        """Passe l'utilisateur au formulaire."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        # Initialiser les soldes si nécessaire (tolérant aux erreurs)
        try:
            from .leave_balance_service import leave_balance_service
            from django.utils import timezone
            leave_balance_service.initialize_employee_balance(self.request.user, timezone.now().year)
        except Exception:
            pass
        
        return kwargs
    
    def form_valid(self, form):
        """
        Traite la soumission d'une demande de congé.
        
        Transaction atomique pour garantir la cohérence :
        - Vérification du solde
        - Création de la demande
        - Envoi des notifications
        """
        # Vérifier que l'utilisateur a un profil (les superusers sont uniquement pour /admin/)
        if not hasattr(self.request.user, 'employee_profile'):
            form.add_error(None, 'Erreur: Votre compte n\'a pas de profil employé. Contactez l\'administrateur.')
            return self.form_invalid(form)
        
        # Vérifier le solde de congés
        leave_type = form.cleaned_data['leave_type']
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        
        # Calculer le nombre de jours demandés
        days_requested = (end_date - start_date).days + 1
        
        # VÉRIFICATION CRITIQUE : Vérifier le solde SEULEMENT pour les congés qui déduisent du solde
        # TOUS les congés payés (vacances, maladie, événements) déduisent du MÊME solde de 30j
        if hasattr(leave_type, 'deducts_balance') and leave_type.deducts_balance:
            # Récupérer le type "Congés payés" comme solde unique
            conges_payes_type = LeaveType.objects.filter(name__icontains='payé').first()
            
            if not conges_payes_type:
                form.add_error(None, 'Erreur de configuration: Type "Congés payés" non trouvé')
                return self.form_invalid(form)
            
            # Vérifier le solde global de 30 jours (pas le solde du type spécifique)
            balance, created = LeaveBalance.objects.get_or_create(
                employee=self.request.user,
                leave_type=conges_payes_type,  # Toujours utiliser le type "Congés payés"
                year=start_date.year,
                defaults={'allocated_balance': 30, 'taken_balance': 0}
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
        
        # Tenter de fixer un DEFAULT en base pour priority AVANT l'INSERT (si la colonne existe)
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("ALTER TABLE leave_leaverequest ALTER COLUMN priority SET DEFAULT 1")
        except Exception:
            pass

        # TRANSACTION ATOMIQUE pour la création
        try:
            with transaction.atomic():
                # Créer la demande
                leave_request = form.save(commit=False)
                leave_request.employee = self.request.user
                
                # Calculer la durée
                leave_request.duration_days = days_requested
                
                # Assurer une priorité par défaut si le modèle la requiert (DB NOT NULL)
                if hasattr(leave_request, 'priority') and (leave_request.priority is None):
                    leave_request.priority = 1  # priorité par défaut
                
                # Déterminer le niveau de validation nécessaire
                # CONFORME AUX SPÉCIFICATIONS (CAPTURES D'ÉCRAN)
                profile = self.request.user.employee_profile
                if profile.role == 'employee':
                    # EMPLOYÉ : validation par Manager puis RH (workflow complet en 2 étapes)
                    leave_request.status = 'pending'
                    leave_request.manager = profile.manager
                elif profile.role == 'manager':
                    # MANAGER : Bypass pré-validation, va DIRECTEMENT au RH
                    # Status 'approved_manager' = "Prêt pour validation RH finale"
                    # Conforme capture : "Demandes Manager → directement au RH"
                    leave_request.status = 'approved_manager'
                elif profile.role == 'rh':
                    # RH : Auto-approbation immédiate
                    leave_request.status = 'approved_rh'
                
                # Sauvegarder avec gestion d'erreur explicite
                leave_request.save()
                
                # Debug: logger les infos (sans requête DB dans la transaction)
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"✅ Demande créée dans transaction: ID={leave_request.id}, Employee={leave_request.employee.id} ({leave_request.employee.username}), Type={leave_request.leave_type.name}, Status={leave_request.status}")
                
                # Sauvegarder l'ID pour les notifications et le UPDATE (après le commit)
                leave_request_id = leave_request.id
                leave_request_status = leave_request.status
                is_manager_request = profile.role == 'manager'
                
                self.object = leave_request  # Important pour get_success_url()
                
                # Programmer l'UPDATE de priority APRÈS le commit (si nécessaire)
                def update_priority():
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "UPDATE leave_leaverequest SET priority=%s WHERE id=%s AND priority IS NULL",
                                [1, leave_request_id]
                            )
                    except Exception:
                        pass
                
                transaction.on_commit(update_priority)
                
                # Programmer l'envoi de notifications APRÈS le commit de la transaction
                def send_notifications():
                    try:
                        # Recharger la demande depuis la DB après le commit
                        saved_request = LeaveRequest.objects.filter(id=leave_request_id).first()
                        if not saved_request:
                            logger.error(f"❌ ERREUR: Demande {leave_request_id} non trouvée après commit!")
                            return
                        
                        logger.info(f"✅ Demande {saved_request.id} vérifiée après commit pour employee {saved_request.employee.id}")
                        
                        # Envoyer les notifications
                        if saved_request.status == 'pending' and hasattr(saved_request, 'manager') and saved_request.manager:
                            # Notifier le manager
                            NotificationService.send_leave_pending_notification(saved_request, saved_request.manager)
                        elif saved_request.status == 'approved_manager':
                            # Notifier les RH
                            rh_users = User.objects.filter(employee_profile__role='rh', employee_profile__is_active=True)
                            for rh_user in rh_users:
                                NotificationService.send_leave_pending_notification(saved_request, rh_user)
                    except Exception as notify_error:
                        # Les notifications ne doivent pas faire échouer la création
                        logger.warning(f"Erreur lors de l'envoi de notification: {notify_error}")
                
                # Exécuter les notifications APRÈS le commit
                transaction.on_commit(send_notifications)
                
        except Exception as e:
            # Logger l'erreur pour diagnostic
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la création de la demande de congé: {e}", exc_info=True)
            form.add_error(None, f'Erreur lors de la création de la demande: {str(e)}')
            return self.form_invalid(form)
        
        # Après la transaction réussie, vérifier que la demande existe vraiment
        import logging
        logger = logging.getLogger(__name__)
        
        # Le bloc atomic() est terminé, la transaction devrait être commitée
        # Vérifier une dernière fois que la demande existe
        final_check = LeaveRequest.objects.filter(id=leave_request_id).first()
        if final_check:
            logger.info(f"✅ Vérification finale: Demande {final_check.id} confirmée en base après transaction")
            messages.success(self.request, f'Demande de congé créée avec succès ! ({days_requested} jours)')
            return HttpResponseRedirect(reverse('leave:leave_request_list'))
        else:
            logger.error(f"❌ ERREUR CRITIQUE: Demande {leave_request_id} NON TROUVÉE après commit de transaction!")
            form.add_error(None, 'Erreur: La demande n\'a pas pu être sauvegardée. Veuillez réessayer.')
            return self.form_invalid(form)


class LeaveApprovalListView(LoginRequiredMixin, ListView):
    """
    Liste des demandes de congés à valider pour les managers et RH.
    """
    model = LeaveRequest
    template_name = 'leave/leave_approval_list.html'
    context_object_name = 'leave_requests'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        if not hasattr(user, 'employee_profile'):
            return LeaveRequest.objects.none()
        
        profile = user.employee_profile
        
        if profile.role == 'manager':
            # Manager : voir les demandes de SON département uniquement
            # Trouver le département que ce manager gère
            managed_department = Department.objects.filter(manager=user).first()
            
            if not managed_department:
                # Manager sans département : aucune demande
                return LeaveRequest.objects.none()
            
            # Filtrer par département du manager et gérer les filtres de statut
            status_filter = self.request.GET.get('status')
            
            if status_filter:
                # Filtrer selon le statut demandé
                if status_filter == 'pending':
                    status_query = ['pending']
                elif status_filter == 'approved':
                    status_query = ['approved_manager']
                elif status_filter == 'rejected':
                    status_query = ['rejected_manager']
                else:
                    status_query = ['pending']  # Par défaut
            else:
                # Pas de filtre : afficher tous les statuts
                status_query = ['pending', 'approved_manager', 'rejected_manager']
            
            queryset = LeaveRequest.objects.filter(
                employee__employee_profile__department=managed_department,
                status__in=status_query
            ).select_related('employee', 'leave_type', 'employee__employee_profile')
        elif profile.role == 'rh':
            # RH : voir TOUTES les demandes de TOUS les départements (employés + managers)
            # Filtre par statut si demandé, sinon affiche pending et approved_manager par défaut
            status_filter = self.request.GET.get('status')
            if status_filter:
                if status_filter == 'pending':
                    # Pour RH, "en attente" = approuvé par manager
                    queryset = LeaveRequest.objects.filter(status='approved_manager')
                elif status_filter == 'approved':
                    # Approuvées finales uniquement
                    queryset = LeaveRequest.objects.filter(status__in=['approved_rh'])
                elif status_filter == 'rejected':
                    # Rejetées finales uniquement
                    queryset = LeaveRequest.objects.filter(status__in=['rejected_rh'])
                else:
                    queryset = LeaveRequest.objects.filter(status=status_filter)
            else:
                # Par défaut: voir toutes les demandes pertinentes pour RH
                queryset = LeaveRequest.objects.filter(
                    status__in=['approved_manager', 'approved_rh', 'rejected_rh']
                )
            
            queryset = queryset.select_related('employee', 'leave_type', 'employee__employee_profile')
        else:
            queryset = LeaveRequest.objects.none()
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not hasattr(user, 'employee_profile'):
            return context
        
        profile = user.employee_profile
        # Expose convenient role flags to templates
        context['is_manager'] = getattr(profile, 'role', '') == 'manager'
        context['is_rh'] = getattr(profile, 'role', '') == 'rh'
        
        if profile.role == 'manager':
            # Pour le manager : calculer les statistiques de SON département
            managed_department = Department.objects.filter(manager=user).first()
            if managed_department:
                # Demandes en attente à TRAITER par ce manager
                pending_qs = LeaveRequest.objects.filter(
                    employee__employee_profile__department=managed_department,
                    status='pending'
                ).exclude(employee=user)

                # Demandes TRAITÉES par CE manager
                approved_by_me_qs = LeaveRequest.objects.filter(
                    manager=user,
                    manager_decision='approved_manager'
                )
                rejected_by_me_qs = LeaveRequest.objects.filter(
                    manager=user,
                    manager_decision='rejected_manager'
                )
            else:
                pending_qs = LeaveRequest.objects.none()
                approved_by_me_qs = LeaveRequest.objects.none()
                rejected_by_me_qs = LeaveRequest.objects.none()
            
            # Statistiques MANAGER (centrées utilisateur)
            context['pending_count'] = pending_qs.count()
            context['approved_count'] = approved_by_me_qs.count()
            context['rejected_count'] = rejected_by_me_qs.count()
            context['total_count'] = (
                context['pending_count'] + context['approved_count'] + context['rejected_count']
            )
            
        elif profile.role == 'rh':
            # Pour le RH : calculer les statistiques sur ses validations finales
            context['pending_count'] = LeaveRequest.objects.filter(status='approved_manager').count()
            # Pas de traçage par RH spécifique dans le modèle; on affiche global finalisé
            context['approved_count'] = LeaveRequest.objects.filter(status='approved_rh').count()
            context['rejected_count'] = LeaveRequest.objects.filter(status='rejected_rh').count()
            context['total_count'] = LeaveRequest.objects.filter(
                status__in=['approved_manager', 'approved_rh', 'rejected_rh']
            ).count()
        
        return context


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
        user = self.request.user
        if hasattr(user, 'employee_profile'):
            role = getattr(user.employee_profile, 'role', '')
            context['is_manager'] = role == 'manager'
            context['is_rh'] = role == 'rh'
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
        """Redirige vers la page de détails (traitement intégré)."""
        self.object = self.get_object()
        return redirect('leave:leave_approval_detail', pk=self.object.pk)
    
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
                    leave_request.manager = user
                    leave_request.manager_decision = 'approved_manager'
                    leave_request.manager_comment = comment
                    leave_request.manager_decision_at = timezone.now()
                    leave_request.status = 'approved_manager'
                    
                else:  # reject
                    leave_request.manager = user
                    leave_request.manager_decision = 'rejected_manager'
                    leave_request.manager_comment = comment
                    leave_request.manager_decision_at = timezone.now()
                    leave_request.status = 'rejected_manager'
            
            elif profile.role == 'rh':
                # Validation RH
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
            
            # Si c'est un manager qui approuve, notifier les RH
            if profile.role == 'manager':
                rh_users = User.objects.filter(employee_profile__role='rh', employee_profile__is_active=True)
                for rh_user in rh_users:
                    NotificationService.send_leave_pending_notification(leave_request, rh_user)
        else:
            NotificationService.send_leave_rejected_notification(leave_request, user, comment)
            messages.success(self.request, 'Demande de congé rejetée.')
        
        return redirect('leave:leave_approval_list')
    
    def form_invalid(self, leave_request, form):
        """Gère les erreurs de formulaire."""
        self.object = leave_request  # Définir self.object pour get_context_data()
        context = self.get_context_data()
        context['approval_form'] = form
        return render(self.request, self.template_name, context)
    
    def _needs_rh_approval(self, leave_request):
        """Détermine si une validation RH est nécessaire."""
        # Logique métier : validation RH requise pour certains types de congés
        return leave_request.leave_type.requires_rh_approval
    
    def _deduct_leave_balance(self, leave_request):
        """
        Déduit les jours de congé du solde UNIQUE de 30 jours de l'employé.
        
        BUG CORRIGÉ : Exclut automatiquement les jours fériés pour conformité légale.
        NOUVEAU : TOUS les congés payés (vacances, maladie, événements) déduisent 
                  du MÊME solde de 30 jours.
        """
        # VÉRIFICATION CRITIQUE : Ce type de congé déduit-il du solde ?
        if not leave_request.leave_type.deducts_balance:
            # Congé sans solde uniquement : NE PAS déduire
            return
        
        from leave.holiday_service import HolidayService
        holiday_service = HolidayService()
        
        # Calculer jours OUVRABLES (excluant automatiquement jours fériés)
        working_days = holiday_service.get_working_days_in_period(
            leave_request.start_date,
            leave_request.end_date
        )
        
        # Récupérer le type "Congés payés" comme solde unique
        conges_payes_type = LeaveType.objects.filter(name__icontains='payé').first()
        
        if not conges_payes_type:
            # Erreur de configuration, mais ne pas bloquer l'approbation
            return
        
        # IMPORTANT : Toujours déduire du solde "Congés payés" (solde unique de 30j)
        # Peu importe le type demandé (maladie, événements, etc.)
        balance, created = LeaveBalance.objects.get_or_create(
            employee=leave_request.employee,
            leave_type=conges_payes_type,  # Toujours utiliser le type "Congés payés"
            year=leave_request.start_date.year,
            defaults={'allocated_balance': 30, 'taken_balance': 0}
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
    
    if not hasattr(user, 'employee_profile'):
        return JsonResponse({'error': 'Profil employé non trouvé'}, status=403)
    
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
    
    elif profile.role == 'rh':
        # Statistiques pour RH (toute l'entreprise)
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
