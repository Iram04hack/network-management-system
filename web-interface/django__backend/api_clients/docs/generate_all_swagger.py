#!/usr/bin/env python
"""
Script de génération de la documentation Swagger pour tous les clients API.

Ce script génère automatiquement la documentation Swagger pour tous les clients
du module api_clients et les enregistre dans le répertoire swagger_output.
"""

import os
import sys
import inspect
import traceback
from pathlib import Path

# Ajouter le répertoire parent au chemin pour pouvoir importer les modules
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

# Création du répertoire de sortie s'il n'existe pas
SWAGGER_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "swagger_output")
if not os.path.exists(SWAGGER_OUTPUT_DIR):
    os.makedirs(SWAGGER_OUTPUT_DIR)
    print(f"Répertoire de sortie créé : {SWAGGER_OUTPUT_DIR}")

# Import des clients
from api_clients.network.gns3_client import GNS3Client
from api_clients.network.snmp_client import SNMPClient
from api_clients.network.netflow_client import NetflowClient
from api_clients.security.fail2ban_client import Fail2BanClient
from api_clients.security.suricata_client import SuricataClient
from api_clients.monitoring.prometheus_client import PrometheusClient
from api_clients.monitoring.grafana_client import GrafanaClient
from api_clients.monitoring.elasticsearch_client import ElasticsearchClient
from api_clients.monitoring.netdata_client import NetdataClient
from api_clients.monitoring.ntopng_client import NtopngClient
from api_clients.infrastructure.haproxy_client import HAProxyClient

# Import du générateur Swagger
from api_clients.docs.swagger_generator import generate_swagger_for_class

def generate_swagger_for_all_clients():
    """Génère la documentation Swagger pour tous les clients API."""
    print("Génération de la documentation Swagger...")
    
    clients = [
        (GNS3Client, "API GNS3 Client"),
        (SNMPClient, "API SNMP Client"),
        (NetflowClient, "API Netflow Client"),
        (Fail2BanClient, "API Fail2Ban Client"),
        (SuricataClient, "API Suricata Client"),
        (PrometheusClient, "API Prometheus Client"),
        (GrafanaClient, "API Grafana Client"),
        (ElasticsearchClient, "API Elasticsearch Client"),
        (NetdataClient, "API Netdata Client"),
        (NtopngClient, "API ntopng Client"),
        (HAProxyClient, "API HAProxy Client"),
    ]
    
    success_count = 0
    error_count = 0
    
    for client_class, title in clients:
        try:
            print(f"Génération pour {client_class.__name__}...")
            swagger = generate_swagger_for_class(
                client_class=client_class,
                title=title,
                description=client_class.__doc__ or f"Documentation API pour {client_class.__name__}",
                version="1.0.0",
                output_filename=f"{client_class.__name__.lower()}_swagger.json"
            )
            print(f"Documentation générée pour {client_class.__name__}")
            success_count += 1
        except Exception as e:
            print(f"❌ Erreur lors de la génération pour {client_class.__name__}: {str(e)}")
            traceback.print_exc()
            error_count += 1
    
    print(f"Génération terminée ! {success_count} succès, {error_count} erreurs.")

if __name__ == "__main__":
    generate_swagger_for_all_clients() 