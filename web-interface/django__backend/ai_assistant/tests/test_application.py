"""
Tests pour les cas d'utilisation du module ai_assistant.

Ce module teste la logique métier indépendamment de l'infrastructure.
Tests migrés et adaptés depuis l'ancien système avec améliorations anti-simulation.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from ai_assistant.application.use_cases import ConversationUseCase, CommandUseCase, KnowledgeUseCase
from ai_assistant.domain.interfaces import AIClient, CommandExecutor, KnowledgeBase, AIAssistantRepository
from ai_assistant.domain.entities import Message, Conversation, MessageRole, Document, SearchResult, CommandResult
from ai_assistant.domain.exceptions import AIClientException, CommandExecutionException, KnowledgeBaseException


class TestConversationUseCase:
    """Tests pour le cas d'utilisation ConversationUseCase."""
    
    def setup_method(self):
        """Configuration avant chaque test."""
        self.repository = Mock(spec=AIAssistantRepository)
        self.ai_client = Mock(spec=AIClient)
        
        self.use_case = ConversationUseCase(
            repository=self.repository,
            ai_client=self.ai_client
        )
    
    def test_create_conversation_with_real_data(self):
        """Test de création d'une conversation avec données réalistes."""
        # Configuration du mock
        self.repository.save_conversation.return_value = "conv_network_support_001"
        
        # Exécution
        result = self.use_case.create_conversation(
            user_id="network_admin_123",
            title="Support réseau - Problème VLAN 100"
        )
        
        # Vérifications de réalisme
        assert result['id'] == "conv_network_support_001"
        assert result['title'] == "Support réseau - Problème VLAN 100"
        assert 'created_at' in result
        assert 'updated_at' in result
        
        # Vérifier que le repository a été appelé
        self.repository.save_conversation.assert_called_once()
        
        # Vérifier l'absence de données factices
        assert "test" not in result['title'].lower()
        assert "mock" not in result['title'].lower()
        assert "fake" not in result['title'].lower()
    
    def test_create_conversation_auto_title(self):
        """Test de création avec titre automatique réaliste."""
        self.repository.save_conversation.return_value = "conv_auto_001"
        
        # Exécution sans titre
        result = self.use_case.create_conversation(user_id="user_456")
        
        # Vérifications
        assert result['id'] == "conv_auto_001"
        assert "Nouvelle conversation" in result['title']
        assert datetime.now().strftime('%Y-%m-%d') in result['title']
    
    def test_get_conversation_with_realistic_messages(self):
        """Test de récupération d'une conversation avec messages réalistes."""
        # Configuration du mock avec données réalistes
        mock_conversation = Conversation(
            id="conv_network_diag_001",
            title="Diagnostic réseau - Latence élevée",
            user_id="network_engineer_789",
            messages=[
                Message(
                    id="msg_001",
                    role=MessageRole.SYSTEM,
                    content="Je suis un assistant IA spécialisé dans la gestion de réseaux informatiques. Comment puis-je vous aider aujourd'hui?",
                    timestamp=datetime.now()
                ),
                Message(
                    id="msg_002",
                    role=MessageRole.USER,
                    content="Nous observons une latence anormalement élevée (>200ms) sur notre VLAN de production. Pouvez-vous m'aider à diagnostiquer?",
                    timestamp=datetime.now()
                ),
                Message(
                    id="msg_003",
                    role=MessageRole.ASSISTANT,
                    content="Je vais vous aider à diagnostiquer ce problème de latence. Commençons par analyser le trafic réseau et identifier les goulots d'étranglement potentiels.",
                    timestamp=datetime.now(),
                    metadata={"confidence": 0.92, "processing_time": 1.3}
                )
            ],
            context="assistant IA pour la gestion de réseau",
            metadata={'created_at': '2024-01-15T10:30:00', 'incident_priority': 'high'}
        )
        self.repository.get_conversation.return_value = mock_conversation
        
        # Exécution
        result = self.use_case.get_conversation("conv_network_diag_001")
        
        # Vérifications de réalisme
        assert result['id'] == "conv_network_diag_001"
        assert result['title'] == "Diagnostic réseau - Latence élevée"
        assert len(result['messages']) == 3
        
        # Vérifier le contenu réaliste des messages
        user_message = result['messages'][1]
        assert "VLAN de production" in user_message['content']
        assert ">200ms" in user_message['content']
        assert "diagnostiquer" in user_message['content']
        
        assistant_message = result['messages'][2]
        assert "goulots d'étranglement" in assistant_message['content']
        assert assistant_message['metadata']['confidence'] > 0.8
        
        # Vérifier l'absence de contenu simulé
        fake_patterns = [
            "simulation de",
            "données de test",
            "mock network",
            "fake response"
        ]
        
        for message in result['messages']:
            for pattern in fake_patterns:
                assert pattern not in message['content'].lower()
    
    def test_add_message_real_network_scenario(self):
        """Test d'ajout de message avec scénario réseau réaliste."""
        # Configuration des mocks avec données réalistes
        mock_conversation = Conversation(
            id="conv_firewall_config_001",
            title="Configuration firewall - Règles de sécurité",
            user_id="security_admin_456",
            messages=[
                Message(
                    id="msg_system",
                    role=MessageRole.SYSTEM,
                    content="Assistant IA pour la sécurité réseau",
                    timestamp=datetime.now()
                )
            ],
            context="assistant IA pour la gestion de réseau",
            metadata={'created_at': datetime.now().isoformat()}
        )
        self.repository.get_conversation.return_value = mock_conversation
        
        # Configuration de la réponse IA réaliste
        self.ai_client.generate_response.return_value = {
            'content': 'Pour configurer des règles de firewall sécurisées, nous devons définir des politiques strictes pour le trafic entrant et sortant. Je recommande de commencer par analyser votre topologie réseau actuelle.',
            'processing_time': 2.1,
            'model_info': {'model': 'gpt-4', 'version': '0613'},
            'confidence': 0.89,
            'actions': [
                {
                    'type': 'command_suggestion',
                    'data': {
                        'command': 'iptables -L -n -v',
                        'description': 'Afficher les règles de firewall actuelles',
                        'safety_level': 'safe'
                    }
                }
            ]
        }
        
        # Exécution
        result = self.use_case.add_message(
            conversation_id="conv_firewall_config_001",
            content="Je dois configurer un firewall pour sécuriser notre réseau d'entreprise. Quelles sont les meilleures pratiques?",
            role="user"
        )
        
        # Vérifications de réalisme
        assert 'user_message' in result
        assert 'assistant_message' in result
        
        user_msg = result['user_message']
        assert "réseau d'entreprise" in user_msg['content']
        assert "meilleures pratiques" in user_msg['content']
        
        assistant_msg = result['assistant_message']
        assert "politiques strictes" in assistant_msg['content']
        assert "topologie réseau" in assistant_msg['content']
        assert assistant_msg['metadata']['confidence'] > 0.8
        assert assistant_msg['metadata']['processing_time'] > 1.0
        
        # Vérifier l'absence de réponses génériques
        generic_responses = [
            "réponse générique",
            "je suis un assistant",
            "comment puis-je vous aider",
            "voici quelques conseils généraux"
        ]
        
        for generic in generic_responses:
            assert generic not in assistant_msg['content'].lower()
        
        # Vérifier les appels
        self.ai_client.generate_response.assert_called_once()
        assert self.repository.save_conversation.call_count >= 1
    
    def test_conversation_error_handling_realistic(self):
        """Test de gestion d'erreurs réaliste."""
        # Configuration pour une erreur de timeout API
        self.ai_client.generate_response.side_effect = AIClientException(
            "Timeout de l'API OpenAI après 30 secondes", 
            "api_timeout"
        )
        
        mock_conversation = Conversation(
            id="conv_timeout_test",
            title="Test timeout",
            user_id="user_123",
            messages=[],
            context="test",
            metadata={'created_at': datetime.now().isoformat()}
        )
        self.repository.get_conversation.return_value = mock_conversation
        
        # Vérifier que l'exception est correctement levée
        with pytest.raises(AIClientException) as exc_info:
            self.use_case.add_message(
                conversation_id="conv_timeout_test",
                content="Message qui provoque un timeout",
                role="user"
            )
        
        assert "Timeout de l'API" in str(exc_info.value)
        assert exc_info.value.error_type == "api_timeout"


