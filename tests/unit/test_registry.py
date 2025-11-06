"""
Unit tests for the workflow registry system.

Tests cover:
- WorkflowMetadata creation and validation
- WorkflowRegistry registration, retrieval, and listing
- Workflow loader and YAML parsing
- Auto-discovery of embedded workflows
- Registry validation
"""

import pytest
import os
import tempfile
from pathlib import Path

from workflows.registry.registry import (
    WorkflowRegistry,
    WorkflowMetadata,
    DeploymentMode,
    get_registry,
    reset_registry,
)
from workflows.registry.loader import (
    load_workflows_from_yaml,
    create_workflow_metadata,
    load_registry,
    discover_embedded_workflows,
    validate_registry,
)


class TestWorkflowMetadata:
    """Tests for WorkflowMetadata dataclass."""

    def test_create_embedded_workflow_metadata(self) -> None:
        """Test creating metadata for an embedded workflow."""
        metadata = WorkflowMetadata(
            name="api_development",
            workflow_type="api_development",
            description="Develops RESTful APIs",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.children.api_development",
            tags=["api", "development"],
        )

        assert metadata.name == "api_development"
        assert metadata.workflow_type == "api_development"
        assert metadata.deployment_mode == DeploymentMode.EMBEDDED
        assert metadata.module_path == "workflows.children.api_development"
        assert "api" in metadata.tags

    def test_create_a2a_workflow_metadata(self) -> None:
        """Test creating metadata for an A2A workflow."""
        metadata = WorkflowMetadata(
            name="ui_development_service",
            workflow_type="ui_development",
            description="Develops UI components",
            version="1.0.0",
            deployment_mode=DeploymentMode.A2A,
            service_url="http://localhost",
            service_port=8001,
        )

        assert metadata.name == "ui_development_service"
        assert metadata.deployment_mode == DeploymentMode.A2A
        assert metadata.service_url == "http://localhost"
        assert metadata.service_port == 8001

    def test_embedded_workflow_requires_module_path(self) -> None:
        """Test that embedded workflows require module_path."""
        with pytest.raises(ValueError, match="requires 'module_path'"):
            WorkflowMetadata(
                name="test_workflow",
                workflow_type="test",
                description="Test",
                version="1.0.0",
                deployment_mode=DeploymentMode.EMBEDDED,
                # Missing module_path
            )

    def test_a2a_workflow_requires_service_url(self) -> None:
        """Test that A2A workflows require service_url."""
        with pytest.raises(ValueError, match="requires 'service_url'"):
            WorkflowMetadata(
                name="test_workflow",
                workflow_type="test",
                description="Test",
                version="1.0.0",
                deployment_mode=DeploymentMode.A2A,
                # Missing service_url
            )

    def test_metadata_to_dict(self) -> None:
        """Test converting metadata to dictionary."""
        metadata = WorkflowMetadata(
            name="test_workflow",
            workflow_type="test",
            description="Test workflow",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.test",
            author="Test Author",
        )

        data = metadata.to_dict()
        assert data["name"] == "test_workflow"
        assert data["deployment_mode"] == "embedded"
        assert data["author"] == "Test Author"


