"""
Prompt templates for UI Enhancement workflow.

This module contains LangChain PromptTemplate objects for all phases of UI enhancement:
- Analysis of enhancement requirements
- Design of enhancements
- Code generation
- Test planning
- Accessibility improvements
- Documentation
"""

from langchain_core.prompts import PromptTemplate

# ========== Enhancement Analysis Templates ==========

ANALYZE_UI_ENHANCEMENT_PROMPT = PromptTemplate(
    input_variables=["story_requirements", "ui_structure"],
    template="""You are an expert UI/UX architect tasked with analyzing UI enhancement requirements.

Based on the following enhancement requirements, create a comprehensive analysis:

Story Requirements:
{story_requirements}

Current UI Structure (if available):
{ui_structure}

Your analysis should include:
1. Current UI component inventory
2. Enhancement requirements categorized by type
3. Component refactoring needs
4. Accessibility improvement opportunities
5. Performance optimization opportunities
6. Migration strategy for existing components
7. Estimated effort for each enhancement

Return the response as a valid JSON object with these keys:
{{
    "current_ui_summary": "string",
    "total_components": number,
    "enhancements": [
        {{
            "name": "string",
            "type": "new_feature|accessibility|performance|ux_improvement|responsive",
            "description": "string",
            "affected_components": ["string"],
            "complexity": "low|medium|high",
            "effort": "string",
            "wcag_target": "A|AA|AAA"
        }}
    ],
    "design_impact": "string",
    "migration_strategy": "string",
    "components_to_update": ["string"],
    "timeline_estimate": "string"
}}""",
)

# ========== Enhancement Design Templates ==========

DESIGN_UI_ENHANCEMENT_PROMPT = PromptTemplate(
    input_variables=["enhancement_analysis"],
    template="""You are an expert UI designer tasked with designing UI enhancements.

Based on the enhancement analysis below, create detailed design specifications:

Enhancement Analysis:
{enhancement_analysis}

Your design should include:
1. Updated component specifications
2. New components needed
3. Accessibility improvements (WCAG compliance)
4. Performance optimization strategies
5. Responsive design updates
6. Animation specifications (if applicable)
7. Updated design tokens
8. Visual hierarchy improvements

Return the response as a valid JSON object with these keys:
{{
    "updated_components": {{}},
    "new_components": {{}},
    "accessibility_improvements": {{}},
    "performance_optimizations": {{}},
    "responsive_updates": {{}},
    "animations": {{}},
    "design_tokens": {{}},
    "design_notes": "string"
}}""",
)

# ========== Enhancement Code Generation Templates ==========

GENERATE_UI_ENHANCEMENT_CODE_PROMPT = PromptTemplate(
    input_variables=["enhancement_design", "enhancement_analysis"],
    template="""You are an expert frontend developer tasked with generating code for UI enhancements.

Based on the enhancement design below, generate implementation plan:

Enhancement Design:
{enhancement_design}

Enhancement Analysis:
{enhancement_analysis}

Your code generation should include:
1. Modified component files and changes
2. New component files
3. Hook updates needed
4. Utility function updates
5. Migration guide for existing code
6. Breaking changes documentation
7. Rollback strategy

Return the response as a valid JSON object with these keys:
{{
    "modified_files": ["string"],
    "new_files": ["string"],
    "hook_updates": ["string"],
    "utility_updates": ["string"],
    "implementation_strategy": "string",
    "migration_guide": "string",
    "breaking_changes": ["string"],
    "rollback_plan": "string"
}}""",
)

# ========== Enhancement Testing Templates ==========

GENERATE_UI_ENHANCEMENT_TESTS_PROMPT = PromptTemplate(
    input_variables=["enhancement_design", "enhancement_analysis"],
    template="""You are an expert QA engineer tasked with planning tests for UI enhancements.

Based on the enhancement design and code strategy below, create a testing plan:

Enhancement Design:
{enhancement_design}

Enhancement Analysis:
{enhancement_analysis}

Your testing plan should include:
1. New component test files
2. Component test updates
3. Accessibility testing (WCAG)
4. Performance/Core Web Vitals testing
5. Responsive design testing
6. Integration tests
7. Visual regression tests

Return the response as a valid JSON object with these keys:
{{
    "test_strategy": "string",
    "test_categories": {{
        "unit": ["string"],
        "integration": ["string"],
        "accessibility": ["string"],
        "performance": ["string"],
        "responsive": ["string"],
        "visual": ["string"]
    }},
    "coverage_targets": {{}},
    "test_data": "string",
    "performance_baselines": {{
        "largest_contentful_paint": "string",
        "cumulative_layout_shift": "string",
        "first_input_delay": "string"
    }}
}}""",
)

# ========== Accessibility Improvement Templates ==========

IMPROVE_ACCESSIBILITY_PROMPT = PromptTemplate(
    input_variables=["enhancement_design", "enhancement_analysis"],
    template="""You are an expert in web accessibility (WCAG 2.1) tasked with improving UI accessibility.

Based on the enhancement design and current UI below, create accessibility improvements:

Enhancement Design:
{enhancement_design}

Enhancement Analysis:
{enhancement_analysis}

Your accessibility improvements should include:
1. WCAG 2.1 compliance checklist
2. ARIA attribute improvements
3. Keyboard navigation enhancements
4. Screen reader support improvements
5. Color contrast improvements
6. Focus management improvements
7. Semantic HTML recommendations

Return the response as a valid JSON object with these keys:
{{
    "wcag_level_target": "A|AA|AAA",
    "wcag_checklist": ["string"],
    "aria_improvements": {{}},
    "keyboard_support": "string",
    "screen_reader_support": "string",
    "color_contrast": ["string"],
    "focus_management": "string",
    "semantic_html": ["string"],
    "testing_tools": ["string"]
}}""",
)

# ========== Enhancement Documentation Templates ==========

GENERATE_UI_ENHANCEMENT_DOCS_PROMPT = PromptTemplate(
    input_variables=["enhancement_design", "enhancement_analysis"],
    template="""You are a technical writer tasked with documenting UI enhancements.

Based on the enhanced UI design and implementation below, create documentation:

Enhancement Design:
{enhancement_design}

Enhancement Analysis:
{enhancement_analysis}

Your documentation should include:
1. Component upgrade guide
2. Migration instructions
3. Accessibility features documentation
4. Performance improvements documentation
5. New component usage examples
6. Breaking changes guide
7. Troubleshooting guide
8. Visual change summary

Return the response as a valid JSON object with these keys:
{{
    "documentation_sections": {{
        "overview": "string",
        "upgrade_guide": "string",
        "migration_instructions": "string",
        "accessibility_features": "string",
        "performance_improvements": "string",
        "examples": ["string"],
        "breaking_changes": ["string"],
        "troubleshooting": "string"
    }},
    "changelog": "string",
    "version_number": "string",
    "release_date": "string"
}}""",
)
