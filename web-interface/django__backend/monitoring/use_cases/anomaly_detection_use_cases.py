"""
Use cases pour la détection d'anomalies.

Ce module contient les cas d'utilisation pour la détection automatique
d'anomalies dans les métriques de surveillance.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import statistics
from decimal import Decimal

from ..domain.interfaces.repositories import (
    MetricValueRepository,
    MetricsRepository,
    AlertRepository
)
from ..domain.interfaces.services import (
    AnomalyDetectionService,
    AlertService
)

logger = logging.getLogger(__name__)


class DetectAnomaliesUseCase:
    """
    Use case pour la détection d'anomalies dans les métriques.
    
    Utilise différents algorithmes de détection d'anomalies
    pour identifier les comportements anormaux.
    """
    
    def __init__(
        self,
        metric_value_repository: MetricValueRepository,
        metrics_repository: MetricsRepository,
        alert_repository: AlertRepository,
        anomaly_detection_service: AnomalyDetectionService,
        alert_service: AlertService
    ):
        self.metric_value_repository = metric_value_repository
        self.metrics_repository = metrics_repository
        self.alert_repository = alert_repository
        self.anomaly_detection_service = anomaly_detection_service
        self.alert_service = alert_service
    
    def execute(
        self,
        metric_id: Optional[int] = None,
        device_id: Optional[int] = None,
        algorithm: str = "statistical",
        sensitivity: float = 0.95
    ) -> Dict[str, Any]:
        """
        Exécute la détection d'anomalies.
        
        Args:
            metric_id: ID de la métrique spécifique (optionnel)
            device_id: ID de l'équipement spécifique (optionnel)
            algorithm: Algorithme de détection ("statistical", "isolation_forest", "z_score")
            sensitivity: Sensibilité de la détection (0.0 à 1.0)
            
        Returns:
            Résultat de la détection avec anomalies trouvées
        """
        try:
            if metric_id:
                return self._detect_metric_anomalies(metric_id, algorithm, sensitivity)
            elif device_id:
                return self._detect_device_anomalies(device_id, algorithm, sensitivity)
            else:
                return self._detect_all_anomalies(algorithm, sensitivity)
                
        except Exception as e:
            logger.error(f"Erreur lors de la détection d'anomalies: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _detect_metric_anomalies(
        self,
        metric_id: int,
        algorithm: str,
        sensitivity: float
    ) -> Dict[str, Any]:
        """Détecte les anomalies pour une métrique spécifique."""
        try:
            # Récupérer les données historiques (30 derniers jours)
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)
            
            values = self.metric_value_repository.get_values_by_period(
                metric_id, start_time, end_time
            )
            
            if len(values) < 10:
                return {
                    "success": False,
                    "message": f"Données insuffisantes pour la métrique {metric_id}",
                    "metric_id": metric_id,
                    "required_points": 10,
                    "available_points": len(values)
                }
            
            # Effectuer la détection selon l'algorithme choisi
            anomalies = self._detect_with_algorithm(values, algorithm, sensitivity)
            
            # Créer des alertes pour les anomalies trouvées
            alerts_created = 0
            for anomaly in anomalies:
                alert_created = self._create_anomaly_alert(metric_id, anomaly)
                if alert_created:
                    alerts_created += 1
            
            return {
                "success": True,
                "metric_id": metric_id,
                "algorithm": algorithm,
                "sensitivity": sensitivity,
                "anomalies_found": len(anomalies),
                "alerts_created": alerts_created,
                "anomalies": anomalies[:10],  # Limiter à 10 pour la réponse
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection pour la métrique {metric_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "metric_id": metric_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def _detect_device_anomalies(
        self,
        device_id: int,
        algorithm: str,
        sensitivity: float
    ) -> Dict[str, Any]:
        """Détecte les anomalies pour toutes les métriques d'un équipement."""
        try:
            metrics = self.metrics_repository.get_by_device(device_id)
            
            if not metrics:
                return {
                    "success": False,
                    "message": f"Aucune métrique trouvée pour l'équipement {device_id}",
                    "device_id": device_id
                }
            
            total_anomalies = 0
            total_alerts = 0
            metric_results = []
            
            for metric in metrics:
                result = self._detect_metric_anomalies(metric.id, algorithm, sensitivity)
                if result["success"]:
                    total_anomalies += result["anomalies_found"]
                    total_alerts += result["alerts_created"]
                    metric_results.append({
                        "metric_id": metric.id,
                        "metric_name": metric.name,
                        "anomalies_found": result["anomalies_found"]
                    })
            
            return {
                "success": True,
                "device_id": device_id,
                "metrics_analyzed": len(metrics),
                "total_anomalies": total_anomalies,
                "total_alerts": total_alerts,
                "algorithm": algorithm,
                "sensitivity": sensitivity,
                "metric_results": metric_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection pour l'équipement {device_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "device_id": device_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def _detect_all_anomalies(
        self,
        algorithm: str,
        sensitivity: float
    ) -> Dict[str, Any]:
        """Détecte les anomalies pour toutes les métriques actives."""
        try:
            metrics = self.metrics_repository.get_active_metrics()
            
            total_anomalies = 0
            total_alerts = 0
            devices_processed = set()
            error_count = 0
            
            for metric in metrics:
                try:
                    result = self._detect_metric_anomalies(metric.id, algorithm, sensitivity)
                    if result["success"]:
                        total_anomalies += result["anomalies_found"]
                        total_alerts += result["alerts_created"]
                        devices_processed.add(metric.device_id)
                    else:
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"Erreur lors de la détection pour la métrique {metric.id}: {e}")
                    error_count += 1
            
            return {
                "success": True,
                "metrics_analyzed": len(metrics),
                "devices_processed": len(devices_processed),
                "total_anomalies": total_anomalies,
                "total_alerts": total_alerts,
                "errors": error_count,
                "algorithm": algorithm,
                "sensitivity": sensitivity,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection globale: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _detect_with_algorithm(
        self,
        values: List[Dict],
        algorithm: str,
        sensitivity: float
    ) -> List[Dict[str, Any]]:
        """Applique l'algorithme de détection choisi."""
        if algorithm == "statistical":
            return self._statistical_detection(values, sensitivity)
        elif algorithm == "z_score":
            return self._z_score_detection(values, sensitivity)
        elif algorithm == "isolation_forest":
            return self._isolation_forest_detection(values, sensitivity)
        else:
            raise ValueError(f"Algorithme non supporté: {algorithm}")
    
    def _statistical_detection(
        self,
        values: List[Dict],
        sensitivity: float
    ) -> List[Dict[str, Any]]:
        """Détection statistique basée sur les écarts-types."""
        numeric_values = [float(v['value']) for v in values]
        
        if len(numeric_values) < 3:
            return []
        
        mean = statistics.mean(numeric_values)
        std_dev = statistics.stdev(numeric_values)
        
        # Calculer le seuil basé sur la sensibilité
        threshold = std_dev * (3 - sensitivity * 2)  # Sensibilité élevée = seuil bas
        
        anomalies = []
        for i, value_dict in enumerate(values):
            value = float(value_dict['value'])
            deviation = abs(value - mean)
            
            if deviation > threshold:
                anomalies.append({
                    "timestamp": value_dict['timestamp'],
                    "value": value,
                    "expected_range": {
                        "min": mean - threshold,
                        "max": mean + threshold
                    },
                    "deviation": deviation,
                    "severity": self._calculate_severity(deviation, std_dev),
                    "algorithm": "statistical"
                })
        
        return anomalies
    
    def _z_score_detection(
        self,
        values: List[Dict],
        sensitivity: float
    ) -> List[Dict[str, Any]]:
        """Détection basée sur le Z-score."""
        numeric_values = [float(v['value']) for v in values]
        
        if len(numeric_values) < 3:
            return []
        
        mean = statistics.mean(numeric_values)
        std_dev = statistics.stdev(numeric_values)
        
        # Seuil Z-score basé sur la sensibilité
        z_threshold = 3 - sensitivity * 1.5  # Sensibilité élevée = seuil bas
        
        anomalies = []
        for i, value_dict in enumerate(values):
            value = float(value_dict['value'])
            z_score = abs(value - mean) / std_dev if std_dev > 0 else 0
            
            if z_score > z_threshold:
                anomalies.append({
                    "timestamp": value_dict['timestamp'],
                    "value": value,
                    "z_score": z_score,
                    "threshold": z_threshold,
                    "severity": self._calculate_severity_from_z_score(z_score),
                    "algorithm": "z_score"
                })
        
        return anomalies
    
    def _isolation_forest_detection(
        self,
        values: List[Dict],
        sensitivity: float
    ) -> List[Dict[str, Any]]:
        """Détection par Isolation Forest (version simplifiée)."""
        # Implémentation simplifiée d'Isolation Forest
        # Dans un vrai système, utiliser scikit-learn
        
        numeric_values = [float(v['value']) for v in values]
        
        if len(numeric_values) < 10:
            return []
        
        # Simulation d'Isolation Forest avec des quartiles
        q1 = statistics.quantiles(numeric_values, n=4)[0]
        q3 = statistics.quantiles(numeric_values, n=4)[2]
        iqr = q3 - q1
        
        # Seuil basé sur la sensibilité
        outlier_factor = 1.5 + (1 - sensitivity) * 1.5
        lower_bound = q1 - outlier_factor * iqr
        upper_bound = q3 + outlier_factor * iqr
        
        anomalies = []
        for i, value_dict in enumerate(values):
            value = float(value_dict['value'])
            
            if value < lower_bound or value > upper_bound:
                distance_from_bounds = min(
                    abs(value - lower_bound) if value < lower_bound else float('inf'),
                    abs(value - upper_bound) if value > upper_bound else float('inf')
                )
                
                anomalies.append({
                    "timestamp": value_dict['timestamp'],
                    "value": value,
                    "bounds": {
                        "lower": lower_bound,
                        "upper": upper_bound
                    },
                    "distance": distance_from_bounds,
                    "severity": self._calculate_severity_from_distance(distance_from_bounds, iqr),
                    "algorithm": "isolation_forest"
                })
        
        return anomalies
    
    def _calculate_severity(self, deviation: float, std_dev: float) -> str:
        """Calcule la sévérité basée sur la déviation."""
        if deviation > 3 * std_dev:
            return "critical"
        elif deviation > 2 * std_dev:
            return "high"
        elif deviation > std_dev:
            return "medium"
        else:
            return "low"
    
    def _calculate_severity_from_z_score(self, z_score: float) -> str:
        """Calcule la sévérité basée sur le Z-score."""
        if z_score > 3:
            return "critical"
        elif z_score > 2.5:
            return "high"
        elif z_score > 2:
            return "medium"
        else:
            return "low"
    
    def _calculate_severity_from_distance(self, distance: float, iqr: float) -> str:
        """Calcule la sévérité basée sur la distance aux bornes."""
        if distance > 3 * iqr:
            return "critical"
        elif distance > 2 * iqr:
            return "high"
        elif distance > iqr:
            return "medium"
        else:
            return "low"
    
    def _create_anomaly_alert(self, metric_id: int, anomaly: Dict[str, Any]) -> bool:
        """Crée une alerte pour une anomalie détectée."""
        try:
            metric = self.metrics_repository.get_by_id(metric_id)
            if not metric:
                return False
            
            alert_data = {
                "title": f"Anomalie détectée: {metric.name}",
                "description": f"Valeur anormale {anomaly['value']} détectée par {anomaly['algorithm']}",
                "severity": anomaly["severity"],
                "source_type": "anomaly_detection",
                "source_id": metric_id,
                "device_id": metric.device_id,
                "details": anomaly
            }
            
            self.alert_service.create_alert(alert_data)
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création d'alerte pour l'anomalie: {e}")
            return False


class AnomalyAnalysisUseCase:
    """
    Use case pour l'analyse des anomalies détectées.
    
    Fournit des analyses et statistiques sur les anomalies
    pour améliorer la détection.
    """
    
    def __init__(
        self,
        alert_repository: AlertRepository,
        metric_value_repository: MetricValueRepository
    ):
        self.alert_repository = alert_repository
        self.metric_value_repository = metric_value_repository
    
    def execute(
        self,
        start_time: datetime,
        end_time: datetime,
        device_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyse les anomalies sur une période donnée.
        
        Args:
            start_time: Début de la période d'analyse
            end_time: Fin de la période d'analyse
            device_id: ID de l'équipement spécifique (optionnel)
            
        Returns:
            Analyse des anomalies avec statistiques
        """
        try:
            # Récupérer les alertes d'anomalies
            alerts = self.alert_repository.get_anomaly_alerts(
                start_time, end_time, device_id
            )
            
            if not alerts:
                return {
                    "success": True,
                    "message": "Aucune anomalie trouvée pour la période",
                    "anomaly_count": 0,
                    "period": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat()
                    }
                }
            
            # Analyser les anomalies
            analysis = self._analyze_anomalies(alerts)
            
            analysis.update({
                "success": True,
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "device_id": device_id,
                "timestamp": datetime.now().isoformat()
            })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des anomalies: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _analyze_anomalies(self, alerts: List[Dict]) -> Dict[str, Any]:
        """Analyse les alertes d'anomalies."""
        total_anomalies = len(alerts)
        
        # Analyser par sévérité
        severity_counts = {}
        for alert in alerts:
            severity = alert.get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Analyser par algorithme
        algorithm_counts = {}
        for alert in alerts:
            details = alert.get("details", {})
            algorithm = details.get("algorithm", "unknown")
            algorithm_counts[algorithm] = algorithm_counts.get(algorithm, 0) + 1
        
        # Analyser la distribution temporelle
        hourly_distribution = self._calculate_hourly_distribution(alerts)
        
        # Identifier les équipements les plus affectés
        device_counts = {}
        for alert in alerts:
            device_id = alert.get("device_id")
            if device_id:
                device_counts[device_id] = device_counts.get(device_id, 0) + 1
        
        top_devices = sorted(
            device_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "anomaly_count": total_anomalies,
            "severity_distribution": severity_counts,
            "algorithm_distribution": algorithm_counts,
            "hourly_distribution": hourly_distribution,
            "top_affected_devices": [
                {"device_id": device_id, "anomaly_count": count}
                for device_id, count in top_devices
            ],
            "average_anomalies_per_day": total_anomalies / max(1, len(set(
                alert["created_at"].date() for alert in alerts
            )))
        }
    
    def _calculate_hourly_distribution(self, alerts: List[Dict]) -> Dict[int, int]:
        """Calcule la distribution horaire des anomalies."""
        hourly_counts = {hour: 0 for hour in range(24)}
        
        for alert in alerts:
            created_at = alert.get("created_at")
            if created_at:
                hour = created_at.hour
                hourly_counts[hour] += 1
        
        return hourly_counts