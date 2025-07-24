"""
Script pour initialiser la base de données de test.

Ce script crée les tables nécessaires pour les tests.
"""

import os
import sys
import django
from pathlib import Path

# Ajouter le répertoire parent au chemin Python
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent.parent
sys.path.append(str(parent_dir))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reporting.tests.settings')
django.setup()

# Importer les modèles
from django.contrib.auth.models import User
from django.db import connection
from django.core.management import call_command

def setup_test_database():
    """Configure la base de données pour les tests."""
    # Créer les tables nécessaires
    with connection.cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS auth_user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password VARCHAR(128) NOT NULL,
            last_login DATETIME NULL,
            is_superuser BOOLEAN NOT NULL,
            username VARCHAR(150) NOT NULL UNIQUE,
            first_name VARCHAR(150) NOT NULL,
            last_name VARCHAR(150) NOT NULL,
            email VARCHAR(254) NOT NULL,
            is_staff BOOLEAN NOT NULL,
            is_active BOOLEAN NOT NULL,
            date_joined DATETIME NOT NULL
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reporting_report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(255) NOT NULL,
            description TEXT NULL,
            report_type VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL,
            content JSON NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            completed_at DATETIME NULL,
            created_by_id INTEGER NOT NULL REFERENCES auth_user(id),
            template_id INTEGER NULL REFERENCES reporting_reporttemplate(id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reporting_reporttemplate (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            description TEXT NULL,
            template_type VARCHAR(50) NOT NULL,
            content JSON NOT NULL,
            is_active BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            created_by_id INTEGER NOT NULL REFERENCES auth_user(id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reporting_scheduledreport (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            description TEXT NULL,
            frequency VARCHAR(50) NOT NULL,
            parameters JSON NOT NULL,
            is_active BOOLEAN NOT NULL,
            last_run DATETIME NULL,
            next_run DATETIME NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            report_id INTEGER NULL REFERENCES reporting_report(id),
            template_id INTEGER NULL REFERENCES reporting_reporttemplate(id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reporting_scheduledreportrecipient (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheduled_report_id INTEGER NOT NULL REFERENCES reporting_scheduledreport(id),
            user_id INTEGER NOT NULL REFERENCES auth_user(id)
        )
        """)

    print("Tables créées avec succès.")

if __name__ == "__main__":
    setup_test_database() 