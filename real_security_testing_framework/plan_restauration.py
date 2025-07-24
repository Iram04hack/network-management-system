#!/usr/bin/env python3
"""
Plan de restauration de la topologie GNS3
"""

import json
import requests

# Configuration de l'API GNS3
PROJECT_ID = "6b858ee5-4a49-4f72-b437-8dcd8d876bad"
BASE_URL = "http://localhost:3080/v2/projects/" + PROJECT_ID

# Mapping des équipements critiques
CRITICAL_NODES = {
    'SW-SERVER': '377b7624-395d-40e6-9dc8-e0efb53147a2',
    'PostTest': '8f063731-8467-47ca-9db4-c75a7a5fc087',
    'SW-LAN': '00339e94-db96-4fd9-a273-00dfe9132fc6',
    'PC1': 'e581f562-2fa9-4be6-9362-d76879420b91',
    'SW-DMZ': 'e58c5f3e-4d0f-4900-a70a-c132a80bef85',
    'Server-Mail': '65ea377e-5a84-42a7-8561-1d10d9e79962',
    'Server-DNS': '5a4bb232-e6cf-48d3-b23a-93987a290d52',
    'SW-ADMIN': '408060b2-7529-4af7-a432-545398091d2e',
    'Admin': 'ac3a765c-8d9c-44bb-b1bb-ba30c84086cf'
}

def get_node_ports(node_id):
    """Récupère les informations sur les ports d'un nœud"""
    response = requests.get(f"{BASE_URL}/nodes/{node_id}")
    node_data = response.json()
    return node_data.get('ports', [])

def get_current_links():
    """Récupère les liens actuels"""
    response = requests.get(f"{BASE_URL}/links")
    return response.json()

def find_available_ports(node_id):
    """Trouve les ports disponibles sur un nœud"""
    ports = get_node_ports(node_id)
    current_links = get_current_links()
    
    # Ports utilisés
    used_ports = set()
    for link in current_links:
        for node in link['nodes']:
            if node['node_id'] == node_id:
                port_key = f"{node['adapter_number']}/{node['port_number']}"
                used_ports.add(port_key)
    
    # Ports disponibles
    available_ports = []
    for port in ports:
        port_key = f"{port['adapter_number']}/{port['port_number']}"
        if port_key not in used_ports:
            available_ports.append({
                'adapter_number': port['adapter_number'],
                'port_number': port['port_number'],
                'name': port['name'],
                'short_name': port['short_name']
            })
    
    return available_ports

