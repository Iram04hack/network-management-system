"""
Tests unitaires pour les validateurs d'entrée.

Ces tests couvrent tous les validateurs sécurisés avec scénarios
d'injection, validation, normalisation et performance.
"""

import pytest
import ipaddress
from datetime import datetime
import re

from api_clients.infrastructure.input_validator import (
    StringValidator,
    URLValidator,
    QueryValidator,
    IPAddressValidator,
    TimestampValidator,
    PortValidator,
    CompositeValidator,
    ValidationException
)


class TestStringValidator:
    """Tests pour le validateur de chaînes."""
    
    def test_string_validator_basic(self):
        """Test la validation de base des chaînes."""
        validator = StringValidator(min_length=2, max_length=10)
        
        # Validation réussie
        assert validator.validate("hello") == "hello"
        assert validator.validate("ab") == "ab"
        assert validator.validate("1234567890") == "1234567890"
        
        # Validation échouée
        with pytest.raises(ValidationException):
            validator.validate("a")  # Trop court
        
        with pytest.raises(ValidationException):
            validator.validate("12345678901")  # Trop long
        
        with pytest.raises(ValidationException):
            validator.validate(None)  # None
        
        with pytest.raises(ValidationException):
            validator.validate(123)  # Pas une chaîne
    
    def test_string_validator_pattern(self):
        """Test la validation avec motif regex."""
        # Validateur pour noms d'utilisateur (lettres, chiffres, tirets)
        validator = StringValidator(
            min_length=3,
            max_length=20,
            pattern=re.compile(r'^[a-zA-Z0-9\-_]+$')
        )
        
        # Valides
        assert validator.validate("user123") == "user123"
        assert validator.validate("test_user") == "test_user"
        assert validator.validate("admin-2024") == "admin-2024"
        
        # Invalides
        with pytest.raises(ValidationException):
            validator.validate("user@domain")  # Caractère interdit
        
        with pytest.raises(ValidationException):
            validator.validate("user name")  # Espace
        
        with pytest.raises(ValidationException):
            validator.validate("user#123")  # Caractère spécial
    
    def test_string_validator_forbidden_chars(self):
        """Test la validation avec caractères interdits."""
        validator = StringValidator(
            min_length=1,
            max_length=50,
            forbidden_chars='"<>&\n\r\t'
        )
        
        # Valides
        assert validator.validate("safe string") == "safe string"
        assert validator.validate("normal_text123") == "normal_text123"
        
        # Invalides
        with pytest.raises(ValidationException):
            validator.validate('text with "quotes"')  # Guillemets
        
        with pytest.raises(ValidationException):
            validator.validate("text with <script>")  # Balises HTML
        
        with pytest.raises(ValidationException):
            validator.validate("text with &amp;")  # Entités HTML
        
        with pytest.raises(ValidationException):
            validator.validate("text with\nnewline")  # Retour à la ligne
    
    def test_string_validator_whitespace_handling(self):
        """Test la gestion des espaces."""
        # Avec suppression des espaces
        validator_strip = StringValidator(
            min_length=3,
            max_length=10,
            strip_whitespace=True
        )
        
        assert validator_strip.validate("  hello  ") == "hello"
        assert validator_strip.validate("\ttest\n") == "test"
        
        # Sans suppression des espaces
        validator_no_strip = StringValidator(
            min_length=3,
            max_length=10,
            strip_whitespace=False
        )
        
        assert validator_no_strip.validate("  hello  ") == "  hello  "
        
        # Validation avec espaces supprimés mais résultat trop court
        with pytest.raises(ValidationException):
            validator_strip.validate("  a  ")  # Devient "a" après strip
    
    def test_string_validator_injection_protection(self):
        """Test la protection contre les injections."""
        validator = StringValidator(
            min_length=1,
            max_length=100,
            forbidden_chars='"\';<>&\n\r\t',
            pattern=re.compile(r'^[a-zA-Z0-9\s\-_\.]+$')
        )
        
        # Tentatives d'injection SQL
        with pytest.raises(ValidationException):
            validator.validate("'; DROP TABLE users; --")
        
        with pytest.raises(ValidationException):
            validator.validate("' OR '1'='1")
        
        # Tentatives d'injection XSS
        with pytest.raises(ValidationException):
            validator.validate("<script>alert('xss')</script>")
        
        with pytest.raises(ValidationException):
            validator.validate("javascript:alert(1)")
        
        # Tentatives d'injection de commandes
        with pytest.raises(ValidationException):
            validator.validate("test; rm -rf /")
        
        with pytest.raises(ValidationException):
            validator.validate("test && echo 'pwned'")


