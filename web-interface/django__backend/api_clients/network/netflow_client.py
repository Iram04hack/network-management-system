"""
Client NetFlow pour analyser les flux réseau.

Ce module fournit un client robuste pour interagir avec les données NetFlow
en respectant les principes de sécurité et de validation.
"""

import ipaddress
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime
import json

from ..base import BaseAPIClient
from ..infrastructure.input_validator import (
    IPAddressValidator, 
    TimestampValidator,
    PortValidator,
    CompositeValidator,
    StringValidator
)
from ..domain.exceptions import ValidationException, APIClientDataException

logger = logging.getLogger(__name__)

class NetflowClient(BaseAPIClient):
    """
    Client pour analyser les données NetFlow.
    
    Ce client permet d'interroger et d'analyser les flux réseau collectés
    via NetFlow/sFlow avec validation sécurisée des paramètres.
    """
    
    # Protocoles supportés
    SUPPORTED_PROTOCOLS = {
        1: 'ICMP', 6: 'TCP', 17: 'UDP', 
        47: 'GRE', 50: 'ESP', 89: 'OSPF'
    }
    
    # Types de requêtes supportés
    QUERY_TYPES = ['flows', 'top_hosts', 'top_protocols', 'top_ports', 'statistics']
    
    def __init__(
        self, 
        base_url: str,
        collector_host: Optional[str] = None,
        collector_port: int = 2055,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        verify_ssl: bool = True,
        timeout: int = 30  # Plus long pour les requêtes analytiques
    ):
        """
        Initialise le client NetFlow.
        
        Args:
            base_url: URL de base de l'API NetFlow
            collector_host: Hôte du collecteur NetFlow
            collector_port: Port du collecteur NetFlow
            username: Nom d'utilisateur pour l'authentification
            password: Mot de passe pour l'authentification  
            api_key: Clé API pour l'authentification
            verify_ssl: Vérifier les certificats SSL
            timeout: Délai d'attente pour les requêtes
        """
        super().__init__(base_url, username, password, api_key, verify_ssl, timeout)
        
        self.collector_host = collector_host
        self.collector_port = collector_port
        
        # Initialiser les validateurs
        self._init_validators()
        
        logger.info(f"NetFlow client initialisé pour {base_url}")
    
    def _init_validators(self):
        """Initialise les validateurs pour les paramètres d'entrée."""
        self.validators = CompositeValidator({
            'src_ip': IPAddressValidator(allow_private=True),
            'dst_ip': IPAddressValidator(allow_private=True),
            'src_port': PortValidator(),
            'dst_port': PortValidator(),
            'start_time': TimestampValidator(),
            'end_time': TimestampValidator(),
            'protocol': StringValidator(
                min_length=1,
                max_length=10,
                strip_whitespace=True
            ),
            'interface': StringValidator(
                min_length=1,
                max_length=50,
                strip_whitespace=True
            )
        })
    
    def test_connection(self) -> bool:
        """
        Teste la connexion au service NetFlow.
        
        Returns:
            True si la connexion est établie avec succès
        """
        try:
            response = self.get("status")
            return response.get("success", False) and "version" in response
        except Exception as e:
            logger.error(f"Test de connexion NetFlow échoué: {e}")
            return False
    
    def get_collector_status(self) -> Dict[str, Any]:
        """
        Récupère l'état du collecteur NetFlow.
        
        Returns:
            État et statistiques du collecteur
        """
        try:
            return self.get("collector/status")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut collecteur: {e}")
            return {"success": False, "error": str(e)}
    
    def query_flows(
        self,
        start_time: Union[datetime, int, str],
        end_time: Union[datetime, int, str],
        src_ip: Optional[str] = None,
        dst_ip: Optional[str] = None,
        src_port: Optional[int] = None,
        dst_port: Optional[int] = None,
        protocol: Optional[Union[str, int]] = None,
        interface: Optional[str] = None,
        limit: int = 1000,
        aggregation: str = 'raw'
    ) -> Dict[str, Any]:
        """
        Interroge les flux NetFlow avec filtres avancés.
        
        Args:
            start_time: Heure de début de la requête
            end_time: Heure de fin de la requête
            src_ip: Adresse IP source (optionnel)
            dst_ip: Adresse IP destination (optionnel)
            src_port: Port source (optionnel)
            dst_port: Port destination (optionnel)
            protocol: Protocole (nom ou numéro, optionnel)
            interface: Interface réseau (optionnel)
            limit: Nombre maximum de flux à retourner
            aggregation: Type d'agrégation ('raw', 'summarized', 'grouped')
            
        Returns:
            Résultats des flux NetFlow
        """
        try:
            # Valider les paramètres d'entrée
            validated_params = self._validate_query_params(
                start_time=start_time,
                end_time=end_time,
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                protocol=protocol,
                interface=interface
            )
            
            # Construire les paramètres de la requête
            query_params = {
                'start_time': validated_params['start_time'],
                'end_time': validated_params['end_time'],
                'limit': min(limit, 10000),  # Limite de sécurité
                'aggregation': aggregation
            }
            
            # Ajouter les filtres optionnels
            for field in ['src_ip', 'dst_ip', 'src_port', 'dst_port', 'protocol', 'interface']:
                if field in validated_params:
                    query_params[field] = validated_params[field]
            
            response = self.get("flows/query", params=query_params)
            
            if response.get("success", True):
                # Enrichir les données avec des informations supplémentaires
                return self._enrich_flow_data(response)
            
            return response
            
        except ValidationException as e:
            logger.warning(f"Paramètres de requête NetFlow invalides: {e}")
            return {"success": False, "error": f"Paramètres invalides: {e.message}"}
        except Exception as e:
            logger.error(f"Erreur lors de la requête NetFlow: {e}")
            return {"success": False, "error": str(e)}
    
    def get_top_talkers(
        self,
        start_time: Union[datetime, int, str],
        end_time: Union[datetime, int, str],
        top_n: int = 10,
        metric: str = 'bytes',
        direction: str = 'bidirectional'
    ) -> Dict[str, Any]:
        """
        Récupère les principaux communicants (top talkers).
        
        Args:
            start_time: Heure de début
            end_time: Heure de fin
            top_n: Nombre de résultats à retourner
            metric: Métrique de classement ('bytes', 'packets', 'flows')
            direction: Direction du trafic ('src', 'dst', 'bidirectional')
            
        Returns:
            Liste des top talkers
        """
        try:
            validated_params = self._validate_time_range(start_time, end_time)
            
            query_params = {
                'start_time': validated_params['start_time'],
                'end_time': validated_params['end_time'],
                'top_n': min(top_n, 100),  # Limite de sécurité
                'metric': metric,
                'direction': direction
            }
            
            response = self.get("analytics/top_talkers", params=query_params)
            
            if response.get("success", True) and "data" in response:
                # Enrichir avec des informations géographiques et organisationnelles
                return self._enrich_top_talkers(response)
            
            return response
            
        except ValidationException as e:
            logger.warning(f"Paramètres top talkers invalides: {e}")
            return {"success": False, "error": f"Paramètres invalides: {e.message}"}
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des top talkers: {e}")
            return {"success": False, "error": str(e)}
    
    def get_protocol_distribution(
        self,
        start_time: Union[datetime, int, str],
        end_time: Union[datetime, int, str],
        interface: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyse la distribution des protocoles dans le trafic.
        
        Args:
            start_time: Heure de début
            end_time: Heure de fin
            interface: Interface spécifique (optionnel)
            
        Returns:
            Distribution des protocoles
        """
        try:
            validated_params = self._validate_time_range(start_time, end_time)
            
            query_params = {
                'start_time': validated_params['start_time'],
                'end_time': validated_params['end_time']
            }
            
            if interface:
                validated_interface = self.validators.validate({'interface': interface})
                query_params['interface'] = validated_interface['interface']
            
            response = self.get("analytics/protocols", params=query_params)
            
            if response.get("success", True) and "data" in response:
                # Enrichir avec les noms de protocoles
                return self._enrich_protocol_data(response)
            
            return response
            
        except ValidationException as e:
            logger.warning(f"Paramètres distribution protocoles invalides: {e}")
            return {"success": False, "error": f"Paramètres invalides: {e.message}"}
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des protocoles: {e}")
            return {"success": False, "error": str(e)}
    
    def detect_anomalies(
        self,
        start_time: Union[datetime, int, str],
        end_time: Union[datetime, int, str],
        threshold_multiplier: float = 2.0,
        min_flow_count: int = 100
    ) -> Dict[str, Any]:
        """
        Détecte les anomalies dans le trafic réseau.
        
        Args:
            start_time: Heure de début
            end_time: Heure de fin
            threshold_multiplier: Multiplicateur de seuil pour la détection
            min_flow_count: Nombre minimum de flux pour considérer une anomalie
            
        Returns:
            Anomalies détectées
        """
        try:
            validated_params = self._validate_time_range(start_time, end_time)
            
            query_params = {
                'start_time': validated_params['start_time'],
                'end_time': validated_params['end_time'],
                'threshold_multiplier': max(1.0, min(threshold_multiplier, 10.0)),
                'min_flow_count': max(1, min(min_flow_count, 10000))
            }
            
            response = self.get("analytics/anomalies", params=query_params)
            
            if response.get("success", True) and "anomalies" in response:
                # Enrichir les anomalies avec du contexte
                return self._enrich_anomaly_data(response)
            
            return response
            
        except ValidationException as e:
            logger.warning(f"Paramètres détection anomalies invalides: {e}")
            return {"success": False, "error": f"Paramètres invalides: {e.message}"}
        except Exception as e:
            logger.error(f"Erreur lors de la détection d'anomalies: {e}")
            return {"success": False, "error": str(e)}
    
    def get_traffic_matrix(
        self,
        start_time: Union[datetime, int, str],
        end_time: Union[datetime, int, str],
        subnet_mask: int = 24
    ) -> Dict[str, Any]:
        """
        Génère une matrice de trafic entre sous-réseaux.
        
        Args:
            start_time: Heure de début
            end_time: Heure de fin
            subnet_mask: Masque de sous-réseau pour l'agrégation
            
        Returns:
            Matrice de trafic
        """
        try:
            validated_params = self._validate_time_range(start_time, end_time)
            
            # Valider le masque de sous-réseau
            if not 8 <= subnet_mask <= 30:
                raise ValidationException("Le masque de sous-réseau doit être entre 8 et 30")
            
            query_params = {
                'start_time': validated_params['start_time'],
                'end_time': validated_params['end_time'],
                'subnet_mask': subnet_mask
            }
            
            return self.get("analytics/traffic_matrix", params=query_params)
            
        except ValidationException as e:
            logger.warning(f"Paramètres matrice de trafic invalides: {e}")
            return {"success": False, "error": f"Paramètres invalides: {e.message}"}
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la matrice: {e}")
            return {"success": False, "error": str(e)}
    
    def _validate_query_params(self, **params) -> Dict[str, Any]:
        """Valide les paramètres de requête NetFlow."""
        validated = {}
        
        # Validation temporelle obligatoire
        time_params = self._validate_time_range(
            params.get('start_time'), 
            params.get('end_time')
        )
        validated.update(time_params)
        
        # Validation des paramètres optionnels
        optional_params = {}
        for field in ['src_ip', 'dst_ip', 'src_port', 'dst_port', 'protocol', 'interface']:
            if params.get(field) is not None:
                optional_params[field] = params[field]
        
        if optional_params:
            validated_optional = self.validators.validate(optional_params)
            validated.update(validated_optional)
        
        # Validation spéciale pour le protocole
        if 'protocol' in validated:
            validated['protocol'] = self._normalize_protocol(validated['protocol'])
        
        return validated
    
    def _validate_time_range(self, start_time, end_time) -> Dict[str, Any]:
        """Valide et normalise une plage temporelle."""
        validator = TimestampValidator()
        
        validated_start = validator.validate(start_time, 'start_time')
        validated_end = validator.validate(end_time, 'end_time')
        
        # Vérifier que start_time < end_time
        if isinstance(validated_start, str) and isinstance(validated_end, str):
            # Convertir en timestamps pour comparaison
            try:
                start_ts = datetime.fromisoformat(validated_start.replace('Z', '+00:00')).timestamp()
                end_ts = datetime.fromisoformat(validated_end.replace('Z', '+00:00')).timestamp()
            except:
                start_ts = float(validated_start)
                end_ts = float(validated_end)
        else:
            start_ts = float(validated_start)
            end_ts = float(validated_end)
        
        if start_ts >= end_ts:
            raise ValidationException("L'heure de début doit être antérieure à l'heure de fin")
        
        # Limiter la plage temporelle pour éviter les requêtes trop lourdes
        max_range = 7 * 24 * 3600  # 7 jours
        if end_ts - start_ts > max_range:
            raise ValidationException("La plage temporelle ne peut pas dépasser 7 jours")
        
        return {
            'start_time': validated_start,
            'end_time': validated_end
        }
    
    def _normalize_protocol(self, protocol) -> Union[str, int]:
        """Normalise un nom ou numéro de protocole."""
        if isinstance(protocol, int):
            if protocol in self.SUPPORTED_PROTOCOLS:
                return protocol
            raise ValidationException(f"Numéro de protocole non supporté: {protocol}")
        
        # Convertir nom en numéro
        protocol_upper = str(protocol).upper()
        for num, name in self.SUPPORTED_PROTOCOLS.items():
            if name == protocol_upper:
                return num
        
        # Essayer de convertir en entier
        try:
            protocol_num = int(protocol)
            if protocol_num in self.SUPPORTED_PROTOCOLS:
                return protocol_num
        except ValueError:
            pass
        
        raise ValidationException(f"Protocole non reconnu: {protocol}")
    
    def _enrich_flow_data(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Enrichit les données de flux avec des informations supplémentaires."""
        if "flows" not in response:
            return response
        
        enriched_flows = []
        for flow in response["flows"]:
            enriched_flow = flow.copy()
            
            # Ajouter le nom du protocole si on a le numéro
            if "protocol" in flow and isinstance(flow["protocol"], int):
                enriched_flow["protocol_name"] = self.SUPPORTED_PROTOCOLS.get(
                    flow["protocol"], f"Unknown({flow['protocol']})"
                )
            
            # Calculer la durée du flux si on a start et end
            if "first_switched" in flow and "last_switched" in flow:
                try:
                    duration = flow["last_switched"] - flow["first_switched"]
                    enriched_flow["duration_seconds"] = duration
                except:
                    pass
            
            # Calculer le débit si on a bytes et duration
            if "bytes" in flow and "duration_seconds" in enriched_flow and enriched_flow["duration_seconds"] > 0:
                enriched_flow["bitrate_bps"] = (flow["bytes"] * 8) / enriched_flow["duration_seconds"]
            
            enriched_flows.append(enriched_flow)
        
        response["flows"] = enriched_flows
        return response
    
    def _enrich_top_talkers(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Enrichit les données des top talkers."""
        if "data" not in response:
            return response
        
        enriched_data = []
        for talker in response["data"]:
            enriched_talker = talker.copy()
            
            # Ajouter des informations sur l'adresse IP
            if "ip_address" in talker:
                try:
                    ip = ipaddress.ip_address(talker["ip_address"])
                    enriched_talker["ip_type"] = "IPv4" if ip.version == 4 else "IPv6"
                    enriched_talker["is_private"] = ip.is_private
                    enriched_talker["is_multicast"] = ip.is_multicast
                except:
                    pass
            
            enriched_data.append(enriched_talker)
        
        response["data"] = enriched_data
        return response
    
    def _enrich_protocol_data(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Enrichit les données de distribution des protocoles."""
        if "data" not in response:
            return response
        
        enriched_data = []
        for protocol_stat in response["data"]:
            enriched_stat = protocol_stat.copy()
            
            # Ajouter le nom du protocole
            if "protocol_number" in protocol_stat:
                protocol_num = protocol_stat["protocol_number"]
                enriched_stat["protocol_name"] = self.SUPPORTED_PROTOCOLS.get(
                    protocol_num, f"Unknown({protocol_num})"
                )
            
            enriched_data.append(enriched_stat)
        
        response["data"] = enriched_data
        return response
    
    def _enrich_anomaly_data(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Enrichit les données d'anomalies avec du contexte."""
        if "anomalies" not in response:
            return response
        
        enriched_anomalies = []
        for anomaly in response["anomalies"]:
            enriched_anomaly = anomaly.copy()
            
            # Catégoriser le type d'anomalie
            if "flow_count" in anomaly and "baseline_flow_count" in anomaly:
                ratio = anomaly["flow_count"] / max(anomaly["baseline_flow_count"], 1)
                if ratio > 5:
                    enriched_anomaly["severity"] = "high"
                elif ratio > 2:
                    enriched_anomaly["severity"] = "medium"
                else:
                    enriched_anomaly["severity"] = "low"
            
            # Ajouter des suggestions d'investigation
            anomaly_type = anomaly.get("type", "unknown")
            if anomaly_type == "volume_spike":
                enriched_anomaly["investigation_hints"] = [
                    "Vérifier les applications gourmandes en bande passante",
                    "Analyser les top talkers sur cette période",
                    "Vérifier les alertes de sécurité corrélées"
                ]
            elif anomaly_type == "new_destination":
                enriched_anomaly["investigation_hints"] = [
                    "Vérifier la légitimité de la nouvelle destination",
                    "Analyser les protocoles utilisés",
                    "Contrôler les politiques de sécurité"
                ]
            
            enriched_anomalies.append(enriched_anomaly)
        
        response["anomalies"] = enriched_anomalies
        return response 