class TestWorkflowRegistry:
    """Tests for WorkflowRegistry class."""

    @pytest.fixture
    def registry(self) -> WorkflowRegistry:
        """Create a fresh registry for each test."""
        return WorkflowRegistry()

    @pytest.fixture
    def sample_metadata(self) -> WorkflowMetadata:
        """Create sample workflow metadata."""
        return WorkflowMetadata(
            name="test_workflow",
            workflow_type="test",
            description="Test workflow",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.test",
        )

    def test_register_workflow(self, registry: WorkflowRegistry, sample_metadata: WorkflowMetadata) -> None:
        """Test registering a workflow."""
        registry.register(sample_metadata)
        assert len(registry) == 1
        assert registry.get("test_workflow") == sample_metadata

    def test_register_duplicate_workflow_raises_error(
        self, registry: WorkflowRegistry, sample_metadata: WorkflowMetadata
    ) -> None:
        """Test that registering a duplicate workflow raises an error."""
        registry.register(sample_metadata)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(sample_metadata)

    def test_get_workflow(self, registry: WorkflowRegistry, sample_metadata: WorkflowMetadata) -> None:
        """Test getting a workflow by name."""
        registry.register(sample_metadata)
        retrieved = registry.get("test_workflow")
        assert retrieved is not None
        assert retrieved.name == "test_workflow"

    def test_get_nonexistent_workflow_returns_none(self, registry: WorkflowRegistry) -> None:
        """Test that getting a nonexistent workflow returns None."""
        assert registry.get("nonexistent") is None

    def test_get_or_raise(self, registry: WorkflowRegistry, sample_metadata: WorkflowMetadata) -> None:
        """Test get_or_raise method."""
        registry.register(sample_metadata)
        retrieved = registry.get_or_raise("test_workflow")
        assert retrieved.name == "test_workflow"

    def test_get_or_raise_nonexistent_raises_error(self, registry: WorkflowRegistry) -> None:
        """Test that get_or_raise raises KeyError for nonexistent workflow."""
        with pytest.raises(KeyError, match="not found"):
            registry.get_or_raise("nonexistent")

    def test_list_all_workflows(self, registry: WorkflowRegistry) -> None:
        """Test listing all workflows."""
        metadata1 = WorkflowMetadata(
            name="workflow1",
            workflow_type="type1",
            description="Workflow 1",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.workflow1",
        )
        metadata2 = WorkflowMetadata(
            name="workflow2",
            workflow_type="type2",
            description="Workflow 2",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.workflow2",
        )

        registry.register(metadata1)
        registry.register(metadata2)

        all_workflows = registry.list_all()
        assert len(all_workflows) == 2
        assert any(w.name == "workflow1" for w in all_workflows)
        assert any(w.name == "workflow2" for w in all_workflows)

    def test_list_active_workflows(self, registry: WorkflowRegistry) -> None:
        """Test listing only active workflows."""
        metadata1 = WorkflowMetadata(
            name="workflow1",
            workflow_type="test",
            description="Active",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.workflow1",
            is_active=True,
        )
        metadata2 = WorkflowMetadata(
            name="workflow2",
            workflow_type="test",
            description="Inactive",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.workflow2",
            is_active=False,
        )

        registry.register(metadata1)
        registry.register(metadata2)

        active = registry.list_active()
        assert len(active) == 1
        assert active[0].name == "workflow1"

    def test_list_by_type(self, registry: WorkflowRegistry) -> None:
        """Test listing workflows by type."""
        metadata1 = WorkflowMetadata(
            name="api1",
            workflow_type="api_development",
            description="API 1",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.api1",
        )
        metadata2 = WorkflowMetadata(
            name="ui1",
            workflow_type="ui_development",
            description="UI 1",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.ui1",
        )

        registry.register(metadata1)
        registry.register(metadata2)

        api_workflows = registry.list_by_type("api_development")
        assert len(api_workflows) == 1
        assert api_workflows[0].name == "api1"

    def test_list_by_deployment_mode(self, registry: WorkflowRegistry) -> None:
        """Test listing workflows by deployment mode."""
        embedded = WorkflowMetadata(
            name="embedded_wf",
            workflow_type="test",
            description="Embedded",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.embedded",
        )
        a2a = WorkflowMetadata(
            name="a2a_wf",
            workflow_type="test",
            description="A2A",
            version="1.0.0",
            deployment_mode=DeploymentMode.A2A,
            service_url="http://localhost:8000",
        )

        registry.register(embedded)
        registry.register(a2a)

        embedded_wfs = registry.list_by_deployment_mode(DeploymentMode.EMBEDDED)
        assert len(embedded_wfs) == 1
        assert embedded_wfs[0].name == "embedded_wf"

    def test_list_types(self, registry: WorkflowRegistry) -> None:
        """Test listing unique workflow types."""
        metadata1 = WorkflowMetadata(
            name="workflow1",
            workflow_type="api_development",
            description="API",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.workflow1",
        )
        metadata2 = WorkflowMetadata(
            name="workflow2",
            workflow_type="ui_development",
            description="UI",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.workflow2",
        )

        registry.register(metadata1)
        registry.register(metadata2)

        types = registry.list_types()
        assert "api_development" in types
        assert "ui_development" in types
        assert len(types) == 2

    def test_deregister_workflow(self, registry: WorkflowRegistry, sample_metadata: WorkflowMetadata) -> None:
        """Test deregistering a workflow."""
        registry.register(sample_metadata)
        assert len(registry) == 1

        result = registry.deregister("test_workflow")
        assert result is True
        assert len(registry) == 0
        assert registry.get("test_workflow") is None

    def test_deregister_nonexistent_workflow(self, registry: WorkflowRegistry) -> None:
        """Test deregistering a nonexistent workflow."""
        result = registry.deregister("nonexistent")
        assert result is False

    def test_clear_registry(self, registry: WorkflowRegistry, sample_metadata: WorkflowMetadata) -> None:
        """Test clearing the registry."""
        registry.register(sample_metadata)
        assert len(registry) == 1

        registry.clear()
        assert len(registry) == 0

    def test_contains(self, registry: WorkflowRegistry, sample_metadata: WorkflowMetadata) -> None:
        """Test the 'in' operator."""
        registry.register(sample_metadata)
        assert "test_workflow" in registry
        assert "nonexistent" not in registry


