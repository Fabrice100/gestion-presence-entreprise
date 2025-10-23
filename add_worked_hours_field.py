"""
Script pour ajouter le champ worked_hours à la table attendance_attendance
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.db import connection

# Ajouter la colonne worked_hours
with connection.cursor() as cursor:
    try:
        cursor.execute("""
            ALTER TABLE attendance_attendance 
            ADD COLUMN IF NOT EXISTS worked_hours NUMERIC(5, 2) NULL;
        """)
        print("✅ Colonne 'worked_hours' ajoutée avec succès !")
    except Exception as e:
        print(f"ℹ️ La colonne existe peut-être déjà : {e}")
    
    # Vérifier si la colonne existe
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'attendance_attendance' 
        AND column_name = 'worked_hours';
    """)
    result = cursor.fetchone()
    
    if result:
        print(f"✅ Vérification : worked_hours | {result[1]} | nullable: {result[2]}")
    else:
        print("❌ La colonne n'a pas été trouvée !")
