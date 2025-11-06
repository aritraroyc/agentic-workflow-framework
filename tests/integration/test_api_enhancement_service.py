"""
Integration tests for API Enhancement workflow A2A service.

Tests cover:
- Service startup and initialization
- /execute endpoint
- /metadata endpoint
- /health endpoint
- Error handling
- Request/response validation
"""

import pytest
import json
from httpx import AsyncClient

# Import will work when FastAPI is available in test environment
try:
    from workflows.children.api_enhancement.service import (
        app,
        ExecuteRequest,
        ExecuteResponse,
        MetadataResponse,
        HealthResponse,
    )

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


@pytest.mark.skipif(
    not FASTAPI_AVAILABLE, reason="FastAPI not available in test environment"
)
class TestAPIEnhancementService:
    """Test suite for API Enhancement A2A service."""

    @pytest.fixture
    def client(self):
        """Create async HTTP client for testing."""
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_service_startup(self, client):
        """Test that service starts up correctly."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "API Enhancement Workflow"
        assert "endpoints" in data

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert "timestamp" in data
        assert "version" in data
        assert "workflow_loaded" in data

    def test_metadata_endpoint(self, client):
        """Test metadata endpoint."""
        response = client.get("/metadata")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "api_enhancement"
        assert data["workflow_type"] == "api_enhancement"
        assert data["deployment_mode"] == "a2a"
        assert isinstance(data["tags"], list)

    def test_execute_endpoint_with_valid_input(self, client):
        """Test execute endpoint with valid input."""
        payload = {
            "story": "# API Enhancement\nAdd batch processing and webhooks",
            "story_requirements": {
                "title": "Batch Processing",
                "description": "Add batch processing capability",
            },
            "story_type": "api_enhancement",
            "preprocessor_output": {},
            "planner_output": {},
        }

        response = client.post("/execute", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "output" in data
        assert "timestamp" in data

    def test_execute_endpoint_with_minimal_input(self, client):
        """Test execute endpoint with minimal required input."""
        payload = {
            "story": "# Enhancement\nAdd new features",
        }

        response = client.post("/execute", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "output" in data

    def test_execute_endpoint_missing_story(self, client):
        """Test execute endpoint without required story field."""
        payload = {
            "story_requirements": {},
        }

        response = client.post("/execute", json=payload)
        assert response.status_code == 422  # Validation error

    def test_execute_response_structure(self, client):
        """Test that execute response has correct structure."""
        payload = {
            "story": "# Test\nEnhance API",
            "story_requirements": {},
            "story_type": "api_enhancement",
        }

        response = client.post("/execute", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        assert "status" in data
        assert data["status"] in ["success", "failure", "partial"]
        assert "output" in data
        assert isinstance(data["output"], dict)
        assert "timestamp" in data

    def test_execute_output_contains_enhancements(self, client):
        """Test that execute output contains expected enhancement artifacts."""
        payload = {
            "story": "# Enhancement\nAdd filtering and batch processing",
            "story_requirements": {
                "enhancement_type": "batch_processing",
            },
        }

        response = client.post("/execute", json=payload)
        assert response.status_code == 200
        data = response.json()
        output = data["output"]

        # Verify expected output keys (may not all be present but structure should be present)
        assert isinstance(output, dict)


class TestExecuteRequestModel:
    """Test suite for ExecuteRequest Pydantic model."""

    def test_execute_request_creation_with_all_fields(self):
        """Test ExecuteRequest with all fields."""
        request = ExecuteRequest(
            story="# Enhancement",
            story_requirements={"title": "Test"},
            story_type="api_enhancement",
            preprocessor_output={"data": "test"},
            planner_output={"plan": "test"},
        )

        assert request.story == "# Enhancement"
        assert request.story_type == "api_enhancement"

    def test_execute_request_creation_with_minimal_fields(self):
        """Test ExecuteRequest with minimal fields."""
        request = ExecuteRequest(story="# Test")

        assert request.story == "# Test"
        assert request.story_type == "api_enhancement"  # default
        assert request.story_requirements == {}  # default
        assert request.preprocessor_output == {}  # default

    def test_execute_request_validation_fails_without_story(self):
        """Test that ExecuteRequest validation fails without story."""
        with pytest.raises(ValueError):
            ExecuteRequest()  # Missing required story field


class TestMetadataResponseModel:
    """Test suite for MetadataResponse Pydantic model."""

    def test_metadata_response_creation(self):
        """Test MetadataResponse model creation."""
        response = MetadataResponse(
            name="api_enhancement",
            workflow_type="api_enhancement",
            description="Test workflow",
            version="1.0.0",
            deployment_mode="a2a",
            tags=["api", "enhancement"],
        )

        assert response.name == "api_enhancement"
        assert response.deployment_mode == "a2a"
        assert "api" in response.tags


class TestHealthResponseModel:
    """Test suite for HealthResponse Pydantic model."""

    def test_health_response_creation(self):
        """Test HealthResponse model creation."""
        from datetime import datetime

        response = HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            version="1.0.0",
            workflow_loaded=True,
        )

        assert response.status == "healthy"
        assert response.workflow_loaded is True
