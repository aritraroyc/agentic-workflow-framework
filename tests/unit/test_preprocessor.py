"""
Unit tests for the Preprocessor Agent.

Tests cover:
- Markdown section parsing
- Structure validation
- Data extraction (heuristic)
- Metadata generation
- Story type detection
- Complexity estimation
"""

import pytest
from workflows.parent.agents.preprocessor import PreprocessorAgent


class TestMarkdownParsing:
    """Tests for markdown section parsing."""

    @pytest.fixture
    def preprocessor(self) -> PreprocessorAgent:
        """Create a preprocessor instance for testing."""
        return PreprocessorAgent()

    def test_parse_simple_sections(self, preprocessor: PreprocessorAgent) -> None:
        """Test parsing simple markdown sections."""
        content = """# Introduction
        This is the intro.

        # Details
        Some details here.

        # More Info
        Additional information."""

        sections = preprocessor._parse_markdown_sections(content)

        assert "Introduction" in sections
        assert "Details" in sections
        assert "More Info" in sections
        assert "This is the intro" in sections["Introduction"]

    def test_parse_preamble(self, preprocessor: PreprocessorAgent) -> None:
        """Test parsing preamble before first header."""
        content = """Some preamble text here.
        This is before any header.

        # Section 1
        Content here."""

        sections = preprocessor._parse_markdown_sections(content)

        assert "preamble" in sections
        assert "Some preamble text" in sections["preamble"]
        assert "Section 1" in sections

    def test_parse_nested_headers(self, preprocessor: PreprocessorAgent) -> None:
        """Test parsing nested header levels (are now parsed as separate sections)."""
        content = """# Main
        Main content.

        ## Sub
        Sub content.

        ### SubSub
        SubSub content."""

        sections = preprocessor._parse_markdown_sections(content)

        # Note: With the updated parser, nested headers are now parsed as separate sections
        assert "Main" in sections
        assert "Sub" in sections
        assert "SubSub" in sections

    def test_parse_empty_sections(self, preprocessor: PreprocessorAgent) -> None:
        """Test parsing with empty sections."""
        content = """# Section 1

        # Section 2
        Content in section 2."""

        sections = preprocessor._parse_markdown_sections(content)

        assert "Section 1" in sections
        assert "Section 2" in sections
        assert sections["Section 1"].strip() == ""

    def test_parse_with_special_characters(self, preprocessor: PreprocessorAgent) -> None:
        """Test parsing sections with special characters in names."""
        content = """# REST API - Design & Implementation
        API design content.

        # User Management (CRUD)
        User management content."""

        sections = preprocessor._parse_markdown_sections(content)

        assert "REST API - Design & Implementation" in sections
        assert "User Management (CRUD)" in sections


class TestStructureValidation:
    """Tests for structure validation."""

    @pytest.fixture
    def preprocessor(self) -> PreprocessorAgent:
        """Create a preprocessor instance for testing."""
        return PreprocessorAgent()

    def test_valid_structure(self, preprocessor: PreprocessorAgent) -> None:
        """Test validation of valid story structure."""
        content = """# Story
This is a great story.

# Requirements
- Requirement 1
- Requirement 2"""

        sections = preprocessor._parse_markdown_sections(content)
        is_valid, errors = preprocessor._validate_structure(sections, content)

        assert is_valid is True
        assert len(errors) == 0

    def test_missing_required_section(self, preprocessor: PreprocessorAgent) -> None:
        """Test validation when required section is missing."""
        content = """# Story
        This is a story but missing requirements."""

        sections = preprocessor._parse_markdown_sections(content)
        is_valid, errors = preprocessor._validate_structure(sections, content)

        assert is_valid is False
        assert any("Requirements" in error for error in errors)

    def test_empty_section_error(self, preprocessor: PreprocessorAgent) -> None:
        """Test validation detects empty sections."""
        content = """# Story

# Requirements
- Requirement 1"""

        sections = preprocessor._parse_markdown_sections(content)
        is_valid, errors = preprocessor._validate_structure(sections, content)

        # Story section is empty, so should have error
        assert any("empty" in error.lower() for error in errors)

    def test_minimum_content_length(self, preprocessor: PreprocessorAgent) -> None:
        """Test validation of minimum content length."""
        short_content = "# Story\nX"
        sections = preprocessor._parse_markdown_sections(short_content)
        is_valid, errors = preprocessor._validate_structure(sections, short_content)

        assert any("too short" in error.lower() for error in errors)

    def test_long_valid_content(self, preprocessor: PreprocessorAgent) -> None:
        """Test validation passes with sufficient content."""
        content = """# Story
        This is a well-formed story with sufficient content to pass minimum length validation. It contains detailed information about the requirements and objectives.

        # Requirements
        - Requirement one that is quite detailed
        - Another requirement with more information"""

        sections = preprocessor._parse_markdown_sections(content)
        is_valid, errors = preprocessor._validate_structure(sections, content)

        assert len([e for e in errors if "too short" in e.lower()]) == 0


