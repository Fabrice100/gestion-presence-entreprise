-- Script de configuration PostgreSQL pour le système de gestion de présence
-- À exécuter en tant que superuser PostgreSQL (postgres)

-- Créer l'utilisateur
CREATE USER attendance_user WITH PASSWORD 'attendance_pass_2025';

-- Créer la base de données
CREATE DATABASE attendance_db
    WITH 
    OWNER = attendance_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'French_France.1252'
    LC_CTYPE = 'French_France.1252'
    TEMPLATE = template0;

-- Donner tous les privilèges à l'utilisateur sur cette base
GRANT ALL PRIVILEGES ON DATABASE attendance_db TO attendance_user;

-- Se connecter à la base de données
\c attendance_db

-- Donner les privilèges sur le schéma public
GRANT ALL ON SCHEMA public TO attendance_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO attendance_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO attendance_user;

-- Permissions par défaut pour les futures tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO attendance_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO attendance_user;

-- Afficher le résultat
\l attendance_db
\du attendance_user
