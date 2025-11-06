"""
State definitions for the UI Enhancement child workflow.

This module defines the TypedDict schemas for enhancing existing UI components
with new features, improved UX, and better accessibility.
"""

from typing import TypedDict, Optional, Dict, List, Any


class UIEnhancementRequirement(TypedDict, total=False):
    """A single UI enhancement requirement."""
    feature_name: str
    description: str
    enhancement_type: str  # new_feature, accessibility, performance, ux_improvement, responsive
    affected_components: List[str]
    complexity: str  # low, medium, high
    estimated_effort: str
    wcag_level: str  # A, AA, AAA
    performance_target: Optional[str]


class UIEnhancementAnalysis(TypedDict, total=False):
    """Analysis of UI enhancement requirements."""
    current_ui_structure: Dict[str, Any]
    enhancement_scope: List[UIEnhancementRequirement]
    design_impact: str
    migration_strategy: str
    component_updates_needed: List[str]
    dependency_updates: List[str]
    estimated_timeline: str


class UIEnhancementDesign(TypedDict, total=False):
    """Design for UI enhancements."""
    updated_component_specs: Dict[str, Any]
    new_components: Dict[str, Any]
    accessibility_improvements: Dict[str, Any]
    performance_optimizations: Dict[str, Any]
    responsive_design_updates: Dict[str, Any]
    animation_specifications: Optional[Dict[str, Any]]
    updated_design_tokens: Dict[str, Any]


class UIEnhancementCode(TypedDict, total=False):
    """Generated code for UI enhancements."""
    modified_files: List[str]
    new_component_files: List[str]
    hook_updates: List[str]
    utility_updates: List[str]
    migration_guide: str
    breaking_changes: List[str]


class UIEnhancementTests(TypedDict, total=False):
    """Tests for UI enhancements."""
    new_test_files: List[str]
    component_test_updates: int
    accessibility_tests: List[str]
    performance_tests: List[str]
    responsive_tests: List[str]
    test_coverage_estimate: float


class UIEnhancementA11y(TypedDict, total=False):
    """Accessibility enhancements."""
    wcag_checklist: List[str]
    aria_improvements: Dict[str, Any]
    keyboard_navigation_updates: str
    screen_reader_support: str
    color_contrast_improvements: List[str]
    focus_management: str


class UIEnhancementState(TypedDict, total=False):
    """
    Internal state for the UI Enhancement workflow.

    This state flows through the internal workflow graph:
    analysis → design → code_generation → testing → accessibility → documentation

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

        # Accessibility phase
        a11y_completed: Whether accessibility improvements are done
        a11y_improvements: Accessibility improvement specifications
        a11y_errors: Any errors during accessibility work

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
    enhancement_analysis: Optional[UIEnhancementAnalysis]
    analysis_errors: List[str]

    # Design phase
    design_completed: bool
    enhancement_design: Optional[UIEnhancementDesign]
    design_errors: List[str]

    # Code generation phase
    code_generation_completed: bool
    enhancement_code: Optional[UIEnhancementCode]
    code_generation_errors: List[str]

    # Testing phase
    testing_completed: bool
    enhancement_tests: Optional[UIEnhancementTests]
    testing_errors: List[str]

    # Accessibility phase
    a11y_completed: bool
    a11y_improvements: Optional[UIEnhancementA11y]
    a11y_errors: List[str]

    # Overall tracking
    all_artifacts: List[str]
    execution_notes: str
    status: str  # in_progress, success, failure, partial


def create_initial_ui_enhancement_state(
    input_story: str,
    story_requirements: Optional[Dict[str, Any]] = None,
    parent_context: Optional[Dict[str, Any]] = None,
) -> UIEnhancementState:
    """
    Create an initial state for UI enhancement workflow execution.

    Args:
        input_story: The raw markdown input story
        story_requirements: Extracted requirements from parent workflow
        parent_context: Additional context from parent workflow

    Returns:
        An initialized UIEnhancementState with default values
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

        # Accessibility phase
        "a11y_completed": False,
        "a11y_improvements": None,
        "a11y_errors": [],

        # Overall tracking
        "all_artifacts": [],
        "execution_notes": "",
        "status": "in_progress",
    }
