"""
Implémentation de l'exécuteur de commandes sécurisé.

Ce module contient l'implémentation de l'interface CommandExecutor
avec des mécanismes de sécurité pour l'exécution de commandes système.
"""

import logging
import subprocess
import shlex
import os
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from ..domain.interfaces import CommandExecutor
from ..domain.entities import CommandResult
from ..domain.exceptions import CommandExecutionException

logger = logging.getLogger(__name__)


class SafeCommandExecutor(CommandExecutor):
    """
    Implémentation sécurisée de l'exécuteur de commandes.
    
    Cette classe fournit une implémentation concrète de l'interface CommandExecutor,
    avec des mécanismes de sécurité pour éviter l'exécution de commandes dangereuses.
    """
    
    # Liste des commandes autorisées par défaut
    DEFAULT_ALLOWED_COMMANDS = [
        'ping', 'traceroute', 'nslookup', 'dig', 'whois',
        'ifconfig', 'ip', 'netstat', 'ss', 'arp',
        'nmap', 'nc', 'curl', 'wget', 'host',
        'route', 'mtr', 'tcpdump', 'iptables', 'ufw',
        'ls', 'cat', 'grep', 'find', 'head', 'tail',
        'echo', 'date', 'uptime', 'df', 'du', 'free',
        'top', 'ps', 'who', 'w', 'last', 'history',
        'systemctl', 'service', 'journalctl'
    ]
    
    # Liste des commandes explicitement interdites
    FORBIDDEN_COMMANDS = [
        'rm', 'mv', 'cp', 'dd', 'mkfs', 'fdisk',
        'chmod', 'chown', 'chgrp', 'chattr',
        'passwd', 'useradd', 'usermod', 'userdel',
        'groupadd', 'groupmod', 'groupdel',
        'sudo', 'su', 'ssh', 'scp', 'sftp',
        'apt', 'apt-get', 'yum', 'dnf', 'pacman',
        'pip', 'npm', 'yarn', 'gem', 'cargo',
        'make', 'gcc', 'g++', 'clang',
        'reboot', 'shutdown', 'halt', 'poweroff',
        'kill', 'killall', 'pkill'
    ]
    
    # Motifs d'expressions régulières interdits
    FORBIDDEN_PATTERNS = [
        r'[;|&]',  # Chaînage de commandes
        r'[><]',   # Redirection
        r'\$\(',   # Substitution de commandes
        r'`',      # Substitution de commandes (backticks)
        r'\{\}',   # Expansion d'accolades
        r'\[\]',   # Expansion de crochets
        r'\*',     # Joker
        r'\?',     # Joker
        r'~',      # Expansion du répertoire personnel
        r'\\',     # Caractère d'échappement
        r'--',     # Options longues (potentiellement dangereuses)
        r'-[a-zA-Z]*r[a-zA-Z]*',  # Options avec 'r' (récursif)
        r'-[a-zA-Z]*f[a-zA-Z]*'   # Options avec 'f' (force)
    ]
    
    def __init__(self, allowed_commands: List[str] = None, timeout: int = 30):
        """
        Initialise l'exécuteur de commandes sécurisé.
        
        Args:
            allowed_commands: Liste des commandes autorisées (utilise la liste par défaut si None)
            timeout: Délai d'expiration en secondes pour l'exécution des commandes
        """
        self.allowed_commands = allowed_commands or self.DEFAULT_ALLOWED_COMMANDS
        self.timeout = timeout
    
    def execute(self, command: str, command_type: str, user_id: int) -> Dict[str, Any]:
        """
        Exécute une commande système de manière sécurisée.
        
        Args:
            command: La commande à exécuter
            command_type: Type de commande (shell, network, diagnostic)
            user_id: ID de l'utilisateur exécutant la commande
            
        Returns:
            Dictionnaire contenant le résultat de l'exécution
            
        Raises:
            CommandExecutionException: Si la commande est interdite ou si une erreur survient
        """
        # Vérification de la sécurité de la commande
        is_safe, reason = self._check_command_safety(command)
        if not is_safe:
            logger.warning(f"Tentative d'exécution d'une commande interdite par l'utilisateur {user_id}: {command}")
            raise CommandExecutionException(f"Commande interdite: {reason}", "security")
        
        try:
            # Log de l'exécution avec les informations utilisateur et le type
            logger.info(f"Exécution de la commande ({command_type}) par l'utilisateur {user_id}: {command}")
            
            # Exécution de la commande
            process = subprocess.Popen(
                shlex.split(command),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Attente du résultat avec timeout
            stdout, stderr = process.communicate(timeout=self.timeout)
            
            # Création du résultat sous forme de dictionnaire
            result = {
                "command": command,
                "command_type": command_type,
                "user_id": user_id,
                "exit_code": process.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "success": (process.returncode == 0),
                "executed_at": datetime.now().isoformat()
            }
            
            return result
        except subprocess.TimeoutExpired:
            # Gestion du timeout
            logger.warning(f"Timeout lors de l'exécution de la commande: {command}")
            try:
                process.kill()
            except Exception:
                pass
            
            raise CommandExecutionException("Délai d'exécution dépassé", "timeout")
        except Exception as e:
            # Gestion des autres erreurs
            logger.exception(f"Erreur lors de l'exécution de la commande: {e}")
            raise CommandExecutionException(f"Erreur d'exécution: {str(e)}", "execution")
    
    def _check_command_safety(self, command: str) -> Tuple[bool, str]:
        """
        Vérifie si une commande est sûre à exécuter.
        
        Args:
            command: La commande à vérifier
            
        Returns:
            Un tuple (is_safe, reason) où is_safe est un booléen indiquant si la commande est sûre,
            et reason est une chaîne expliquant pourquoi la commande est interdite si elle ne l'est pas
        """
        # Extraction du nom de la commande (premier mot)
        command_parts = shlex.split(command)
        if not command_parts:
            return False, "Commande vide"
        
        base_command = os.path.basename(command_parts[0])
        
        # Vérification si la commande est dans la liste des commandes interdites
        if base_command in self.FORBIDDEN_COMMANDS:
            return False, f"Commande '{base_command}' explicitement interdite"
        
        # Vérification si la commande est dans la liste des commandes autorisées
        if base_command not in self.allowed_commands:
            return False, f"Commande '{base_command}' non autorisée"
        
        # Vérification des motifs interdits
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, command):
                return False, f"Motif interdit détecté: {pattern}"
        
        return True, ""
    
    def validate(self, command: str, command_type: str) -> Dict[str, Any]:
        """
        Valide une commande sans l'exécuter.
        
        Args:
            command: La commande à valider
            command_type: Type de commande
            
        Returns:
            Un dictionnaire contenant les informations de validation
        """
        is_safe, reason = self._check_command_safety(command)
        
        return {
            "is_valid": is_safe,
            "reason": reason if not is_safe else "Commande valide",
            "command": command,
            "command_type": command_type
        }
    
    def get_allowed_commands(self) -> List[str]:
        """
        Retourne la liste des commandes autorisées.
        
        Returns:
            Liste des commandes autorisées
        """
        return self.allowed_commands
