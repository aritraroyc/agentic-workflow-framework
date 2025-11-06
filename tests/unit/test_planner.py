"""
Unit tests for the Planner Agent.

Tests cover:
- Story scope analysis
- Workflow identification
- Task creation
- Dependency determination
- Execution strategy planning
- Risk identification
- Topological sorting
"""

import pytest
from workflows.parent.agents.planner import PlannerAgent
from workflows.parent.state import PreprocessorOutput
from workflows.registry.registry import WorkflowRegistry, WorkflowMetadata, DeploymentMode


class TestScopeAnalysis:
    """Tests for story scope analysis."""

    @pytest.fixture
    def planner(self) -> PlannerAgent:
        """Create a planner instance for testing."""
        return PlannerAgent()

    @pytest.fixture
    def sample_preprocessor_output(self) -> PreprocessorOutput:
        """Create sample preprocessor output."""
        return {
            "parsed_sections": {
                "Story": "Build a user management API",
                "Requirements": "- Registration\n- Authentication",
            },
            "structure_valid": True,
            "extracted_data": {
                "title": "User Management API",
                "requirements": ["User registration", "JWT authentication", "Profile management"],
                "constraints": ["Python 3.11+", "PostgreSQL"],
            },
            "metadata": {
                "story_type": "api_development",
                "title": "User Management API",
                "estimated_complexity": "medium",
                "word_count": 250,
                "requirement_count": 3,
            },
            "parsing_errors": [],
            "parsing_warnings": [],
            "input_summary": "Build user management API",
            "detected_story_type": "api_development",
        }

    @pytest.mark.asyncio
    async def test_analyze_story_scope_without_llm(
        self, planner: PlannerAgent, sample_preprocessor_output: PreprocessorOutput
    ) -> None:
        """Test scope analysis without LLM."""
        scope = await planner._analyze_story_scope(sample_preprocessor_output)

        assert len(scope) > 0
        assert "api_development" in scope or "API" in scope
        assert "User Management" in scope

    @pytest.mark.asyncio
    async def test_analyze_story_scope_with_requirements(
        self, planner: PlannerAgent
    ) -> None:
        """Test scope analysis captures requirements."""
        output: PreprocessorOutput = {
            "parsed_sections": {},
            "structure_valid": True,
            "extracted_data": {
                "requirements": ["Req1", "Req2", "Req3", "Req4"],
            },
            "metadata": {
                "story_type": "api_enhancement",
            },
            "parsing_errors": [],
            "parsing_warnings": [],
            "input_summary": "",
            "detected_story_type": "api_enhancement",
        }

        scope = await planner._analyze_story_scope(output)

        assert len(scope) > 0
        assert "4" in scope or "requirement" in scope.lower()


