"""
Vues pour l'export des rapports RH en PDF et Excel.

Conforme aux spécifications: MODULE 3 - Rapports RH
- Rapport Paie (heures travaillées + heures supplémentaires)
- Rapport Anomalies (tous types)
- Rapport Solde Congés (par employé)
"""

from django.http import HttpResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

# Imports pour PDF (reportlab)
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfgen import canvas

# Imports pour Excel (openpyxl)
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Imports modèles
from attendance.models import Attendance, AttendanceAnomaly
# OvertimeRecord sera ajouté dans Task 6 (Workflow heures sup)
from leave.models import LeaveBalance, LeaveRequest
from accounts.models import EmployeeProfile
from django.contrib.auth.models import User


class PayrollReportExportView(LoginRequiredMixin, View):
    """
    Export du Rapport de Paie en PDF ou Excel.
    
    Contenu:
    - Heures travaillées par employé
    - Heures supplémentaires (tous types)
    - Période du rapport
    - Totaux par employé et global
    """
    
    def get(self, request, format='pdf'):
        """
        Génère le rapport au format demandé.
        
        Args:
            format: 'pdf' ou 'excel'
        """
        # Récupérer les paramètres
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not start_date or not end_date:
            # Par défaut: mois en cours
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Récupérer les données
        data = self._get_payroll_data(start_date, end_date)
        
        # Générer selon le format
        if format == 'excel':
            return self._generate_excel(data, start_date, end_date)
        else:
            return self._generate_pdf(data, start_date, end_date)
    
    def _get_payroll_data(self, start_date, end_date):
        """Récupère les données de paie pour la période."""
        employees = User.objects.filter(
            employee_profile__is_active=True
        ).select_related('employee_profile')
        
        payroll_data = []
        
        for employee in employees:
            # Heures travaillées
            attendances = Attendance.objects.filter(
                employee=employee,
                date__gte=start_date,
                date__lte=end_date,
                punch_type='out'
            )
            
            total_hours = sum(
                (att.worked_hours or Decimal('0.00')) for att in attendances
            )
            
            # Heures supplémentaires (TODO: Implémenter OvertimeRecord dans Task 6)
            # Pour l'instant, calculer basé sur heures > 8h/jour
            overtime_hours = sum(
                max(Decimal('0.00'), (att.worked_hours or Decimal('0.00')) - Decimal('8.00'))
                for att in attendances
            )
            
            payroll_data.append({
                'employee_id': employee.employee_profile.employee_id,
                'name': employee.get_full_name() or employee.username,
                'department': employee.employee_profile.department.name if employee.employee_profile.department else 'N/A',
                'total_hours': float(total_hours),
                'overtime_hours': float(overtime_hours),
                'total_payable': float(total_hours + overtime_hours)
            })
        
        return payroll_data
    
    def _generate_pdf(self, data, start_date, end_date):
        """Génère le PDF du rapport de paie."""
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_paie_{start_date}_{end_date}.pdf"'
        
        # Créer le document PDF
        doc = SimpleDocTemplate(response, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=30,
            alignment=1  # Center
        )
        elements.append(Paragraph('📊 RAPPORT DE PAIE', title_style))
        elements.append(Paragraph(f'Période: {start_date.strftime("%d/%m/%Y")} - {end_date.strftime("%d/%m/%Y")}', styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Tableau des données
        table_data = [
            ['ID', 'Employé', 'Département', 'H. Travaillées', 'H. Sup.', 'Total Payable']
        ]
        
        for row in data:
            table_data.append([
                row['employee_id'],
                row['name'],
                row['department'],
                f"{row['total_hours']:.2f}h",
                f"{row['overtime_hours']:.2f}h",
                f"{row['total_payable']:.2f}h"
            ])
        
        # Ligne de total
        total_hours = sum(row['total_hours'] for row in data)
        total_overtime = sum(row['overtime_hours'] for row in data)
        total_payable = sum(row['total_payable'] for row in data)
        
        table_data.append([
            'TOTAL',
            '',
            '',
            f"{total_hours:.2f}h",
            f"{total_overtime:.2f}h",
            f"{total_payable:.2f}h"
        ])
        
        # Créer le tableau
        table = Table(table_data)
        table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            # Corps
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            # Ligne total
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fbbf24')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Statistiques
        elements.append(Paragraph(f'<b>Nombre d\'employés:</b> {len(data)}', styles['Normal']))
        elements.append(Paragraph(f'<b>Moyenne heures/employé:</b> {total_hours/len(data):.2f}h' if len(data) > 0 else '0h', styles['Normal']))
        
        # Construire le PDF
        doc.build(elements)
        return response
    
    def _generate_excel(self, data, start_date, end_date):
        """Génère le fichier Excel du rapport de paie."""
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="rapport_paie_{start_date}_{end_date}.xlsx"'
        
        # Créer le workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Rapport de Paie"
        
        # Styles
        header_fill = PatternFill(start_color="2563eb", end_color="2563eb", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        total_fill = PatternFill(start_color="fbbf24", end_color="fbbf24", fill_type="solid")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Titre
        ws['A1'] = '📊 RAPPORT DE PAIE'
        ws['A1'].font = Font(bold=True, size=16, color="2563eb")
        ws.merge_cells('A1:F1')
        
        ws['A2'] = f'Période: {start_date.strftime("%d/%m/%Y")} - {end_date.strftime("%d/%m/%Y")}'
        ws.merge_cells('A2:F2')
        
        # En-têtes
        headers = ['ID Employé', 'Nom', 'Département', 'H. Travaillées', 'H. Supplémentaires', 'Total Payable']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=4, column=col)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
        
        # Données
        for row_idx, row_data in enumerate(data, start=5):
            ws.cell(row=row_idx, column=1, value=row_data['employee_id']).border = border
            ws.cell(row=row_idx, column=2, value=row_data['name']).border = border
            ws.cell(row=row_idx, column=3, value=row_data['department']).border = border
            ws.cell(row=row_idx, column=4, value=row_data['total_hours']).border = border
            ws.cell(row=row_idx, column=5, value=row_data['overtime_hours']).border = border
            ws.cell(row=row_idx, column=6, value=row_data['total_payable']).border = border
        
        # Ligne de total
        total_row = len(data) + 5
        ws.cell(row=total_row, column=1, value='TOTAL').font = Font(bold=True)
        ws.cell(row=total_row, column=1).fill = total_fill
        ws.cell(row=total_row, column=4, value=sum(row['total_hours'] for row in data)).font = Font(bold=True)
        ws.cell(row=total_row, column=4).fill = total_fill
        ws.cell(row=total_row, column=5, value=sum(row['overtime_hours'] for row in data)).font = Font(bold=True)
        ws.cell(row=total_row, column=5).fill = total_fill
        ws.cell(row=total_row, column=6, value=sum(row['total_payable'] for row in data)).font = Font(bold=True)
        ws.cell(row=total_row, column=6).fill = total_fill
        
        # Ajuster largeur colonnes
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 18
        ws.column_dimensions['F'].width = 15
        
        # Sauvegarder
        wb.save(response)
        return response


class AnomalyReportExportView(LoginRequiredMixin, View):
    """
    Export du Rapport d'Anomalies en PDF ou Excel.
    
    Contenu:
    - Tous types d'anomalies détectées
    - Statut de résolution
    - Période du rapport
    """
    
    def get(self, request, format='pdf'):
        """Génère le rapport d'anomalies."""
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not start_date or not end_date:
            today = timezone.now().date()
            start_date = today - timedelta(days=30)
            end_date = today
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        data = self._get_anomaly_data(start_date, end_date)
        
        if format == 'excel':
            return self._generate_excel(data, start_date, end_date)
        else:
            return self._generate_pdf(data, start_date, end_date)
    
    def _get_anomaly_data(self, start_date, end_date):
        """Récupère les anomalies pour la période."""
        anomalies = AttendanceAnomaly.objects.filter(
            attendance__date__gte=start_date,
            attendance__date__lte=end_date
        ).select_related('attendance__employee')
        
        anomaly_data = []
        for anomaly in anomalies:
            anomaly_data.append({
                'date': anomaly.attendance.date.strftime('%d/%m/%Y'),
                'employee': anomaly.attendance.employee.get_full_name() or anomaly.attendance.employee.username,
                'type': anomaly.get_anomaly_type_display(),
                'status': anomaly.get_status_display(),
                'description': anomaly.description or 'N/A'
            })
        
        return anomaly_data
    
    def _generate_pdf(self, data, start_date, end_date):
        """Génère le PDF des anomalies."""
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_anomalies_{start_date}_{end_date}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#ef4444'),
            spaceAfter=30,
            alignment=1
        )
        elements.append(Paragraph('🚨 RAPPORT D\'ANOMALIES', title_style))
        elements.append(Paragraph(f'Période: {start_date.strftime("%d/%m/%Y")} - {end_date.strftime("%d/%m/%Y")}', styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Tableau
        table_data = [['Date', 'Employé', 'Type', 'Statut', 'Description']]
        
        for row in data:
            table_data.append([
                row['date'],
                row['employee'],
                row['type'],
                row['status'],
                row['description'][:30] + '...' if len(row['description']) > 30 else row['description']
            ])
        
        table = Table(table_data, colWidths=[70, 120, 100, 80, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ef4444')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f'<b>Total anomalies:</b> {len(data)}', styles['Normal']))
        
        doc.build(elements)
        return response
    
    def _generate_excel(self, data, start_date, end_date):
        """Génère l'Excel des anomalies."""
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="rapport_anomalies_{start_date}_{end_date}.xlsx"'
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Anomalies"
        
        # Titre
        ws['A1'] = '🚨 RAPPORT D\'ANOMALIES'
        ws['A1'].font = Font(bold=True, size=16, color="ef4444")
        ws.merge_cells('A1:E1')
        
        ws['A2'] = f'Période: {start_date.strftime("%d/%m/%Y")} - {end_date.strftime("%d/%m/%Y")}'
        ws.merge_cells('A2:E2')
        
        # En-têtes
        headers = ['Date', 'Employé', 'Type', 'Statut', 'Description']
        header_fill = PatternFill(start_color="ef4444", end_color="ef4444", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=4, column=col)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')
        
        # Données
        for row_idx, row_data in enumerate(data, start=5):
            ws.cell(row=row_idx, column=1, value=row_data['date'])
            ws.cell(row=row_idx, column=2, value=row_data['employee'])
            ws.cell(row=row_idx, column=3, value=row_data['type'])
            ws.cell(row=row_idx, column=4, value=row_data['status'])
            ws.cell(row=row_idx, column=5, value=row_data['description'])
        
        # Largeurs
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 25
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 40
        
        wb.save(response)
        return response


class LeaveBalanceReportExportView(LoginRequiredMixin, View):
    """
    Export du Rapport Solde de Congés en PDF ou Excel.
    
    Contenu:
    - Soldes par employé
    - Solde alloué vs pris
    - Solde restant
    """
    
    def get(self, request, format='pdf'):
        """Génère le rapport des soldes de congés."""
        year = int(request.GET.get('year', timezone.now().year))
        data = self._get_leave_balance_data(year)
        
        if format == 'excel':
            return self._generate_excel(data, year)
        else:
            return self._generate_pdf(data, year)
    
    def _get_leave_balance_data(self, year):
        """Récupère les soldes de congés."""
        balances = LeaveBalance.objects.filter(
            year=year
        ).select_related('employee', 'leave_type')
        
        balance_data = []
        for balance in balances:
            balance_data.append({
                'employee': balance.employee.get_full_name() or balance.employee.username,
                'leave_type': balance.leave_type.name,
                'allocated': float(balance.allocated_balance),
                'taken': float(balance.taken_balance),
                'remaining': float(balance.remaining_balance)
            })
        
        return balance_data
    
    def _generate_pdf(self, data, year):
        """Génère le PDF des soldes."""
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_solde_conges_{year}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#10b981'),
            spaceAfter=30,
            alignment=1
        )
        elements.append(Paragraph(f'📅 RAPPORT SOLDE DE CONGÉS - {year}', title_style))
        elements.append(Spacer(1, 20))
        
        # Tableau
        table_data = [['Employé', 'Type', 'Alloué', 'Pris', 'Restant']]
        
        for row in data:
            table_data.append([
                row['employee'],
                row['leave_type'],
                f"{row['allocated']:.1f}j",
                f"{row['taken']:.1f}j",
                f"{row['remaining']:.1f}j"
            ])
        
        table = Table(table_data, colWidths=[150, 100, 70, 70, 70])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f'<b>Total employés:</b> {len(set(row["employee"] for row in data))}', styles['Normal']))
        
        doc.build(elements)
        return response
    
    def _generate_excel(self, data, year):
        """Génère l'Excel des soldes."""
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="rapport_solde_conges_{year}.xlsx"'
        
        wb = Workbook()
        ws = wb.active
        ws.title = f"Soldes {year}"
        
        # Titre
        ws['A1'] = f'📅 RAPPORT SOLDE DE CONGÉS - {year}'
        ws['A1'].font = Font(bold=True, size=16, color="10b981")
        ws.merge_cells('A1:E1')
        
        # En-têtes
        headers = ['Employé', 'Type de Congé', 'Alloué (jours)', 'Pris (jours)', 'Restant (jours)']
        header_fill = PatternFill(start_color="10b981", end_color="10b981", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=col)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')
        
        # Données
        for row_idx, row_data in enumerate(data, start=4):
            ws.cell(row=row_idx, column=1, value=row_data['employee'])
            ws.cell(row=row_idx, column=2, value=row_data['leave_type'])
            ws.cell(row=row_idx, column=3, value=row_data['allocated'])
            ws.cell(row=row_idx, column=4, value=row_data['taken'])
            ws.cell(row=row_idx, column=5, value=row_data['remaining'])
        
        # Largeurs
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
        
        wb.save(response)
        return response
