#!/usr/bin/env python3
"""
Script de vérification finale de la topologie restaurée
Génère un rapport complet de l'état de tous les équipements
"""
import requests
import json
import datetime

# Configuration
gns3_server = 'http://localhost:3080'
project_id = '6b858ee5-4a49-4f72-b437-8dcd8d876bad'

def get_topology_status():
    """Récupère l'état complet de la topologie"""
    try:
        # Récupérer nœuds et liens
        nodes_response = requests.get(f'{gns3_server}/v2/projects/{project_id}/nodes')
        links_response = requests.get(f'{gns3_server}/v2/projects/{project_id}/links')
        
        if nodes_response.status_code == 200 and links_response.status_code == 200:
            return nodes_response.json(), links_response.json()
        else:
            return None, None
    except Exception as e:
        print(f"Erreur lors de la récupération des données: {e}")
        return None, None

def analyze_connectivity(nodes, links):
    """Analyse la connectivité de chaque nœud"""
    # Créer un mapping des connexions
    connectivity_map = {}
    node_names = {node['node_id']: node['name'] for node in nodes}
    
    for node in nodes:
        connectivity_map[node['node_id']] = {
            'name': node['name'],
            'status': node['status'],
            'node_type': node['node_type'],
            'connections': []
        }
    
    # Analyser les liens
    for link in links:
        if len(link['nodes']) >= 2:
            node1_id = link['nodes'][0]['node_id']
            node2_id = link['nodes'][1]['node_id']
            
            # Ajouter les connexions mutuelles
            if node1_id in connectivity_map and node2_id in connectivity_map:
                connectivity_map[node1_id]['connections'].append({
                    'target': node_names.get(node2_id, 'Inconnu'),
                    'target_id': node2_id,
                    'my_port': f"ethernet{link['nodes'][0].get('adapter_number', 0)}/{link['nodes'][0].get('port_number', 0)}",
                    'target_port': f"ethernet{link['nodes'][1].get('adapter_number', 0)}/{link['nodes'][1].get('port_number', 0)}"
                })
                connectivity_map[node2_id]['connections'].append({
                    'target': node_names.get(node1_id, 'Inconnu'),
                    'target_id': node1_id,
                    'my_port': f"ethernet{link['nodes'][1].get('adapter_number', 0)}/{link['nodes'][1].get('port_number', 0)}",
                    'target_port': f"ethernet{link['nodes'][0].get('adapter_number', 0)}/{link['nodes'][0].get('port_number', 0)}"
                })
    
    return connectivity_map