class TestCommandUseCase:
    """Tests pour le cas d'utilisation CommandUseCase."""
    
    def setup_method(self):
        """Configuration avant chaque test."""
        self.command_executor = Mock(spec=CommandExecutor)
        self.ai_client = Mock(spec=AIClient)
        self.use_case = CommandUseCase(
            command_executor=self.command_executor,
            ai_client=self.ai_client
        )
    
    def test_execute_safe_network_command(self):
        """Test d'exécution de commande réseau sûre."""
        # Configuration des mocks pour commande sûre
        self.ai_client.analyze_command.return_value = {
            'is_valid': True,
            'safety_level': 'safe',
            'intent': 'network_query',
            'reason': 'Commande de diagnostic réseau en lecture seule'
        }
        
        self.command_executor.validate.return_value = {
            'is_valid': True,
            'reason': 'Commande autorisée pour diagnostic réseau'
        }
        
        self.command_executor.execute.return_value = {
            'success': True,
            'output': 'PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.\n64 bytes from 8.8.8.8: icmp_seq=1 ttl=116 time=12.3 ms\n64 bytes from 8.8.8.8: icmp_seq=2 ttl=116 time=11.8 ms\n--- 8.8.8.8 ping statistics ---\n2 packets transmitted, 2 received, 0% packet loss',
            'exit_code': 0,
            'execution_time': 2.1
        }
        
        # Exécution
        result = self.use_case.execute_command(
            command="ping -c 2 8.8.8.8",
            command_type="network",
            user_id="network_admin_001"
        )
        
        # Vérifications
        assert result['success']
        assert result['command'] == "ping -c 2 8.8.8.8"
        assert "64 bytes from 8.8.8.8" in result['output']
        assert result['exit_code'] == 0
        assert result['execution_time'] > 2.0
        
        # Vérifier l'absence de données simulées
        fake_output_patterns = [
            "simulated ping",
            "mock network response",
            "fake ping output",
            "test network data"
        ]
        
        for pattern in fake_output_patterns:
            assert pattern not in result['output'].lower()
        
        # Vérifier les appels
        self.ai_client.analyze_command.assert_called_once_with("ping -c 2 8.8.8.8")
        self.command_executor.validate.assert_called_once()
        self.command_executor.execute.assert_called_once()
    
    def test_block_dangerous_command(self):
        """Test de blocage de commande dangereuse."""
        # Configuration pour commande dangereuse
        self.ai_client.analyze_command.return_value = {
            'is_valid': False,
            'safety_level': 'dangerous',
            'intent': 'system_destruction',
            'reason': 'Commande de suppression système critique - risque de destruction complète'
        }
        
        # Exécution
        result = self.use_case.execute_command(
            command="rm -rf /etc/",
            command_type="shell",
            user_id="user_123"
        )
        
        # Vérifications
        assert not result['success']
        assert result['command'] == "rm -rf /etc/"
        assert "dangereuse" in result['error']
        assert "destruction" in result['error']
        assert result['safety_level'] == "dangerous"
        
        # Vérifier que l'exécuteur n'a pas été appelé
        self.command_executor.execute.assert_not_called()
    
    def test_command_validation_realistic_errors(self):
        """Test de validation avec erreurs réalistes."""
        # Configuration pour commande avec permissions insuffisantes
        self.ai_client.analyze_command.return_value = {
            'is_valid': True,
            'safety_level': 'safe',
            'intent': 'network_config'
        }
        
        self.command_executor.validate.return_value = {
            'is_valid': False,
            'reason': 'Permissions insuffisantes - commande nécessite les privilèges root'
        }
        
        # Exécution
        result = self.use_case.execute_command(
            command="iptables -L",
            command_type="network",
            user_id="regular_user_456"
        )
        
        # Vérifications
        assert not result['success']
        assert "Permissions insuffisantes" in result['error']
        assert "privilèges root" in result['error']
        assert not result['validated']
    
    def test_command_execution_exception_handling(self):
        """Test de gestion d'exception lors de l'exécution."""
        # Configuration des mocks
        self.ai_client.analyze_command.return_value = {
            'is_valid': True,
            'safety_level': 'safe'
        }
        
        self.command_executor.validate.return_value = {
            'is_valid': True,
            'reason': 'Commande autorisée'
        }
        
        # Simulation d'exception réaliste
        self.command_executor.execute.side_effect = CommandExecutionException(
            "Interface 'eth99' introuvable - vérifiez la configuration réseau",
            "interface_not_found"
        )
        
        # Exécution
        result = self.use_case.execute_command("ifconfig eth99", "network")
        
        # Vérifications
        assert not result['success']
        assert "Interface 'eth99' introuvable" in result['error']
        assert result['exception_type'] == "interface_not_found"
    
    def test_get_allowed_commands_realistic(self):
        """Test de récupération des commandes autorisées."""
        # Configuration du mock avec commandes réalistes
        self.command_executor.get_allowed_commands.return_value = [
            "ping", "traceroute", "nslookup", "dig",
            "netstat", "ss", "ip route show", "ip addr show",
            "arp -a", "ifconfig", "iwconfig"
        ]
        
        # Exécution
        commands = self.use_case.get_allowed_commands()
        
        # Vérifications
        assert len(commands) > 5
        assert "ping" in commands
        assert "traceroute" in commands
        assert "netstat" in commands
        
        # Vérifier l'absence de commandes dangereuses
        dangerous_commands = ["rm", "format", "delete", "shutdown", "reboot"]
        for dangerous in dangerous_commands:
            assert dangerous not in commands


