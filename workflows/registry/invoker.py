"""
Workflow Invoker for executing child workflows.

This module provides a unified interface for invoking workflows in both embedded
(local Python) and A2A (remote service) modes. It handles:
- Dynamic loading of embedded workflow classes
- HTTP communication with A2A services
- Lazy loading and caching of workflow instances
- Error handling and retries
- Request/response validation
"""

import json
import logging
import asyncio
import importlib
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import aiohttp

from workflows.registry.registry import WorkflowMetadata, DeploymentMode
from workflows.parent.state import EnhancedWorkflowState, WorkflowExecutionResult

logger = logging.getLogger(__name__)


class WorkflowInvoker:
    """
    Unified invoker for executing child workflows.

    Supports both embedded (local Python) and A2A (remote service) workflows.
    Handles lazy loading, caching, error handling, and retries.

    Attributes:
        default_timeout: HTTP request timeout in seconds (default: 300)
        default_retries: Number of retries for failed requests (default: 3)
        embedded_workflows_cache: Cache for loaded embedded workflow instances
    """

    def __init__(
        self,
        default_timeout: float = 300.0,
        default_retries: int = 3,
    ):
        """
        Initialize the workflow invoker.

        Args:
            default_timeout: HTTP request timeout in seconds
            default_retries: Number of retries for failed requests
        """
        self.default_timeout = default_timeout
        self.default_retries = default_retries
        self.embedded_workflows_cache: Dict[str, Any] = {}
        logger.info(
            f"WorkflowInvoker initialized (timeout={default_timeout}s, retries={default_retries})"
        )

    async def invoke(
        self,
        workflow_metadata: WorkflowMetadata,
        parent_state: EnhancedWorkflowState,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> WorkflowExecutionResult:
        """
        Invoke a workflow (embedded or A2A) and return the result.

        Args:
            workflow_metadata: Metadata about the workflow to invoke
            parent_state: Parent workflow state to pass to the child workflow
            timeout: Optional timeout override (seconds)
            max_retries: Optional retry count override

        Returns:
            WorkflowExecutionResult with status, output, artifacts, etc.
        """
        timeout_seconds = timeout or self.default_timeout
        retries = max_retries if max_retries is not None else self.default_retries

        try:
            if workflow_metadata.deployment_mode == DeploymentMode.EMBEDDED:
                return await self._invoke_embedded(
                    workflow_metadata, parent_state, timeout_seconds, retries
                )
            elif workflow_metadata.deployment_mode == DeploymentMode.A2A:
                return await self._invoke_a2a(
                    workflow_metadata, parent_state, timeout_seconds, retries
                )
            else:
                raise ValueError(
                    f"Unknown deployment mode: {workflow_metadata.deployment_mode}"
                )

        except Exception as e:
            logger.error(
                f"Error invoking workflow {workflow_metadata.name}: {str(e)}",
                exc_info=True,
            )
            return self._create_error_result(
                workflow_metadata.name, str(e), type(e).__name__
            )

    async def _invoke_embedded(
        self,
        workflow_metadata: WorkflowMetadata,
        parent_state: EnhancedWorkflowState,
        timeout_seconds: float,
        max_retries: int,
    ) -> WorkflowExecutionResult:
        """
        Invoke an embedded (local Python) workflow.

        Args:
            workflow_metadata: Workflow metadata with module_path
            parent_state: Parent workflow state
            timeout_seconds: Request timeout
            max_retries: Maximum retries

        Returns:
            WorkflowExecutionResult
        """
        logger.info(
            f"Invoking embedded workflow: {workflow_metadata.name} "
            f"({workflow_metadata.module_path})"
        )

        # Validate that module_path is provided
        if not workflow_metadata.module_path:
            raise ValueError(
                f"Embedded workflow {workflow_metadata.name} missing module_path"
            )

        # Get or load the workflow instance
        workflow_instance = await self._get_or_load_embedded_workflow(
            workflow_metadata.module_path, workflow_metadata.name
        )

        # Invoke the workflow with retry logic
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(
                    f"Executing embedded workflow {workflow_metadata.name} "
                    f"(attempt {attempt}/{max_retries})"
                )

                # Use asyncio.wait_for for timeout
                result = await asyncio.wait_for(
                    workflow_instance.execute(parent_state), timeout=timeout_seconds
                )

                # Ensure result has expected structure
                result = self._ensure_valid_result(result, workflow_metadata.name)

                logger.info(
                    f"Embedded workflow {workflow_metadata.name} completed with status: {result['status']}"
                )
                return result

            except asyncio.TimeoutError:
                logger.error(
                    f"Embedded workflow {workflow_metadata.name} timed out "
                    f"after {timeout_seconds}s"
                )
                if attempt < max_retries:
                    logger.info("Retrying...")
                    await asyncio.sleep(1)
                else:
                    return self._create_error_result(
                        workflow_metadata.name,
                        f"Workflow timed out after {timeout_seconds}s",
                        "TimeoutError",
                    )

            except Exception as e:
                logger.warning(
                    f"Embedded workflow {workflow_metadata.name} failed "
                    f"(attempt {attempt}/{max_retries}): {str(e)}"
                )
                if attempt < max_retries:
                    await asyncio.sleep(1)
                else:
                    return self._create_error_result(
                        workflow_metadata.name, str(e), type(e).__name__
                    )

        # Fallback (should not reach here)
        return self._create_error_result(
            workflow_metadata.name, "Unknown error", "Exception"
        )

    async def _invoke_a2a(
        self,
        workflow_metadata: WorkflowMetadata,
        parent_state: EnhancedWorkflowState,
        timeout_seconds: float,
        max_retries: int,
    ) -> WorkflowExecutionResult:
        """
        Invoke an A2A (remote service) workflow via HTTP.

        Args:
            workflow_metadata: Workflow metadata with service_url
            parent_state: Parent workflow state
            timeout_seconds: Request timeout
            max_retries: Maximum retries

        Returns:
            WorkflowExecutionResult
        """
        logger.info(
            f"Invoking A2A workflow: {workflow_metadata.name} "
            f"({workflow_metadata.service_url})"
        )

        # Validate that service_url is provided
        if not workflow_metadata.service_url:
            raise ValueError(
                f"A2A workflow {workflow_metadata.name} missing service_url"
            )

        # Build the service endpoint
        service_url = workflow_metadata.service_url.rstrip("/")
        port_suffix = (
            f":{workflow_metadata.service_port}"
            if workflow_metadata.service_port
            else ""
        )
        execute_url = f"{service_url}{port_suffix}/execute"

        # Prepare request payload
        payload = {
            "workflow_name": workflow_metadata.name,
            "parent_state": parent_state,
        }

        # Invoke the service with retry logic
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(
                    f"Executing A2A workflow {workflow_metadata.name} "
                    f"(attempt {attempt}/{max_retries}) at {execute_url}"
                )

                result = await self._make_http_request(
                    execute_url, payload, timeout_seconds
                )

                # Ensure result has expected structure
                result = self._ensure_valid_result(result, workflow_metadata.name)

                logger.info(
                    f"A2A workflow {workflow_metadata.name} completed with status: {result['status']}"
                )
                return result

            except asyncio.TimeoutError:
                logger.error(
                    f"A2A workflow {workflow_metadata.name} timed out "
                    f"after {timeout_seconds}s"
                )
                if attempt < max_retries:
                    logger.info("Retrying...")
                    await asyncio.sleep(1)
                else:
                    return self._create_error_result(
                        workflow_metadata.name,
                        f"Service request timed out after {timeout_seconds}s",
                        "TimeoutError",
                    )

            except Exception as e:
                logger.warning(
                    f"A2A workflow {workflow_metadata.name} failed "
                    f"(attempt {attempt}/{max_retries}): {str(e)}"
                )
                if attempt < max_retries:
                    await asyncio.sleep(1)
                else:
                    return self._create_error_result(
                        workflow_metadata.name, str(e), type(e).__name__
                    )

        # Fallback
        return self._create_error_result(
            workflow_metadata.name, "Unknown error", "Exception"
        )

    async def _get_or_load_embedded_workflow(
        self, module_path: str, workflow_name: str
    ) -> Any:
        """
        Get a cached embedded workflow instance or load it dynamically.

        Args:
            module_path: Python module path (e.g., "workflows.children.api_development.workflow")
            workflow_name: Name of the workflow

        Returns:
            Instantiated workflow object

        Raises:
            ImportError: If module cannot be imported
            AttributeError: If workflow class cannot be found
        """
        # Check cache first
        if module_path in self.embedded_workflows_cache:
            logger.debug(f"Using cached embedded workflow: {module_path}")
            return self.embedded_workflows_cache[module_path]

        try:
            logger.info(f"Loading embedded workflow from: {module_path}")

            # Dynamically import the module
            module = importlib.import_module(module_path)

            # Find the workflow class
            # Convention: Module contains a class that matches the workflow name in CamelCase
            workflow_class_name = self._infer_workflow_class_name(workflow_name)

            if not hasattr(module, workflow_class_name):
                # Try to find any class that looks like a workflow
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and "Workflow" in attr_name
                        and attr_name[0].isupper()
                    ):
                        workflow_class_name = attr_name
                        break
                else:
                    raise AttributeError(
                        f"Cannot find workflow class in {module_path} for {workflow_name}"
                    )

            workflow_class = getattr(module, workflow_class_name)

            # Instantiate the workflow
            workflow_instance = workflow_class()
            logger.info(
                f"Successfully loaded embedded workflow: {module_path}.{workflow_class_name}"
            )

            # Cache the instance
            self.embedded_workflows_cache[module_path] = workflow_instance

            return workflow_instance

        except ImportError as e:
            raise ImportError(f"Cannot import workflow module {module_path}: {str(e)}")
        except AttributeError as e:
            raise AttributeError(f"Cannot find workflow class in {module_path}: {str(e)}")

    def _infer_workflow_class_name(self, workflow_name: str) -> str:
        """
        Infer the workflow class name from workflow name.

        Convention: workflow names are snake_case, class names are CamelCase.
        Example: "api_development" -> "ApiDevelopmentWorkflow"

        Args:
            workflow_name: Workflow name (snake_case)

        Returns:
            Inferred class name (CamelCase)
        """
        # Convert snake_case to CamelCase
        parts = workflow_name.split("_")
        camel_case = "".join(word.capitalize() for word in parts)

        # Add Workflow suffix if not already there
        if not camel_case.endswith("Workflow"):
            camel_case += "Workflow"

        return camel_case

    async def _make_http_request(
        self, url: str, payload: Dict[str, Any], timeout_seconds: float
    ) -> Dict[str, Any]:
        """
        Make an async HTTP POST request to A2A service.

        Args:
            url: Service endpoint URL
            payload: Request payload
            timeout_seconds: Request timeout

        Returns:
            Response JSON as dictionary

        Raises:
            aiohttp.ClientError: On HTTP error
            asyncio.TimeoutError: On timeout
        """
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(
                        f"Service returned status {response.status}: {error_text}"
                    )

                data = await response.json()
                return data

    def _ensure_valid_result(
        self, result: Any, workflow_name: str
    ) -> WorkflowExecutionResult:
        """
        Ensure result has the expected WorkflowExecutionResult structure.

        Args:
            result: Result from workflow execution
            workflow_name: Name of the workflow for logging

        Returns:
            Valid WorkflowExecutionResult

        Raises:
            ValueError: If result is missing required fields
        """
        if not isinstance(result, dict):
            raise ValueError(f"Result must be a dictionary, got {type(result)}")

        # Check required fields
        required_fields = ["status", "output", "artifacts", "execution_time_seconds"]
        missing_fields = [f for f in required_fields if f not in result]

        if missing_fields:
            raise ValueError(
                f"Result missing required fields for {workflow_name}: {missing_fields}"
            )

        # Create properly typed result
        execution_result: WorkflowExecutionResult = {
            "workflow_name": workflow_name,
            "status": str(result.get("status", "unknown")),
            "output": result.get("output", {}),
            "artifacts": result.get("artifacts", []),
            "execution_time_seconds": float(result.get("execution_time_seconds", 0.0)),
            "error": result.get("error"),
            "error_type": result.get("error_type"),
            "metadata": result.get("metadata", {}),
        }

        return execution_result

    def _create_error_result(
        self, workflow_name: str, error_message: str, error_type: str
    ) -> WorkflowExecutionResult:
        """
        Create an error result for a failed workflow execution.

        Args:
            workflow_name: Name of the workflow
            error_message: Error message
            error_type: Type of error

        Returns:
            WorkflowExecutionResult with failure status
        """
        return {
            "workflow_name": workflow_name,
            "status": "failure",
            "output": {},
            "artifacts": [],
            "execution_time_seconds": 0.0,
            "error": error_message,
            "error_type": error_type,
            "metadata": {"error_timestamp": datetime.now().isoformat()},
        }

    def clear_cache(self) -> None:
        """Clear the embedded workflows cache."""
        logger.info(f"Clearing embedded workflows cache ({len(self.embedded_workflows_cache)} items)")
        self.embedded_workflows_cache.clear()

    def get_cached_workflow(self, module_path: str) -> Optional[Any]:
        """
        Get a cached workflow instance without loading.

        Args:
            module_path: Module path to check

        Returns:
            Cached workflow instance or None
        """
        return self.embedded_workflows_cache.get(module_path)

    def list_cached_workflows(self) -> Dict[str, str]:
        """
        List all cached workflow instances.

        Returns:
            Dictionary mapping module paths to class names
        """
        result = {}
        for module_path, instance in self.embedded_workflows_cache.items():
            result[module_path] = f"{instance.__class__.__module__}.{instance.__class__.__name__}"
        return result
