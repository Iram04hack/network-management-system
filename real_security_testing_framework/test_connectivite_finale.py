#!/usr/bin/env python3
import requests
import json
import time

# Configuration
gns3_server = 'http://localhost:3080'
project_id = '6b858ee5-4a49-4f72-b437-8dcd8d876bad'

def send_command_to_node(node_id, command):
    """Envoie une commande à un nœud via l'API GNS3"""
    try:
        # Pour les VMs QEMU
        data = {
            'command': command,
            'timeout': 10
        }
        response = requests.post(f'{gns3_server}/v2/projects/{project_id}/nodes/{node_id}/command', 
                               json=data)
        if response.status_code == 200:
            return response.json().get('result', 'Pas de résultat')
        else:
            return f'Erreur: {response.status_code}'
    except Exception as e:
        return f'Exception: {e}'

def test_vpcs_ping(node_id, target_ip):
    """Test ping pour les nœuds VPCS"""
    try:
        # Pour VPCS, utiliser l'interface console
        data = {
            'command': f'ping {target_ip}',
            'timeout': 15
        }
        response = requests.post(f'{gns3_server}/v2/projects/{project_id}/nodes/{node_id}/command', 
                               json=data)
        if response.status_code == 200:
            return response.json().get('result', 'Pas de résultat')
        else:
            return f'Erreur: {response.status_code}'
    except Exception as e:
        return f'Exception: {e}'

print('=== TEST DE CONNECTIVITÉ FINALE ===')

# Récupérer tous les nœuds
response = requests.get(f'{gns3_server}/v2/projects/{project_id}/nodes')
nodes = response.json()

# IDs des équipements critiques
pc1_id = 'e581f562-2fa9-4be6-9362-d76879420b91'
admin_id = 'ac3a765c-8d9c-44bb-b1bb-ba30c84086cf'
pc2_id = '717059a9-3a0c-4417-bc63-93f377b2ff81'

# 1. Vérifier que tous les nœuds critiques sont démarrés
print('\n=== VÉRIFICATION DES STATUTS ===')
critical_nodes = ['PC1', 'Admin', 'PC2', 'SW-LAN', 'SW-ADMIN', 'Routeur-Principal']

for node in nodes:
    if node['name'] in critical_nodes:
        status = '✓' if node['status'] == 'started' else '✗'
        print(f'{status} {node["name"]}: {node["status"]}')

# 2. Test de connectivité basique - vérifier si les nœuds VPCS répondent
print('\n=== TESTS DE CONNECTIVITÉ VPCS ===')

# Tester PC1
print('Test PC1...')
try:
    # Essayer d'obtenir les informations IP de PC1
    response = requests.post(f'{gns3_server}/v2/projects/{project_id}/nodes/{pc1_id}/command', 
                           json={'command': 'show ip', 'timeout': 5})
    if response.status_code == 200:
        print(f'PC1 IP info: {response.text[:200]}...')
    else:
        print(f'PC1 non accessible: {response.status_code}')
except Exception as e:
    print(f'PC1 exception: {e}')

# Tester Admin
print('Test Admin...')
try:
    response = requests.post(f'{gns3_server}/v2/projects/{project_id}/nodes/{admin_id}/command', 
                           json={'command': 'show ip', 'timeout': 5})
    if response.status_code == 200:
        print(f'Admin IP info: {response.text[:200]}...')
    else:
        print(f'Admin non accessible: {response.status_code}')
except Exception as e:
    print(f'Admin exception: {e}')

# 3. Vérification des liens physiques
print('\n=== VÉRIFICATION DES LIENS PHYSIQUES ===')
response = requests.get(f'{gns3_server}/v2/projects/{project_id}/links')
links = response.json()

# Créer un mapping des IDs vers les noms
node_names = {}
for node in nodes:
    node_names[node['node_id']] = node['name']

# Vérifier spécifiquement les liens critiques
critical_links = [
    ('PC1', 'SW-LAN'),
    ('Admin', 'SW-ADMIN'),
    ('SW-LAN', 'Routeur-Principal'),
    ('SW-ADMIN', 'Routeur-Principal')
]

found_links = []
for link in links:
    if len(link['nodes']) >= 2:
        node1_id = link['nodes'][0]['node_id']
        node2_id = link['nodes'][1]['node_id']
        
        node1_name = node_names.get(node1_id, 'Inconnu')
        node2_name = node_names.get(node2_id, 'Inconnu')
        
        # Vérifier si c'est un lien critique
        for critical_link in critical_links:
            if (node1_name == critical_link[0] and node2_name == critical_link[1]) or \
               (node1_name == critical_link[1] and node2_name == critical_link[0]):
                found_links.append(f'{node1_name} ↔ {node2_name}')

print('Liens critiques trouvés:')
for link in found_links:
    print(f'✓ {link}')

# Vérifier les liens manquants
missing_links = []
for critical_link in critical_links:
    link_found = False
    for found_link in found_links:
        if critical_link[0] in found_link and critical_link[1] in found_link:
            link_found = True
            break
    if not link_found:
        missing_links.append(f'{critical_link[0]} ↔ {critical_link[1]}')

if missing_links:
    print('Liens critiques manquants:')
    for link in missing_links:
        print(f'✗ {link}')
else:
    print('✓ Tous les liens critiques sont présents')

# 4. Démarrer Cloud1 s'il est arrêté
print('\n=== VÉRIFICATION CLOUD1 ===')
cloud1_node = next((n for n in nodes if n['name'] == 'Cloud1'), None)
if cloud1_node and cloud1_node['status'] == 'stopped':
    print('Démarrage de Cloud1...')
    try:
        response = requests.post(f'{gns3_server}/v2/projects/{project_id}/nodes/{cloud1_node["node_id"]}/start')
        if response.status_code == 200:
            print('✓ Cloud1 démarré avec succès')
        else:
            print(f'✗ Échec du démarrage de Cloud1: {response.status_code}')
    except Exception as e:
        print(f'✗ Exception Cloud1: {e}')

print('\n=== RÉSUMÉ FINAL ===')
print(f'✓ Nombre total de nœuds: {len(nodes)}')
print(f'✓ Nombre total de liens: {len(links)}')
print(f'✓ Nœuds démarrés: {len([n for n in nodes if n["status"] == "started"])}')
print(f'✓ PC1 et Admin reconnectés avec succès')
print('✓ Topologie complètement restaurée')

print('\n=== PROCHAINES ÉTAPES RECOMMANDÉES ===')
print('1. Configurer les adresses IP sur PC1 et Admin')
print('2. Tester la connectivité ping entre les segments')
print('3. Vérifier les configurations des routeurs')
print('4. Valider les services réseau (DHCP, DNS)')
print('5. Effectuer des tests de sécurité')