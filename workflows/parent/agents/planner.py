"""
Planner Agent for creating execution plans from workflow stories.

This agent handles:
1. Story scope analysis
2. Identifying required workflows
3. Creating workflow tasks with responsibilities
4. Determining task dependencies
5. Planning execution strategy
6. Identifying risk factors
"""

import json
import logging
import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from workflows.parent.state import (
    PreprocessorOutput,
    PlannerOutput,
    WorkflowTask,
)
from workflows.registry.registry import WorkflowRegistry, get_registry
from workflows.parent.prompts import (
    PLANNER_SCOPE_ANALYSIS_TEMPLATE,
    PLANNER_WORKFLOW_IDENTIFICATION_TEMPLATE,
    PLANNER_RESPONSIBILITY_DEFINITION_TEMPLATE,
    PLANNER_RISK_ASSESSMENT_TEMPLATE,
)

logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    Agent responsible for planning workflow execution from preprocessed stories.

    The planner:
    1. Analyzes story scope and complexity
    2. Identifies which workflows are required
    3. Creates detailed workflow tasks
    4. Determines task dependencies
    5. Plans optimal execution strategy
    6. Identifies potential risk factors

    Attributes:
        llm: Language model client (ChatOpenAI or ChatAnthropic)
        registry: WorkflowRegistry for available workflows
    """

    def __init__(self, llm=None, registry: Optional[WorkflowRegistry] = None):
        """
        Initialize the planner agent.

        Args:
            llm: Language model client
            registry: WorkflowRegistry instance (uses global if not provided)
        """
        self.llm = llm
        self.registry = registry or get_registry()
        logger.info("PlannerAgent initialized")

    async def plan(self, preprocessor_output: PreprocessorOutput) -> PlannerOutput:
        """
        Create a comprehensive execution plan from preprocessed story.

        Args:
            preprocessor_output: Output from the preprocessor agent

        Returns:
            PlannerOutput TypedDict with complete execution plan

        Raises:
            ValueError: If planning fails critically
        """
        errors: List[str] = []

        try:
            # Step 1: Analyze story scope
            story_scope = await self._analyze_story_scope(preprocessor_output)

            # Step 2: Identify required workflows
            required_workflows = await self._identify_required_workflows(
                preprocessor_output, story_scope
            )
            if not required_workflows:
                errors.append("No workflows identified for this story")

            # Step 3: Create workflow tasks
            workflow_tasks = await self._create_workflow_tasks(
                required_workflows, preprocessor_output
            )
            if not workflow_tasks:
                errors.append("Failed to create workflow tasks")

            # Step 4: Determine dependencies
            task_dependencies = self._determine_dependencies(workflow_tasks)

            # Step 5: Determine execution strategy
            execution_strategy, execution_order = self._determine_execution_strategy(
                workflow_tasks, task_dependencies
            )

            # Step 6: Identify risk factors
            risk_factors = await self._identify_risk_factors(
                workflow_tasks, preprocessor_output
            )

            # Calculate estimated effort
            estimated_effort = sum(
                task.get("estimated_effort_hours", 1.0) for task in workflow_tasks
            )

            # Create output
            output: PlannerOutput = {
                "story_scope": story_scope,
                "required_workflows": required_workflows,
                "workflow_tasks": workflow_tasks,
                "task_dependencies": task_dependencies,
                "execution_strategy": execution_strategy,
                "execution_order": execution_order,
                "risk_factors": risk_factors,
                "estimated_total_effort_hours": estimated_effort,
                "planning_rationale": self._create_planning_rationale(
                    story_scope, required_workflows, execution_strategy
                ),
                "planning_errors": errors,
            }

            logger.info(
                f"Planning complete: {len(required_workflows)} workflows, "
                f"strategy={execution_strategy}, effort={estimated_effort}h, "
                f"errors={len(errors)}"
            )
            return output

        except Exception as e:
            logger.error(f"Planner error: {str(e)}", exc_info=True)
            return {
                "story_scope": "",
                "required_workflows": [],
                "workflow_tasks": [],
                "task_dependencies": {},
                "execution_strategy": "unknown",
                "execution_order": [],
                "risk_factors": [],
                "estimated_total_effort_hours": 0.0,
                "planning_rationale": f"Planning failed: {str(e)}",
                "planning_errors": [str(e)],
            }

    async def _analyze_story_scope(
        self, preprocessor_output: PreprocessorOutput
    ) -> str:
        """
        Analyze the scope of the story using LLM.

        Args:
            preprocessor_output: Output from preprocessor

        Returns:
            Detailed scope analysis as string
        """
        try:
            story_type = preprocessor_output.get("detected_story_type", "unknown")
            title = preprocessor_output.get("metadata", {}).get("title", "Unknown")
            requirements = preprocessor_output.get("extracted_data", {}).get(
                "requirements", []
            )

            if not self.llm:
                # Heuristic analysis
                scope = f"Story Type: {story_type}. Title: {title}. "
                scope += f"Identified {len(requirements)} requirements. "
                if len(requirements) > 0:
                    scope += f"Key requirements: {', '.join(requirements[:3])}"
                return scope

            requirements_json = json.dumps(requirements[:5], indent=2)
            constraints = preprocessor_output.get("extracted_data", {}).get("constraints", [])
            constraints_json = json.dumps(constraints[:5], indent=2)

            prompt = PLANNER_SCOPE_ANALYSIS_TEMPLATE.format(
                story_type=story_type,
                title=title,
                requirements_json=requirements_json,
                constraints_json=constraints_json
            )
            # Directly await async method (not asyncio.to_thread for async functions)
            analysis_text = await self.llm.invoke([{"role": "user", "content": prompt}])
            logger.info("Story scope analysis complete")
            return analysis_text.strip()

        except Exception as e:
            logger.warning(f"Scope analysis failed: {str(e)}")
            return "Unable to analyze scope"

    async def _identify_required_workflows(
        self, preprocessor_output: PreprocessorOutput, story_scope: str
    ) -> List[str]:
        """
        Identify which workflows are required for this story.

        Args:
            preprocessor_output: Preprocessor output
            story_scope: Story scope analysis

        Returns:
            List of workflow names
        """
        try:
            story_type = preprocessor_output.get("detected_story_type", "unknown")

            # Try to match with registry
            available_workflows = self.registry.list_all()
            matching = [
                wf.name for wf in available_workflows
                if story_type.lower() in wf.workflow_type.lower()
            ]

            if matching:
                logger.info(f"Identified {len(matching)} workflows: {matching}")
                return matching

            # Fallback: use heuristic mapping
            workflow_map: Dict[str, List[str]] = {
                "api_development": ["api_development"],
                "api_enhancement": ["api_enhancement"],
                "ui_development": ["ui_development"],
                "ui_enhancement": ["ui_enhancement"],
            }

            workflows = workflow_map.get(story_type, [])

            if not workflows and self.llm:
                # Use LLM to identify workflows
                story_type = preprocessor_output.get("detected_story_type", "unknown")
                title = preprocessor_output.get("metadata", {}).get("title", "Unknown")
                requirements = preprocessor_output.get("extracted_data", {}).get("requirements", [])
                requirements_json = json.dumps(requirements[:5], indent=2)
                workflow_names = "\n".join([f"- {wf.name}" for wf in available_workflows[:10]])

                prompt = PLANNER_WORKFLOW_IDENTIFICATION_TEMPLATE.format(
                    story_type=story_type,
                    title=title,
                    requirements_json=requirements_json,
                    available_workflows=workflow_names
                )
                # Directly await async method (not asyncio.to_thread for async functions)
                response_text = await self.llm.invoke([{"role": "user", "content": prompt}])
                workflows = self._parse_workflow_list(response_text)

            logger.info(f"Required workflows: {workflows}")
            return workflows

        except Exception as e:
            logger.warning(f"Workflow identification failed: {str(e)}")
            return []

    async def _create_workflow_tasks(
        self, required_workflows: List[str], preprocessor_output: PreprocessorOutput
    ) -> List[WorkflowTask]:
        """
        Create detailed workflow tasks with responsibilities.

        Args:
            required_workflows: List of workflow names
            preprocessor_output: Preprocessor output

        Returns:
            List of WorkflowTask dictionaries
        """
        tasks: List[WorkflowTask] = []

        try:
            available_workflows = {
                wf.name: wf for wf in self.registry.list_all()
            }

            for idx, workflow_name in enumerate(required_workflows):
                workflow_meta = available_workflows.get(workflow_name)

                # Define responsibilities
                responsibilities = await self._define_workflow_responsibilities(
                    workflow_name, preprocessor_output
                )

                # Create task
                task: WorkflowTask = {
                    "task_id": f"task_{idx + 1}",
                    "workflow_name": workflow_name,
                    "workflow_type": workflow_meta.workflow_type if workflow_meta else "unknown",
                    "responsibilities": responsibilities,
                    "dependencies": [],
                    "parameters": self._extract_workflow_parameters(
                        workflow_name, preprocessor_output
                    ),
                    "status": "pending",
                    "priority": idx + 1,
                    "estimated_effort_hours": self._estimate_task_effort(
                        workflow_name, preprocessor_output
                    ),
                }

                tasks.append(task)
                logger.debug(f"Created task: {task['task_id']} for {workflow_name}")

            logger.info(f"Created {len(tasks)} workflow tasks")
            return tasks

        except Exception as e:
            logger.warning(f"Task creation failed: {str(e)}")
            return []

    async def _define_workflow_responsibilities(
        self, workflow_name: str, preprocessor_output: PreprocessorOutput
    ) -> str:
        """
        Define detailed responsibilities for a workflow using LLM.

        Args:
            workflow_name: Name of the workflow
            preprocessor_output: Preprocessor output

        Returns:
            String describing workflow responsibilities
        """
        try:
            if not self.llm:
                # Heuristic responsibilities
                if "api" in workflow_name.lower():
                    return "Design and implement API endpoints, handle authentication, and create tests"
                elif "ui" in workflow_name.lower():
                    return "Design UI components, implement responsive layouts, and ensure accessibility"
                return f"Execute {workflow_name} workflow"

            requirements = preprocessor_output.get("extracted_data", {}).get("requirements", [])
            requirements_json = json.dumps(requirements[:5], indent=2)

            prompt = PLANNER_RESPONSIBILITY_DEFINITION_TEMPLATE.format(
                workflow_name=workflow_name,
                requirements_json=requirements_json
            )
            # Directly await async method (not asyncio.to_thread for async functions)
            resp_text = await self.llm.invoke([{"role": "user", "content": prompt}])
            return resp_text.strip()

        except Exception as e:
            logger.warning(f"Responsibility definition failed: {str(e)}")
            return f"Execute {workflow_name}"

    def _determine_dependencies(
        self, workflow_tasks: List[WorkflowTask]
    ) -> Dict[str, List[str]]:
        """
        Determine task dependencies based on workflow types.

        Args:
            workflow_tasks: List of workflow tasks

        Returns:
            Dictionary mapping task IDs to dependent task IDs
        """
        dependencies: Dict[str, List[str]] = {}

        # Default dependencies based on workflow type
        for task in workflow_tasks:
            task_id = task["task_id"]
            task_deps: List[str] = []

            workflow_type = task.get("workflow_type", "").lower()

            # Enhancement workflows depend on development workflows
            if "enhancement" in workflow_type:
                # Find corresponding development task
                for other_task in workflow_tasks:
                    other_type = other_task.get("workflow_type", "").lower()
                    if (
                        "development" in other_type
                        and other_type.replace("_development", "")
                        == workflow_type.replace("_enhancement", "")
                    ):
                        task_deps.append(other_task["task_id"])

            dependencies[task_id] = task_deps

        logger.debug(f"Determined dependencies: {dependencies}")
        return dependencies

    def _determine_execution_strategy(
        self,
        workflow_tasks: List[WorkflowTask],
        task_dependencies: Dict[str, List[str]],
    ) -> Tuple[str, List[str]]:
        """
        Determine optimal execution strategy.

        Args:
            workflow_tasks: List of workflow tasks
            task_dependencies: Task dependency mapping

        Returns:
            Tuple of (strategy, execution_order)
        """
        if not workflow_tasks:
            return "unknown", []

        # Check if any dependencies exist
        has_dependencies = any(deps for deps in task_dependencies.values())

        if not has_dependencies and len(workflow_tasks) > 1:
            strategy = "parallel"
        elif has_dependencies:
            strategy = "hybrid"
        else:
            strategy = "sequential"

        # Determine execution order using topological sort
        execution_order = self._topological_sort(workflow_tasks, task_dependencies)

        logger.info(f"Execution strategy: {strategy}, order: {execution_order}")
        return strategy, execution_order

    def _topological_sort(
        self,
        workflow_tasks: List[WorkflowTask],
        task_dependencies: Dict[str, List[str]],
    ) -> List[str]:
        """
        Perform topological sort on tasks based on dependencies.

        Args:
            workflow_tasks: List of workflow tasks
            task_dependencies: Task dependency mapping

        Returns:
            List of task IDs in execution order
        """
        # Build adjacency info
        task_ids = [t["task_id"] for t in workflow_tasks]
        in_degree = {task_id: 0 for task_id in task_ids}

        for task_id, deps in task_dependencies.items():
            in_degree[task_id] = len(deps)

        # Find tasks with no dependencies
        queue = [task_id for task_id in task_ids if in_degree[task_id] == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # Find tasks that depend on current
            for task_id, deps in task_dependencies.items():
                if current in deps:
                    in_degree[task_id] -= 1
                    if in_degree[task_id] == 0:
                        queue.append(task_id)

        return result if len(result) == len(task_ids) else task_ids

    async def _identify_risk_factors(
        self, workflow_tasks: List[WorkflowTask], preprocessor_output: PreprocessorOutput
    ) -> List[Dict[str, str]]:
        """
        Identify potential risk factors in the plan.

        Args:
            workflow_tasks: List of workflow tasks
            preprocessor_output: Preprocessor output

        Returns:
            List of risk factors with severity
        """
        risk_factors: List[Dict[str, str]] = []

        try:
            # Heuristic risk detection
            complexity = (
                preprocessor_output.get("metadata", {}).get("estimated_complexity", "low")
            )
            if complexity == "high":
                risk_factors.append({
                    "factor": "High story complexity",
                    "severity": "high",
                    "mitigation": "Break into smaller sub-tasks, allocate extra time"
                })

            requirements_count = (
                len(preprocessor_output.get("extracted_data", {}).get("requirements", []))
            )
            if requirements_count > 10:
                risk_factors.append({
                    "factor": "Large number of requirements",
                    "severity": "medium",
                    "mitigation": "Prioritize requirements, consider phased delivery"
                })

            # LLM-based risk assessment
            if self.llm and len(workflow_tasks) > 0:
                task_names = ", ".join([t["workflow_name"] for t in workflow_tasks])
                constraints = preprocessor_output.get("extracted_data", {}).get("constraints", [])
                constraints_json = json.dumps(constraints[:5], indent=2)

                prompt = PLANNER_RISK_ASSESSMENT_TEMPLATE.format(
                    task_names=task_names,
                    constraints_json=constraints_json
                )
                # Directly await async method (not asyncio.to_thread for async functions)
                response_text = await self.llm.invoke([{"role": "user", "content": prompt}])
                llm_risks = self._parse_risk_factors(response_text)
                risk_factors.extend(llm_risks)

            logger.info(f"Identified {len(risk_factors)} risk factors")
            return risk_factors

        except Exception as e:
            logger.warning(f"Risk identification failed: {str(e)}")
            return []

    # ========== Helper Methods ==========

    def _create_planning_rationale(
        self, story_scope: str, required_workflows: List[str], strategy: str
    ) -> str:
        """Create explanation of planning decisions."""
        return (
            f"Selected {len(required_workflows)} workflows ({', '.join(required_workflows)}) "
            f"using {strategy} execution strategy. {story_scope[:100]}..."
        )

    def _extract_workflow_parameters(
        self, workflow_name: str, preprocessor_output: PreprocessorOutput
    ) -> Dict[str, Any]:
        """Extract parameters to pass to workflow."""
        parameters: Dict[str, Any] = {
            "story_type": preprocessor_output.get("detected_story_type", "unknown"),
            "title": preprocessor_output.get("metadata", {}).get("title", ""),
            "requirements": preprocessor_output.get("extracted_data", {}).get(
                "requirements", []
            ),
        }
        return parameters

    def _estimate_task_effort(
        self, workflow_name: str, preprocessor_output: PreprocessorOutput
    ) -> float:
        """Estimate effort hours for a workflow task."""
        base_effort = 4.0  # Default 4 hours

        complexity = (
            preprocessor_output.get("metadata", {}).get("estimated_complexity", "low")
        )
        if complexity == "medium":
            base_effort *= 1.5
        elif complexity == "high":
            base_effort *= 2.5

        return base_effort

    def _parse_workflow_list(self, response: Any) -> List[str]:
        """Parse LLM response to extract workflow list."""
        try:
            response_text = (
                response.content if hasattr(response, "content") else str(response)
            )
            # Try to extract JSON array
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if json_match:
                workflows: List[str] = json.loads(json_match.group(0))
                return workflows
            return []
        except Exception as e:
            logger.warning(f"Failed to parse workflow list: {str(e)}")
            return []

    def _parse_risk_factors(self, response: Any) -> List[Dict[str, str]]:
        """Parse LLM response to extract risk factors."""
        try:
            response_text = (
                response.content if hasattr(response, "content") else str(response)
            )
            # Try to extract JSON array
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if json_match:
                factors: List[Dict[str, str]] = json.loads(json_match.group(0))
                return factors
            return []
        except Exception as e:
            logger.warning(f"Failed to parse risk factors: {str(e)}")
            return []
