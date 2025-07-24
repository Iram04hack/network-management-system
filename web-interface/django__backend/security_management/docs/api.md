# Documentation de l'API Security Management

Cette documentation décrit les endpoints de l'API REST du module Security Management, qui permet de gérer les règles de sécurité et les alertes dans le système de gestion de réseau.

## Base URL

```
/api/security/
```

## Authentification

Toutes les requêtes à l'API nécessitent une authentification. L'API utilise l'authentification par token JWT.

Pour authentifier les requêtes, incluez le header suivant :

```
Authorization: Bearer <token>
```

## Formats de données

L'API accepte et renvoie des données au format JSON.

## Règles de sécurité

Les règles de sécurité définissent les critères et actions pour la détection et la prévention des menaces de sécurité.

### Types de règles supportés

- `suricata` : Règles pour le système de détection d'intrusion Suricata
- `firewall` : Règles de pare-feu
- `fail2ban` : Règles pour le système Fail2Ban
- `access_control` : Règles de contrôle d'accès

### Actions supportées

- `allow` : Autoriser le trafic correspondant
- `block` : Bloquer le trafic correspondant
- `alert` : Générer une alerte sans bloquer
- `log` : Enregistrer le trafic sans alerter ni bloquer

### Liste des règles

```
GET /api/security/rules/
```

#### Paramètres de requête

| Paramètre | Type | Description |
|-----------|------|-------------|
| rule_type | string | Filtrer par type de règle (suricata, firewall, fail2ban, access_control) |
| enabled | boolean | Filtrer par statut d'activation (true, false) |

#### Exemple de réponse

```json
[
  {
    "id": "1",
    "name": "Bloquer les tentatives de connexion SSH",
    "description": "Bloque les adresses IP après 5 tentatives de connexion SSH échouées",
    "rule_type": "fail2ban",
    "content": "failregex = ^Authentication failure for .* from <HOST>\\s*$",
    "source_ip": null,
    "destination_ip": null,
    "action": "block",
    "enabled": true,
    "priority": 100,
    "creation_date": "2023-06-15T10:30:00Z",
    "last_modified": "2023-06-15T10:30:00Z",
    "trigger_count": 23,
    "tags": ["ssh", "authentication"]
  },
  {
    "id": "2",
    "name": "Détecter les scans de ports",
    "description": "Détecte les tentatives de scan de ports",
    "rule_type": "suricata",
    "content": "alert tcp any any -> $HOME_NET any (msg:\"Port scan detected\"; flow:to_server; threshold: type threshold, track by_src, count 30, seconds 60; classtype:attempted-recon; sid:1000001; rev:1;)",
    "source_ip": null,
    "destination_ip": null,
    "action": "alert",
    "enabled": true,
    "priority": 80,
    "creation_date": "2023-06-10T14:20:00Z",
    "last_modified": "2023-06-10T14:20:00Z",
    "trigger_count": 5,
    "tags": ["scan", "reconnaissance"]
  }
]
```

### Récupérer une règle

```
GET /api/security/rules/{id}/
```

#### Exemple de réponse

```json
{
  "id": "1",
  "name": "Bloquer les tentatives de connexion SSH",
  "description": "Bloque les adresses IP après 5 tentatives de connexion SSH échouées",
  "rule_type": "fail2ban",
  "content": "failregex = ^Authentication failure for .* from <HOST>\\s*$",
  "source_ip": null,
  "destination_ip": null,
  "action": "block",
  "enabled": true,
  "priority": 100,
  "creation_date": "2023-06-15T10:30:00Z",
  "last_modified": "2023-06-15T10:30:00Z",
  "trigger_count": 23,
  "tags": ["ssh", "authentication"]
}
```

### Créer une règle

```
POST /api/security/rules/
```

#### Corps de la requête

```json
{
  "name": "Bloquer le trafic malveillant",
  "description": "Bloque le trafic provenant d'adresses IP connues comme malveillantes",
  "rule_type": "firewall",
  "source_ip": "192.168.1.100",
  "action": "block",
  "enabled": true,
  "priority": 50,
  "tags": ["malicious", "blacklist"]
}
```

