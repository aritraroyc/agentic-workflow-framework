"""
Workflow registry loader for loading workflows from configuration.

This module provides functionality to load workflow definitions from YAML files
and auto-discover embedded workflows.
"""

import os
import logging
from typing import Dict, List, Any, Optional
import yaml

from workflows.registry.registry import (
    WorkflowRegistry,
    WorkflowMetadata,
    DeploymentMode,
    get_registry,
)

logger = logging.getLogger(__name__)


def load_workflows_from_yaml(config_path: str) -> List[Dict[str, Any]]:
    """
    Load workflow definitions from a YAML configuration file.

    Args:
        config_path: Path to the workflows.yaml configuration file

    Returns:
        List of workflow definitions from the YAML file

    Raises:
        FileNotFoundError: If the config file is not found
        yaml.YAMLError: If the YAML is invalid
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        config: Dict[str, Any] = yaml.safe_load(f) or {}

    workflows: List[Dict[str, Any]] = config.get("workflows", [])
    logger.info(f"Loaded {len(workflows)} workflows from {config_path}")
    return workflows


def create_workflow_metadata(workflow_def: Dict[str, Any]) -> WorkflowMetadata:
    """
    Create a WorkflowMetadata object from a workflow definition.

    Args:
        workflow_def: Dictionary containing workflow definition

    Returns:
        WorkflowMetadata object

    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Validate required fields
    required_fields = {"name", "workflow_type", "description", "version", "deployment_mode"}
    missing_fields = required_fields - set(workflow_def.keys())
    if missing_fields:
        raise ValueError(
            f"Workflow definition missing required fields: {missing_fields}"
        )

    # Parse deployment mode
    try:
        deployment_mode = DeploymentMode(workflow_def["deployment_mode"])
    except ValueError:
        raise ValueError(
            f"Invalid deployment_mode: {workflow_def['deployment_mode']}"
        )

    # Create metadata
    metadata = WorkflowMetadata(
        name=workflow_def["name"],
        workflow_type=workflow_def["workflow_type"],
        description=workflow_def["description"],
        version=workflow_def["version"],
        deployment_mode=deployment_mode,
        input_schema=workflow_def.get("input_schema", {}),
        output_schema=workflow_def.get("output_schema", {}),
        dependencies=workflow_def.get("dependencies", []),
        module_path=workflow_def.get("module_path"),
        service_url=workflow_def.get("service_url"),
        service_port=workflow_def.get("service_port"),
        tags=workflow_def.get("tags", []),
        is_active=workflow_def.get("is_active", True),
        created_at=workflow_def.get("created_at"),
        updated_at=workflow_def.get("updated_at"),
        author=workflow_def.get("author"),
        metadata=workflow_def.get("metadata", {}),
    )

    return metadata


def load_registry(
    config_path: str = "config/workflows.yaml",
    registry: Optional[WorkflowRegistry] = None,
) -> WorkflowRegistry:
    """
    Load all workflows from configuration file into the registry.

    Args:
        config_path: Path to the workflows.yaml configuration file
        registry: WorkflowRegistry instance to populate (uses global if not provided)

    Returns:
        The populated WorkflowRegistry instance

    Raises:
        FileNotFoundError: If the config file is not found
        ValueError: If workflow definitions are invalid
    """
    if registry is None:
        registry = get_registry()

    try:
        workflow_defs = load_workflows_from_yaml(config_path)
    except FileNotFoundError:
        logger.warning(f"Config file not found at {config_path}, using empty registry")
        return registry

    registered_count = 0
    failed_count = 0

    for workflow_def in workflow_defs:
        try:
            metadata = create_workflow_metadata(workflow_def)
            registry.register(metadata)
            registered_count += 1
        except (ValueError, KeyError) as e:
            logger.error(
                f"Failed to register workflow {workflow_def.get('name', 'unknown')}: {e}"
            )
            failed_count += 1

    logger.info(
        f"Registry loading complete: {registered_count} registered, {failed_count} failed"
    )
    return registry


def discover_embedded_workflows(
    base_path: str = "workflows/children",
) -> List[str]:
    """
    Auto-discover embedded workflows by scanning directories.

    This function looks for __init__.py files in subdirectories of the base path
    and treats each as a potential embedded workflow.

    Args:
        base_path: Base path to scan for embedded workflows

    Returns:
        List of discovered workflow names (directory names)
    """
    if not os.path.isdir(base_path):
        logger.warning(f"Base path not found: {base_path}")
        return []

    discovered: List[str] = []
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        # Check if it's a directory with __init__.py
        if os.path.isdir(item_path) and os.path.exists(
            os.path.join(item_path, "__init__.py")
        ):
            discovered.append(item)

    logger.info(f"Discovered {len(discovered)} embedded workflows: {discovered}")
    return discovered


def validate_registry(registry: WorkflowRegistry) -> Dict[str, Any]:
    """
    Validate the registry for consistency and completeness.

    Args:
        registry: WorkflowRegistry to validate

    Returns:
        Dictionary with validation results

    Raises:
        ValueError: If validation fails
    """
    results: Dict[str, Any] = {
        "valid": True,
        "total_workflows": len(registry),
        "embedded_workflows": len(registry.list_by_deployment_mode(DeploymentMode.EMBEDDED)),
        "a2a_workflows": len(registry.list_by_deployment_mode(DeploymentMode.A2A)),
        "workflow_types": registry.list_types(),
        "errors": [],
    }

    # Validate each workflow
    for workflow in registry.list_all():
        # Check that embedded workflows have module_path
        if workflow.deployment_mode == DeploymentMode.EMBEDDED:
            if not workflow.module_path:
                error_list: List[str] = results["errors"]  # type: ignore
                error_list.append(
                    f"Embedded workflow '{workflow.name}' missing module_path"
                )
                results["valid"] = False

        # Check that A2A workflows have service_url
        if workflow.deployment_mode == DeploymentMode.A2A:
            if not workflow.service_url:
                error_list = results["errors"]  # type: ignore
                error_list.append(
                    f"A2A workflow '{workflow.name}' missing service_url"
                )
                results["valid"] = False

    return results
