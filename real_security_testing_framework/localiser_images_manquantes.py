#!/usr/bin/env python3
"""
Script pour localiser les images disques manquantes des VMs QEMU
"""
import subprocess
import os
import requests
import json

# Configuration
gns3_server = 'http://localhost:3080'
missing_images = ['ubuntu-server.qcow2', 'ubuntu-Desktop.qcow2']

def search_system_for_images():
    """Recherche les images sur tout le système"""
    print("=== RECHERCHE SYSTÈME DES IMAGES MANQUANTES ===")
    
    found_images = {}
    
    for image in missing_images:
        print(f"\n🔍 Recherche de {image}...")
        
        try:
            # Recherche avec find
            result = subprocess.run(
                ['find', '/', '-name', image, '-type', 'f', '2>/dev/null'], 
                capture_output=True, text=True, timeout=30
            )
            
            if result.stdout.strip():
                paths = result.stdout.strip().split('\n')
                print(f"✅ Trouvé à {len(paths)} endroit(s):")
                for path in paths:
                    if os.path.exists(path):
                        size = os.path.getsize(path)
                        print(f"  - {path} ({size} bytes)")
                        found_images[image] = paths
            else:
                print(f"❌ {image} non trouvé sur le système")
                
        except subprocess.TimeoutExpired:
            print(f"⏱️ Timeout pour la recherche de {image}")
        except Exception as e:
            print(f"❌ Erreur lors de la recherche: {e}")
    
    return found_images

def get_gns3_images_directory():
    """Récupère le répertoire des images GNS3"""
    try:
        response = requests.get(f'{gns3_server}/v2/compute/qemu/images')
        print(f"\n📁 RÉPERTOIRE IMAGES GNS3")
        
        if response.status_code == 200:
            # En général, les images sont dans un répertoire standard
            # Essayons de le déduire des chemins possibles
            possible_paths = [
                '/opt/gns3/images/QEMU',
                '/home/adjada/GNS3/images/QEMU',
                '~/.config/GNS3/2.2/images/QEMU',
                '/var/lib/gns3/images/QEMU'
            ]
            
            for path in possible_paths:
                expanded_path = os.path.expanduser(path)
                if os.path.exists(expanded_path):
                    print(f"✅ Répertoire GNS3 trouvé: {expanded_path}")
                    files = os.listdir(expanded_path)
                    print(f"   {len(files)} fichiers présents")
                    return expanded_path
            
            print("⚠️ Répertoire GNS3 standard non trouvé")
            return None
        else:
            print(f"❌ Erreur API: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def check_common_vm_locations():
    """Vérifie les emplacements communs de VMs"""
    print(f"\n📂 VÉRIFICATION EMPLACEMENTS COMMUNS")
    
    common_locations = [
        '/home/adjada/VMs',
        '/home/adjada/Documents/VMs', 
        '/var/lib/libvirt/images',
        '/home/adjada/Downloads',
        '/opt/VMs',
        '/srv/VMs'
    ]
    
    found_vms = []
    
    for location in common_locations:
        expanded_location = os.path.expanduser(location)
        if os.path.exists(expanded_location):
            print(f"✅ Vérification {expanded_location}")
            try:
                files = os.listdir(expanded_location)
                vm_files = [f for f in files if f.endswith(('.qcow2', '.vmdk', '.vdi', '.img'))]
                if vm_files:
                    print(f"   Fichiers VMs trouvés: {len(vm_files)}")
                    for vm_file in vm_files[:5]:  # Limiter l'affichage
                        full_path = os.path.join(expanded_location, vm_file)
                        size = os.path.getsize(full_path)
                        print(f"     - {vm_file} ({size} bytes)")
                        found_vms.append(full_path)
                else:
                    print(f"   Aucun fichier VM trouvé")
            except PermissionError:
                print(f"   ❌ Accès refusé")
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
        else:
            print(f"❌ {expanded_location} n'existe pas")
    
    return found_vms

def suggest_solutions(found_images, gns3_dir, found_vms):
    """Propose des solutions pour résoudre le problème"""
    print(f"\n" + "="*60)
    print(f"🔧 SOLUTIONS PROPOSÉES")
    print(f"="*60)
    
    if found_images:
        print(f"✅ OPTION 1: COPIER LES IMAGES EXISTANTES")
        for image, paths in found_images.items():
            print(f"   {image} trouvé à:")
            for path in paths:
                print(f"     - {path}")
        
        if gns3_dir:
            print(f"\n   Commandes de copie vers GNS3:")
            for image, paths in found_images.items():
                if paths:
                    source = paths[0]  # Prendre le premier chemin trouvé
                    print(f"   sudo cp '{source}' '{gns3_dir}/'")
    
    print(f"\n🔄 OPTION 2: CRÉER DE NOUVELLES IMAGES")
    print(f"   1. Télécharger Ubuntu Server ISO")
    print(f"   2. Créer des images qcow2 avec qemu-img")
    print(f"   3. Installer Ubuntu sur les images")
    
    print(f"\n⚙️ OPTION 3: UTILISER DES IMAGES EXISTANTES")
    existing_images = ['empty8G.qcow2', 'empty10G.qcow2', 'empty20G.qcow2']
    print(f"   Reconfigurer les VMs pour utiliser:")
    for img in existing_images:
        print(f"     - {img}")
    
    if found_vms:
        print(f"\n📂 OPTION 4: UTILISER DES VMs EXISTANTES")
        print(f"   {len(found_vms)} fichiers VM trouvés sur le système")
        print(f"   Vérifier si certains peuvent être utilisés")
    
    print(f"\n🔧 OPTION 5: CORRECTION AUTOMATIQUE")
    print(f"   Lancer le script de correction qui:")
    print(f"   - Reconfigure les VMs avec des images vides")
    print(f"   - Redémarre les VMs")
    print(f"   - Configure le réseau de base")

def main():
    print("=== LOCALISATION DES IMAGES DISQUES MANQUANTES ===")
    
    # Recherche système
    found_images = search_system_for_images()
    
    # Répertoire GNS3
    gns3_dir = get_gns3_images_directory()
    
    # Emplacements communs
    found_vms = check_common_vm_locations()
    
    # Proposer des solutions
    suggest_solutions(found_images, gns3_dir, found_vms)
    
    # Demander quelle action entreprendre
    print(f"\n❓ QUELLE ACTION SOUHAITEZ-VOUS ENTREPRENDRE?")
    print(f"1. Corriger automatiquement (images vides temporaires)")
    print(f"2. Afficher les commandes de copie d'images")
    print(f"3. Quitter et corriger manuellement")
    
    choice = input("Votre choix (1-3): ")
    
    if choice == "1":
        print(f"🔧 Lancement de la correction automatique...")
        return "auto_fix"
    elif choice == "2":
        print(f"📋 Commandes de copie à exécuter manuellement:")
        if found_images and gns3_dir:
            for image, paths in found_images.items():
                if paths:
                    print(f"sudo cp '{paths[0]}' '{gns3_dir}/'")
        return "manual_copy"
    else:
        print(f"ℹ️ Correction manuelle requise")
        return "manual"

if __name__ == "__main__":
    result = main()