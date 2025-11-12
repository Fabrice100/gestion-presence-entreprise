"""
Vues pour l'export des rapports RH en PDF et Excel.

Conforme aux spécifications: MODULE 3 - Rapports RH
- Rapport Heures travaillées (sans heures supplémentaires)
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
from attendance.models import Attendance
from leave.models import LeaveBalance, LeaveRequest
from accounts.models import EmployeeProfile
from django.contrib.auth.models import User


class PayrollReportExportView(LoginRequiredMixin, View):
    """
    Export du Rapport d'Heures travaillées (sans heures supplémentaires) en PDF ou Excel.
    """
    
    def get(self, request, format='pdf'):
        """Génère le rapport au format demandé (pdf ou excel)."""
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
        """Récupère les heures travaillées pour la période (sans heures sup)."""
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
            
            payroll_data.append({
                'employee_id': employee.employee_profile.employee_id,
                'name': employee.get_full_name() or employee.username,
                'department': employee.employee_profile.department.name if employee.employee_profile.department else 'N/A',
                'total_hours': float(total_hours),
            })
        
        return payroll_data
    
    def _generate_pdf(self, data, start_date, end_date):
        """Génère le PDF du rapport d'heures travaillées."""
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_heures_{start_date}_{end_date}.pdf"'
        
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
        elements.append(Paragraph('⏱️ RAPPORT HEURES TRAVAILLÉES', title_style))
        elements.append(Paragraph(f'Période: {start_date.strftime("%d/%m/%Y")} - {end_date.strftime("%d/%m/%Y")}', styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Tableau des données
        table_data = [
            ['ID', 'Employé', 'Département', 'Heures Travaillées']
        ]
        
        for row in data:
            table_data.append([
                row['employee_id'],
                row['name'],
                row['department'],
                f"{row['total_hours']:.2f}h",
            ])
        
        # Pas de ligne TOTAL (exigence PME)
        
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
        elements.append(Paragraph(f"<b>Nombre d'employés:</b> {len(data)}", styles['Normal']))
        elements.append(Paragraph(f"<b>Moyenne heures/employé:</b> {total_hours/len(data):.2f}h" if len(data) > 0 else '0h', styles['Normal']))
        
        # Construire le PDF
        doc.build(elements)
        return response
    
    def _generate_excel(self, data, start_date, end_date):
        """Génère le fichier Excel des heures travaillées."""
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="rapport_heures_{start_date}_{end_date}.xlsx"'
        
        # Créer le workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Rapport Heures"
        
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
        ws['A1'] = '⏱️ RAPPORT HEURES TRAVAILLÉES'
        ws['A1'].font = Font(bold=True, size=16, color="2563eb")
        ws.merge_cells('A1:D1')
        
        ws['A2'] = f'Période: {start_date.strftime("%d/%m/%Y")} - {end_date.strftime("%d/%m/%Y")}'
        ws.merge_cells('A2:D2')
        
        # En-têtes
        headers = ['ID Employé', 'Nom', 'Département', 'Heures Travaillées']
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
        
        # Pas de ligne TOTAL (exigence PME)
        
        # Ajuster largeur colonnes
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 18
        
        # Sauvegarder
        wb.save(response)
        return response


# ============================================================================
# EXPORTS DÉSACTIVÉS - Non utilisés actuellement
# ============================================================================

"""
# Export d'Anomalies - DÉSACTIVÉ
# class AnomalyReportExportView(LoginRequiredMixin, View):
#     ... (code commenté pour économiser l'espace)
#     Réactiver si besoin en décommentant cette classe
"""


"""
# Export de Soldes de Congés - DÉSACTIVÉ
# class LeaveBalanceReportExportView(LoginRequiredMixin, View):
#     ... (code commenté pour économiser l'espace)
#     Réactiver si besoin en décommentant cette classe
"""
