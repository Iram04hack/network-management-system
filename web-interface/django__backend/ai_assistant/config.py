"""
Configuration pour le module d'assistant IA.

Ce module contient les configurations pour le module d'assistant IA.
"""

import os
from pathlib import Path

# Configuration de l'API OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4")
OPENAI_EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")

# Configuration de l'API Google Custom Search
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID", "")

# Configuration des chemins
BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = os.environ.get("AI_ASSISTANT_STORAGE_DIR", BASE_DIR / "storage")
DOCUMENTS_DIR = os.path.join(STORAGE_DIR, "documents")
CONVERSATIONS_DIR = os.path.join(STORAGE_DIR, "conversations")
COMMAND_HISTORY_DIR = os.path.join(STORAGE_DIR, "command_history")

# Créer les répertoires s'ils n'existent pas
for directory in [STORAGE_DIR, DOCUMENTS_DIR, CONVERSATIONS_DIR, COMMAND_HISTORY_DIR]:
    os.makedirs(directory, exist_ok=True)

# Configuration des limites
MAX_MESSAGES_HISTORY = 10
MAX_COMMAND_HISTORY = 10
MAX_SEARCH_RESULTS = 10
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10 Mo

# Configuration des commandes réseau
PING_COUNT = 5
TRACEROUTE_MAX_HOPS = 30
NMAP_SCAN_TYPE = "-sV"  # Scan de version
NETSTAT_OPTIONS = "-tuln"  # TCP, UDP, listening, numeric
IFCONFIG_INTERFACE = ""  # Toutes les interfaces

# Configuration de la sécurité
ALLOWED_COMMANDS = [
    "ping",
    "traceroute",
    "nmap",
    "netstat",
    "ifconfig",
    "ip",
    "ss",
    "arp",
    "route",
    "hostname",
    "dig",
    "nslookup",
    "host",
    "whois",
    "curl",
    "wget",
    "nc",
    "telnet",
    "ssh",
    "scp",
    "rsync",
    "ftp",
    "sftp",
    "tcpdump",
    "wireshark",
    "tshark",
] 