"""
Stratégies de génération et de distribution de rapports.

Ce module implémente le pattern Strategy pour la génération et la distribution
de différents types de rapports selon différents canaux.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ReportGenerationStrategy(ABC):
    """
    Stratégie abstraite pour la génération de rapports.
    
    Cette classe définit l'interface commune à toutes les stratégies 
    de génération de rapports.
    """
    
    @abstractmethod
    def generate(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un rapport selon les paramètres fournis.
        
        Args:
            parameters: Paramètres spécifiques au type de rapport
            
        Returns:
            Données du rapport généré
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Retourne les formats supportés par cette stratégie.
        
        Returns:
            Liste des formats supportés (pdf, csv, xlsx, etc.)
        """
        pass
        
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, str]:
        """
        Valide les paramètres du rapport.
        
        Args:
            parameters: Paramètres à valider
            
        Returns:
            Dictionnaire d'erreurs (vide si aucune erreur)
        """
        pass


class NetworkPerformanceReportStrategy(ReportGenerationStrategy):
    """
    Stratégie pour générer des rapports de performance réseau.
    """
    
    def generate(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un rapport de performance réseau.
        
        Args:
            parameters: Paramètres du rapport
                - start_date: Date de début de la période
                - end_date: Date de fin de la période
                - devices: Liste des équipements (optionnel)
                - metrics: Liste des métriques à inclure
                - format: Format du rapport (pdf, xlsx)
                
        Returns:
            Données du rapport généré
        """
        # Récupération des métriques de performance réseau
        start_date = parameters.get('start_date')
        end_date = parameters.get('end_date')
        devices = parameters.get('devices', [])
        metrics = parameters.get('metrics', ['cpu', 'memory', 'bandwidth'])
        
        # Initialiser le service d'intégration topologique
        try:
            from ..infrastructure.topology_integration_service import TopologyReportingService
            topology_service = TopologyReportingService()
        except ImportError as e:
            logger.warning(f"Service d'intégration topologique non disponible: {e}")
            topology_service = None
        
        # Récupérer les données de performance réelles
        if topology_service and topology_service.is_topology_service_available():
            performance_result = topology_service.get_network_performance_data({
                'start_date': start_date,
                'end_date': end_date,
                'devices': devices,
                'metrics': metrics
            })
            
            if performance_result['success']:
                performance_data = performance_result['data']
                logger.info(f"Données de performance récupérées depuis {performance_result['source']}")
            else:
                logger.error(f"Erreur lors de la récupération: {performance_result.get('error')}")
                performance_data = performance_result['data']  # Fallback data
        else:
            logger.warning("Service Central de Topologie non disponible - Utilisation de données simulées")
            performance_data = {
                'devices_analyzed': len(devices) if devices else 0,
                'summary_statistics': {},
                'device_performance': {}
            }
        
        # Génération du rapport avec les données réelles
        report_data = {
            'title': parameters.get('title', 'Rapport de performance réseau'),
            'subtitle': f"Période: {start_date} - {end_date}",
            'type': 'network_performance',
            'generated_at': datetime.now().isoformat(),
            'data_source': 'topology_service' if topology_service and topology_service.is_topology_service_available() else 'simulated',
            'content': {
                'summary': {
                    'total_devices': performance_data.get('devices_analyzed', len(devices) if devices else 0),
                    'period': {
                        'start_date': start_date,
                        'end_date': end_date
                    },
                    'metrics': metrics,
                    'statistics': performance_data.get('summary_statistics', {})
                },
                'device_performance': performance_data.get('device_performance', {}),
                'sections': self._build_performance_sections(performance_data, metrics)
            }
        }
        
        return report_data
    
    def _build_performance_sections(self, performance_data: Dict[str, Any], metrics: List[str]) -> List[Dict[str, Any]]:
        """
        Construit les sections du rapport à partir des données de performance.
        """
        sections = []
        
        # Section résumé exécutif
        summary_stats = performance_data.get('summary_statistics', {})
        if summary_stats:
            sections.append({
                'title': 'Résumé exécutif',
                'type': 'summary',
                'content': {
                    'total_devices': summary_stats.get('total_devices', 0),
                    'device_types': summary_stats.get('device_types', {}),
                    'overall_metrics': summary_stats.get('overall_metrics', {})
                }
            })
        
        # Section détails par métrique
        for metric in metrics:
            metric_section = {
                'title': f'Analyse {metric.upper()}',
                'type': 'metric_analysis',
                'metric': metric,
                'content': self._extract_metric_analysis(performance_data, metric)
            }
            sections.append(metric_section)
        
        # Section recommandations
        sections.append({
            'title': 'Recommandations',
            'type': 'recommendations',
            'content': self._generate_recommendations(performance_data, metrics)
        })
        
        return sections
    
    def _extract_metric_analysis(self, performance_data: Dict[str, Any], metric: str) -> Dict[str, Any]:
        """
        Extrait l'analyse d'une métrique spécifique.
        """
        device_performances = performance_data.get('device_performance', {})
        metric_analysis = {
            'devices_count': len(device_performances),
            'top_performers': [],
            'problem_devices': [],
            'trend_analysis': 'Stable'
        }
        
        metric_values = []
        for device_id, device_data in device_performances.items():
            device_metrics = device_data.get('metrics', {})
            if metric in device_metrics:
                metric_data = device_metrics[metric]
                metric_values.append({
                    'device_id': device_id,
                    'device_name': device_data.get('device_info', {}).get('name', f'Device {device_id}'),
                    'average': metric_data.get('average', 0),
                    'max': metric_data.get('max', 0)
                })
        
        if metric_values:
            # Trier par performance
            metric_values.sort(key=lambda x: x['average'])
            
            # Meilleurs performers (plus faible utilisation pour CPU/Memory, plus élevée pour bandwidth)
            if metric in ['cpu', 'memory']:
                metric_analysis['top_performers'] = metric_values[:3]
                metric_analysis['problem_devices'] = [d for d in metric_values if d['average'] > 80]
            else:  # bandwidth
                metric_analysis['top_performers'] = metric_values[-3:]
                metric_analysis['problem_devices'] = [d for d in metric_values if d['average'] < 20]
        
        return metric_analysis
    
    def _generate_recommendations(self, performance_data: Dict[str, Any], metrics: List[str]) -> List[str]:
        """
        Génère des recommandations basées sur l'analyse des performances.
        """
        recommendations = []
        summary_stats = performance_data.get('summary_statistics', {})
        overall_metrics = summary_stats.get('overall_metrics', {})
        
        # Recommandations basées sur les métriques globales
        if 'cpu' in overall_metrics:
            cpu_avg = overall_metrics['cpu'].get('network_average', 0)
            if cpu_avg > 70:
                recommendations.append("Attention: Utilisation CPU élevée sur le réseau. Considérer l'optimisation ou la mise à niveau.")
            elif cpu_avg < 20:
                recommendations.append("Utilisation CPU optimale sur l'ensemble du réseau.")
        
        if 'memory' in overall_metrics:
            memory_avg = overall_metrics['memory'].get('network_average', 0)
            if memory_avg > 80:
                recommendations.append("Utilisation mémoire critique détectée. Action immédiate recommandée.")
        
        if 'bandwidth' in overall_metrics:
            bandwidth_avg = overall_metrics['bandwidth'].get('network_average', 0)
            if bandwidth_avg > 85:
                recommendations.append("Saturation de bande passante approchant. Planifier l'augmentation de capacité.")
        
        # Recommandation générale si aucune spécifique
        if not recommendations:
            recommendations.append("Les performances réseau sont dans les paramètres normaux. Continuer la surveillance.")
        
        return recommendations
    
    def get_supported_formats(self) -> List[str]:
        """Liste des formats supportés."""
        return ['pdf', 'xlsx']
        
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, str]:
        """Valide les paramètres du rapport de performance réseau."""
        errors = {}
        
        if not parameters.get('start_date'):
            errors['start_date'] = "La date de début est requise"
            
        if not parameters.get('end_date'):
            errors['end_date'] = "La date de fin est requise"
            
        if not parameters.get('metrics'):
            errors['metrics'] = "Au moins une métrique doit être spécifiée"
            
        return errors


class SecurityAuditReportStrategy(ReportGenerationStrategy):
    """
    Stratégie pour générer des rapports d'audit de sécurité.
    """
    
    def generate(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un rapport d'audit de sécurité.
        
        Args:
            parameters: Paramètres du rapport
                - start_date: Date de début de la période
                - end_date: Date de fin de la période
                - include_alerts: Inclure les alertes (bool)
                - include_violations: Inclure les violations (bool)
                - format: Format du rapport (pdf, csv)
                
        Returns:
            Données du rapport généré
        """
        # Récupération des données d'audit de sécurité
        start_date = parameters.get('start_date')
        end_date = parameters.get('end_date')
        include_alerts = parameters.get('include_alerts', True)
        include_violations = parameters.get('include_violations', True)
        
        # Initialiser le service d'intégration topologique
        try:
            from ..infrastructure.topology_integration_service import TopologyReportingService
            topology_service = TopologyReportingService()
        except ImportError as e:
            logger.warning(f"Service d'intégration topologique non disponible: {e}")
            topology_service = None
        
        # Récupérer les données d'audit de sécurité réelles
        if topology_service and topology_service.is_topology_service_available():
            security_result = topology_service.get_security_audit_data({
                'start_date': start_date,
                'end_date': end_date,
                'include_alerts': include_alerts,
                'include_violations': include_violations
            })
            
            if security_result['success']:
                security_data = security_result['data']
                logger.info(f"Données de sécurité récupérées depuis {security_result['source']}")
            else:
                logger.error(f"Erreur lors de la récupération: {security_result.get('error')}")
                security_data = security_result['data']  # Fallback data
        else:
            logger.warning("Service Central de Topologie non disponible - Utilisation de données simulées")
            security_data = {
                'security_devices': 0,
                'alerts': [] if include_alerts else None,
                'violations': [] if include_violations else None,
                'compliance_status': {}
            }
        
        # Génération du rapport avec les données réelles
        report_data = {
            'title': parameters.get('title', "Rapport d'audit de sécurité"),
            'subtitle': f"Période: {start_date} - {end_date}",
            'type': 'security_audit',
            'generated_at': datetime.now().isoformat(),
            'data_source': 'topology_service' if topology_service and topology_service.is_topology_service_available() else 'simulated',
            'content': {
                'summary': {
                    'period': {
                        'start_date': start_date,
                        'end_date': end_date
                    },
                    'security_devices': security_data.get('security_devices', 0),
                    'include_alerts': include_alerts,
                    'include_violations': include_violations,
                    'compliance_status': security_data.get('compliance_status', {})
                },
                'alerts': security_data.get('alerts') if include_alerts else None,
                'violations': security_data.get('violations') if include_violations else None,
                'sections': self._build_security_sections(security_data, include_alerts, include_violations)
            }
        }
        
        return report_data
    
    def _build_security_sections(self, security_data: Dict[str, Any], include_alerts: bool, include_violations: bool) -> List[Dict[str, Any]]:
        """
        Construit les sections du rapport d'audit de sécurité.
        """
        sections = []
        
        # Section conformité
        compliance_status = security_data.get('compliance_status', {})
        if compliance_status:
            sections.append({
                'title': 'Statut de Conformité',
                'type': 'compliance',
                'content': compliance_status
            })
        
        # Section alertes
        if include_alerts:
            alerts = security_data.get('alerts', [])
            sections.append({
                'title': 'Alertes de Sécurité',
                'type': 'alerts',
                'content': {
                    'total_alerts': len(alerts),
                    'alerts_by_severity': self._group_alerts_by_severity(alerts),
                    'recent_alerts': alerts[:10] if alerts else []  # Les 10 plus récentes
                }
            })
        
        # Section violations
        if include_violations:
            violations = security_data.get('violations', [])
            sections.append({
                'title': 'Violations de Politique',
                'type': 'violations',
                'content': {
                    'total_violations': len(violations),
                    'violations_by_type': self._group_violations_by_type(violations),
                    'high_impact_violations': [v for v in violations if v.get('impact') == 'high']
                }
            })
        
        # Section recommandations
        sections.append({
            'title': 'Recommandations de Sécurité',
            'type': 'security_recommendations',
            'content': self._generate_security_recommendations(security_data)
        })
        
        return sections
    
    def _group_alerts_by_severity(self, alerts: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Groupe les alertes par niveau de sévérité.
        """
        severity_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for alert in alerts:
            severity = alert.get('severity', 'medium')
            if severity in severity_counts:
                severity_counts[severity] += 1
        return severity_counts
    
    def _group_violations_by_type(self, violations: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Groupe les violations par type.
        """
        type_counts = {}
        for violation in violations:
            violation_type = violation.get('violation_type', 'unknown')
            type_counts[violation_type] = type_counts.get(violation_type, 0) + 1
        return type_counts
    
    def _generate_security_recommendations(self, security_data: Dict[str, Any]) -> List[str]:
        """
        Génère des recommandations de sécurité.
        """
        recommendations = []
        
        # Recommandations basées sur la conformité
        compliance_status = security_data.get('compliance_status', {})
        compliance_rate = compliance_status.get('compliance_rate', 0)
        
        if compliance_rate < 80:
            recommendations.append("Taux de conformité faible détecté. Revoir les politiques de sécurité.")
        elif compliance_rate > 95:
            recommendations.append("Excellent taux de conformité. Maintenir les bonnes pratiques.")
        
        # Recommandations basées sur les alertes
        alerts = security_data.get('alerts', [])
        if alerts:
            critical_alerts = [a for a in alerts if a.get('severity') == 'critical']
            if critical_alerts:
                recommendations.append(f"{len(critical_alerts)} alerte(s) critique(s) détectée(s). Action immédiate requise.")
        
        # Recommandations basées sur les violations
        violations = security_data.get('violations', [])
        if violations:
            high_impact = [v for v in violations if v.get('impact') == 'high']
            if high_impact:
                recommendations.append(f"{len(high_impact)} violation(s) à fort impact. Investigation recommandée.")
        
        if not recommendations:
            recommendations.append("Aucun problème de sécurité majeur détecté. Continuer la surveillance.")
        
        return recommendations
    
    def get_supported_formats(self) -> List[str]:
        """Liste des formats supportés."""
        return ['pdf', 'csv']
        
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, str]:
        """Valide les paramètres du rapport d'audit de sécurité."""
        errors = {}
        
        if not parameters.get('start_date'):
            errors['start_date'] = "La date de début est requise"
            
        if not parameters.get('end_date'):
            errors['end_date'] = "La date de fin est requise"
            
        return errors


class ComplianceReportStrategy(ReportGenerationStrategy):
    """
    Stratégie pour générer des rapports de conformité.
    """
    
    def generate(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un rapport de conformité.
        
        Args:
            parameters: Paramètres du rapport
                - compliance_type: Type de conformité (pci, iso27001, gdpr, etc.)
                - devices: Liste des équipements à inclure (optionnel)
                - detailed: Niveau de détail (bool)
                - format: Format du rapport (pdf)
                
        Returns:
            Données du rapport généré
        """
        # Récupération des paramètres
        compliance_type = parameters.get('compliance_type', 'general')
        devices = parameters.get('devices', [])
        detailed = parameters.get('detailed', True)
        
        # Logique de génération du rapport de conformité
        report_data = {
            'title': parameters.get('title', f"Rapport de conformité {compliance_type.upper()}"),
            'subtitle': "État de conformité des systèmes",
            'type': 'compliance',
            'content': {
                'summary': {
                    'compliance_type': compliance_type,
                    'total_devices': len(devices) if devices else 0,
                    'detailed': detailed
                },
                'sections': []  # Sections à remplir avec les données
            }
        }
        
        # Logique pour récupérer et formater les données de conformité
        # (implémentation réelle connectée aux services de conformité)
        
        return report_data
    
    def get_supported_formats(self) -> List[str]:
        """Liste des formats supportés."""
        return ['pdf']
        
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, str]:
        """Valide les paramètres du rapport de conformité."""
        errors = {}
        
        if not parameters.get('compliance_type'):
            errors['compliance_type'] = "Le type de conformité est requis"
            
        return errors


class InventoryReportStrategy(ReportGenerationStrategy):
    """
    Stratégie pour générer des rapports d'inventaire.
    """
    
    def generate(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un rapport d'inventaire.
        
        Args:
            parameters: Paramètres du rapport
                - device_types: Types d'équipements à inclure
                - include_inactive: Inclure les équipements inactifs (bool)
                - group_by: Grouper par (location, type, vendor, etc.)
                - format: Format du rapport (pdf, xlsx, csv)
                
        Returns:
            Données du rapport généré
        """
        # Récupération des paramètres
        device_types = parameters.get('device_types', [])
        include_inactive = parameters.get('include_inactive', False)
        group_by = parameters.get('group_by', 'type')
        
        # Initialiser le service d'intégration topologique
        try:
            from ..infrastructure.topology_integration_service import TopologyReportingService
            topology_service = TopologyReportingService()
        except ImportError as e:
            logger.warning(f"Service d'intégration topologique non disponible: {e}")
            topology_service = None
        
        # Récupérer les données d'inventaire réelles
        if topology_service and topology_service.is_topology_service_available():
            inventory_result = topology_service.get_inventory_data({
                'device_types': device_types,
                'include_inactive': include_inactive,
                'group_by': group_by
            })
            
            if inventory_result['success']:
                inventory_data = inventory_result['data']
                logger.info(f"Données d'inventaire récupérées depuis {inventory_result['source']}")
            else:
                logger.error(f"Erreur lors de la récupération: {inventory_result.get('error')}")
                inventory_data = inventory_result['data']  # Fallback data
        else:
            logger.warning("Service Central de Topologie non disponible - Utilisation de données simulées")
            inventory_data = {
                'total_devices': 0,
                'device_types': {},
                'devices_by_location': {},
                'devices_by_status': {'active': 0, 'inactive': 0},
                'devices_details': []
            }
        
        # Génération du rapport avec les données réelles
        report_data = {
            'title': parameters.get('title', "Rapport d'inventaire des équipements"),
            'subtitle': f"Groupé par: {group_by} - {inventory_data.get('total_devices', 0)} équipements",
            'type': 'inventory',
            'generated_at': datetime.now().isoformat(),
            'data_source': 'topology_service' if topology_service and topology_service.is_topology_service_available() else 'simulated',
            'content': {
                'summary': {
                    'total_devices': inventory_data.get('total_devices', 0),
                    'device_types': device_types if device_types else list(inventory_data.get('device_types', {}).keys()),
                    'include_inactive': include_inactive,
                    'group_by': group_by,
                    'devices_by_status': inventory_data.get('devices_by_status', {}),
                    'last_updated': inventory_data.get('last_updated')
                },
                'inventory_data': inventory_data,
                'sections': self._build_inventory_sections(inventory_data, group_by, device_types, include_inactive)
            }
        }
        
        return report_data
    
    def _build_inventory_sections(self, inventory_data: Dict[str, Any], group_by: str, device_types: List[str], include_inactive: bool) -> List[Dict[str, Any]]:
        """
        Construit les sections du rapport d'inventaire.
        """
        sections = []
        
        # Section résumé global
        sections.append({
            'title': 'Résumé Global',
            'type': 'global_summary',
            'content': {
                'total_devices': inventory_data.get('total_devices', 0),
                'device_types_count': inventory_data.get('device_types', {}),
                'status_distribution': inventory_data.get('devices_by_status', {}),
                'location_distribution': inventory_data.get('devices_by_location', {})
            }
        })
        
        # Section groupée selon le paramètre group_by
        if group_by == 'type':
            sections.append(self._build_devices_by_type_section(inventory_data))
        elif group_by == 'location':
            sections.append(self._build_devices_by_location_section(inventory_data))
        elif group_by == 'status':
            sections.append(self._build_devices_by_status_section(inventory_data))
        
        # Section détails des équipements
        devices_details = inventory_data.get('devices_details', [])
        if devices_details:
            # Filtrer selon les critères
            filtered_devices = self._filter_devices(devices_details, device_types, include_inactive)
            
            sections.append({
                'title': 'Détail des Équipements',
                'type': 'devices_detail',
                'content': {
                    'devices_count': len(filtered_devices),
                    'devices': filtered_devices[:50] if len(filtered_devices) > 50 else filtered_devices,  # Limiter à 50 pour le rapport
                    'truncated': len(filtered_devices) > 50
                }
            })
        
        return sections
    
    def _build_devices_by_type_section(self, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construit la section groupée par type d'équipement.
        """
        device_types = inventory_data.get('device_types', {})
        devices_details = inventory_data.get('devices_details', [])
        
        type_details = {}
        for device_type, count in device_types.items():
            type_devices = [d for d in devices_details if d.get('device_type') == device_type]
            type_details[device_type] = {
                'count': count,
                'active_count': len([d for d in type_devices if d.get('is_active', True)]),
                'manufacturers': list(set([d.get('manufacturer', 'Unknown') for d in type_devices])),
                'models': list(set([d.get('model', 'Unknown') for d in type_devices]))
            }
        
        return {
            'title': 'Inventaire par Type d\'\u00c9quipement',
            'type': 'by_device_type',
            'content': type_details
        }
    
    def _build_devices_by_location_section(self, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construit la section groupée par emplacement.
        """
        devices_by_location = inventory_data.get('devices_by_location', {})
        devices_details = inventory_data.get('devices_details', [])
        
        location_details = {}
        for location, count in devices_by_location.items():
            location_devices = [d for d in devices_details if d.get('location') == location]
            location_details[location] = {
                'count': count,
                'device_types': list(set([d.get('device_type', 'unknown') for d in location_devices])),
                'active_count': len([d for d in location_devices if d.get('is_active', True)])
            }
        
        return {
            'title': 'Inventaire par Emplacement',
            'type': 'by_location',
            'content': location_details
        }
    
    def _build_devices_by_status_section(self, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construit la section groupée par statut.
        """
        devices_by_status = inventory_data.get('devices_by_status', {})
        devices_details = inventory_data.get('devices_details', [])
        
        status_details = {}
        for status, count in devices_by_status.items():
            is_active = status == 'active'
            status_devices = [d for d in devices_details if d.get('is_active', True) == is_active]
            status_details[status] = {
                'count': count,
                'device_types': list(set([d.get('device_type', 'unknown') for d in status_devices])),
                'recent_changes': []  # Pourrait être enrichi avec des données de changement
            }
        
        return {
            'title': 'Inventaire par Statut',
            'type': 'by_status',
            'content': status_details
        }
    
    def _filter_devices(self, devices: List[Dict[str, Any]], device_types: List[str], include_inactive: bool) -> List[Dict[str, Any]]:
        """
        Filtre les équipements selon les critères.
        """
        filtered = devices
        
        # Filtrer par type si spécifié
        if device_types:
            filtered = [d for d in filtered if d.get('device_type') in device_types]
        
        # Filtrer par statut si nécessaire
        if not include_inactive:
            filtered = [d for d in filtered if d.get('is_active', True)]
        
        return filtered
    
    def get_supported_formats(self) -> List[str]:
        """Liste des formats supportés."""
        return ['pdf', 'xlsx', 'csv']
        
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, str]:
        """Valide les paramètres du rapport d'inventaire."""
        errors = {}
        
        if parameters.get('group_by') and parameters.get('group_by') not in ['type', 'location', 'vendor', 'status']:
            errors['group_by'] = "Option de regroupement non supportée"
            
        return errors


# Stratégies de distribution de rapports

class ReportDistributionStrategy(ABC):
    """
    Stratégie abstraite pour la distribution de rapports.
    
    Cette classe définit l'interface commune à toutes les stratégies 
    de distribution de rapports.
    """
    
    @abstractmethod
    def distribute(self, report_info: Dict[str, Any], recipients: List[Dict[str, Any]]) -> bool:
        """
        Distribue un rapport aux destinataires spécifiés.
        
        Args:
            report_info: Informations sur le rapport
            recipients: Liste des destinataires
            
        Returns:
            True si la distribution a réussi
        """
        pass
        
    @abstractmethod
    def validate_recipients(self, recipients: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Valide les destinataires du rapport.
        
        Args:
            recipients: Destinataires à valider
            
        Returns:
            Dictionnaire d'erreurs (vide si aucune erreur)
        """
        pass


class EmailDistributionStrategy(ReportDistributionStrategy):
    """
    Stratégie pour distribuer des rapports par email.
    """
    
    def distribute(self, report_info: Dict[str, Any], recipients: List[Dict[str, Any]]) -> bool:
        """
        Distribue un rapport par email.
        
        Args:
            report_info: Informations sur le rapport
            recipients: Liste des destinataires avec leur email
            
        Returns:
            True si l'envoi a réussi
        """
        # Logique d'envoi d'email avec le rapport en pièce jointe
        # (implémentation réelle utilisant un service d'email)
        
        file_path = report_info.get('file_path')
        subject = f"Rapport {report_info.get('title')}"
        
        # Simulation de l'envoi d'emails
        for recipient in recipients:
            email = recipient.get('email')
            if email:
                # Logique d'envoi d'email
                pass
        
        return True
    
    def validate_recipients(self, recipients: List[Dict[str, Any]]) -> Dict[str, str]:
        """Valide les destinataires pour la distribution par email."""
        errors = {}
        
        if not recipients:
            errors['recipients'] = "Au moins un destinataire est requis"
            
        # Vérifier que chaque destinataire a une adresse email
        for i, recipient in enumerate(recipients):
            if not recipient.get('email'):
                errors[f'recipient_{i}'] = "L'adresse email est requise"
                
        return errors


class WebhookDistributionStrategy(ReportDistributionStrategy):
    """
    Stratégie pour distribuer des rapports via webhook.
    """
    
    def distribute(self, report_info: Dict[str, Any], recipients: List[Dict[str, Any]]) -> bool:
        """
        Distribue un rapport via webhook.
        
        Args:
            report_info: Informations sur le rapport
            recipients: Liste des destinataires avec leur URL webhook
            
        Returns:
            True si l'envoi a réussi
        """
        # Logique d'envoi du rapport via webhook
        # (implémentation réelle utilisant un client HTTP)
        
        # Simulation de l'envoi via webhook
        for recipient in recipients:
            webhook_url = recipient.get('webhook_url')
            if webhook_url:
                # Logique d'envoi via webhook
                pass
        
        return True
    
    def validate_recipients(self, recipients: List[Dict[str, Any]]) -> Dict[str, str]:
        """Valide les destinataires pour la distribution via webhook."""
        errors = {}
        
        if not recipients:
            errors['recipients'] = "Au moins un destinataire est requis"
            
        # Vérifier que chaque destinataire a une URL webhook
        for i, recipient in enumerate(recipients):
            if not recipient.get('webhook_url'):
                errors[f'recipient_{i}'] = "L'URL webhook est requise"
                
        return errors


class SlackDistributionStrategy(ReportDistributionStrategy):
    """
    Stratégie pour distribuer des rapports via Slack.
    """
    
    def distribute(self, report_info: Dict[str, Any], recipients: List[Dict[str, Any]]) -> bool:
        """
        Distribue un rapport via Slack.
        
        Args:
            report_info: Informations sur le rapport
            recipients: Liste des destinataires avec leur canal Slack
            
        Returns:
            True si l'envoi a réussi
        """
        # Logique d'envoi du rapport via Slack
        # (implémentation réelle utilisant une API Slack)
        
        # Simulation de l'envoi via Slack
        for recipient in recipients:
            channel = recipient.get('slack_channel')
            if channel:
                # Logique d'envoi via Slack
                pass
        
        return True
    
    def validate_recipients(self, recipients: List[Dict[str, Any]]) -> Dict[str, str]:
        """Valide les destinataires pour la distribution via Slack."""
        errors = {}
        
        if not recipients:
            errors['recipients'] = "Au moins un destinataire est requis"
            
        # Vérifier que chaque destinataire a un canal Slack
        for i, recipient in enumerate(recipients):
            if not recipient.get('slack_channel'):
                errors[f'recipient_{i}'] = "Le canal Slack est requis"
                
        return errors


class FileShareDistributionStrategy(ReportDistributionStrategy):
    """
    Stratégie pour distribuer des rapports via partage de fichiers.
    """
    
    def distribute(self, report_info: Dict[str, Any], recipients: List[Dict[str, Any]]) -> bool:
        """
        Distribue un rapport via partage de fichiers.
        
        Args:
            report_info: Informations sur le rapport
            recipients: Liste des destinataires avec leur chemin de partage
            
        Returns:
            True si l'envoi a réussi
        """
        # Logique de copie du rapport vers des partages réseau
        # (implémentation réelle utilisant des opérations de fichiers)
        
        file_path = report_info.get('file_path')
        
        # Simulation de la copie vers des partages
        for recipient in recipients:
            share_path = recipient.get('share_path')
            if share_path:
                # Logique de copie de fichier
                pass
        
        return True
    
    def validate_recipients(self, recipients: List[Dict[str, Any]]) -> Dict[str, str]:
        """Valide les destinataires pour la distribution via partage de fichiers."""
        errors = {}
        
        if not recipients:
            errors['recipients'] = "Au moins un destinataire est requis"
            
        # Vérifier que chaque destinataire a un chemin de partage
        for i, recipient in enumerate(recipients):
            if not recipient.get('share_path'):
                errors[f'recipient_{i}'] = "Le chemin de partage est requis"
                
        return errors 