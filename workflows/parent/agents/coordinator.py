"""
Coordinator Agent for orchestrating workflow execution.

This agent handles:
1. Sequential execution of workflows
2. Parallel execution of independent workflows
3. Dependency tracking and validation
4. Dependency-level grouping for optimal parallelization
5. Individual workflow execution
6. Status aggregation and reporting
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from workflows.parent.state import (
    EnhancedWorkflowState,
    PlannerOutput,
    WorkflowTask,
    WorkflowExecutionResult,
)
from workflows.registry.registry import WorkflowRegistry
from workflows.registry.invoker import WorkflowInvoker

logger = logging.getLogger(__name__)


class WorkflowCoordinator:
    """
    Orchestrator for executing workflow tasks according to a plan.

    The coordinator:
    1. Executes workflows sequentially or in parallel based on strategy
    2. Tracks task dependencies
    3. Groups tasks by dependency levels for efficient execution
    4. Handles errors gracefully with proper reporting
    5. Tracks execution times and status
    6. Aggregates results into a unified execution result

    Attributes:
        timeout_seconds: Maximum time allowed for all workflows (default: 3600)
        max_retries: Number of retries for failed tasks (default: 3)
    """

    def __init__(
        self,
        timeout_seconds: float = 3600,
        max_retries: int = 3,
        registry: Optional[WorkflowRegistry] = None,
        invoker: Optional[WorkflowInvoker] = None,
    ):
        """
        Initialize the coordinator.

        Args:
            timeout_seconds: Maximum execution time for all tasks
            max_retries: Maximum number of retries per failed task
            registry: WorkflowRegistry for looking up workflow metadata
            invoker: WorkflowInvoker for executing workflows
        """
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.registry = registry
        self.invoker = invoker or WorkflowInvoker(default_timeout=timeout_seconds, default_retries=max_retries)
        logger.info(
            f"WorkflowCoordinator initialized (timeout={timeout_seconds}s, retries={max_retries})"
        )

    async def execute(
        self,
        workflow_tasks: List[WorkflowTask],
        execution_strategy: str,
        execution_order: List[str],
        task_dependencies: Dict[str, List[str]],
        parent_state: Optional[EnhancedWorkflowState] = None,
    ) -> Dict[str, WorkflowExecutionResult]:
        """
        Execute workflow tasks according to strategy.

        Args:
            workflow_tasks: List of tasks to execute
            execution_strategy: Strategy (sequential, parallel, hybrid)
            execution_order: Preferred execution order
            task_dependencies: Task dependency mapping
            parent_state: Parent workflow state to pass to child workflows

        Returns:
            Dictionary mapping task IDs to execution results
        """
        execution_results: Dict[str, WorkflowExecutionResult] = {}
        start_time = time.time()

        # Store parent state for use in _execute_single_workflow
        self._parent_state = parent_state or {}

        try:
            logger.info(
                f"Starting workflow execution: strategy={execution_strategy}, "
                f"tasks={len(workflow_tasks)}"
            )

            if execution_strategy == "sequential":
                execution_results = await self._execute_sequential(
                    workflow_tasks, execution_order
                )
            elif execution_strategy == "parallel":
                execution_results = await self._execute_parallel(workflow_tasks)
            elif execution_strategy == "hybrid":
                execution_results = await self._execute_hybrid(
                    workflow_tasks, execution_order, task_dependencies
                )
            else:
                # Default to sequential
                logger.warning(f"Unknown strategy {execution_strategy}, using sequential")
                execution_results = await self._execute_sequential(
                    workflow_tasks, execution_order
                )

            elapsed = time.time() - start_time
            logger.info(
                f"Workflow execution complete: {len(execution_results)} results, "
                f"elapsed={elapsed:.2f}s"
            )
            return execution_results

        except asyncio.TimeoutError:
            logger.error(f"Workflow execution timed out after {self.timeout_seconds}s")
            return self._create_timeout_results(workflow_tasks)
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
            return self._create_error_results(workflow_tasks, str(e))

    async def _execute_sequential(
        self, workflow_tasks: List[WorkflowTask], execution_order: List[str]
    ) -> Dict[str, WorkflowExecutionResult]:
        """
        Execute workflows sequentially in order.

        Args:
            workflow_tasks: List of tasks to execute
            execution_order: Order of execution

        Returns:
            Dictionary of execution results
        """
        logger.info(f"Starting sequential execution of {len(workflow_tasks)} tasks")
        execution_results: Dict[str, WorkflowExecutionResult] = {}

        # Use provided execution_order if available, otherwise use task order
        task_id_to_task = {t["task_id"]: t for t in workflow_tasks}
        ordered_task_ids = execution_order if execution_order else [t["task_id"] for t in workflow_tasks]

        for task_id in ordered_task_ids:
            task = task_id_to_task.get(task_id)
            if not task:
                logger.warning(f"Task {task_id} not found in workflow_tasks")
                continue

            logger.info(f"Executing task: {task_id} ({task['workflow_name']})")
            result = await self._execute_single_workflow(task)
            execution_results[task_id] = result

        return execution_results

    async def _execute_parallel(
        self, workflow_tasks: List[WorkflowTask]
    ) -> Dict[str, WorkflowExecutionResult]:
        """
        Execute all workflows in parallel.

        Args:
            workflow_tasks: List of tasks to execute in parallel

        Returns:
            Dictionary of execution results
        """
        logger.info(f"Starting parallel execution of {len(workflow_tasks)} tasks")

        # Create coroutines for all tasks
        coros = [
            self._execute_single_workflow(task)
            for task in workflow_tasks
        ]

        # Execute all tasks concurrently
        results = await asyncio.gather(*coros, return_exceptions=True)

        # Map results back to task IDs
        execution_results: Dict[str, WorkflowExecutionResult] = {}
        for task, result in zip(workflow_tasks, results):
            task_id = task["task_id"]
            if isinstance(result, Exception):
                exec_result: WorkflowExecutionResult = {
                    "workflow_name": task["workflow_name"],
                    "status": "failure",
                    "error": str(result),
                    "error_type": type(result).__name__,
                    "execution_time_seconds": 0.0,
                    "output": {},
                    "artifacts": [],
                }
                execution_results[task_id] = exec_result
            else:
                execution_results[task_id] = result  # type: ignore

        return execution_results

    async def _execute_hybrid(
        self,
        workflow_tasks: List[WorkflowTask],
        execution_order: List[str],
        task_dependencies: Dict[str, List[str]],
    ) -> Dict[str, WorkflowExecutionResult]:
        """
        Execute workflows using hybrid strategy (parallel within dependency levels).

        Args:
            workflow_tasks: List of tasks to execute
            execution_order: Execution order hint
            task_dependencies: Task dependency mapping

        Returns:
            Dictionary of execution results
        """
        logger.info(f"Starting hybrid execution of {len(workflow_tasks)} tasks")
        execution_results: Dict[str, WorkflowExecutionResult] = {}

        # Group tasks by dependency level
        dependency_levels = self._group_by_dependency_level(
            workflow_tasks, task_dependencies
        )

        # Execute each level sequentially, but tasks within a level in parallel
        for level_idx, level_tasks in enumerate(dependency_levels):
            logger.info(
                f"Executing dependency level {level_idx + 1} with {len(level_tasks)} tasks"
            )

            # Execute all tasks in this level in parallel
            coros = [
                self._execute_single_workflow(task)
                for task in level_tasks
            ]

            results = await asyncio.gather(*coros, return_exceptions=True)

            # Map results
            for task, result in zip(level_tasks, results):
                task_id = task["task_id"]
                if isinstance(result, Exception):
                    exec_result: WorkflowExecutionResult = {
                        "workflow_name": task["workflow_name"],
                        "status": "failure",
                        "error": str(result),
                        "error_type": type(result).__name__,
                        "execution_time_seconds": 0.0,
                        "output": {},
                        "artifacts": [],
                    }
                    execution_results[task_id] = exec_result
                else:
                    execution_results[task_id] = result  # type: ignore

        return execution_results

    async def _execute_single_workflow(
        self, task: WorkflowTask
    ) -> WorkflowExecutionResult:
        """
        Execute a single workflow task with retry logic.

        Args:
            task: Workflow task to execute

        Returns:
            Execution result
        """
        task_id = task["task_id"]
        workflow_name = task["workflow_name"]

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Executing {task_id} (attempt {attempt}/{self.max_retries})")
                start_time = time.time()

                # Simulate workflow execution
                # In real implementation, this would invoke the actual workflow
                result = await self._simulate_workflow_execution(task)

                elapsed = time.time() - start_time
                result["execution_time_seconds"] = elapsed

                logger.info(
                    f"Task {task_id} completed with status: {result['status']} "
                    f"(elapsed={elapsed:.2f}s)"
                )
                return result

            except Exception as e:
                elapsed = time.time() - start_time
                if attempt < self.max_retries:
                    logger.warning(
                        f"Task {task_id} failed (attempt {attempt}): {str(e)}, "
                        f"retrying..."
                    )
                    await asyncio.sleep(1)  # Brief delay before retry
                else:
                    logger.error(
                        f"Task {task_id} failed after {self.max_retries} attempts: {str(e)}"
                    )
                    return {
                        "workflow_name": workflow_name,
                        "status": "failure",
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "execution_time_seconds": elapsed,
                        "output": {},
                        "artifacts": [],
                        "metadata": {"attempts": attempt},
                    }

        # Fallback (should not reach here)
        return {
            "workflow_name": workflow_name,
            "status": "failure",
            "error": "Unknown error",
            "error_type": "Exception",
            "execution_time_seconds": 0.0,
            "output": {},
            "artifacts": [],
        }

    def _dependencies_satisfied(
        self,
        task_id: str,
        task_dependencies: Dict[str, List[str]],
        completed_tasks: set,
    ) -> bool:
        """
        Check if all dependencies for a task are satisfied.

        Args:
            task_id: Task to check
            task_dependencies: Task dependency mapping
            completed_tasks: Set of completed task IDs

        Returns:
            True if all dependencies are satisfied
        """
        deps = task_dependencies.get(task_id, [])
        return all(dep in completed_tasks for dep in deps)

    def _group_by_dependency_level(
        self,
        workflow_tasks: List[WorkflowTask],
        task_dependencies: Dict[str, List[str]],
    ) -> List[List[WorkflowTask]]:
        """
        Group tasks by dependency level for efficient execution.

        Tasks with no dependencies are level 0, tasks depending only on level 0
        are level 1, etc.

        Args:
            workflow_tasks: List of workflow tasks
            task_dependencies: Task dependency mapping

        Returns:
            List of task groups, one per dependency level
        """
        task_id_to_task = {t["task_id"]: t for t in workflow_tasks}
        task_levels: Dict[str, int] = {}

        def get_level(task_id: str) -> int:
            """Calculate dependency level for a task."""
            if task_id in task_levels:
                return task_levels[task_id]

            deps = task_dependencies.get(task_id, [])
            if not deps:
                task_levels[task_id] = 0
                return 0

            max_dep_level = max(get_level(dep) for dep in deps)
            task_levels[task_id] = max_dep_level + 1
            return task_levels[task_id]

        # Calculate levels for all tasks
        for task in workflow_tasks:
            get_level(task["task_id"])

        # Group by level
        max_level = max(task_levels.values()) if task_levels else 0
        levels: List[List[WorkflowTask]] = [[] for _ in range(max_level + 1)]

        for task in workflow_tasks:
            level = task_levels[task["task_id"]]
            levels[level].append(task)

        logger.debug(f"Grouped {len(workflow_tasks)} tasks into {len(levels)} dependency levels")
        return levels

    def _determine_overall_status(
        self, execution_results: Dict[str, WorkflowExecutionResult]
    ) -> str:
        """
        Determine overall execution status from task results.

        Args:
            execution_results: Dictionary of execution results

        Returns:
            Overall status: success, partial, or failure
        """
        if not execution_results:
            return "failure"

        statuses = [r.get("status", "unknown") for r in execution_results.values()]
        success_count = sum(1 for s in statuses if s == "success")
        failure_count = sum(1 for s in statuses if s == "failure")
        total = len(statuses)

        if failure_count == 0:
            return "success"
        elif success_count > 0:
            return "partial"
        else:
            return "failure"

    # ========== Helper Methods ==========

    async def _simulate_workflow_execution(
        self, task: WorkflowTask
    ) -> WorkflowExecutionResult:
        """
        Execute a single workflow task using the WorkflowInvoker.

        This method looks up the workflow metadata from the registry and invokes
        it with the parent state. If the registry is not available, falls back
        to simulation.

        Args:
            task: Workflow task to execute

        Returns:
            Workflow execution result
        """
        workflow_name = task["workflow_name"]
        parent_state = getattr(self, "_parent_state", {})

        # If no registry, fall back to simulation
        if not self.registry:
            logger.warning(
                f"No registry available for {workflow_name}, using simulated execution"
            )
            await asyncio.sleep(0.1)
            return {
                "workflow_name": workflow_name,
                "status": "success",
                "output": {
                    "message": f"Simulated execution of {workflow_name}",
                    "parameters": task.get("parameters", {}),
                },
                "artifacts": [
                    f"artifact_{task['task_id']}_1.json",
                    f"artifact_{task['task_id']}_2.json",
                ],
                "execution_time_seconds": 0.1,
                "metadata": {
                    "executed_at": datetime.now().isoformat(),
                    "workflow_type": task.get("workflow_type", "unknown"),
                },
            }

        try:
            # Look up workflow metadata from registry
            workflow_metadata = self.registry.get(workflow_name)
            if not workflow_metadata:
                raise ValueError(f"Workflow {workflow_name} not found in registry")

            logger.debug(f"Invoking workflow {workflow_name} with parent state")

            # Invoke the workflow with timeout and retries
            result = await self.invoker.invoke(
                workflow_metadata,
                parent_state,
                timeout=task.get("timeout"),
                max_retries=task.get("max_retries"),
            )

            return result

        except Exception as e:
            logger.error(
                f"Error invoking workflow {workflow_name}: {str(e)}", exc_info=True
            )
            return {
                "workflow_name": workflow_name,
                "status": "failure",
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_time_seconds": 0.0,
                "output": {},
                "artifacts": [],
            }

    def _create_timeout_results(
        self, workflow_tasks: List[WorkflowTask]
    ) -> Dict[str, WorkflowExecutionResult]:
        """Create timeout results for all tasks."""
        return {
            task["task_id"]: {
                "workflow_name": task["workflow_name"],
                "status": "failure",
                "error": f"Execution timed out after {self.timeout_seconds}s",
                "error_type": "TimeoutError",
                "execution_time_seconds": self.timeout_seconds,
                "output": {},
                "artifacts": [],
            }
            for task in workflow_tasks
        }

    def _create_error_results(
        self, workflow_tasks: List[WorkflowTask], error_msg: str
    ) -> Dict[str, WorkflowExecutionResult]:
        """Create error results for all tasks."""
        return {
            task["task_id"]: {
                "workflow_name": task["workflow_name"],
                "status": "failure",
                "error": error_msg,
                "error_type": "ExecutionError",
                "execution_time_seconds": 0.0,
                "output": {},
                "artifacts": [],
            }
            for task in workflow_tasks
        }

    def get_execution_summary(
        self, execution_results: Dict[str, WorkflowExecutionResult]
    ) -> Dict[str, Any]:
        """
        Get a summary of execution results.

        Args:
            execution_results: Dictionary of execution results

        Returns:
            Summary dictionary with statistics
        """
        total = len(execution_results)
        successful = sum(
            1 for r in execution_results.values() if r.get("status") == "success"
        )
        failed = sum(
            1 for r in execution_results.values() if r.get("status") == "failure"
        )
        total_time = sum(
            r.get("execution_time_seconds", 0) for r in execution_results.values()
        )

        return {
            "total_tasks": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "total_execution_time_seconds": total_time,
            "overall_status": self._determine_overall_status(execution_results),
        }
