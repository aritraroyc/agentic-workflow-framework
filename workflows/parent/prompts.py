"""
Prompt templates for parent workflow agents.

This module contains LangChain PromptTemplate objects for:
- PreprocessorAgent: Data extraction and parsing
- PlannerAgent: Scope analysis, workflow identification, responsibility definition, risk assessment
"""

from langchain_core.prompts import PromptTemplate

# ========== Preprocessor Agent Templates ==========

PREPROCESSOR_EXTRACTION_TEMPLATE = PromptTemplate(
    input_variables=["full_content"],
    template="""Analyze the following workflow story and extract structured information.

Story:
{full_content}

Please extract and return a JSON object with:
1. title: Main title or subject
2. description: Brief description
3. requirements: List of technical/functional requirements
4. success_criteria: List of success criteria
5. constraints: Any constraints or limitations
6. estimated_effort_hours: Estimate in hours
7. dependencies: List of dependencies

Return ONLY valid JSON, no markdown formatting.""",
)

# ========== Planner Agent Templates ==========

PLANNER_SCOPE_ANALYSIS_TEMPLATE = PromptTemplate(
    input_variables=["story_type", "title", "requirements_json", "constraints_json"],
    template="""Analyze the scope of this {story_type} story:

Title: {title}

Requirements:
{requirements_json}

Constraints:
{constraints_json}

Provide a concise analysis of:
1. Overall scope and scale
2. Technical complexity
3. Key focus areas
4. Dependencies or integrations needed

Keep response concise (2-3 sentences).""",
)

PLANNER_WORKFLOW_IDENTIFICATION_TEMPLATE = PromptTemplate(
    input_variables=["story_type", "title", "requirements_json", "available_workflows"],
    template="""Given this {story_type} story, identify which workflows are needed:

Story: {title}
Requirements: {requirements_json}

Available workflows:
{available_workflows}

Return ONLY a JSON array of workflow names, e.g. ["workflow1", "workflow2"]""",
)

PLANNER_RESPONSIBILITY_DEFINITION_TEMPLATE = PromptTemplate(
    input_variables=["workflow_name", "requirements_json"],
    template="""Define specific responsibilities for the {workflow_name} workflow in this story.

Requirements:
{requirements_json}

Provide 2-3 specific, actionable responsibilities this workflow should handle.""",
)

PLANNER_RISK_ASSESSMENT_TEMPLATE = PromptTemplate(
    input_variables=["task_names", "constraints_json"],
    template="""Identify risks for executing these workflows: {task_names}

Constraints: {constraints_json}

Return JSON array with objects like {{"factor": "...", "severity": "low|medium|high", "mitigation": "..."}}""",
)
