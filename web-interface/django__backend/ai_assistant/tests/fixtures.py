"""
Fixtures pour les tests.

Ce module contient des données de test réutilisables pour les tests unitaires.
"""

from datetime import datetime
import json
import uuid

from ai_assistant.domain.entities import Message, Conversation, MessageRole, Document, SearchResult


# Données pour les messages
SAMPLE_MESSAGES = [
    {
        "id": "msg_1",
        "role": MessageRole.SYSTEM,
        "content": "Je suis un assistant IA pour la gestion de réseau.",
        "timestamp": datetime.now(),
        "metadata": {"type": "system_prompt"},
        "actions_taken": []
    },
    {
        "id": "msg_2",
        "role": MessageRole.USER,
        "content": "Bonjour, pouvez-vous m'aider à analyser mon réseau ?",
        "timestamp": datetime.now(),
        "metadata": {},
        "actions_taken": []
    },
    {
        "id": "msg_3",
        "role": MessageRole.ASSISTANT,
        "content": "Bien sûr, je peux vous aider à analyser votre réseau.",
        "timestamp": datetime.now(),
        "metadata": {"model": "test-model"},
        "actions_taken": [
            {
                "type": "execute_command",
                "data": {
                    "command": "ifconfig",
                    "command_type": "shell"
                },
                "status": "success",
                "result": {
                    "output": "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n        inet 192.168.1.100  netmask 255.255.255.0  broadcast 192.168.1.255",
                    "exit_code": 0
                }
            }
        ]
    }
]

# Données pour les conversations
SAMPLE_CONVERSATIONS = [
    {
        "id": "conv_1",
        "title": "Analyse réseau",
        "user_id": "user_1",
        "messages": SAMPLE_MESSAGES,
        "context": "Analyse de la configuration réseau",
        "metadata": {"created_at": datetime.now().isoformat()}
    },
    {
        "id": "conv_2",
        "title": "Dépannage connexion",
        "user_id": "user_1",
        "messages": [],
        "context": "Dépannage de problèmes de connexion",
        "metadata": {"created_at": datetime.now().isoformat()}
    },
    {
        "id": "conv_3",
        "title": "Configuration firewall",
        "user_id": "user_2",
        "messages": [],
        "context": "Configuration des règles de firewall",
        "metadata": {"created_at": datetime.now().isoformat()}
    }
]

# Données pour les documents
SAMPLE_DOCUMENTS = [
    {
        "id": "doc_1",
        "title": "Guide de dépannage réseau",
        "content": "Ce guide explique comment diagnostiquer et résoudre les problèmes de réseau courants...",
        "metadata": {"source": "internal", "category": "troubleshooting"}
    },
    {
        "id": "doc_2",
        "title": "Configuration de routeurs",
        "content": "Instructions détaillées pour configurer différents types de routeurs...",
        "metadata": {"source": "vendor", "category": "configuration"}
    },
    {
        "id": "doc_3",
        "title": "Bonnes pratiques de sécurité réseau",
        "content": "Recommandations pour sécuriser votre infrastructure réseau...",
        "metadata": {"source": "internal", "category": "security"}
    }
]

# Données pour les résultats de recherche
SAMPLE_SEARCH_RESULTS = [
    {
        "id": "result_1",
        "title": "Guide de dépannage réseau",
        "content": "Ce guide explique comment diagnostiquer et résoudre les problèmes de réseau courants...",
        "metadata": {"source": "internal", "category": "troubleshooting"},
        "score": 0.95
    },
    {
        "id": "result_2",
        "title": "Configuration de routeurs",
        "content": "Instructions détaillées pour configurer différents types de routeurs...",
        "metadata": {"source": "vendor", "category": "configuration"},
        "score": 0.85
    },
    {
        "id": "result_3",
        "title": "Bonnes pratiques de sécurité réseau",
        "content": "Recommandations pour sécuriser votre infrastructure réseau...",
        "metadata": {"source": "internal", "category": "security"},
        "score": 0.75
    }
]