class TestDataExtraction:
    """Tests for data extraction from sections."""

    @pytest.fixture
    def preprocessor(self) -> PreprocessorAgent:
        """Create a preprocessor instance for testing."""
        return PreprocessorAgent()

    @pytest.fixture
    def sample_sections(self) -> dict:
        """Create sample parsed sections."""
        return {
            "preamble": "User Management API",
            "Story": "Build a user management API with authentication",
            "Requirements": "- JWT tokens\n- User registration\n- Email verification",
            "Success Criteria": "- All endpoints working\n- 80% test coverage",
            "Constraints": "- Python 3.11+\n- PostgreSQL required",
        }

    def test_extract_title(self, preprocessor: PreprocessorAgent, sample_sections: dict) -> None:
        """Test title extraction."""
        title = preprocessor._extract_title(sample_sections)

        assert title == "User Management API"
        assert len(title) > 0

    def test_extract_description(self, preprocessor: PreprocessorAgent, sample_sections: dict) -> None:
        """Test description extraction."""
        description = preprocessor._extract_description(sample_sections)

        assert "user management" in description.lower() or "API" in description
        assert len(description) > 0

    def test_extract_requirements(self, preprocessor: PreprocessorAgent, sample_sections: dict) -> None:
        """Test requirements extraction."""
        requirements = preprocessor._extract_requirements(sample_sections)

        assert len(requirements) >= 2
        assert any("JWT" in req or "token" in req.lower() for req in requirements)

    def test_extract_success_criteria(self, preprocessor: PreprocessorAgent, sample_sections: dict) -> None:
        """Test success criteria extraction."""
        criteria = preprocessor._extract_success_criteria(sample_sections)

        assert len(criteria) >= 1
        assert any("test" in c.lower() or "endpoint" in c.lower() for c in criteria)

    def test_extract_constraints(self, preprocessor: PreprocessorAgent, sample_sections: dict) -> None:
        """Test constraints extraction."""
        constraints = preprocessor._extract_constraints(sample_sections)

        assert len(constraints) >= 1
        assert any("Python" in c or "PostgreSQL" in c for c in constraints)

    def test_extract_components(self, preprocessor: PreprocessorAgent) -> None:
        """Test component extraction from content."""
        sections = {
            "Overview": "We need to create an API service for user management with authentication module"
        }

        components = preprocessor._extract_components(sections)

        assert isinstance(components, list)


class TestMetadataGeneration:
    """Tests for metadata generation."""

    @pytest.fixture
    def preprocessor(self) -> PreprocessorAgent:
        """Create a preprocessor instance for testing."""
        return PreprocessorAgent()

    def test_metadata_includes_story_type(self, preprocessor: PreprocessorAgent) -> None:
        """Test that metadata includes detected story type."""
        sections = {
            "Story": "Build a REST API for user authentication",
        }
        extracted = {"title": "Auth API"}
        full_content = "Build a REST API endpoint for authentication service"

        metadata = preprocessor._extract_metadata(sections, extracted, full_content)

        assert "story_type" in metadata
        assert metadata["story_type"] in ["api_development", "api_enhancement", "unknown"]

    def test_metadata_includes_metrics(self, preprocessor: PreprocessorAgent) -> None:
        """Test that metadata includes story metrics."""
        sections = {
            "Story": "Build an API",
            "Requirements": "- Requirement 1\n- Requirement 2",
        }
        extracted = {
            "requirements": ["Req1", "Req2"],
            "success_criteria": ["Crit1"],
        }
        full_content = "Build a REST API for user authentication with proper error handling and comprehensive documentation"

        metadata = preprocessor._extract_metadata(sections, extracted, full_content)

        assert "word_count" in metadata
        assert "section_count" in metadata
        assert "requirement_count" in metadata
        assert metadata["section_count"] == 2
        assert metadata["requirement_count"] == 2

    def test_metadata_timestamp(self, preprocessor: PreprocessorAgent) -> None:
        """Test that metadata includes timestamp."""
        metadata = preprocessor._extract_metadata({}, {}, "sample content")

        assert "detected_at" in metadata
        assert len(metadata["detected_at"]) > 0


