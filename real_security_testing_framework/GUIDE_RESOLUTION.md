# Guide de Résolution des Problèmes GNS3

## 🎯 Problèmes Identifiés dans tes Logs

Basé sur l'analyse de tes logs du 2025-07-20 12:12:04, voici les problèmes détectés :

### 🔴 Problèmes Critiques
1. **Cloud1 arrêté** : `"Cloud1 (cloud): stopped"`
2. **Erreurs HTTP 409** : Conflits lors des connexions au cloud
3. **Connectivité limitée** : Seulement 2/15 équipements accessibles
4. **Serveurs QEMU non responsifs** : Diagnostics VNC échouent (0/5 commandes)

### 📊 État Actuel
- ✅ **Équipements accessibles** : PC1 (192.168.20.10), Admin (192.168.41.10)
- ❌ **Équipements inaccessibles** : 13/15 incluant tous les serveurs et routeurs
- ⚠️ **Taux de connectivité** : 13.3% seulement

## 🛠️ Solutions Créées

### 1. **Solution Automatique (Recommandée)**

```bash
cd /home/adjada/network-management-system/real_security_testing_framework
./run_diagnosis_and_fix.sh
```

Ce script :
- Analyse tes logs automatiquement
- Diagnostique l'état actuel
- Applique les corrections spécifiques
- Vérifie les résultats

### 2. **Solution Manuelle par Étapes**

#### Étape 1 : Diagnostic
```bash
python3 quick_diagnostic.py
```

#### Étape 2 : Analyse des Logs
```bash
python3 analyze_logs.py
```

#### Étape 3 : Correction Spécifique
```bash
python3 fix_specific_issues.py
```

#### Étape 4 : Investigation Avancée (si nécessaire)
```bash
python3 investigate_gns3_issues.py
```

## 🔧 Corrections Appliquées par les Scripts

### 1. **Démarrage de Cloud1**
- Détection automatique du statut
- Démarrage via API GNS3
- Configuration des ports vers les bridges

### 2. **Résolution des Erreurs HTTP 409**
- Suppression des liens conflictuels
- Recréation propre des connexions
- Mapping correct des équipements aux ports cloud

### 3. **Configuration des Bridges Système**
- `br-vlan10` → 192.168.10.1/24
- `br-vlan20` → 192.168.20.1/24  
- `br-vlan41` → 192.168.41.1/24
- `br-vlan30` → 192.168.30.1/24

### 4. **Redémarrage des Serveurs QEMU**
- Server-Mail, Server-DNS, Server-DB
- PostTest, Server-Web, Server-Fichiers
- Correction des problèmes VNC

### 5. **Connexions Équipements → Cloud1**
- PC1 → Cloud1 port 1 (br-vlan20)
- Admin → Cloud1 port 2 (br-vlan41)
- Server-Web → Cloud1 port 0 (br-vlan10)
- Server-Mail → Cloud1 port 0 (br-vlan10)
- Server-DB → Cloud1 port 3 (br-vlan30)
- PostTest → Cloud1 port 3 (br-vlan30)

## 📈 Résultats Attendus

Après correction, tu devrais avoir :
- ✅ **Cloud1 démarré et configuré**
- ✅ **80%+ d'équipements accessibles**
- ✅ **Connectivité hôte ↔ équipements GNS3**
- ✅ **Framework de sécurité fonctionnel**

## 🚨 Utilisation Immédiate

**Pour résoudre tes problèmes maintenant :**

```bash
# Navigation vers le répertoire
cd /home/adjada/network-management-system/real_security_testing_framework

# Exécution de la solution complète
./run_diagnosis_and_fix.sh

# Ou solution directe rapide
python3 fix_specific_issues.py
```

## 📋 Vérification Après Correction

```bash
# Test de connectivité
ping 192.168.20.10  # PC1
ping 192.168.41.10  # Admin  
ping 192.168.10.10  # Server-Web
ping 192.168.30.10  # Server-DB

# Test du framework
python3 core/real_security_framework.py
```

## 🔍 Logs et Diagnostic

- **Logs diagnostic** : `/tmp/gns3_diagnosis_*.log`
- **Rapports détaillés** : `/tmp/gns3_investigation_*.txt`

## 💡 Notes Importantes

1. **Mot de passe sudo** : Les scripts utilisent `sudo` pour configurer les bridges (mot de passe requis)
2. **Pas de données hardcodées** : Tout est détecté dynamiquement via l'API GNS3
3. **Solutions progressives** : Si une étape échoue, les suivantes s'adaptent
4. **Sauvegardes** : Tous les logs sont conservés pour analyse

## 🆘 Si les Scripts Échouent

1. **Vérifier GNS3** : Service actif sur port 3080
2. **Vérifier le projet** : ID 6b858ee5-4a49-4f72-b437-8dcd8d876bad accessible
3. **Vérifier les permissions** : Droits sudo pour les bridges
4. **Logs détaillés** : Consulter les fichiers de log générés

## 🎉 Après Résolution

Une fois les problèmes corrigés :
- Le framework de sécurité sera pleinement fonctionnel
- Tous les tests d'injection de trafic fonctionneront
- La connectivité sera établie entre l'hôte et les équipements GNS3
- Les modules Django pourront découvrir et analyser les équipements

---

**Créé par l'équipe de développement NMS - Résolution basée sur l'analyse des logs du 2025-07-20**