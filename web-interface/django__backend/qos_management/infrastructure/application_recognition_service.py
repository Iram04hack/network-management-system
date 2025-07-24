"""
Service de reconnaissance d'applications pour la classification de trafic QoS.

Ce module implémente la reconnaissance d'applications basée sur l'analyse de paquets,
les signatures d'applications et les modèles comportementaux.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

from ..domain.interfaces import TrafficClassificationService

logger = logging.getLogger(__name__)


@dataclass
class ApplicationSignature:
    """
    Signature d'application pour l'identification.
    """
    app_name: str
    category: str
    protocols: List[str]
    ports: List[int]
    payload_patterns: List[str]
    headers: Dict[str, str]
    behavioral_patterns: Dict[str, Any]
    confidence_threshold: float = 0.7


@dataclass
class TrafficFlow:
    """
    Représentation d'un flux de trafic pour l'analyse.
    """
    flow_id: str
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    protocol: str
    start_time: datetime
    last_seen: datetime
    packet_count: int = 0
    byte_count: int = 0
    payload_samples: List[bytes] = None
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.payload_samples is None:
            self.payload_samples = []
        if self.headers is None:
            self.headers = {}


class ApplicationRecognitionService(TrafficClassificationService):
    """
    Service de reconnaissance d'applications avec DPI et analyse comportementale.
    """
    
    def __init__(self):
        self.application_signatures = self._load_application_signatures()
        self.active_flows = {}
        self.behavioral_models = self._initialize_behavioral_models()
        self.classification_cache = {}
    
    def classify_traffic(self, traffic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifie le trafic réseau en identifiant l'application.
        
        Args:
            traffic_data: Données de trafic à classifier
            
        Returns:
            Classification du trafic avec application identifiée
        """
        try:
            # Créer ou mettre à jour le flux
            flow = self._get_or_create_flow(traffic_data)
            
            # Analyser le flux avec différentes méthodes
            classification_results = {
                'port_based': self._classify_by_port(flow),
                'payload_based': self._classify_by_payload(flow),
                'behavioral_based': self._classify_by_behavior(flow),
                'header_based': self._classify_by_headers(flow)
            }
            
            # Fusionner les résultats et calculer la confiance
            final_classification = self._merge_classifications(classification_results)
            
            # Mettre en cache le résultat
            cache_key = self._generate_cache_key(flow)
            self.classification_cache[cache_key] = final_classification
            
            return final_classification
            
        except Exception as e:
            logger.error(f"Erreur lors de la classification de trafic: {str(e)}")
            return {
                'application': 'unknown',
                'category': 'unclassified',
                'confidence': 0.0,
                'method': 'error',
                'details': str(e)
            }
    
    def suggest_qos_policy(self, traffic_class: str) -> Dict[str, Any]:
        """
        Suggère une politique QoS adaptée à une classe de trafic.
        
        Args:
            traffic_class: Classe de trafic identifiée
            
        Returns:
            Politique QoS suggérée
        """
        qos_templates = self._get_qos_templates()
        
        # Normaliser la classe de trafic
        normalized_class = traffic_class.lower().replace(' ', '_')
        
        # Chercher un template correspondant
        for template_name, template in qos_templates.items():
            if any(keyword in normalized_class for keyword in template['keywords']):
                return self._customize_qos_template(template, traffic_class)
        
        # Template par défaut
        return qos_templates.get('default', {
            'name': f'Policy_{traffic_class}',
            'description': f'Politique automatique pour {traffic_class}',
            'bandwidth_allocation': 10,
            'priority': 3,
            'latency_target': 100,
            'jitter_tolerance': 50
        })
    
    def get_traffic_classes(self) -> List[str]:
        """
        Récupère la liste des classes de trafic disponibles.
        
        Returns:
            Liste des classes de trafic
        """
        return [
            'voice', 'video_conferencing', 'video_streaming', 'gaming',
            'web_browsing', 'email', 'file_transfer', 'database',
            'backup', 'monitoring', 'management', 'unknown'
        ]
    
    def _load_application_signatures(self) -> Dict[str, ApplicationSignature]:
        """
        Charge les signatures d'applications connues.
        
        Returns:
            Dictionnaire des signatures d'applications
        """
        signatures = {}
        
        # Signatures VoIP
        signatures['sip'] = ApplicationSignature(
            app_name='SIP',
            category='voice',
            protocols=['udp', 'tcp'],
            ports=[5060, 5061],
            payload_patterns=[
                r'INVITE sip:',
                r'SIP/2\.0',
                r'Via: SIP/2\.0',
                r'Content-Type: application/sdp'
            ],
            headers={'User-Agent': r'.*SIP.*'},
            behavioral_patterns={
                'packet_size_range': (100, 1500),
                'flow_duration': 'variable',
                'bidirectional': True
            }
        )
        
        signatures['rtp'] = ApplicationSignature(
            app_name='RTP',
            category='voice',
            protocols=['udp'],
            ports=list(range(16384, 32768)),  # Plage RTP dynamique
            payload_patterns=[
                r'\x80[\x00-\xFF]{11}',  # Header RTP basique
            ],
            headers={},
            behavioral_patterns={
                'packet_size_range': (160, 200),
                'packet_interval': 20,  # ms
                'constant_bitrate': True
            }
        )
        
        # Signatures vidéo
        signatures['rtmp'] = ApplicationSignature(
            app_name='RTMP',
            category='video_streaming',
            protocols=['tcp'],
            ports=[1935],
            payload_patterns=[
                r'\x03\x00\x00\x00',  # RTMP handshake
                r'connect\x00',
                r'play\x00'
            ],
            headers={},
            behavioral_patterns={
                'variable_bitrate': True,
                'large_packets': True,
                'sustained_connection': True
            }
        )
        
        signatures['http_video'] = ApplicationSignature(
            app_name='HTTP Video',
            category='video_streaming',
            protocols=['tcp'],
            ports=[80, 443, 8080],
            payload_patterns=[
                r'GET .+\.m3u8',
                r'GET .+\.ts',
                r'Content-Type: video/',
                r'Range: bytes='
            ],
            headers={
                'Content-Type': r'video/.*',
                'User-Agent': r'.*(VLC|YouTube|Netflix).*'
            },
            behavioral_patterns={
                'chunked_download': True,
                'high_bandwidth': True
            }
        )
        
        # Signatures gaming
        signatures['steam'] = ApplicationSignature(
            app_name='Steam',
            category='gaming',
            protocols=['tcp', 'udp'],
            ports=[27015, 27036],
            payload_patterns=[
                r'Steam.*',
                r'\xFF\xFF\xFF\xFF'  # Source engine queries
            ],
            headers={},
            behavioral_patterns={
                'low_latency_required': True,
                'irregular_patterns': True
            }
        )
        
        # Signatures web
        signatures['http'] = ApplicationSignature(
            app_name='HTTP',
            category='web_browsing',
            protocols=['tcp'],
            ports=[80],
            payload_patterns=[
                r'GET .+ HTTP/1\.[01]',
                r'POST .+ HTTP/1\.[01]',
                r'HTTP/1\.[01] \d{3}',
                r'Content-Type: text/html'
            ],
            headers={
                'Host': r'.*',
                'User-Agent': r'.*(Mozilla|Chrome|Safari).*'
            },
            behavioral_patterns={
                'request_response': True,
                'mixed_content': True
            }
        )
        
        signatures['https'] = ApplicationSignature(
            app_name='HTTPS',
            category='web_browsing',
            protocols=['tcp'],
            ports=[443],
            payload_patterns=[
                r'\x16\x03[\x01-\x03]',  # TLS handshake
                r'\x17\x03[\x01-\x03]'   # TLS application data
            ],
            headers={},
            behavioral_patterns={
                'encrypted': True,
                'certificate_exchange': True
            }
        )
        
        # Signatures email
        signatures['smtp'] = ApplicationSignature(
            app_name='SMTP',
            category='email',
            protocols=['tcp'],
            ports=[25, 587],
            payload_patterns=[
                r'220 .+ SMTP',
                r'EHLO ',
                r'MAIL FROM:',
                r'RCPT TO:'
            ],
            headers={},
            behavioral_patterns={
                'command_response': True,
                'text_based': True
            }
        )
        
        return signatures
    
    def _get_or_create_flow(self, traffic_data: Dict[str, Any]) -> TrafficFlow:
        """
        Récupère ou crée un flux de trafic.
        
        Args:
            traffic_data: Données de trafic
            
        Returns:
            Objet TrafficFlow
        """
        # Générer un ID de flux unique
        flow_id = self._generate_flow_id(traffic_data)
        
        if flow_id in self.active_flows:
            # Mettre à jour le flux existant
            flow = self.active_flows[flow_id]
            flow.last_seen = datetime.now()
            flow.packet_count += 1
            flow.byte_count += traffic_data.get('packet_size', 0)
            
            # Ajouter l'échantillon de payload si disponible
            payload = traffic_data.get('payload')
            if payload and len(flow.payload_samples) < 10:  # Limiter les échantillons
                flow.payload_samples.append(payload[:200])  # Premiers 200 bytes
                
        else:
            # Créer un nouveau flux
            now = datetime.now()
            flow = TrafficFlow(
                flow_id=flow_id,
                source_ip=traffic_data.get('source_ip', ''),
                destination_ip=traffic_data.get('destination_ip', ''),
                source_port=traffic_data.get('source_port', 0),
                destination_port=traffic_data.get('destination_port', 0),
                protocol=traffic_data.get('protocol', ''),
                start_time=now,
                last_seen=now,
                packet_count=1,
                byte_count=traffic_data.get('packet_size', 0)
            )
            
            # Ajouter le payload initial
            payload = traffic_data.get('payload')
            if payload:
                flow.payload_samples.append(payload[:200])
            
            # Ajouter les headers
            headers = traffic_data.get('headers', {})
            if headers:
                flow.headers.update(headers)
            
            self.active_flows[flow_id] = flow
        
        return flow
    
    def _generate_flow_id(self, traffic_data: Dict[str, Any]) -> str:
        """
        Génère un ID unique pour un flux.
        
        Args:
            traffic_data: Données de trafic
            
        Returns:
            ID de flux unique
        """
        # Créer une clé basée sur les 5-tuples
        key_parts = [
            traffic_data.get('source_ip', ''),
            str(traffic_data.get('source_port', 0)),
            traffic_data.get('destination_ip', ''),
            str(traffic_data.get('destination_port', 0)),
            traffic_data.get('protocol', '')
        ]
        
        key_string = '_'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    def _classify_by_port(self, flow: TrafficFlow) -> Dict[str, Any]:
        """
        Classification basée sur les ports.
        
        Args:
            flow: Flux de trafic à analyser
            
        Returns:
            Résultat de classification
        """
        for app_name, signature in self.application_signatures.items():
            if (flow.destination_port in signature.ports or 
                flow.source_port in signature.ports):
                return {
                    'application': signature.app_name,
                    'category': signature.category,
                    'confidence': 0.6,  # Confiance modérée pour classification par port
                    'method': 'port_based'
                }
        
        return {
            'application': 'unknown',
            'category': 'unclassified', 
            'confidence': 0.0,
            'method': 'port_based'
        }
    
    def _classify_by_payload(self, flow: TrafficFlow) -> Dict[str, Any]:
        """
        Classification basée sur l'analyse du payload (DPI).
        
        Args:
            flow: Flux de trafic à analyser
            
        Returns:
            Résultat de classification
        """
        if not flow.payload_samples:
            return {
                'application': 'unknown',
                'category': 'unclassified',
                'confidence': 0.0,
                'method': 'payload_based'
            }
        
        best_match = None
        best_confidence = 0.0
        
        for app_name, signature in self.application_signatures.items():
            confidence = 0.0
            matches = 0
            
            # Analyser chaque échantillon de payload
            for payload_sample in flow.payload_samples:
                if isinstance(payload_sample, bytes):
                    payload_str = payload_sample.decode('utf-8', errors='ignore')
                else:
                    payload_str = str(payload_sample)
                
                # Vérifier les patterns de payload
                for pattern in signature.payload_patterns:
                    try:
                        if re.search(pattern, payload_str, re.IGNORECASE):
                            matches += 1
                    except re.error:
                        continue
            
            # Calculer la confiance basée sur le nombre de matches
            if matches > 0:
                confidence = min(0.9, matches / len(signature.payload_patterns))
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = signature
        
        if best_match and best_confidence >= best_match.confidence_threshold:
            return {
                'application': best_match.app_name,
                'category': best_match.category,
                'confidence': best_confidence,
                'method': 'payload_based'
            }
        
        return {
            'application': 'unknown',
            'category': 'unclassified',
            'confidence': 0.0,
            'method': 'payload_based'
        }
    
    def _classify_by_headers(self, flow: TrafficFlow) -> Dict[str, Any]:
        """
        Classification basée sur les headers HTTP/HTTPS.
        
        Args:
            flow: Flux de trafic à analyser
            
        Returns:
            Résultat de classification
        """
        if not flow.headers:
            return {
                'application': 'unknown',
                'category': 'unclassified',
                'confidence': 0.0,
                'method': 'header_based'
            }
        
        for app_name, signature in self.application_signatures.items():
            if not signature.headers:
                continue
            
            matches = 0
            total_headers = len(signature.headers)
            
            for header_name, header_pattern in signature.headers.items():
                flow_header_value = flow.headers.get(header_name, '')
                
                try:
                    if re.search(header_pattern, flow_header_value, re.IGNORECASE):
                        matches += 1
                except re.error:
                    continue
            
            confidence = matches / total_headers if total_headers > 0 else 0.0
            
            if confidence >= signature.confidence_threshold:
                return {
                    'application': signature.app_name,
                    'category': signature.category,
                    'confidence': confidence,
                    'method': 'header_based'
                }
        
        return {
            'application': 'unknown',
            'category': 'unclassified',
            'confidence': 0.0,
            'method': 'header_based'
        }
    
    def _classify_by_behavior(self, flow: TrafficFlow) -> Dict[str, Any]:
        """
        Classification basée sur l'analyse comportementale.
        
        Args:
            flow: Flux de trafic à analyser
            
        Returns:
            Résultat de classification
        """
        # Calculer les caractéristiques comportementales du flux
        flow_characteristics = self._calculate_flow_characteristics(flow)
        
        best_match = None
        best_confidence = 0.0
        
        for app_name, signature in self.application_signatures.items():
            if not signature.behavioral_patterns:
                continue
            
            confidence = self._match_behavioral_patterns(
                flow_characteristics, 
                signature.behavioral_patterns
            )
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = signature
        
        if best_match and best_confidence >= best_match.confidence_threshold:
            return {
                'application': best_match.app_name,
                'category': best_match.category,
                'confidence': best_confidence,
                'method': 'behavioral_based'
            }
        
        return {
            'application': 'unknown',
            'category': 'unclassified',
            'confidence': 0.0,
            'method': 'behavioral_based'
        }
    
    def _calculate_flow_characteristics(self, flow: TrafficFlow) -> Dict[str, Any]:
        """
        Calcule les caractéristiques comportementales d'un flux.
        
        Args:
            flow: Flux de trafic
            
        Returns:
            Caractéristiques comportementales
        """
        duration = (flow.last_seen - flow.start_time).total_seconds()
        
        characteristics = {
            'duration': duration,
            'packet_count': flow.packet_count,
            'byte_count': flow.byte_count,
            'average_packet_size': flow.byte_count / max(flow.packet_count, 1),
            'packets_per_second': flow.packet_count / max(duration, 1),
            'bytes_per_second': flow.byte_count / max(duration, 1),
            'bidirectional': self._is_bidirectional_flow(flow),
            'protocol': flow.protocol.lower()
        }
        
        return characteristics
    
    def _match_behavioral_patterns(
        self, 
        characteristics: Dict[str, Any], 
        patterns: Dict[str, Any]
    ) -> float:
        """
        Compare les caractéristiques avec les patterns comportementaux.
        
        Args:
            characteristics: Caractéristiques du flux
            patterns: Patterns attendus
            
        Returns:
            Score de confiance (0.0 à 1.0)
        """
        matches = 0
        total_patterns = len(patterns)
        
        for pattern_name, pattern_value in patterns.items():
            if pattern_name == 'packet_size_range' and isinstance(pattern_value, tuple):
                min_size, max_size = pattern_value
                avg_size = characteristics.get('average_packet_size', 0)
                if min_size <= avg_size <= max_size:
                    matches += 1
                    
            elif pattern_name == 'constant_bitrate' and pattern_value:
                # Vérifier si le débit est relativement constant (simplification)
                if characteristics.get('bytes_per_second', 0) > 0:
                    matches += 0.5  # Demi-point pour cette heuristique simple
                    
            elif pattern_name == 'bidirectional' and pattern_value:
                if characteristics.get('bidirectional', False):
                    matches += 1
                    
            elif pattern_name == 'low_latency_required' and pattern_value:
                # Heuristique: petits paquets fréquents = besoin de faible latence
                pps = characteristics.get('packets_per_second', 0)
                if pps > 10:  # Plus de 10 paquets/seconde
                    matches += 1
        
        return matches / max(total_patterns, 1)
    
    def _is_bidirectional_flow(self, flow: TrafficFlow) -> bool:
        """
        Détermine si un flux est bidirectionnel (simplification).
        
        Args:
            flow: Flux de trafic
            
        Returns:
            True si le flux semble bidirectionnel
        """
        # Heuristique simple: si le flux dure plus de 5 secondes et a plus de 10 paquets,
        # on assume qu'il y a eu des échanges bidirectionnels
        duration = (flow.last_seen - flow.start_time).total_seconds()
        return duration > 5 and flow.packet_count > 10
    
    def _merge_classifications(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fusionne les résultats de classification de différentes méthodes.
        
        Args:
            results: Résultats de classification par méthode
            
        Returns:
            Classification finale fusionnée
        """
        # Pondération des méthodes
        method_weights = {
            'payload_based': 0.4,
            'header_based': 0.3,
            'behavioral_based': 0.2,
            'port_based': 0.1
        }
        
        # Collecter les applications candidates avec leurs scores pondérés
        candidates = defaultdict(list)
        
        for method, result in results.items():
            if result['confidence'] > 0:
                app = result['application']
                weighted_confidence = result['confidence'] * method_weights.get(method, 0.1)
                candidates[app].append({
                    'confidence': weighted_confidence,
                    'method': method,
                    'category': result['category']
                })
        
        if not candidates:
            return {
                'application': 'unknown',
                'category': 'unclassified',
                'confidence': 0.0,
                'methods_used': list(results.keys()),
                'details': 'No classification matches found'
            }
        
        # Calculer le score final pour chaque application candidate
        final_scores = {}
        for app, method_results in candidates.items():
            total_confidence = sum(r['confidence'] for r in method_results)
            final_scores[app] = {
                'confidence': total_confidence,
                'methods': [r['method'] for r in method_results],
                'category': method_results[0]['category']  # Prendre la première catégorie
            }
        
        # Sélectionner la meilleure classification
        best_app = max(final_scores.keys(), key=lambda x: final_scores[x]['confidence'])
        best_result = final_scores[best_app]
        
        return {
            'application': best_app,
            'category': best_result['category'],
            'confidence': min(1.0, best_result['confidence']),
            'methods_used': best_result['methods'],
            'all_candidates': final_scores
        }
    
    def _generate_cache_key(self, flow: TrafficFlow) -> str:
        """
        Génère une clé de cache pour un flux.
        
        Args:
            flow: Flux de trafic
            
        Returns:
            Clé de cache
        """
        return f"{flow.flow_id}_{flow.packet_count}"
    
    def _get_qos_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Retourne les templates de politiques QoS pour différentes applications.
        
        Returns:
            Templates de politiques QoS
        """
        return {
            'voice': {
                'keywords': ['sip', 'rtp', 'voice', 'voip'],
                'name': 'Voice_Policy',
                'description': 'Politique optimisée pour la voix',
                'bandwidth_allocation': 15,
                'priority': 7,
                'latency_target': 20,  # ms
                'jitter_tolerance': 10,
                'packet_loss_tolerance': 0.1
            },
            'video_conferencing': {
                'keywords': ['video', 'conference', 'webrtc', 'zoom', 'teams'],
                'name': 'VideoConf_Policy',
                'description': 'Politique pour visioconférence',
                'bandwidth_allocation': 25,
                'priority': 6,
                'latency_target': 150,
                'jitter_tolerance': 50,
                'packet_loss_tolerance': 0.5
            },
            'video_streaming': {
                'keywords': ['streaming', 'youtube', 'netflix', 'rtmp'],
                'name': 'VideoStream_Policy',
                'description': 'Politique pour streaming vidéo',
                'bandwidth_allocation': 40,
                'priority': 4,
                'latency_target': 500,
                'jitter_tolerance': 100,
                'packet_loss_tolerance': 1.0
            },
            'gaming': {
                'keywords': ['game', 'gaming', 'steam'],
                'name': 'Gaming_Policy',
                'description': 'Politique pour jeux en ligne',
                'bandwidth_allocation': 20,
                'priority': 5,
                'latency_target': 50,
                'jitter_tolerance': 20,
                'packet_loss_tolerance': 0.3
            },
            'web_browsing': {
                'keywords': ['http', 'https', 'web', 'browser'],
                'name': 'Web_Policy', 
                'description': 'Politique pour navigation web',
                'bandwidth_allocation': 30,
                'priority': 3,
                'latency_target': 200,
                'jitter_tolerance': 100,
                'packet_loss_tolerance': 2.0
            },
            'default': {
                'keywords': [],
                'name': 'Default_Policy',
                'description': 'Politique par défaut',
                'bandwidth_allocation': 10,
                'priority': 2,
                'latency_target': 1000,
                'jitter_tolerance': 500,
                'packet_loss_tolerance': 5.0
            }
        }
    
    def _customize_qos_template(self, template: Dict[str, Any], traffic_class: str) -> Dict[str, Any]:
        """
        Personnalise un template QoS pour une classe de trafic spécifique.
        
        Args:
            template: Template de base
            traffic_class: Classe de trafic
            
        Returns:
            Template personnalisé
        """
        customized = template.copy()
        customized['name'] = f"{template['name']}_{traffic_class}"
        customized['description'] = f"{template['description']} pour {traffic_class}"
        
        return customized
    
    def _initialize_behavioral_models(self) -> Dict[str, Any]:
        """
        Initialise les modèles comportementaux pour l'analyse de trafic.
        
        Returns:
            Modèles comportementaux
        """
        return {
            'voice_model': {
                'packet_size_distribution': {'mean': 180, 'std': 20},
                'packet_interval': {'mean': 20, 'std': 5},  # ms
                'flow_duration': {'min': 30, 'max': 3600}  # seconds
            },
            'video_model': {
                'packet_size_distribution': {'mean': 1200, 'std': 400},
                'variable_bitrate': True,
                'burst_patterns': True
            },
            'web_model': {
                'request_response_pattern': True,
                'varying_content_sizes': True,
                'session_based': True
            }
        }
    
    def cleanup_old_flows(self, max_age_minutes: int = 30):
        """
        Nettoie les anciens flux pour libérer la mémoire.
        
        Args:
            max_age_minutes: Âge maximum des flux en minutes
        """
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        old_flows = [
            flow_id for flow_id, flow in self.active_flows.items()
            if flow.last_seen < cutoff_time
        ]
        
        for flow_id in old_flows:
            del self.active_flows[flow_id]
        
        logger.info(f"Nettoyage: {len(old_flows)} anciens flux supprimés") 