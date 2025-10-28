"""
Script pour vérifier la correspondance entre les vues backend et les templates frontend.
"""

import os
import re
from pathlib import Path

def find_template_names():
    """Trouve tous les template_name dans les fichiers views.py"""
    templates_required = []
    views_files = Path('.').rglob('*views.py')
    
    for view_file in views_files:
        if 'migrations' in str(view_file) or '__pycache__' in str(view_file):
            continue
            
        try:
            with open(view_file, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = re.findall(r"template_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                for match in matches:
                    templates_required.append((match, str(view_file)))
        except Exception as e:
            print(f"Erreur lecture {view_file}: {e}")
    
    return templates_required

def check_template_exists(template_path):
    """Vérifie si un template existe"""
    full_path = Path('templates') / template_path
    return full_path.exists()

def main():
    print("="*80)
    print("VÉRIFICATION BACKEND ↔ FRONTEND")
    print("="*80)
    print()
    
    templates_required = find_template_names()
    
    # Grouper par app
    by_app = {}
    for template, view_file in templates_required:
        app = template.split('/')[0] if '/' in template else 'root'
        if app not in by_app:
            by_app[app] = []
        by_app[app].append((template, view_file))
    
    total = 0
    missing = 0
    
    for app, templates in sorted(by_app.items()):
        print(f"\n📁 {app.upper()}")
        print("-" * 80)
        
        for template, view_file in sorted(set(templates)):
            total += 1
            exists = check_template_exists(template)
            status = "✅" if exists else "❌"
            
            if not exists:
                missing += 1
                
            print(f"{status} {template}")
            if not exists:
                print(f"   └─ Requis par: {view_file}")
    
    print()
    print("="*80)
    print(f"RÉSULTAT: {total - missing}/{total} templates présents")
    
    if missing == 0:
        print("✅ TOUTES les fonctionnalités backend ont leur frontend!")
    else:
        print(f"⚠️  {missing} template(s) manquant(s)")
    print("="*80)

if __name__ == '__main__':
    main()
