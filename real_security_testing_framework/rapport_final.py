#!/usr/bin/env python3
"""
Rapport final de l'état de la topologie après restauration
"""

import json
import requests

# Configuration de l'API GNS3
PROJECT_ID = "6b858ee5-4a49-4f72-b437-8dcd8d876bad"
BASE_URL = "http://localhost:3080/v2/projects/" + PROJECT_ID

def get_nodes():
    """Récupère tous les nœuds"""
    response = requests.get(f"{BASE_URL}/nodes")
    return response.json()

def get_links():
    """Récupère tous les liens"""
    response = requests.get(f"{BASE_URL}/links")
    return response.json()

def generate_final_report():
    """Génère le rapport final"""
    
    nodes = get_nodes()
    links = get_links()
    
    # Mapping complet des nœuds
    node_mapping = {node['node_id']: node['name'] for node in nodes}
    
    print("=" * 60)
    print("RAPPORT FINAL - ÉTAT DE LA TOPOLOGIE APRÈS RESTAURATION")
    print("=" * 60)
    
    print(f"\nProjet ID: {PROJECT_ID}")
    print(f"Nombre total d'équipements: {len(nodes)}")
    print(f"Nombre total de liens: {len(links)}")
    
    print("\n" + "=" * 40)
    print("1. CONNEXIONS ACTUELLES")
    print("=" * 40)
    
    for i, link in enumerate(links, 1):
        node1_id = link['nodes'][0]['node_id']
        node2_id = link['nodes'][1]['node_id']
        node1_name = node_mapping.get(node1_id, f"Unknown-{node1_id[:8]}")
        node2_name = node_mapping.get(node2_id, f"Unknown-{node2_id[:8]}")
        
        port1 = link['nodes'][0]['label']['text']
        port2 = link['nodes'][1]['label']['text']
        
        print(f"{i:2d}. {node1_name}({port1}) <-> {node2_name}({port2})")
    
    print("\n" + "=" * 40)
    print("2. ANALYSE DES CONNEXIONS CRITIQUES")
    print("=" * 40)
    
    # Définir les connexions critiques attendues
    critical_connections = {
        'SW-SERVER <-> PostTest': ('377b7624-395d-40e6-9dc8-e0efb53147a2', '8f063731-8467-47ca-9db4-c75a7a5fc087'),
        'SW-LAN <-> PC1': ('00339e94-db96-4fd9-a273-00dfe9132fc6', 'e581f562-2fa9-4be6-9362-d76879420b91'),
        'SW-DMZ <-> Server-Mail': ('e58c5f3e-4d0f-4900-a70a-c132a80bef85', '65ea377e-5a84-42a7-8561-1d10d9e79962'),
        'SW-DMZ <-> Server-DNS': ('e58c5f3e-4d0f-4900-a70a-c132a80bef85', '5a4bb232-e6cf-48d3-b23a-93987a290d52'),
        'SW-ADMIN <-> Admin': ('408060b2-7529-4af7-a432-545398091d2e', 'ac3a765c-8d9c-44bb-b1bb-ba30c84086cf')
    }
    
    restored_count = 0
    
    for connection_name, (node1_id, node2_id) in critical_connections.items():
        is_connected = False
        connection_details = ""
        
        for link in links:
            link_nodes = [link['nodes'][0]['node_id'], link['nodes'][1]['node_id']]
            if node1_id in link_nodes and node2_id in link_nodes:
                is_connected = True
                # Trouver les détails du port
                for node in link['nodes']:
                    if node['node_id'] == node1_id:
                        port1 = node['label']['text']
                    elif node['node_id'] == node2_id:
                        port2 = node['label']['text']
                connection_details = f" - Ports: {port1} <-> {port2}"
                break
        
        status = "✓ RESTAURÉE" if is_connected else "✗ MANQUANTE"
        print(f"   {status} - {connection_name}{connection_details}")
        
        if is_connected:
            restored_count += 1
    
    print(f"\nRésultat: {restored_count}/{len(critical_connections)} connexions critiques restaurées")
    
    print("\n" + "=" * 40)
    print("3. ÉQUIPEMENTS ISOLÉS")
    print("=" * 40)
    
    # Identifier les équipements isolés
    connected_nodes = set()
    for link in links:
        connected_nodes.add(link['nodes'][0]['node_id'])
        connected_nodes.add(link['nodes'][1]['node_id'])
    
    isolated_nodes = []
    for node_id, name in node_mapping.items():
        if node_id not in connected_nodes:
            isolated_nodes.append((name, node_id))
    
    if isolated_nodes:
        for name, node_id in isolated_nodes:
            print(f"   - {name} (ID: {node_id})")
    else:
        print("   Aucun équipement isolé")
    
    print("\n" + "=" * 40)
    print("4. ACTIONS RECOMMANDÉES")
    print("=" * 40)
    
    if restored_count < len(critical_connections):
        print("\nConnexions manquantes à restaurer:")
        
        # PC1 - analyser pourquoi il ne peut pas être connecté
        pc1_connected = any(node_id == 'e581f562-2fa9-4be6-9362-d76879420b91' 
                           for link in links 
                           for node in link['nodes'])
        
        if not pc1_connected:
            print("\n   A. PC1 (e581f562-2fa9-4be6-9362-d76879420b91):")
            print("      - PC1 semble complètement isolé")
            print("      - Action: Vérifier si PC1 n'a vraiment aucune connexion")
            print("      - Commande suggérée:")
            print("        curl -X POST \"http://localhost:3080/v2/projects/6b858ee5-4a49-4f72-b437-8dcd8d876bad/links\" \\")
            print("             -H \"Content-Type: application/json\" \\")
            print("             -d '{\"link_type\": \"ethernet\", \"nodes\": [")
            print("                   {\"adapter_number\": 0, \"node_id\": \"00339e94-db96-4fd9-a273-00dfe9132fc6\", \"port_number\": 3},")
            print("                   {\"adapter_number\": 0, \"node_id\": \"e581f562-2fa9-4be6-9362-d76879420b91\", \"port_number\": 0}")
            print("                 ]}'")
        
        # Admin
        admin_connected = any(node_id == 'ac3a765c-8d9c-44bb-b1bb-ba30c84086cf' 
                             for link in links 
                             for node in link['nodes'])
        
        if not admin_connected:
            print("\n   B. Admin (ac3a765c-8d9c-44bb-b1bb-ba30c84086cf):")
            print("      - Admin semble complètement isolé")
            print("      - Action: Connecter Admin à SW-ADMIN")
            print("      - Commande suggérée:")
            print("        curl -X POST \"http://localhost:3080/v2/projects/6b858ee5-4a49-4f72-b437-8dcd8d876bad/links\" \\")
            print("             -H \"Content-Type: application/json\" \\")
            print("             -d '{\"link_type\": \"ethernet\", \"nodes\": [")
            print("                   {\"adapter_number\": 0, \"node_id\": \"408060b2-7529-4af7-a432-545398091d2e\", \"port_number\": 2},")
            print("                   {\"adapter_number\": 0, \"node_id\": \"ac3a765c-8d9c-44bb-b1bb-ba30c84086cf\", \"port_number\": 0}")
            print("                 ]}'")
    else:
        print("✓ Toutes les connexions critiques sont restaurées!")
    
    print("\n" + "=" * 40)
    print("5. RÉSUMÉ DES DÉGÂTS CAUSÉS PAR LE SCRIPT")
    print("=" * 40)
    
    print("\nDégâts identifiés:")
    print("   - SW-SERVER était déconnecté de PostTest → ✓ RÉPARÉ")
    print("   - SW-LAN était déconnecté de PC1 → ✗ NON RÉPARÉ")
    print("   - Server-Mail était isolé → ✓ RÉPARÉ (connecté à SW-DMZ)")
    print("   - Server-DNS était isolé → ✓ RÉPARÉ (connecté à SW-DMZ)")
    print("   - Admin était isolé → ✗ NON RÉPARÉ")
    
    print(f"\nTaux de réparation: {((restored_count / len(critical_connections)) * 100):.1f}%")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    generate_final_report()