#!/usr/bin/env python
"""
Script pour exécuter les tests unitaires.

Ce script permet d'exécuter les tests unitaires avec pytest
et de générer un rapport de couverture de code.
"""

import os
import sys
import pytest
import coverage

# Configuration de la couverture de code
cov = coverage.Coverage(
    source=["ai_assistant"],
    omit=[
        "*/tests/*",
        "*/migrations/*",
        "*/__init__.py",
        "*/settings.py",
        "*/urls.py",
        "*/wsgi.py",
        "*/asgi.py",
        "*/manage.py",
    ],
    branch=True,
)

def main():
    """Exécute les tests unitaires et génère un rapport de couverture."""
    # Démarrage de la couverture de code
    cov.start()
    
    # Exécution des tests
    print("Exécution des tests unitaires...")
    exit_code = pytest.main([
        "-v",
        "--tb=native",
        "--no-header",
        os.path.dirname(__file__),
    ])
    
    # Arrêt de la couverture de code
    cov.stop()
    
    # Génération du rapport de couverture
    print("\nGénération du rapport de couverture de code...")
    cov.report()
    
    # Génération du rapport HTML
    html_dir = os.path.join(os.path.dirname(__file__), "coverage_html")
    cov.html_report(directory=html_dir)
    print(f"Rapport HTML généré dans: {html_dir}")
    
    # Génération du rapport XML
    xml_file = os.path.join(os.path.dirname(__file__), "coverage.xml")
    cov.xml_report(outfile=xml_file)
    print(f"Rapport XML généré dans: {xml_file}")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 