"""
Script pour supprimer les doublons de décorateurs swagger_auto_schema.
"""

import re
from pathlib import Path


def remove_duplicate_swagger_decorators(file_path: Path):
    """Supprime les doublons de décorateurs swagger_auto_schema dans un fichier."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Si c'est un décorateur swagger_auto_schema
        if '@swagger_auto_schema(' in line.strip():
            # Chercher la fin du décorateur
            decorator_start = i
            bracket_count = line.count('(') - line.count(')')
            j = i + 1
            
            while j < len(lines) and bracket_count > 0:
                bracket_count += lines[j].count('(') - lines[j].count(')')
                j += 1
            
            decorator_end = j - 1
            
            # Vérifier s'il y a un autre décorateur swagger_auto_schema juste après
            k = j
            while k < len(lines) and (lines[k].strip() == '' or lines[k].strip().startswith('@')):
                if '@swagger_auto_schema(' in lines[k].strip():
                    # Doublon trouvé - ignorer le premier décorateur
                    print(f"  🔧 Doublon supprimé lignes {decorator_start+1}-{decorator_end+1}")
                    i = decorator_end + 1
                    break
                k += 1
            else:
                # Pas de doublon, garder le décorateur
                new_lines.append(line)
                i += 1
        else:
            new_lines.append(line)
            i += 1
    
    # Écrire le fichier corrigé
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))


def main():
    """Point d'entrée principal."""
    print("🔧 === SUPPRESSION DES DOUBLONS SWAGGER ===\n")
    
    base_path = Path(__file__).parent.parent / "views"
    view_files = [
        'dashboard_views.py',
        'device_management_views.py', 
        'search_views.py',
        'topology_discovery_views.py',
        'prometheus_views.py',
        'grafana_views.py',
        'security_views.py'
    ]
    
    for file_name in view_files:
        file_path = base_path / file_name
        if file_path.exists():
            print(f"📝 Nettoyage de {file_name}...")
            remove_duplicate_swagger_decorators(file_path)
            print(f"  ✅ {file_name} nettoyé")
        else:
            print(f"⚠️ Fichier non trouvé: {file_name}")
    
    print("\n✅ Suppression des doublons terminée!")


if __name__ == "__main__":
    main() 
    