class TestWorkflowIdentification:
    """Tests for workflow identification."""

    @pytest.fixture
    def planner_with_registry(self) -> PlannerAgent:
        """Create planner with populated registry."""
        registry = WorkflowRegistry()
        registry.register(
            WorkflowMetadata(
                name="api_development",
                workflow_type="api_development",
                description="API development workflow",
                version="1.0.0",
                deployment_mode=DeploymentMode.EMBEDDED,
                module_path="workflows.children.api_development",
            )
        )
        registry.register(
            WorkflowMetadata(
                name="api_enhancement",
                workflow_type="api_enhancement",
                description="API enhancement workflow",
                version="1.0.0",
                deployment_mode=DeploymentMode.EMBEDDED,
                module_path="workflows.children.api_enhancement",
            )
        )
        return PlannerAgent(registry=registry)

    @pytest.fixture
    def api_dev_output(self) -> PreprocessorOutput:
        """Create API development story output."""
        return {
            "parsed_sections": {},
            "structure_valid": True,
            "extracted_data": {"requirements": ["Build REST API"]},
            "metadata": {"story_type": "api_development"},
            "parsing_errors": [],
            "parsing_warnings": [],
            "input_summary": "",
            "detected_story_type": "api_development",
        }

    @pytest.mark.asyncio
    async def test_identify_workflows_from_registry(
        self, planner_with_registry: PlannerAgent, api_dev_output: PreprocessorOutput
    ) -> None:
        """Test identifying workflows from registry."""
        workflows = await planner_with_registry._identify_required_workflows(
            api_dev_output, "Build API"
        )

        assert len(workflows) > 0
        assert "api_development" in workflows

    @pytest.mark.asyncio
    async def test_identify_workflows_heuristic_fallback(
        self, planner_with_registry: PlannerAgent
    ) -> None:
        """Test heuristic workflow identification."""
        output: PreprocessorOutput = {
            "parsed_sections": {},
            "structure_valid": True,
            "extracted_data": {},
            "metadata": {},
            "parsing_errors": [],
            "parsing_warnings": [],
            "input_summary": "",
            "detected_story_type": "ui_development",
        }

        workflows = await planner_with_registry._identify_required_workflows(
            output, "Scope"
        )

        assert isinstance(workflows, list)

    @pytest.mark.asyncio
    async def test_identify_workflows_returns_list(
        self, planner_with_registry: PlannerAgent, api_dev_output: PreprocessorOutput
    ) -> None:
        """Test that identified workflows is always a list."""
        workflows = await planner_with_registry._identify_required_workflows(
            api_dev_output, "Scope"
        )

        assert isinstance(workflows, list)


class TestTaskCreation:
    """Tests for workflow task creation."""

    @pytest.fixture
    def planner_with_registry(self) -> PlannerAgent:
        """Create planner with registry."""
        registry = WorkflowRegistry()
        registry.register(
            WorkflowMetadata(
                name="api_development",
                workflow_type="api_development",
                description="API dev",
                version="1.0.0",
                deployment_mode=DeploymentMode.EMBEDDED,
                module_path="workflows.children.api_development",
            )
        )
        return PlannerAgent(registry=registry)

    @pytest.fixture
    def sample_output(self) -> PreprocessorOutput:
        """Create sample output."""
        return {
            "parsed_sections": {},
            "structure_valid": True,
            "extracted_data": {
                "title": "Test Story",
                "requirements": ["Req1", "Req2"],
            },
            "metadata": {
                "story_type": "api_development",
                "estimated_complexity": "medium",
            },
            "parsing_errors": [],
            "parsing_warnings": [],
            "input_summary": "",
            "detected_story_type": "api_development",
        }

    @pytest.mark.asyncio
    async def test_create_workflow_tasks(
        self, planner_with_registry: PlannerAgent, sample_output: PreprocessorOutput
    ) -> None:
        """Test creating workflow tasks."""
        tasks = await planner_with_registry._create_workflow_tasks(
            ["api_development"], sample_output
        )

        assert len(tasks) == 1
        task = tasks[0]
        assert task["workflow_name"] == "api_development"
        assert task["task_id"] == "task_1"
        assert "responsibilities" in task
        assert "estimated_effort_hours" in task

    @pytest.mark.asyncio
    async def test_create_multiple_tasks(
        self, planner_with_registry: PlannerAgent, sample_output: PreprocessorOutput
    ) -> None:
        """Test creating multiple workflow tasks."""
        tasks = await planner_with_registry._create_workflow_tasks(
            ["api_development", "api_development"], sample_output
        )

        assert len(tasks) == 2
        assert tasks[0]["task_id"] == "task_1"
        assert tasks[1]["task_id"] == "task_2"
        assert tasks[0]["priority"] == 1
        assert tasks[1]["priority"] == 2

    @pytest.mark.asyncio
    async def test_task_parameters_extraction(
        self, planner_with_registry: PlannerAgent, sample_output: PreprocessorOutput
    ) -> None:
        """Test that task parameters are extracted."""
        tasks = await planner_with_registry._create_workflow_tasks(
            ["api_development"], sample_output
        )

        task = tasks[0]
        assert "parameters" in task
        params = task.get("parameters", {})
        assert "story_type" in params
        assert params["story_type"] == "api_development"

    @pytest.mark.asyncio
    async def test_effort_estimation_by_complexity(
        self, planner_with_registry: PlannerAgent
    ) -> None:
        """Test effort estimation varies by complexity."""
        low_output: PreprocessorOutput = {
            "parsed_sections": {},
            "structure_valid": True,
            "extracted_data": {},
            "metadata": {"estimated_complexity": "low"},
            "parsing_errors": [],
            "parsing_warnings": [],
            "input_summary": "",
            "detected_story_type": "api_development",
        }

        high_output: PreprocessorOutput = {
            "parsed_sections": {},
            "structure_valid": True,
            "extracted_data": {},
            "metadata": {"estimated_complexity": "high"},
            "parsing_errors": [],
            "parsing_warnings": [],
            "input_summary": "",
            "detected_story_type": "api_development",
        }

        low_tasks = await planner_with_registry._create_workflow_tasks(
            ["api_development"], low_output
        )
        high_tasks = await planner_with_registry._create_workflow_tasks(
            ["api_development"], high_output
        )

        low_effort = low_tasks[0]["estimated_effort_hours"]
        high_effort = high_tasks[0]["estimated_effort_hours"]

        assert high_effort > low_effort


