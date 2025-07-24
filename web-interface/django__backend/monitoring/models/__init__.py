"""
Package contenant les modèles Django pour le module de surveillance.
"""

# Import des modèles d'alertes
from .alert import Alert, AlertComment, AlertHistory

# Import des modèles de métriques
from .metric import (
    MetricsDefinition, DeviceMetric, MetricValue,
    ThresholdRule, AnomalyDetectionConfig, MetricThreshold
)

# Import des modèles de vérifications de service
from .service_check import (
    MonitoringTemplate, ServiceCheck, 
    DeviceServiceCheck, CheckResult
)

# Import des modèles de notification
from .notification import (
    Notification, NotificationChannel, NotificationRule
)

# Import des modèles de tableaux de bord
from .dashboard import (
    Dashboard, DashboardWidget, SavedView,
    BusinessKPI, KPIHistory
)

# Les autres imports seront ajoutés au fur et à mesure de la création des modèles 