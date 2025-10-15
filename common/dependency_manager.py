"""
Gestionnaire de dépendances et versions pour le système de gestion de présence.

Ce module respecte les principes SOLID en centralisant la gestion des versions
et en fournissant des utilitaires pour maintenir la cohérence des dépendances.

Auteur: Système de Gestion de Présence
Version: 2.0 (Refactorisé)
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re


class DependencyAnalyzer:
    """
    Analyseur de dépendances respectant le Single Responsibility Principle.
    
    Se concentre uniquement sur l'analyse des dépendances installées vs requises.
    """
    
    def __init__(self, requirements_file: str = "requirements.txt"):
        """
        Initialise l'analyseur avec le fichier de requirements.
        
        Args:
            requirements_file: Chemin vers le fichier requirements.txt
        """
        self.requirements_file = Path(requirements_file)
        self.installed_packages = {}
        self.required_packages = {}
        
    def get_installed_packages(self) -> Dict[str, str]:
        """
        Récupère la liste des packages installés avec leurs versions.
        
        Returns:
            Dict mapping nom_package -> version
        """
        if self.installed_packages:
            return self.installed_packages
            
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=freeze'],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.strip().split('\n'):
                if '==' in line:
                    name, version = line.split('==', 1)
                    self.installed_packages[name.lower()] = version
                    
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de la récupération des packages: {e}")
            
        return self.installed_packages
    
    def parse_requirements(self) -> Dict[str, str]:
        """
        Parse le fichier requirements.txt.
        
        Returns:
            Dict mapping nom_package -> version_requise
        """
        if self.required_packages or not self.requirements_file.exists():
            return self.required_packages
            
        try:
            with open(self.requirements_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Ignorer les commentaires et lignes vides
                    if line and not line.startswith('#'):
                        # Parser les formats courants: package==version
                        match = re.match(r'^([a-zA-Z0-9\-_\.]+)==([0-9\.]+(?:[a-zA-Z0-9\-\_\.]*)?)', line)
                        if match:
                            name, version = match.groups()
                            self.required_packages[name.lower()] = version
                            
        except Exception as e:
            print(f"❌ Erreur lors du parsing de {self.requirements_file}: {e}")
            
        return self.required_packages
    
    def find_version_conflicts(self) -> List[Tuple[str, str, str]]:
        """
        Trouve les conflits de versions entre installé et requis.
        
        Returns:
            Liste de tuples (package, version_installée, version_requise)
        """
        installed = self.get_installed_packages()
        required = self.parse_requirements()
        
        conflicts = []
        
        for pkg_name, required_version in required.items():
            installed_version = installed.get(pkg_name)
            
            if installed_version and installed_version != required_version:
                conflicts.append((pkg_name, installed_version, required_version))
                
        return conflicts
    
    def find_missing_packages(self) -> List[Tuple[str, str]]:
        """
        Trouve les packages requis mais non installés.
        
        Returns:
            Liste de tuples (package, version_requise)
        """
        installed = self.get_installed_packages()
        required = self.parse_requirements()
        
        missing = []
        
        for pkg_name, required_version in required.items():
            if pkg_name not in installed:
                missing.append((pkg_name, required_version))
                
        return missing
    
    def get_django_version_info(self) -> Dict[str, Optional[str]]:
        """
        Analyse spécifique pour Django.
        
        Returns:
            Dict avec les informations de version Django
        """
        info = {
            'installed': None,
            'required': None,
            'in_migrations': [],
            'conflict': False
        }
        
        # Version installée
        installed = self.get_installed_packages()
        info['installed'] = installed.get('django')
        
        # Version requise
        required = self.parse_requirements()
        info['required'] = required.get('django')
        
        # Vérifier les migrations
        info['in_migrations'] = self.scan_migrations_for_django_versions()
        
        # Détecter les conflits
        if info['installed'] and info['required']:
            info['conflict'] = info['installed'] != info['required']
            
        return info
    
    def scan_migrations_for_django_versions(self) -> List[str]:
        """
        Scanne les migrations pour détecter les versions Django utilisées.
        
        Returns:
            Liste des versions Django trouvées dans les migrations
        """
        versions = set()
        
        # Chercher dans tous les dossiers de migrations
        for migration_dir in Path('.').glob('*/migrations/'):
            for migration_file in migration_dir.glob('*.py'):
                try:
                    with open(migration_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Chercher les lignes "# Generated by Django X.Y.Z"
                        matches = re.findall(r'# Generated by Django ([0-9\.]+)', content)
                        versions.update(matches)
                except Exception:
                    continue  # Ignorer les erreurs de lecture
                    
        return sorted(list(versions))


class DependencyUpdater:
    """
    Gestionnaire de mise à jour des dépendances.
    
    Respecte l'Open/Closed Principle en permettant l'extension
    sans modification du code existant.
    """
    
    def __init__(self, target_django_version: str = "4.2.16"):
        """
        Initialise l'updater avec une version Django cible.
        
        Args:
            target_django_version: Version Django à utiliser
        """
        self.target_django_version = target_django_version
        self.compatible_versions = self._get_compatible_versions()
    
    def _get_compatible_versions(self) -> Dict[str, str]:
        """
        Définit les versions compatibles avec Django 4.2.16 (LTS).
        
        Returns:
            Dict des versions recommandées
        """
        return {
            'django': '4.2.16',  # Version LTS stable
            'django-crispy-forms': '2.3',
            'crispy-bootstrap5': '2024.2',
            'psycopg2-binary': '2.9.9',
            'python-decouple': '3.8',
            'django-debug-toolbar': '4.4.6',
            'pytest': '8.3.3',
            'pytest-django': '4.9.0',
            'coverage': '7.6.1',
            'gunicorn': '23.0.0',
            'whitenoise': '6.7.0',
            'python-dateutil': '2.9.0',
            'reportlab': '4.2.5',
            'openpyxl': '3.1.5',
        }
    
    def generate_updated_requirements(self) -> str:
        """
        Génère un fichier requirements.txt mis à jour et sécurisé.
        
        Returns:
            Contenu du nouveau fichier requirements.txt
        """
        content = f"""# ===================================================================