class TestDependencyDetermination:
    """Tests for dependency determination."""

    @pytest.fixture
    def planner(self) -> PlannerAgent:
        """Create planner instance."""
        return PlannerAgent()

    def test_no_dependencies_for_same_type(self, planner: PlannerAgent) -> None:
        """Test that same workflow type has no dependencies."""
        tasks = [
            {
                "task_id": "task_1",
                "workflow_name": "api_development",
                "workflow_type": "api_development",
            }
        ]

        deps = planner._determine_dependencies(tasks)

        assert deps["task_1"] == []

    def test_enhancement_depends_on_development(self, planner: PlannerAgent) -> None:
        """Test that enhancement depends on development."""
        tasks = [
            {
                "task_id": "task_1",
                "workflow_name": "api_development",
                "workflow_type": "api_development",
            },
            {
                "task_id": "task_2",
                "workflow_name": "api_enhancement",
                "workflow_type": "api_enhancement",
            },
        ]

        deps = planner._determine_dependencies(tasks)

        assert "task_1" in deps["task_2"]
        assert deps["task_1"] == []

    def test_empty_tasks_returns_empty_deps(self, planner: PlannerAgent) -> None:
        """Test empty task list returns empty dependencies."""
        deps = planner._determine_dependencies([])

        assert deps == {}


class TestExecutionStrategy:
    """Tests for execution strategy determination."""

    @pytest.fixture
    def planner(self) -> PlannerAgent:
        """Create planner instance."""
        return PlannerAgent()

    def test_sequential_for_single_task(self, planner: PlannerAgent) -> None:
        """Test sequential strategy for single task."""
        tasks = [{"task_id": "task_1"}]
        deps = {"task_1": []}

        strategy, order = planner._determine_execution_strategy(tasks, deps)

        assert strategy == "sequential"
        assert "task_1" in order

    def test_parallel_for_independent_tasks(self, planner: PlannerAgent) -> None:
        """Test parallel strategy for independent tasks."""
        tasks = [
            {"task_id": "task_1"},
            {"task_id": "task_2"},
        ]
        deps = {"task_1": [], "task_2": []}

        strategy, order = planner._determine_execution_strategy(tasks, deps)

        assert strategy == "parallel"

    def test_hybrid_for_dependent_tasks(self, planner: PlannerAgent) -> None:
        """Test hybrid strategy for dependent tasks."""
        tasks = [
            {"task_id": "task_1"},
            {"task_id": "task_2"},
        ]
        deps = {"task_1": [], "task_2": ["task_1"]}

        strategy, order = planner._determine_execution_strategy(tasks, deps)

        assert strategy == "hybrid"

    def test_execution_order_respects_dependencies(self, planner: PlannerAgent) -> None:
        """Test execution order respects dependencies."""
        tasks = [
            {"task_id": "task_1"},
            {"task_id": "task_2"},
        ]
        deps = {"task_1": [], "task_2": ["task_1"]}

        strategy, order = planner._determine_execution_strategy(tasks, deps)

        assert order.index("task_1") < order.index("task_2")


