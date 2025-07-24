#!/usr/bin/env python3
import requests
import json

# Configuration
gns3_server = 'http://localhost:3080'
project_id = '6b858ee5-4a49-4f72-b437-8dcd8d876bad'

# IDs des équipements
pc1_id = 'e581f562-2fa9-4be6-9362-d76879420b91'
admin_id = 'ac3a765c-8d9c-44bb-b1bb-ba30c84086cf'

# Récupérer tous les liens
response = requests.get(f'{gns3_server}/v2/projects/{project_id}/links')
links = response.json()

print('=== VÉRIFICATION PORTS PC1 ET ADMIN ===')

# Vérifier chaque lien pour PC1 et Admin
pc1_links = []
admin_links = []

for link in links:
    for node_link in link['nodes']:
        if node_link['node_id'] == pc1_id:
            pc1_links.append(link)
            print(f'PC1 trouvé dans un lien: {node_link}')
        if node_link['node_id'] == admin_id:
            admin_links.append(link)
            print(f'Admin trouvé dans un lien: {node_link}')

print(f'\nPC1 est présent dans {len(pc1_links)} liens')
print(f'Admin est présent dans {len(admin_links)} liens')

# Vérifier les détails des nœuds PC1 et Admin
print('\n=== DÉTAILS DES NŒUDS ===')
response = requests.get(f'{gns3_server}/v2/projects/{project_id}/nodes/{pc1_id}')
pc1_details = response.json()
print(f'PC1 - Statut: {pc1_details.get("status", "unknown")}')

response = requests.get(f'{gns3_server}/v2/projects/{project_id}/nodes/{admin_id}')
admin_details = response.json()
print(f'Admin - Statut: {admin_details.get("status", "unknown")}')

# Essayer de créer un lien avec un port différent - ethernet1/0 sur SW-LAN
print('\n=== TENTATIVE AVEC PORTS DIFFÉRENTS ===')
sw_lan_id = '00339e94-db96-4fd9-a273-00dfe9132fc6'
sw_admin_id = '408060b2-7529-4af7-a432-545398091d2e'

# Test avec ethernet1/0 sur SW-LAN
print('Test connexion SW-LAN ethernet1/0 ↔ PC1 ethernet0...')
link_data = {
    'nodes': [
        {
            'node_id': sw_lan_id,
            'adapter_number': 1,
            'port_number': 0  # ethernet1/0
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
        print('✓ Connexion SW-LAN ethernet1/0 ↔ PC1 créée avec succès')
        link_info = response.json()
        print(f'  ID du lien: {link_info["link_id"]}')
    else:
        print(f'✗ Erreur: {response.status_code}')
        print(f'  Réponse: {response.text}')
except Exception as e:
    print(f'✗ Exception: {e}')

# Test avec ethernet1/0 sur SW-ADMIN
print('\nTest connexion SW-ADMIN ethernet1/0 ↔ Admin ethernet0...')
link_data = {
    'nodes': [
        {
            'node_id': sw_admin_id,
            'adapter_number': 1,
            'port_number': 0  # ethernet1/0
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
        print('✓ Connexion SW-ADMIN ethernet1/0 ↔ Admin créée avec succès')
        link_info = response.json()
        print(f'  ID du lien: {link_info["link_id"]}')
    else:
        print(f'✗ Erreur: {response.status_code}')
        print(f'  Réponse: {response.text}')
except Exception as e:
    print(f'✗ Exception: {e}')