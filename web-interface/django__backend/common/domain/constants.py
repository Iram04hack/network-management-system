"""
Constantes métier partagées par l'ensemble du système NMS.

Ce module centralise les différentes constantes métier utilisées
à travers le système pour garantir une cohérence globale.
"""

# Types d'équipements réseau supportés par le système
DEVICE_TYPES = [
    ('router', 'Router'),
    ('switch', 'Switch'),
    ('firewall', 'Firewall'),
    ('server', 'Server'),
    ('workstation', 'Workstation'),
    ('other', 'Other')
]

# Types de vérifications de monitoring supportées
CHECK_TYPES = [
    ('ping', 'ICMP Ping'),
    ('tcp', 'TCP Port'),
    ('http', 'HTTP/HTTPS'),
    ('snmp', 'SNMP'),
    ('custom', 'Custom Script')
]

# Types de métriques pour le système de monitoring
METRIC_TYPES = [
    ('counter', 'Counter'),  # Valeur qui ne peut qu'augmenter (ex: octets transmis)
    ('gauge', 'Gauge'),      # Valeur qui peut augmenter et diminuer (ex: température CPU)
    ('histogram', 'Histogram'),  # Distribution de valeurs (ex: temps de réponse)
    ('summary', 'Summary')   # Similaire à histogram mais avec percentiles calculés
]

# Niveaux de sévérité pour les alertes et notifications
SEVERITY_CHOICES = [
    ('warning', 'Warning'),    # Problème mineur, surveillance recommandée
    ('critical', 'Critical'),  # Problème majeur nécessitant une intervention
    ('unknown', 'Unknown')     # État indéterminé
]

# Statuts des alertes et incidents
STATUS_CHOICES = [
    ('active', 'Active'),          # Problème en cours, non résolu
    ('acknowledged', 'Acknowledged'),  # Problème reconnu, en cours de traitement
    ('resolved', 'Resolved')       # Problème résolu
]

# Modes QoS (Quality of Service)
QOS_MODES = [
    ('fifo', 'First In First Out'),
    ('priority', 'Priority Queuing'),
    ('fair', 'Fair Queuing'),
    ('weighted', 'Weighted Fair Queuing'),
    ('custom', 'Custom Queuing')
]

# Types d'authentification supportés
AUTH_TYPES = [
    ('local', 'Local Authentication'),
    ('ldap', 'LDAP'),
    ('radius', 'RADIUS'),
    ('tacacs', 'TACACS+'),
    ('oauth', 'OAuth 2.0'),
    ('saml', 'SAML')
] 