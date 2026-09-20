from rs_collector.exceptions.base import RsCollectorError


class ConfigurationError(RsCollectorError):
    pass


class ConfigFileNotFoundError(ConfigurationError):
    pass


class ConfigFileFormatError(ConfigurationError):
    pass


class ConfigValidationError(ConfigurationError):
    pass


class MissingCredentialsError(ConfigurationError):
    pass
