"""
Services d'export pour les rapports.

Ce module contient les services pour :
- Export PDF avec ReportLab
- Export Excel avec OpenPyXL
- Génération de rapports professionnels

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

import os
import tempfile
from datetime import datetime, date
from io import BytesIO

from django.http import HttpResponse
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from .report_views import AttendanceReportView, LeaveReportView, AnomalyReportView


class PDFExportService:
    """Service pour l'export PDF des rapports."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Configure les styles personnalisés."""
        # Style pour le titre principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50')
        ))
        
        # Style pour les sous-titres
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e')
        ))
        
        # Style pour le texte normal
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def export_attendance_report(self, request, start_date, end_date, department_id=None, employee_id=None):
        """Export du rapport de présence en PDF."""
        # Récupérer les données
        view = AttendanceReportView()
        view.request = request
        view.get_context_data()
        
        # Créer le PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
        story = []
        
        # Titre
        story.append(Paragraph("RAPPORT DE PRÉSENCE", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        
        # Informations du rapport
        info_data = [
            ['Période', f"Du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}"],
            ['Généré le', datetime.now().strftime('%d/%m/%Y à %H:%M')],
            ['Généré par', request.user.get_full_name() or request.user.username],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Statistiques générales
        story.append(Paragraph("STATISTIQUES GÉNÉRALES", self.styles['CustomHeading']))
        
        # Récupérer les données de présence
        from accounts.models import EmployeeProfile
        from attendance.models import Attendance
        
        if request.user.employee_profile.role == 'rh_dg':
            employees = EmployeeProfile.objects.filter(is_active=True).exclude(role__in=['admin', 'rh_dg'])
            if department_id:
                employees = employees.filter(department_id=department_id)
        elif request.user.employee_profile.role == 'manager':
            employees = EmployeeProfile.objects.filter(
                manager=request.user,
                is_active=True
            )
        else:
            employees = EmployeeProfile.objects.filter(user=request.user)
        
        # Calculer les statistiques
        total_employees = employees.count()
        period_days = (end_date - start_date).days + 1
        
        # Tableau des statistiques
        stats_data = [
            ['Métrique', 'Valeur'],
            ['Nombre d\'employés', str(total_employees)],
            ['Période analysée', f"{period_days} jours"],
            ['Date de début', start_date.strftime('%d/%m/%Y')],
            ['Date de fin', end_date.strftime('%d/%m/%Y')],
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # Détail par employé
        story.append(Paragraph("DÉTAIL PAR EMPLOYÉ", self.styles['CustomHeading']))
        
        # En-tête du tableau
        header_data = [['Employé', 'Département', 'Présents', 'Absents', 'Taux %']]
        
        # Données des employés
        employee_data = []
        for employee in employees:
            # Calculer les présences
            attendances = Attendance.objects.filter(
                employee=employee.user,
                date__range=[start_date, end_date],
                punch_type='in'
            )
            present_days = attendances.count()
            absent_days = period_days - present_days
            attendance_rate = (present_days / period_days * 100) if period_days > 0 else 0
            
            employee_data.append([
                employee.user.get_full_name() or employee.user.username,
                employee.department.name if employee.department else 'Non assigné',
                str(present_days),
                str(absent_days),
                f"{attendance_rate:.1f}%"
            ])
        
        # Créer le tableau
        table_data = header_data + employee_data
        employee_table = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1*inch, 1*inch])
        employee_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(employee_table)
        
        # Construire le PDF
        doc.build(story)
        
        # Retourner la réponse
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_presence_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.pdf"'
        return response
    
    def export_leave_report(self, request, year, leave_type_id=None, status=None):
        """Export du rapport de congés en PDF."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
        story = []
        
        # Titre
        story.append(Paragraph("RAPPORT DE CONGÉS", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        
        # Informations du rapport
        info_data = [
            ['Année', str(year)],
            ['Généré le', datetime.now().strftime('%d/%m/%Y à %H:%M')],
            ['Généré par', request.user.get_full_name() or request.user.username],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Récupérer les données de congés
        from leave.models import LeaveRequest
        
        if request.user.employee_profile.role == 'rh_dg':
            leave_requests = LeaveRequest.objects.filter(start_date__year=year)
        elif request.user.employee_profile.role == 'manager':
            managed_employees = request.user.employee_profile.get_managed_employees()
            leave_requests = LeaveRequest.objects.filter(
                employee__in=managed_employees,
                start_date__year=year
            )
        else:
            leave_requests = LeaveRequest.objects.filter(
                employee=request.user,
                start_date__year=year
            )
        
        if leave_type_id:
            leave_requests = leave_requests.filter(leave_type_id=leave_type_id)
        if status:
            leave_requests = leave_requests.filter(status=status)
        
        # Statistiques
        total_requests = leave_requests.count()
        approved_requests = leave_requests.filter(status__in=['approved_manager', 'approved_rh']).count()
        pending_requests = leave_requests.filter(status='pending').count()
        rejected_requests = leave_requests.filter(status__in=['rejected_manager', 'rejected_rh']).count()
        
        story.append(Paragraph("STATISTIQUES", self.styles['CustomHeading']))
        
        stats_data = [
            ['Métrique', 'Valeur'],
            ['Total demandes', str(total_requests)],
            ['Demandes approuvées', str(approved_requests)],
            ['En attente', str(pending_requests)],
            ['Rejetées', str(rejected_requests)],
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # Détail des demandes
        story.append(Paragraph("DÉTAIL DES DEMANDES", self.styles['CustomHeading']))
        
        # En-tête
        header_data = [['Employé', 'Type', 'Période', 'Durée', 'Statut']]
        
        # Données
        request_data = []
        for req in leave_requests[:50]:  # Limiter à 50 pour éviter les PDF trop longs
            request_data.append([
                req.employee.get_full_name() or req.employee.username,
                req.leave_type.name,
                f"{req.start_date.strftime('%d/%m')} - {req.end_date.strftime('%d/%m/%Y')}",
                f"{req.duration_days} jour(s)",
                req.get_status_display()
            ])
        
        table_data = header_data + request_data
        request_table = Table(table_data, colWidths=[2*inch, 1.5*inch, 2*inch, 1*inch, 1.5*inch])
        request_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(request_table)
        
        # Construire le PDF
        doc.build(story)
        
        # Retourner la réponse
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_conges_{year}.pdf"'
        return response


class ExcelExportService:
    """Service pour l'export Excel des rapports."""
    
    def export_attendance_report(self, request, start_date, end_date, department_id=None, employee_id=None):
        """Export du rapport de présence en Excel."""
        # Créer le workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Rapport de Présence"
        
        # Styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
        subheader_font = Font(bold=True, color="2C3E50")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Titre
        ws.merge_cells('A1:F1')
        ws['A1'] = f"RAPPORT DE PRÉSENCE - {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}"
        ws['A1'].font = Font(bold=True, size=16, color="2C3E50")
        ws['A1'].alignment = Alignment(horizontal='center')
        
        # Informations du rapport
        ws['A3'] = "Informations du rapport"
        ws['A3'].font = subheader_font
        
        info_data = [
            ['Période', f"Du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}"],
            ['Généré le', datetime.now().strftime('%d/%m/%Y à %H:%M')],
            ['Généré par', request.user.get_full_name() or request.user.username],
        ]
        
        for i, (label, value) in enumerate(info_data, 4):
            ws[f'A{i}'] = label
            ws[f'B{i}'] = value
            ws[f'A{i}'].font = Font(bold=True)
        
        # Récupérer les données
        from accounts.models import EmployeeProfile
        from attendance.models import Attendance
        
        if request.user.employee_profile.role == 'rh_dg':
            employees = EmployeeProfile.objects.filter(is_active=True).exclude(role__in=['admin', 'rh_dg'])
            if department_id:
                employees = employees.filter(department_id=department_id)
        elif request.user.employee_profile.role == 'manager':
            employees = EmployeeProfile.objects.filter(
                manager=request.user,
                is_active=True
            )
        else:
            employees = EmployeeProfile.objects.filter(user=request.user)
        
        # En-tête du tableau
        row = 8
        headers = ['Employé', 'Département', 'Jours présents', 'Jours absents', 'Taux présence', 'Heures estimées']
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        
        # Données des employés
        period_days = (end_date - start_date).days + 1
        
        for employee in employees:
            row += 1
            
            # Calculer les présences
            attendances = Attendance.objects.filter(
                employee=employee.user,
                date__range=[start_date, end_date],
                punch_type='in'
            )
            present_days = attendances.count()
            absent_days = period_days - present_days
            attendance_rate = (present_days / period_days * 100) if period_days > 0 else 0
            estimated_hours = present_days * 8  # Estimation 8h/jour
            
            data = [
                employee.user.get_full_name() or employee.user.username,
                employee.department.name if employee.department else 'Non assigné',
                present_days,
                absent_days,
                f"{attendance_rate:.1f}%",
                estimated_hours
            ]
            
            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = border
                if col in [3, 4, 6]:  # Colonnes numériques
                    cell.alignment = Alignment(horizontal='center')
        
        # Ajuster la largeur des colonnes
        column_widths = [25, 20, 15, 15, 15, 15]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width
        
        # Sauvegarder
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="rapport_presence_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.xlsx"'
        
        wb.save(response)
        return response
    
    def export_leave_report(self, request, year, leave_type_id=None, status=None):
        """Export du rapport de congés en Excel."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Rapport de Congés"
        
        # Styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="27AE60", end_color="27AE60", fill_type="solid")
        subheader_font = Font(bold=True, color="27AE60")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Titre
        ws.merge_cells('A1:F1')
        ws['A1'] = f"RAPPORT DE CONGÉS - {year}"
        ws['A1'].font = Font(bold=True, size=16, color="27AE60")
        ws['A1'].alignment = Alignment(horizontal='center')
        
        # Informations
        ws['A3'] = "Informations du rapport"
        ws['A3'].font = subheader_font
        
        info_data = [
            ['Année', str(year)],
            ['Généré le', datetime.now().strftime('%d/%m/%Y à %H:%M')],
            ['Généré par', request.user.get_full_name() or request.user.username],
        ]
        
        for i, (label, value) in enumerate(info_data, 4):
            ws[f'A{i}'] = label
            ws[f'B{i}'] = value
            ws[f'A{i}'].font = Font(bold=True)
        
        # Récupérer les données
        from leave.models import LeaveRequest
        
        if request.user.employee_profile.role == 'rh_dg':
            leave_requests = LeaveRequest.objects.filter(start_date__year=year)
        elif request.user.employee_profile.role == 'manager':
            managed_employees = request.user.employee_profile.get_managed_employees()
            leave_requests = LeaveRequest.objects.filter(
                employee__in=managed_employees,
                start_date__year=year
            )
        else:
            leave_requests = LeaveRequest.objects.filter(
                employee=request.user,
                start_date__year=year
            )
        
        if leave_type_id:
            leave_requests = leave_requests.filter(leave_type_id=leave_type_id)
        if status:
            leave_requests = leave_requests.filter(status=status)
        
        # En-tête du tableau
        row = 8
        headers = ['Employé', 'Type de congé', 'Date début', 'Date fin', 'Durée', 'Statut']
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        
        # Données
        for req in leave_requests:
            row += 1
            
            data = [
                req.employee.get_full_name() or req.employee.username,
                req.leave_type.name,
                req.start_date.strftime('%d/%m/%Y'),
                req.end_date.strftime('%d/%m/%Y'),
                req.duration_days,
                req.get_status_display()
            ]
            
            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = border
                if col in [3, 4, 5]:  # Colonnes de dates et durée
                    cell.alignment = Alignment(horizontal='center')
        
        # Ajuster la largeur des colonnes
        column_widths = [25, 20, 12, 12, 10, 20]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width
        
        # Sauvegarder
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="rapport_conges_{year}.xlsx"'
        
        wb.save(response)
        return response


# Service supprimé - export inutile
class _EmployeeExportService:
    """Service pour l'export des listes d'employés."""
    
    def export_employees_list_excel(self, request):
        """Export de la liste des employés en Excel."""
        from accounts.models import EmployeeProfile
        
        # Récupérer les employés (exclure admin et rh_dg)
        employees = EmployeeProfile.objects.select_related('user', 'department', 'manager').filter(
            is_active=True
        ).exclude(role__in=['admin', 'rh_dg']).order_by('employee_id')
        
        # Créer le workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Liste des Employés"
        
        # Styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="2E86AB", end_color="2E86AB", fill_type="solid")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Titre
        ws.merge_cells('A1:H1')
        title_cell = ws['A1']
        title_cell.value = "LISTE DES EMPLOYÉS"
        title_cell.font = Font(size=16, bold=True, color="2E86AB")
        title_cell.alignment = Alignment(horizontal='center')
        
        # Informations du rapport
        ws['A3'] = "Généré le:"
        ws['B3'] = datetime.now().strftime('%d/%m/%Y à %H:%M')
        ws['A4'] = "Généré par:"
        ws['B4'] = request.user.get_full_name() or request.user.username
        ws['A5'] = "Total employés:"
        ws['B5'] = employees.count()
        
        # En-têtes du tableau
        headers = ['ID Employé', 'Nom', 'Prénom', 'Email', 'Département', 'Rôle', 'Manager', 'Date embauche']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=7, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = border
        
        # Données des employés
        for row, employee in enumerate(employees, 8):
            ws.cell(row=row, column=1, value=employee.employee_id).border = border
            ws.cell(row=row, column=2, value=employee.user.last_name).border = border
            ws.cell(row=row, column=3, value=employee.user.first_name).border = border
            ws.cell(row=row, column=4, value=employee.user.email).border = border
            ws.cell(row=row, column=5, value=employee.department.name if employee.department else '').border = border
            ws.cell(row=row, column=6, value=employee.get_role_display()).border = border
            ws.cell(row=row, column=7, value=f"{employee.manager.get_full_name()}" if employee.manager else '').border = border
            ws.cell(row=row, column=8, value=employee.user.date_joined.strftime('%d/%m/%Y')).border = border
        
        # Ajuster la largeur des colonnes
        column_widths = [15, 20, 20, 30, 20, 15, 25, 15]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width
        
        # Réponse HTTP
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"liste_employes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        wb.save(response)
        return response
    
    def export_employees_list_csv(self, request):
        """Export de la liste des employés en CSV."""
        import csv
        from accounts.models import EmployeeProfile
        
        # Récupérer les employés
        employees = EmployeeProfile.objects.select_related('user', 'department', 'manager').filter(
            is_active=True
        ).exclude(role__in=['admin', 'rh_dg']).order_by('employee_id')
        
        response = HttpResponse(content_type='text/csv')
        filename = f"liste_employes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # En-têtes
        writer.writerow(['ID Employé', 'Nom', 'Prénom', 'Email', 'Département', 'Rôle', 'Manager', 'Date embauche'])
        
        # Données
        for employee in employees:
            writer.writerow([
                employee.employee_id,
                employee.user.last_name,
                employee.user.first_name,
                employee.user.email,
                employee.department.name if employee.department else '',
                employee.get_role_display(),
                f"{employee.manager.get_full_name()}" if employee.manager else '',
                employee.user.date_joined.strftime('%d/%m/%Y')
            ])
        
        return response


# Service supprimé - export inutile  
class _AttendanceExportService:
    """Service pour l'export des données de présence."""
    
    def export_attendance_data_excel(self, request, start_date, end_date, department_id=None, employee_id=None):
        """Export des données de présence en Excel."""
        from attendance.models import Attendance
        
        # Construire la requête
        queryset = Attendance.objects.select_related(
            'employee__employee_profile__department',
            'employee__employee_profile'
        ).filter(date__range=[start_date, end_date])
        
        # Filtres
        if department_id:
            queryset = queryset.filter(employee__employee_profile__department_id=department_id)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Créer le workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Données de Présence"
        
        # Styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="E74C3C", end_color="E74C3C", fill_type="solid")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Titre
        ws.merge_cells('A1:F1')
        title_cell = ws['A1']
        title_cell.value = "DONNÉES DE PRÉSENCE"
        title_cell.font = Font(size=16, bold=True, color="E74C3C")
        title_cell.alignment = Alignment(horizontal='center')
        
        # Informations du rapport
        ws['A3'] = "Période:"
        ws['B3'] = f"Du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}"
        ws['A4'] = "Généré le:"
        ws['B4'] = datetime.now().strftime('%d/%m/%Y à %H:%M')
        ws['A5'] = "Généré par:"
        ws['B5'] = request.user.get_full_name() or request.user.username
        
        # En-têtes du tableau
        headers = ['Date', 'Employé', 'ID Employé', 'Type', 'Heure', 'Département']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=7, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = border
        
        # Données des présences
        for row, attendance in enumerate(queryset.order_by('date', 'employee__last_name'), 8):
            ws.cell(row=row, column=1, value=attendance.date.strftime('%d/%m/%Y')).border = border
            ws.cell(row=row, column=2, value=attendance.employee.get_full_name()).border = border
            ws.cell(row=row, column=3, value=attendance.employee.employee_profile.employee_id).border = border
            ws.cell(row=row, column=4, value=attendance.get_punch_type_display()).border = border
            ws.cell(row=row, column=5, value=attendance.time.strftime('%H:%M')).border = border
            ws.cell(row=row, column=6, value=attendance.employee.employee_profile.department.name if attendance.employee.employee_profile.department else '').border = border
        
        # Ajuster la largeur des colonnes
        column_widths = [12, 25, 15, 12, 10, 20]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width
        
        # Réponse HTTP
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"presences_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        wb.save(response)
        return response