# DÉPENDANCES - SYSTÈME DE GESTION DE PRÉSENCE
# ===================================================================
# Fichier généré automatiquement avec versions compatibles
# Django {self.target_django_version} LTS (Support Long Terme)
# Dernière mise à jour: {self._get_current_date()}

# ==========================================
# FRAMEWORK PRINCIPAL
# ==========================================
Django=={self.compatible_versions['django']}

# ==========================================
# INTERFACE UTILISATEUR
# ==========================================
django-crispy-forms=={self.compatible_versions['django-crispy-forms']}
crispy-bootstrap5=={self.compatible_versions['crispy-bootstrap5']}

# ==========================================
# BASE DE DONNÉES
# ==========================================
psycopg2-binary=={self.compatible_versions['psycopg2-binary']}

# ==========================================
# CONFIGURATION & ENVIRONNEMENT
# ==========================================
python-decouple=={self.compatible_versions['python-decouple']}

# ==========================================
# DÉVELOPPEMENT & DÉBOGAGE
# ==========================================
django-debug-toolbar=={self.compatible_versions['django-debug-toolbar']}

# ==========================================
# TESTS & QUALITÉ
# ==========================================
pytest=={self.compatible_versions['pytest']}
pytest-django=={self.compatible_versions['pytest-django']}
coverage=={self.compatible_versions['coverage']}

# ==========================================
# PRODUCTION & DÉPLOIEMENT
# ==========================================
gunicorn=={self.compatible_versions['gunicorn']}
whitenoise=={self.compatible_versions['whitenoise']}

# ==========================================
# UTILITAIRES
# ==========================================
python-dateutil=={self.compatible_versions['python-dateutil']}

# ==========================================
# EXPORT & RAPPORTS
# ==========================================
reportlab=={self.compatible_versions['reportlab']}
openpyxl=={self.compatible_versions['openpyxl']}

# ==========================================
# NOTES DE VERSION
# ==========================================
# Django 4.2.16 : Version LTS avec support jusqu'en avril 2026
# Toutes les versions sont testées et compatibles
# Mise à jour sécurisée sans breaking changes
"""
        return content
    
    def _get_current_date(self) -> str:
        """Retourne la date actuelle formatée."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def create_backup_requirements(self, original_file: str) -> str:
        """
        Crée une sauvegarde du fichier requirements existant.
        
        Args:
            original_file: Chemin vers le fichier original
            
        Returns:
            Chemin vers le fichier de sauvegarde
        """
        import time
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        backup_file = f"{original_file}.backup_{timestamp}"
        
        try:
            if Path(original_file).exists():
                Path(original_file).rename(backup_file)
                print(f"💾 Sauvegarde créée: {backup_file}")
            return backup_file
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return ""


