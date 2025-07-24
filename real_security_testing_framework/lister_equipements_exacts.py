#!/usr/bin/env python3
"""
Script pour lister tous les équipements avec leurs noms EXACTS
"""
import requests
import json

# Configuration
gns3_server = 'http://localhost:3080'
project_id = '6b858ee5-4a49-4f72-b437-8dcd8d876bad'

def main():
    print("=== LISTE EXACTE DE TOUS LES ÉQUIPEMENTS ===")
    
    # Récupérer tous les nœuds
    response = requests.get(f'{gns3_server}/v2/projects/{project_id}/nodes')
    nodes = response.json()
    
    print(f"Nombre total d'équipements: {len(nodes)}")
    print("\n=== NOMS EXACTS DES ÉQUIPEMENTS ===")
    
    for i, node in enumerate(nodes):
        print(f"{i+1:2d}. '{node['name']}' (ID: {node['node_id']}, Type: {node['node_type']}, Statut: {node['status']})")
    
    # Chercher spécifiquement les variantes de sw-admin et Admin
    print("\n=== RECHERCHE SPÉCIFIQUE ===")
    
    sw_admin_variants = []
    admin_variants = []
    
    for node in nodes:
        name_lower = node['name'].lower()
        if 'admin' in name_lower and 'sw' in name_lower:
            sw_admin_variants.append(node)
        elif 'admin' in name_lower and 'sw' not in name_lower:
            admin_variants.append(node)
    
    print(f"Équipements contenant 'sw' et 'admin': {len(sw_admin_variants)}")
    for node in sw_admin_variants:
        print(f"  - '{node['name']}' (ID: {node['node_id']})")
    
    print(f"\nÉquipements contenant 'admin' (sans 'sw'): {len(admin_variants)}")
    for node in admin_variants:
        print(f"  - '{node['name']}' (ID: {node['node_id']})")
    
    # Vérifier les connexions pour tous les équipements admin
    if sw_admin_variants and admin_variants:
        print(f"\n=== VÉRIFICATION DES CONNEXIONS ENTRE ÉQUIPEMENTS ADMIN ===")
        
        # Récupérer tous les liens
        response = requests.get(f'{gns3_server}/v2/projects/{project_id}/links')
        links = response.json()
        
        for sw_node in sw_admin_variants:
            for admin_node in admin_variants:
                print(f"\nVérification connexion '{sw_node['name']}' ↔ '{admin_node['name']}':")
                
                connection_found = False
                for link in links:
                    link_nodes = link.get('nodes', [])
                    if len(link_nodes) >= 2:
                        node1_id = link_nodes[0]['node_id']
                        node2_id = link_nodes[1]['node_id']
                        
                        if (node1_id == sw_node['node_id'] and node2_id == admin_node['node_id']) or \
                           (node2_id == sw_node['node_id'] and node1_id == admin_node['node_id']):
                            connection_found = True
                            print(f"  ✅ CONNEXION TROUVÉE (Lien ID: {link['link_id']})")
                            print(f"     Port 1: ethernet{link_nodes[0].get('adapter_number', 0)}/{link_nodes[0].get('port_number', 0)}")
                            print(f"     Port 2: ethernet{link_nodes[1].get('adapter_number', 0)}/{link_nodes[1].get('port_number', 0)}")
                            break
                
                if not connection_found:
                    print(f"  ❌ AUCUNE CONNEXION TROUVÉE")
                    
                    # Tenter de créer la connexion
                    print(f"  🔧 TENTATIVE DE CRÉATION DE LA CONNEXION...")
                    
                    # Analyser les ports utilisés sur sw_node
                    used_ports_sw = []
                    for link in links:
                        for link_node in link.get('nodes', []):
                            if link_node['node_id'] == sw_node['node_id']:
                                used_ports_sw.append(link_node.get('port_number', 0))
                    
                    # Trouver un port libre
                    free_port_sw = None
                    for port in range(0, 4):
                        if port not in used_ports_sw:
                            free_port_sw = port
                            break
                    
                    if free_port_sw is not None:
                        link_data = {
                            'nodes': [
                                {
                                    'node_id': sw_node['node_id'],
                                    'adapter_number': 0,
                                    'port_number': free_port_sw
                                },
                                {
                                    'node_id': admin_node['node_id'],
                                    'adapter_number': 0,
                                    'port_number': 0
                                }
                            ]
                        }
                        
                        print(f"     Création: {sw_node['name']}:ethernet0/{free_port_sw} ↔ {admin_node['name']}:ethernet0/0")
                        response = requests.post(f'{gns3_server}/v2/projects/{project_id}/links', json=link_data)
                        
                        if response.status_code == 201:
                            link_info = response.json()
                            print(f"     ✅ CONNEXION CRÉÉE (ID: {link_info['link_id']})")
                        else:
                            print(f"     ❌ ÉCHEC: {response.status_code} - {response.text}")
                    else:
                        print(f"     ❌ Aucun port libre sur {sw_node['name']}")

if __name__ == "__main__":
    main()