class TestKnowledgeUseCase:
    """Tests pour le cas d'utilisation KnowledgeUseCase."""
    
    def setup_method(self):
        """Configuration avant chaque test."""
        self.knowledge_base = Mock(spec=KnowledgeBase)
        self.use_case = KnowledgeUseCase(knowledge_base=self.knowledge_base)
    
    def test_search_with_realistic_network_content(self):
        """Test de recherche avec contenu réseau réaliste."""
        # Configuration du mock avec résultats réalistes
        mock_results = [
            SearchResult(
                id="kb_vlan_config_001",
                title="Configuration VLAN sur switches Cisco Catalyst",
                content="Pour configurer un VLAN sur un switch Cisco Catalyst, suivez ces étapes :\n1. Accédez au mode de configuration globale : enable, configure terminal\n2. Créez le VLAN : vlan 100\n3. Nommez le VLAN : name Marketing_Department\n4. Assignez les ports : interface range fastethernet 0/1-12, switchport mode access, switchport access vlan 100",
                score=0.94,
                metadata={
                    'category': 'network_configuration',
                    'vendor': 'cisco',
                    'last_updated': '2024-01-10',
                    'verified': True
                }
            ),
            SearchResult(
                id="kb_vlan_troubleshoot_002",
                title="Dépannage des problèmes de connectivité VLAN",
                content="Étapes de diagnostic pour les problèmes VLAN :\n1. Vérifiez la configuration VLAN : show vlan brief\n2. Contrôlez les assignments de ports : show interfaces switchport\n3. Testez la connectivité inter-VLAN : ping entre différents VLANs\n4. Vérifiez le routage VLAN : show ip route vlan",
                score=0.89,
                metadata={
                    'category': 'troubleshooting',
                    'difficulty': 'intermediate',
                    'estimated_time': '15-30 minutes'
                }
            )
        ]
        self.knowledge_base.search.return_value = mock_results
        
        # Exécution
        results = self.use_case.search("configuration VLAN problème connectivité", limit=5)
        
        # Vérifications de réalisme
        assert len(results) == 2
        assert all(result['score'] > 0.8 for result in results)
        
        # Vérifier le contenu technique réaliste
        first_result = results[0]
        assert "Cisco Catalyst" in first_result['title']
        assert "configure terminal" in first_result['content']
        assert "switchport mode access" in first_result['content']
        assert first_result['metadata']['verified']
        
        second_result = results[1]
        assert "show vlan brief" in second_result['content']
        assert "show interfaces switchport" in second_result['content']
        assert "15-30 minutes" in second_result['metadata']['estimated_time']
        
        # Vérifier l'absence de contenu factice
        fake_content_patterns = [
            "lorem ipsum", "placeholder", "example text",
            "sample configuration", "test vlan", "fake switch"
        ]
        
        for result in results:
            for pattern in fake_content_patterns:
                assert pattern not in result['content'].lower()
                assert pattern not in result['title'].lower()
        
        # Vérifier l'appel
        self.knowledge_base.search.assert_called_once_with("configuration VLAN problème connectivité", 5)
    
    def test_add_realistic_network_document(self):
        """Test d'ajout de document réseau réaliste."""
        # Configuration du mock
        self.knowledge_base.add_document.return_value = "kb_bgp_config_advanced_001"
        
        # Exécution avec contenu réseau réaliste
        result = self.use_case.add_document(
            title="Configuration BGP avancée pour ISP multihomed",
            content="""Configuration BGP pour environnement multi-ISP :

1. Configuration de base BGP :
router bgp 65001
bgp router-id 192.168.1.1
neighbor 203.0.113.1 remote-as 174
neighbor 203.0.113.1 description "ISP1-Cogent"
neighbor 198.51.100.1 remote-as 3356
neighbor 198.51.100.1 description "ISP2-Level3"

2. Politique de routage sortant :
ip as-path access-list 1 permit ^$
route-map ISP1-OUT permit 10
match as-path 1
set local-preference 150

3. Load balancing et redondance :
bgp bestpath as-path multipath-relax
maximum-paths 2""",
            metadata={
                'category': 'advanced_routing',
                'protocol': 'bgp',
                'complexity': 'expert',
                'vendor': 'cisco',
                'use_case': 'ISP_multihoming',
                'author': 'network_engineering_team'
            }
        )
        
        # Vérifications
        assert result['id'] == "kb_bgp_config_advanced_001"
        assert result['title'] == "Configuration BGP avancée pour ISP multihomed"
        assert "Configuration BGP pour environnement multi-ISP" in result['content_preview']
        assert result['metadata']['protocol'] == 'bgp'
        assert result['metadata']['complexity'] == 'expert'
        
        # Vérifier que le contenu est technique et réaliste
        assert "router bgp" in result['content_preview']
        assert "remote-as" in result['content_preview']
        
        # Vérifier l'appel
        self.knowledge_base.add_document.assert_called_once()
        added_doc = self.knowledge_base.add_document.call_args[0][0]
        assert isinstance(added_doc, Document)
        assert "BGP" in added_doc.title
    
    def test_knowledge_base_error_handling(self):
        """Test de gestion d'erreurs de la base de connaissances."""
        # Configuration pour erreur de connexion Elasticsearch
        self.knowledge_base.search.side_effect = KnowledgeBaseException(
            "Connexion à Elasticsearch refusée - vérifiez que le service est démarré",
            "connection_refused"
        )
        
        # Exécution - ne doit pas lever d'exception mais retourner liste vide
        results = self.use_case.search("test query")
        
        # Vérifications
        assert results == []
        self.knowledge_base.search.assert_called_once()
    
    def test_get_document_realistic_content(self):
        """Test de récupération de document avec contenu réaliste."""
        # Configuration du mock
        mock_document = Document(
            title="Guide de sécurisation des switches Cisco",
            content="""Procédures de sécurisation des équipements Cisco :

1. Configuration des mots de passe :
enable secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7m0
service password-encryption
username admin privilege 15 secret cisco123!

2. Sécurisation SSH :
ip domain-name company.local
crypto key generate rsa modulus 2048
ip ssh version 2
line vty 0 15
transport input ssh
login local

3. Protection contre les attaques :
spanning-tree portfast bpduguard default
errdisable recovery cause bpduguard
port-security maximum 2
port-security violation shutdown""",
            metadata={
                'category': 'security',
                'vendor': 'cisco',
                'security_level': 'enterprise',
                'compliance': ['ISO27001', 'NIST'],
                'last_audit': '2024-01-05'
            }
        )
        self.knowledge_base.get_document.return_value = mock_document
        
        # Exécution
        result = self.use_case.get_document("kb_cisco_security_001")
        
        # Vérifications
        assert result['id'] == "kb_cisco_security_001"
        assert result['title'] == "Guide de sécurisation des switches Cisco"
        assert "enable secret" in result['content']
        assert "crypto key generate rsa" in result['content']
        assert result['metadata']['vendor'] == 'cisco'
        assert 'ISO27001' in result['metadata']['compliance']
        
        # Vérifier l'absence de contenu générique
        generic_content = [
            "exemple de configuration",
            "placeholder password",
            "sample security",
            "test configuration"
        ]
        
        for generic in generic_content:
            assert generic not in result['content'].lower()


