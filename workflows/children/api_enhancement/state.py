"""
State definitions for the API Enhancement child workflow.

This module defines the TypedDict schemas for enhancing existing APIs with
new features, performance improvements, and observability.
"""

from typing import TypedDict, Optional, Dict, List, Any


class EnhancementRequirement(TypedDict, total=False):
    """A single enhancement requirement for the API."""
    feature_name: str
    description: str
    enhancement_type: str  # new_endpoint, batch_processing, webhooks, filtering, optimization, monitoring
    affected_endpoints: List[str]
    complexity: str  # low, medium, high
    estimated_effort: str
    dependencies: List[str]
    breaking_change: bool


class EnhancementAnalysis(TypedDict, total=False):
    """Analysis of enhancement requirements."""
    current_api_structure: Dict[str, Any]
    current_language: str  # "Python|Java"
    current_framework: str  # "FastAPI|Flask|Django|Spring Boot"
    enhancement_scope: List[EnhancementRequirement]
    architectural_impact: str
    migration_strategy: Optional[str]
    backward_compatibility_approach: str
    versioning_strategy: str  # semantic, URL-based, header-based
    estimated_timeline: str
    # Java/Spring Boot specific fields (optional)
    java_version: str  # "17" or "21" (only for Spring Boot)
    build_tool: str  # "Maven" or "Gradle" (only for Spring Boot)
    spring_boot_starters: List[str]  # Spring Boot starter dependencies
    spring_security_config: str  # Spring Security configuration approach


class EnhancementDesign(TypedDict, total=False):
    """Design for API enhancements."""
    enhanced_endpoints: Dict[str, Any]
    new_endpoints: Dict[str, Any]
    batch_processing_design: Optional[Dict[str, Any]]
    webhook_design: Optional[Dict[str, Any]]
    filtering_strategy: Optional[Dict[str, Any]]
    caching_strategy: Optional[Dict[str, Any]]
    error_handling_updates: str
    rate_limiting_updates: Optional[Dict[str, Any]]


class EnhancementCode(TypedDict, total=False):
    """Generated code for enhancements."""
    modified_files: List[str]
    new_files: List[str]
    migration_scripts: List[str]
    configuration_updates: str
    deployment_plan: str


class EnhancementTests(TypedDict, total=False):
    """Tests for enhancements."""
    new_test_cases: int
    integration_tests: List[str]
    migration_tests: List[str]
    performance_tests: List[str]
    backward_compatibility_tests: List[str]
    test_coverage_estimate: float


class EnhancementMonitoring(TypedDict, total=False):
    """Monitoring and observability enhancements."""
    metrics_to_track: List[str]
    logging_enhancements: str
    distributed_tracing_setup: str
    alerting_rules: List[str]
    monitoring_dashboard_spec: str


class ApiEnhancementState(TypedDict, total=False):
    """
    Internal state for the API Enhancement workflow.

    This state flows through the internal workflow graph:
    analysis → design → code_generation → testing → monitoring → documentation

    Attributes:
        # Input from parent workflow
        input_story: Raw input story from parent
        story_requirements: Extracted requirements from parent preprocessor
        parent_context: Additional context from parent

        # Analysis phase
        analysis_completed: Whether analysis is done
        enhancement_analysis: Analysis of enhancement requirements
        analysis_errors: Any errors during analysis

        # Design phase
        design_completed: Whether design is done
        enhancement_design: Design specifications for enhancements
        design_errors: Any errors during design

        # Code generation phase
        code_generation_completed: Whether code generation is done
        enhancement_code: Generated code for enhancements
        code_generation_errors: Any errors during code generation

        # Testing phase
        testing_completed: Whether testing is done
        enhancement_tests: Test specifications
        testing_errors: Any errors during testing

        # Monitoring phase
        monitoring_completed: Whether monitoring setup is done
        monitoring_setup: Monitoring and observability setup
        monitoring_errors: Any errors during monitoring setup

        # Overall tracking
        all_artifacts: List of all generated artifact paths
        execution_notes: Notes from execution
        status: Overall status (in_progress, success, failure, partial)
    """
    # Input from parent workflow
    input_story: str
    story_requirements: Dict[str, Any]
    parent_context: Dict[str, Any]

    # Analysis phase
    analysis_completed: bool
    enhancement_analysis: Optional[EnhancementAnalysis]
    analysis_errors: List[str]

    # Design phase
    design_completed: bool
    enhancement_design: Optional[EnhancementDesign]
    design_errors: List[str]

    # Code generation phase
    code_generation_completed: bool
    enhancement_code: Optional[EnhancementCode]
    code_generation_errors: List[str]

    # Testing phase
    testing_completed: bool
    enhancement_tests: Optional[EnhancementTests]
    testing_errors: List[str]

    # Monitoring phase
    monitoring_completed: bool
    monitoring_setup: Optional[EnhancementMonitoring]
    monitoring_errors: List[str]

    # Overall tracking
    all_artifacts: List[str]
    execution_notes: str
    status: str  # in_progress, success, failure, partial


def create_initial_enhancement_state(
    input_story: str,
    story_requirements: Optional[Dict[str, Any]] = None,
    parent_context: Optional[Dict[str, Any]] = None,
) -> ApiEnhancementState:
    """
    Create an initial state for API enhancement workflow execution.

    Args:
        input_story: The raw markdown input story
        story_requirements: Extracted requirements from parent workflow
        parent_context: Additional context from parent workflow

    Returns:
        An initialized ApiEnhancementState with default values
    """
    return {
        # Input from parent workflow
        "input_story": input_story,
        "story_requirements": story_requirements or {},
        "parent_context": parent_context or {},

        # Analysis phase
        "analysis_completed": False,
        "enhancement_analysis": None,
        "analysis_errors": [],

        # Design phase
        "design_completed": False,
        "enhancement_design": None,
        "design_errors": [],

        # Code generation phase
        "code_generation_completed": False,
        "enhancement_code": None,
        "code_generation_errors": [],

        # Testing phase
        "testing_completed": False,
        "enhancement_tests": None,
        "testing_errors": [],

        # Monitoring phase
        "monitoring_completed": False,
        "monitoring_setup": None,
        "monitoring_errors": [],

        # Overall tracking
        "all_artifacts": [],
        "execution_notes": "",
        "status": "in_progress",
    }
