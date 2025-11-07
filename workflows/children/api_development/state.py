"""
State definitions for the API Development child workflow.

This module defines the TypedDict schemas for the internal state used by the API
development workflow as it progresses through planning, design, code generation,
testing, and documentation phases.
"""

from typing import TypedDict, Optional, Dict, List, Any


class ApiRequirement(TypedDict, total=False):
    """A single API requirement extracted from the story."""
    endpoint: str
    method: str  # GET, POST, PUT, DELETE, PATCH
    description: str
    request_schema: Dict[str, Any]
    response_schema: Dict[str, Any]
    status_codes: List[int]
    authentication_required: bool
    tags: List[str]


class ApiPlanOutput(TypedDict, total=False):
    """Output from API planning phase."""
    api_name: str
    api_description: str
    base_path: str
    requirements: List[ApiRequirement]
    framework: str  # FastAPI, Flask, Django, Spring Boot
    authentication_method: str  # JWT, OAuth2, API Key, Spring Security, None
    database_type: Optional[str]  # PostgreSQL, MongoDB, SQLite
    has_database: bool
    required_dependencies: List[str]
    architecture_notes: str
    design_decisions: str
    # Java/Spring Boot specific fields (optional)
    java_version: str  # "17" or "21" (only for Spring Boot)
    build_tool: str  # "Maven" or "Gradle" (only for Spring Boot)
    spring_boot_starters: List[str]  # Spring Boot starter dependencies
    spring_security_config: str  # Spring Security configuration approach


class ApiDesignOutput(TypedDict, total=False):
    """Output from API design phase."""
    openapi_spec: Dict[str, Any]  # OpenAPI 3.0 specification
    design_notes: str
    validation_rules: Dict[str, Any]
    error_handling_strategy: str


class ApiCodeOutput(TypedDict, total=False):
    """Output from code generation phase."""
    main_file: str  # Path to main application file
    models_file: str  # Path to data models file
    routes_file: str  # Path to route definitions
    schemas_file: str  # Path to Pydantic schemas
    config_file: str  # Path to configuration file
    requirements_file: str  # Path to requirements.txt
    generated_files: List[str]  # All generated files


class ApiTestOutput(TypedDict, total=False):
    """Output from testing phase."""
    test_file: str  # Path to test file
    test_cases_generated: int
    test_coverage_estimate: float  # Percentage
    generated_tests: List[str]


class ApiDocsOutput(TypedDict, total=False):
    """Output from documentation phase."""
    readme_file: str  # Path to README
    api_docs_file: str  # Path to API documentation
    setup_instructions: str
    generated_docs: List[str]


class ApiDevelopmentState(TypedDict, total=False):
    """
    Internal state for the API Development workflow.

    This state flows through the internal workflow graph:
    planning → design → code_generation → testing → documentation

    Attributes:
        # Input from parent workflow
        input_story: Raw input story from parent
        story_requirements: Extracted requirements from parent preprocessor
        parent_context: Additional context from parent

        # Planning phase
        planning_completed: Whether planning is done
        api_plan: Detailed API plan
        planning_errors: Any errors during planning

        # Design phase
        design_completed: Whether design is done
        api_design: Design including OpenAPI spec
        design_errors: Any errors during design

        # Code generation phase
        code_generation_completed: Whether code generation is done
        code_output: Generated code files
        code_generation_errors: Any errors during code generation

        # Testing phase
        testing_completed: Whether testing is done
        test_output: Generated test files
        testing_errors: Any errors during testing

        # Documentation phase
        documentation_completed: Whether documentation is done
        docs_output: Generated documentation files
        documentation_errors: Any errors during documentation

        # Overall tracking
        all_artifacts: List of all generated artifact paths
        execution_notes: Notes from execution
        status: Overall status (in_progress, success, failure, partial)
    """
    # Input from parent workflow
    input_story: str
    story_requirements: Dict[str, Any]
    parent_context: Dict[str, Any]

    # Planning phase
    planning_completed: bool
    api_plan: Optional[ApiPlanOutput]
    planning_errors: List[str]

    # Design phase
    design_completed: bool
    api_design: Optional[ApiDesignOutput]
    design_errors: List[str]

    # Code generation phase
    code_generation_completed: bool
    code_output: Optional[ApiCodeOutput]
    code_generation_errors: List[str]

    # Testing phase
    testing_completed: bool
    test_output: Optional[ApiTestOutput]
    testing_errors: List[str]

    # Documentation phase
    documentation_completed: bool
    docs_output: Optional[ApiDocsOutput]
    documentation_errors: List[str]

    # Overall tracking
    all_artifacts: List[str]
    execution_notes: str
    status: str  # in_progress, success, failure, partial


def create_initial_api_state(
    input_story: str,
    story_requirements: Optional[Dict[str, Any]] = None,
    parent_context: Optional[Dict[str, Any]] = None,
) -> ApiDevelopmentState:
    """
    Create an initial state for API development workflow execution.

    Args:
        input_story: The raw markdown input story
        story_requirements: Extracted requirements from parent workflow
        parent_context: Additional context from parent workflow

    Returns:
        An initialized ApiDevelopmentState with default values
    """
    return {
        # Input from parent workflow
        "input_story": input_story,
        "story_requirements": story_requirements or {},
        "parent_context": parent_context or {},

        # Planning phase
        "planning_completed": False,
        "api_plan": None,
        "planning_errors": [],

        # Design phase
        "design_completed": False,
        "api_design": None,
        "design_errors": [],

        # Code generation phase
        "code_generation_completed": False,
        "code_output": None,
        "code_generation_errors": [],

        # Testing phase
        "testing_completed": False,
        "test_output": None,
        "testing_errors": [],

        # Documentation phase
        "documentation_completed": False,
        "docs_output": None,
        "documentation_errors": [],

        # Overall tracking
        "all_artifacts": [],
        "execution_notes": "",
        "status": "in_progress",
    }
