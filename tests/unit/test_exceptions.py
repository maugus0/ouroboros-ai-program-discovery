"""Unit tests for custom exceptions."""

from app.utils.exceptions import (
    DatabaseError,
    NotFoundError,
    ProgramDiscoveryBaseError,
    ServiceAuthError,
    ValidationError,
)


class TestExceptions:
    """Tests for custom exceptions."""

    def test_base_error(self):
        """Test base error with default values."""
        error = ProgramDiscoveryBaseError()
        assert error.message == "An unexpected error occurred"
        assert error.status_code == 500

    def test_base_error_custom(self):
        """Test base error with custom values."""
        error = ProgramDiscoveryBaseError("Custom error", 400)
        assert error.message == "Custom error"
        assert error.status_code == 400

    def test_database_error(self):
        """Test database error."""
        error = DatabaseError("Connection failed")
        assert error.message == "Connection failed"
        assert error.status_code == 500

    def test_not_found_error(self):
        """Test not found error."""
        error = NotFoundError("Institution")
        assert error.message == "Institution not found"
        assert error.status_code == 404

    def test_validation_error(self):
        """Test validation error."""
        error = ValidationError("Invalid field")
        assert error.message == "Invalid field"
        assert error.status_code == 422

    def test_service_auth_error(self):
        """Test service auth error."""
        error = ServiceAuthError()
        assert error.message == "Service authentication failed"
        assert error.status_code == 401

    def test_exception_inheritance(self):
        """Test that all errors inherit from base."""
        assert issubclass(DatabaseError, ProgramDiscoveryBaseError)
        assert issubclass(NotFoundError, ProgramDiscoveryBaseError)
        assert issubclass(ValidationError, ProgramDiscoveryBaseError)
        assert issubclass(ServiceAuthError, ProgramDiscoveryBaseError)