#### Exemple de réponse

```json
{
  "id": "3",
  "name": "Bloquer le trafic malveillant",
  "description": "Bloque le trafic provenant d'adresses IP connues comme malveillantes",
  "rule_type": "firewall",
  "content": null,
  "source_ip": "192.168.1.100",
  "destination_ip": null,
  "action": "block",
  "enabled": true,
  "priority": 50,
  "creation_date": "2023-07-01T09:45:00Z",
  "last_modified": "2023-07-01T09:45:00Z",
  "trigger_count": 0,
  "tags": ["malicious", "blacklist"]
}
```

### Mettre à jour une règle

```
PUT /api/security/rules/{id}/
```

#### Corps de la requête

```json
{
  "name": "Bloquer le trafic malveillant",
  "description": "Bloque le trafic provenant d'adresses IP connues comme malveillantes",
  "source_ip": "192.168.1.0/24",
  "action": "block",
  "enabled": true,
  "priority": 30
}
```

#### Exemple de réponse

```json
{
  "id": "3",
  "name": "Bloquer le trafic malveillant",
  "description": "Bloque le trafic provenant d'adresses IP connues comme malveillantes",
  "rule_type": "firewall",
  "content": null,
  "source_ip": "192.168.1.0/24",
  "destination_ip": null,
  "action": "block",
  "enabled": true,
  "priority": 30,
  "creation_date": "2023-07-01T09:45:00Z",
  "last_modified": "2023-07-01T10:15:00Z",
  "trigger_count": 0,
  "tags": ["malicious", "blacklist"]
}
```

### Supprimer une règle

```
DELETE /api/security/rules/{id}/
```

#### Réponse

```
204 No Content
```

### Activer/désactiver une règle

```
PATCH /api/security/rules/{id}/toggle_status/
```

#### Corps de la requête

```json
{
  "enabled": false
}
```

#### Exemple de réponse

```json
{
  "id": "3",
  "name": "Bloquer le trafic malveillant",
  "description": "Bloque le trafic provenant d'adresses IP connues comme malveillantes",
  "rule_type": "firewall",
  "content": null,
  "source_ip": "192.168.1.0/24",
  "destination_ip": null,
  "action": "block",
  "enabled": false,
  "priority": 30,
  "creation_date": "2023-07-01T09:45:00Z",
  "last_modified": "2023-07-01T11:20:00Z",
  "trigger_count": 0,
  "tags": ["malicious", "blacklist"]
}
```

## Alertes de sécurité

Les alertes de sécurité sont générées lorsqu'une règle de sécurité est déclenchée ou qu'une anomalie est détectée.

### Niveaux de gravité

- `critical` : Alerte critique nécessitant une attention immédiate
- `high` : Alerte de haute importance
- `medium` : Alerte de moyenne importance
- `low` : Alerte de faible importance
- `info` : Information de sécurité

### Statuts d'alerte

- `new` : Nouvelle alerte non traitée
- `processed` : Alerte qui a été examinée
- `closed` : Alerte fermée après traitement

### Liste des alertes

```
GET /api/security/alerts/
```

#### Paramètres de requête

| Paramètre | Type | Description |
|-----------|------|-------------|
| severity | string | Filtrer par niveau de gravité (critical, high, medium, low, info) |
| status | string | Filtrer par statut (new, processed, closed) |
| source_ip | string | Filtrer par adresse IP source |
| from_date | string | Filtrer à partir d'une date (format ISO) |
| to_date | string | Filtrer jusqu'à une date (format ISO) |

#### Exemple de réponse

