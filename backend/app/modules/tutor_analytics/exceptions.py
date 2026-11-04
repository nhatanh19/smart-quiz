"""Custom exceptions for the Auto-Grading Engine and Tutor Analytics module."""


class GradingError(Exception):
    """Base exception for all grading related errors."""
    pass


class NotFoundError(GradingError):
    """Raised when an attempt, exam, or question is not found."""
    pass


class InvalidAttemptStateError(GradingError):
    """Raised when an attempt is in an invalid state for grading."""
    pass


class SnapshotMismatchError(GradingError):
    """Raised when answer question IDs do not match the attempt snapshot (K-02)."""
    pass
