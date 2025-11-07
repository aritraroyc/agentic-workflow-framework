"""
Prompt templates for UI Development workflow.

This module contains LangChain PromptTemplate objects for all phases of UI development:
- Planning and component identification
- Design system specification
- Code generation
- Styling strategy
- Testing strategy
- Documentation
"""

from langchain_core.prompts import PromptTemplate

# ========== UI Planning Templates ==========

PLAN_UI_PROMPT = PromptTemplate(
    input_variables=["story_requirements", "framework_preference", "typescript"],
    template="""You are an expert UI/UX architect tasked with planning a web application.

Based on the following requirements, create a comprehensive UI development plan:

Story Requirements:
{story_requirements}

Target Framework Preference: {framework_preference}
TypeScript Enabled: {typescript}

Your plan should include:
1. List of all components needed (name, description, key props, states)
2. List of all pages in the application
3. Pages and their primary components
4. Required UI frameworks/libraries
5. State management approach (Redux, Zustand, Context API, etc.)
6. Design system requirements (responsive, accessibility level)
7. Key architectural decisions

Return the response as a valid JSON object with these keys:
{{
    "project_name": "string",
    "description": "string",
    "target_framework": "React|Vue|Angular",
    "typescript_enabled": boolean,
    "components": [
        {{
            "name": "string",
            "description": "string",
            "key_props": ["string"],
            "states": ["string"],
            "events": ["string"]
        }}
    ],
    "pages": ["string"],
    "required_dependencies": ["string"],
    "design_system_needed": boolean,
    "responsive_design": boolean,
    "accessibility_level": "A|AA|AAA",
    "state_management": "string",
    "architecture_notes": "string"
}}""",
)

# ========== UI Design Templates ==========

DESIGN_UI_PROMPT = PromptTemplate(
    input_variables=["ui_plan"],
    template="""You are an expert UI/UX designer tasked with creating a design system and component specifications.

Based on the UI plan below, create detailed design specifications:

UI Plan:
{ui_plan}

Your design output should include:
1. Color palette (primary, secondary, neutrals, semantic colors)
2. Typography system (font families, sizes, weights, line heights)
3. Spacing system (consistent scale)
4. Component specifications (detailed props, variants, states)
5. Layout patterns and grid system
6. Design tokens for all design decisions

Return the response as a valid JSON object with these keys:
{{
    "design_system": {{
        "colors": {{
            "primary": "string",
            "secondary": "string",
            "neutrals": {{}},
            "semantic": {{}}
        }},
        "typography": {{
            "font_families": ["string"],
            "sizes": {{}},
            "weights": {{}},
            "line_heights": {{}}
        }},
        "spacing": ["string"],
        "border_radius": {{}},
        "shadows": {{}}
    }},
    "component_specs": {{
        "component_name": {{
            "description": "string",
            "props": {{}},
            "variants": ["string"],
            "states": ["string"]
        }}
    }},
    "layout_patterns": ["string"],
    "design_notes": "string"
}}""",
)

# ========== Code Generation Templates ==========

GENERATE_UI_CODE_PROMPT = PromptTemplate(
    input_variables=["design_specs", "ui_plan"],
    template="""You are an expert frontend developer tasked with generating production-ready React/TypeScript code.

Based on the design specifications below, generate the component code structure:

Design Specifications:
{design_specs}

UI Plan:
{ui_plan}

Your code generation should include:
1. Component files structure (src/components, src/pages, src/hooks, src/utils)
2. TypeScript types/interfaces
3. Key component implementations
4. Page component structure
5. Custom hooks for common functionality
6. Utility functions

Return the response as a valid JSON object with these keys:
{{
    "file_structure": {{
        "src": {{
            "components": ["string"],
            "pages": ["string"],
            "hooks": ["string"],
            "utils": ["string"],
            "types": "string"
        }}
    }},
    "implementation_notes": "string",
    "key_patterns": ["string"],
    "component_hierarchy": "string",
    "state_management_plan": "string"
}}""",
)

# ========== Styling Templates ==========

GENERATE_STYLING_PROMPT = PromptTemplate(
    input_variables=["design_system", "component_specs", "framework"],
    template="""You are an expert CSS/styling specialist tasked with defining the styling approach.

Based on the design tokens and specifications below, create a styling strategy:

Design System:
{design_system}

Component Specs:
{component_specs}

Framework: {framework}

Your styling plan should include:
1. Styling approach (Tailwind CSS, CSS Modules, Styled Components, etc.)
2. Theme configuration structure
3. Responsive design utilities
4. Global styles
5. Component styling patterns
6. Utility classes structure

Return the response as a valid JSON object with these keys:
{{
    "styling_approach": "Tailwind|StyledComponents|CSSModules|SCSS",
    "theme_config": {{
        "colors": {{}},
        "typography": {{}},
        "spacing": {{}},
        "breakpoints": {{}}
    }},
    "responsive_strategy": "string",
    "global_styles": "string",
    "component_styling_pattern": "string",
    "tailwind_config": {{}}
}}""",
)

# ========== Testing Templates ==========

GENERATE_TESTS_PROMPT = PromptTemplate(
    input_variables=["component_specs", "pages", "testing_framework"],
    template="""You are an expert in UI testing tasked with planning comprehensive test coverage.

Based on the component specifications and code structure below, create a testing strategy:

Components:
{component_specs}

Pages:
{pages}

Testing Framework: {testing_framework}

Your testing plan should include:
1. Unit tests for each component (props, events, states)
2. Integration tests for page compositions
3. Accessibility tests (a11y)
4. Responsive design tests
5. User interaction tests
6. Snapshot tests

Return the response as a valid JSON object with these keys:
{{
    "testing_strategy": "string",
    "test_categories": {{
        "unit": ["string"],
        "integration": ["string"],
        "accessibility": ["string"],
        "responsive": ["string"]
    }},
    "coverage_targets": {{
        "statements": number,
        "branches": number,
        "functions": number,
        "lines": number
    }},
    "testing_libraries": ["string"],
    "key_test_scenarios": ["string"]
}}""",
)

# ========== Documentation Templates ==========

GENERATE_DOCS_PROMPT = PromptTemplate(
    input_variables=["component_specs", "design_system", "pages"],
    template="""You are a technical writer tasked with creating comprehensive UI documentation.

Based on the component specifications, design system, and code structure below, create documentation:

Components:
{component_specs}

Design System:
{design_system}

Pages:
{pages}

Your documentation should include:
1. Component library documentation (props, usage examples)
2. Design system documentation
3. Setup and installation instructions
4. Development workflow guide
5. Contributing guidelines
6. Component best practices
7. Accessibility guidelines

Return the response as a valid JSON object with these keys:
{{
    "documentation_sections": {{
        "getting_started": "string",
        "design_system": "string",
        "components": "string",
        "pages": "string",
        "development": "string",
        "accessibility": "string"
    }},
    "storybook_needed": boolean,
    "example_code_sections": ["string"],
    "setup_instructions": "string"
}}""",
)
