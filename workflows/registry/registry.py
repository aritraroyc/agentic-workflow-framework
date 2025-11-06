"""
Workflow registry system for managing workflow registration and discovery.

This module provides the central registry for managing workflows in both embedded
(local Python classes) and A2A (Application-to-Application service) modes.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class DeploymentMode(Enum):
    """Enumeration of workflow deployment modes."""

    EMBEDDED = "embedded"  # Local Python implementation
    A2A = "a2a"  # Remote service (HTTP-based)


@dataclass
class WorkflowMetadata:
    """
    Metadata about a workflow.

    Attributes:
        name: Unique identifier for the workflow
        workflow_type: Type/category of the workflow (e.g., api_development, ui_development)
        description: Human-readable description of what the workflow does
        version: Semantic version of the workflow
        deployment_mode: How the workflow is deployed (EMBEDDED or A2A)
        input_schema: JSON schema describing expected input parameters
        output_schema: JSON schema describing output structure
        dependencies: List of required Python packages or services
        module_path: For EMBEDDED mode: Python module path (e.g., "workflows.children.api_development")
        service_url: For A2A mode: Base URL of the remote service
        service_port: For A2A mode: Port number of the service
        tags: List of tags for categorization/search
        is_active: Whether this workflow is available for use
        created_at: ISO timestamp when workflow was registered
        updated_at: ISO timestamp when workflow was last updated
        author: Name of the workflow creator
        metadata: Additional custom metadata
    """

    name: str
    workflow_type: str
    description: str
    version: str
    deployment_mode: DeploymentMode
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    module_path: Optional[str] = None
    service_url: Optional[str] = None
    service_port: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    author: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate metadata after initialization."""
        if self.deployment_mode == DeploymentMode.EMBEDDED:
            if not self.module_path:
                raise ValueError(
                    f"Embedded workflow '{self.name}' requires 'module_path'"
                )
        elif self.deployment_mode == DeploymentMode.A2A:
            if not self.service_url:
                raise ValueError(
                    f"A2A workflow '{self.name}' requires 'service_url'"
                )

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "workflow_type": self.workflow_type,
            "description": self.description,
            "version": self.version,
            "deployment_mode": self.deployment_mode.value,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "dependencies": self.dependencies,
            "module_path": self.module_path,
            "service_url": self.service_url,
            "service_port": self.service_port,
            "tags": self.tags,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
            "metadata": self.metadata,
        }


class WorkflowRegistry:
    """
    Central registry for managing workflows.

    This registry maintains metadata about all available workflows and provides
    methods to register, retrieve, and list workflows.
    """

    def __init__(self) -> None:
        """Initialize the registry."""
        self._workflows: Dict[str, WorkflowMetadata] = {}
        self._workflow_by_type: Dict[str, List[str]] = {}
        logger.info("WorkflowRegistry initialized")

    def register(self, metadata: WorkflowMetadata) -> None:
        """
        Register a workflow with the registry.

        Args:
            metadata: WorkflowMetadata object describing the workflow

        Raises:
            ValueError: If a workflow with the same name is already registered
        """
        if metadata.name in self._workflows:
            raise ValueError(
                f"Workflow '{metadata.name}' is already registered"
            )

        self._workflows[metadata.name] = metadata

        # Index by workflow type for quick lookup
        if metadata.workflow_type not in self._workflow_by_type:
            self._workflow_by_type[metadata.workflow_type] = []
        self._workflow_by_type[metadata.workflow_type].append(metadata.name)

        logger.info(
            f"Registered workflow '{metadata.name}' "
            f"(type: {metadata.workflow_type}, mode: {metadata.deployment_mode.value})"
        )

    def get(self, workflow_name: str) -> Optional[WorkflowMetadata]:
        """
        Get workflow metadata by name.

        Args:
            workflow_name: Name of the workflow to retrieve

        Returns:
            WorkflowMetadata if found, None otherwise
        """
        return self._workflows.get(workflow_name)

    def get_or_raise(self, workflow_name: str) -> WorkflowMetadata:
        """
        Get workflow metadata by name, raising if not found.

        Args:
            workflow_name: Name of the workflow to retrieve

        Returns:
            WorkflowMetadata

        Raises:
            KeyError: If workflow is not found
        """
        if workflow_name not in self._workflows:
            raise KeyError(f"Workflow '{workflow_name}' not found in registry")
        return self._workflows[workflow_name]

    def list_all(self) -> List[WorkflowMetadata]:
        """
        List all registered workflows.

        Returns:
            List of all WorkflowMetadata objects
        """
        return list(self._workflows.values())

    def list_active(self) -> List[WorkflowMetadata]:
        """
        List all active workflows.

        Returns:
            List of active WorkflowMetadata objects
        """
        return [wf for wf in self._workflows.values() if wf.is_active]

    def list_by_type(self, workflow_type: str) -> List[WorkflowMetadata]:
        """
        List all workflows of a specific type.

        Args:
            workflow_type: Type of workflows to retrieve

        Returns:
            List of WorkflowMetadata objects of the specified type
        """
        workflow_names = self._workflow_by_type.get(workflow_type, [])
        return [self._workflows[name] for name in workflow_names]

    def list_by_deployment_mode(self, mode: DeploymentMode) -> List[WorkflowMetadata]:
        """
        List all workflows with a specific deployment mode.

        Args:
            mode: DeploymentMode to filter by

        Returns:
            List of WorkflowMetadata objects with the specified deployment mode
        """
        return [
            wf for wf in self._workflows.values()
            if wf.deployment_mode == mode
        ]

    def list_types(self) -> List[str]:
        """
        List all unique workflow types.

        Returns:
            List of unique workflow type strings
        """
        return list(self._workflow_by_type.keys())

    def deregister(self, workflow_name: str) -> bool:
        """
        Deregister a workflow.

        Args:
            workflow_name: Name of the workflow to deregister

        Returns:
            True if deregistered, False if workflow not found
        """
        if workflow_name not in self._workflows:
            return False

        metadata = self._workflows.pop(workflow_name)
        workflow_type = metadata.workflow_type

        if workflow_type in self._workflow_by_type:
            self._workflow_by_type[workflow_type].remove(workflow_name)
            if not self._workflow_by_type[workflow_type]:
                del self._workflow_by_type[workflow_type]

        logger.info(f"Deregistered workflow '{workflow_name}'")
        return True

    def clear(self) -> None:
        """Clear all registered workflows."""
        self._workflows.clear()
        self._workflow_by_type.clear()
        logger.info("Registry cleared")

    def __len__(self) -> int:
        """Return the number of registered workflows."""
        return len(self._workflows)

    def __contains__(self, workflow_name: str) -> bool:
        """Check if a workflow is registered."""
        return workflow_name in self._workflows


# Global registry instance
_global_registry: Optional[WorkflowRegistry] = None


def get_registry() -> WorkflowRegistry:
    """
    Get the global workflow registry instance (singleton pattern).

    Returns:
        The global WorkflowRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = WorkflowRegistry()
    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (useful for testing)."""
    global _global_registry
    _global_registry = None