class TestWorkflowLoader:
    """Tests for workflow loader functions."""

    def test_load_workflows_from_yaml(self) -> None:
        """Test loading workflows from YAML file."""
        yaml_content = """
workflows:
  - name: test_workflow
    workflow_type: test
    description: Test workflow
    version: 1.0.0
    deployment_mode: embedded
    module_path: workflows.test
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            try:
                workflows = load_workflows_from_yaml(f.name)
                assert len(workflows) == 1
                assert workflows[0]["name"] == "test_workflow"
            finally:
                os.unlink(f.name)

    def test_load_workflows_file_not_found(self) -> None:
        """Test that loading from nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_workflows_from_yaml("nonexistent_file.yaml")

    def test_create_workflow_metadata_from_dict(self) -> None:
        """Test creating metadata from dictionary."""
        workflow_def = {
            "name": "test_workflow",
            "workflow_type": "test",
            "description": "Test",
            "version": "1.0.0",
            "deployment_mode": "embedded",
            "module_path": "workflows.test",
        }

        metadata = create_workflow_metadata(workflow_def)
        assert metadata.name == "test_workflow"
        assert metadata.module_path == "workflows.test"

    def test_create_metadata_missing_required_fields(self) -> None:
        """Test that missing required fields raise ValueError."""
        workflow_def = {
            "name": "test_workflow",
            # Missing required fields
        }

        with pytest.raises(ValueError, match="missing required fields"):
            create_workflow_metadata(workflow_def)

    def test_create_metadata_invalid_deployment_mode(self) -> None:
        """Test that invalid deployment mode raises ValueError."""
        workflow_def = {
            "name": "test_workflow",
            "workflow_type": "test",
            "description": "Test",
            "version": "1.0.0",
            "deployment_mode": "invalid_mode",
        }

        with pytest.raises(ValueError, match="Invalid deployment_mode"):
            create_workflow_metadata(workflow_def)

    def test_load_registry(self) -> None:
        """Test loading registry from YAML file."""
        yaml_content = """
workflows:
  - name: workflow1
    workflow_type: api_development
    description: API Workflow
    version: 1.0.0
    deployment_mode: embedded
    module_path: workflows.api_development
  - name: workflow2
    workflow_type: ui_development
    description: UI Workflow
    version: 1.0.0
    deployment_mode: a2a
    service_url: http://localhost:8001
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            try:
                registry = WorkflowRegistry()
                load_registry(f.name, registry)
                assert len(registry) == 2
                assert registry.get("workflow1") is not None
                assert registry.get("workflow2") is not None
            finally:
                os.unlink(f.name)

    def test_discover_embedded_workflows(self) -> None:
        """Test discovering embedded workflows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some mock workflow directories
            os.makedirs(os.path.join(tmpdir, "workflow1"))
            os.makedirs(os.path.join(tmpdir, "workflow2"))
            Path(os.path.join(tmpdir, "workflow1", "__init__.py")).touch()
            Path(os.path.join(tmpdir, "workflow2", "__init__.py")).touch()

            discovered = discover_embedded_workflows(tmpdir)
            assert "workflow1" in discovered
            assert "workflow2" in discovered

    def test_discover_embedded_workflows_nonexistent_path(self) -> None:
        """Test discovering from nonexistent path."""
        discovered = discover_embedded_workflows("/nonexistent/path")
        assert discovered == []

    def test_validate_registry(self) -> None:
        """Test registry validation."""
        registry = WorkflowRegistry()

        metadata1 = WorkflowMetadata(
            name="workflow1",
            workflow_type="test",
            description="Test",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.workflow1",
        )
        metadata2 = WorkflowMetadata(
            name="workflow2",
            workflow_type="test",
            description="Test",
            version="1.0.0",
            deployment_mode=DeploymentMode.A2A,
            service_url="http://localhost",
        )

        registry.register(metadata1)
        registry.register(metadata2)

        results = validate_registry(registry)
        assert results["valid"] is True
        assert results["total_workflows"] == 2
        assert results["embedded_workflows"] == 1
        assert results["a2a_workflows"] == 1


class TestGlobalRegistry:
    """Tests for global registry instance."""

    def test_get_registry_singleton(self) -> None:
        """Test that get_registry returns a singleton."""
        reset_registry()
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2

    def test_reset_registry(self) -> None:
        """Test resetting the global registry."""
        registry = get_registry()
        metadata = WorkflowMetadata(
            name="test",
            workflow_type="test",
            description="Test",
            version="1.0.0",
            deployment_mode=DeploymentMode.EMBEDDED,
            module_path="workflows.test",
        )
        registry.register(metadata)
        assert len(registry) == 1

        reset_registry()
        new_registry = get_registry()
        assert len(new_registry) == 0
