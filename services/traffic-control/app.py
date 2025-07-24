#!/usr/bin/env python3
"""
Traffic Control Service pour NMS
Service de contrôle de trafic et QoS
"""

import os
import sys
import json
import yaml
import time
import schedule
import logging
import subprocess
import psutil
from datetime import datetime
from typing import Dict, List, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_restful import Api, Resource
import redis

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
api = Api(app)

# Configuration Redis pour la communication avec Django
try:
    redis_host = os.getenv('REDIS_HOST', 'nms-redis')
    redis_port = int(os.getenv('REDIS_PORT', '6379'))
    redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
    redis_client.ping()
    logger.info(f"Connexion Redis établie sur {redis_host}:{redis_port}")
except Exception as e:
    logger.error(f"Erreur de connexion Redis: {e}")
    redis_client = None

class TrafficControlManager:
    """Gestionnaire principal du contrôle de trafic"""
    
    def __init__(self):
        self.config_file = '/etc/tc/rules.yaml'
        self.rules = self.load_rules()
        
    def load_rules(self) -> Dict:
        """Charge les règles de traffic control depuis le fichier de configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    rules = yaml.safe_load(f)
                    logger.info(f"Règles TC chargées: {len(rules.get('policies', []))} politiques")
                    return rules
            else:
                logger.warning(f"Fichier de configuration non trouvé: {self.config_file}")
                return {'policies': [], 'interfaces': []}
        except Exception as e:
            logger.error(f"Erreur lors du chargement des règles TC: {e}")
            return {'policies': [], 'interfaces': []}
    
    def save_rules(self):
        """Sauvegarde les règles dans le fichier de configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.rules, f, default_flow_style=False, allow_unicode=True)
            logger.info("Règles TC sauvegardées")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des règles TC: {e}")
    
    def get_network_interfaces(self) -> List[str]:
        """Récupère la liste des interfaces réseau disponibles"""
        try:
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True)
            interfaces = []
            for line in result.stdout.split('\n'):
                if ': ' in line and not line.strip().startswith(' '):
                    interface = line.split(': ')[1].split('@')[0]
                    if interface not in ['lo']:  # Exclure loopback
                        interfaces.append(interface)
            return interfaces
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des interfaces: {e}")
            return []
    
    def apply_tc_rule(self, interface: str, bandwidth: str, priority: int = 1) -> bool:
        """Applique une règle TC sur une interface"""
        try:
            # Nettoyer les règles existantes
            subprocess.run(['tc', 'qdisc', 'del', 'dev', interface, 'root'], 
                         capture_output=True, text=True)
            
            # Ajouter la nouvelle règle
            cmd = [
                'tc', 'qdisc', 'add', 'dev', interface, 'root', 'handle', '1:',
                'htb', 'default', '30'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Ajouter la classe de bande passante
                cmd = [
                    'tc', 'class', 'add', 'dev', interface, 'parent', '1:', 
                    'classid', f'1:{priority}', 'htb', 'rate', bandwidth
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"Règle TC appliquée sur {interface}: {bandwidth}")
                    return True
            
            logger.error(f"Erreur lors de l'application de la règle TC: {result.stderr}")
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application de la règle TC: {e}")
            return False
    
    def remove_tc_rules(self, interface: str) -> bool:
        """Supprime toutes les règles TC d'une interface"""
        try:
            result = subprocess.run(['tc', 'qdisc', 'del', 'dev', interface, 'root'], 
                                 capture_output=True, text=True)
            if result.returncode == 0 or 'RTNETLINK answers: No such file or directory' in result.stderr:
                logger.info(f"Règles TC supprimées de {interface}")
                return True
            else:
                logger.error(f"Erreur lors de la suppression des règles TC: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des règles TC: {e}")
            return False
    
    def get_traffic_stats(self, interface: str) -> Dict:
        """Récupère les statistiques de trafic d'une interface"""
        try:
            result = subprocess.run(['tc', '-s', 'qdisc', 'show', 'dev', interface], 
                                 capture_output=True, text=True)
            stats = {
                'interface': interface,
                'timestamp': datetime.now().isoformat(),
                'raw_output': result.stdout
            }
            
            # Parser les statistiques basiques
            if result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Sent' in line:
                        stats['traffic_info'] = line.strip()
                        
            return stats
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {e}")
            return {'interface': interface, 'error': str(e)}

# Instance globale du gestionnaire
tc_manager = TrafficControlManager()

class InterfacesResource(Resource):
    """API pour gérer les interfaces réseau"""
    
    def get(self):
        """Récupère la liste des interfaces réseau"""
        interfaces = tc_manager.get_network_interfaces()
        return {'interfaces': interfaces}

class TrafficStatsResource(Resource):
    """API pour les statistiques de trafic"""
    
    def get(self, interface=None):
        """Récupère les statistiques de trafic"""
        if interface:
            stats = tc_manager.get_traffic_stats(interface)
            return stats
        else:
            interfaces = tc_manager.get_network_interfaces()
            all_stats = {}
            for iface in interfaces:
                all_stats[iface] = tc_manager.get_traffic_stats(iface)
            return all_stats

class QoSPolicyResource(Resource):
    """API pour gérer les politiques QoS"""
    
    def get(self):
        """Récupère toutes les politiques QoS"""
        return tc_manager.rules
    
    def post(self):
        """Crée une nouvelle politique QoS"""
        data = request.get_json()
        
        if not data or 'interface' not in data or 'bandwidth' not in data:
            return {'error': 'Interface et bandwidth requis'}, 400
        
        interface = data['interface']
        bandwidth = data['bandwidth']
        priority = data.get('priority', 1)
        
        # Appliquer la règle
        if tc_manager.apply_tc_rule(interface, bandwidth, priority):
            # Sauvegarder dans la configuration
            policy = {
                'id': f"{interface}_{int(time.time())}",
                'interface': interface,
                'bandwidth': bandwidth,
                'priority': priority,
                'created_at': datetime.now().isoformat()
            }
            
            tc_manager.rules['policies'].append(policy)
            tc_manager.save_rules()
            
            # Notifier Django via Redis
            if redis_client:
                try:
                    redis_client.publish('tc_policy_applied', json.dumps(policy))
                except Exception as e:
                    logger.error(f"Erreur notification Redis: {e}")
            
            return {'policy': policy, 'status': 'applied'}, 201
        else:
            return {'error': 'Erreur lors de l\'application de la politique'}, 500
    
    def delete(self):
        """Supprime une politique QoS"""
        data = request.get_json()
        
        if not data or 'interface' not in data:
            return {'error': 'Interface requise'}, 400
        
        interface = data['interface']
        
        if tc_manager.remove_tc_rules(interface):
            # Supprimer de la configuration
            tc_manager.rules['policies'] = [
                p for p in tc_manager.rules['policies'] 
                if p.get('interface') != interface
            ]
            tc_manager.save_rules()
            
            # Notifier Django via Redis
            if redis_client:
                try:
                    redis_client.publish('tc_policy_removed', json.dumps({'interface': interface}))
                except Exception as e:
                    logger.error(f"Erreur notification Redis: {e}")
            
            return {'status': 'removed', 'interface': interface}
        else:
            return {'error': 'Erreur lors de la suppression de la politique'}, 500

# Enregistrement des routes API
api.add_resource(InterfacesResource, '/api/interfaces')
api.add_resource(TrafficStatsResource, '/api/stats', '/api/stats/<string:interface>')
api.add_resource(QoSPolicyResource, '/api/qos')

@app.route('/health')
def health_check():
    """Vérification de santé du service"""
    return {
        'status': 'healthy',
        'service': 'traffic-control',
        'timestamp': datetime.now().isoformat(),
        'redis_connected': redis_client is not None
    }

@app.route('/')
def index():
    """Page d'accueil du service"""
    return {
        'service': 'NMS Traffic Control Service',
        'version': '1.0.0',
        'endpoints': [
            '/health',
            '/api/interfaces',
            '/api/stats',
            '/api/stats/<interface>',
            '/api/qos'
        ]
    }

def periodic_stats_collection():
    """Collecte périodique des statistiques"""
    try:
        interfaces = tc_manager.get_network_interfaces()
        stats_data = {}
        
        for interface in interfaces:
            stats = tc_manager.get_traffic_stats(interface)
            stats_data[interface] = stats
        
        # Publier les stats via Redis
        if redis_client:
            redis_client.publish('tc_stats_update', json.dumps(stats_data))
        
        logger.info(f"Statistiques collectées pour {len(interfaces)} interfaces")
        
    except Exception as e:
        logger.error(f"Erreur lors de la collecte des statistiques: {e}")

# Planifier la collecte des statistiques toutes les 5 minutes
schedule.every(5).minutes.do(periodic_stats_collection)

def run_scheduler():
    """Exécute le planificateur de tâches"""
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    # Créer le fichier de configuration par défaut s'il n'existe pas
    if not os.path.exists('/etc/tc/rules.yaml'):
        os.makedirs('/etc/tc', exist_ok=True)
        default_config = {
            'policies': [],
            'interfaces': tc_manager.get_network_interfaces()
        }
        with open('/etc/tc/rules.yaml', 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        logger.info("Configuration par défaut créée")
    
    # Démarrer le planificateur en arrière-plan
    import threading
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("Traffic Control Service démarré")
    logger.info(f"Interfaces disponibles: {tc_manager.get_network_interfaces()}")
    
    # Démarrer le serveur Flask
    app.run(host='0.0.0.0', port=8003, debug=False) 