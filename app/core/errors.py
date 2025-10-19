# app/core/errors.py
class ServiceError(Exception):
    """Base exception for service layer errors."""

    pass


class NotFoundError(ServiceError):
    """Exception raised when a resource is not found."""

    pass


class ConflictError(ServiceError):
    """Exception raised when there is a conflict in the current state."""

    pass


class UnauthorizedError(ServiceError):
    """Exception raised when the user is not authorized."""

    pass


class ForbiddenError(ServiceError):
    """Exception raised when the action is forbidden."""

    pass


class ValidationDomainError(ServiceError):
    """Exception raised when domain validation fails."""

    pass
