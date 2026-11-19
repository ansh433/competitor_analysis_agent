class DomainError(Exception):
    """Base error raised by domain services."""

    code = "domain_error"
    status_code = 400


class ResourceNotFoundError(DomainError):
    code = "resource_not_found"
    status_code = 404


class ResourceConflictError(DomainError):
    code = "resource_conflict"
    status_code = 409


class PermissionDeniedError(DomainError):
    code = "permission_denied"
    status_code = 403


class AuthenticationError(DomainError):
    code = "authentication_required"
    status_code = 401


class QuotaExceededError(DomainError):
    code = "quota_exceeded"
    status_code = 429


class ExternalProviderError(DomainError):
    code = "external_provider_error"
    status_code = 503


class RetryableExternalProviderError(ExternalProviderError):
    code = "retryable_external_provider_error"
