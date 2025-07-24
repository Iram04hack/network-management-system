#!/usr/bin/env python3
import requests
import json

# Configuration
gns3_server = 'http://localhost:3080'
project_id = '6b858ee5-4a49-4f72-b437-8dcd8d876bad'

print('=== DIAGNOSTIC EXHAUSTIF ===')

# Récupérer TOUS les liens avec détails complets
response = requests.get(f'{gns3_server}/v2/projects/{project_id}/links')
all_links = response.json()

print(f'Nombre total de liens: {len(all_links)}')

pc1_id = 'e581f562-2fa9-4be6-9362-d76879420b91'
admin_id = 'ac3a765c-8d9c-44bb-b1bb-ba30c84086cf'

print('\n=== RECHERCHE EXHAUSTIVE PC1 ET ADMIN ===')
for i, link in enumerate(all_links):
    print(f'\nLien {i+1}: {link.get("link_id", "unknown")}')
    print(f'  Statut: {link.get("link_type", "unknown")}')
    
    for j, node in enumerate(link.get('nodes', [])):
        node_id = node.get('node_id', 'unknown')
        adapter = node.get('adapter_number', 'N/A')
        port = node.get('port_number', 'N/A')
        
        if node_id == pc1_id:
            print(f'  ** PC1 TROUVÉ ** - Adapter: {adapter}, Port: {port}')
        elif node_id == admin_id:
            print(f'  ** ADMIN TROUVÉ ** - Adapter: {adapter}, Port: {port}')
        else:
            print(f'  Nœud {j+1}: ID: {node_id}, Adapter: {adapter}, Port: {port}')

# Test différent - arrêter et redémarrer les nœuds
print('\n=== TENTATIVE AVEC REDÉMARRAGE DES NŒUDS ===')

# Arrêter PC1 et Admin
try:
    print('Arrêt de PC1...')
    response = requests.post(f'{gns3_server}/v2/projects/{project_id}/nodes/{pc1_id}/stop')
    print(f'Arrêt PC1: {response.status_code}')
    
    print('Arrêt d\'Admin...')
    response = requests.post(f'{gns3_server}/v2/projects/{project_id}/nodes/{admin_id}/stop')
    print(f'Arrêt Admin: {response.status_code}')
    
    import time
    time.sleep(2)
    
    # Redémarrer
    print('Redémarrage de PC1...')
    response = requests.post(f'{gns3_server}/v2/projects/{project_id}/nodes/{pc1_id}/start')
    print(f'Redémarrage PC1: {response.status_code}')
    
    print('Redémarrage d\'Admin...')
    response = requests.post(f'{gns3_server}/v2/projects/{project_id}/nodes/{admin_id}/start')
    print(f'Redémarrage Admin: {response.status_code}')
    
    time.sleep(3)
    
    # Maintenant essayer de créer les liens
    print('\n=== NOUVELLE TENTATIVE APRÈS REDÉMARRAGE ===')
    
    # SW-LAN ↔ PC1
    link_data = {
        'nodes': [
            {
                'node_id': '00339e94-db96-4fd9-a273-00dfe9132fc6',  # SW-LAN
                'adapter_number': 0,
                'port_number': 1  # ethernet0/1
            },
            {
                'node_id': pc1_id,
                'adapter_number': 0,
                'port_number': 0
            }
        ]
    }
    
    response = requests.post(f'{gns3_server}/v2/projects/{project_id}/links', json=link_data)
    if response.status_code == 201:
        print('✓ Connexion SW-LAN ↔ PC1 créée après redémarrage')
        link_info = response.json()
        print(f'  ID du lien: {link_info["link_id"]}')
    else:
        print(f'✗ Échec SW-LAN ↔ PC1: {response.status_code}')
        print(f'  Réponse: {response.text}')
    
    # SW-ADMIN ↔ Admin
    link_data = {
        'nodes': [
            {
                'node_id': '408060b2-7529-4af7-a432-545398091d2e',  # SW-ADMIN
                'adapter_number': 0,
                'port_number': 1  # ethernet0/1
            },
            {
                'node_id': admin_id,
                'adapter_number': 0,
                'port_number': 0
            }
        ]
    }
    
    response = requests.post(f'{gns3_server}/v2/projects/{project_id}/links', json=link_data)
    if response.status_code == 201:
        print('✓ Connexion SW-ADMIN ↔ Admin créée après redémarrage')
        link_info = response.json()
        print(f'  ID du lien: {link_info["link_id"]}')
    else:
        print(f'✗ Échec SW-ADMIN ↔ Admin: {response.status_code}')
        print(f'  Réponse: {response.text}')
        
except Exception as e:
    print(f'Exception: {e}')

# Vérification finale
print('\n=== VÉRIFICATION FINALE ===')
response = requests.get(f'{gns3_server}/v2/projects/{project_id}/links')
final_links = response.json()
print(f'Nombre de liens finaux: {len(final_links)}')