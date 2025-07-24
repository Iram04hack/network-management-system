#!/usr/bin/env python3
"""
Script de correction automatique des VMs QEMU avec images manquantes
Remplace les images manquantes par des images existantes vides
"""
import requests
import json
import time

# Configuration
gns3_server = 'http://localhost:3080'
project_id = '6b858ee5-4a49-4f72-b437-8dcd8d876bad'

# Mapping des images manquantes vers les images existantes
IMAGE_MAPPING = {
    'ubuntu-server.qcow2': 'empty20G.qcow2',  # 20GB pour les serveurs
    'ubuntu-Desktop.qcow2': 'empty30G.qcow2'   # 30GB pour le desktop
}

def get_qemu_nodes():
    """Récupère tous les nœuds QEMU du projet"""
    try:
        response = requests.get(f'{gns3_server}/v2/projects/{project_id}/nodes')
        if response.status_code == 200:
            nodes = response.json()
            return [n for n in nodes if n['node_type'] == 'qemu']
        else:
            print(f"❌ Erreur API: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Exception: {e}")
        return []

def update_node_image(node, new_image):
    """Met à jour l'image disque d'un nœud QEMU"""
    print(f"\n🔧 MISE À JOUR {node['name']}")
    print(f"   Ancienne image: {node.get('properties', {}).get('hda_disk_image', 'N/A')}")
    print(f"   Nouvelle image: {new_image}")
    
    try:
        # Arrêter le nœud d'abord
        print("   1. Arrêt du nœud...")
        stop_response = requests.post(f'{gns3_server}/v2/projects/{project_id}/nodes/{node["node_id"]}/stop')
        print(f"      Arrêt: {stop_response.status_code}")
        
        if stop_response.status_code not in [200, 204]:
            print(f"   ⚠️ Arrêt non confirmé, continuation...")
        
        time.sleep(2)
        
        # Mettre à jour les propriétés du nœud
        print("   2. Mise à jour des propriétés...")
        update_data = {
            'properties': {
                'hda_disk_image': new_image
            }
        }
        
        update_response = requests.put(
            f'{gns3_server}/v2/projects/{project_id}/nodes/{node["node_id"]}',
            json=update_data
        )
        
        if update_response.status_code == 200:
            print("   ✅ Propriétés mises à jour")
        else:
            print(f"   ❌ Échec mise à jour: {update_response.status_code}")
            print(f"      Réponse: {update_response.text}")
            return False
        
        time.sleep(1)
        
        # Redémarrer le nœud
        print("   3. Redémarrage du nœud...")
        start_response = requests.post(f'{gns3_server}/v2/projects/{project_id}/nodes/{node["node_id"]}/start')
        
        if start_response.status_code == 200:
            print("   ✅ Nœud redémarré avec succès")
            return True
        else:
            print(f"   ❌ Échec redémarrage: {start_response.status_code}")
            print(f"      Réponse: {start_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def verify_correction(node):
    """Vérifie que la correction a fonctionné"""
    try:
        time.sleep(3)  # Attendre que le nœud démarre
        
        response = requests.get(f'{gns3_server}/v2/projects/{project_id}/nodes/{node["node_id"]}')
        if response.status_code == 200:
            details = response.json()
            current_image = details.get('properties', {}).get('hda_disk_image', 'N/A')
            status = details.get('status', 'unknown')
            
            print(f"   📊 Vérification:")
            print(f"      Image actuelle: {current_image}")
            print(f"      Statut: {status}")
            
            return status == 'started' and current_image in IMAGE_MAPPING.values()
        else:
            print(f"   ❌ Impossible de vérifier: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur vérification: {e}")
        return False

def main():
    print("=== CORRECTION AUTOMATIQUE DES IMAGES VMs QEMU ===")
    
    # Récupérer les nœuds QEMU
    qemu_nodes = get_qemu_nodes()
    print(f"\n📊 {len(qemu_nodes)} nœuds QEMU trouvés")
    
    if not qemu_nodes:
        print("❌ Aucun nœud QEMU trouvé")
        return
    
    # Identifier les nœuds avec des images problématiques
    problematic_nodes = []
    
    for node in qemu_nodes:
        try:
            response = requests.get(f'{gns3_server}/v2/projects/{project_id}/nodes/{node["node_id"]}')
            if response.status_code == 200:
                details = response.json()
                current_image = details.get('properties', {}).get('hda_disk_image', '')
                
                if current_image in IMAGE_MAPPING:
                    problematic_nodes.append({
                        'node': node,
                        'current_image': current_image,
                        'new_image': IMAGE_MAPPING[current_image]
                    })
        except Exception as e:
            print(f"⚠️ Erreur lors de l'analyse de {node['name']}: {e}")
    
    print(f"\n🎯 {len(problematic_nodes)} nœuds à corriger:")
    for item in problematic_nodes:
        print(f"   - {item['node']['name']}: {item['current_image']} → {item['new_image']}")
    
    if not problematic_nodes:
        print("✅ Aucune correction nécessaire")
        return
    
    # Effectuer les corrections
    print(f"\n🔧 DÉBUT DES CORRECTIONS")
    print("="*50)
    
    successful_corrections = 0
    
    for item in problematic_nodes:
        success = update_node_image(item['node'], item['new_image'])
        
        if success:
            # Vérifier la correction
            if verify_correction(item['node']):
                print(f"   ✅ {item['node']['name']}: CORRECTION RÉUSSIE")
                successful_corrections += 1
            else:
                print(f"   ⚠️ {item['node']['name']}: CORRECTION PARTIELLE")
        else:
            print(f"   ❌ {item['node']['name']}: CORRECTION ÉCHOUÉE")
    
    # Résumé final
    print(f"\n" + "="*50)
    print(f"📋 RÉSUMÉ DES CORRECTIONS")
    print(f"="*50)
    print(f"Nœuds traités: {len(problematic_nodes)}")
    print(f"Corrections réussies: {successful_corrections}")
    print(f"Taux de succès: {(successful_corrections/len(problematic_nodes)*100):.1f}%")
    
    if successful_corrections == len(problematic_nodes):
        print(f"\n🎉 TOUTES LES CORRECTIONS RÉUSSIES!")
        print(f"✅ Les VMs devraient maintenant être accessibles")
        print(f"🔄 Recommandation: Relancer le framework de tests pour vérifier")
    elif successful_corrections > 0:
        print(f"\n⚠️ CORRECTIONS PARTIELLES")
        print(f"🔄 Certaines VMs peuvent nécessiter une intervention manuelle")
    else:
        print(f"\n❌ AUCUNE CORRECTION RÉUSSIE")
        print(f"🔧 Intervention manuelle requise")
    
    print(f"\n📝 PROCHAINES ÉTAPES:")
    print(f"1. Vérifier que les VMs démarrent correctement")
    print(f"2. Configurer le système d'exploitation sur les images vides")
    print(f"3. Installer les services requis (serveur web, DNS, etc.)")
    print(f"4. Relancer le framework de tests de sécurité")

if __name__ == "__main__":
    main()