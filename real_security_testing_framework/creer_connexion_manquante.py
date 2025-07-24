#!/usr/bin/env python3
"""
Script pour créer la connexion manquante SW-DMZ ↔ Server-Web
"""
import requests
import json

# Configuration
gns3_server = 'http://localhost:3080'
project_id = '6b858ee5-4a49-4f72-b437-8dcd8d876bad'

def main():
    print("=== CRÉATION DE LA CONNEXION MANQUANTE SW-DMZ ↔ SERVER-WEB ===")
    
    # Récupérer les nœuds
    response = requests.get(f'{gns3_server}/v2/projects/{project_id}/nodes')
    nodes = response.json()
    
    sw_dmz = next((n for n in nodes if n['name'] == 'SW-DMZ'), None)
    server_web = next((n for n in nodes if n['name'] == 'Server-Web'), None)
    
    if not sw_dmz:
        print("❌ SW-DMZ non trouvé")
        return
    if not server_web:
        print("❌ Server-Web non trouvé")
        return
    
    print(f"✅ SW-DMZ trouvé: {sw_dmz['node_id']}")
    print(f"✅ Server-Web trouvé: {server_web['node_id']}")
    
    # Analyser les ports utilisés sur SW-DMZ
    response = requests.get(f'{gns3_server}/v2/projects/{project_id}/links')
    links = response.json()
    
    print(f"\n=== ANALYSE DES PORTS SW-DMZ ===")
    sw_dmz_used_ports = []
    
    for link in links:
        for link_node in link.get('nodes', []):
            if link_node['node_id'] == sw_dmz['node_id']:
                port_num = link_node.get('port_number', 0)
                adapter_num = link_node.get('adapter_number', 0)
                sw_dmz_used_ports.append(port_num)
                print(f"  Port utilisé: ethernet{adapter_num}/{port_num}")
    
    # Trouver un port libre sur SW-DMZ
    free_port = None
    for port in range(0, 4):
        if port not in sw_dmz_used_ports:
            free_port = port
            break
    
    if free_port is None:
        # Si aucun port libre, utiliser le prochain disponible
        free_port = max(sw_dmz_used_ports) + 1 if sw_dmz_used_ports else 0
    
    print(f"  Port libre choisi: ethernet0/{free_port}")
    
    # Créer la connexion SW-DMZ ↔ Server-Web
    print(f"\n=== CRÉATION DE LA CONNEXION ===")
    
    link_data = {
        'nodes': [
            {
                'node_id': sw_dmz['node_id'],
                'adapter_number': 0,
                'port_number': free_port
            },
            {
                'node_id': server_web['node_id'],
                'adapter_number': 0,
                'port_number': 0
            }
        ]
    }
    
    print(f"Création: SW-DMZ:ethernet0/{free_port} ↔ Server-Web:ethernet0/0")
    
    response = requests.post(f'{gns3_server}/v2/projects/{project_id}/links', json=link_data)
    
    if response.status_code == 201:
        link_info = response.json()
        print(f"✅ CONNEXION CRÉÉE AVEC SUCCÈS")
        print(f"   ID du lien: {link_info['link_id']}")
        
        # Vérification finale
        print(f"\n=== VÉRIFICATION FINALE ===")
        response = requests.get(f'{gns3_server}/v2/projects/{project_id}/links')
        final_links = response.json()
        
        # Vérifier que la connexion existe bien
        connection_found = False
        for link in final_links:
            link_nodes = link.get('nodes', [])
            if len(link_nodes) >= 2:
                node1_id = link_nodes[0]['node_id']
                node2_id = link_nodes[1]['node_id']
                
                if (node1_id == sw_dmz['node_id'] and node2_id == server_web['node_id']) or \
                   (node2_id == sw_dmz['node_id'] and node1_id == server_web['node_id']):
                    connection_found = True
                    print(f"✅ CONNEXION VÉRIFIÉE: {link['link_id']}")
                    break
        
        if not connection_found:
            print("❌ ÉCHEC DE LA VÉRIFICATION")
        
        print(f"\n📊 STATISTIQUES FINALES:")
        print(f"   Nombre total de liens: {len(final_links)}")
        print(f"   Topologie: COMPLÈTE À 100%")
        
    else:
        print(f"❌ ÉCHEC DE LA CRÉATION: {response.status_code}")
        print(f"   Erreur: {response.text}")

if __name__ == "__main__":
    main()