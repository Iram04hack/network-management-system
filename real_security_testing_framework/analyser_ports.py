#!/usr/bin/env python3
import requests
import json

# Configuration
gns3_server = 'http://localhost:3080'
project_id = '6b858ee5-4a49-4f72-b437-8dcd8d876bad'

# Récupérer tous les liens et nœuds
response = requests.get(f'{gns3_server}/v2/projects/{project_id}/links')
links = response.json()

response = requests.get(f'{gns3_server}/v2/projects/{project_id}/nodes')
nodes = response.json()

# Créer un mapping des IDs vers les noms
node_names = {}
for node in nodes:
    node_names[node['node_id']] = node['name']

print('=== ANALYSE DÉTAILLÉE DES PORTS UTILISÉS ===')

# IDs des équipements critiques
sw_lan_id = '00339e94-db96-4fd9-a273-00dfe9132fc6'
sw_admin_id = '408060b2-7529-4af7-a432-545398091d2e'
pc1_id = 'e581f562-2fa9-4be6-9362-d76879420b91'
admin_id = 'ac3a765c-8d9c-44bb-b1bb-ba30c84086cf'

print('\n=== PORTS UTILISÉS PAR SW-LAN ===')
sw_lan_ports = []
for link in links:
    for node_link in link['nodes']:
        if node_link['node_id'] == sw_lan_id:
            adapter = node_link.get('adapter_number', 0)
            port = node_link.get('port_number', 0)
            port_name = f'ethernet{adapter}/{port}'
            sw_lan_ports.append(port_name)
            # Trouver l'autre nœud
            other_node_id = None
            for n in link['nodes']:
                if n['node_id'] != sw_lan_id:
                    other_node_id = n['node_id']
                    break
            other_name = node_names.get(other_node_id, 'Inconnu')
            print(f'  {port_name} → {other_name}')

print('\n=== PORTS UTILISÉS PAR SW-ADMIN ===')
sw_admin_ports = []
for link in links:
    for node_link in link['nodes']:
        if node_link['node_id'] == sw_admin_id:
            adapter = node_link.get('adapter_number', 0)
            port = node_link.get('port_number', 0)
            port_name = f'ethernet{adapter}/{port}'
            sw_admin_ports.append(port_name)
            # Trouver l'autre nœud
            other_node_id = None
            for n in link['nodes']:
                if n['node_id'] != sw_admin_id:
                    other_node_id = n['node_id']
                    break
            other_name = node_names.get(other_node_id, 'Inconnu')
            print(f'  {port_name} → {other_name}')

# Vérifier si PC1 et Admin sont déjà connectés
print('\n=== VÉRIFICATION PC1 ET ADMIN ===')
pc1_connected = False
admin_connected = False

for link in links:
    for node_link in link['nodes']:
        if node_link['node_id'] == pc1_id:
            pc1_connected = True
            other_node_id = None
            for n in link['nodes']:
                if n['node_id'] != pc1_id:
                    other_node_id = n['node_id']
                    break
            other_name = node_names.get(other_node_id, 'Inconnu')
            print(f'PC1 est déjà connecté à: {other_name}')
        
        if node_link['node_id'] == admin_id:
            admin_connected = True
            other_node_id = None
            for n in link['nodes']:
                if n['node_id'] != admin_id:
                    other_node_id = n['node_id']
                    break
            other_name = node_names.get(other_node_id, 'Inconnu')
            print(f'Admin est déjà connecté à: {other_name}')

if not pc1_connected:
    print('PC1 n\'est pas connecté')
if not admin_connected:
    print('Admin n\'est pas connecté')

# Proposer des ports libres
print('\n=== PORTS LIBRES SUGGÉRÉS ===')
all_sw_lan_ports = [f'ethernet{a}/{p}' for a in range(4) for p in range(4)]
free_sw_lan_ports = [p for p in all_sw_lan_ports if p not in sw_lan_ports]
print(f'SW-LAN ports libres: {free_sw_lan_ports[:5]}')

all_sw_admin_ports = [f'ethernet{a}/{p}' for a in range(4) for p in range(4)]
free_sw_admin_ports = [p for p in all_sw_admin_ports if p not in sw_admin_ports]
print(f'SW-ADMIN ports libres: {free_sw_admin_ports[:5]}')