# Tests d'intégration entre cas d'utilisation
class TestUseCaseIntegration:
    """Tests d'intégration entre plusieurs cas d'utilisation."""
    
    def setup_method(self):
        """Configuration avant chaque test."""
        # Mocks partagés
        self.ai_client = Mock(spec=AIClient)
        self.repository = Mock(spec=AIAssistantRepository)
        self.knowledge_base = Mock(spec=KnowledgeBase)
        self.command_executor = Mock(spec=CommandExecutor)
        
        # Cas d'utilisation
        self.conversation_uc = ConversationUseCase(self.repository, self.ai_client)
        self.command_uc = CommandUseCase(self.command_executor, self.ai_client)
        self.knowledge_uc = KnowledgeUseCase(self.knowledge_base)
    
    def test_complete_network_support_workflow(self):
        """Test d'un workflow complet de support réseau."""
        # 1. Créer une conversation pour incident réseau
        self.repository.save_conversation.return_value = "conv_incident_network_001"
        
        conversation = self.conversation_uc.create_conversation(
            user_id="network_admin_789",
            title="Incident - Perte connectivité datacenter"
        )
        
        # 2. Recherche dans la base de connaissances pour diagnostic
        self.knowledge_base.search.return_value = [
            SearchResult(
                id="kb_datacenter_connectivity_001",
                title="Diagnostic perte connectivité datacenter",
                content="Procédure de diagnostic : 1. Vérifier liens physiques 2. Contrôler tables ARP 3. Analyser logs switching",
                score=0.96,
                metadata={'urgency': 'critical', 'sla': '15_minutes'}
            )
        ]
        
        knowledge_results = self.knowledge_uc.search("perte connectivité datacenter", limit=3)
        
        # 3. Traiter un message avec le contexte de la base de connaissances
        mock_conversation = Conversation(
            id=conversation['id'],
            title=conversation['title'],
            user_id="network_admin_789",
            messages=[],
            context="incident critique datacenter",
            metadata={'created_at': conversation['created_at']}
        )
        self.repository.get_conversation.return_value = mock_conversation
        
        self.ai_client.generate_response.return_value = {
            'content': 'Je comprends la criticité de cette situation. Basé sur notre documentation, commençons par vérifier les liens physiques et les tables ARP. Je recommande d\'exécuter ces commandes de diagnostic.',
            'processing_time': 1.8,
            'confidence': 0.91,
            'actions': [
                {
                    'type': 'command_suggestion',
                    'data': {
                        'command': 'show interface status',
                        'priority': 'high',
                        'description': 'Vérifier l\'état des interfaces'
                    }
                }
            ]
        }
        
        message_result = self.conversation_uc.add_message(
            conversation_id=conversation['id'],
            content="Perte totale de connectivité vers le datacenter depuis 5 minutes. Les utilisateurs ne peuvent plus accéder aux applications critiques.",
            role="user"
        )
        
        # 4. Exécuter une commande de diagnostic suggérée
        self.ai_client.analyze_command.return_value = {
            'is_valid': True,
            'safety_level': 'safe',
            'intent': 'network_diagnostic'
        }
        
        self.command_executor.validate.return_value = {
            'is_valid': True,
            'reason': 'Commande de diagnostic autorisée'
        }
        
        self.command_executor.execute.return_value = {
            'success': True,
            'output': 'Gi0/1    connected    1         a-full  a-1000  10/100/1000-TX\nGi0/2    notconnect   1            auto   auto 10/100/1000-TX\nGi0/3    connected    1         a-full  a-1000  10/100/1000-TX',
            'exit_code': 0,
            'execution_time': 0.8
        }
        
        command_result = self.command_uc.execute_command(
            command="show interface status",
            command_type="network",
            user_id="network_admin_789"
        )
        
        # Vérifications du workflow complet
        assert conversation['id'] == "conv_incident_network_001"
        assert "Incident - Perte connectivité datacenter" in conversation['title']
        
        assert len(knowledge_results) == 1
        assert knowledge_results[0]['metadata']['urgency'] == 'critical'
        assert "Diagnostic perte connectivité" in knowledge_results[0]['title']
        
        assert 'assistant_message' in message_result
        assert "criticité de cette situation" in message_result['assistant_message']['content']
        assert "liens physiques" in message_result['assistant_message']['content']
        
        assert command_result['success']
        assert "Gi0/2    notconnect" in command_result['output']  # Interface déconnectée détectée
        
        # Vérifier l'absence de données simulées dans tout le workflow
        all_content = [
            conversation['title'],
            knowledge_results[0]['content'],
            message_result['assistant_message']['content'],
            command_result['output']
        ]
        
        simulation_indicators = [
            "simulation de", "données factices", "test network",
            "mock interface", "fake connectivity", "placeholder"
        ]
        
        for content in all_content:
            for indicator in simulation_indicators:
                assert indicator not in content.lower()


if __name__ == '__main__':
    pytest.main([__file__])
