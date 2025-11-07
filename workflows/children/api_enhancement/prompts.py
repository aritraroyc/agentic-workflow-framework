"""
Prompt templates for API Enhancement workflow.

This module contains LangChain PromptTemplate objects for all phases of API enhancement:
- Analysis of enhancement requirements
- Design of enhancements
- Code generation
- Test planning
- Monitoring setup
- Documentation
"""

from langchain_core.prompts import PromptTemplate

# ========== Enhancement Analysis Templates ==========

ANALYZE_ENHANCEMENT_PROMPT = PromptTemplate(
    input_variables=["story_requirements", "api_structure"],
    template="""You are an expert API architect tasked with analyzing enhancement requirements for an existing API.

Based on the following enhancement requirements, create a comprehensive analysis:

Story Requirements:
{story_requirements}

Current API Structure (if available):
{api_structure}

Your analysis should include:
1. List of enhancement requirements with categorization
2. Impact assessment on current architecture
3. Backward compatibility considerations
4. Versioning strategy (semantic, URL-based, header-based)
5. Migration strategy for existing clients
6. Estimated effort for each enhancement
7. Dependencies and prerequisites
8. Framework/language consistency (if Python API, keep Python; if Java API, keep Java/Spring Boot)

Return the response as a valid JSON object with these keys:
{{
    "current_api_summary": "string",
    "current_language": "Python|Java",
    "current_framework": "FastAPI|Flask|Django|Spring Boot",
    "enhancements": [
        {{
            "name": "string",
            "type": "new_endpoint|batch_processing|webhooks|filtering|optimization|monitoring",
            "description": "string",
            "affected_endpoints": ["string"],
            "complexity": "low|medium|high",
            "effort": "string",
            "breaking_change": boolean
        }}
    ],
    "architectural_impact": "string",
    "versioning_approach": "string",
    "backward_compatibility": "string",
    "timeline_estimate": "string",
    "dependencies": ["string"],
    "framework_notes": "If Python API, recommend Python technologies; if Java API, recommend Spring Boot ecosystem"
}}

IMPORTANT: When analyzing enhancements:
- If current API is Python (FastAPI/Flask/Django), recommend Python enhancements using same tech stack
- If current API is Java/Spring Boot, recommend Java/Spring enhancements maintaining consistency
- Consider technology debt and ecosystem consistency in recommendations""",
)

# ========== Enhancement Design Templates ==========

DESIGN_ENHANCEMENT_PROMPT = PromptTemplate(
    input_variables=["enhancement_analysis"],
    template="""You are an expert API designer tasked with designing API enhancements.

Based on the enhancement analysis below, create detailed design specifications:

Enhancement Analysis:
{enhancement_analysis}

Your design should include:
1. Enhanced endpoint specifications (with versioning)
2. New endpoint designs (if applicable)
3. Batch processing API design (if needed)
4. Webhook event types and payloads (if needed)
5. Advanced filtering capabilities
6. Caching strategy
7. Rate limiting updates
8. Error handling enhancements
9. Documentation updates needed
10. Language/Framework-specific considerations

Return the response as a valid JSON object with these keys:
{{
    "versioned_endpoints": {{}},
    "new_endpoints": {{}},
    "batch_processing": {{}},
    "webhooks": {{}},
    "filtering_capabilities": {{}},
    "caching_strategy": {{}},
    "rate_limiting": {{}},
    "error_handling": "string",
    "migration_notes": "string",
    "language_specific": {{
        "if_python": {{
            "additional_dependencies": ["string"],
            "middleware_changes": "string"
        }},
        "if_java_spring_boot": {{
            "additional_starters": ["spring-boot-starter-*"],
            "security_updates": "Spring Security config changes if needed",
            "monitoring_config": "Spring Boot Actuator configuration"
        }}
    }}
}}

IMPORTANT: Keep recommendations consistent with the current API language/framework
- For Python APIs: Recommend Python libraries and frameworks
- For Java/Spring Boot APIs: Recommend Spring Boot starters and Spring ecosystem components""",
)

# ========== Enhancement Code Generation Templates ==========