class TestTopologicalSort:
    """Tests for topological sorting."""

    @pytest.fixture
    def planner(self) -> PlannerAgent:
        """Create planner instance."""
        return PlannerAgent()

    def test_topological_sort_linear_dependency(self, planner: PlannerAgent) -> None:
        """Test topological sort with linear dependency."""
        tasks = [
            {"task_id": "task_1"},
            {"task_id": "task_2"},
            {"task_id": "task_3"},
        ]
        deps = {
            "task_1": [],
            "task_2": ["task_1"],
            "task_3": ["task_2"],
        }

        result = planner._topological_sort(tasks, deps)

        assert result.index("task_1") < result.index("task_2")
        assert result.index("task_2") < result.index("task_3")

    def test_topological_sort_no_dependencies(self, planner: PlannerAgent) -> None:
        """Test topological sort with no dependencies."""
        tasks = [
            {"task_id": "task_1"},
            {"task_id": "task_2"},
        ]
        deps = {"task_1": [], "task_2": []}

        result = planner._topological_sort(tasks, deps)

        assert len(result) == 2
        assert "task_1" in result
        assert "task_2" in result

    def test_topological_sort_diamond_dependency(self, planner: PlannerAgent) -> None:
        """Test topological sort with diamond dependency."""
        tasks = [
            {"task_id": "task_1"},
            {"task_id": "task_2"},
            {"task_id": "task_3"},
            {"task_id": "task_4"},
        ]
        deps = {
            "task_1": [],
            "task_2": ["task_1"],
            "task_3": ["task_1"],
            "task_4": ["task_2", "task_3"],
        }

        result = planner._topological_sort(tasks, deps)

        assert result.index("task_1") < result.index("task_2")
        assert result.index("task_1") < result.index("task_3")
        assert result.index("task_2") < result.index("task_4")
        assert result.index("task_3") < result.index("task_4")


class TestRiskIdentification:
    """Tests for risk factor identification."""

    @pytest.fixture
    def planner(self) -> PlannerAgent:
        """Create planner instance."""
        return PlannerAgent()

    @pytest.mark.asyncio
    async def test_identify_risk_high_complexity(self, planner: PlannerAgent) -> None:
        """Test risk identification for high complexity."""
        output: PreprocessorOutput = {
            "parsed_sections": {},
            "structure_valid": True,
            "extracted_data": {},
            "metadata": {"estimated_complexity": "high"},
            "parsing_errors": [],
            "parsing_warnings": [],
            "input_summary": "",
            "detected_story_type": "api_development",
        }
        tasks = [{"task_id": "task_1"}]

        risks = await planner._identify_risk_factors(tasks, output)

        assert any("complexity" in r.get("factor", "").lower() for r in risks)

    @pytest.mark.asyncio
    async def test_identify_risk_many_requirements(self, planner: PlannerAgent) -> None:
        """Test risk identification for many requirements."""
        output: PreprocessorOutput = {
            "parsed_sections": {},
            "structure_valid": True,
            "extracted_data": {
                "requirements": [f"Req{i}" for i in range(15)]
            },
            "metadata": {},
            "parsing_errors": [],
            "parsing_warnings": [],
            "input_summary": "",
            "detected_story_type": "api_development",
        }
        tasks = [{"task_id": "task_1"}]

        risks = await planner._identify_risk_factors(tasks, output)

        assert any("requirement" in r.get("factor", "").lower() for r in risks)

    @pytest.mark.asyncio
    async def test_identify_risk_returns_list(self, planner: PlannerAgent) -> None:
        """Test risk identification returns list."""
        output: PreprocessorOutput = {
            "parsed_sections": {},
            "structure_valid": True,
            "extracted_data": {},
            "metadata": {},
            "parsing_errors": [],
            "parsing_warnings": [],
            "input_summary": "",
            "detected_story_type": "api_development",
        }
        tasks = [{"task_id": "task_1"}]

        risks = await planner._identify_risk_factors(tasks, output)

        assert isinstance(risks, list)
        for risk in risks:
            assert "factor" in risk
            assert "severity" in risk


