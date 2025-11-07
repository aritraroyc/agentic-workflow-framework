"""
Prompt template utilities and management for the agentic workflow framework.

This module provides utilities for working with LangChain PromptTemplate objects,
including validation, composition, and management of prompt templates across the framework.
"""

import json
import re
from typing import Any, Dict, List, Optional, Set
from langchain_core.prompts import PromptTemplate


class PromptTemplateValidator:
    """Validates PromptTemplate objects to ensure correct configuration."""

    @staticmethod
    def validate_template(
        template: PromptTemplate,
        template_name: str,
        expected_variables: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        """
        Validate a PromptTemplate for correctness.

        Args:
            template: The PromptTemplate to validate
            template_name: Name of the template for error reporting
            expected_variables: Optional set of variables that should be present

        Returns:
            Dict with validation results including:
            - 'valid': bool indicating if template is valid
            - 'variables': set of variables in the template
            - 'errors': list of validation errors if any
            - 'warnings': list of warnings if any

        Raises:
            ValueError: If template is invalid and contains critical issues
        """
        result = {
            "valid": True,
            "variables": set(template.input_variables),
            "errors": [],
            "warnings": [],
        }

        # Check if template has input_variables
        if not template.input_variables:
            result["errors"].append(f"{template_name}: No input_variables defined")
            result["valid"] = False

        # Check if expected variables match actual variables
        if expected_variables:
            actual = set(template.input_variables)
            missing = expected_variables - actual
            extra = actual - expected_variables

            if missing:
                result["warnings"].append(
                    f"{template_name}: Missing expected variables: {missing}"
                )
            if extra:
                result["warnings"].append(
                    f"{template_name}: Unexpected variables: {extra}"
                )

        # Check if template contains all declared variables
        template_str = template.template
        for var in template.input_variables:
            pattern = rf"\{{{var}\}}"
            if not re.search(pattern, template_str):
                result["errors"].append(
                    f"{template_name}: Variable '{var}' declared but not used in template"
                )
                result["valid"] = False

        if result["errors"]:
            raise ValueError(
                f"Template '{template_name}' validation failed: {result['errors']}"
            )

        return result

    @staticmethod
    def validate_all_templates(
        templates: Dict[str, PromptTemplate],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Validate multiple PromptTemplate objects.

        Args:
            templates: Dict mapping template names to PromptTemplate objects

        Returns:
            Dict mapping template names to validation results
        """
        results = {}
        for name, template in templates.items():
            try:
                results[name] = PromptTemplateValidator.validate_template(template, name)
            except ValueError as e:
                results[name] = {
                    "valid": False,
                    "variables": set(),
                    "errors": [str(e)],
                    "warnings": [],
                }
        return results


class PromptComposer:
    """Utilities for composing and combining prompts."""

    @staticmethod
    def create_system_user_messages(
        system_prompt: str, user_template: PromptTemplate, **kwargs
    ) -> List[Dict[str, str]]:
        """
        Create a system + user message pair for LLM invocation.

        Args:
            system_prompt: System message content
            user_template: PromptTemplate for user message
            **kwargs: Variables to format the user template with

        Returns:
            List of message dicts with role and content keys
        """
        user_content = user_template.format(**kwargs)
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

    @staticmethod
    def create_user_only_messages(
        user_template: PromptTemplate, **kwargs
    ) -> List[Dict[str, str]]:
        """
        Create a user-only message for LLM invocation.

        Args:
            user_template: PromptTemplate for user message
            **kwargs: Variables to format the template with

        Returns:
            List with single message dict
        """
        user_content = user_template.format(**kwargs)
        return [{"role": "user", "content": user_content}]

    @staticmethod
    def concatenate_templates(
        templates: List[PromptTemplate],
        separator: str = "\n\n",
    ) -> PromptTemplate:
        """
        Concatenate multiple PromptTemplate objects into a single template.

        Args:
            templates: List of PromptTemplate objects to combine
            separator: String to separate template outputs

        Returns:
            New PromptTemplate combining all input templates
        """
        # Collect all input variables
        all_variables = set()
        template_strings = []

        for template in templates:
            all_variables.update(template.input_variables)
            template_strings.append(template.template)

        combined_template = separator.join(template_strings)

        return PromptTemplate(
            input_variables=sorted(list(all_variables)),
            template=combined_template,
        )


class PromptFormatter:
    """Utilities for formatting and processing prompt content."""

    @staticmethod
    def format_json_for_prompt(
        data: Any, indent: int = 2, max_items: Optional[int] = None
    ) -> str:
        """
        Format data as JSON for inclusion in prompts.

        Args:
            data: Data to format
            indent: JSON indentation level
            max_items: Optional limit on array items to show

        Returns:
            Formatted JSON string
        """
        if max_items and isinstance(data, list):
            truncated_data = data[:max_items]
            json_str = json.dumps(truncated_data, indent=indent)
            if len(data) > max_items:
                json_str = json_str.rstrip("]") + f"\n  // ... ({len(data) - max_items} more items) ...\n]"
            return json_str
        else:
            return json.dumps(data, indent=indent)

    @staticmethod
    def format_list_for_prompt(
        items: List[str],
        format_style: str = "bullet",
        numbered_start: int = 1,
    ) -> str:
        """
        Format a list of items for inclusion in prompts.

        Args:
            items: List of strings to format
            format_style: 'bullet', 'numbered', or 'comma-separated'
            numbered_start: Starting number for numbered format

        Returns:
            Formatted string
        """
        if format_style == "bullet":
            return "\n".join(f"- {item}" for item in items)
        elif format_style == "numbered":
            return "\n".join(
                f"{i}. {item}" for i, item in enumerate(items, start=numbered_start)
            )
        elif format_style == "comma-separated":
            return ", ".join(items)
        else:
            raise ValueError(f"Unknown format_style: {format_style}")

    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """
        Truncate text to a maximum length.

        Args:
            text: Text to truncate
            max_length: Maximum length including suffix
            suffix: Suffix to add if truncated

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[: max_length - len(suffix)] + suffix


class PromptVariableExtractor:
    """Extract variables from prompt templates."""

    @staticmethod
    def extract_variables(template_str: str) -> Set[str]:
        """
        Extract variable names from a template string.

        Args:
            template_str: Template string with {variable} placeholders

        Returns:
            Set of variable names found in template
        """
        pattern = r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}"
        matches = re.findall(pattern, template_str)
        return set(matches)

    @staticmethod
    def check_missing_variables(
        template_str: str, provided_variables: Set[str]
    ) -> Set[str]:
        """
        Check which template variables are missing from provided variables.

        Args:
            template_str: Template string
            provided_variables: Set of provided variable names

        Returns:
            Set of missing variable names
        """
        required = PromptVariableExtractor.extract_variables(template_str)
        return required - provided_variables

    @staticmethod
    def check_unused_variables(
        template_str: str, provided_variables: Set[str]
    ) -> Set[str]:
        """
        Check which provided variables are not used in template.

        Args:
            template_str: Template string
            provided_variables: Set of provided variable names

        Returns:
            Set of unused variable names
        """
        required = PromptVariableExtractor.extract_variables(template_str)
        return provided_variables - required


class PromptTemplateManager:
    """
    Central manager for all prompt templates in the framework.

    Provides loading, caching, validation, and discovery of prompt templates.
    """

    def __init__(self):
        """Initialize the PromptTemplateManager."""
        self._templates: Dict[str, PromptTemplate] = {}
        self._categories: Dict[str, List[str]] = {}
        self._loaded = False

    def register_template(
        self,
        template_id: str,
        template: PromptTemplate,
        category: Optional[str] = None,
    ) -> None:
        """
        Register a PromptTemplate in the manager.

        Args:
            template_id: Unique identifier for the template
            template: The PromptTemplate object
            category: Optional category for grouping templates
        """
        # Validate template
        PromptTemplateValidator.validate_template(template, template_id)

        self._templates[template_id] = template

        if category:
            if category not in self._categories:
                self._categories[category] = []
            self._categories[category].append(template_id)

    def register_templates(
        self,
        templates: Dict[str, PromptTemplate],
        category: Optional[str] = None,
    ) -> None:
        """
        Register multiple PromptTemplate objects at once.

        Args:
            templates: Dict mapping template IDs to PromptTemplate objects
            category: Optional category for all templates
        """
        for template_id, template in templates.items():
            self.register_template(template_id, template, category)

    def get_template(self, template_id: str) -> PromptTemplate:
        """
        Get a PromptTemplate by ID.

        Args:
            template_id: ID of the template to retrieve

        Returns:
            The PromptTemplate object

        Raises:
            KeyError: If template_id not found
        """
        if template_id not in self._templates:
            raise KeyError(f"Template '{template_id}' not found in registry")
        return self._templates[template_id]

    def list_templates(self, category: Optional[str] = None) -> List[str]:
        """
        List available template IDs.

        Args:
            category: Optional category to filter by

        Returns:
            List of template IDs
        """
        if category:
            return self._categories.get(category, [])
        return list(self._templates.keys())

    def list_categories(self) -> List[str]:
        """Get list of all categories."""
        return list(self._categories.keys())

    def get_templates_by_category(self, category: str) -> Dict[str, PromptTemplate]:
        """
        Get all templates in a category.

        Args:
            category: Category name

        Returns:
            Dict mapping template IDs to PromptTemplate objects
        """
        template_ids = self._categories.get(category, [])
        return {tid: self._templates[tid] for tid in template_ids}

    def validate_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Validate all registered templates.

        Returns:
            Dict with validation results for each template
        """
        return PromptTemplateValidator.validate_all_templates(self._templates)

    def stats(self) -> Dict[str, Any]:
        """
        Get statistics about registered templates.

        Returns:
            Dict with statistics
        """
        return {
            "total_templates": len(self._templates),
            "total_categories": len(self._categories),
            "categories": self._categories,
            "templates_by_category": {
                cat: len(ids) for cat, ids in self._categories.items()
            },
        }