GENERATE_ENHANCEMENT_CODE_PROMPT = PromptTemplate(
    input_variables=["enhancement_design", "enhancement_analysis"],
    template="""You are an expert backend developer tasked with generating code for API enhancements.

Based on the enhancement design below, generate implementation plan and code structure:

Enhancement Design:
{enhancement_design}

Enhancement Analysis:
{enhancement_analysis}

IMPORTANT: Select code language/framework based on current API technology stack.

IF CURRENT API IS PYTHON (FastAPI/Flask/Django):
{{
    "language": "Python",
    "modified_files": [{{
        "file_path": "path/to/file.py",
        "changes": "description of changes"
    }}],
    "new_files": {{
        "path/to/newfile.py": "complete Python code"
    }},
    "database_migrations": ["SQL migrations if applicable"],
    "configuration_changes": {{}},
    "dependency_updates": ["new Python packages"],
    "implementation_strategy": "step-by-step implementation plan"
}}

IF CURRENT API IS JAVA/SPRING BOOT:
{{
    "language": "Java",
    "modified_files": [{{
        "file_path": "src/main/java/com/example/Controller.java",
        "changes": "description of changes with Spring annotations"
    }}],
    "new_files": {{
        "src/main/java/com/example/NewController.java": "complete Java/Spring Boot code",
        "src/main/java/com/example/NewEntity.java": "JPA entity classes",
        "pom_updates": "additional <dependency> entries for pom.xml"
    }},
    "database_migrations": ["SQL or Flyway migrations"],
    "configuration_changes": {{"application.yml": "Spring Boot config additions"}},
    "dependency_updates": ["Spring Boot starter coordinates"],
    "implementation_strategy": "step-by-step implementation plan with Spring considerations"
}}

Your code generation should include:
1. Modified files and changes needed (language-appropriate)
2. New endpoint implementations
3. Batch processing implementation strategy
4. Webhook service implementation
5. Database migration scripts (if needed)
6. Configuration changes (language/framework-specific)
7. Deployment and rollout plan

Return the response as a valid JSON object with appropriate structure for the detected language.""",
)

# ========== Enhancement Testing Templates ==========

GENERATE_ENHANCEMENT_TESTS_PROMPT = PromptTemplate(
    input_variables=["enhancement_design", "enhancement_analysis"],
    template="""You are an expert QA engineer tasked with planning tests for API enhancements.

Based on the enhancement design and code strategy below, create a comprehensive testing plan:

Enhancement Design:
{enhancement_design}

Enhancement Analysis:
{enhancement_analysis}

IMPORTANT: Select testing framework based on current API language (pytest for Python, JUnit 5 for Java/Spring Boot).

Your testing plan should include:
1. Unit tests for new functionality
2. Integration tests with existing API
3. Backward compatibility tests
4. Performance tests for enhanced features
5. Migration tests
6. Load tests for new features
7. Security tests

FOR PYTHON APIs (pytest):
{{
    "test_strategy": "string with pytest approach",
    "test_categories": {{
        "unit": ["pytest test functions"],
        "integration": ["fixture-based integration tests"],
        "backward_compatibility": ["tests verifying old endpoints still work"],
        "performance": ["performance benchmarks with pytest-benchmark"],
        "migration": ["tests for data migration"],
        "security": ["security-focused tests"]
    }},
    "coverage_targets": {{"statement_percent": 85, "branch_percent": 80}},
    "test_files": {{
        "test_new_endpoints.py": "complete pytest code"
    }},
    "migration_testing": "strategy for testing data migrations"
}}

FOR JAVA/SPRING BOOT APIs (JUnit 5):
{{
    "test_strategy": "string with JUnit 5 and MockMvc approach",
    "test_categories": {{
        "unit": ["@Test methods with mocking"],
        "integration": ["@SpringBootTest integration tests"],
        "backward_compatibility": ["tests verifying old endpoints still work"],
        "performance": ["JMH or Spring Boot performance tests"],
        "migration": ["database migration tests with TestContainers"],
        "security": ["@WithMockUser security tests"]
    }},
    "coverage_targets": {{"statement_percent": 85, "branch_percent": 80}},
    "test_files": {{
        "ControllerTests.java": "complete JUnit 5 test code with MockMvc",
        "ServiceTests.java": "service layer tests with Mockito",
        "RepositoryTests.java": "@DataJpaTest repository tests"
    }},
    "migration_testing": "database migration verification with Flyway/Liquibase"
}}

Return the response as a valid JSON object with appropriate structure for the detected language.""",
)

# ========== Monitoring Setup Templates ==========