class TestPlanningIntegration:
    """Integration tests for complete planning pipeline."""

    @pytest.fixture
    def planner_with_registry(self) -> PlannerAgent:
        """Create planner with registry."""
        registry = WorkflowRegistry()
        registry.register(
            WorkflowMetadata(
                name="api_development",
                workflow_type="api_development",
                description="API dev",
                version="1.0.0",
                deployment_mode=DeploymentMode.EMBEDDED,
                module_path="workflows.children.api_development",
            )
        )
        return PlannerAgent(registry=registry)

    @pytest.fixture
    def complete_preprocessor_output(self) -> PreprocessorOutput:
        """Create complete preprocessor output."""
        return {
            "parsed_sections": {
                "Story": "Build user management API",
                "Requirements": "- Registration\n- Auth",
            },
            "structure_valid": True,
            "extracted_data": {
                "title": "User Management API",
                "description": "Build user management API",
                "requirements": ["User registration", "JWT auth", "Profile mgmt"],
                "success_criteria": ["All endpoints working"],
                "constraints": ["Python 3.11+"],
            },
            "metadata": {
                "story_type": "api_development",
                "title": "User Management API",
                "estimated_complexity": "medium",
                "word_count": 300,
                "requirement_count": 3,
            },
            "parsing_errors": [],
            "parsing_warnings": [],
            "input_summary": "Build user management API",
            "detected_story_type": "api_development",
        }

    @pytest.mark.asyncio
    async def test_plan_creates_valid_output_structure(
        self,
        planner_with_registry: PlannerAgent,
        complete_preprocessor_output: PreprocessorOutput,
    ) -> None:
        """Test that plan returns valid output structure."""
        output = await planner_with_registry.plan(complete_preprocessor_output)

        # Verify all required fields
        assert "story_scope" in output
        assert "required_workflows" in output
        assert "workflow_tasks" in output
        assert "task_dependencies" in output
        assert "execution_strategy" in output
        assert "execution_order" in output
        assert "risk_factors" in output
        assert "estimated_total_effort_hours" in output
        assert "planning_rationale" in output
        assert "planning_errors" in output

    @pytest.mark.asyncio
    async def test_plan_identifies_workflows(
        self,
        planner_with_registry: PlannerAgent,
        complete_preprocessor_output: PreprocessorOutput,
    ) -> None:
        """Test that plan identifies workflows."""
        output = await planner_with_registry.plan(complete_preprocessor_output)

        assert len(output["required_workflows"]) > 0

    @pytest.mark.asyncio
    async def test_plan_creates_workflow_tasks(
        self,
        planner_with_registry: PlannerAgent,
        complete_preprocessor_output: PreprocessorOutput,
    ) -> None:
        """Test that plan creates workflow tasks."""
        output = await planner_with_registry.plan(complete_preprocessor_output)

        assert len(output["workflow_tasks"]) > 0
        for task in output["workflow_tasks"]:
            assert "task_id" in task
            assert "workflow_name" in task
            assert "responsibilities" in task

    @pytest.mark.asyncio
    async def test_plan_determines_execution_strategy(
        self,
        planner_with_registry: PlannerAgent,
        complete_preprocessor_output: PreprocessorOutput,
    ) -> None:
        """Test that plan determines execution strategy."""
        output = await planner_with_registry.plan(complete_preprocessor_output)

        assert output["execution_strategy"] in ["sequential", "parallel", "hybrid", "unknown"]
        assert isinstance(output["execution_order"], list)

    @pytest.mark.asyncio
    async def test_plan_estimates_effort(
        self,
        planner_with_registry: PlannerAgent,
        complete_preprocessor_output: PreprocessorOutput,
    ) -> None:
        """Test that plan estimates total effort."""
        output = await planner_with_registry.plan(complete_preprocessor_output)

        assert output["estimated_total_effort_hours"] >= 0
        assert isinstance(output["estimated_total_effort_hours"], (int, float))

    @pytest.mark.asyncio
    async def test_plan_includes_rationale(
        self,
        planner_with_registry: PlannerAgent,
        complete_preprocessor_output: PreprocessorOutput,
    ) -> None:
        """Test that plan includes planning rationale."""
        output = await planner_with_registry.plan(complete_preprocessor_output)

        assert len(output["planning_rationale"]) > 0