def generate_restoration_plan():
    """Génère le plan de restauration complet"""
    
    print("=== PLAN DE RESTAURATION DE LA TOPOLOGIE ===\n")
    
    # 1. Analyser les ports disponibles sur les équipements critiques
    print("1. ANALYSE DES PORTS DISPONIBLES:\n")
    
    for node_name, node_id in CRITICAL_NODES.items():
        available_ports = find_available_ports(node_id)
        print(f"{node_name} ({node_id}):")
        if available_ports:
            for port in available_ports[:5]:  # Afficher les 5 premiers ports disponibles
                print(f"   - {port['name']} ({port['short_name']})")
            if len(available_ports) > 5:
                print(f"   ... et {len(available_ports) - 5} autres ports")
        else:
            print("   Aucun port disponible")
        print()
    
    # 2. Plan de connexions à restaurer
    print("2. CONNEXIONS À RESTAURER:\n")
    
    restoration_plan = [
        {
            'description': 'Connexion SW-SERVER vers PostTest',
            'node1': {'name': 'SW-SERVER', 'id': CRITICAL_NODES['SW-SERVER']},
            'node2': {'name': 'PostTest', 'id': CRITICAL_NODES['PostTest']},
            'priority': 'HAUTE',
            'reason': 'Connexion critique pour les tests de sécurité'
        },
        {
            'description': 'Connexion SW-LAN vers PC1',
            'node1': {'name': 'SW-LAN', 'id': CRITICAL_NODES['SW-LAN']},
            'node2': {'name': 'PC1', 'id': CRITICAL_NODES['PC1']},
            'priority': 'HAUTE',
            'reason': 'PC1 isolé du réseau LAN'
        },
        {
            'description': 'Connexion SW-DMZ vers Server-Mail',
            'node1': {'name': 'SW-DMZ', 'id': CRITICAL_NODES['SW-DMZ']},
            'node2': {'name': 'Server-Mail', 'id': CRITICAL_NODES['Server-Mail']},
            'priority': 'MOYENNE',
            'reason': 'Server-Mail isolé dans la DMZ'
        },
        {
            'description': 'Connexion SW-DMZ vers Server-DNS',
            'node1': {'name': 'SW-DMZ', 'id': CRITICAL_NODES['SW-DMZ']},
            'node2': {'name': 'Server-DNS', 'id': CRITICAL_NODES['Server-DNS']},
            'priority': 'MOYENNE',
            'reason': 'Server-DNS isolé dans la DMZ'
        },
        {
            'description': 'Connexion SW-ADMIN vers Admin',
            'node1': {'name': 'SW-ADMIN', 'id': CRITICAL_NODES['SW-ADMIN']},
            'node2': {'name': 'Admin', 'id': CRITICAL_NODES['Admin']},
            'priority': 'MOYENNE',
            'reason': 'Poste Admin isolé du réseau d\'administration'
        }
    ]
    
    for i, connection in enumerate(restoration_plan, 1):
        print(f"Connexion {i}: {connection['description']}")
        print(f"   Priorité: {connection['priority']}")
        print(f"   Raison: {connection['reason']}")
        
        # Trouver les ports disponibles
        ports1 = find_available_ports(connection['node1']['id'])
        ports2 = find_available_ports(connection['node2']['id'])
        
        if ports1 and ports2:
            suggested_port1 = ports1[0]
            suggested_port2 = ports2[0]
            print(f"   Ports suggérés:")
            print(f"      {connection['node1']['name']}: {suggested_port1['short_name']}")
            print(f"      {connection['node2']['name']}: {suggested_port2['short_name']}")
            
            # Générer la commande API
            print(f"   Commande API:")
            api_command = {
                "link_type": "ethernet",
                "nodes": [
                    {
                        "adapter_number": suggested_port1['adapter_number'],
                        "node_id": connection['node1']['id'],
                        "port_number": suggested_port1['port_number']
                    },
                    {
                        "adapter_number": suggested_port2['adapter_number'],
                        "node_id": connection['node2']['id'],
                        "port_number": suggested_port2['port_number']
                    }
                ]
            }
            print(f"      curl -X POST \"{BASE_URL}/links\" \\")
            print(f"           -H \"Content-Type: application/json\" \\")
            print(f"           -d '{json.dumps(api_command, indent=2)}'")
        else:
            print(f"   PROBLÈME: Ports non disponibles")
            if not ports1:
                print(f"      {connection['node1']['name']}: Aucun port libre")
            if not ports2:
                print(f"      {connection['node2']['name']}: Aucun port libre")
        print()
    
    # 3. Script de restauration automatique
    print("3. SCRIPT DE RESTAURATION AUTOMATIQUE:\n")
    
    script_content = f"""#!/bin/bash
# Script de restauration automatique de la topologie GNS3
# Projet: {PROJECT_ID}

BASE_URL="{BASE_URL}"

echo "=== DÉBUT DE LA RESTAURATION ==="

"""
    
    for i, connection in enumerate(restoration_plan, 1):
        ports1 = find_available_ports(connection['node1']['id'])
        ports2 = find_available_ports(connection['node2']['id'])
        
        if ports1 and ports2:
            suggested_port1 = ports1[0]
            suggested_port2 = ports2[0]
            
            api_command = {
                "link_type": "ethernet",
                "nodes": [
                    {
                        "adapter_number": suggested_port1['adapter_number'],
                        "node_id": connection['node1']['id'],
                        "port_number": suggested_port1['port_number']
                    },
                    {
                        "adapter_number": suggested_port2['adapter_number'],
                        "node_id": connection['node2']['id'],
                        "port_number": suggested_port2['port_number']
                    }
                ]
            }
            
            script_content += f"""
echo "Création du lien {i}: {connection['description']}"
curl -X POST "$BASE_URL/links" \\
     -H "Content-Type: application/json" \\
     -d '{json.dumps(api_command)}' \\
     --silent --show-error
if [ $? -eq 0 ]; then
    echo "✓ Lien {i} créé avec succès"
else
    echo "✗ Échec de création du lien {i}"
fi
sleep 1
"""
    
    script_content += """
echo "=== FIN DE LA RESTAURATION ==="
echo "Vérification des liens créés:"
curl -X GET "$BASE_URL/links" | python3 -m json.tool
"""
    
    # Sauvegarder le script
    with open('restaurer_topologie.sh', 'w') as f:
        f.write(script_content)
    
    print("Script sauvegardé dans: restaurer_topologie.sh")
    print("Pour exécuter: chmod +x restaurer_topologie.sh && ./restaurer_topologie.sh")
    
    return restoration_plan

if __name__ == "__main__":
    try:
        plan = generate_restoration_plan()
    except Exception as e:
        print(f"Erreur lors de la génération du plan: {e}")