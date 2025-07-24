"""Exceptions spécifiques au domaine GNS3."""


class GNS3Exception(Exception):
    """Exception de base pour toutes les erreurs liées à GNS3."""
    pass


class GNS3Error(GNS3Exception):
    """Exception de base pour toutes les erreurs liées à GNS3."""
    pass


class GNS3ConnectionError(GNS3Exception):
    """Exception levée lors d'une erreur de connexion au serveur GNS3."""
    pass


class GNS3AuthenticationError(GNS3ConnectionError):
    """Exception levée lors d'une erreur d'authentification au serveur GNS3."""
    pass


class GNS3ProjectError(GNS3Exception):
    """Exception levée lors d'une erreur liée à un projet GNS3."""
    pass


class GNS3NodeError(GNS3Exception):
    """Exception levée lors d'une erreur liée à un nœud GNS3."""
    pass


class GNS3LinkError(GNS3Exception):
    """Exception levée lors d'une erreur liée à un lien GNS3."""
    pass


class GNS3ResourceNotFoundError(GNS3Exception):
    """Exception levée lorsqu'une ressource GNS3 n'est pas trouvée."""
    pass


class GNS3ValidationError(GNS3Exception):
    """Exception levée lors d'une erreur de validation des données GNS3."""
    pass


class GNS3TimeoutError(GNS3Exception):
    """Exception levée lors d'un timeout d'opération GNS3."""
    pass


class GNS3OperationError(GNS3Exception):
    """Exception levée lors d'une erreur d'opération GNS3."""
    pass


class GNS3RepositoryError(GNS3Exception):
    """Exception levée lors d'une erreur de repository GNS3."""
    pass


class GNS3ServerError(GNS3Exception):
    """Exception levée lors d'une erreur de serveur GNS3."""
    pass