class TestHelperMethods:
    """Tests for helper methods."""

    @pytest.fixture
    def planner(self) -> PlannerAgent:
        """Create planner instance."""
        return PlannerAgent()

    def test_extract_workflow_parameters(
        self, planner: PlannerAgent
    ) -> None:
        """Test extracting workflow parameters."""
        output: PreprocessorOutput = {
            "parsed_sections": {},
            "structure_valid": True,
            "extracted_data": {
                "title": "Test",
                "requirements": ["Req1"],
            },
            "metadata": {"story_type": "api_development"},
            "parsing_errors": [],
            "parsing_warnings": [],
            "input_summary": "",
            "detected_story_type": "api_development",
        }

        params = planner._extract_workflow_parameters("api_development", output)

        assert "story_type" in params
        assert "title" in params
        assert "requirements" in params

    def test_estimate_task_effort_low_complexity(
        self, planner: PlannerAgent
    ) -> None:
        """Test effort estimation for low complexity."""
        output: PreprocessorOutput = {
            "parsed_sections": {},
            "structure_valid": True,
            "extracted_data": {},
            "metadata": {"estimated_complexity": "low"},
            "parsing_errors": [],
            "parsing_warnings": [],
            "input_summary": "",
            "detected_story_type": "api_development",
        }

        effort = planner._estimate_task_effort("api_development", output)

        assert effort == 4.0

    def test_estimate_task_effort_medium_complexity(
        self, planner: PlannerAgent
    ) -> None:
        """Test effort estimation for medium complexity."""
        output: PreprocessorOutput = {
            "parsed_sections": {},
            "structure_valid": True,
            "extracted_data": {},
            "metadata": {"estimated_complexity": "medium"},
            "parsing_errors": [],
            "parsing_warnings": [],
            "input_summary": "",
            "detected_story_type": "api_development",
        }

        effort = planner._estimate_task_effort("api_development", output)

        assert effort == 6.0  # 4.0 * 1.5

    def test_estimate_task_effort_high_complexity(
        self, planner: PlannerAgent
    ) -> None:
        """Test effort estimation for high complexity."""
        output: PreprocessorOutput = {
            "parsed_sections": {},
            "structure_valid": True,
            "extracted_data": {},
            "metadata": {"estimated_complexity": "high"},
            "parsing_errors": [],
            "parsing_warnings": [],
            "input_summary": "",
            "detected_story_type": "api_development",
        }

        effort = planner._estimate_task_effort("api_development", output)

        assert effort == 10.0  # 4.0 * 2.5

    def test_create_planning_rationale(self, planner: PlannerAgent) -> None:
        """Test creating planning rationale."""
        rationale = planner._create_planning_rationale(
            "API development story", ["api_development"], "sequential"
        )

        assert len(rationale) > 0
        assert "api_development" in rationale
        assert "sequential" in rationale
