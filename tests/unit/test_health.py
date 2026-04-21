"""Unit tests for the health endpoint."""

from app.config import APP_VERSION


class TestHealthEndpoint:
    """Tests for the health endpoint."""

    def test_health_check_structure(self):
        """Test that health response has expected structure."""
        from datetime import datetime

        from app.models import HealthResponse

        response = HealthResponse(
            status="healthy",
            version=APP_VERSION,
            database="connected",
            timestamp=datetime.utcnow(),
        )

        assert response.status == "healthy"
        assert response.version == APP_VERSION
        assert response.database == "connected"
        assert response.timestamp is not None

    def test_health_check_degraded(self):
        """Test degraded health response."""
        from datetime import datetime

        from app.models import HealthResponse

        response = HealthResponse(
            status="degraded",
            version=APP_VERSION,
            database="disconnected",
            timestamp=datetime.utcnow(),
        )

        assert response.status == "degraded"
        assert response.database == "disconnected"
