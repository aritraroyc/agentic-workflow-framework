"""
LLM prompts for the API Development workflow.

This module contains all the prompt templates used for LLM interactions
during different phases of API development.
"""


# ========== API Planning Prompts ==========

PLAN_API_PROMPT = """Analyze the following story and create a detailed API development plan.

Story:
{story}

Requirements extracted:
{requirements}

Your task is to create a comprehensive API plan in JSON format with the following structure:
{{
    "api_name": "Name of the API",
    "api_description": "Detailed description of the API",
    "base_path": "/api/v1",
    "framework": "FastAPI|Flask|Django",
    "authentication_method": "JWT|OAuth2|API Key|None",
    "database_type": "PostgreSQL|MongoDB|SQLite|None",
    "has_database": true|false,
    "required_dependencies": ["list", "of", "dependencies"],
    "requirements": [
        {{
            "endpoint": "/endpoint",
            "method": "GET|POST|PUT|DELETE|PATCH",
            "description": "What this endpoint does",
            "authentication_required": true|false,
            "tags": ["tag1", "tag2"],
            "request_schema": {{}},
            "response_schema": {{}},
            "status_codes": [200, 400, 404, 500]
        }}
    ],
    "architecture_notes": "Notes about the overall architecture",
    "design_decisions": "Explanation of key design decisions"
}}

Focus on:
1. Extracting all endpoints mentioned in the story
2. Determining appropriate HTTP methods
3. Planning proper authentication and authorization
4. Selecting the best framework
5. Identifying database requirements
6. Planning error handling strategy

Return ONLY valid JSON, no additional text."""


# ========== API Design Prompts ==========

DESIGN_API_PROMPT = """Create a detailed OpenAPI specification and design document for the following API.

API Plan:
{plan}

Your task is to create a complete API design in JSON format with:
{{
    "openapi_spec": {{
        "openapi": "3.0.0",
        "info": {{}},
        "paths": {{}},
        "components": {{
            "schemas": {{}},
            "securitySchemes": {{}}
        }},
        "servers": []
    }},
    "design_notes": "Architecture and design decisions",
    "validation_rules": {{}},
    "error_handling_strategy": "Description of error handling approach"
}}

Focus on:
1. Creating complete OpenAPI 3.0 specification
2. Defining request/response schemas in detail
3. Planning validation rules for inputs
4. Defining error responses
5. Planning rate limiting and pagination if needed

Return ONLY valid JSON, no additional text."""


# ========== Code Generation Prompts ==========

GENERATE_CODE_PROMPT = """Generate Python {framework} code for the following API.

API Plan:
{plan}

API Design:
{design}

Generate Python code in the following structure. Return a Python dictionary with these keys:

{{
    "main_file": "FastAPI application code with all endpoints",
    "models_file": "Database models if needed",
    "schemas_file": "Pydantic request/response schemas",
    "routes_file": "Route definitions and handlers",
    "config_file": "Configuration and environment handling",
    "requirements": ["list", "of", "required", "packages"]
}}

For each key, provide the complete, production-ready Python code.

Code requirements:
1. Use proper type hints throughout
2. Include proper error handling
3. Add logging where appropriate
4. Use async/await where needed
5. Include comprehensive docstrings
6. Follow PEP 8 style guide
7. Include proper validation with Pydantic
8. Implement authentication if needed

Return ONLY valid JSON with code strings, no markdown code blocks."""


GENERATE_TESTS_PROMPT = """Generate comprehensive unit tests for the following API.

API Plan:
{plan}

Generated Code:
{code}

Generate pytest test code covering:
1. All endpoints
2. Request validation
3. Response validation
4. Error cases
5. Authentication (if implemented)
6. Database operations (if applicable)

Return a Python string containing complete test code with:
- Setup fixtures
- Test cases for each endpoint
- Parametrized tests where appropriate
- Mocking where needed
- Clear test names and docstrings

Focus on:
1. Happy path testing
2. Error case testing
3. Edge case testing
4. Integration testing between endpoints

Return ONLY the test code as a string in JSON format."""


GENERATE_DOCS_PROMPT = """Generate comprehensive documentation for the following API.

API Plan:
{plan}

API Design (OpenAPI spec):
{design}

Generated Code Summary:
{code_summary}

Generate documentation in JSON format:
{{
    "readme": "Complete README.md content with setup instructions and overview",
    "api_docs": "API documentation explaining endpoints, authentication, examples",
    "setup_instructions": "Step-by-step setup and installation instructions"
}}

Include in documentation:
1. API overview and purpose
2. Installation and setup instructions
3. Configuration guide
4. Authentication guide (if applicable)
5. Example requests and responses for each endpoint
6. Error codes and meanings
7. Rate limiting (if applicable)
8. Pagination details (if applicable)
9. Contributing guidelines
10. License information

Return ONLY valid JSON with markdown content in string fields."""


# ========== Validation Prompts ==========

VALIDATE_REQUIREMENTS_PROMPT = """Analyze if the following story contains sufficient information for API development.

Story:
{story}

Check for:
1. Clear API purpose and goals
2. At least 2-3 endpoint specifications
3. Authentication/authorization requirements
4. Data model descriptions
5. Error handling expectations
6. Performance requirements
7. Database requirements
8. Integration requirements

Return JSON:
{{
    "is_valid": true|false,
    "missing_elements": ["list", "of", "missing", "items"],
    "suggestions": ["list", "of", "suggestions"],
    "confidence": 0.0-1.0,
    "summary": "Brief assessment"
}}"""
