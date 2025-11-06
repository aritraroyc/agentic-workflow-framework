"""
Unit tests for the Coordinator Agent.

Tests cover:
- Sequential execution
- Parallel execution
- Hybrid execution
- Dependency satisfaction checking
- Dependency level grouping
- Status aggregation
- Execution summary
- Error handling and retries
"""

import pytest
import asyncio
from workflows.parent.agents.coordinator import WorkflowCoordinator
from workflows.parent.state import WorkflowTask, WorkflowExecutionResult


class TestSequentialExecution:
    """Tests for sequential workflow execution."""

    @pytest.fixture
    def coordinator(self) -> WorkflowCoordinator:
        """Create a coordinator instance for testing."""
        return WorkflowCoordinator()

    @pytest.fixture
    def sample_tasks(self) -> list:
        """Create sample workflow tasks."""
        return [
            {
                "task_id": "task_1",
                "workflow_name": "api_development",
                "workflow_type": "api_development",
                "responsibilities": "Develop API",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 4.0,
            },
            {
                "task_id": "task_2",
                "workflow_name": "api_enhancement",
                "workflow_type": "api_enhancement",
                "responsibilities": "Enhance API",
                "dependencies": ["task_1"],
                "parameters": {},
                "status": "pending",
                "priority": 2,
                "estimated_effort_hours": 2.0,
            },
        ]

    @pytest.mark.asyncio
    async def test_execute_sequential_single_task(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test sequential execution with single task."""
        tasks = [
            {
                "task_id": "task_1",
                "workflow_name": "test_workflow",
                "workflow_type": "test",
                "responsibilities": "Test",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 1.0,
            }
        ]

        results = await coordinator._execute_sequential(tasks, [])

        assert len(results) == 1
        assert "task_1" in results
        assert results["task_1"]["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_sequential_multiple_tasks(
        self, coordinator: WorkflowCoordinator, sample_tasks: list
    ) -> None:
        """Test sequential execution with multiple tasks."""
        results = await coordinator._execute_sequential(sample_tasks, [])

        assert len(results) == 2
        assert "task_1" in results
        assert "task_2" in results
        assert results["task_1"]["status"] == "success"
        assert results["task_2"]["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_sequential_respects_order(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test that sequential execution respects specified order."""
        tasks = [
            {
                "task_id": "task_1",
                "workflow_name": "workflow_1",
                "workflow_type": "test",
                "responsibilities": "Test",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 1.0,
            },
            {
                "task_id": "task_2",
                "workflow_name": "workflow_2",
                "workflow_type": "test",
                "responsibilities": "Test",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 1.0,
            },
        ]
        execution_order = ["task_2", "task_1"]

        results = await coordinator._execute_sequential(tasks, execution_order)

        assert len(results) == 2
        assert "task_1" in results
        assert "task_2" in results


class TestParallelExecution:
    """Tests for parallel workflow execution."""

    @pytest.fixture
    def coordinator(self) -> WorkflowCoordinator:
        """Create a coordinator instance for testing."""
        return WorkflowCoordinator()

    @pytest.fixture
    def independent_tasks(self) -> list:
        """Create independent workflow tasks (no dependencies)."""
        return [
            {
                "task_id": "task_1",
                "workflow_name": "api_development",
                "workflow_type": "api_development",
                "responsibilities": "Develop API",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 4.0,
            },
            {
                "task_id": "task_2",
                "workflow_name": "ui_development",
                "workflow_type": "ui_development",
                "responsibilities": "Develop UI",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 3.0,
            },
            {
                "task_id": "task_3",
                "workflow_name": "database_setup",
                "workflow_type": "database",
                "responsibilities": "Setup Database",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 2.0,
            },
        ]

    @pytest.mark.asyncio
    async def test_execute_parallel_multiple_tasks(
        self, coordinator: WorkflowCoordinator, independent_tasks: list
    ) -> None:
        """Test parallel execution with multiple independent tasks."""
        results = await coordinator._execute_parallel(independent_tasks)

        assert len(results) == 3
        for task_id in ["task_1", "task_2", "task_3"]:
            assert task_id in results
            assert results[task_id]["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_parallel_single_task(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test parallel execution with single task."""
        tasks = [
            {
                "task_id": "task_1",
                "workflow_name": "test",
                "workflow_type": "test",
                "responsibilities": "Test",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 1.0,
            }
        ]

        results = await coordinator._execute_parallel(tasks)

        assert len(results) == 1
        assert results["task_1"]["status"] == "success"


class TestHybridExecution:
    """Tests for hybrid workflow execution."""

    @pytest.fixture
    def coordinator(self) -> WorkflowCoordinator:
        """Create a coordinator instance for testing."""
        return WorkflowCoordinator()

    @pytest.fixture
    def dependent_tasks(self) -> list:
        """Create workflow tasks with dependencies."""
        return [
            {
                "task_id": "task_1",
                "workflow_name": "api_development",
                "workflow_type": "api_development",
                "responsibilities": "Develop API",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 4.0,
            },
            {
                "task_id": "task_2",
                "workflow_name": "api_enhancement",
                "workflow_type": "api_enhancement",
                "responsibilities": "Enhance API",
                "dependencies": ["task_1"],
                "parameters": {},
                "status": "pending",
                "priority": 2,
                "estimated_effort_hours": 2.0,
            },
            {
                "task_id": "task_3",
                "workflow_name": "ui_development",
                "workflow_type": "ui_development",
                "responsibilities": "Develop UI",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 3.0,
            },
        ]

    @pytest.fixture
    def dependent_task_deps(self) -> dict:
        """Task dependency mapping."""
        return {
            "task_1": [],
            "task_2": ["task_1"],
            "task_3": [],
        }

    @pytest.mark.asyncio
    async def test_execute_hybrid(
        self,
        coordinator: WorkflowCoordinator,
        dependent_tasks: list,
        dependent_task_deps: dict,
    ) -> None:
        """Test hybrid execution with mixed dependencies."""
        results = await coordinator._execute_hybrid(
            dependent_tasks,
            ["task_1", "task_3", "task_2"],
            dependent_task_deps,
        )

        assert len(results) == 3
        for task_id in ["task_1", "task_2", "task_3"]:
            assert task_id in results
            assert results[task_id]["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_hybrid_respects_dependencies(
        self,
        coordinator: WorkflowCoordinator,
        dependent_tasks: list,
        dependent_task_deps: dict,
    ) -> None:
        """Test that hybrid execution respects dependencies."""
        results = await coordinator._execute_hybrid(
            dependent_tasks,
            [],
            dependent_task_deps,
        )

        # All tasks should complete successfully
        assert all(r["status"] == "success" for r in results.values())


class TestDependencySatisfaction:
    """Tests for dependency satisfaction checking."""

    @pytest.fixture
    def coordinator(self) -> WorkflowCoordinator:
        """Create a coordinator instance for testing."""
        return WorkflowCoordinator()

    def test_dependencies_satisfied_no_deps(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test that task with no dependencies is satisfied."""
        deps = {"task_1": []}
        completed = set()

        result = coordinator._dependencies_satisfied("task_1", deps, completed)

        assert result is True

    def test_dependencies_satisfied_single_dep_met(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test that task with met dependency is satisfied."""
        deps = {"task_2": ["task_1"]}
        completed = {"task_1"}

        result = coordinator._dependencies_satisfied("task_2", deps, completed)

        assert result is True

    def test_dependencies_satisfied_single_dep_unmet(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test that task with unmet dependency is not satisfied."""
        deps = {"task_2": ["task_1"]}
        completed = set()

        result = coordinator._dependencies_satisfied("task_2", deps, completed)

        assert result is False

    def test_dependencies_satisfied_multiple_deps_all_met(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test that task with all dependencies met is satisfied."""
        deps = {"task_3": ["task_1", "task_2"]}
        completed = {"task_1", "task_2"}

        result = coordinator._dependencies_satisfied("task_3", deps, completed)

        assert result is True

    def test_dependencies_satisfied_multiple_deps_partial_met(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test that task with partial dependencies met is not satisfied."""
        deps = {"task_3": ["task_1", "task_2"]}
        completed = {"task_1"}

        result = coordinator._dependencies_satisfied("task_3", deps, completed)

        assert result is False


class TestDependencyLevelGrouping:
    """Tests for dependency level grouping."""

    @pytest.fixture
    def coordinator(self) -> WorkflowCoordinator:
        """Create a coordinator instance for testing."""
        return WorkflowCoordinator()

    def test_group_by_dependency_level_no_deps(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test grouping tasks with no dependencies."""
        tasks = [
            {
                "task_id": "task_1",
                "workflow_name": "wf1",
                "workflow_type": "test",
                "responsibilities": "Test",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 1.0,
            },
            {
                "task_id": "task_2",
                "workflow_name": "wf2",
                "workflow_type": "test",
                "responsibilities": "Test",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 1.0,
            },
        ]
        deps = {"task_1": [], "task_2": []}

        levels = coordinator._group_by_dependency_level(tasks, deps)

        assert len(levels) == 1
        assert len(levels[0]) == 2

    def test_group_by_dependency_level_linear(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test grouping tasks with linear dependencies."""
        tasks = [
            {
                "task_id": "task_1",
                "workflow_name": "wf1",
                "workflow_type": "test",
                "responsibilities": "Test",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 1.0,
            },
            {
                "task_id": "task_2",
                "workflow_name": "wf2",
                "workflow_type": "test",
                "responsibilities": "Test",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 1.0,
            },
            {
                "task_id": "task_3",
                "workflow_name": "wf3",
                "workflow_type": "test",
                "responsibilities": "Test",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 1.0,
            },
        ]
        deps = {
            "task_1": [],
            "task_2": ["task_1"],
            "task_3": ["task_2"],
        }

        levels = coordinator._group_by_dependency_level(tasks, deps)

        assert len(levels) == 3
        assert len(levels[0]) == 1
        assert len(levels[1]) == 1
        assert len(levels[2]) == 1

    def test_group_by_dependency_level_diamond(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test grouping tasks with diamond dependency pattern."""
        tasks = [
            {
                "task_id": "task_1",
                "workflow_name": "wf1",
                "workflow_type": "test",
                "responsibilities": "Test",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 1.0,
            },
            {
                "task_id": "task_2",
                "workflow_name": "wf2",
                "workflow_type": "test",
                "responsibilities": "Test",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 1.0,
            },
            {
                "task_id": "task_3",
                "workflow_name": "wf3",
                "workflow_type": "test",
                "responsibilities": "Test",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 1.0,
            },
            {
                "task_id": "task_4",
                "workflow_name": "wf4",
                "workflow_type": "test",
                "responsibilities": "Test",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 1.0,
            },
        ]
        deps = {
            "task_1": [],
            "task_2": ["task_1"],
            "task_3": ["task_1"],
            "task_4": ["task_2", "task_3"],
        }

        levels = coordinator._group_by_dependency_level(tasks, deps)

        assert len(levels) == 3
        assert len(levels[0]) == 1  # task_1
        assert len(levels[1]) == 2  # task_2, task_3
        assert len(levels[2]) == 1  # task_4


class TestStatusAggregation:
    """Tests for execution status aggregation."""

    @pytest.fixture
    def coordinator(self) -> WorkflowCoordinator:
        """Create a coordinator instance for testing."""
        return WorkflowCoordinator()

    def test_determine_overall_status_all_success(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test overall status when all tasks succeed."""
        results = {
            "task_1": {"workflow_name": "wf1", "status": "success"},
            "task_2": {"workflow_name": "wf2", "status": "success"},
        }

        status = coordinator._determine_overall_status(results)

        assert status == "success"

    def test_determine_overall_status_all_failure(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test overall status when all tasks fail."""
        results = {
            "task_1": {"workflow_name": "wf1", "status": "failure"},
            "task_2": {"workflow_name": "wf2", "status": "failure"},
        }

        status = coordinator._determine_overall_status(results)

        assert status == "failure"

    def test_determine_overall_status_partial(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test overall status when some tasks succeed and some fail."""
        results = {
            "task_1": {"workflow_name": "wf1", "status": "success"},
            "task_2": {"workflow_name": "wf2", "status": "failure"},
        }

        status = coordinator._determine_overall_status(results)

        assert status == "partial"

    def test_determine_overall_status_empty(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test overall status with empty results."""
        results = {}

        status = coordinator._determine_overall_status(results)

        assert status == "failure"


class TestExecutionSummary:
    """Tests for execution summary generation."""

    @pytest.fixture
    def coordinator(self) -> WorkflowCoordinator:
        """Create a coordinator instance for testing."""
        return WorkflowCoordinator()

    def test_get_execution_summary_all_success(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test summary with all successful tasks."""
        results = {
            "task_1": {
                "workflow_name": "wf1",
                "status": "success",
                "execution_time_seconds": 1.5,
            },
            "task_2": {
                "workflow_name": "wf2",
                "status": "success",
                "execution_time_seconds": 2.5,
            },
        }

        summary = coordinator.get_execution_summary(results)

        assert summary["total_tasks"] == 2
        assert summary["successful"] == 2
        assert summary["failed"] == 0
        assert summary["success_rate"] == 100.0
        assert summary["total_execution_time_seconds"] == 4.0
        assert summary["overall_status"] == "success"

    def test_get_execution_summary_partial_failure(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test summary with partial failure."""
        results = {
            "task_1": {
                "workflow_name": "wf1",
                "status": "success",
                "execution_time_seconds": 1.0,
            },
            "task_2": {
                "workflow_name": "wf2",
                "status": "failure",
                "execution_time_seconds": 0.5,
            },
            "task_3": {
                "workflow_name": "wf3",
                "status": "success",
                "execution_time_seconds": 1.5,
            },
        }

        summary = coordinator.get_execution_summary(results)

        assert summary["total_tasks"] == 3
        assert summary["successful"] == 2
        assert summary["failed"] == 1
        assert summary["success_rate"] == pytest.approx(66.666666, rel=0.01)
        assert summary["overall_status"] == "partial"

    def test_get_execution_summary_all_failure(
        self, coordinator: WorkflowCoordinator
    ) -> None:
        """Test summary with all failures."""
        results = {
            "task_1": {
                "workflow_name": "wf1",
                "status": "failure",
                "execution_time_seconds": 0.5,
            },
            "task_2": {
                "workflow_name": "wf2",
                "status": "failure",
                "execution_time_seconds": 0.3,
            },
        }

        summary = coordinator.get_execution_summary(results)

        assert summary["total_tasks"] == 2
        assert summary["successful"] == 0
        assert summary["failed"] == 2
        assert summary["success_rate"] == 0.0
        assert summary["overall_status"] == "failure"


class TestMainExecuteMethod:
    """Tests for the main execute method."""

    @pytest.fixture
    def coordinator(self) -> WorkflowCoordinator:
        """Create a coordinator instance for testing."""
        return WorkflowCoordinator()

    @pytest.fixture
    def sample_tasks(self) -> list:
        """Create sample workflow tasks."""
        return [
            {
                "task_id": "task_1",
                "workflow_name": "workflow_1",
                "workflow_type": "test",
                "responsibilities": "Test",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 1.0,
            },
            {
                "task_id": "task_2",
                "workflow_name": "workflow_2",
                "workflow_type": "test",
                "responsibilities": "Test",
                "dependencies": [],
                "parameters": {},
                "status": "pending",
                "priority": 1,
                "estimated_effort_hours": 1.0,
            },
        ]

    @pytest.mark.asyncio
    async def test_execute_sequential_strategy(
        self, coordinator: WorkflowCoordinator, sample_tasks: list
    ) -> None:
        """Test execute with sequential strategy."""
        results = await coordinator.execute(
            sample_tasks,
            "sequential",
            [],
            {},
        )

        assert len(results) == 2
        assert all(r["status"] == "success" for r in results.values())

    @pytest.mark.asyncio
    async def test_execute_parallel_strategy(
        self, coordinator: WorkflowCoordinator, sample_tasks: list
    ) -> None:
        """Test execute with parallel strategy."""
        results = await coordinator.execute(
            sample_tasks,
            "parallel",
            [],
            {},
        )

        assert len(results) == 2
        assert all(r["status"] == "success" for r in results.values())

    @pytest.mark.asyncio
    async def test_execute_hybrid_strategy(
        self, coordinator: WorkflowCoordinator, sample_tasks: list
    ) -> None:
        """Test execute with hybrid strategy."""
        deps = {"task_1": [], "task_2": []}

        results = await coordinator.execute(
            sample_tasks,
            "hybrid",
            [],
            deps,
        )

        assert len(results) == 2
        assert all(r["status"] == "success" for r in results.values())

    @pytest.mark.asyncio
    async def test_execute_unknown_strategy_defaults_to_sequential(
        self, coordinator: WorkflowCoordinator, sample_tasks: list
    ) -> None:
        """Test that unknown strategy defaults to sequential."""
        results = await coordinator.execute(
            sample_tasks,
            "unknown_strategy",
            [],
            {},
        )

        assert len(results) == 2
        assert all(r["status"] == "success" for r in results.values())

    @pytest.mark.asyncio
    async def test_execute_returns_all_results(
        self, coordinator: WorkflowCoordinator, sample_tasks: list
    ) -> None:
        """Test that execute returns results for all tasks."""
        results = await coordinator.execute(
            sample_tasks,
            "sequential",
            [],
            {},
        )

        assert "task_1" in results
        assert "task_2" in results
        assert isinstance(results["task_1"], dict)
        assert isinstance(results["task_2"], dict)
