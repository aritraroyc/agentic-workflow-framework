"""
Prompt templates for the API Development workflow.

This module contains LangChain PromptTemplate objects for all phases of API development:
- Planning and analysis
- Design and specification
- Code generation
- Test generation
- Validation
"""

from langchain_core.prompts import PromptTemplate

# ========== API Planning Templates ==========

VALIDATE_REQUIREMENTS_PROMPT = PromptTemplate(
    input_variables=["story"],
    template="""Analyze if the following story contains sufficient information for API development.

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
}}""",
)

PLAN_API_PROMPT = PromptTemplate(
    input_variables=["story", "requirements"],
    template="""Analyze the following story and create a detailed API development plan.

Story:
{story}

Requirements extracted:
{requirements}

Your task is to create a comprehensive API plan in JSON format with the following structure:
{{
    "api_name": "Name of the API",
    "api_description": "Detailed description of the API",
    "base_path": "/api/v1",
    "framework": "FastAPI|Flask|Django|Spring Boot",
    "java_version": "17|21",
    "build_tool": "Maven|Gradle",
    "authentication_method": "JWT|OAuth2|API Key|Spring Security|None",
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

Framework Selection Guidance:
- For Python: Use FastAPI (modern async), Flask (simple), or Django (full-featured)
- For Java: Use Spring Boot 3.x with Spring Web (traditional) or Spring WebFlux (reactive)
- If story mentions "Java", "Spring", "Kotlin", or "enterprise", prefer Spring Boot
- If story mentions "Python", "async", "lightweight", prefer FastAPI
- If no preference, choose based on team expertise mentioned

If Framework is Spring Boot:
- Set java_version to 21 (latest LTS) unless specified otherwise
- Set build_tool based on team preference (Maven for simplicity, Gradle for flexibility)
- Set authentication to "Spring Security" for enterprise patterns
- Dependencies will be Spring Boot starters (handled in code generation)

Focus on:
1. Extracting all endpoints mentioned in the story
2. Determining appropriate HTTP methods
3. Planning proper authentication and authorization
4. Selecting the best framework for the use case
5. Identifying database requirements
6. Planning error handling strategy
7. For Spring Boot: Identifying if reactive (WebFlux) or traditional (Web) is needed

Return ONLY valid JSON, no additional text.""",
)

# ========== API Design Templates ==========

DESIGN_API_PROMPT = PromptTemplate(
    input_variables=["plan"],
    template="""Create a detailed API design specification for the following API plan.

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
    "error_handling_strategy": "Description of error handling approach",
    "spring_boot_specific": {{
        "if_framework_is_spring_boot": {{
            "controller_structure": "Recommended controller organization",
            "service_layer_pattern": "Service layer design pattern",
            "jpa_entity_mapping": "Entity relationships and JPA annotations",
            "spring_security_filters": "Security filter chain configuration",
            "exception_handlers": "GlobalExceptionHandler mapping"
        }}
    }}
}}

If Framework is Spring Boot:
1. Include controller structure with recommended annotations (@RestController, @RequestMapping, @PostMapping, etc.)
2. Plan JPA entity relationships (@OneToMany, @ManyToOne, @JoinTable, etc.)
3. Define Spring Security configuration approach (JWT token validation, role-based access)
4. Plan service layer structure with @Service and @Transactional annotations
5. Define exception handling with @ControllerAdvice and custom exceptions
6. Include Spring Data JPA repository patterns

If Framework is Python (FastAPI/Flask/Django):
1. Create OpenAPI spec focusing on endpoint definitions
2. Plan request/response validation with Pydantic (FastAPI) or marshmallow (Flask)
3. Define error handling middleware structure

Focus on:
1. Creating complete OpenAPI 3.0 specification
2. Defining request/response schemas in detail
3. Planning validation rules for inputs
4. Defining error responses
5. Planning rate limiting and pagination if needed
6. For Spring Boot: Planning entity relationships and security configuration

Return ONLY valid JSON, no additional text.""",
)

# ========== Code Generation Templates ==========

GENERATE_CODE_PROMPT = PromptTemplate(
    input_variables=["framework", "plan", "design"],
    template="""Generate {framework} code for the following API.

API Plan:
{plan}

API Design:
{design}

IMPORTANT: Select output format based on framework type. Return ONLY valid JSON with code strings.

IF FRAMEWORK IS FASTAPI, FLASK, OR DJANGO (Python):
{{
    "language": "Python",
    "main_file": "FastAPI application code with all endpoints",
    "models_file": "Database models if needed",
    "schemas_file": "Pydantic request/response schemas",
    "routes_file": "Route definitions and handlers",
    "config_file": "Configuration and environment handling",
    "requirements_txt": "pip dependencies file content"
}}

IF FRAMEWORK IS SPRING BOOT (Java):
{{
    "language": "Java",
    "pom_xml": "Maven pom.xml with Spring Boot dependencies and plugins",
    "gradle_build": "Alternative: Gradle build.gradle.kts (provide pom_xml OR gradle_build)",
    "main_application_class": "SpringBootApplication with main method",
    "controllers": {{
        "ControllerName.java": "Spring REST controller code with @RestController"
    }},
    "entities": {{
        "EntityName.java": "JPA @Entity classes with relationships"
    }},
    "repositories": {{
        "RepositoryName.java": "Spring Data JPA @Repository interfaces"
    }},
    "services": {{
        "ServiceName.java": "@Service classes with @Transactional business logic"
    }},
    "security_config": "SecurityConfig.java or SecurityFilterChain configuration",
    "exception_handler": "GlobalExceptionHandler with @ControllerAdvice",
    "application_yml": "application-dev.yml Spring Boot configuration",
    "test_files": {{
        "TestClassName.java": "JUnit 5 tests with @SpringBootTest"
    }}
}}

For Python (FastAPI/Flask/Django):
1. Use proper type hints throughout
2. Include proper error handling with try-except
3. Add logging where appropriate
4. Use async/await where needed for FastAPI
5. Include comprehensive docstrings
6. Follow PEP 8 style guide
7. Include proper validation with Pydantic (FastAPI) or marshmallow (Flask)
8. Implement authentication if needed

For Java/Spring Boot (Java 21+, Spring Boot 3+):
1. Use Spring Boot 3.x annotations (@RestController, @Service, @Repository, @Entity)
2. Use Java records where appropriate for DTOs
3. Implement Spring Security with JWT or OAuth2 if needed
4. Use Spring Data JPA with proper relationships (@OneToMany, @ManyToOne, @JoinTable)
5. Include @Transactional for service methods
6. Add @ControllerAdvice for global exception handling
7. Use Lombok annotations (@Data, @Getter, @Setter) for entities
8. Include proper logging with SLF4J/Logback
9. Follow Spring Boot conventions (package structure, naming)
10. Include build tool configuration (Maven pom.xml or Gradle build.gradle.kts)

Code Quality Requirements for Both Languages:
- Production-ready, not pseudocode
- Proper error handling and validation
- Security best practices
- Comprehensive documentation/comments
- Database integration if applicable
- Configuration management

Return ONLY valid JSON with code strings, no markdown code blocks, no ```java``` or ```python``` markers.""",
)

