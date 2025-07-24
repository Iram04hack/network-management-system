#!/usr/bin/env python3
"""
Script pour tester l'état réel des VMs QEMU via VNC et diagnostiquer les problèmes de communication
"""
import requests
import json
import telnetlib
import socket
import time
import subprocess

# Configuration
gns3_server = 'http://localhost:3080'
project_id = '6b858ee5-4a49-4f72-b437-8dcd8d876bad'

def get_qemu_nodes_with_console():
    """Récupère les nœuds QEMU avec leurs informations de console"""
    try:
        response = requests.get(f'{gns3_server}/v2/projects/{project_id}/nodes')
        if response.status_code == 200:
            nodes = response.json()
            qemu_nodes = []
            
            for node in nodes:
                if node['node_type'] == 'qemu':
                    # Récupérer les détails complets
                    detail_response = requests.get(f'{gns3_server}/v2/projects/{project_id}/nodes/{node["node_id"]}')
                    if detail_response.status_code == 200:
                        details = detail_response.json()
                        qemu_nodes.append(details)
                        
            return qemu_nodes
        else:
            print(f"❌ Erreur API: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Exception: {e}")
        return []

def test_vnc_connection(node):
    """Teste la connexion VNC et essaie de capturer l'état de l'écran"""
    name = node['name']
    console_port = node.get('console', 0)
    console_host = node.get('console_host', '192.168.122.95')
    
    print(f"\n🖥️ TEST VNC {name}")
    print(f"   Connexion: {console_host}:{console_port}")
    
    try:
        # Test de connexion basique
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((console_host, console_port))
        sock.close()
        
        if result == 0:
            print(f"   ✅ Port VNC accessible")
            
            # Essayer de voir si on peut détecter l'activité
            # Via un client VNC simple ou screenshot si possible
            try:
                # Utiliser vncviewer pour un test rapide si disponible
                vnc_test = subprocess.run(
                    ['timeout', '3', 'vncviewer', f'{console_host}:{console_port-5900}', '-ViewOnly', '-passwd', '/dev/null'],
                    capture_output=True, text=True, timeout=5
                )
                print(f"   📺 Test client VNC: {vnc_test.returncode}")
            except:
                print(f"   📺 Client VNC non disponible pour test")
            
            return True
        else:
            print(f"   ❌ Port VNC inaccessible")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur VNC: {e}")
        return False

def test_console_activity(node):
    """Teste l'activité de la console en envoyant des commandes simples"""
    name = node['name']
    console_port = node.get('console', 0)
    console_host = node.get('console_host', '192.168.122.95')
    console_type = node.get('console_type', 'vnc')
    
    print(f"\n⌨️ TEST ACTIVITÉ CONSOLE {name}")
    
    if console_type == 'telnet':
        return test_telnet_activity(name, console_host, console_port)
    elif console_type == 'vnc':
        # Pour VNC, on ne peut pas facilement envoyer des commandes
        # mais on peut vérifier la disponibilité
        print(f"   📺 Console VNC - vérification de base")
        return test_vnc_connection_simple(console_host, console_port)
    else:
        print(f"   ❌ Type de console non supporté: {console_type}")
        return False

def test_telnet_activity(name, host, port):
    """Teste l'activité via telnet"""
    try:
        print(f"   📡 Connexion telnet {host}:{port}")
        tn = telnetlib.Telnet(host, port, timeout=5)
        
        # Envoyer quelques commandes de base
        commands = [b'\r\n', b'help\r\n', b'?\r\n', b'show version\r\n']
        
        responses = []
        for cmd in commands:
            tn.write(cmd)
            time.sleep(1)
            try:
                response = tn.read_very_eager().decode('utf-8', errors='ignore')
                if response.strip():
                    responses.append(response[:100])  # Limiter la taille
            except:
                pass
        
        tn.close()
        
        if responses:
            print(f"   ✅ Console active - {len(responses)} réponses reçues")
            for i, resp in enumerate(responses[:2]):  # Montrer max 2 réponses
                print(f"      {i+1}: {resp[:50]}...")
            return True
        else:
            print(f"   ⚠️ Console connectée mais aucune réponse")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur telnet: {e}")
        return False

