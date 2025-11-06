"""
Preprocessor Agent for parsing and validating workflow input stories.

This agent handles:
1. Markdown parsing of input stories
2. Structure validation against rules
3. LLM-based structured data extraction
4. Metadata generation and story type detection
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import asyncio
import yaml

from workflows.parent.state import PreprocessorOutput, ExecutionLogEntry

logger = logging.getLogger(__name__)


class PreprocessorAgent:
    """
    Agent responsible for preprocessing and validating workflow input stories.

    The preprocessor:
    1. Parses markdown sections from input
    2. Validates structure against configured rules
    3. Extracts structured data using LLM
    4. Generates metadata about the story

    Attributes:
        llm: Language model client for data extraction
        validation_rules: Dictionary of validation rules from config
    """

    def __init__(self, llm=None, validation_rules_path: str = "config/validation_rules.yaml"):
        """
        Initialize the preprocessor agent.

        Args:
            llm: Language model client (ChatOpenAI or ChatAnthropic)
            validation_rules_path: Path to validation rules YAML file
        """
        self.llm = llm
        self.validation_rules = self._load_validation_rules(validation_rules_path)
        self.markdown_section_pattern = re.compile(r"^#+\s+(.+?)$", re.MULTILINE)
        logger.info("PreprocessorAgent initialized")

    def _load_validation_rules(self, rules_path: str) -> Dict[str, Any]:
        """
        Load validation rules from YAML configuration.

        Args:
            rules_path: Path to the validation rules YAML file

        Returns:
            Dictionary containing validation rules, empty dict if file not found
        """
        try:
            with open(rules_path, "r") as f:
                rules: Dict[str, Any] = yaml.safe_load(f) or {}
                logger.info(f"Loaded validation rules from {rules_path}")
                return rules
        except FileNotFoundError:
            logger.warning(f"Validation rules file not found at {rules_path}, using defaults")
            return self._get_default_rules()

    def _get_default_rules(self) -> Dict[str, Any]:
        """
        Return default validation rules if config file is not found.

        Returns:
            Dictionary with default validation rules
        """
        return {
            "story_types": ["api_development", "ui_development", "api_enhancement", "ui_enhancement"],
            "required_sections": ["Story", "Requirements"],
            "optional_sections": ["Success Criteria", "Constraints", "Notes", "Acceptance Criteria"],
            "required_fields": ["title", "description"],
        }

    async def process(self, input_story: str) -> PreprocessorOutput:
        """
        Process the input story through the complete preprocessing pipeline.

        Args:
            input_story: Raw markdown story input

        Returns:
            PreprocessorOutput TypedDict with parsed and processed data

        Raises:
            ValueError: If critical validation fails
        """
        errors: List[str] = []
        warnings: List[str] = []

        try:
            # Step 1: Parse markdown sections
            parsed_sections = self._parse_markdown_sections(input_story)

            # Step 2: Validate structure
            structure_valid, validation_errors = self._validate_structure(
                parsed_sections, input_story
            )
            if validation_errors:
                errors.extend(validation_errors)
                warnings.append("Structure validation failed")

            # Step 3: Extract structured data using LLM
            extracted_data = await self._extract_structured_data(
                input_story, parsed_sections
            )
            if not extracted_data and structure_valid:
                warnings.append("LLM extraction returned empty data")

            # Step 4: Generate metadata
            metadata = self._extract_metadata(
                parsed_sections, extracted_data, input_story
            )

            # Create output
            output: PreprocessorOutput = {
                "parsed_sections": parsed_sections,
                "structure_valid": structure_valid,
                "extracted_data": extracted_data,
                "metadata": metadata,
                "parsing_errors": errors,
                "parsing_warnings": warnings,
                "input_summary": self._create_summary(parsed_sections),
                "detected_story_type": metadata.get("story_type", "unknown"),
            }

            logger.info(
                f"Preprocessing complete: {len(parsed_sections)} sections parsed, "
                f"structure_valid={structure_valid}, errors={len(errors)}, warnings={len(warnings)}"
            )
            return output

        except Exception as e:
            logger.error(f"Preprocessor error: {str(e)}", exc_info=True)
            return {
                "parsed_sections": {},
                "structure_valid": False,
                "extracted_data": {},
                "metadata": {},
                "parsing_errors": [str(e)],
                "parsing_warnings": warnings,
                "input_summary": "",
                "detected_story_type": "unknown",
            }

    def _parse_markdown_sections(self, content: str) -> Dict[str, str]:
        """
        Parse markdown content into sections by headers.

        Args:
            content: Raw markdown content

        Returns:
            Dictionary mapping section names to section content
        """
        sections: Dict[str, str] = {}
        current_section = "preamble"
        current_content: List[str] = []

        for line in content.split("\n"):
            # Check if line is a markdown header (allowing for leading whitespace)
            stripped_line = line.lstrip()
            match = re.match(r"^(#+)\s+(.+?)$", stripped_line)
            if match:
                # Save previous section
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                    current_content = []

                # Start new section
                current_section = match.group(2).strip()
                logger.debug(f"Parsed section: {current_section}")
            else:
                # Only add non-empty lines or preserve spacing
                current_content.append(line)

        # Save final section
        if current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def _validate_structure(
        self, sections: Dict[str, str], full_content: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate the structure of parsed sections against rules.

        Args:
            sections: Dictionary of parsed sections
            full_content: Original full content for context

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors: List[str] = []

        # Get required sections from rules
        required = self.validation_rules.get("required_sections", [])
        optional = self.validation_rules.get("optional_sections", [])

        # Check required sections
        section_names = [s.lower().strip() for s in sections.keys()]

        for req in required:
            req_lower = req.lower()
            if not any(req_lower in sn for sn in section_names):
                errors.append(f"Missing required section: {req}")

        # Warn about empty sections
        for section_name, content in sections.items():
            if not content.strip():
                errors.append(f"Section '{section_name}' is empty")

        # Check minimum content length
        if len(full_content.strip()) < 50:
            errors.append("Input story is too short (minimum 50 characters)")

        logger.debug(f"Structure validation: {len(errors)} errors found")
        return len(errors) == 0, errors

    async def _extract_structured_data(
        self, full_content: str, sections: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Use LLM to extract structured data from the story.

        Args:
            full_content: Full story content
            sections: Parsed sections

        Returns:
            Dictionary with extracted structured data
        """
        if not self.llm:
            logger.warning("No LLM client provided, skipping LLM extraction")
            return self._extract_structured_data_heuristic(sections)

        try:
            # Create extraction prompt
            prompt = self._create_extraction_prompt(full_content, sections)

            # Call LLM
            response = await asyncio.to_thread(
                self.llm.invoke,
                [{"role": "user", "content": prompt}]
            )

            # Parse response
            extracted = self._parse_llm_response(response)
            logger.info("Successfully extracted structured data using LLM")
            return extracted

        except Exception as e:
            logger.warning(f"LLM extraction failed: {str(e)}, falling back to heuristic")
            return self._extract_structured_data_heuristic(sections)

    def _extract_structured_data_heuristic(
        self, sections: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Extract structured data using heuristic rules (fallback).

        Args:
            sections: Parsed sections

        Returns:
            Dictionary with extracted data
        """
        extracted: Dict[str, Any] = {
            "title": self._extract_title(sections),
            "description": self._extract_description(sections),
            "requirements": self._extract_requirements(sections),
            "success_criteria": self._extract_success_criteria(sections),
            "constraints": self._extract_constraints(sections),
            "components": self._extract_components(sections),
        }

        return extracted

    def _extract_title(self, sections: Dict[str, str]) -> str:
        """Extract story title from sections."""
        # Try preamble first
        if "preamble" in sections:
            first_line = sections["preamble"].split("\n")[0]
            if first_line.strip():
                return first_line.strip()

        # Try first section that's not empty
        for section_name, content in sections.items():
            if section_name != "preamble" and content.strip():
                first_line = content.split("\n")[0]
                return first_line.strip()

        return "Untitled Story"

    def _extract_description(self, sections: Dict[str, str]) -> str:
        """Extract description from sections."""
        for section_name in ["Story", "Description", "Overview"]:
            for key in sections.keys():
                if section_name.lower() in key.lower():
                    return sections[key].strip()

        return sections.get("preamble", "").strip()

    def _extract_requirements(self, sections: Dict[str, str]) -> List[str]:
        """Extract requirements list from sections."""
        requirements: List[str] = []

        for key, content in sections.items():
            if "requirement" in key.lower():
                # Split by lines and clean up
                lines = [
                    line.strip().lstrip("- •*").strip()
                    for line in content.split("\n")
                    if line.strip() and not line.strip().startswith("#")
                ]
                requirements.extend(lines)

        return requirements

    def _extract_success_criteria(self, sections: Dict[str, str]) -> List[str]:
        """Extract success criteria from sections."""
        criteria: List[str] = []

        for key, content in sections.items():
            if "success" in key.lower() or "acceptance" in key.lower():
                lines = [
                    line.strip().lstrip("- •*").strip()
                    for line in content.split("\n")
                    if line.strip() and not line.strip().startswith("#")
                ]
                criteria.extend(lines)

        return criteria

    def _extract_constraints(self, sections: Dict[str, str]) -> List[str]:
        """Extract constraints from sections."""
        constraints: List[str] = []

        for key, content in sections.items():
            if "constraint" in key.lower() or "limitation" in key.lower():
                lines = [
                    line.strip().lstrip("- •*").strip()
                    for line in content.split("\n")
                    if line.strip() and not line.strip().startswith("#")
                ]
                constraints.extend(lines)

        return constraints

    def _extract_components(self, sections: Dict[str, str]) -> List[str]:
        """Extract component references from content."""
        components: List[str] = []
        all_text = " ".join(sections.values())

        # Look for common component patterns
        patterns = [
            r"(?:component|service|module|api|endpoint)\s+['\"]?([a-zA-Z0-9_\-]+)",
            r"(?:create|build|develop|implement)\s+(?:a|the)?\s+([a-zA-Z0-9_\-]+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            components.extend(matches)

        return list(set(components))  # Remove duplicates

    def _extract_metadata(
        self, sections: Dict[str, str], extracted: Dict[str, Any], full_content: str
    ) -> Dict[str, Any]:
        """
        Generate metadata about the story.

        Args:
            sections: Parsed sections
            extracted: Extracted structured data
            full_content: Full story content

        Returns:
            Dictionary with metadata
        """
        # Detect story type
        story_type = self._detect_story_type(full_content, extracted)

        # Calculate story metrics
        word_count = len(full_content.split())
        section_count = len(sections)
        requirement_count = len(extracted.get("requirements", []))

        metadata: Dict[str, Any] = {
            "story_type": story_type,
            "detected_at": datetime.now().isoformat(),
            "word_count": word_count,
            "section_count": section_count,
            "requirement_count": requirement_count,
            "success_criteria_count": len(extracted.get("success_criteria", [])),
            "constraint_count": len(extracted.get("constraints", [])),
            "components_mentioned": extracted.get("components", []),
            "has_preamble": "preamble" in sections and bool(sections["preamble"].strip()),
            "estimated_complexity": self._estimate_complexity(
                word_count, requirement_count
            ),
        }

        return metadata

    def _detect_story_type(
        self, full_content: str, extracted: Dict[str, Any]
    ) -> str:
        """
        Detect the type of story (API, UI, etc.) using keyword matching.

        Counts keyword matches to determine the most likely story type,
        allowing stories to mention both API and UI concepts.
        Uses word boundaries to avoid substring matches (e.g., "add" in "addresses").

        Args:
            full_content: Full story content
            extracted: Extracted data

        Returns:
            Story type string
        """
        lower_content = full_content.lower()

        # Define keyword patterns (used for counting)
        api_keywords = ["api", "endpoint", "rest", "http", "service", "backend", "database"]
        ui_keywords = ["ui", "frontend", "interface", "component", "mfe", "react", "vue", "angular",
                      "dashboard", "design", "layout", "button", "form", "widget", "page"]
        # Enhancement keywords - using more specific terms to avoid substring matches
        enhancement_keywords = ["enhancement", "enhance", "improve", "improvement", "upgrade", "extend", "extension"]

        # Helper function to check for whole word matches using word boundaries
        def count_word_matches(content: str, keywords: List[str]) -> int:
            count = 0
            for keyword in keywords:
                # Use word boundary regex: \b matches word boundaries
                import re
                if re.search(rf'\b{re.escape(keyword)}\b', content):
                    count += 1
            return count

        # Count keyword matches using word boundaries
        api_count = count_word_matches(lower_content, api_keywords)
        ui_count = count_word_matches(lower_content, ui_keywords)
        is_enhancement = count_word_matches(lower_content, enhancement_keywords) > 0

        # Determine type based on keyword count
        if ui_count > api_count:
            return "ui_enhancement" if is_enhancement else "ui_development"
        elif api_count > ui_count:
            return "api_enhancement" if is_enhancement else "api_development"
        else:
            # Fallback to keyword presence (UI takes precedence if equal)
            if ui_count > 0:
                return "ui_enhancement" if is_enhancement else "ui_development"
            elif api_count > 0:
                return "api_enhancement" if is_enhancement else "api_development"

        # Default
        return "unknown"

    def _estimate_complexity(self, word_count: int, requirement_count: int) -> str:
        """
        Estimate story complexity based on metrics.

        Args:
            word_count: Total word count
            requirement_count: Number of requirements

        Returns:
            Complexity level: low, medium, high
        """
        complexity_score = (word_count / 100) + (requirement_count * 2)

        if complexity_score < 5:
            return "low"
        elif complexity_score < 15:
            return "medium"
        else:
            return "high"

    def _create_summary(self, sections: Dict[str, str]) -> str:
        """
        Create a brief summary of the story.

        Args:
            sections: Parsed sections

        Returns:
            Summary string
        """
        summary_parts: List[str] = []

        # Add first section as summary
        for section_name, content in sections.items():
            if section_name != "preamble" and content.strip():
                first_line = content.split("\n")[0]
                summary_parts.append(f"{section_name}: {first_line}")
                break

        if not summary_parts:
            return "No summary available"

        return " | ".join(summary_parts[:2])

    def _create_extraction_prompt(
        self, full_content: str, sections: Dict[str, str]
    ) -> str:
        """
        Create the LLM prompt for structured data extraction.

        Args:
            full_content: Full story content
            sections: Parsed sections

        Returns:
            Prompt string for LLM
        """
        return f"""Analyze the following workflow story and extract structured information.

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

Return ONLY valid JSON, no markdown formatting."""

    def _parse_llm_response(self, response: Any) -> Dict[str, Any]:
        """
        Parse LLM response into structured data.

        Args:
            response: Response from LLM

        Returns:
            Dictionary with extracted data
        """
        try:
            import json

            response_text = (
                response.content if hasattr(response, "content") else str(response)
            )

            # Try to extract JSON from response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed: Dict[str, Any] = json.loads(json_str)
                return parsed

            return {}
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {str(e)}")
            return {}
