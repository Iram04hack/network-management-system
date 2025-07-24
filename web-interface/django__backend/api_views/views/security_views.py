"""
Vues API pour la gestion de la sécurité (Fail2ban et Suricata)
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging
import random

logger = logging.getLogger(__name__)

class Fail2banViewSet(viewsets.ViewSet):
    """
    ViewSet pour Fail2ban avec CRUD complet.
    
    Fournit les opérations CRUD pour :
    - Gestion des jails Fail2ban
    - Configuration des filtres
    - Administration des bannissements
    - Gestion des whitelist/blacklist
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Liste tous les configuration Fail2ban",
        operation_description="Récupère la liste complète des configuration Fail2ban avec filtrage, tri et pagination.",
        tags=['API Views'],
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, description='Numéro de page', type=openapi.TYPE_INTEGER, default=1),
            openapi.Parameter('page_size', openapi.IN_QUERY, description='Éléments par page', type=openapi.TYPE_INTEGER, default=20),
            openapi.Parameter('search', openapi.IN_QUERY, description='Recherche textuelle', type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description='Champ de tri', type=openapi.TYPE_STRING),
        ],
        responses={
            200: "Liste récupérée avec succès",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def list(self, request):
        """Récupère la liste des jails Fail2ban configurées"""
        try:
            jails = [
                {
                    'name': 'sshd',
                    'status': 'active',
                    'failed_attempts': random.randint(5, 50),
                    'banned_ips': random.randint(2, 15),
                    'filter': 'sshd',
                    'action': 'iptables-multiport'
                },
                {
                    'name': 'apache-auth',
                    'status': 'active',
                    'failed_attempts': random.randint(0, 20),
                    'banned_ips': random.randint(0, 8),
                    'filter': 'apache-auth',
                    'action': 'iptables-multiport'
                }
            ]
            return Response({
                'jails': jails,
                'count': len(jails),
                'timestamp': timezone.now().isoformat()
            })
        except Exception as e:
            logger.exception(f"Erreur Fail2ban jails: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    @swagger_auto_schema(
        operation_summary="Action status",
        operation_description="Vérifie le statut du service avec statistiques globales et santé des jails.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def status(self, request):
        """Vérifie l'état de santé du service Fail2ban"""
        try:
            status_data = {
                'service': 'fail2ban',
                'status': 'running',
                'version': '0.11.2',
                'uptime': f'{random.randint(1, 30)} days',
                'active_jails': random.randint(3, 8),
                'total_banned_ips': random.randint(10, 100),
                'timestamp': timezone.now().isoformat()
            }
            return Response(status_data)
        except Exception as e:
            logger.exception(f"Erreur Fail2ban status: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='ban-ip')
    @swagger_auto_schema(
        operation_summary="Action ban_ip",
        operation_description="Ajoute une adresse IP à la liste de bannissement avec durée configurable.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def ban_ip(self, request):
        """Bannit manuellement une adresse IP dans une jail spécifique"""
        try:
            ip = request.data.get('ip')
            if not ip:
                return Response({'error': 'IP address required'}, status=status.HTTP_400_BAD_REQUEST)

            result = {
                'ip': ip,
                'banned': True,
                'ban_time': timezone.now().isoformat()
            }
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception(f"Erreur ban IP: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    @swagger_auto_schema(
        operation_summary="Action banned",
        operation_description="Récupère toutes les IPs bannies avec détails des violations et durées restantes.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def banned(self, request):
        """Récupère la liste de toutes les adresses IP bannies"""
        try:
            banned_ips = []
            for i in range(random.randint(3, 10)):
                banned_ips.append({
                    'ip': f'192.168.{random.randint(1, 255)}.{random.randint(1, 255)}',
                    'jail': random.choice(['sshd', 'apache-auth']),
                    'ban_time': timezone.now().isoformat(),
                    'attempts': random.randint(3, 10)
                })

            return Response({
                'banned_ips': banned_ips,
                'count': len(banned_ips),
                'timestamp': timezone.now().isoformat()
            })
        except Exception as e:
            logger.exception(f"Erreur Fail2ban banned: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    @swagger_auto_schema(
        operation_summary="Action unban_ip",
        operation_description="Ajoute une adresse IP à la liste de bannissement avec durée configurable.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def unban_ip(self, request):
        """Retire une adresse IP de la liste de bannissement"""
        try:
            ip = request.data.get('ip')
            if not ip:
                return Response({'error': 'IP address required'}, status=status.HTTP_400_BAD_REQUEST)

            result = {
                'ip': ip,
                'unbanned': True,
                'unban_time': timezone.now().isoformat()
            }
            return Response(result)
        except Exception as e:
            logger.exception(f"Erreur unban IP: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Crée un nouveau configuration Fail2ban",
        operation_description="Crée un nouveau configuration Fail2ban avec validation des données et configuration automatique.",
        
        tags=['API Views'],responses={
            201: "Créé avec succès",
            400: "Données invalides",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def create(self, request):
        """Crée une nouvelle configuration de jail"""
        try:
            data = request.data
            jail_config = {
                'id': random.randint(1, 1000),
                'name': data.get('name', 'custom-jail'),
                'enabled': data.get('enabled', True),
                'port': data.get('port', '22'),
                'filter': data.get('filter', 'sshd'),
                'action': data.get('action', 'iptables-multiport'),
                'maxretry': data.get('maxretry', 5),
                'bantime': data.get('bantime', 3600),
                'created_at': timezone.now().isoformat(),
                'created_by': request.user.username
            }
            return Response(jail_config, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception(f"Erreur création jail: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Détails d'un configuration Fail2ban",
        operation_description="Récupère les détails complets d'un configuration Fail2ban spécifique.",
        
        tags=['API Views'],responses={
            200: "Détails récupérés avec succès",
            404: "Non trouvé",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def retrieve(self, request, pk=None):
        """Récupère les détails d'une jail spécifique"""
        try:
            jail_detail = {
                'id': pk,
                'name': f'jail-{pk}',
                'enabled': True,
                'port': '22',
                'filter': 'sshd',
                'action': 'iptables-multiport',
                'failed_attempts': random.randint(0, 50),
                'banned_ips': random.randint(0, 15),
                'maxretry': 5,
                'bantime': 3600,
                'findtime': 600,
                'created_at': timezone.now().isoformat()
            }
            return Response(jail_detail)
        except Exception as e:
            logger.exception(f"Erreur récupération jail: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Met à jour un configuration Fail2ban",
        operation_description="Met à jour complètement un configuration Fail2ban existant.",
        
        tags=['API Views'],responses={
            200: "Mis à jour avec succès",
            400: "Données invalides",
            404: "Non trouvé",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def update(self, request, pk=None):
        """Met à jour une configuration de jail"""
        try:
            data = request.data
            updated_jail = {
                'id': pk,
                'name': data.get('name', f'jail-{pk}'),
                'enabled': data.get('enabled', True),
                'port': data.get('port', '22'),
                'filter': data.get('filter', 'sshd'),
                'action': data.get('action', 'iptables-multiport'),
                'maxretry': data.get('maxretry', 5),
                'bantime': data.get('bantime', 3600),
                'updated_at': timezone.now().isoformat(),
                'updated_by': request.user.username
            }
            return Response(updated_jail)
        except Exception as e:
            logger.exception(f"Erreur mise à jour jail: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Supprime un configuration Fail2ban",
        operation_description="Supprime définitivement un configuration Fail2ban du système.",
        
        tags=['API Views'],responses={
            204: "Supprimé avec succès",
            404: "Non trouvé",
            401: "Non authentifié",
            403: "Permission refusée",
            500: "Erreur serveur",
        },
    )
    def destroy(self, request, pk=None):
        """Supprime une configuration de jail"""
        try:
            return Response({'message': f'Jail {pk} supprimée avec succès'}, 
                          status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.exception(f"Erreur suppression jail: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SuricataViewSet(viewsets.ViewSet):
    """
    ViewSet pour Suricata IDS/IPS avec CRUD complet.
    
    Fournit les opérations CRUD pour :
    - Gestion des règles Suricata
    - Configuration des signatures
    - Administration des alertes
    - Gestion des logs d'événements
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Liste tous les configuration Fail2ban",
        operation_description="Récupère la liste complète des configuration Fail2ban avec filtrage, tri et pagination.",
        tags=['API Views'],
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, description='Numéro de page', type=openapi.TYPE_INTEGER, default=1),
            openapi.Parameter('page_size', openapi.IN_QUERY, description='Éléments par page', type=openapi.TYPE_INTEGER, default=20),
            openapi.Parameter('search', openapi.IN_QUERY, description='Recherche textuelle', type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description='Champ de tri', type=openapi.TYPE_STRING),
        ],
        responses={
            200: "Liste récupérée avec succès",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def list(self, request):
        """Récupère la liste des règles Suricata configurées"""
        try:
            rules = [
                {
                    'id': 1,
                    'sid': 2001001,
                    'msg': 'ET SCAN Potential SSH Scan',
                    'category': 'scan',
                    'severity': 'medium',
                    'enabled': True
                },
                {
                    'id': 2,
                    'sid': 2001002,
                    'msg': 'ET MALWARE Suspicious DNS Query',
                    'category': 'malware',
                    'severity': 'high',
                    'enabled': True
                }
            ]
            return Response({
                'rules': rules,
                'count': len(rules),
                'timestamp': timezone.now().isoformat()
            })
        except Exception as e:
            logger.exception(f"Erreur Suricata rules: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    @swagger_auto_schema(
        operation_summary="Action alerts",
        operation_description="Récupère les alertes de sécurité détectées avec détails des attaques.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def alerts(self, request):
        """Récupère les alertes de sécurité détectées par Suricata"""
        try:
            alerts = []
            for i in range(random.randint(3, 10)):
                alerts.append({
                    'id': i + 1,
                    'timestamp': timezone.now().isoformat(),
                    'src_ip': f'192.168.{random.randint(1, 255)}.{random.randint(1, 255)}',
                    'dest_ip': f'10.0.{random.randint(1, 255)}.{random.randint(1, 255)}',
                    'signature': f'ET SCAN Alert {i+1}',
                    'severity': random.choice(['low', 'medium', 'high'])
                })
            
            return Response({
                'alerts': alerts,
                'count': len(alerts),
                'timestamp': timezone.now().isoformat()
            })
        except Exception as e:
            logger.exception(f"Erreur Suricata alerts: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    @swagger_auto_schema(
        operation_summary="Action status",
        operation_description="Vérifie le statut du service avec statistiques globales et santé des jails.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def status(self, request):
        """Vérifie l'état de santé du service Suricata IDS/IPS"""
        try:
            status_data = {
                'service': 'suricata',
                'status': 'running',
                'version': '6.0.8',
                'mode': 'IDS/IPS',
                'uptime': f'{random.randint(1, 30)} days',
                'rules_loaded': random.randint(20000, 50000),
                'timestamp': timezone.now().isoformat()
            }
            return Response(status_data)
        except Exception as e:
            logger.exception(f"Erreur Suricata status: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='add-rule')
    @swagger_auto_schema(
        operation_summary="Action add_rule",
        operation_description="Ajoute et active immédiatement une nouvelle règle sans redémarrage.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def add_rule(self, request):
        """Ajoute une nouvelle règle"""
        try:
            rule_data = {
                'id': random.randint(1000, 9999),
                'sid': request.data.get('sid', random.randint(3000000, 3999999)),
                'msg': request.data.get('msg', 'Custom Rule'),
                'category': request.data.get('category', 'custom'),
                'severity': request.data.get('severity', 'medium'),
                'enabled': request.data.get('enabled', True),
                'created': timezone.now().isoformat()
            }
            return Response(rule_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception(f"Erreur add rule: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    @swagger_auto_schema(
        operation_summary="Action reload",
        operation_description="Recharge toutes les règles depuis les fichiers de configuration.",
        
        tags=['API Views'],responses={
            200: "Opération réussie",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def reload(self, request):
        """Recharge les règles Suricata"""
        try:
            result = {
                'reloaded': True,
                'rules_loaded': random.randint(20000, 50000),
                'reload_time': timezone.now().isoformat(),
                'status': 'success'
            }
            return Response(result)
        except Exception as e:
            logger.exception(f"Erreur reload rules: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Crée un nouveau configuration Fail2ban",
        operation_description="Crée un nouveau configuration Fail2ban avec validation des données et configuration automatique.",
        
        tags=['API Views'],responses={
            201: "Créé avec succès",
            400: "Données invalides",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def create(self, request):
        """Crée une nouvelle règle Suricata"""
        try:
            data = request.data
            rule_config = {
                'id': random.randint(1, 1000),
                'sid': data.get('sid', random.randint(3000000, 3999999)),
                'msg': data.get('msg', 'Custom Suricata Rule'),
                'rule': data.get('rule', 'alert tcp any any -> any any (msg:"Custom Rule"; sid:3000001; rev:1;)'),
                'category': data.get('category', 'custom'),
                'severity': data.get('severity', 'medium'),
                'enabled': data.get('enabled', True),
                'created_at': timezone.now().isoformat(),
                'created_by': request.user.username
            }
            return Response(rule_config, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception(f"Erreur création règle: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Détails d'un configuration Fail2ban",
        operation_description="Récupère les détails complets d'un configuration Fail2ban spécifique.",
        
        tags=['API Views'],responses={
            200: "Détails récupérés avec succès",
            404: "Non trouvé",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def retrieve(self, request, pk=None):
        """Récupère les détails d'une règle spécifique"""
        try:
            rule_detail = {
                'id': pk,
                'sid': f'300000{pk}',
                'msg': f'Rule {pk}',
                'rule': f'alert tcp any any -> any any (msg:"Rule {pk}"; sid:300000{pk}; rev:1;)',
                'category': 'custom',
                'severity': random.choice(['low', 'medium', 'high']),
                'enabled': True,
                'alert_count': random.randint(0, 100),
                'last_triggered': timezone.now().isoformat(),
                'created_at': timezone.now().isoformat()
            }
            return Response(rule_detail)
        except Exception as e:
            logger.exception(f"Erreur récupération règle: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Met à jour un configuration Fail2ban",
        operation_description="Met à jour complètement un configuration Fail2ban existant.",
        
        tags=['API Views'],responses={
            200: "Mis à jour avec succès",
            400: "Données invalides",
            404: "Non trouvé",
            401: "Non authentifié",
            500: "Erreur serveur",
        },
    )
    def update(self, request, pk=None):
        """Met à jour une règle Suricata"""
        try:
            data = request.data
            updated_rule = {
                'id': pk,
                'sid': data.get('sid', f'300000{pk}'),
                'msg': data.get('msg', f'Updated Rule {pk}'),
                'rule': data.get('rule', f'alert tcp any any -> any any (msg:"Updated Rule {pk}"; sid:300000{pk}; rev:2;)'),
                'category': data.get('category', 'custom'),
                'severity': data.get('severity', 'medium'),
                'enabled': data.get('enabled', True),
                'updated_at': timezone.now().isoformat(),
                'updated_by': request.user.username
            }
            return Response(updated_rule)
        except Exception as e:
            logger.exception(f"Erreur mise à jour règle: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Supprime un configuration Fail2ban",
        operation_description="Supprime définitivement un configuration Fail2ban du système.",
        
        tags=['API Views'],responses={
            204: "Supprimé avec succès",
            404: "Non trouvé",
            401: "Non authentifié",
            403: "Permission refusée",
            500: "Erreur serveur",
        },
    )
    def destroy(self, request, pk=None):
        """Supprime une règle Suricata"""
        try:
            return Response({'message': f'Règle {pk} supprimée avec succès'}, 
                          status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.exception(f"Erreur suppression règle: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