def test_vnc_connection_simple(host, port):
    """Test simple de connexion VNC"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def check_vm_network_from_host():
    """Vérifie la connectivité réseau depuis la machine hôte"""
    print(f"\n🌐 TEST CONNECTIVITÉ RÉSEAU DEPUIS L'HÔTE")
    
    # IPs supposées des VMs selon les logs
    vm_ips = {
        'SW-DMZ': '192.168.12.1',
        'Server-Mail': '192.168.10.11', 
        'Server-DNS': '192.168.11.11',
        'SW-LAN': '192.168.21.1',
        'SW-SERVER': '192.168.31.1',
        'SW-ADMIN': '192.168.41.1',
        'Server-DB': '192.168.30.10',
        'PostTest': '192.168.32.10',
        'Server-Web': '192.168.10.10',
        'Server-Fichiers': '192.168.31.10'
    }
    
    reachable = 0
    total = len(vm_ips)
    
    for vm_name, ip in vm_ips.items():
        try:
            # Test ping simple
            ping_result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', ip],
                capture_output=True, text=True, timeout=5
            )
            
            if ping_result.returncode == 0:
                print(f"   ✅ {vm_name} ({ip}): ACCESSIBLE")
                reachable += 1
            else:
                print(f"   ❌ {vm_name} ({ip}): INACCESSIBLE")
                
        except Exception as e:
            print(f"   ❌ {vm_name} ({ip}): ERREUR - {e}")
    
    print(f"\n   📊 Résultat: {reachable}/{total} VMs accessibles depuis l'hôte ({reachable/total*100:.1f}%)")
    return reachable, total

def diagnose_vm_boot_state():
    """Diagnostic de l'état de boot des VMs"""
    print(f"\n🔍 DIAGNOSTIC ÉTAT DE BOOT DES VMs")
    
    qemu_nodes = get_qemu_nodes_with_console()
    
    vm_states = {}
    
    for node in qemu_nodes:
        name = node['name']
        status = node.get('status', 'unknown')
        
        print(f"\n--- {name} ---")
        print(f"Statut GNS3: {status}")
        
        if status == 'started':
            # Tester la console
            console_active = test_console_activity(node)
            vm_states[name] = {
                'gns3_status': status,
                'console_active': console_active
            }
        else:
            print(f"⚠️ VM non démarrée dans GNS3")
            vm_states[name] = {
                'gns3_status': status,
                'console_active': False
            }
    
    return vm_states

def main():
    print("=== DIAGNOSTIC COMPLET ÉTAT DES VMs ===")
    
    # 1. État de boot des VMs
    vm_states = diagnose_vm_boot_state()
    
    # 2. Test connectivité réseau
    reachable, total = check_vm_network_from_host()
    
    # 3. Résumé et analyse
    print(f"\n" + "="*60)
    print(f"📋 RÉSUMÉ DU DIAGNOSTIC")
    print(f"="*60)
    
    active_vms = sum(1 for state in vm_states.values() if state['console_active'])
    started_vms = sum(1 for state in vm_states.values() if state['gns3_status'] == 'started')
    
    print(f"VMs démarrées dans GNS3: {started_vms}/{len(vm_states)}")
    print(f"VMs avec console active: {active_vms}/{len(vm_states)}")
    print(f"VMs accessibles réseau: {reachable}/{total}")
    
    # Identifier les problèmes
    problems = []
    
    if started_vms < len(vm_states):
        problems.append("Certaines VMs ne sont pas démarrées dans GNS3")
    
    if active_vms < started_vms:
        problems.append("Certaines VMs démarrées n'ont pas de console active")
    
    if reachable < total:
        problems.append("Certaines VMs ne sont pas accessibles via réseau")
    
    if problems:
        print(f"\n❌ PROBLÈMES IDENTIFIÉS:")
        for i, problem in enumerate(problems, 1):
            print(f"   {i}. {problem}")
    else:
        print(f"\n✅ AUCUN PROBLÈME MAJEUR DÉTECTÉ")
    
    # Recommandations
    print(f"\n🔧 RECOMMANDATIONS:")
    
    if active_vms == 0:
        print("1. Les VMs semblent être en cours de boot ou ont besoin de configuration")
        print("2. Vérifier manuellement via VNC si les VMs sont au login")
        print("3. Configurer les VMs avec un utilisateur/mot de passe")
    elif reachable == 0:
        print("1. Les VMs sont actives mais pas configurées réseau")
        print("2. Configurer les interfaces réseau dans chaque VM")
        print("3. Vérifier le routage et les VLANs")
    else:
        print("1. Les VMs semblent fonctionnelles")
        print("2. Le problème peut être dans les scripts d'automatisation")
        print("3. Vérifier les credentials et méthodes de connexion")

if __name__ == "__main__":
    main()