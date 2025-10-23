-- Ajouter le champ worked_hours à la table attendance
ALTER TABLE attendance_attendance 
ADD COLUMN IF NOT EXISTS worked_hours NUMERIC(5, 2) NULL;

-- Vérifier que la colonne a été ajoutée
\d attendance_attendance