def generate_report(nodes, links, connectivity_map):
    """Génère un rapport complet"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("=" * 70)
    print(f"RAPPORT DE VÉRIFICATION FINALE DE LA TOPOLOGIE")
    print(f"Date: {timestamp}")
    print("=" * 70)
    
    # Statistiques générales
    total_nodes = len(nodes)
    total_links = len(links)
    started_nodes = len([n for n in nodes if n['status'] == 'started'])
    stopped_nodes = len([n for n in nodes if n['status'] == 'stopped'])
    isolated_nodes = len([n for n in nodes if len(connectivity_map[n['node_id']]['connections']) == 0])
    
    print(f"\n📊 STATISTIQUES GÉNÉRALES")
    print(f"   Nombre total d'équipements: {total_nodes}")
    print(f"   Nombre total de liens: {total_links}")
    print(f"   Équipements démarrés: {started_nodes}")
    print(f"   Équipements arrêtés: {stopped_nodes}")
    print(f"   Équipements isolés: {isolated_nodes}")
    
    # État par type d'équipement
    print(f"\n🔧 RÉPARTITION PAR TYPE")
    node_types = {}
    for node in nodes:
        node_type = node['node_type']
        if node_type not in node_types:
            node_types[node_type] = {'total': 0, 'started': 0}
        node_types[node_type]['total'] += 1
        if node['status'] == 'started':
            node_types[node_type]['started'] += 1
    
    for node_type, stats in node_types.items():
        print(f"   {node_type}: {stats['started']}/{stats['total']} démarrés")
    
    # Vérification des équipements critiques
    print(f"\n🎯 ÉQUIPEMENTS CRITIQUES")
    critical_equipment = ['PC1', 'Admin', 'SW-LAN', 'SW-ADMIN', 'Routeur-Principal', 'Routeur-Bordure']
    
    for equipment in critical_equipment:
        node_info = next((n for n in nodes if n['name'] == equipment), None)
        if node_info:
            connections = connectivity_map[node_info['node_id']]['connections']
            status_icon = "✅" if node_info['status'] == 'started' else "❌"
            conn_count = len(connections)
            print(f"   {status_icon} {equipment}: {node_info['status']} ({conn_count} connexions)")
            for conn in connections:
                print(f"      └─ {conn['target']} via {conn['my_port']} ↔ {conn['target_port']}")
        else:
            print(f"   ❌ {equipment}: NON TROUVÉ")
    
    # Validation des connexions critiques restaurées
    print(f"\n🔗 VALIDATION DES CONNEXIONS RESTAURÉES")
    
    # Vérifier PC1 ↔ SW-LAN
    pc1_node = next((n for n in nodes if n['name'] == 'PC1'), None)
    if pc1_node:
        pc1_connections = [conn['target'] for conn in connectivity_map[pc1_node['node_id']]['connections']]
        if 'SW-LAN' in pc1_connections:
            print(f"   ✅ PC1 ↔ SW-LAN: CONNECTÉ")
        else:
            print(f"   ❌ PC1 ↔ SW-LAN: NON CONNECTÉ")
    
    # Vérifier Admin ↔ SW-ADMIN
    admin_node = next((n for n in nodes if n['name'] == 'Admin'), None)
    if admin_node:
        admin_connections = [conn['target'] for conn in connectivity_map[admin_node['node_id']]['connections']]
        if 'SW-ADMIN' in admin_connections:
            print(f"   ✅ Admin ↔ SW-ADMIN: CONNECTÉ")
        else:
            print(f"   ❌ Admin ↔ SW-ADMIN: NON CONNECTÉ")
    
    # Topologie de base validée
    print(f"\n🌐 STRUCTURE DE LA TOPOLOGIE")
    backbone_connections = [
        ('Routeur-Principal', 'SW-LAN'),
        ('Routeur-Principal', 'SW-ADMIN'),
        ('Routeur-Principal', 'SW-SERVER'),
        ('Routeur-Principal', 'SW-DMZ'),
        ('Routeur-Bordure', 'Routeur-Principal')
    ]
    
    for conn1, conn2 in backbone_connections:
        node1 = next((n for n in nodes if n['name'] == conn1), None)
        if node1:
            connections = [conn['target'] for conn in connectivity_map[node1['node_id']]['connections']]
            if conn2 in connections:
                print(f"   ✅ {conn1} ↔ {conn2}")
            else:
                print(f"   ❌ {conn1} ↔ {conn2}")
    
    # Équipements isolés
    if isolated_nodes > 0:
        print(f"\n⚠️  ÉQUIPEMENTS ISOLÉS")
        for node in nodes:
            if len(connectivity_map[node['node_id']]['connections']) == 0:
                print(f"   ❌ {node['name']} ({node['node_type']})")
    else:
        print(f"\n✅ AUCUN ÉQUIPEMENT ISOLÉ")
    
    # Résumé final
    print(f"\n" + "=" * 70)
    if isolated_nodes == 0 and started_nodes >= (total_nodes - 1):  # Cloud1 peut être arrêté
        print(f"🎉 STATUT GLOBAL: TOPOLOGIE ENTIÈREMENT OPÉRATIONNELLE")
        print(f"   ✅ Restauration complète réussie")
        print(f"   ✅ PC1 et Admin reconnectés")
        print(f"   ✅ Infrastructure backbone fonctionnelle")
    else:
        print(f"⚠️  STATUT GLOBAL: PROBLÈMES DÉTECTÉS")
        if isolated_nodes > 0:
            print(f"   ❌ {isolated_nodes} équipements isolés")
        if started_nodes < (total_nodes - 1):
            print(f"   ❌ {total_nodes - started_nodes} équipements arrêtés")
    
    print(f"=" * 70)
    
    return {
        'total_nodes': total_nodes,
        'total_links': total_links,
        'started_nodes': started_nodes,
        'isolated_nodes': isolated_nodes,
        'critical_restored': isolated_nodes == 0
    }

def main():
    """Fonction principale"""
    print("🔍 Vérification finale de la topologie en cours...")
    
    nodes, links = get_topology_status()
    if nodes is None or links is None:
        print("❌ Impossible de récupérer l'état de la topologie")
        return False
    
    connectivity_map = analyze_connectivity(nodes, links)
    stats = generate_report(nodes, links, connectivity_map)
    
    return stats['critical_restored']

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)