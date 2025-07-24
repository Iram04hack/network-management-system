# Scripts d'Investigation et de Dépannage GNS3

Ce répertoire contient des scripts spécialisés pour diagnostiquer et corriger les problèmes GNS3 identifiés dans le système de gestion de réseau.

## Problèmes Ciblés

Les scripts adressent spécifiquement les problèmes suivants :

1. **Cloud1 arrêté** - Le nœud Cloud1 est dans l'état "stopped"
2. **Erreurs HTTP 409** - Conflits lors des connexions d'équipements au cloud
3. **Connectivité limitée** - Seulement 2/15 équipements accessibles (PC1 et Admin se pinguent eux-mêmes)
4. **Serveurs QEMU non-responsifs** - Les serveurs QEMU ne répondent pas aux diagnostics VNC

## Scripts Disponibles

### 1. investigate_gns3_issues.py (Principal)

**Script d'investigation automatique et de correction**

```bash
cd /home/adjada/network-management-system/real_security_testing_framework
python3 investigate_gns3_issues.py
```

**Fonctionnalités :**
- Auto-découverte du projet GNS3 actif
- Analyse complète de la topologie (nœuds, liens, connectivité)
- Détection des problèmes Cloud1, QEMU/VNC et HTTP 409
- Corrections automatiques :
  - Démarrage de Cloud1 avec gestion des erreurs 409
  - Reconfiguration et redémarrage forcé si nécessaire
  - Redémarrage des nœuds QEMU problématiques
  - Configuration des bridges système
  - Établissement des connexions critiques
- Test de connectivité réelle vers les équipements
- Génération d'un rapport détaillé sauvegardé dans `/tmp/`

**Codes de sortie :**
- `0` : Investigation réussie (>80% connectivité)
- `1` : Investigation partielle (>50% connectivité)
- `2` : Investigation limitée ou échec

### 2. gns3_advanced_troubleshoot.py (Intervention Manuelle)

**Script de dépannage avancé pour interventions manuelles**

```bash
cd /home/adjada/network-management-system/real_security_testing_framework
python3 gns3_advanced_troubleshoot.py
```

**Options disponibles :**
1. **Arrêt forcé de tous les nœuds** - Force l'arrêt de tous les nœuds du projet
2. **Remise à zéro de la topologie** - Supprime tous les liens et remet à zéro
3. **Recréation de Cloud1** - Supprime et recrée complètement le nœud Cloud1
4. **Réparation des bridges système** - Recrée les bridges br-vlan* avec configuration optimale
5. **Redémarrage du service GNS3** - Redémarre le service GNS3 si disponible
6. **Procédure de récupération complète** - Exécute toutes les étapes de récupération

### 3. Scripts Complémentaires

- `fix_gns3_topology.py` - Script de correction topologique spécialisé
- `diagnostic_connectivite.py` - Diagnostic de connectivité approfondi

## Utilisation Recommandée

### Première Investigation
1. Exécuter d'abord `investigate_gns3_issues.py` pour un diagnostic automatique
2. Consulter le rapport généré dans `/tmp/gns3_investigation_report_*.txt`
3. Si les corrections automatiques ne suffisent pas, passer au dépannage avancé

### Dépannage Avancé
Si l'investigation automatique échoue :

1. **Pour l'erreur HTTP 409 persistante :**
   ```bash
   python3 gns3_advanced_troubleshoot.py
   # Choisir option 3 (Recréation de Cloud1)
   ```

2. **Pour les problèmes de bridges :**
   ```bash
   python3 gns3_advanced_troubleshoot.py
   # Choisir option 4 (Réparation des bridges système)
   ```

3. **Pour une récupération complète :**
   ```bash
   python3 gns3_advanced_troubleshoot.py
   # Choisir option 6 (Procédure de récupération complète)
   ```

### Re-test après Intervention
Après toute intervention manuelle, relancer l'investigation :
```bash
python3 investigate_gns3_issues.py
```

## Configuration Système Requise

### Bridges Réseau
Les scripts configurent automatiquement ces bridges :
- `br-vlan10` (192.168.10.1/24) - Serveurs
- `br-vlan20` (192.168.20.1/24) - Clients
- `br-vlan41` (192.168.41.1/24) - Administration
- `br-vlan30` (192.168.30.1/24) - Base de données
- `br-vlan31` (192.168.31.1/24) - Services étendus

### Équipements Ciblés
Les scripts tentent de connecter ces équipements critiques :
- **PC1** → br-vlan20 (192.168.20.10)
- **Admin** → br-vlan41 (192.168.41.10)
- **Server-Web** → br-vlan10 (192.168.10.10)
- **Server-Mail** → br-vlan10 (192.168.10.11)
- **Server-DNS** → br-vlan10 (192.168.10.12)
- **Server-DB** → br-vlan30 (192.168.30.10)
- **PostTest** → br-vlan30 (192.168.30.15)

### Ports VNC QEMU
- Server-Mail: port 5902
- Server-DNS: port 5903
- Server-DB: port 5905
- PostTest: port 5901
- Server-Fichiers: port 5904

## Journalisation

### Logs Automatiques
- Console principale avec horodatage détaillé
- Logs sauvegardés dans `/tmp/gns3_investigation_*.log`
- Rapports détaillés dans `/tmp/gns3_investigation_report_*.txt`

### Niveaux de Log
- **INFO** : Opérations normales et succès
- **WARNING** : Problèmes non-critiques
- **ERROR** : Échecs d'opérations spécifiques
- **DEBUG** : Détails techniques (si activé)

## Dépannage des Scripts

### Erreur de Permission
```bash
# Si erreur de permission sudo
echo "root" | sudo -S python3 investigate_gns3_issues.py
```

### Service GNS3 Inaccessible
```bash
# Vérifier que GNS3 tourne
curl http://localhost:3080/v2/version

# Si échec, redémarrer GNS3 manuellement
```

### Bridges Non Créés
```bash
# Vérifier les permissions bridge-utils
sudo apt install bridge-utils
sudo brctl show
```

## Exemple de Flux Complet

```bash
# 1. Investigation initiale
cd /home/adjada/network-management-system/real_security_testing_framework
python3 investigate_gns3_issues.py

# 2. Si échec avec HTTP 409, intervention manuelle
python3 gns3_advanced_troubleshoot.py
# Choisir option 6 (récupération complète)

# 3. Re-test
python3 investigate_gns3_issues.py

# 4. Vérification manuelle
ping 192.168.20.10  # PC1
ping 192.168.41.10  # Admin
ping 192.168.10.10  # Server-Web
```

## Support et Maintenance

### Fichiers de Configuration
- Les scripts s'adaptent automatiquement au projet GNS3 actif
- Pas de données hardcodées (sauf les IP de test prédéfinies)
- Configuration des bridges adaptable

### Extensions Possibles
- Ajout de nouveaux équipements dans la liste `critical_equipment`
- Personnalisation des plages IP et bridges
- Extensions pour d'autres types de nœuds GNS3

### Monitoring Continu
Pour un monitoring en continu :
```bash
# Script de surveillance (exemple)
while true; do
    python3 investigate_gns3_issues.py
    sleep 300  # 5 minutes
done
```

---
**Note :** Ces scripts sont conçus pour fonctionner avec l'environnement Django backend et s'intègrent dans le framework de sécurité existant du système de gestion de réseau.