class TestURLValidator:
    """Tests pour le validateur d'URL."""
    
    def test_url_validator_basic(self):
        """Test la validation de base des URL."""
        validator = URLValidator(
            allowed_schemes=['http', 'https'],
            allow_localhost=True
        )
        
        # URLs valides
        assert validator.validate("https://example.com") == "https://example.com"
        assert validator.validate("http://localhost:8080") == "http://localhost:8080"
        assert validator.validate("https://sub.domain.com/path") == "https://sub.domain.com/path"
        
        # URLs invalides
        with pytest.raises(ValidationException):
            validator.validate("ftp://example.com")  # Schéma non autorisé
        
        with pytest.raises(ValidationException):
            validator.validate("not_a_url")  # Pas une URL
        
        with pytest.raises(ValidationException):
            validator.validate("https://")  # URL incomplète
    
    def test_url_validator_localhost_restriction(self):
        """Test la restriction localhost."""
        validator_no_localhost = URLValidator(
            allowed_schemes=['http', 'https'],
            allow_localhost=False
        )
        
        # Valide
        assert validator_no_localhost.validate("https://example.com") == "https://example.com"
        
        # Invalides
        with pytest.raises(ValidationException):
            validator_no_localhost.validate("http://localhost")
        
        with pytest.raises(ValidationException):
            validator_no_localhost.validate("https://127.0.0.1")
        
        with pytest.raises(ValidationException):
            validator_no_localhost.validate("http://::1")  # IPv6 localhost
    
    def test_url_validator_private_ip_restriction(self):
        """Test la restriction des IP privées."""
        validator = URLValidator(
            allowed_schemes=['http', 'https'],
            allow_private_ips=False
        )
        
        # Valide
        assert validator.validate("https://8.8.8.8") == "https://8.8.8.8"
        
        # Invalides
        with pytest.raises(ValidationException):
            validator.validate("http://192.168.1.1")  # IP privée
        
        with pytest.raises(ValidationException):
            validator.validate("https://10.0.0.1")  # IP privée
        
        with pytest.raises(ValidationException):
            validator.validate("http://172.16.0.1")  # IP privée
    
    def test_url_validator_max_length(self):
        """Test la limitation de longueur d'URL."""
        validator = URLValidator(max_length=50)
        
        # Valide
        short_url = "https://example.com"
        assert validator.validate(short_url) == short_url
        
        # Invalide
        long_url = "https://example.com/" + "a" * 100
        with pytest.raises(ValidationException):
            validator.validate(long_url)
    
    def test_url_validator_normalization(self):
        """Test la normalisation d'URL."""
        validator = URLValidator(normalize=True)
        
        # Normalisation des schémas
        assert validator.validate("HTTP://EXAMPLE.COM") == "http://example.com"
        assert validator.validate("https://Example.Com/PATH") == "https://example.com/PATH"
        
        # Suppression du port par défaut
        assert validator.validate("https://example.com:443/path") == "https://example.com/path"
        assert validator.validate("http://example.com:80/path") == "http://example.com/path"