# ========== Test Generation Templates ==========

GENERATE_TESTS_PROMPT = PromptTemplate(
    input_variables=["plan", "code"],
    template="""Generate comprehensive unit and integration tests for the following API.

API Plan:
{plan}

Generated Code:
{code}

IMPORTANT: Select testing framework based on the code language/framework.

IF LANGUAGE IS PYTHON (FastAPI/Flask/Django):
Generate pytest test code covering:
1. All endpoints
2. Request validation
3. Response validation
4. Error cases
5. Authentication (if implemented)
6. Database operations (if applicable)

Return test code with:
- Setup fixtures (pytest fixtures, database fixtures)
- Test cases for each endpoint
- Parametrized tests where appropriate (pytest.mark.parametrize)
- Mocking with unittest.mock or pytest-mock
- Clear test names and docstrings
- Database transaction rollback for isolated tests

IF LANGUAGE IS JAVA (Spring Boot):
Generate JUnit 5 test code covering:
1. All REST endpoints
2. Request/response validation
3. Error cases and exception handling
4. Spring Security authentication and authorization
5. Service layer business logic
6. Repository/JPA operations
7. Integration tests

Return test code with:
- @SpringBootTest for integration tests
- @WebMvcTest or @WebFluxTest for controller unit tests
- @DataJpaTest for repository tests
- MockMvc for HTTP testing
- @MockBean for mocking dependencies
- Mockito for object mocking
- TestContainers for database testing (optional, if using real database)
- @Transactional for test isolation
- Clear test method names and documentation

Testing Focus for Both Languages:
1. Happy path testing
2. Error case testing
3. Edge case testing
4. Boundary condition testing
5. Integration testing between components

Return ONLY the test code as a string in JSON format with appropriate language/framework specifics.""",
)

GENERATE_DOCS_PROMPT = PromptTemplate(
    input_variables=["plan", "design", "code_summary"],
    template="""Generate comprehensive documentation for the following API.

API Plan:
{plan}

API Design (OpenAPI spec):
{design}

Generated Code Summary:
{code_summary}

Generate documentation in JSON format. Adapt content based on framework/language.

FOR PYTHON APIs:
{{
    "readme": "Complete README.md with Python setup, virtual env, pip install",
    "api_docs": "API documentation with curl examples and Python client examples",
    "setup_instructions": "Python-specific setup: venv, pip install -r requirements.txt, .env config",
    "deployment_guide": "Deployment using Gunicorn, Docker, or cloud platforms"
}}

FOR JAVA/SPRING BOOT APIs:
{{
    "readme": "Complete README.md with Java/Maven/Gradle setup instructions",
    "api_docs": "API documentation with curl examples and Java client (RestTemplate/WebClient) examples",
    "setup_instructions": "Java-specific setup: JDK 21+, Maven/Gradle, application.yml configuration",
    "deployment_guide": "Deployment using Docker, JAR build, cloud platforms (Spring Boot ready)",
    "spring_boot_guide": "Spring Boot specific: actuator endpoints, configuration profiles, logging setup",
    "security_setup": "Spring Security configuration details, JWT token generation and validation",
    "database_migration": "Database schema setup and any Flyway/Liquibase migration scripts"
}}

Include in documentation (adapt for language/framework):
1. API overview and purpose
2. Technology stack and dependencies
3. Installation and setup instructions (language-specific)
4. Building and running (Maven build, Gradle build, or Python venv)
5. Configuration guide (application.yml for Spring Boot, .env for Python)
6. Authentication guide (Spring Security config or Python auth libraries)
7. Example requests and responses for each endpoint (with language-specific clients)
8. Error codes and meanings
9. Rate limiting (if applicable)
10. Pagination details (if applicable)
11. Logging and monitoring setup
12. Deployment instructions
13. Contributing guidelines
14. License information

Special Sections for Java/Spring Boot:
- Spring Boot Actuator endpoints documentation
- How to run tests (mvn test vs gradle test)
- Packaging and running JAR file
- Docker deployment with Spring Boot
- Configuration profiles (dev, prod, test)

Special Sections for Python:
- Virtual environment setup
- Requirements management
- Running with uvicorn (FastAPI) vs development server
- Docker deployment with Python

Return ONLY valid JSON with markdown content in string fields.""",
)
