#!/usr/bin/env python3
"""
Script de vérification complète des équipements nécessaires via l'API GNS3
Vérifie si tous les nœuds requis pour le framework de sécurité sont présents
"""
import requests
import json

# Configuration
gns3_server = 'http://localhost:3080'
project_id = '6b858ee5-4a49-4f72-b437-8dcd8d876bad'

# Liste des équipements attendus pour un framework de tests de sécurité complet
EQUIPEMENTS_ATTENDUS = {
    # Routeurs et infrastructure backbone
    'routeurs': [
        'Routeur-Principal',
        'Routeur-Bordure'
    ],
    
    # Switches de distribution
    'switches': [
        'SW-LAN',
        'SW-ADMIN', 
        'SW-SERVER',
        'SW-DMZ'
    ],
    
    # Stations de travail et clients
    'stations': [
        'PC1',
        'PC2',
        'Admin'
    ],
    
    # Serveurs
    'serveurs': [
        'Server-Web',
        'Server-DB',
        'Server-Mail',
        'Server-DNS',
        'Server-Fichiers',
        'PostTest'
    ],
    
    # Infrastructure réseau
    'infrastructure': [
        'Cloud1',
        'Hub1'
    ]
}

def get_all_nodes():
    """Récupère tous les nœuds du projet via l'API"""
    try:
        response = requests.get(f'{gns3_server}/v2/projects/{project_id}/nodes')
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Erreur API: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Exception lors de la récupération des nœuds: {e}")
        return None

def get_all_links():
    """Récupère tous les liens du projet via l'API"""
    try:
        response = requests.get(f'{gns3_server}/v2/projects/{project_id}/links')
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Erreur API: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Exception lors de la récupération des liens: {e}")
        return None

def verify_equipment_presence(nodes):
    """Vérifie la présence de tous les équipements attendus"""
    print("=== VÉRIFICATION DE LA PRÉSENCE DES ÉQUIPEMENTS ===")
    
    # Créer une liste des noms présents
    present_names = [node['name'] for node in nodes]
    
    all_missing = []
    all_present = []
    
    for category, equipment_list in EQUIPEMENTS_ATTENDUS.items():
        print(f"\n🔍 {category.upper()}:")
        missing_in_category = []
        
        for equipment in equipment_list:
            if equipment in present_names:
                node_info = next(n for n in nodes if n['name'] == equipment)
                status_icon = "✅" if node_info['status'] == 'started' else "⚠️"
                print(f"  {status_icon} {equipment} ({node_info['node_type']}, {node_info['status']})")
                all_present.append(equipment)
            else:
                print(f"  ❌ {equipment} - MANQUANT")
                missing_in_category.append(equipment)
                all_missing.append(equipment)
        
        if missing_in_category:
            print(f"     → {len(missing_in_category)} équipement(s) manquant(s) dans {category}")
    
    return all_present, all_missing

def analyze_extra_equipment(nodes):
    """Analyse les équipements présents qui ne sont pas dans la liste attendue"""
    print("\n=== ÉQUIPEMENTS SUPPLÉMENTAIRES ===")
    
    expected_names = []
    for equipment_list in EQUIPEMENTS_ATTENDUS.values():
        expected_names.extend(equipment_list)
    
    extra_equipment = []
    for node in nodes:
        if node['name'] not in expected_names:
            extra_equipment.append(node)
    
    if extra_equipment:
        print(f"Équipements supplémentaires trouvés ({len(extra_equipment)}):")
        for node in extra_equipment:
            print(f"  ➕ {node['name']} ({node['node_type']}, {node['status']})")
    else:
        print("✅ Aucun équipement supplémentaire")
    
    return extra_equipment