class TestQueryValidator:
    """Tests pour le validateur de requêtes."""
    
    def test_query_validator_basic(self):
        """Test la validation de base des requêtes."""
        validator = QueryValidator(max_length=100)
        
        # Valides
        assert validator.validate("SELECT * FROM users") == "SELECT * FROM users"
        assert validator.validate("user search") == "user search"
        
        # Invalide - trop long
        long_query = "A" * 150
        with pytest.raises(ValidationException):
            validator.validate(long_query)
    
    def test_query_validator_injection_protection(self):
        """Test la protection contre les injections."""
        validator = QueryValidator()
        
        # Tentatives d'injection SQL
        with pytest.raises(ValidationException):
            validator.validate("'; DROP TABLE users; --")
        
        with pytest.raises(ValidationException):
            validator.validate("' UNION SELECT password FROM users --")
        
        with pytest.raises(ValidationException):
            validator.validate("1' OR '1'='1")
        
        # Tentatives NoSQL injection
        with pytest.raises(ValidationException):
            validator.validate("'; return true; //")
        
        # Tentatives LDAP injection
        with pytest.raises(ValidationException):
            validator.validate("*)(|(objectClass=*))")
    
    def test_query_validator_special_chars(self):
        """Test la gestion des caractères spéciaux."""
        validator = QueryValidator()
        
        # Caractères dangereux
        dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'sp_', '@@']
        
        for char in dangerous_chars:
            with pytest.raises(ValidationException):
                validator.validate(f"test {char} query")
    
    def test_query_validator_normalization(self):
        """Test la normalisation des requêtes."""
        validator = QueryValidator(normalize=True)
        
        # Normalisation des espaces
        assert validator.validate("  test   query  ") == "test query"
        assert validator.validate("test\t\nquery") == "test query"


class TestIPAddressValidator:
    """Tests pour le validateur d'adresses IP."""
    
    def test_ip_validator_ipv4(self):
        """Test la validation IPv4."""
        validator = IPAddressValidator(allow_ipv4=True, allow_ipv6=False)
        
        # Valides
        assert validator.validate("192.168.1.1") == "192.168.1.1"
        assert validator.validate("8.8.8.8") == "8.8.8.8"
        assert validator.validate("127.0.0.1") == "127.0.0.1"
        
        # Invalides
        with pytest.raises(ValidationException):
            validator.validate("2001:db8::1")  # IPv6 non autorisé
        
        with pytest.raises(ValidationException):
            validator.validate("256.1.1.1")  # IP invalide
        
        with pytest.raises(ValidationException):
            validator.validate("not.an.ip")  # Pas une IP
    
    def test_ip_validator_ipv6(self):
        """Test la validation IPv6."""
        validator = IPAddressValidator(allow_ipv4=False, allow_ipv6=True)
        
        # Valides
        assert validator.validate("2001:db8::1") == "2001:db8::1"
        assert validator.validate("::1") == "::1"
        assert validator.validate("fe80::1%lo0") == "fe80::1%lo0"
        
        # Invalides
        with pytest.raises(ValidationException):
            validator.validate("192.168.1.1")  # IPv4 non autorisé
    
    def test_ip_validator_private_restriction(self):
        """Test la restriction des IP privées."""
        validator = IPAddressValidator(allow_private=False)
        
        # Valides (publiques)
        assert validator.validate("8.8.8.8") == "8.8.8.8"
        assert validator.validate("1.1.1.1") == "1.1.1.1"
        
        # Invalides (privées)
        with pytest.raises(ValidationException):
            validator.validate("192.168.1.1")
        
        with pytest.raises(ValidationException):
            validator.validate("10.0.0.1")
        
        with pytest.raises(ValidationException):
            validator.validate("172.16.0.1")
        
        with pytest.raises(ValidationException):
            validator.validate("127.0.0.1")  # Loopback
    
    def test_ip_validator_reserved_restriction(self):
        """Test la restriction des IP réservées."""
        validator = IPAddressValidator(allow_reserved=False)
        
        # Valides
        assert validator.validate("8.8.8.8") == "8.8.8.8"
        
        # Invalides (réservées)
        with pytest.raises(ValidationException):
            validator.validate("0.0.0.0")
        
        with pytest.raises(ValidationException):
            validator.validate("255.255.255.255")
    
    def test_ip_validator_multicast_restriction(self):
        """Test la restriction des IP multicast."""
        validator = IPAddressValidator(allow_multicast=False)
        
        # Valides
        assert validator.validate("8.8.8.8") == "8.8.8.8"
        
        # Invalides (multicast)
        with pytest.raises(ValidationException):
            validator.validate("224.0.0.1")  # IPv4 multicast
        
        with pytest.raises(ValidationException):
            validator.validate("ff02::1")  # IPv6 multicast


