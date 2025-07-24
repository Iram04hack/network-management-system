#!/usr/bin/env python3
"""
Script pour analyser en détail les connexions du Server-Web
"""
import requests
import json

# Configuration
gns3_server = 'http://localhost:3080'
project_id = '6b858ee5-4a49-4f72-b437-8dcd8d876bad'

def main():
    print("=== ANALYSE DÉTAILLÉE DES CONNEXIONS SERVER-WEB ===")
    
    # Récupérer les nœuds
    response = requests.get(f'{gns3_server}/v2/projects/{project_id}/nodes')
    nodes = response.json()
    
    # Récupérer les liens
    response = requests.get(f'{gns3_server}/v2/projects/{project_id}/links')
    links = response.json()
    
    # Trouver Server-Web
    server_web = next((n for n in nodes if n['name'] == 'Server-Web'), None)
    if not server_web:
        print("❌ Server-Web non trouvé")
        return
    
    print(f"✅ Server-Web trouvé: {server_web['node_id']}")
    print(f"   Type: {server_web['node_type']}")
    print(f"   Statut: {server_web['status']}")
    
    # Analyser toutes les connexions de Server-Web
    print(f"\n=== CONNEXIONS ACTUELLES DE SERVER-WEB ===")
    server_web_connections = []
    
    node_names = {node['node_id']: node['name'] for node in nodes}
    
    for link in links:
        link_nodes = link.get('nodes', [])
        if len(link_nodes) >= 2:
            node1_id = link_nodes[0]['node_id']
            node2_id = link_nodes[1]['node_id']
            
            if node1_id == server_web['node_id']:
                target_name = node_names.get(node2_id, 'Inconnu')
                port_info = f"ethernet{link_nodes[0].get('adapter_number', 0)}/{link_nodes[0].get('port_number', 0)}"
                target_port = f"ethernet{link_nodes[1].get('adapter_number', 0)}/{link_nodes[1].get('port_number', 0)}"
                server_web_connections.append({
                    'target': target_name,
                    'my_port': port_info,
                    'target_port': target_port,
                    'link_id': link['link_id']
                })
                print(f"  ✅ Server-Web:{port_info} ↔ {target_name}:{target_port} (ID: {link['link_id']})")
                
            elif node2_id == server_web['node_id']:
                target_name = node_names.get(node1_id, 'Inconnu')
                port_info = f"ethernet{link_nodes[1].get('adapter_number', 0)}/{link_nodes[1].get('port_number', 0)}"
                target_port = f"ethernet{link_nodes[0].get('adapter_number', 0)}/{link_nodes[0].get('port_number', 0)}"
                server_web_connections.append({
                    'target': target_name,
                    'my_port': port_info,
                    'target_port': target_port,
                    'link_id': link['link_id']
                })
                print(f"  ✅ Server-Web:{port_info} ↔ {target_name}:{target_port} (ID: {link['link_id']})")
    
    if not server_web_connections:
        print("  ❌ Server-Web n'a AUCUNE connexion")
    else:
        print(f"  📊 Server-Web a {len(server_web_connections)} connexion(s)")
    
    # Analyser Cloud1 et ses connexions
    print(f"\n=== ANALYSE DE CLOUD1 ===")
    cloud1 = next((n for n in nodes if n['name'] == 'Cloud1'), None)
    if cloud1:
        print(f"✅ Cloud1 trouvé: {cloud1['node_id']}")
        print(f"   Statut: {cloud1['status']}")
        
        cloud1_connections = []
        for link in links:
            link_nodes = link.get('nodes', [])
            if len(link_nodes) >= 2:
                node1_id = link_nodes[0]['node_id']
                node2_id = link_nodes[1]['node_id']
                
                if node1_id == cloud1['node_id']:
                    target_name = node_names.get(node2_id, 'Inconnu')
                    port_info = f"ethernet{link_nodes[0].get('adapter_number', 0)}/{link_nodes[0].get('port_number', 0)}"
                    target_port = f"ethernet{link_nodes[1].get('adapter_number', 0)}/{link_nodes[1].get('port_number', 0)}"
                    cloud1_connections.append(target_name)
                    print(f"  ✅ Cloud1:{port_info} ↔ {target_name}:{target_port}")
                    
                elif node2_id == cloud1['node_id']:
                    target_name = node_names.get(node1_id, 'Inconnu')
                    port_info = f"ethernet{link_nodes[1].get('adapter_number', 0)}/{link_nodes[1].get('port_number', 0)}"
                    target_port = f"ethernet{link_nodes[0].get('adapter_number', 0)}/{link_nodes[0].get('port_number', 0)}"
                    cloud1_connections.append(target_name)
                    print(f"  ✅ Cloud1:{port_info} ↔ {target_name}:{target_port}")
        
        print(f"  📊 Cloud1 connexions: {cloud1_connections}")
    
    # Analyser SW-DMZ et ses connexions
    print(f"\n=== ANALYSE DE SW-DMZ ===")
    sw_dmz = next((n for n in nodes if n['name'] == 'SW-DMZ'), None)
    if sw_dmz:
        print(f"✅ SW-DMZ trouvé: {sw_dmz['node_id']}")
        
        sw_dmz_connections = []
        for link in links:
            link_nodes = link.get('nodes', [])
            if len(link_nodes) >= 2:
                node1_id = link_nodes[0]['node_id']
                node2_id = link_nodes[1]['node_id']
                
                if node1_id == sw_dmz['node_id']:
                    target_name = node_names.get(node2_id, 'Inconnu')
                    port_info = f"ethernet{link_nodes[0].get('adapter_number', 0)}/{link_nodes[0].get('port_number', 0)}"
                    target_port = f"ethernet{link_nodes[1].get('adapter_number', 0)}/{link_nodes[1].get('port_number', 0)}"
                    sw_dmz_connections.append(target_name)
                    print(f"  ✅ SW-DMZ:{port_info} ↔ {target_name}:{target_port}")
                    
                elif node2_id == sw_dmz['node_id']:
                    target_name = node_names.get(node1_id, 'Inconnu')
                    port_info = f"ethernet{link_nodes[1].get('adapter_number', 0)}/{link_nodes[1].get('port_number', 0)}"
                    target_port = f"ethernet{link_nodes[0].get('adapter_number', 0)}/{link_nodes[0].get('port_number', 0)}"
                    sw_dmz_connections.append(target_name)
                    print(f"  ✅ SW-DMZ:{port_info} ↔ {target_name}:{target_port}")
        
        print(f"  📊 SW-DMZ connexions: {sw_dmz_connections}")
    
    # Conclusion et recommandations
    print(f"\n=== CONCLUSION ===")
    
    if 'Server-Web' in [conn['target'] for conn in server_web_connections]:
        print("✅ Server-Web semble déjà connecté")
    elif 'Server-Web' in cloud1_connections if 'cloud1_connections' in locals() else []:
        print("✅ Server-Web est connecté via Cloud1")
        print("💡 Ceci est normal pour une DMZ - Cloud1 sert de pont réseau")
    elif not server_web_connections:
        print("❌ Server-Web n'est PAS connecté")
        print("🔧 Nécessite une connexion directe à SW-DMZ ou via Cloud1")
    
    print(f"\n📊 RÉSUMÉ TOPOLOGIE DMZ:")
    print(f"   SW-DMZ connecté à: {sw_dmz_connections if 'sw_dmz_connections' in locals() else 'N/A'}")
    print(f"   Cloud1 connecté à: {cloud1_connections if 'cloud1_connections' in locals() else 'N/A'}")
    print(f"   Server-Web connecté à: {[conn['target'] for conn in server_web_connections]}")

if __name__ == "__main__":
    main()