```json
[
  {
    "id": "1",
    "title": "Tentative de connexion SSH échouée",
    "description": "Plusieurs tentatives de connexion SSH échouées détectées",
    "source_ip": "203.0.113.42",
    "destination_ip": "192.168.1.10",
    "source_port": "54321",
    "destination_port": "22",
    "protocol": "tcp",
    "detection_time": "2023-07-02T15:30:00Z",
    "severity": "medium",
    "status": "new",
    "source_rule_id": "1",
    "false_positive": false,
    "tags": ["ssh", "authentication"]
  },
  {
    "id": "2",
    "title": "Scan de ports détecté",
    "description": "Scan de ports détecté depuis une adresse IP externe",
    "source_ip": "198.51.100.75",
    "destination_ip": "192.168.1.1",
    "source_port": null,
    "destination_port": null,
    "protocol": "tcp",
    "detection_time": "2023-07-02T16:45:00Z",
    "severity": "high",
    "status": "new",
    "source_rule_id": "2",
    "false_positive": false,
    "tags": ["scan", "reconnaissance"]
  }
]
```

### Récupérer une alerte

```
GET /api/security/alerts/{id}/
```

#### Exemple de réponse

```json
{
  "id": "1",
  "title": "Tentative de connexion SSH échouée",
  "description": "Plusieurs tentatives de connexion SSH échouées détectées",
  "source_ip": "203.0.113.42",
  "destination_ip": "192.168.1.10",
  "source_port": "54321",
  "destination_port": "22",
  "protocol": "tcp",
  "detection_time": "2023-07-02T15:30:00Z",
  "severity": "medium",
  "status": "new",
  "source_rule_id": "1",
  "raw_data": {
    "attempts": 5,
    "user": "root",
    "first_attempt": "2023-07-02T15:25:00Z",
    "last_attempt": "2023-07-02T15:30:00Z"
  },
  "false_positive": false,
  "tags": ["ssh", "authentication"]
}
```

### Marquer une alerte comme traitée

```
PATCH /api/security/alerts/{id}/mark_processed/
```

#### Exemple de réponse

```json
{
  "id": "1",
  "title": "Tentative de connexion SSH échouée",
  "description": "Plusieurs tentatives de connexion SSH échouées détectées",
  "source_ip": "203.0.113.42",
  "destination_ip": "192.168.1.10",
  "source_port": "54321",
  "destination_port": "22",
  "protocol": "tcp",
  "detection_time": "2023-07-02T15:30:00Z",
  "severity": "medium",
  "status": "processed",
  "source_rule_id": "1",
  "false_positive": false,
  "tags": ["ssh", "authentication"]
}
```

### Marquer une alerte comme faux positif

```
PATCH /api/security/alerts/{id}/mark_false_positive/
```

#### Exemple de réponse

```json
{
  "id": "1",
  "title": "Tentative de connexion SSH échouée",
  "description": "Plusieurs tentatives de connexion SSH échouées détectées",
  "source_ip": "203.0.113.42",
  "destination_ip": "192.168.1.10",
  "source_port": "54321",
  "destination_port": "22",
  "protocol": "tcp",
  "detection_time": "2023-07-02T15:30:00Z",
  "severity": "medium",
  "status": "closed",
  "source_rule_id": "1",
  "false_positive": true,
  "tags": ["ssh", "authentication"]
}
```

## Codes d'erreur

| Code | Description |
|------|-------------|
| 400 | Requête invalide |
| 401 | Non authentifié |
| 403 | Non autorisé |
| 404 | Ressource non trouvée |
| 409 | Conflit (par exemple, conflit entre règles) |
| 500 | Erreur interne du serveur |

## Exemples d'erreurs

### Erreur de validation

```json
{
  "detail": "La règle n'est pas valide",
  "errors": [
    "L'adresse IP source '300.168.1.100' est invalide",
    "L'option 'sid' est obligatoire dans une règle Suricata"
  ]
}
```

### Erreur de conflit

```json
{
  "detail": "La règle entre en conflit avec des règles existantes",
  "conflicts": [
    {
      "rule_id": "5",
      "rule_name": "Bloquer le trafic entrant",
      "conflict_type": "action_conflict",
      "description": "Action opposée pour des adresses IP qui se chevauchent",
      "severity": "high"
    }
  ]
}
``` 