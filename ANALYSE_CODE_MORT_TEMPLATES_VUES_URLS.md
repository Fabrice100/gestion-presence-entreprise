# 🔍 Analyse des Templates, Vues et URLs Non Utilisés

## 📊 Méthodologie

1. **Templates trouvés** : 57 fichiers HTML
2. **Vues analysées** : Tous les fichiers `*views.py`
3. **URLs analysées** : Tous les fichiers `*urls.py`

---

## ⚠️ TEMPLATES NON UTILISÉS (Suspects)

### 1. Templates d'Anciennes Versions
- `leave/manager_validation_backend_connected.html` - Ancienne version
- `leave/manager_validation_simple.html` - Ancienne version
- `leave/manager_validation_ultra_modern.html` - Ancienne version
- `leave/manager_my_requests_ultra_modern.html` - Ancienne version
- `leave/leave_approval_list_modern.html` - Ancienne version
- `leave/leave_unified.html` - Redirige vers autre page
- `leave/leave_request_edit.html` - Peut-être non utilisé
- `leave/leave_calendar_ultra_modern.html` - Peut-être non utilisé
- `leave/leave_balance_list.html` - À vérifier
- `leave/rh_leave_management_ultra_modern.html` - À vérifier

### 2. Templates de Rapports
- `reports/anomaly_report.html` - Anomalies désactivées
- `reports/leave_report.html` - Commenté dans URLs
- `reports/reports_dashboard.html` - À vérifier
- `reports/template_list.html` - À vérifier
- `reports/system_settings.html` - À vérifier

### 3. Templates de Diagnostic/Test
- `attendance/anomaly_detail.html` - Anomalies désactivées
- `attendance/company_settings.html` - Utilisé dans settings_views

### 4. Templates de Base
- `base.html` - Ancienne version, remplacée par `base_ultra_modern.html`

### 5. Templates de Profil
- `accounts/profile_edit.html` - Erreur (champ phone n'existe pas)

### 6. Templates d'Email
- `accounts/welcome_email.html` - Email (utilisé)
- `accounts/password_reset_email.html` - Email (utilisé)

---

## ⚠️ VUES NON UTILISÉES (Suspects)

### Dans `leave/views.py`
- `ManagerLeaveRequestsView` - URL existe mais peut être redondant
- `ManagerLeaveValidationView` - URL existe mais peut être redondant
- `RHLeaveManagementView` - URL existe mais peut être redondant
- `RHLeaveReportsView` - URL existe mais peut être redondant
- `LeaveRequestEditView` - URL existe mais peut être non utilisé
- `LeaveRequestCancelView` - URL existe mais peut être non utilisé
- `LeaveBalanceDetailView` - URL existe mais peut être non utilisé
- `LeaveCalendarView` - URL existe mais peut être non utilisé
- `LeaveReportView` - URL existe mais commenté
- `LeaveTypeListView` - URL existe mais peut être non utilisé
- `LeaveTypeDetailView` - URL existe mais peut être non utilisé
- `HolidayListView` - URL existe mais peut être non utilisé
- `HolidayDetailView` - URL existe mais peut être non utilisé

### Dans `reports/views.py`
- `SystemSettingsView` - URL existe mais peut être non utilisé
- `ReportTemplateListView` - URL existe mais peut être non utilisé

### Dans `attendance/views.py`
- `AnomaliesManagementView` - URL existe mais anomalies désactivées
- Plusieurs vues de punch avec templates différents (punch_demo, punch_test, etc.)

---

## ⚠️ URLs NON UTILISÉES (Suspects)

### Dans `attendance/urls.py`
- `punch/original/` - Version originale (non utilisée)
- `punch/gps-test/` - Template de test
- `punch/demo/` - Template de démo
- `punch/test/` - Template de test
- `anomalies/` - Anomalies désactivées
- `gps-diagnostic/` - Diagnostic GPS
- `test-gps/` - Test GPS

### Dans `leave/urls.py`
- `manager/my-requests/` - Peut être redondant avec workflow
- `manager/validation/` - Peut être redondant avec workflow
- `rh/management/` - Peut être redondant avec workflow
- `rh/reports/` - Peut être redondant
- `requests/<pk>/edit/` - Peut être non utilisé
- `requests/<pk>/cancel/` - Peut être non utilisé
- `balances/<pk>/` - Peut être non utilisé
- `calendar/` - Peut être non utilisé
- `reports/` - Commenté
- `types/` et `types/<pk>/` - Peut être non utilisé
- `holidays/` et `holidays/<pk>/` - Peut être non utilisé

---

## 🔍 VÉRIFICATION DÉTAILLÉE À FAIRE

1. Vérifier chaque template dans les vues pour voir s'il est référencé
2. Vérifier chaque vue dans les URLs pour voir si elle est référencée
3. Vérifier les liens dans les templates pour voir quelles pages sont accessibles
4. Vérifier les redirections et les vues qui ne font que rediriger

---

## 📝 PROCHAINES ÉTAPES

1. Analyser chaque fichier views.py pour voir quels templates sont utilisés
2. Comparer avec les templates existants
3. Identifier les templates non référencés
4. Faire la même chose pour les vues et URLs