class TestTimestampValidator:
    """Tests pour le validateur de timestamps."""
    
    def test_timestamp_validator_unix(self):
        """Test la validation des timestamps Unix."""
        validator = TimestampValidator()
        
        # Valides
        current_timestamp = 1640995200  # 2022-01-01 00:00:00 UTC
        assert validator.validate(current_timestamp) == current_timestamp
        assert validator.validate("1640995200") == 1640995200
        
        # Invalides
        with pytest.raises(ValidationException):
            validator.validate(-1)  # Timestamp négatif
        
        with pytest.raises(ValidationException):
            validator.validate(4102444800)  # Trop dans le futur (2100)
    
    def test_timestamp_validator_iso_format(self):
        """Test la validation des timestamps ISO."""
        validator = TimestampValidator()
        
        # Valides
        iso_timestamp = "2022-01-01T00:00:00Z"
        result = validator.validate(iso_timestamp)
        assert isinstance(result, str)
        assert "2022-01-01" in result
        
        iso_with_tz = "2022-01-01T00:00:00+01:00"
        result = validator.validate(iso_with_tz)
        assert isinstance(result, str)
        
        # Invalides
        with pytest.raises(ValidationException):
            validator.validate("not-a-date")
        
        with pytest.raises(ValidationException):
            validator.validate("2022-13-01T00:00:00Z")  # Mois invalide
    
    def test_timestamp_validator_datetime_object(self):
        """Test la validation des objets datetime."""
        validator = TimestampValidator()
        
        # Valide
        dt = datetime(2022, 1, 1, 0, 0, 0)
        result = validator.validate(dt)
        assert isinstance(result, str)
        assert "2022-01-01" in result
    
    def test_timestamp_validator_range_validation(self):
        """Test la validation de plage temporelle."""
        validator = TimestampValidator(
            min_timestamp=1640995200,  # 2022-01-01
            max_timestamp=1672531200   # 2023-01-01
        )
        
        # Valide
        valid_timestamp = 1641081600  # 2022-01-02
        assert validator.validate(valid_timestamp) == valid_timestamp
        
        # Invalides
        with pytest.raises(ValidationException):
            validator.validate(1609459200)  # 2021-01-01 (trop ancien)
        
        with pytest.raises(ValidationException):
            validator.validate(1704067200)  # 2024-01-01 (trop récent)


class TestPortValidator:
    """Tests pour le validateur de ports."""
    
    def test_port_validator_basic(self):
        """Test la validation de base des ports."""
        validator = PortValidator()
        
        # Valides
        assert validator.validate(80) == 80
        assert validator.validate("443") == 443
        assert validator.validate(8080) == 8080
        
        # Invalides
        with pytest.raises(ValidationException):
            validator.validate(0)  # Port 0
        
        with pytest.raises(ValidationException):
            validator.validate(65536)  # Port trop élevé
        
        with pytest.raises(ValidationException):
            validator.validate(-1)  # Port négatif
        
        with pytest.raises(ValidationException):
            validator.validate("not_a_port")  # Pas un nombre
    
    def test_port_validator_range_restriction(self):
        """Test la restriction de plage de ports."""
        # Seulement ports non-privilégiés
        validator = PortValidator(min_port=1024, max_port=65535)
        
        # Valides
        assert validator.validate(8080) == 8080
        assert validator.validate(1024) == 1024
        
        # Invalides
        with pytest.raises(ValidationException):
            validator.validate(80)  # Port privilégié
        
        with pytest.raises(ValidationException):
            validator.validate(22)  # Port privilégié
    
    def test_port_validator_reserved_restriction(self):
        """Test la restriction des ports réservés."""
        validator = PortValidator(allow_reserved=False)
        
        # Valides
        assert validator.validate(8080) == 8080
        assert validator.validate(3000) == 3000
        
        # Invalides (ports réservés/bien connus)
        reserved_ports = [22, 23, 25, 53, 80, 110, 143, 443, 993, 995]
        for port in reserved_ports:
            with pytest.raises(ValidationException):
                validator.validate(port)


