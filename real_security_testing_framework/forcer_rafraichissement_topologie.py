#!/usr/bin/env python3
"""
Script pour forcer le rafraîchissement de la topologie et recréer la connexion sw-admin → Admin si nécessaire
"""
import requests
import json
import time

# Configuration
gns3_server = 'http://localhost:3080'
project_id = '6b858ee5-4a49-4f72-b437-8dcd8d876bad'

def main():
    print("=== FORCER LE RAFRAÎCHISSEMENT DE LA TOPOLOGIE ===")
    
    # 1. Récupérer les équipements
    response = requests.get(f'{gns3_server}/v2/projects/{project_id}/nodes')
    nodes = response.json()
    
    sw_admin = next((n for n in nodes if n['name'] == 'SW-ADMIN'), None)
    admin = next((n for n in nodes if n['name'] == 'Admin'), None)
    
    if not sw_admin or not admin:
        print("❌ SW-ADMIN ou Admin non trouvé")
        return
    
    print(f"✅ SW-ADMIN trouvé: {sw_admin['node_id']}")
    print(f"✅ Admin trouvé: {admin['node_id']}")
    
    # 2. Récupérer les liens actuels
    response = requests.get(f'{gns3_server}/v2/projects/{project_id}/links')
    links = response.json()
    
    # 3. Chercher la connexion existante
    existing_link = None
    for link in links:
        link_nodes = link.get('nodes', [])
        if len(link_nodes) >= 2:
            node1_id = link_nodes[0]['node_id']
            node2_id = link_nodes[1]['node_id']
            
            if (node1_id == sw_admin['node_id'] and node2_id == admin['node_id']) or \
               (node2_id == sw_admin['node_id'] and node1_id == admin['node_id']):
                existing_link = link
                break
    
    if existing_link:
        print(f"✅ Connexion existante trouvée: {existing_link['link_id']}")
        print("🔄 Suppression et recréation de la connexion pour forcer le rafraîchissement...")
        
        # Supprimer la connexion existante
        delete_response = requests.delete(f'{gns3_server}/v2/projects/{project_id}/links/{existing_link["link_id"]}')
        print(f"Suppression: {delete_response.status_code}")
        
        time.sleep(2)
    else:
        print("❌ Aucune connexion existante trouvée")
    
    # 4. Analyser les ports disponibles sur SW-ADMIN
    print("\n=== ANALYSE DES PORTS SW-ADMIN ===")
    sw_admin_used_ports = []
    
    for link in links:
        if link == existing_link:  # Ignorer le lien qu'on vient de supprimer
            continue
            
        for link_node in link.get('nodes', []):
            if link_node['node_id'] == sw_admin['node_id']:
                port_num = link_node.get('port_number', 0)
                sw_admin_used_ports.append(port_num)
                adapter_num = link_node.get('adapter_number', 0)
                print(f"  Port utilisé: ethernet{adapter_num}/{port_num}")
    
    # Trouver un port libre
    free_port = None
    for port in range(0, 4):
        if port not in sw_admin_used_ports:
            free_port = port
            break
    
    if free_port is None:
        free_port = 1  # Forcer le port 1 s'il semble libre
    
    print(f"  Port libre choisi: ethernet0/{free_port}")
    
    # 5. Créer la nouvelle connexion
    print(f"\n=== CRÉATION DE LA CONNEXION SW-ADMIN ↔ ADMIN ===")
    
    link_data = {
        'nodes': [
            {
                'node_id': sw_admin['node_id'],
                'adapter_number': 0,
                'port_number': free_port
            },
            {
                'node_id': admin['node_id'],
                'adapter_number': 0,
                'port_number': 0
            }
        ]
    }
    
    print(f"Création: SW-ADMIN:ethernet0/{free_port} ↔ Admin:ethernet0/0")
    
    create_response = requests.post(f'{gns3_server}/v2/projects/{project_id}/links', json=link_data)
    
    if create_response.status_code == 201:
        link_info = create_response.json()
        print(f"✅ CONNEXION CRÉÉE AVEC SUCCÈS")
        print(f"   Nouvel ID du lien: {link_info['link_id']}")
        
        # Attendre et vérifier
        time.sleep(2)
        
        # 6. Vérification finale
        print(f"\n=== VÉRIFICATION FINALE ===")
        response = requests.get(f'{gns3_server}/v2/projects/{project_id}/links')
        final_links = response.json()
        
        connection_verified = False
        for link in final_links:
            link_nodes = link.get('nodes', [])
            if len(link_nodes) >= 2:
                node1_id = link_nodes[0]['node_id']
                node2_id = link_nodes[1]['node_id']
                
                if (node1_id == sw_admin['node_id'] and node2_id == admin['node_id']) or \
                   (node2_id == sw_admin['node_id'] and node1_id == admin['node_id']):
                    connection_verified = True
                    print(f"✅ CONNEXION VÉRIFIÉE: {link['link_id']}")
                    print(f"   SW-ADMIN port: ethernet{link_nodes[0 if node1_id == sw_admin['node_id'] else 1].get('adapter_number', 0)}/{link_nodes[0 if node1_id == sw_admin['node_id'] else 1].get('port_number', 0)}")
                    print(f"   Admin port: ethernet{link_nodes[1 if node1_id == sw_admin['node_id'] else 0].get('adapter_number', 0)}/{link_nodes[1 if node1_id == sw_admin['node_id'] else 0].get('port_number', 0)}")
                    break
        
        if not connection_verified:
            print("❌ ÉCHEC DE LA VÉRIFICATION")
        
        print(f"\nNombre total de liens finaux: {len(final_links)}")
        
    else:
        print(f"❌ ÉCHEC DE LA CRÉATION: {create_response.status_code}")
        print(f"   Erreur: {create_response.text}")
        
        # Essayer avec un autre port
        if free_port != 1:
            print(f"🔄 Tentative avec le port ethernet0/1...")
            link_data['nodes'][0]['port_number'] = 1
            
            retry_response = requests.post(f'{gns3_server}/v2/projects/{project_id}/links', json=link_data)
            if retry_response.status_code == 201:
                retry_info = retry_response.json()
                print(f"✅ CONNEXION CRÉÉE AU PORT 1: {retry_info['link_id']}")
            else:
                print(f"❌ ÉCHEC ÉGALEMENT AU PORT 1: {retry_response.status_code}")

if __name__ == "__main__":
    main()