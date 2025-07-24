#!/usr/bin/env python3
"""
Script pour vérifier spécifiquement la connexion SW-ADMIN → Admin
"""
import requests
import json

# Configuration
gns3_server = 'http://localhost:3080'
project_id = '6b858ee5-4a49-4f72-b437-8dcd8d876bad'

def main():
    print("=== VÉRIFICATION SPÉCIFIQUE SW-ADMIN → ADMIN ===")
    
    # Récupérer tous les nœuds
    response = requests.get(f'{gns3_server}/v2/projects/{project_id}/nodes')
    nodes = response.json()
    
    # Trouver SW-ADMIN et Admin
    sw_admin = None
    admin = None
    
    for node in nodes:
        if node['name'] == 'SW-ADMIN':
            sw_admin = node
        elif node['name'] == 'Admin':
            admin = node
    
    if not sw_admin:
        print("❌ SW-ADMIN non trouvé")
        return
    if not admin:
        print("❌ Admin non trouvé")
        return
    
    print(f"✅ SW-ADMIN trouvé: {sw_admin['node_id']} (statut: {sw_admin['status']})")
    print(f"✅ Admin trouvé: {admin['node_id']} (statut: {admin['status']})")
    
    # Récupérer tous les liens
    response = requests.get(f'{gns3_server}/v2/projects/{project_id}/links')
    links = response.json()
    
    print(f"\n=== ANALYSE DES LIENS (total: {len(links)}) ===")
    
    # Chercher la connexion SW-ADMIN ↔ Admin
    sw_admin_links = []
    admin_links = []
    connection_found = False
    
    for link in links:
        link_nodes = link.get('nodes', [])
        if len(link_nodes) >= 2:
            node1_id = link_nodes[0]['node_id']
            node2_id = link_nodes[1]['node_id']
            
            # Vérifier si SW-ADMIN est dans ce lien
            if node1_id == sw_admin['node_id']:
                sw_admin_links.append({
                    'target_id': node2_id,
                    'my_port': f"ethernet{link_nodes[0].get('adapter_number', 0)}/{link_nodes[0].get('port_number', 0)}",
                    'target_port': f"ethernet{link_nodes[1].get('adapter_number', 0)}/{link_nodes[1].get('port_number', 0)}",
                    'link_id': link['link_id']
                })
                
                # Vérifier si c'est connecté à Admin
                if node2_id == admin['node_id']:
                    connection_found = True
                    print(f"✅ CONNEXION TROUVÉE: SW-ADMIN → Admin")
                    print(f"   Lien ID: {link['link_id']}")
                    print(f"   SW-ADMIN port: {link_nodes[0].get('adapter_number', 0)}/{link_nodes[0].get('port_number', 0)}")
                    print(f"   Admin port: {link_nodes[1].get('adapter_number', 0)}/{link_nodes[1].get('port_number', 0)}")
            
            elif node2_id == sw_admin['node_id']:
                sw_admin_links.append({
                    'target_id': node1_id,
                    'my_port': f"ethernet{link_nodes[1].get('adapter_number', 0)}/{link_nodes[1].get('port_number', 0)}",
                    'target_port': f"ethernet{link_nodes[0].get('adapter_number', 0)}/{link_nodes[0].get('port_number', 0)}",
                    'link_id': link['link_id']
                })
                
                # Vérifier si c'est connecté à Admin
                if node1_id == admin['node_id']:
                    connection_found = True
                    print(f"✅ CONNEXION TROUVÉE: Admin → SW-ADMIN")
                    print(f"   Lien ID: {link['link_id']}")
                    print(f"   Admin port: {link_nodes[0].get('adapter_number', 0)}/{link_nodes[0].get('port_number', 0)}")
                    print(f"   SW-ADMIN port: {link_nodes[1].get('adapter_number', 0)}/{link_nodes[1].get('port_number', 0)}")
            
            # Vérifier si Admin est dans ce lien
            if node1_id == admin['node_id']:
                admin_links.append({
                    'target_id': node2_id,
                    'my_port': f"ethernet{link_nodes[0].get('adapter_number', 0)}/{link_nodes[0].get('port_number', 0)}",
                    'target_port': f"ethernet{link_nodes[1].get('adapter_number', 0)}/{link_nodes[1].get('port_number', 0)}",
                    'link_id': link['link_id']
                })
            elif node2_id == admin['node_id']:
                admin_links.append({
                    'target_id': node1_id,
                    'my_port': f"ethernet{link_nodes[1].get('adapter_number', 0)}/{link_nodes[1].get('port_number', 0)}",
                    'target_port': f"ethernet{link_nodes[0].get('adapter_number', 0)}/{link_nodes[0].get('port_number', 0)}",
                    'link_id': link['link_id']
                })
    
    print(f"\n=== CONNEXIONS DE SW-ADMIN ===")
    print(f"Nombre de connexions: {len(sw_admin_links)}")
    for i, link in enumerate(sw_admin_links):
        # Trouver le nom du nœud cible
        target_node = next((n for n in nodes if n['node_id'] == link['target_id']), None)
        target_name = target_node['name'] if target_node else 'Inconnu'
        print(f"  {i+1}. {target_name} via {link['my_port']} ↔ {link['target_port']}")
    
    print(f"\n=== CONNEXIONS D'ADMIN ===")
    print(f"Nombre de connexions: {len(admin_links)}")
    for i, link in enumerate(admin_links):
        # Trouver le nom du nœud cible
        target_node = next((n for n in nodes if n['node_id'] == link['target_id']), None)
        target_name = target_node['name'] if target_node else 'Inconnu'
        print(f"  {i+1}. {target_name} via {link['my_port']} ↔ {link['target_port']}")
    
    print(f"\n=== RÉSULTAT FINAL ===")
    if connection_found:
        print("✅ LA CONNEXION SW-ADMIN ↔ ADMIN EXISTE")
    else:
        print("❌ LA CONNEXION SW-ADMIN ↔ ADMIN N'EXISTE PAS")
        print("\n=== TENTATIVE DE CRÉATION DE LA CONNEXION ===")
        
        # Analyser les ports disponibles sur SW-ADMIN
        print("Ports SW-ADMIN utilisés:")
        sw_admin_used_ports = []
        for link in sw_admin_links:
            port = link['my_port'].split('/')
            if len(port) >= 2:
                sw_admin_used_ports.append(int(port[1]))
        
        print(f"  Ports utilisés: {sorted(sw_admin_used_ports)}")
        
        # Trouver un port libre sur SW-ADMIN
        free_port = None
        for port_num in range(0, 4):  # Essayer ports 0-3
            if port_num not in sw_admin_used_ports:
                free_port = port_num
                break
        
        if free_port is not None:
            print(f"  Port libre trouvé: ethernet0/{free_port}")
            
            # Créer la connexion
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
            
            print(f"Création du lien SW-ADMIN:ethernet0/{free_port} ↔ Admin:ethernet0/0...")
            response = requests.post(f'{gns3_server}/v2/projects/{project_id}/links', json=link_data)
            
            if response.status_code == 201:
                link_info = response.json()
                print(f"✅ CONNEXION CRÉÉE AVEC SUCCÈS")
                print(f"   ID du lien: {link_info['link_id']}")
            else:
                print(f"❌ ÉCHEC DE LA CRÉATION: {response.status_code}")
                print(f"   Réponse: {response.text}")
        else:
            print("❌ Aucun port libre trouvé sur SW-ADMIN")

if __name__ == "__main__":
    main()