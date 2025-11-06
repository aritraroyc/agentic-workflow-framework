"""
State definitions for the UI Development child workflow.

This module defines the TypedDict schemas for the internal state used by the UI
development workflow as it progresses through planning, design, code generation,
styling, testing, and documentation phases.
"""

from typing import TypedDict, Optional, Dict, List, Any


class UIComponent(TypedDict, total=False):
    """A single UI component specification."""
    name: str
    description: str
    props: Dict[str, Any]  # Component props/properties
    states: List[str]  # Component states (active, hover, disabled, etc.)
    events: List[str]  # Component events (onClick, onChange, etc.)
    accessibility_requirements: List[str]
    responsive_breakpoints: List[str]  # sm, md, lg, xl, 2xl
    tags: List[str]


class UIPlanOutput(TypedDict, total=False):
    """Output from UI planning phase."""
    project_name: str
    description: str
    target_framework: str  # React, Vue, Angular
    typescript_enabled: bool
    component_list: List[UIComponent]
    pages: List[str]
    required_dependencies: List[str]
    design_system_needed: bool
    responsive_design: bool
    accessibility_requirements: str  # WCAG 2.1 level
    authentication_required: bool
    state_management: str  # Redux, Zustand, Context API, Pinia, etc.
    architecture_notes: str
    design_decisions: str


class UIDesignOutput(TypedDict, total=False):
    """Output from UI design phase."""
    design_system_spec: Dict[str, Any]  # Colors, typography, spacing, etc.
    component_specifications: Dict[str, Any]  # Detailed component specs
    layout_patterns: List[str]  # Layout systems and patterns
    design_tokens: Dict[str, Any]  # Design tokens in JSON
    wireframes_description: str
    design_notes: str


class UICodeOutput(TypedDict, total=False):
    """Output from code generation phase."""
    main_app_file: str
    component_files: List[str]
    page_files: List[str]
    hooks_files: List[str]
    utils_files: List[str]
    types_file: str  # TypeScript types
    generated_files: List[str]
    file_structure_description: str


class UIStylingOutput(TypedDict, total=False):
    """Output from styling phase."""
    styling_approach: str  # Tailwind, Styled-components, CSS Modules, etc.
    main_css_file: str
    theme_config: Dict[str, Any]
    responsive_utilities: str
    generated_style_files: List[str]


class UITestOutput(TypedDict, total=False):
    """Output from testing phase."""
    test_files: List[str]
    test_cases_generated: int
    coverage_estimate: float  # Percentage
    testing_framework: str  # Jest, Vitest, etc.
    generated_tests: List[str]


class UIDocsOutput(TypedDict, total=False):
    """Output from documentation phase."""
    component_docs_file: str
    storybook_config: Optional[str]
    setup_instructions: str
    component_guide: str
    generated_docs: List[str]


class UIDevState(TypedDict, total=False):
    """
    Internal state for the UI Development workflow.

    This state flows through the internal workflow graph:
    planning → design → code_generation → styling → testing → documentation

    Attributes:
        # Input from parent workflow
        input_story: Raw input story from parent
        story_requirements: Extracted requirements from parent preprocessor
        parent_context: Additional context from parent

        # Planning phase
        planning_completed: Whether planning is done
        ui_plan: Detailed UI plan
        planning_errors: Any errors during planning

        # Design phase
        design_completed: Whether design is done
        ui_design: Design specifications
        design_errors: Any errors during design

        # Code generation phase
        code_generation_completed: Whether code generation is done
        code_output: Generated code files
        code_generation_errors: Any errors during code generation

        # Styling phase
        styling_completed: Whether styling is done
        styling_output: Generated styling files
        styling_errors: Any errors during styling

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
    ui_plan: Optional[UIPlanOutput]
    planning_errors: List[str]

    # Design phase
    design_completed: bool
    ui_design: Optional[UIDesignOutput]
    design_errors: List[str]

    # Code generation phase
    code_generation_completed: bool
    code_output: Optional[UICodeOutput]
    code_generation_errors: List[str]

    # Styling phase
    styling_completed: bool
    styling_output: Optional[UIStylingOutput]
    styling_errors: List[str]

    # Testing phase
    testing_completed: bool
    test_output: Optional[UITestOutput]
    testing_errors: List[str]

    # Documentation phase
    documentation_completed: bool
    docs_output: Optional[UIDocsOutput]
    documentation_errors: List[str]

    # Overall tracking
    all_artifacts: List[str]
    execution_notes: str
    status: str  # in_progress, success, failure, partial


def create_initial_ui_state(
    input_story: str,
    story_requirements: Optional[Dict[str, Any]] = None,
    parent_context: Optional[Dict[str, Any]] = None,
) -> UIDevState:
    """
    Create an initial state for UI development workflow execution.

    Args:
        input_story: The raw markdown input story
        story_requirements: Extracted requirements from parent workflow
        parent_context: Additional context from parent workflow

    Returns:
        An initialized UIDevState with default values
    """
    return {
        # Input from parent workflow
        "input_story": input_story,
        "story_requirements": story_requirements or {},
        "parent_context": parent_context or {},

        # Planning phase
        "planning_completed": False,
        "ui_plan": None,
        "planning_errors": [],

        # Design phase
        "design_completed": False,
        "ui_design": None,
        "design_errors": [],

        # Code generation phase
        "code_generation_completed": False,
        "code_output": None,
        "code_generation_errors": [],

        # Styling phase
        "styling_completed": False,
        "styling_output": None,
        "styling_errors": [],

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