class TestCompositeValidator:
    """Tests pour le validateur composite."""
    
    def test_composite_validator_basic(self):
        """Test la validation composite de base."""
        validators = {
            'username': StringValidator(min_length=3, max_length=20, pattern=re.compile(r'^[a-zA-Z0-9_]+$')),
            'email': StringValidator(min_length=5, max_length=100),  # Simplified email validation
            'port': PortValidator(min_port=1000, max_port=9999)
        }
        
        composite = CompositeValidator(validators)
        
        # Validation réussie
        data = {
            'username': 'test_user',
            'email': 'test@example.com',
            'port': 8080
        }
        
        validated = composite.validate(data)
        assert validated['username'] == 'test_user'
        assert validated['email'] == 'test@example.com'
        assert validated['port'] == 8080
        
        # Validation échouée
        invalid_data = {
            'username': 'a',  # Trop court
            'email': 'test@example.com',
            'port': 8080
        }
        
        with pytest.raises(ValidationException):
            composite.validate(invalid_data)
    
    def test_composite_validator_partial_validation(self):
        """Test la validation partielle."""
        validators = {
            'field1': StringValidator(min_length=3),
            'field2': StringValidator(min_length=5),
            'field3': PortValidator()
        }
        
        composite = CompositeValidator(validators)
        
        # Validation avec seulement certains champs
        partial_data = {
            'field1': 'test',
            'field3': 8080
            # field2 manquant
        }
        
        validated = composite.validate(partial_data)
        assert 'field1' in validated
        assert 'field3' in validated
        assert 'field2' not in validated
    
    def test_composite_validator_nested(self):
        """Test la validation composite imbriquée."""
        user_validators = {
            'name': StringValidator(min_length=2, max_length=50),
            'age': StringValidator(pattern=re.compile(r'^\d+$'))  # Simple age validation
        }
        
        address_validators = {
            'street': StringValidator(min_length=5, max_length=100),
            'city': StringValidator(min_length=2, max_length=50)
        }
        
        main_validators = {
            'user': CompositeValidator(user_validators),
            'address': CompositeValidator(address_validators)
        }
        
        composite = CompositeValidator(main_validators)
        
        # Cette fonctionnalité nécessiterait une extension du CompositeValidator
        # pour supporter la validation imbriquée
        # Pour l'instant, on teste avec une structure plate
        
        flat_data = {
            'user_name': 'John Doe',
            'user_age': '25',
            'address_street': '123 Main St',
            'address_city': 'Anytown'
        }
        
        flat_validators = {
            'user_name': StringValidator(min_length=2, max_length=50),
            'user_age': StringValidator(pattern=re.compile(r'^\d+$')),
            'address_street': StringValidator(min_length=5, max_length=100),
            'address_city': StringValidator(min_length=2, max_length=50)
        }
        
        flat_composite = CompositeValidator(flat_validators)
        validated = flat_composite.validate(flat_data)
        
        assert len(validated) == 4
        assert validated['user_name'] == 'John Doe'
    
    def test_composite_validator_error_aggregation(self):
        """Test l'agrégation d'erreurs."""
        validators = {
            'field1': StringValidator(min_length=10),  # Échouera
            'field2': PortValidator(min_port=1000),    # Échouera
            'field3': StringValidator(min_length=2)    # Réussira
        }
        
        composite = CompositeValidator(validators)
        
        invalid_data = {
            'field1': 'short',  # Trop court
            'field2': 80,       # Port trop petit
            'field3': 'ok'      # Valide
        }
        
        # Le validateur composite devrait lever une exception
        # avec des détails sur tous les champs invalides
        with pytest.raises(ValidationException) as exc_info:
            composite.validate(invalid_data)
        
        # L'exception devrait contenir des informations sur les champs échoués
        error_message = str(exc_info.value)
        assert "field1" in error_message or "field2" in error_message