class TestStoryTypeDetection:
    """Tests for story type detection."""

    @pytest.fixture
    def preprocessor(self) -> PreprocessorAgent:
        """Create a preprocessor instance for testing."""
        return PreprocessorAgent()

    def test_detect_api_development(self, preprocessor: PreprocessorAgent) -> None:
        """Test detection of API development story."""
        content = "Build a REST API endpoint for user management with proper authentication"
        extracted = {}

        story_type = preprocessor._detect_story_type(content, extracted)

        assert story_type == "api_development"

    def test_detect_api_enhancement(self, preprocessor: PreprocessorAgent) -> None:
        """Test detection of API enhancement story."""
        content = "Enhance the existing API with rate limiting and better error handling"
        extracted = {}

        story_type = preprocessor._detect_story_type(content, extracted)

        assert story_type == "api_enhancement"

    def test_detect_ui_development(self, preprocessor: PreprocessorAgent) -> None:
        """Test detection of UI development story."""
        content = "Create a user interface component for the dashboard with real-time data updates"
        extracted = {}

        story_type = preprocessor._detect_story_type(content, extracted)

        assert story_type == "ui_development"

    def test_detect_ui_enhancement(self, preprocessor: PreprocessorAgent) -> None:
        """Test detection of UI enhancement story."""
        content = "Enhance the existing UI component with improved accessibility and performance"
        extracted = {}

        story_type = preprocessor._detect_story_type(content, extracted)

        assert story_type == "ui_enhancement"

    def test_detect_unknown_type(self, preprocessor: PreprocessorAgent) -> None:
        """Test detection when story type is unclear."""
        content = "Implement a generic feature with some functionality"
        extracted = {}

        story_type = preprocessor._detect_story_type(content, extracted)

        assert story_type == "unknown"


class TestComplexityEstimation:
    """Tests for story complexity estimation."""

    @pytest.fixture
    def preprocessor(self) -> PreprocessorAgent:
        """Create a preprocessor instance for testing."""
        return PreprocessorAgent()

    def test_low_complexity(self, preprocessor: PreprocessorAgent) -> None:
        """Test estimation of low complexity story."""
        complexity = preprocessor._estimate_complexity(word_count=200, requirement_count=1)

        assert complexity == "low"

    def test_medium_complexity(self, preprocessor: PreprocessorAgent) -> None:
        """Test estimation of medium complexity story."""
        # Complexity = (word_count/100) + (requirement_count * 2)
        # For medium: 5 <= score < 15
        complexity = preprocessor._estimate_complexity(word_count=300, requirement_count=3)

        assert complexity == "medium"

    def test_high_complexity(self, preprocessor: PreprocessorAgent) -> None:
        """Test estimation of high complexity story."""
        complexity = preprocessor._estimate_complexity(word_count=2000, requirement_count=15)

        assert complexity == "high"


class TestProcessIntegration:
    """Integration tests for the complete preprocessing pipeline."""

    @pytest.fixture
    def preprocessor(self) -> PreprocessorAgent:
        """Create a preprocessor instance for testing."""
        return PreprocessorAgent()

    @pytest.mark.asyncio
    async def test_process_valid_story(self, preprocessor: PreprocessorAgent) -> None:
        """Test processing a complete valid story."""
        story = """# Story
Build a comprehensive user management API with authentication.

# Requirements
- User registration with email verification
- JWT authentication
- Role-based access control
- User profile management

# Success Criteria
- All endpoints functional
- 80% test coverage
- OpenAPI documentation complete"""

        output = await preprocessor.process(story)

        assert output["structure_valid"] is True
        assert len(output["parsed_sections"]) > 0
        assert "detected_story_type" in output
        assert output["detected_story_type"] in ["api_development", "unknown"]

    @pytest.mark.asyncio
    async def test_process_invalid_story(self, preprocessor: PreprocessorAgent) -> None:
        """Test processing an invalid story."""
        story = "Too short"

        output = await preprocessor.process(story)

        assert output["structure_valid"] is False
        assert len(output["parsing_errors"]) > 0

    @pytest.mark.asyncio
    async def test_process_missing_section(self, preprocessor: PreprocessorAgent) -> None:
        """Test processing story with missing required sections."""
        story = """# Story
        This is the story section.
        With some good content here."""

        output = await preprocessor.process(story)

        assert output["structure_valid"] is False
        assert any("Requirements" in error for error in output["parsing_errors"])

    @pytest.mark.asyncio
    async def test_process_returns_valid_output_structure(self, preprocessor: PreprocessorAgent) -> None:
        """Test that process returns properly structured output."""
        story = """# Story
        Build a user management API with authentication.

        # Requirements
        - Support user registration
        - Implement JWT tokens
        - Add rate limiting"""

        output = await preprocessor.process(story)

        # Verify all required fields are present
        assert "parsed_sections" in output
        assert "structure_valid" in output
        assert "extracted_data" in output
        assert "metadata" in output
        assert "parsing_errors" in output
        assert "parsing_warnings" in output
        assert "input_summary" in output
        assert "detected_story_type" in output

    def test_load_validation_rules(self, preprocessor: PreprocessorAgent) -> None:
        """Test loading validation rules."""
        rules = preprocessor.validation_rules

        assert "story_types" in rules or "required_sections" in rules
        # Should have either loaded from file or defaults
        assert len(rules) > 0

    def test_create_summary(self, preprocessor: PreprocessorAgent) -> None:
        """Test summary creation."""
        sections = {
            "preamble": "Intro",
            "Story": "Build an API service",
            "Requirements": "Requirements list",
        }

        summary = preprocessor._create_summary(sections)

        assert len(summary) > 0
        assert isinstance(summary, str)
