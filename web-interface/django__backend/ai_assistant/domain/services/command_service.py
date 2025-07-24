"""
Service d'exécution de commandes.

Ce module contient le service pour exécuter des commandes shell,
SQL ou Python et analyser leur sécurité.
"""

import logging
import subprocess
import sqlite3
import re
from typing import Dict, Any, List

from ai_assistant.domain.models import CommandResult
from ai_assistant.domain.exceptions import CommandExecutionError, SecurityError

logger = logging.getLogger(__name__)


class CommandService:
    """Service pour exécuter des commandes."""
    
    def __init__(self):
        """Initialise le service de commande."""
        # Liste des commandes dangereuses
        self.dangerous_commands = [
            "rm -rf", "rmdir", "DROP TABLE", "DROP DATABASE", "DELETE FROM",
            "FORMAT", "dd if=", "mkfs", "fdisk", "> /dev/", "shutdown", "reboot",
            "halt", "poweroff", "init 0", "init 6", ":(){:|:&};:", "chmod -R 777",
            "chmod -R 000", "chown -R", "eval", "exec", "fork bomb", "wget", "curl"
        ]
        
        # Liste des chemins sensibles
        self.sensitive_paths = [
            "/etc/passwd", "/etc/shadow", "/etc/sudoers", "/etc/ssh",
            "/var/log", "/root", "/boot", "/dev", "/proc", "/sys"
        ]
    
    def execute_shell_command(self, command: str) -> CommandResult:
        """
        Exécute une commande shell.
        
        Args:
            command: Commande à exécuter
            
        Returns:
            CommandResult: Résultat de la commande
            
        Raises:
            SecurityError: Si la commande est considérée comme dangereuse
            CommandExecutionError: Si une erreur se produit lors de l'exécution de la commande
        """
        # Vérifier la sécurité de la commande
        safety_analysis = self.analyze_command_safety(command, "shell")
        if not safety_analysis.get("is_safe", False):
            raise SecurityError(safety_analysis.get("reason", "Commande potentiellement dangereuse"))
        
        try:
            # Exécuter la commande
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(timeout=30)  # Timeout de 30 secondes
            exit_code = process.returncode
            
            return CommandResult(
                command=command,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                success=(exit_code == 0)
            )
        
        except subprocess.TimeoutExpired:
            # Tuer le processus s'il dépasse le timeout
            process.kill()
            stdout, stderr = process.communicate()
            raise CommandExecutionError("La commande a dépassé le délai d'exécution (30 secondes)")
        
        except Exception as e:
            logger.exception(f"Erreur lors de l'exécution de la commande: {command}")
            raise CommandExecutionError(f"Erreur lors de l'exécution de la commande: {str(e)}")
    
    def execute_sql_query(self, query: str, database_path: str = ":memory:") -> CommandResult:
        """
        Exécute une requête SQL.
        
        Args:
            query: Requête SQL à exécuter
            database_path: Chemin vers la base de données SQLite
            
        Returns:
            CommandResult: Résultat de la requête
            
        Raises:
            SecurityError: Si la requête est considérée comme dangereuse
            CommandExecutionError: Si une erreur se produit lors de l'exécution de la requête
        """
        # Vérifier la sécurité de la requête
        safety_analysis = self.analyze_command_safety(query, "sql")
        if not safety_analysis.get("is_safe", False):
            raise SecurityError(safety_analysis.get("reason", "Requête SQL potentiellement dangereuse"))
        
        try:
            # Se connecter à la base de données
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
            
            # Exécuter la requête
            cursor.execute(query)
            
            # Récupérer les résultats
            if query.strip().upper().startswith(("SELECT", "PRAGMA", "EXPLAIN", "ANALYZE")):
                rows = cursor.fetchall()
                column_names = [description[0] for description in cursor.description] if cursor.description else []
                
                # Formater les résultats
                result_lines = []
                if column_names:
                    result_lines.append(" | ".join(column_names))
                    result_lines.append("-" * len(" | ".join(column_names)))
                
                for row in rows:
                    result_lines.append(" | ".join(str(cell) for cell in row))
                
                stdout = "\n".join(result_lines)
                stderr = ""
                success = True
            else:
                # Pour les requêtes non-SELECT (INSERT, UPDATE, DELETE, etc.)
                conn.commit()
                stdout = f"{cursor.rowcount} ligne(s) affectée(s)"
                stderr = ""
                success = True
            
            # Fermer la connexion
            conn.close()
            
            return CommandResult(
                command=query,
                exit_code=0 if success else 1,
                stdout=stdout,
                stderr=stderr,
                success=success
            )
        
        except Exception as e:
            logger.exception(f"Erreur lors de l'exécution de la requête SQL: {query}")
            return CommandResult(
                command=query,
                exit_code=1,
                stdout="",
                stderr=str(e),
                success=False
            )
    
    def execute_python_code(self, code: str) -> CommandResult:
        """
        Exécute du code Python.
        
        Args:
            code: Code Python à exécuter
            
        Returns:
            CommandResult: Résultat de l'exécution
            
        Raises:
            SecurityError: Si le code est considéré comme dangereux
            CommandExecutionError: Si une erreur se produit lors de l'exécution du code
        """
        # Vérifier la sécurité du code
        safety_analysis = self.analyze_command_safety(code, "python")
        if not safety_analysis.get("is_safe", False):
            raise SecurityError(safety_analysis.get("reason", "Code Python potentiellement dangereux"))
        
        try:
            # Créer un environnement d'exécution isolé
            local_vars = {}
            global_vars = {
                "__builtins__": {
                    name: __builtins__[name]
                    for name in [
                        "abs", "all", "any", "bin", "bool", "chr", "complex", "dict",
                        "dir", "divmod", "enumerate", "filter", "float", "format", "frozenset",
                        "hash", "hex", "int", "isinstance", "issubclass", "len", "list",
                        "map", "max", "min", "oct", "ord", "pow", "print", "range",
                        "repr", "reversed", "round", "set", "slice", "sorted", "str",
                        "sum", "tuple", "type", "zip"
                    ]
                }
            }
            
            # Rediriger stdout et stderr
            import io
            import sys
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            old_stdout, old_stderr = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = stdout_capture, stderr_capture
            
            try:
                # Exécuter le code
                exec(code, global_vars, local_vars)
                success = True
                exit_code = 0
            except Exception as e:
                success = False
                exit_code = 1
                print(f"Erreur: {str(e)}", file=sys.stderr)
            finally:
                # Restaurer stdout et stderr
                sys.stdout, sys.stderr = old_stdout, old_stderr
            
            stdout = stdout_capture.getvalue()
            stderr = stderr_capture.getvalue()
            
            return CommandResult(
                command=code,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                success=success
            )
        
        except Exception as e:
            logger.exception(f"Erreur lors de l'exécution du code Python")
            raise CommandExecutionError(f"Erreur lors de l'exécution du code Python: {str(e)}")
    
    def analyze_command_safety(self, command: str, command_type: str = "shell") -> Dict[str, Any]:
        """
        Analyse la sécurité d'une commande.
        
        Args:
            command: Commande à analyser
            command_type: Type de commande (shell, sql, python)
            
        Returns:
            Dict[str, Any]: Résultat de l'analyse de sécurité
        """
        if command_type == "shell":
            return self._analyze_shell_command_safety(command)
        elif command_type == "sql":
            return self._analyze_sql_query_safety(command)
        elif command_type == "python":
            return self._analyze_python_code_safety(command)
        else:
            return {
                "is_safe": False,
                "reason": f"Type de commande non supporté: {command_type}",
                "details": []
            }
    
    def _analyze_shell_command_safety(self, command: str) -> Dict[str, Any]:
        """
        Analyse la sécurité d'une commande shell.
        
        Args:
            command: Commande shell à analyser
            
        Returns:
            Dict[str, Any]: Résultat de l'analyse de sécurité
        """
        command_lower = command.lower()
        issues = []
        
        # Vérifier les commandes dangereuses
        for dangerous_command in self.dangerous_commands:
            if dangerous_command.lower() in command_lower:
                issues.append(f"Commande dangereuse détectée: {dangerous_command}")
        
        # Vérifier les chemins sensibles
        for sensitive_path in self.sensitive_paths:
            if sensitive_path in command:
                issues.append(f"Chemin sensible détecté: {sensitive_path}")
        
        # Vérifier les caractères suspects
        suspicious_chars = [";", "&&", "||", "`", "$", ">", "<", "|", "&"]
        for char in suspicious_chars:
            if char in command:
                issues.append(f"Caractère suspect détecté: {char}")
        
        # Vérifier les commandes autorisées
        allowed_commands = ["ls", "cat", "grep", "find", "echo", "pwd", "whoami", "ps", "netstat", "ifconfig", "ip"]
        command_base = command.split()[0] if command.split() else ""
        
        if command_base and command_base not in allowed_commands:
            issues.append(f"Commande non autorisée: {command_base}")
        
        # Décision finale
        is_safe = len(issues) == 0
        
        return {
            "is_safe": is_safe,
            "reason": issues[0] if issues else "Commande sécurisée",
            "details": issues
        }
    
    def _analyze_sql_query_safety(self, query: str) -> Dict[str, Any]:
        """
        Analyse la sécurité d'une requête SQL.
        
        Args:
            query: Requête SQL à analyser
            
        Returns:
            Dict[str, Any]: Résultat de l'analyse de sécurité
        """
        query_upper = query.upper()
        issues = []
        
        # Vérifier les opérations dangereuses
        dangerous_operations = ["DROP", "DELETE", "TRUNCATE", "ALTER", "UPDATE", "INSERT INTO"]
        for operation in dangerous_operations:
            if operation in query_upper:
                issues.append(f"Opération SQL dangereuse détectée: {operation}")
        
        # Vérifier les injections SQL potentielles
        suspicious_patterns = [
            "--", "/*", "*/", "UNION", "OR 1=1", "' OR '", "\" OR \"",
            "OR 'a'='a", "OR \"a\"=\"a", "SLEEP(", "BENCHMARK(", "WAITFOR DELAY"
        ]
        for pattern in suspicious_patterns:
            if pattern in query_upper:
                issues.append(f"Motif d'injection SQL potentiel détecté: {pattern}")
        
        # Décision finale
        is_safe = len(issues) == 0 or query_upper.startswith(("SELECT", "PRAGMA", "EXPLAIN", "ANALYZE"))
        
        return {
            "is_safe": is_safe,
            "reason": issues[0] if issues else "Requête SQL sécurisée",
            "details": issues
        }
    
    def _analyze_python_code_safety(self, code: str) -> Dict[str, Any]:
        """
        Analyse la sécurité du code Python.
        
        Args:
            code: Code Python à analyser
            
        Returns:
            Dict[str, Any]: Résultat de l'analyse de sécurité
        """
        issues = []
        
        # Vérifier les imports dangereux
        dangerous_imports = [
            "os", "sys", "subprocess", "shutil", "pathlib", "glob",
            "pickle", "shelve", "marshal", "socket", "requests"
        ]
        
        import_pattern = re.compile(r"(?:from|import)\s+(\w+)")
        for match in import_pattern.finditer(code):
            module = match.group(1)
            if module in dangerous_imports:
                issues.append(f"Import de module dangereux détecté: {module}")
        
        # Vérifier les fonctions dangereuses
        dangerous_functions = [
            "eval", "exec", "compile", "open", "file", "input",
            "__import__", "globals", "locals", "getattr", "setattr"
        ]
        
        for func in dangerous_functions:
            if re.search(r"\b" + func + r"\s*\(", code):
                issues.append(f"Fonction dangereuse détectée: {func}")
        
        # Décision finale
        is_safe = len(issues) == 0
        
        return {
            "is_safe": is_safe,
            "reason": issues[0] if issues else "Code Python sécurisé",
            "details": issues
        } 