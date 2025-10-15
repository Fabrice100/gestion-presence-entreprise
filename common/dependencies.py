"""
Gestionnaire de dépendances pour le système de gestion de présence.

Ce module fournit des outils pour analyser, valider et maintenir
les dépendances du projet selon les bonnes pratiques.

Auteur: Système de Gestion de Présence
Version: 2.0 (Refactorisé)
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re


class DependencyAnalyzer:
    """
    Analyseur de dépendances respectant le Single Responsibility Principle.
    
    Se concentre uniquement sur l'analyse des dépendances sans les modifier.
    """
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.requirements_files = self._find_requirements_files()
    
    def _find_requirements_files(self) -> List[Path]:
        """Trouve tous les fichiers requirements dans le projet."""
        patterns = [
            'requirements.txt',
            'requirements/*.txt',
            '*/requirements.txt',
            'requirements-*.txt'
        ]
        
        files = []
        for pattern in patterns:
            files.extend(self.project_root.glob(pattern))
        
        return sorted(set(files))
    
    def get_installed_packages(self) -> Dict[str, str]:
        """
        Récupère la liste des packages installés avec leurs versions.
        
        Returns:
            Dict[str, str]: {package_name: version}
        """
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                check=True
            )
            
            import json
            packages = json.loads(result.stdout)
            return {pkg['name'].lower(): pkg['version'] for pkg in packages}
            
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"❌ Erreur lors de la récupération des packages installés: {e}")
            return {}
    
    def parse_requirements_file(self, file_path: Path) -> Dict[str, str]:
        """
        Parse un fichier requirements.txt.
        
        Args:
            file_path: Chemin vers le fichier requirements
            
        Returns:
            Dict[str, str]: {package_name: version_spec}
        """
        requirements = {}
        
        if not file_path.exists():
            return requirements
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Ignorer les commentaires et lignes vides
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parser la ligne (format: package==version)
                    match = re.match(r'^([a-zA-Z0-9_-]+)\s*([><=!]+.*)?$', line)
                    if match:
                        package_name = match.group(1).lower()
                        version_spec = match.group(2) or ''
                        requirements[package_name] = version_spec.strip()
        
        except Exception as e:
            print(f"❌ Erreur lors du parsing de {file_path}: {e}")
        
        return requirements
    
    def analyze_discrepancies(self) -> Dict[str, Dict]:
        """
        Analyse les écarts entre les requirements et les packages installés.
        
        Returns:
            Dict contenant les analyses par fichier requirements
        """
        installed = self.get_installed_packages()
        analysis = {}
        
        for req_file in self.requirements_files:
            requirements = self.parse_requirements_file(req_file)
            file_analysis = {
                'file_path': str(req_file),
                'missing_packages': [],
                'version_mismatches': [],
                'extra_packages': [],
                'requirements_count': len(requirements),
                'installed_count': len(installed)
            }
            
            # Vérifier les packages manquants et versions
            for pkg_name, version_spec in requirements.items():
                if pkg_name not in installed:
                    file_analysis['missing_packages'].append({
                        'package': pkg_name,
                        'required_version': version_spec
                    })
                elif version_spec.startswith('=='):
                    required_version = version_spec[2:]
                    installed_version = installed[pkg_name]
                    if required_version != installed_version:
                        file_analysis['version_mismatches'].append({
                            'package': pkg_name,
                            'required': required_version,
                            'installed': installed_version
                        })
            
            analysis[str(req_file)] = file_analysis
        
        return analysis


class DependencyValidator:
    """
    Validateur de dépendances respectant le principe de responsabilité unique.
    """
    
    CRITICAL_PACKAGES = {
        'django': {
            'min_version': '4.2.0',
            'max_version': '5.0.0',
            'reason': 'LTS version recommandée pour la stabilité'
        }
    }
    
    @staticmethod
    def validate_django_version(version: str) -> Tuple[bool, str]:
        """
        Valide la version de Django.
        
        Args:
            version: Version de Django installée
            
        Returns:
            Tuple[bool, str]: (is_valid, message)
        """
        try:
            # Comparaison simple de versions
            major, minor, patch = map(int, version.split('.'))
            
            # Django 4.2.x recommandé (LTS)
            if major == 4 and minor == 2:
                return True, f"Django {version} - Version LTS recommandée ✅"
            elif major == 5:
                return False, f"Django {version} - Version 5.x non recommandée (utilisez 4.2.x LTS)"
            elif major < 4 or (major == 4 and minor < 2):
                return False, f"Django {version} - Version trop ancienne (minimum 4.2.0)"
            else:
                return True, f"Django {version} - Version compatible ✅"
                
        except Exception as e:
            return False, f"Erreur lors de la validation de Django: {e}"
    
    @staticmethod
    def check_security_packages(installed_packages: Dict[str, str]) -> List[str]:
        """
        Vérifie la présence de packages de sécurité recommandés.
        
        Args:
            installed_packages: Packages installés
            
        Returns:
            List[str]: Messages d'avertissement
        """
        warnings = []
        
        security_packages = {
            'cryptography': 'Chiffrement sécurisé',
            'django-ratelimit': 'Protection contre le spam (optionnel)'
        }
        
        for pkg, description in security_packages.items():
            if pkg not in installed_packages:
                if 'optionnel' not in description:
                    warnings.append(f"⚠️  Package de sécurité manquant: {pkg} ({description})")
        
        return warnings


def audit_dependencies(project_root: str = ".") -> None:
    """
    Fonction principale d'audit des dépendances.
    
    Args:
        project_root: Chemin vers la racine du projet
    """
    print("🔍 AUDIT DES DÉPENDANCES")
    print("=" * 50)
    
    analyzer = DependencyAnalyzer(Path(project_root))
    validator = DependencyValidator()
    
    # 1. Analyser les fichiers requirements
    print(f"\n📋 Fichiers requirements trouvés: {len(analyzer.requirements_files)}")
    for req_file in analyzer.requirements_files:
        print(f"   - {req_file}")
    
    # 2. Analyser les écarts
    print(f"\n🔍 ANALYSE DES ÉCARTS:")
    analysis = analyzer.analyze_discrepancies()
    
    for file_path, data in analysis.items():
        print(f"\n📄 {file_path}:")
        print(f"   Requirements: {data['requirements_count']} packages")
        
        if data['missing_packages']:
            print(f"   ❌ Packages manquants: {len(data['missing_packages'])}")
            for pkg in data['missing_packages'][:3]:  # Afficher max 3
                print(f"      - {pkg['package']} {pkg['required_version']}")
        
        if data['version_mismatches']:
            print(f"   ⚠️  Versions différentes: {len(data['version_mismatches'])}")
            for pkg in data['version_mismatches'][:3]:  # Afficher max 3
                print(f"      - {pkg['package']}: requis {pkg['required']} vs installé {pkg['installed']}")
    
    # 3. Valider Django
    installed = analyzer.get_installed_packages()
    if 'django' in installed:
        is_valid, message = validator.validate_django_version(installed['django'])
        print(f"\n🎯 DJANGO: {message}")
    
    # 4. Vérifier la sécurité
    security_warnings = validator.check_security_packages(installed)
    if security_warnings:
        print(f"\n🔒 AVERTISSEMENTS SÉCURITÉ:")
        for warning in security_warnings:
            print(f"   {warning}")
    
    print(f"\n✅ Audit terminé !")