def analyze_connectivity_matrix(nodes, links):
    """Analyse la matrice de connectivité"""
    print("\n=== ANALYSE DE LA CONNECTIVITÉ ===")
    
    # Créer un mapping ID → Nom
    node_names = {node['node_id']: node['name'] for node in nodes}
    
    # Construire la matrice de connectivité
    connectivity = {}
    for node in nodes:
        connectivity[node['name']] = []
    
    for link in links:
        if len(link['nodes']) >= 2:
            node1_id = link['nodes'][0]['node_id']
            node2_id = link['nodes'][1]['node_id']
            
            node1_name = node_names.get(node1_id, 'Inconnu')
            node2_name = node_names.get(node2_id, 'Inconnu')
            
            if node1_name in connectivity:
                connectivity[node1_name].append(node2_name)
            if node2_name in connectivity:
                connectivity[node2_name].append(node1_name)
    
    # Analyser les connexions critiques attendues
    connexions_critiques = [
        ('Routeur-Principal', 'SW-LAN'),
        ('Routeur-Principal', 'SW-ADMIN'),
        ('Routeur-Principal', 'SW-SERVER'),
        ('Routeur-Principal', 'SW-DMZ'),
        ('Routeur-Bordure', 'Routeur-Principal'),
        ('SW-LAN', 'PC1'),
        ('SW-LAN', 'PC2'),
        ('SW-ADMIN', 'Admin'),
        ('SW-SERVER', 'Server-Fichiers'),
        ('SW-SERVER', 'PostTest'),
        ('SW-DMZ', 'Server-Web'),
        ('SW-DMZ', 'Server-Mail'),
        ('SW-DMZ', 'Server-DNS'),
        ('SW-DMZ', 'Hub1')
    ]
    
    print("Connexions critiques:")
    missing_connections = []
    
    for conn1, conn2 in connexions_critiques:
        if conn1 in connectivity and conn2 in connectivity[conn1]:
            print(f"  ✅ {conn1} ↔ {conn2}")
        else:
            print(f"  ❌ {conn1} ↔ {conn2} - MANQUANTE")
            missing_connections.append((conn1, conn2))
    
    # Identifier les équipements isolés
    isolated = [name for name, connections in connectivity.items() if not connections]
    if isolated:
        print(f"\n⚠️  Équipements isolés ({len(isolated)}):")
        for equipment in isolated:
            print(f"  - {equipment}")
    else:
        print(f"\n✅ Aucun équipement isolé")
    
    return missing_connections, isolated

def generate_topology_report(nodes, links, present, missing, extra, missing_connections, isolated):
    """Génère un rapport complet de la topologie"""
    print("\n" + "="*70)
    print("📋 RAPPORT COMPLET DE LA TOPOLOGIE")
    print("="*70)
    
    total_expected = sum(len(equipment_list) for equipment_list in EQUIPEMENTS_ATTENDUS.values())
    
    print(f"\n📊 STATISTIQUES GÉNÉRALES:")
    print(f"   Équipements attendus: {total_expected}")
    print(f"   Équipements présents: {len(present)}")
    print(f"   Équipements manquants: {len(missing)}")
    print(f"   Équipements supplémentaires: {len(extra)}")
    print(f"   Total des nœuds: {len(nodes)}")
    print(f"   Total des liens: {len(links)}")
    
    print(f"\n🎯 ÉTAT DE COMPLÉTUDE:")
    completeness = (len(present) / total_expected) * 100
    if completeness == 100:
        print(f"   ✅ TOPOLOGIE COMPLÈTE ({completeness:.1f}%)")
    elif completeness >= 90:
        print(f"   ⚠️  PRESQUE COMPLÈTE ({completeness:.1f}%)")
    else:
        print(f"   ❌ INCOMPLÈTE ({completeness:.1f}%)")
    
    print(f"\n🔗 CONNECTIVITÉ:")
    print(f"   Connexions critiques manquantes: {len(missing_connections)}")
    print(f"   Équipements isolés: {len(isolated)}")
    
    if missing:
        print(f"\n❌ ÉQUIPEMENTS MANQUANTS:")
        for equipment in missing:
            print(f"   - {equipment}")
    
    if missing_connections:
        print(f"\n❌ CONNEXIONS MANQUANTES:")
        for conn1, conn2 in missing_connections:
            print(f"   - {conn1} ↔ {conn2}")
    
    print(f"\n🔧 RECOMMANDATIONS:")
    if missing:
        print(f"   1. Ajouter les {len(missing)} équipements manquants")
    if missing_connections:
        print(f"   2. Créer les {len(missing_connections)} connexions manquantes")
    if isolated:
        print(f"   3. Connecter les {len(isolated)} équipements isolés")
    
    if not missing and not missing_connections and not isolated:
        print(f"   ✅ AUCUNE ACTION REQUISE - TOPOLOGIE OPTIMALE")
    
    print("="*70)

def main():
    print("=== VÉRIFICATION COMPLÈTE DES ÉQUIPEMENTS ET NŒUDS ===")
    print(f"Serveur GNS3: {gns3_server}")
    print(f"Projet ID: {project_id}")
    
    # Récupérer les données
    nodes = get_all_nodes()
    if nodes is None:
        return
    
    links = get_all_links()
    if links is None:
        return
    
    print(f"\n📡 DONNÉES RÉCUPÉRÉES:")
    print(f"   Nœuds trouvés: {len(nodes)}")
    print(f"   Liens trouvés: {len(links)}")
    
    # Vérifications
    present, missing = verify_equipment_presence(nodes)
    extra = analyze_extra_equipment(nodes)
    missing_connections, isolated = analyze_connectivity_matrix(nodes, links)
    
    # Rapport final
    generate_topology_report(nodes, links, present, missing, extra, missing_connections, isolated)

if __name__ == "__main__":
    main()