#!/usr/bin/env python3
import requests
import json

# Configuration
gns3_server = 'http://localhost:3080'
project_id = '6b858ee5-4a49-4f72-b437-8dcd8d876bad'

# IDs des équipements
pc1_id = 'e581f562-2fa9-4be6-9362-d76879420b91'
admin_id = 'ac3a765c-8d9c-44bb-b1bb-ba30c84086cf'
sw_lan_id = '00339e94-db96-4fd9-a273-00dfe9132fc6'
sw_admin_id = '408060b2-7529-4af7-a432-545398091d2e'

print('=== CRÉATION DES CONNEXIONS MANQUANTES ===')

# 1. Créer la connexion SW-LAN ↔ PC1 (utiliser ethernet0/1 sur SW-LAN)
print('\n1. Connexion SW-LAN ↔ PC1...')
link_data = {
    'nodes': [
        {
            'node_id': sw_lan_id,
            'adapter_number': 0,
            'port_number': 1  # ethernet0/1 (libre)
        },
        {
            'node_id': pc1_id,
            'adapter_number': 0,
            'port_number': 0  # ethernet0
        }
    ]
}

try:
    response = requests.post(f'{gns3_server}/v2/projects/{project_id}/links', 
                           json=link_data)
    if response.status_code == 201:
        print('✓ Connexion SW-LAN ↔ PC1 créée avec succès')
        link_info = response.json()
        print(f'  ID du lien: {link_info["link_id"]}')
    else:
        print(f'✗ Erreur lors de la création du lien SW-LAN ↔ PC1: {response.status_code}')
        print(f'  Réponse: {response.text}')
        
        # Essayer avec ethernet0/3 en cas d'échec
        print('  Tentative avec ethernet0/3...')
        link_data['nodes'][0]['port_number'] = 3
        response = requests.post(f'{gns3_server}/v2/projects/{project_id}/links', 
                               json=link_data)
        if response.status_code == 201:
            print('✓ Connexion SW-LAN ↔ PC1 créée avec ethernet0/3')
            link_info = response.json()
            print(f'  ID du lien: {link_info["link_id"]}')
        else:
            print(f'✗ Échec également avec ethernet0/3: {response.status_code}')
            print(f'  Réponse: {response.text}')
            
except Exception as e:
    print(f'✗ Exception lors de la création du lien SW-LAN ↔ PC1: {e}')

# 2. Créer la connexion SW-ADMIN ↔ Admin (utiliser ethernet0/1 sur SW-ADMIN)
print('\n2. Connexion SW-ADMIN ↔ Admin...')
link_data = {
    'nodes': [
        {
            'node_id': sw_admin_id,
            'adapter_number': 0,
            'port_number': 1  # ethernet0/1 (libre)
        },
        {
            'node_id': admin_id,
            'adapter_number': 0,
            'port_number': 0  # ethernet0
        }
    ]
}

try:
    response = requests.post(f'{gns3_server}/v2/projects/{project_id}/links', 
                           json=link_data)
    if response.status_code == 201:
        print('✓ Connexion SW-ADMIN ↔ Admin créée avec succès')
        link_info = response.json()
        print(f'  ID du lien: {link_info["link_id"]}')
    else:
        print(f'✗ Erreur lors de la création du lien SW-ADMIN ↔ Admin: {response.status_code}')
        print(f'  Réponse: {response.text}')
        
        # Essayer avec ethernet0/2 en cas d'échec
        print('  Tentative avec ethernet0/2...')
        link_data['nodes'][0]['port_number'] = 2
        response = requests.post(f'{gns3_server}/v2/projects/{project_id}/links', 
                               json=link_data)
        if response.status_code == 201:
            print('✓ Connexion SW-ADMIN ↔ Admin créée avec ethernet0/2')
            link_info = response.json()
            print(f'  ID du lien: {link_info["link_id"]}')
        else:
            print(f'✗ Échec également avec ethernet0/2: {response.status_code}')
            print(f'  Réponse: {response.text}')
            
except Exception as e:
    print(f'✗ Exception lors de la création du lien SW-ADMIN ↔ Admin: {e}')

print('\n=== VÉRIFICATION FINALE ===')

# Récupérer tous les liens après création
response = requests.get(f'{gns3_server}/v2/projects/{project_id}/links')
links = response.json()

print(f'Nombre total de liens après restauration: {len(links)}')

# Récupérer tous les nœuds pour afficher les noms
response = requests.get(f'{gns3_server}/v2/projects/{project_id}/nodes')
nodes = response.json()

# Créer un mapping des IDs vers les noms
node_names = {}
for node in nodes:
    node_names[node['node_id']] = node['name']

print('\nListe complète des connexions:')
for i, link in enumerate(links):
    nodes_in_link = link['nodes']
    if len(nodes_in_link) >= 2:
        node1_id = nodes_in_link[0]['node_id']
        node2_id = nodes_in_link[1]['node_id']
        
        node1_name = node_names.get(node1_id, 'Inconnu')
        node2_name = node_names.get(node2_id, 'Inconnu')
        
        print(f'{i+1}. {node1_name} ↔ {node2_name}')

# Vérifier spécifiquement PC1 et Admin
print('\n=== ÉTAT FINAL PC1 ET ADMIN ===')
for node in nodes:
    if node['name'] in ['PC1', 'Admin']:
        connections = []
        for link in links:
            for node_link in link['nodes']:
                if node_link['node_id'] == node['node_id']:
                    # Trouver l'autre nœud dans ce lien
                    other_node_id = None
                    for n in link['nodes']:
                        if n['node_id'] != node['node_id']:
                            other_node_id = n['node_id']
                            break
                    if other_node_id:
                        other_node_name = node_names.get(other_node_id, 'Inconnu')
                        connections.append(other_node_name)
        
        status = '✓ CONNECTÉ' if connections else '✗ ISOLÉ'
        print(f'{node["name"]}: {status}')
        for conn in connections:
            print(f'  → {conn}')