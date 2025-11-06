"""
Integration tests for Coordinator with WorkflowInvoker.

Tests the integration between the Coordinator and WorkflowInvoker,
including workflow execution with embedded and A2A modes.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from workflows.parent.agents.coordinator import WorkflowCoordinator
from workflows.registry.registry import WorkflowRegistry, WorkflowMetadata, DeploymentMode
from workflows.registry.invoker import WorkflowInvoker
from workflows.parent.state import WorkflowTask, create_initial_state
from workflows.children.api_development.workflow import ApiDevelopmentWorkflow


# ========== Test Fixtures ==========


@pytest.fixture
def workflow_registry() -> WorkflowRegistry:
    """Create a populated WorkflowRegistry."""
    registry = WorkflowRegistry()

    # Register embedded workflow
    api_metadata = WorkflowMetadata(
        name="api_development",
        workflow_type="api_development",
        description="API Development workflow",
        version="1.0.0",
        deployment_mode=DeploymentMode.EMBEDDED,
        module_path="workflows.children.api_development.workflow",
    )
    registry.register(api_metadata)

    return registry


@pytest.fixture
def workflow_invoker() -> WorkflowInvoker:
    """Create a WorkflowInvoker instance."""
    return WorkflowInvoker(default_timeout=60, default_retries=2)


@pytest.fixture
def coordinator_with_registry(workflow_registry, workflow_invoker) -> WorkflowCoordinator:
    """Create a Coordinator with registry and invoker."""
    return WorkflowCoordinator(
        timeout_seconds=300,
        max_retries=2,
        registry=workflow_registry,
        invoker=workflow_invoker,
    )


@pytest.fixture
def coordinator_without_registry(workflow_invoker) -> WorkflowCoordinator:
    """Create a Coordinator without registry (falls back to simulation)."""
    return WorkflowCoordinator(
        timeout_seconds=300,
        max_retries=2,
        registry=None,
        invoker=workflow_invoker,
    )


@pytest.fixture
def sample_parent_state() -> Dict[str, Any]:
    """Create a sample parent workflow state."""
    return create_initial_state("# Test Story\n\n## Story\nTest\n\n## Requirements\nTest")


@pytest.fixture
def sample_workflow_task() -> WorkflowTask:
    """Create a sample workflow task."""
    return {
        "task_id": "task_1",
        "workflow_name": "api_development",
        "workflow_type": "api_development",
        "description": "Test API development task",
        "parameters": {},
    }


# ========== Test Classes ==========


class TestCoordinatorWithRegistry:
    """Tests for Coordinator with registry and invoker."""

    def test_coordinator_can_be_initialized_with_registry(
        self, coordinator_with_registry
    ) -> None:
        """Test that Coordinator can be initialized with registry and invoker."""
        assert coordinator_with_registry is not None
        assert coordinator_with_registry.registry is not None
        assert coordinator_with_registry.invoker is not None

    @pytest.mark.asyncio
    async def test_execute_single_workflow_with_registry(
        self,
        coordinator_with_registry,
        sample_workflow_task,
        sample_parent_state,
    ) -> None:
        """Test executing a single workflow with registry lookup."""
        coordinator_with_registry._parent_state = sample_parent_state

        # Mock the invoker to avoid actual workflow execution
        with patch.object(
            coordinator_with_registry.invoker, "invoke"
        ) as mock_invoke:
            mock_result = {
                "workflow_name": "api_development",
                "status": "success",
                "output": {"test": "data"},
                "artifacts": [],
                "execution_time_seconds": 0.5,
            }
            mock_invoke.return_value = mock_result

            result = await coordinator_with_registry._simulate_workflow_execution(
                sample_workflow_task
            )

            assert result is not None
            assert result["status"] == "success"
            assert result["workflow_name"] == "api_development"
            mock_invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_sequential_with_registry(
        self,
        coordinator_with_registry,
        sample_parent_state,
    ) -> None:
        """Test sequential execution with registry."""
        coordinator_with_registry._parent_state = sample_parent_state

        tasks: list[WorkflowTask] = [
            {
                "task_id": "task_1",
                "workflow_name": "api_development",
                "workflow_type": "api_development",
                "description": "Task 1",
                "parameters": {},
            },
            {
                "task_id": "task_2",
                "workflow_name": "api_development",
                "workflow_type": "api_development",
                "description": "Task 2",
                "parameters": {},
            },
        ]

        with patch.object(
            coordinator_with_registry.invoker, "invoke"
        ) as mock_invoke:
            mock_invoke.return_value = {
                "workflow_name": "api_development",
                "status": "success",
                "output": {},
                "artifacts": [],
                "execution_time_seconds": 0.5,
            }

            results = await coordinator_with_registry._execute_sequential(tasks, [])

            assert len(results) == 2
            assert "task_1" in results
            assert "task_2" in results
            assert mock_invoke.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_parent_state(
        self,
        coordinator_with_registry,
        sample_parent_state,
    ) -> None:
        """Test that parent state is properly passed to child workflows."""
        tasks: list[WorkflowTask] = [
            {
                "task_id": "task_1",
                "workflow_name": "api_development",
                "workflow_type": "api_development",
                "description": "Task 1",
                "parameters": {},
            },
        ]

        with patch.object(
            coordinator_with_registry.invoker, "invoke"
        ) as mock_invoke:
            mock_invoke.return_value = {
                "workflow_name": "api_development",
                "status": "success",
                "output": {},
                "artifacts": [],
                "execution_time_seconds": 0.5,
            }

            await coordinator_with_registry.execute(
                tasks,
                execution_strategy="sequential",
                execution_order=[],
                task_dependencies={},
                parent_state=sample_parent_state,
            )

            # Verify invoker was called with parent state
            mock_invoke.assert_called()
            call_args = mock_invoke.call_args
            assert call_args is not None
            # Parent state should be passed as second argument
            passed_state = call_args[0][1] if len(call_args[0]) > 1 else None
            assert passed_state is not None


class TestCoordinatorWithoutRegistry:
    """Tests for Coordinator without registry (simulation fallback)."""

    @pytest.mark.asyncio
    async def test_execute_single_workflow_without_registry(
        self,
        coordinator_without_registry,
        sample_workflow_task,
    ) -> None:
        """Test that workflows are simulated when registry is unavailable."""
        coordinator_without_registry._parent_state = {}

        result = await coordinator_without_registry._simulate_workflow_execution(
            sample_workflow_task
        )

        assert result is not None
        assert result["status"] == "success"
        assert "Simulated execution" in result["output"]["message"]


class TestCoordinatorInitialization:
    """Tests for Coordinator initialization."""

    def test_coordinator_creates_invoker_if_not_provided(self) -> None:
        """Test that Coordinator creates invoker if not provided."""
        registry = WorkflowRegistry()
        coordinator = WorkflowCoordinator(
            timeout_seconds=300,
            max_retries=2,
            registry=registry,
            invoker=None,  # Not provided
        )

        assert coordinator.invoker is not None
        assert isinstance(coordinator.invoker, WorkflowInvoker)

    def test_coordinator_uses_provided_invoker(
        self, workflow_invoker
    ) -> None:
        """Test that Coordinator uses provided invoker."""
        registry = WorkflowRegistry()
        coordinator = WorkflowCoordinator(
            timeout_seconds=300,
            max_retries=2,
            registry=registry,
            invoker=workflow_invoker,
        )

        assert coordinator.invoker is workflow_invoker


class TestCoordinatorWithMockedWorkflow:
    """Tests with mocked embedded workflow."""

    @pytest.mark.asyncio
    async def test_execute_with_mocked_embedded_workflow(
        self,
        coordinator_with_registry,
        sample_parent_state,
    ) -> None:
        """Test executing with a mocked embedded workflow."""
        task: WorkflowTask = {
            "task_id": "task_1",
            "workflow_name": "api_development",
            "workflow_type": "api_development",
            "description": "Mock task",
            "parameters": {},
        }

        # Mock the workflow loading and execution
        with patch.object(
            coordinator_with_registry.invoker, "_get_or_load_embedded_workflow"
        ) as mock_load:
            mock_workflow = AsyncMock()
            mock_workflow.execute = AsyncMock(
                return_value={
                    "status": "success",
                    "output": {"result": "test"},
                    "artifacts": [],
                    "execution_time_seconds": 0.1,
                }
            )
            mock_load.return_value = mock_workflow

            with patch.object(
                coordinator_with_registry.invoker, "invoke"
            ) as mock_invoke:
                mock_invoke.return_value = {
                    "workflow_name": "api_development",
                    "status": "success",
                    "output": {"result": "test"},
                    "artifacts": [],
                    "execution_time_seconds": 0.1,
                }

                coordinator_with_registry._parent_state = sample_parent_state

                result = await coordinator_with_registry._simulate_workflow_execution(
                    task
                )

                assert result["status"] == "success"
                mock_invoke.assert_called_once()


class TestCoordinatorErrorHandling:
    """Tests for error handling in Coordinator."""

    @pytest.mark.asyncio
    async def test_execute_with_workflow_not_found(
        self,
        coordinator_with_registry,
    ) -> None:
        """Test handling of workflow not found error."""
        task: WorkflowTask = {
            "task_id": "task_1",
            "workflow_name": "nonexistent_workflow",
            "workflow_type": "unknown",
            "description": "Task for nonexistent workflow",
            "parameters": {},
        }

        coordinator_with_registry._parent_state = {}

        result = await coordinator_with_registry._simulate_workflow_execution(task)

        assert result["status"] == "failure"
        assert "not found" in result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_execute_with_invoker_error(
        self,
        coordinator_with_registry,
        sample_workflow_task,
    ) -> None:
        """Test handling of invoker errors."""
        coordinator_with_registry._parent_state = {}

        with patch.object(
            coordinator_with_registry.invoker, "invoke"
        ) as mock_invoke:
            mock_invoke.side_effect = RuntimeError("Service error")

            result = await coordinator_with_registry._simulate_workflow_execution(
                sample_workflow_task
            )

            assert result["status"] == "failure"
            assert "Service error" in result.get("error", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
