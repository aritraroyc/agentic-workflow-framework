"""
LLM prompts for API Enhancement workflow.

These prompts guide the LLM through different phases of API enhancement:
analysis, design, code generation, testing, and monitoring setup.
"""

ANALYZE_ENHANCEMENT_PROMPT = """
You are an expert API architect tasked with analyzing enhancement requirements for an existing API.

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

Return the response as a valid JSON object with these keys:
{{
    "current_api_summary": "string",
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
    "dependencies": ["string"]
}}
"""

DESIGN_ENHANCEMENT_PROMPT = """
You are an expert API designer tasked with designing API enhancements.

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
    "migration_notes": "string"
}}
"""

GENERATE_ENHANCEMENT_CODE_PROMPT = """
You are an expert backend developer tasked with generating code for API enhancements.

Based on the enhancement design below, generate implementation plan and code structure:

Enhancement Design:
{enhancement_design}

Enhancement Analysis:
{enhancement_analysis}

Your code generation should include:
1. Modified files and changes needed
2. New endpoint implementations
3. Batch processing implementation strategy
4. Webhook service implementation
5. Database migration scripts (if needed)
6. Configuration changes
7. Deployment and rollout plan

Return the response as a valid JSON object with these keys:
{{
    "modified_files": ["string"],
    "new_files": ["string"],
    "migration_scripts": ["string"],
    "implementation_strategy": "string",
    "deployment_phases": ["string"],
    "rollback_plan": "string",
    "configuration_changes": {{}},
    "dependency_updates": ["string"]
}}
"""

GENERATE_ENHANCEMENT_TESTS_PROMPT = """
You are an expert QA engineer tasked with planning tests for API enhancements.

Based on the enhancement design and code strategy below, create a comprehensive testing plan:

Enhancement Design:
{enhancement_design}

Enhancement Analysis:
{enhancement_analysis}

Your testing plan should include:
1. Unit tests for new functionality
2. Integration tests with existing API
3. Backward compatibility tests
4. Performance tests for enhanced features
5. Migration tests
6. Load tests for new features
7. Security tests

Return the response as a valid JSON object with these keys:
{{
    "test_strategy": "string",
    "test_categories": {{
        "unit": ["string"],
        "integration": ["string"],
        "backward_compatibility": ["string"],
        "performance": ["string"],
        "migration": ["string"],
        "security": ["string"]
    }},
    "coverage_targets": {{}},
    "test_data_requirements": "string",
    "performance_baselines": {{}}
}}
"""

SETUP_MONITORING_PROMPT = """
You are an expert in observability and monitoring tasked with setting up monitoring for API enhancements.

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

Return the response as a valid JSON object with these keys:
{{
    "metrics": {{
        "performance": ["string"],
        "business": ["string"],
        "infrastructure": ["string"]
    }},
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
    "logging_aggregation": "string"
}}
"""

GENERATE_ENHANCEMENT_DOCS_PROMPT = """
You are a technical writer tasked with documenting API enhancements.

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

Return the response as a valid JSON object with these keys:
{{
    "documentation_sections": {{
        "overview": "string",
        "migration_guide": "string",
        "new_features": "string",
        "api_reference": "string",
        "examples": ["string"],
        "upgrade_instructions": "string",
        "troubleshooting": "string"
    }},
    "changelog": "string",
    "deprecation_notices": ["string"],
    "support_timeline": "string"
}}
"""
