#!/usr/bin/env python3
"""
Script pour finaliser la restauration de la topologie
"""

import json
import requests
import time

# Configuration de l'API GNS3
PROJECT_ID = "6b858ee5-4a49-4f72-b437-8dcd8d876bad"
BASE_URL = "http://localhost:3080/v2/projects/" + PROJECT_ID

def create_link(node1_id, port1_adapter, port1_number, node2_id, port2_adapter, port2_number):
    """Crée un nouveau lien"""
    link_data = {
        "link_type": "ethernet",
        "nodes": [
            {
                "adapter_number": port1_adapter,
                "node_id": node1_id,
                "port_number": port1_number
            },
            {
                "adapter_number": port2_adapter,
                "node_id": node2_id,
                "port_number": port2_number
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/links", 
                               headers={"Content-Type": "application/json"},
                               json=link_data)
        return response.status_code == 201, response.json() if response.status_code == 201 else response.text
    except Exception as e:
        return False, str(e)

def finalize_restoration():
    """Finalise la restauration des connexions manquantes"""
    
    print("=== FINALISATION DE LA RESTAURATION ===\n")
    
    # Connexion SW-LAN -> PC1
    print("1. Connexion SW-LAN vers PC1...")
    success, result = create_link(
        "00339e94-db96-4fd9-a273-00dfe9132fc6", 0, 1,  # SW-LAN e0/1
        "e581f562-2fa9-4be6-9362-d76879420b91", 0, 0    # PC1 e0
    )
    if success:
        print("✓ SW-LAN connecté à PC1")
    else:
        print(f"✗ Échec de connexion SW-LAN vers PC1: {result}")
    time.sleep(1)
    
    # Connexion SW-ADMIN -> Admin
    print("2. Connexion SW-ADMIN vers Admin...")
    success, result = create_link(
        "408060b2-7529-4af7-a432-545398091d2e", 0, 1,  # SW-ADMIN e0/1
        "ac3a765c-8d9c-44bb-b1bb-ba30c84086cf", 0, 0    # Admin e0
    )
    if success:
        print("✓ SW-ADMIN connecté à Admin")
    else:
        print(f"✗ Échec de connexion SW-ADMIN vers Admin: {result}")
    time.sleep(1)
    
    print("\n=== VÉRIFICATION FINALE ===")
    
    # Vérification complète
    try:
        response = requests.get(f"{BASE_URL}/links")
        links = response.json()
        print(f"Nombre total de liens: {len(links)}")
        
        # Vérifier toutes les connexions critiques
        nodes_mapping = {
            '377b7624-395d-40e6-9dc8-e0efb53147a2': 'SW-SERVER',
            '8f063731-8467-47ca-9db4-c75a7a5fc087': 'PostTest',
            '00339e94-db96-4fd9-a273-00dfe9132fc6': 'SW-LAN',
            'e581f562-2fa9-4be6-9362-d76879420b91': 'PC1',
            'e58c5f3e-4d0f-4900-a70a-c132a80bef85': 'SW-DMZ',
            '65ea377e-5a84-42a7-8561-1d10d9e79962': 'Server-Mail',
            '5a4bb232-e6cf-48d3-b23a-93987a290d52': 'Server-DNS',
            '408060b2-7529-4af7-a432-545398091d2e': 'SW-ADMIN',
            'ac3a765c-8d9c-44bb-b1bb-ba30c84086cf': 'Admin'
        }
        
        all_connections = []
        for link in links:
            node1_id = link['nodes'][0]['node_id']
            node2_id = link['nodes'][1]['node_id']
            node1_name = nodes_mapping.get(node1_id, f"Node-{node1_id[:8]}")
            node2_name = nodes_mapping.get(node2_id, f"Node-{node2_id[:8]}")
            
            port1 = link['nodes'][0]['label']['text']
            port2 = link['nodes'][1]['label']['text']
            
            all_connections.append(f"{node1_name}({port1}) <-> {node2_name}({port2})")
        
        print("\nToutes les connexions actuelles:")
        for conn in sorted(all_connections):
            print(f"   - {conn}")
        
        # Vérification des connexions critiques restaurées
        critical_connections = [
            ('SW-SERVER', 'PostTest'),
            ('SW-LAN', 'PC1'),
            ('SW-DMZ', 'Server-Mail'),
            ('SW-DMZ', 'Server-DNS'),
            ('SW-ADMIN', 'Admin')
        ]
        
        verified_connections = []
        for link in links:
            node1_id = link['nodes'][0]['node_id']
            node2_id = link['nodes'][1]['node_id']
            node1_name = nodes_mapping.get(node1_id)
            node2_name = nodes_mapping.get(node2_id)
            
            if node1_name and node2_name:
                connection = (node1_name, node2_name)
                reverse_connection = (node2_name, node1_name)
                
                for critical in critical_connections:
                    if connection == critical or reverse_connection == critical:
                        verified_connections.append(critical)
        
        print("\nRésumé des connexions critiques:")
        all_restored = True
        for connection in critical_connections:
            status = "✓" if connection in verified_connections else "✗"
            print(f"   {status} {connection[0]} <-> {connection[1]}")
            if connection not in verified_connections:
                all_restored = False
        
        print(f"\nStatut: {len(verified_connections)}/{len(critical_connections)} connexions critiques restaurées")
        
        if all_restored:
            print("🎉 TOUTES LES CONNEXIONS CRITIQUES SONT RESTAURÉES !")
        else:
            print("⚠️  Certaines connexions restent à restaurer")
        
    except Exception as e:
        print(f"Erreur lors de la vérification: {e}")

if __name__ == "__main__":
    finalize_restoration()