# Données pour les commandes et leurs résultats
SAMPLE_COMMANDS = {
    "ifconfig": {
        "success": True,
        "output": "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n        inet 192.168.1.100  netmask 255.255.255.0  broadcast 192.168.1.255",
        "error": "",
        "exit_code": 0
    },
    "ping -c 3 google.com": {
        "success": True,
        "output": "PING google.com (142.250.201.78) 56(84) bytes of data.\n64 bytes from par21s19-in-f14.1e100.net (142.250.201.78): icmp_seq=1 ttl=115 time=9.95 ms\n64 bytes from par21s19-in-f14.1e100.net (142.250.201.78): icmp_seq=2 ttl=115 time=10.1 ms\n64 bytes from par21s19-in-f14.1e100.net (142.250.201.78): icmp_seq=3 ttl=115 time=9.87 ms\n\n--- google.com ping statistics ---\n3 packets transmitted, 3 received, 0% packet loss, time 2003ms\nrtt min/avg/max/mdev = 9.866/9.970/10.071/0.084 ms",
        "error": "",
        "exit_code": 0
    },
    "netstat -tuln": {
        "success": True,
        "output": "Active Internet connections (only servers)\nProto Recv-Q Send-Q Local Address           Foreign Address         State      \ntcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN     \ntcp        0      0 127.0.0.1:5432          0.0.0.0:*               LISTEN     \ntcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN     \ntcp6       0      0 :::22                   :::*                    LISTEN     \ntcp6       0      0 :::80                   :::*                    LISTEN     \nudp        0      0 0.0.0.0:68              0.0.0.0:*                          \nudp        0      0 0.0.0.0:53              0.0.0.0:*                          \nudp6       0      0 :::53                   :::*                               ",
        "error": "",
        "exit_code": 0
    },
    "ip route": {
        "success": True,
        "output": "default via 192.168.1.1 dev eth0 proto dhcp metric 100\n192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.100 metric 100",
        "error": "",
        "exit_code": 0
    },
    "ls -la": {
        "success": True,
        "output": "total 32\ndrwxr-xr-x  5 user user 4096 May 10 14:23 .\ndrwxr-xr-x 25 user user 4096 May 10 14:20 ..\n-rw-r--r--  1 user user  220 May 10 14:20 .bash_logout\n-rw-r--r--  1 user user 3771 May 10 14:20 .bashrc\ndrwxr-xr-x  3 user user 4096 May 10 14:23 .config\n-rw-r--r--  1 user user  807 May 10 14:20 .profile\ndrwxr-xr-x  2 user user 4096 May 10 14:23 Documents\ndrwxr-xr-x  2 user user 4096 May 10 14:23 Downloads",
        "error": "",
        "exit_code": 0
    }
}

# Fonctions pour créer des instances d'entités

def create_message(message_data=None):
    """
    Crée une instance de Message avec les données fournies ou par défaut.
    
    Args:
        message_data: Données pour initialiser le message
        
    Returns:
        Instance de Message
    """
    if message_data is None:
        message_data = SAMPLE_MESSAGES[1]
    
    return Message(
        id=message_data.get("id"),
        role=message_data.get("role", MessageRole.USER),
        content=message_data.get("content", "Test message"),
        timestamp=message_data.get("timestamp", datetime.now()),
        metadata=message_data.get("metadata", {}),
        actions_taken=message_data.get("actions_taken", [])
    )

def create_conversation(conversation_data=None, with_messages=True):
    """
    Crée une instance de Conversation avec les données fournies ou par défaut.
    
    Args:
        conversation_data: Données pour initialiser la conversation
        with_messages: Si True, inclut des messages dans la conversation
        
    Returns:
        Instance de Conversation
    """
    if conversation_data is None:
        conversation_data = SAMPLE_CONVERSATIONS[0]
    
    messages = []
    if with_messages:
        messages = [create_message(msg) for msg in conversation_data.get("messages", SAMPLE_MESSAGES)]
    
    return Conversation(
        id=conversation_data.get("id"),
        title=conversation_data.get("title", "Test conversation"),
        user_id=conversation_data.get("user_id", "user_1"),
        messages=messages,
        context=conversation_data.get("context", "Test context"),
        metadata=conversation_data.get("metadata", {})
    )

def create_document(document_data=None):
    """
    Crée une instance de Document avec les données fournies ou par défaut.
    
    Args:
        document_data: Données pour initialiser le document
        
    Returns:
        Instance de Document
    """
    if document_data is None:
        document_data = SAMPLE_DOCUMENTS[0]
    
    return Document(
        title=document_data.get("title", "Test document"),
        content=document_data.get("content", "Test content"),
        metadata=document_data.get("metadata", {})
    )

def create_search_result(result_data=None):
    """
    Crée une instance de SearchResult avec les données fournies ou par défaut.
    
    Args:
        result_data: Données pour initialiser le résultat de recherche
        
    Returns:
        Instance de SearchResult
    """
    if result_data is None:
        result_data = SAMPLE_SEARCH_RESULTS[0]
    
    return SearchResult(
        id=result_data.get("id"),
        title=result_data.get("title", "Test result"),
        content=result_data.get("content", "Test content"),
        metadata=result_data.get("metadata", {}),
        score=result_data.get("score", 0.9)
    ) 