class MigrationCleaner:
    """
    Nettoyeur de migrations pour résoudre les incohérences de versions.
    
    Interface Segregation Principle : Se concentre uniquement sur les migrations.
    """
    
    def __init__(self):
        self.migration_dirs = self._find_migration_directories()
    
    def _find_migration_directories(self) -> List[Path]:
        """Trouve tous les répertoires de migrations."""
        return list(Path('.').glob('*/migrations/'))
    
    def analyze_migration_versions(self) -> Dict[str, List[str]]:
        """
        Analyse les versions Django dans les migrations.
        
        Returns:
            Dict mapping app_name -> liste_versions_django
        """
        results = {}
        
        for migration_dir in self.migration_dirs:
            app_name = migration_dir.parent.name
            versions = []
            
            for migration_file in migration_dir.glob('*.py'):
                if migration_file.name == '__init__.py':
                    continue
                    
                try:
                    with open(migration_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Chercher "# Generated by Django X.Y.Z"
                        matches = re.findall(r'# Generated by Django ([0-9\.]+)', content)
                        versions.extend(matches)
                except Exception:
                    continue
            
            if versions:
                results[app_name] = list(set(versions))  # Unique versions
                
        return results
    
    def suggest_migration_strategy(self) -> str:
        """
        Suggère une stratégie pour nettoyer les migrations.
        
        Returns:
            Texte avec les recommandations
        """
        analysis = self.analyze_migration_versions()
        
        if not analysis:
            return "✅ Aucune migration détectée nécessitant un nettoyage."
        
        strategy = """
🔧 STRATÉGIE DE NETTOYAGE DES MIGRATIONS

Options recommandées :

1. 📚 OPTION CONSERVATIVE (Recommandée) :
   - Garder les migrations existantes
   - Créer de nouvelles migrations avec Django unifié
   - Tester sur une copie de la base de données

2. 🗑️ OPTION RESET (Développement uniquement) :
   - Supprimer toutes les migrations
   - Régénérer avec une version Django unique
   - ⚠️ PERTE DE DONNÉES : Sauvegarder d'abord !

3. 🔄 OPTION SQUASH :
   - Fusionner les migrations par app
   - Unifier les versions Django
   - Maintenir l'historique essentiel

COMMANDES À EXÉCUTER (après sauvegarde) :
"""
        
        for app_name, versions in analysis.items():
            if len(versions) > 1:
                strategy += f"""
   # Pour l'app '{app_name}' (versions: {', '.join(versions)})
   python manage.py showmigrations {app_name}
   python manage.py squashmigrations {app_name} 0001 --squashed-name unified
"""
        
        return strategy


def run_dependency_audit():
    """
    Fonction principale d'audit des dépendances.
    
    Orchestrateur respectant le Dependency Inversion Principle.
    """
    print("🔍 AUDIT DES DÉPENDANCES - ANALYSE COMPLÈTE")
    print("=" * 60)
    
    # Analyser les dépendances
    analyzer = DependencyAnalyzer()
    
    print("\n📊 ÉTAT ACTUEL DES DÉPENDANCES:")
    print("-" * 40)
    
    # Conflits de versions
    conflicts = analyzer.find_version_conflicts()
    if conflicts:
        print("\n❌ CONFLITS DE VERSIONS DÉTECTÉS:")
        for pkg, installed, required in conflicts:
            print(f"   {pkg}: installé={installed}, requis={required}")
    else:
        print("\n✅ Aucun conflit de version détecté")
    
    # Packages manquants
    missing = analyzer.find_missing_packages()
    if missing:
        print("\n📥 PACKAGES MANQUANTS:")
        for pkg, version in missing:
            print(f"   {pkg}=={version}")
    else:
        print("\n✅ Tous les packages requis sont installés")
    
    # Analyse Django spécifique
    django_info = analyzer.get_django_version_info()
    print(f"\n🐍 ANALYSE DJANGO:")
    print(f"   Version installée: {django_info['installed'] or 'Non installé'}")
    print(f"   Version requise: {django_info['required'] or 'Non spécifiée'}")
    print(f"   Versions dans migrations: {', '.join(django_info['in_migrations']) or 'Aucune'}")
    print(f"   Conflit détecté: {'❌ OUI' if django_info['conflict'] else '✅ NON'}")
    
    # Analyse des migrations
    migration_cleaner = MigrationCleaner()
    migration_analysis = migration_cleaner.analyze_migration_versions()
    
    if migration_analysis:
        print(f"\n🗃️ VERSIONS DJANGO DANS LES MIGRATIONS:")
        for app, versions in migration_analysis.items():
            print(f"   {app}: {', '.join(versions)}")
    
    return analyzer, migration_cleaner