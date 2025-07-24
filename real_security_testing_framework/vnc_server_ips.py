#!/usr/bin/env python3
"""
Configuration des Adresses IP des Serveurs VNC
==============================================

Ce module permet d'intégrer facilement les adresses IP des serveurs VNC
découvertes manuellement via les connexions VNC.

Instructions d'utilisation :
1. Connectez-vous à chaque serveur via VNC
2. Notez l'adresse IP affichée par 'ip addr show'
3. Mettez à jour le dictionnaire VNC_SERVER_IPS ci-dessous
4. Le framework utilisera automatiquement ces adresses
"""

# 🔧 CONFIGURATION DES ADRESSES IP DES SERVEURS VNC
# ===================================================
# 
# Mettez à jour ce dictionnaire avec les vraies adresses IP
# découvertes en vous connectant manuellement aux serveurs VNC.
#
# Format: 'nom_serveur': ['ip1', 'ip2', ...]
#
VNC_SERVER_IPS = {
    # ✅ IPs découvertes via captures d'écran utilisateur
    'Server-Web': [
        '192.168.11.11'  # ✅ Image #1 - inet 192.168.11.11/24
    ],
    
    'Server-Mail': [
        '192.168.31.11'  # ✅ Image #2 - inet 192.168.31.11/24
    ],
    
    'Server-DNS': [
        '192.168.31.11'  # ✅ Image #3 - inet 192.168.31.11/24
    ],
    
    'Server-DB': [
        '192.168.31.11'  # ✅ Image #4 - inet 192.168.31.11/24
    ],
    
    'PostTest': [
        # Image #5 - Pas d'IP réseau configurée, seulement loopback
        # Interface ens3 disponible mais sans IP DHCP assignée
        # Nécessite configuration réseau supplémentaire
    ],
    
    'Server-Fichiers': [
        '10.1.1.100'  # ✅ IP découverte via VNC - capture d'écran précédente
    ]
}

# 📋 INFORMATIONS DE CONNEXION VNC
# =================================
VNC_CONNECTION_INFO = {
    'Server-Web': {'host': '192.168.122.95', 'port': 5900},
    'Server-Mail': {'host': '192.168.122.95', 'port': 5902},
    'Server-DNS': {'host': '192.168.122.95', 'port': 5903},
    'Server-DB': {'host': '192.168.122.95', 'port': 5905},
    'PostTest': {'host': '192.168.122.95', 'port': 5901},
    'Server-Fichiers': {'host': '192.168.122.95', 'port': 5904}
}

# 🔐 IDENTIFIANTS D'AUTHENTIFICATION
# ==================================
VNC_CREDENTIALS = {
    'username': 'osboxes',
    'password': 'osboxes.org'
}

def get_vnc_server_ips(server_name: str):
    """
    Récupère les adresses IP configurées pour un serveur VNC.
    
    Args:
        server_name: Nom du serveur (ex: 'Server-Web')
        
    Returns:
        Liste des adresses IP ou liste vide si non configuré
    """
    return VNC_SERVER_IPS.get(server_name, [])

def get_all_configured_vnc_ips():
    """
    Récupère toutes les adresses IP VNC configurées.
    
    Returns:
        Dictionnaire {server_name: [ip_list]}
    """
    return {name: ips for name, ips in VNC_SERVER_IPS.items() if ips}

def get_vnc_connection_info(server_name: str):
    """
    Récupère les informations de connexion VNC pour un serveur.
    
    Args:
        server_name: Nom du serveur
        
    Returns:
        Dictionnaire avec host et port ou None
    """
    return VNC_CONNECTION_INFO.get(server_name)

def is_vnc_server_configured(server_name: str) -> bool:
    """
    Vérifie si un serveur VNC a des adresses IP configurées.
    
    Args:
        server_name: Nom du serveur
        
    Returns:
        True si au moins une IP est configurée
    """
    ips = VNC_SERVER_IPS.get(server_name, [])
    return len(ips) > 0

def get_configuration_status():
    """
    Retourne le statut de configuration de tous les serveurs VNC.
    
    Returns:
        Dictionnaire avec le statut de chaque serveur
    """
    status = {}
    for server_name in VNC_SERVER_IPS.keys():
        ips = VNC_SERVER_IPS[server_name]
        status[server_name] = {
            'configured': len(ips) > 0,
            'ip_count': len(ips),
            'ips': ips,
            'vnc_info': VNC_CONNECTION_INFO.get(server_name)
        }
    
    return status

def print_manual_configuration_instructions():
    """
    Affiche les instructions pour la configuration manuelle des serveurs VNC.
    """
    print('🛠️ INSTRUCTIONS DE CONFIGURATION MANUELLE DES SERVEURS VNC')
    print('=' * 80)
    print('Les serveurs VNC nécessitent une découverte manuelle de leurs adresses IP.')
    print('Suivez ces étapes pour chaque serveur :')
    print()
    
    for server_name, vnc_info in VNC_CONNECTION_INFO.items():
        print(f'📋 {server_name}:')
        print(f'   1. Ouvrez VNC Viewer')
        print(f'   2. Connectez-vous à {vnc_info["host"]}:{vnc_info["port"]}')
        print(f'   3. Utilisez les identifiants: {VNC_CREDENTIALS["username"]} / {VNC_CREDENTIALS["password"]}')
        print(f'   4. Ouvrez un terminal et exécutez: ip addr show')
        print(f'   5. Notez l\'adresse IP affichée (format 192.168.x.x)')
        print(f'   6. Mettez à jour VNC_SERVER_IPS[\'{server_name}\'] dans ce fichier')
        print()
    
    print('💡 EXEMPLE DE CONFIGURATION:')
    print('   VNC_SERVER_IPS = {')
    print('       \'Server-Web\': [\'192.168.10.10\'],')
    print('       \'Server-Mail\': [\'192.168.10.12\'],')
    print('       # ... autres serveurs')
    print('   }')
    print()
    print('🔄 Après configuration, relancez le framework pour utiliser ces adresses.')

if __name__ == "__main__":
    # Test du module
    print('🧪 TEST DU MODULE VNC SERVER IPS')
    print('=' * 50)
    
    status = get_configuration_status()
    total_servers = len(status)
    configured_servers = sum(1 for s in status.values() if s['configured'])
    
    print(f'📊 Statut de configuration:')
    print(f'   • Total serveurs: {total_servers}')
    print(f'   • Serveurs configurés: {configured_servers}')
    print(f'   • Taux de configuration: {(configured_servers/total_servers*100):.1f}%')
    print()
    
    for name, info in status.items():
        if info['configured']:
            print(f'✅ {name}: {info["ips"]}')
        else:
            print(f'❌ {name}: Non configuré')
    
    if configured_servers == 0:
        print()
        print_manual_configuration_instructions()