class TestValidatorPerformance:
    """Tests de performance pour les validateurs."""
    
    @pytest.mark.performance
    def test_string_validator_performance(self):
        """Test de performance du validateur de chaînes."""
        import time
        
        validator = StringValidator(
            min_length=1,
            max_length=100,
            pattern=re.compile(r'^[a-zA-Z0-9\s\-_]+$'),
            forbidden_chars='<>&"'
        )
        
        test_strings = [f"test_string_{i}" for i in range(1000)]
        
        start_time = time.time()
        for test_string in test_strings:
            validator.validate(test_string)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # La validation ne devrait pas être trop lente
        assert execution_time < 0.1  # Moins de 100ms pour 1000 validations
    
    @pytest.mark.performance
    def test_composite_validator_performance(self):
        """Test de performance du validateur composite."""
        import time
        
        validators = {
            'string_field': StringValidator(min_length=3, max_length=50),
            'ip_field': IPAddressValidator(),
            'port_field': PortValidator(),
            'url_field': URLValidator()
        }
        
        composite = CompositeValidator(validators)
        
        test_data = {
            'string_field': 'test_value',
            'ip_field': '192.168.1.1',
            'port_field': 8080,
            'url_field': 'https://example.com'
        }
        
        start_time = time.time()
        for _ in range(100):
            composite.validate(test_data)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # La validation composite ne devrait pas être trop lente
        assert execution_time < 0.05  # Moins de 50ms pour 100 validations


class TestValidatorIntegration:
    """Tests d'intégration pour les validateurs."""
    
    def test_real_world_user_registration(self):
        """Test simulation d'une validation de registration utilisateur."""
        registration_validators = {
            'username': StringValidator(
                min_length=3,
                max_length=20,
                pattern=re.compile(r'^[a-zA-Z0-9_]+$'),
                forbidden_chars='<>&"'
            ),
            'email': StringValidator(
                min_length=5,
                max_length=100,
                pattern=re.compile(r'^[^@]+@[^@]+\.[^@]+$')  # Simplified email regex
            ),
            'website': URLValidator(
                allowed_schemes=['http', 'https'],
                allow_localhost=False,
                max_length=200
            ),
            'port': PortValidator(
                min_port=1024,
                max_port=65535,
                allow_reserved=False
            )
        }
        
        validator = CompositeValidator(registration_validators)
        
        # Données valides
        valid_data = {
            'username': 'john_doe_2024',
            'email': 'john@example.com',
            'website': 'https://johndoe.com',
            'port': 8080
        }
        
        validated = validator.validate(valid_data)
        assert len(validated) == 4
        
        # Données avec tentatives d'injection
        malicious_data = {
            'username': '<script>alert("xss")</script>',
            'email': 'test"; DROP TABLE users; --@evil.com',
            'website': 'javascript:alert(1)',
            'port': 22  # Port réservé
        }
        
        # Toutes les validations devraient échouer
        with pytest.raises(ValidationException):
            validator.validate(malicious_data)
    
    def test_api_parameter_validation(self):
        """Test simulation de validation de paramètres API."""
        api_validators = {
            'query': QueryValidator(max_length=200),
            'limit': StringValidator(pattern=re.compile(r'^\d+$')),  # Number as string
            'offset': StringValidator(pattern=re.compile(r'^\d+$')),
            'sort_by': StringValidator(
                pattern=re.compile(r'^[a-zA-Z_]+$'),
                max_length=50
            ),
            'client_ip': IPAddressValidator(allow_private=False)
        }
        
        validator = CompositeValidator(api_validators)
        
        # Paramètres valides
        valid_params = {
            'query': 'search term',
            'limit': '100',
            'offset': '0',
            'sort_by': 'created_at',
            'client_ip': '8.8.8.8'
        }
        
        validated = validator.validate(valid_params)
        assert validated['query'] == 'search term'
        assert validated['limit'] == '100'
        
        # Paramètres avec tentatives d'injection
        malicious_params = {
            'query': "'; DROP TABLE data; --",
            'limit': '-1 UNION SELECT password FROM users',
            'offset': '0; DELETE FROM logs;',
            'sort_by': '../../../etc/passwd',
            'client_ip': '192.168.1.1'  # IP privée
        }
        
        with pytest.raises(ValidationException):
            validator.validate(malicious_params) 