#!/usr/bin/env python3
"""
Script d'analyse de l'état actuel de la topologie GNS3
"""

import json
import requests

# Configuration de l'API GNS3
PROJECT_ID = "6b858ee5-4a49-4f72-b437-8dcd8d876bad"
BASE_URL = "http://localhost:3080/v2/projects/" + PROJECT_ID

def get_nodes():
    """Récupère tous les nœuds du projet"""
    response = requests.get(f"{BASE_URL}/nodes")
    return response.json()

def get_links():
    """Récupère tous les liens du projet"""
    response = requests.get(f"{BASE_URL}/links")
    return response.json()

def analyze_topology():
    """Analyse l'état actuel de la topologie"""
    nodes = get_nodes()
    links = get_links()
    
    # Créer un dictionnaire de correspondance ID -> nom
    node_mapping = {node['node_id']: node['name'] for node in nodes}
    
    print("=== ANALYSE DE LA TOPOLOGIE GNS3 ===\n")
    
    print("1. ÉQUIPEMENTS PRÉSENTS:")
    for node_id, name in node_mapping.items():
        print(f"   - {name}: {node_id}")
    
    print(f"\nNombre total d'équipements: {len(nodes)}")
    print(f"Nombre total de liens: {len(links)}")
    
    print("\n2. CONNEXIONS ACTUELLES:")
    connections = []
    for link in links:
        node1_id = link['nodes'][0]['node_id']
        node2_id = link['nodes'][1]['node_id']
        node1_name = node_mapping.get(node1_id, "INCONNU")
        node2_name = node_mapping.get(node2_id, "INCONNU")
        
        port1 = link['nodes'][0]['label']['text']
        port2 = link['nodes'][1]['label']['text']
        
        connection = f"{node1_name}({port1}) <-> {node2_name}({port2})"
        connections.append(connection)
        print(f"   - {connection}")
    
    print("\n3. ANALYSE DES CONNEXIONS CRITIQUES:")
    
    # Vérifier SW-SERVER <-> PostTest
    sw_server_id = "377b7624-395d-40e6-9dc8-e0efb53147a2"
    posttest_id = "8f063731-8467-47ca-9db4-c75a7a5fc087"
    
    sw_server_connected = False
    posttest_connected = False
    
    for link in links:
        nodes_in_link = [link['nodes'][0]['node_id'], link['nodes'][1]['node_id']]
        if sw_server_id in nodes_in_link and posttest_id in nodes_in_link:
            sw_server_connected = True
            posttest_connected = True
            break
    
    print(f"   SW-SERVER connecté à PostTest: {'✓' if sw_server_connected else '✗'}")
    
    # Vérifier SW-LAN <-> PC1
    sw_lan_id = "00339e94-db96-4fd9-a273-00dfe9132fc6"
    pc1_id = "e581f562-2fa9-4be6-9362-d76879420b91"
    
    sw_lan_pc1_connected = False
    
    for link in links:
        nodes_in_link = [link['nodes'][0]['node_id'], link['nodes'][1]['node_id']]
        if sw_lan_id in nodes_in_link and pc1_id in nodes_in_link:
            sw_lan_pc1_connected = True
            break
    
    print(f"   SW-LAN connecté à PC1: {'✓' if sw_lan_pc1_connected else '✗'}")
    
    print("\n4. ÉQUIPEMENTS ISOLÉS:")
    connected_nodes = set()
    for link in links:
        connected_nodes.add(link['nodes'][0]['node_id'])
        connected_nodes.add(link['nodes'][1]['node_id'])
    
    isolated_nodes = []
    for node_id, name in node_mapping.items():
        if node_id not in connected_nodes:
            isolated_nodes.append(name)
            print(f"   - {name} (ID: {node_id})")
    
    if not isolated_nodes:
        print("   Aucun équipement isolé détecté")
    
    print("\n5. PORTS UTILISÉS PAR ÉQUIPEMENT:")
    port_usage = {}
    for node_id, name in node_mapping.items():
        port_usage[name] = []
    
    for link in links:
        node1_id = link['nodes'][0]['node_id']
        node2_id = link['nodes'][1]['node_id']
        node1_name = node_mapping.get(node1_id, "INCONNU")
        node2_name = node_mapping.get(node2_id, "INCONNU")
        
        port1 = link['nodes'][0]['label']['text']
        port2 = link['nodes'][1]['label']['text']
        
        port_usage[node1_name].append(port1)
        port_usage[node2_name].append(port2)
    
    for equipment, ports in port_usage.items():
        if ports:
            print(f"   {equipment}: {', '.join(sorted(ports))}")
        else:
            print(f"   {equipment}: Aucun port utilisé")
    
    return {
        'nodes': node_mapping,
        'links': links,
        'sw_server_posttest_connected': sw_server_connected,
        'sw_lan_pc1_connected': sw_lan_pc1_connected,
        'isolated_nodes': isolated_nodes,
        'connections': connections
    }

if __name__ == "__main__":
    try:
        result = analyze_topology()
    except Exception as e:
        print(f"Erreur lors de l'analyse: {e}")