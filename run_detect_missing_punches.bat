@echo off
REM ========================================================================
REM Script de détection automatique des oublis de pointage
REM À exécuter quotidiennement via Windows Task Scheduler
REM ========================================================================

REM Définir le chemin vers Python et le projet
set PYTHON_PATH=python
set PROJECT_PATH=C:\Users\HUSUNUKPE Fabrice\Desktop\mon_projet\attendance_system

REM Créer un dossier pour les logs s'il n'existe pas
if not exist "%PROJECT_PATH%\logs" mkdir "%PROJECT_PATH%\logs"

REM Nom du fichier log avec la date
set LOG_FILE=%PROJECT_PATH%\logs\detect_missing_punches_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log

REM Se déplacer dans le dossier du projet
cd /d "%PROJECT_PATH%"

REM Afficher le début de l'exécution dans le log
echo ======================================================================== >> "%LOG_FILE%"
echo Execution: %date% %time% >> "%LOG_FILE%"
echo ======================================================================== >> "%LOG_FILE%"

REM Exécuter la commande Django avec notifications
%PYTHON_PATH% manage.py detect_missing_punches --notify --verbose >> "%LOG_FILE%" 2>&1

REM Afficher le code de retour
echo. >> "%LOG_FILE%"
echo Code de retour: %ERRORLEVEL% >> "%LOG_FILE%"
echo ======================================================================== >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM Code de retour
exit /b %ERRORLEVEL%
