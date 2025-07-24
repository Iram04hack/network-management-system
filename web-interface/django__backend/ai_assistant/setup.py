#!/usr/bin/env python3
"""
Script d'initialisation pour le module d'assistant IA.

Ce script configure l'environnement pour le module d'assistant IA.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def setup_environment(args):
    """Configure l'environnement pour le module d'assistant IA."""
    # Chemin du répertoire courant
    current_dir = Path(__file__).resolve().parent
    
    # Créer les répertoires de stockage
    storage_dir = current_dir / "storage"
    documents_dir = storage_dir / "documents"
    conversations_dir = storage_dir / "conversations"
    command_history_dir = storage_dir / "command_history"
    
    for directory in [storage_dir, documents_dir, conversations_dir, command_history_dir]:
        os.makedirs(directory, exist_ok=True)
        print(f"Répertoire créé: {directory}")
    
    # Installer les dépendances
    if args.install_deps:
        requirements_file = current_dir / "requirements.txt"
        if requirements_file.exists():
            print("Installation des dépendances...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
            print("Dépendances installées avec succès.")
        else:
            print("Fichier requirements.txt non trouvé.")
    
    # Configurer les variables d'environnement
    if args.setup_env:
        env_file = current_dir.parent / ".env"
        
        # Vérifier si le fichier .env existe
        if not env_file.exists():
            print("Création du fichier .env...")
            with open(env_file, "w") as f:
                f.write("# Variables d'environnement pour le module d'assistant IA\n")
                f.write("OPENAI_API_KEY=\n")
                f.write("OPENAI_MODEL=gpt-4\n")
                f.write("OPENAI_EMBEDDING_MODEL=text-embedding-ada-002\n")
                f.write("GOOGLE_API_KEY=\n")
                f.write("GOOGLE_CSE_ID=\n")
                f.write("AI_ASSISTANT_STORAGE_DIR=\n")
            print(f"Fichier .env créé: {env_file}")
            print("Veuillez éditer ce fichier pour configurer les variables d'environnement.")
        else:
            print(f"Le fichier .env existe déjà: {env_file}")
    
    # Exécuter les migrations Django
    if args.migrate:
        print("Exécution des migrations Django...")
        django_dir = current_dir.parent
        os.chdir(django_dir)
        subprocess.run([sys.executable, "manage.py", "makemigrations", "ai_assistant"])
        subprocess.run([sys.executable, "manage.py", "migrate", "ai_assistant"])
        print("Migrations exécutées avec succès.")
    
    print("Configuration terminée.")


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Configuration du module d'assistant IA")
    parser.add_argument("--install-deps", action="store_true", help="Installer les dépendances")
    parser.add_argument("--setup-env", action="store_true", help="Configurer les variables d'environnement")
    parser.add_argument("--migrate", action="store_true", help="Exécuter les migrations Django")
    parser.add_argument("--all", action="store_true", help="Exécuter toutes les étapes")
    
    args = parser.parse_args()
    
    # Si --all est spécifié, activer toutes les options
    if args.all:
        args.install_deps = True
        args.setup_env = True
        args.migrate = True
    
    # Si aucune option n'est spécifiée, afficher l'aide
    if not (args.install_deps or args.setup_env or args.migrate):
        parser.print_help()
        return
    
    setup_environment(args)


if __name__ == "__main__":
    main() 