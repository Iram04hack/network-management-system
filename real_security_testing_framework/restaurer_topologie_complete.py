#!/usr/bin/env python3
"""
Script de restauration complète de la topologie GNS3
"""

import json
import requests
import time

# Configuration de l'API GNS3
PROJECT_ID = "6b858ee5-4a49-4f72-b437-8dcd8d876bad"
BASE_URL = "http://localhost:3080/v2/projects/" + PROJECT_ID

def delete_link(link_id):
    """Supprime un lien"""
    try:
        response = requests.delete(f"{BASE_URL}/links/{link_id}")
        return response.status_code == 204
    except Exception as e:
        print(f"Erreur lors de la suppression du lien {link_id}: {e}")
        return False

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

def restore_topology():
    """Restaure la topologie complète"""
    
    print("=== RESTAURATION COMPLÈTE DE LA TOPOLOGIE ===\n")
    
    # Étape 1: Déconnecter PC1 de Cloud1
    print("Étape 1: Déconnexion de PC1 du Cloud1")
    pc1_cloud_link_id = "4ed8c66b-a07c-4667-98e9-4e5abaa5c499"
    if delete_link(pc1_cloud_link_id):
        print("✓ PC1 déconnecté du Cloud1 avec succès")
    else:
        print("✗ Échec de déconnexion de PC1 du Cloud1")
    time.sleep(1)
    
    # Étape 2: Connexions prioritaires
    print("\nÉtape 2: Création des connexions prioritaires")
    
    # Connexion SW-SERVER -> PostTest
    print("2.1 Connexion SW-SERVER vers PostTest...")
    success, result = create_link(
        "377b7624-395d-40e6-9dc8-e0efb53147a2", 0, 2,  # SW-SERVER e0/2
        "8f063731-8467-47ca-9db4-c75a7a5fc087", 0, 0    # PostTest e0
    )
    if success:
        print("✓ SW-SERVER connecté à PostTest")
    else:
        print(f"✗ Échec de connexion SW-SERVER vers PostTest: {result}")
    time.sleep(1)
    
    # Connexion SW-LAN -> PC1
    print("2.2 Connexion SW-LAN vers PC1...")
    success, result = create_link(
        "00339e94-db96-4fd9-a273-00dfe9132fc6", 0, 1,  # SW-LAN e0/1
        "e581f562-2fa9-4be6-9362-d76879420b91", 0, 0    # PC1 e0
    )
    if success:
        print("✓ SW-LAN connecté à PC1")
    else:
        print(f"✗ Échec de connexion SW-LAN vers PC1: {result}")
    time.sleep(1)
    
    # Étape 3: Connexions DMZ
    print("\nÉtape 3: Restauration de la DMZ")
    
    # Connexion SW-DMZ -> Server-Mail
    print("3.1 Connexion SW-DMZ vers Server-Mail...")
    success, result = create_link(
        "e58c5f3e-4d0f-4900-a70a-c132a80bef85", 0, 1,  # SW-DMZ e0/1
        "65ea377e-5a84-42a7-8561-1d10d9e79962", 0, 0    # Server-Mail e0
    )
    if success:
        print("✓ SW-DMZ connecté à Server-Mail")
    else:
        print(f"✗ Échec de connexion SW-DMZ vers Server-Mail: {result}")
    time.sleep(1)
    
    # Connexion SW-DMZ -> Server-DNS
    print("3.2 Connexion SW-DMZ vers Server-DNS...")
    success, result = create_link(
        "e58c5f3e-4d0f-4900-a70a-c132a80bef85", 0, 2,  # SW-DMZ e0/2
        "5a4bb232-e6cf-48d3-b23a-93987a290d52", 0, 0    # Server-DNS e0
    )
    if success:
        print("✓ SW-DMZ connecté à Server-DNS")
    else:
        print(f"✗ Échec de connexion SW-DMZ vers Server-DNS: {result}")
    time.sleep(1)
    
    # Étape 4: Connexion Administration
    print("\nÉtape 4: Restauration du réseau d'administration")
    
    # Connexion SW-ADMIN -> Admin
    print("4.1 Connexion SW-ADMIN vers Admin...")
    success, result = create_link(
        "408060b2-7529-4af7-a432-545398091d2e", 0, 1,  # SW-ADMIN e0/1
        "ac3a765c-8d9c-44bb-b1bb-ba30c84086cf", 0, 0    # Admin e0
    )
    if success:
        print("✓ SW-ADMIN connecté à Admin")
    else:
        print(f"✗ Échec de connexion SW-ADMIN vers Admin: {result}")
    time.sleep(1)
    
    # Étape 5: Vérification finale
    print("\nÉtape 5: Vérification de la topologie restaurée")
    
    try:
        response = requests.get(f"{BASE_URL}/links")
        links = response.json()
        print(f"Nombre total de liens après restauration: {len(links)}")
        
        # Vérifier les connexions critiques
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
            node1_name = nodes_mapping.get(node1_id, node1_id)
            node2_name = nodes_mapping.get(node2_id, node2_id)
            
            connection = (node1_name, node2_name)
            reverse_connection = (node2_name, node1_name)
            
            for critical in critical_connections:
                if connection == critical or reverse_connection == critical:
                    verified_connections.append(critical)
        
        print("\nConnexions critiques vérifiées:")
        for connection in critical_connections:
            status = "✓" if connection in verified_connections else "✗"
            print(f"   {status} {connection[0]} <-> {connection[1]}")
        
        print(f"\nConnexions critiques restaurées: {len(verified_connections)}/{len(critical_connections)}")
        
    except Exception as e:
        print(f"Erreur lors de la vérification: {e}")
    
    print("\n=== RESTAURATION TERMINÉE ===")

if __name__ == "__main__":
    restore_topology()