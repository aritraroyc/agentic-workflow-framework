"""
Unit tests for the Workflow Invoker.

Tests cover:
- Embedded workflow invocation
- A2A workflow invocation
- Lazy loading and caching
- Error handling and retries
- HTTP request handling
- Result validation
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

from workflows.registry.invoker import WorkflowInvoker
from workflows.registry.registry import WorkflowMetadata, DeploymentMode
from workflows.parent.state import create_initial_state
from workflows.children.api_development.workflow import ApiDevelopmentWorkflow


# ========== Test Fixtures ==========


@pytest.fixture
def invoker() -> WorkflowInvoker:
    """Create a WorkflowInvoker instance."""
    return WorkflowInvoker(default_timeout=10.0, default_retries=2)


@pytest.fixture
def embedded_workflow_metadata() -> WorkflowMetadata:
    """Create metadata for an embedded workflow."""
    return WorkflowMetadata(
        name="api_development",
        workflow_type="api_development",
        description="API Development workflow",
        version="1.0.0",
        deployment_mode=DeploymentMode.EMBEDDED,
        module_path="workflows.children.api_development.workflow",
    )


@pytest.fixture
def a2a_workflow_metadata() -> WorkflowMetadata:
    """Create metadata for an A2A workflow."""
    return WorkflowMetadata(
        name="ui_development",
        workflow_type="ui_development",
        description="UI Development service",
        version="1.0.0",
        deployment_mode=DeploymentMode.A2A,
        service_url="http://localhost:8000",
        service_port=8001,
    )


@pytest.fixture
def sample_parent_state() -> Dict[str, Any]:
    """Create a sample parent workflow state."""
    return create_initial_state("# Test Story\n\n## Story\nTest")


@pytest.fixture
def sample_workflow_result() -> Dict[str, Any]:
    """Create a sample workflow execution result."""
    return {
        "status": "success",
        "output": {"test": "data"},
        "artifacts": ["artifact1", "artifact2"],
        "execution_time_seconds": 1.5,
    }


# ========== Tests ==========


class TestWorkflowInvokerInstantiation:
    """Tests for WorkflowInvoker instantiation."""

    def test_invoker_can_be_instantiated(self, invoker) -> None:
        """Test that WorkflowInvoker can be instantiated."""
        assert invoker is not None
        assert invoker.default_timeout == 10.0
        assert invoker.default_retries == 2

    def test_invoker_with_custom_defaults(self) -> None:
        """Test creating invoker with custom defaults."""
        custom_invoker = WorkflowInvoker(
            default_timeout=30.0, default_retries=5
        )

        assert custom_invoker.default_timeout == 30.0
        assert custom_invoker.default_retries == 5


class TestEmbeddedWorkflowInvocation:
    """Tests for invoking embedded workflows."""

    @pytest.mark.asyncio
    async def test_invoke_embedded_workflow_success(
        self, invoker, embedded_workflow_metadata, sample_parent_state, sample_workflow_result
    ) -> None:
        """Test successful invocation of embedded workflow."""
        with patch.object(invoker, "_get_or_load_embedded_workflow") as mock_load:
            mock_workflow = AsyncMock()
            mock_workflow.execute = AsyncMock(return_value=sample_workflow_result)
            mock_load.return_value = mock_workflow

            result = await invoker.invoke(
                embedded_workflow_metadata, sample_parent_state
            )

            assert result is not None
            assert result["status"] == "success"
            assert result["workflow_name"] == "api_development"
            assert "output" in result
            assert "artifacts" in result
            assert "execution_time_seconds" in result

    @pytest.mark.asyncio
    async def test_invoke_embedded_workflow_timeout(
        self, invoker, embedded_workflow_metadata, sample_parent_state
    ) -> None:
        """Test timeout handling for embedded workflow."""
        with patch.object(invoker, "_get_or_load_embedded_workflow") as mock_load:
            mock_workflow = AsyncMock()
            mock_workflow.execute = AsyncMock(side_effect=TimeoutError())
            mock_load.return_value = mock_workflow

            result = await invoker.invoke(
                embedded_workflow_metadata,
                sample_parent_state,
                timeout=0.1,
                max_retries=1,
            )

            assert result["status"] == "failure"
            assert "timed out" in result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_invoke_embedded_workflow_with_retries(
        self, invoker, embedded_workflow_metadata, sample_parent_state, sample_workflow_result
    ) -> None:
        """Test retry logic for embedded workflow."""
        with patch.object(invoker, "_get_or_load_embedded_workflow") as mock_load:
            mock_workflow = AsyncMock()
            # Fail once, then succeed
            mock_workflow.execute = AsyncMock(
                side_effect=[
                    RuntimeError("First attempt failed"),
                    sample_workflow_result,
                ]
            )
            mock_load.return_value = mock_workflow

            result = await invoker.invoke(
                embedded_workflow_metadata,
                sample_parent_state,
                max_retries=3,
            )

            assert result["status"] == "success"
            assert mock_workflow.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_invoke_embedded_workflow_missing_module_path(
        self, invoker, sample_parent_state
    ) -> None:
        """Test error when module_path is missing."""
        # WorkflowMetadata validation raises error at creation time
        with pytest.raises(ValueError, match="module_path"):
            WorkflowMetadata(
                name="invalid",
                workflow_type="invalid",
                description="Invalid",
                version="1.0.0",
                deployment_mode=DeploymentMode.EMBEDDED,
                # module_path is required but missing
            )


class TestA2AWorkflowInvocation:
    """Tests for invoking A2A (remote service) workflows."""

    @pytest.mark.asyncio
    async def test_invoke_a2a_workflow_success(
        self, invoker, a2a_workflow_metadata, sample_parent_state, sample_workflow_result
    ) -> None:
        """Test successful invocation of A2A workflow."""
        with patch.object(invoker, "_make_http_request") as mock_http:
            mock_http.return_value = sample_workflow_result

            result = await invoker.invoke(
                a2a_workflow_metadata, sample_parent_state
            )

            assert result is not None
            assert result["status"] == "success"
            assert result["workflow_name"] == "ui_development"
            mock_http.assert_called_once()

    @pytest.mark.asyncio
    async def test_invoke_a2a_workflow_timeout(
        self, invoker, a2a_workflow_metadata, sample_parent_state
    ) -> None:
        """Test timeout handling for A2A workflow."""
        import asyncio

        with patch.object(invoker, "_make_http_request") as mock_http:
            mock_http.side_effect = asyncio.TimeoutError()

            result = await invoker.invoke(
                a2a_workflow_metadata,
                sample_parent_state,
                timeout=0.1,
                max_retries=1,
            )

            assert result["status"] == "failure"
            assert "timed out" in result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_invoke_a2a_workflow_with_retries(
        self, invoker, a2a_workflow_metadata, sample_parent_state, sample_workflow_result
    ) -> None:
        """Test retry logic for A2A workflow."""
        with patch.object(invoker, "_make_http_request") as mock_http:
            # Fail once, then succeed
            mock_http.side_effect = [
                RuntimeError("Service unavailable"),
                sample_workflow_result,
            ]

            result = await invoker.invoke(
                a2a_workflow_metadata,
                sample_parent_state,
                max_retries=3,
            )

            assert result["status"] == "success"
            assert mock_http.call_count == 2

    @pytest.mark.asyncio
    async def test_invoke_a2a_workflow_missing_service_url(
        self, invoker, sample_parent_state
    ) -> None:
        """Test error when service_url is missing."""
        # WorkflowMetadata validation raises error at creation time
        with pytest.raises(ValueError, match="service_url"):
            WorkflowMetadata(
                name="invalid",
                workflow_type="invalid",
                description="Invalid",
                version="1.0.0",
                deployment_mode=DeploymentMode.A2A,
                # service_url is required but missing
            )


class TestEmbeddedWorkflowLoading:
    """Tests for loading embedded workflows."""

    @pytest.mark.asyncio
    async def test_load_api_development_workflow(self, invoker) -> None:
        """Test loading the API development workflow."""
        module_path = "workflows.children.api_development.workflow"
        workflow = await invoker._get_or_load_embedded_workflow(
            module_path, "api_development"
        )

        assert workflow is not None
        assert isinstance(workflow, ApiDevelopmentWorkflow)

    @pytest.mark.asyncio
    async def test_load_workflow_caching(self, invoker) -> None:
        """Test that loaded workflows are cached."""
        module_path = "workflows.children.api_development.workflow"

        workflow1 = await invoker._get_or_load_embedded_workflow(
            module_path, "api_development"
        )
        workflow2 = await invoker._get_or_load_embedded_workflow(
            module_path, "api_development"
        )

        # Same instance should be returned from cache
        assert workflow1 is workflow2

    @pytest.mark.asyncio
    async def test_load_workflow_invalid_module(self, invoker) -> None:
        """Test error when module cannot be imported."""
        with pytest.raises(ImportError):
            await invoker._get_or_load_embedded_workflow(
                "invalid.module.path", "invalid"
            )

    @pytest.mark.asyncio
    async def test_infer_workflow_class_name(self, invoker) -> None:
        """Test class name inference."""
        assert invoker._infer_workflow_class_name("api_development") == "ApiDevelopmentWorkflow"
        assert invoker._infer_workflow_class_name("ui_development") == "UiDevelopmentWorkflow"
        assert invoker._infer_workflow_class_name("simple") == "SimpleWorkflow"


class TestResultValidation:
    """Tests for result validation."""

    def test_ensure_valid_result_success(self, invoker, sample_workflow_result) -> None:
        """Test validation of valid result."""
        result = invoker._ensure_valid_result(sample_workflow_result, "test_workflow")

        assert result["status"] == "success"
        assert result["workflow_name"] == "test_workflow"
        assert result["output"] == {"test": "data"}
        assert isinstance(result["artifacts"], list)
        assert isinstance(result["execution_time_seconds"], float)

    def test_ensure_valid_result_missing_fields(self, invoker) -> None:
        """Test validation fails for missing required fields."""
        invalid_result = {"status": "success"}  # Missing other required fields

        with pytest.raises(ValueError, match="missing required fields"):
            invoker._ensure_valid_result(invalid_result, "test_workflow")

    def test_ensure_valid_result_invalid_type(self, invoker) -> None:
        """Test validation fails for non-dict result."""
        with pytest.raises(ValueError, match="must be a dictionary"):
            invoker._ensure_valid_result("not a dict", "test_workflow")

    def test_create_error_result(self, invoker) -> None:
        """Test creation of error result."""
        result = invoker._create_error_result(
            "test_workflow", "Something went wrong", "RuntimeError"
        )

        assert result["status"] == "failure"
        assert result["workflow_name"] == "test_workflow"
        assert result["error"] == "Something went wrong"
        assert result["error_type"] == "RuntimeError"
        assert result["output"] == {}
        assert result["artifacts"] == []


class TestCacheManagement:
    """Tests for cache management."""

    def test_clear_cache(self, invoker) -> None:
        """Test clearing the cache."""
        # Add something to cache
        invoker.embedded_workflows_cache["test_module"] = MagicMock()
        assert len(invoker.embedded_workflows_cache) > 0

        invoker.clear_cache()

        assert len(invoker.embedded_workflows_cache) == 0

    def test_get_cached_workflow(self, invoker) -> None:
        """Test retrieving cached workflow."""
        mock_workflow = MagicMock()
        invoker.embedded_workflows_cache["test_module"] = mock_workflow

        result = invoker.get_cached_workflow("test_module")

        assert result is mock_workflow

    def test_get_cached_workflow_not_found(self, invoker) -> None:
        """Test retrieving non-existent workflow."""
        result = invoker.get_cached_workflow("nonexistent")

        assert result is None

    def test_list_cached_workflows(self, invoker) -> None:
        """Test listing cached workflows."""
        mock_workflow1 = MagicMock(spec=ApiDevelopmentWorkflow)
        mock_workflow1.__class__.__module__ = "workflows.children.api_development.workflow"
        mock_workflow1.__class__.__name__ = "ApiDevelopmentWorkflow"

        invoker.embedded_workflows_cache["module1"] = mock_workflow1

        result = invoker.list_cached_workflows()

        assert "module1" in result
        assert "Workflow" in result["module1"]


class TestHTTPRequests:
    """Tests for HTTP request handling."""

    def test_http_request_method_exists(self, invoker) -> None:
        """Test that HTTP request method exists and is callable."""
        assert hasattr(invoker, "_make_http_request")
        assert callable(getattr(invoker, "_make_http_request"))

    def test_http_timeout_configuration(self, invoker) -> None:
        """Test HTTP timeout is properly configured."""
        assert invoker.default_timeout == 10.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