SETUP_MONITORING_PROMPT = PromptTemplate(
    input_variables=["enhancement_design", "enhancement_analysis"],
    template="""You are an expert in observability and monitoring tasked with setting up monitoring for API enhancements.

Based on the enhanced API design below, create a comprehensive monitoring setup:

Enhancement Design:
{enhancement_design}

Enhancement Analysis:
{enhancement_analysis}

Your monitoring setup should include:
1. Key metrics to track (latency, throughput, error rates, etc.)
2. Logging enhancements
3. Distributed tracing setup
4. Health check endpoints
5. Alerting rules and thresholds
6. Monitoring dashboard specification
7. Dashboards for operations and business metrics

FOR PYTHON APIs:
{{
    "metrics": {{
        "performance": ["request_latency", "response_time_p99", "throughput", "error_rate"],
        "business": ["active_users", "requests_per_endpoint", "success_rate"],
        "infrastructure": ["cpu_usage", "memory_usage", "disk_usage", "db_connections"]
    }},
    "logging_strategy": "Python logging configuration with structured JSON logs",
    "tracing_setup": {{"type": "OpenTelemetry or Jaeger"}},
    "health_checks": ["/health", "/readiness", "/liveness"],
    "monitoring_tools": ["Prometheus for metrics", "ELK/Datadog for logs"],
    "alerting_rules": []
}}

FOR JAVA/SPRING BOOT APIs:
{{
    "metrics": {{
        "performance": ["http.server.request.duration", "http.server.requests.total", "process.runtime.jvm.memory.usage"],
        "business": ["custom_business_metrics", "API_endpoint_metrics"],
        "infrastructure": ["jvm.memory.used", "jvm.threads.live", "process.cpu.usage", "system.load.average"]
    }},
    "logging_strategy": "SLF4J with Logback configuration, structured JSON output",
    "tracing_setup": {{
        "type": "Spring Cloud Sleuth + Zipkin or Jaeger",
        "spring_boot_actuator": "Enable /actuator/metrics and /actuator/health endpoints"
    }},
    "health_checks": [
        "{{endpoint: '/actuator/health', type: 'liveness'}}",
        "{{endpoint: '/actuator/health/readiness', type: 'readiness'}}",
        "{{endpoint: '/actuator/health/db', type: 'database check'}}"
    ],
    "spring_boot_actuator": {{
        "endpoints_enabled": ["health", "metrics", "prometheus", "env", "loggers"],
        "custom_metrics": "Using @Timed, @Counted, MeterRegistry"
    }},
    "monitoring_tools": ["Prometheus for metrics", "Grafana for dashboards", "ELK/Datadog for logs"],
    "alerting_rules": []
}}

Return the response as a valid JSON object:
{{
    "metrics": {{}},
    "logging_strategy": "string",
    "tracing_setup": {{}},
    "health_checks": ["string"],
    "alerting_rules": [
        {{
            "name": "string",
            "condition": "string",
            "severity": "critical|warning|info"
        }}
    ],
    "dashboards": {{
        "operations": "string",
        "business": "string",
        "infrastructure": "string"
    }},
    "logging_aggregation": "string",
    "tool_specific_configuration": {{
        "if_spring_boot": "Spring Boot Actuator config, Micrometer setup"
    }}
}}""",
)

# ========== Enhancement Documentation Templates ==========

GENERATE_ENHANCEMENT_DOCS_PROMPT = PromptTemplate(
    input_variables=["enhancement_design", "enhancement_analysis"],
    template="""You are a technical writer tasked with documenting API enhancements.

Based on the enhanced API design and implementation below, create comprehensive documentation:

Enhancement Design:
{enhancement_design}

Enhancement Analysis:
{enhancement_analysis}

Your documentation should include:
1. Enhanced API specification
2. Migration guide for existing clients
3. New feature documentation
4. Batch processing API usage
5. Webhook event reference
6. Backward compatibility notes
7. Upgrade instructions
8. Troubleshooting guide
9. Framework-specific deployment and configuration guidance

FOR PYTHON APIs:
{{
    "documentation_sections": {{
        "overview": "Enhancement summary and benefits",
        "migration_guide": "Python-specific migration from old API to enhanced API",
        "new_features": "New endpoint documentation with Python client examples",
        "api_reference": "Updated OpenAPI spec and endpoint details",
        "examples": ["Python requests library examples", "curl examples"],
        "upgrade_instructions": "venv, pip update, .env configuration changes",
        "troubleshooting": "Common Python/FastAPI/Flask issues and solutions",
        "performance_tuning": "Uvicorn configuration, async optimization"
    }}
}}

FOR JAVA/SPRING BOOT APIs:
{{
    "documentation_sections": {{
        "overview": "Enhancement summary and benefits",
        "migration_guide": "Java-specific migration with Spring Boot version compatibility",
        "new_features": "New endpoint documentation with Java client examples (RestTemplate/WebClient)",
        "api_reference": "Updated OpenAPI spec and Spring Boot endpoint annotations",
        "examples": ["Java client code examples", "curl examples", "Spring Boot RestTemplate usage"],
        "upgrade_instructions": "Maven/Gradle build commands, JDK version, Spring Boot version compatibility",
        "configuration_guide": "application.yml configuration changes for new features",
        "spring_security_updates": "Security configuration changes if applicable",
        "monitoring_setup": "Spring Boot Actuator endpoint changes and monitoring setup",
        "troubleshooting": "Common Spring Boot issues, dependency conflicts, configuration problems",
        "deployment_notes": "Docker, Kubernetes, or cloud deployment considerations"
    }}
}}

Return the response as a valid JSON object:
{{
    "documentation_sections": {{}},
    "changelog": "Detailed changelog listing all additions, modifications, and removals",
    "deprecation_notices": ["List of deprecated endpoints/features with timeline"],
    "support_timeline": "When old API versions will no longer be supported",
    "migration_checklist": "Step-by-step checklist for clients upgrading to enhanced API"
}}""",
)
