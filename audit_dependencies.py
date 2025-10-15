#!/usr/bin/env python3
"""
Script d'audit et nettoyage des dépendances.

Ce script analyse l'état des dépendances et propose des solutions
pour résoudre les incohérences de versions.

Usage:
    python audit_dependencies.py [--fix] [--backup]

Auteur: Système de Gestion de Présence
Version: 2.0 (Refactorisé)
"""

import os
import sys
import argparse
from pathlib import Path

# Ajouter le répertoire du projet au path Python
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from common.dependency_manager import (
        DependencyAnalyzer, 
        DependencyUpdater, 
        MigrationCleaner,
        run_dependency_audit
    )
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("💡 Assurez-vous d'être dans le répertoire du projet")
    sys.exit(1)


def display_summary(analyzer, migration_cleaner):
    """
    Affiche un résumé des problèmes détectés.
    
    Args:
        analyzer: Instance de DependencyAnalyzer
        migration_cleaner: Instance de MigrationCleaner
    """
    print("\n" + "="*60)
    print("📋 RÉSUMÉ DES PROBLÈMES DÉTECTÉS")
    print("="*60)
    
    conflicts = analyzer.find_version_conflicts()
    missing = analyzer.find_missing_packages()
    django_info = analyzer.get_django_version_info()
    migration_analysis = migration_cleaner.analyze_migration_versions()
    
    # Compter les problèmes
    issues_count = 0
    
    if conflicts:
        issues_count += len(conflicts)
        print(f"\n🔴 {len(conflicts)} conflit(s) de version")
        
    if missing:
        issues_count += len(missing)
        print(f"\n🟡 {len(missing)} package(s) manquant(s)")
        
    if django_info['conflict']:
        issues_count += 1
        print(f"\n🔴 Conflit Django : {django_info['installed']} ≠ {django_info['required']}")
        
    # Vérifier les migrations incohérentes
    migration_issues = 0
    for app, versions in migration_analysis.items():
        if len(versions) > 1:
            migration_issues += 1
            
    if migration_issues:
        issues_count += migration_issues
        print(f"\n🟠 {migration_issues} app(s) avec migrations incohérentes")
    
    # Conclusion
    if issues_count == 0:
        print(f"\n✅ EXCELLENT ! Aucun problème détecté.")
        print("🎉 Votre projet est dans un état stable.")
    else:
        print(f"\n⚠️  TOTAL: {issues_count} problème(s) détecté(s)")
        print("🔧 Utilisez --fix pour appliquer les corrections automatiques")


def fix_dependencies(backup=True):
    """
    Corrige automatiquement les problèmes de dépendances.
    
    Args:
        backup: Si True, crée une sauvegarde avant les modifications
    """
    print("\n🔧 APPLICATION DES CORRECTIONS AUTOMATIQUES")
    print("="*50)
    
    updater = DependencyUpdater()
    
    # 1. Créer une sauvegarde si demandé
    if backup:
        print("\n📦 Création des sauvegardes...")
        
        # Sauvegarder requirements.txt
        if Path('requirements.txt').exists():
            backup_file = updater.create_backup_requirements('requirements.txt')
            if backup_file:
                print(f"   ✅ requirements.txt → {backup_file}")
        
        # Sauvegarder le requirements.txt dupliqué
        project_req = Path('../requirements.txt')
        if project_req.exists():
            backup_file = updater.create_backup_requirements(str(project_req))
            if backup_file:
                print(f"   ✅ ../requirements.txt → {backup_file}")
    
    # 2. Générer le nouveau requirements.txt
    print("\n📝 Génération du nouveau requirements.txt...")
    try:
        new_content = updater.generate_updated_requirements()
        
        # Écrire le nouveau fichier
        with open('requirements.txt', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("   ✅ requirements.txt mis à jour avec Django 4.2.16 LTS")
        
        # Supprimer le doublon dans le répertoire parent
        project_req = Path('../requirements.txt')
        if project_req.exists():
            project_req.unlink()
            print("   ✅ Fichier requirements.txt dupliqué supprimé")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # 3. Installer les nouvelles dépendances
    print("\n⬇️  Installation des dépendances mises à jour...")
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt', '--upgrade'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("   ✅ Dépendances installées avec succès")
        else:
            print(f"   ⚠️  Avertissements lors de l'installation:")
            print(f"   {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ Erreur lors de l'installation: {e}")
        return False
    
    # 4. Vérifier Django
    print("\n🐍 Vérification de Django...")
    try:
        import django
        print(f"   ✅ Django {django.get_version()} installé correctement")
    except Exception as e:
        print(f"   ❌ Erreur Django: {e}")
        return False
    
    print("\n🎉 CORRECTIONS APPLIQUÉES AVEC SUCCÈS !")
    print("\n📋 PROCHAINES ÉTAPES RECOMMANDÉES:")
    print("   1. Tester le serveur de développement")
    print("   2. Exécuter les tests")
    print("   3. Vérifier les migrations (voir suggestions ci-dessous)")
    
    return True


def suggest_migration_fixes():
    """Affiche les suggestions pour corriger les migrations."""
    print("\n🗃️ SUGGESTIONS POUR LES MIGRATIONS:")
    print("-" * 45)
    
    migration_cleaner = MigrationCleaner()
    strategy = migration_cleaner.suggest_migration_strategy()
    print(strategy)


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Audit et nettoyage des dépendances du projet"
    )
    parser.add_argument(
        '--fix', 
        action='store_true',
        help='Applique automatiquement les corrections'
    )
    parser.add_argument(
        '--no-backup', 
        action='store_true',
        help='Ne crée pas de sauvegarde avant les modifications'
    )
    parser.add_argument(
        '--migrations', 
        action='store_true',
        help='Affiche seulement les suggestions pour les migrations'
    )
    
    args = parser.parse_args()
    
    print("🔍 AUDIT DES DÉPENDANCES - SYSTÈME DE GESTION DE PRÉSENCE")
    print("=" * 65)
    
    if args.migrations:
        suggest_migration_fixes()
        return
    
    try:
        # Exécuter l'audit complet
        analyzer, migration_cleaner = run_dependency_audit()
        
        # Afficher le résumé
        display_summary(analyzer, migration_cleaner)
        
        # Appliquer les corrections si demandé
        if args.fix:
            success = fix_dependencies(backup=not args.no_backup)
            if success:
                # Réexécuter l'audit pour vérifier
                print("\n🔍 VÉRIFICATION POST-CORRECTION...")
                analyzer, migration_cleaner = run_dependency_audit()
                display_summary(analyzer, migration_cleaner)
        
        # Suggestions pour les migrations
        suggest_migration_fixes()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Audit interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR FATALE: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()