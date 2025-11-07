# Implementation Notes - Critical Patterns & Known Issues

**Last Updated**: 2025-11-06
**Status**: Ready for Use
**Critical Issues**: 1 (identified but requires further action)

---

## Overview

This document captures critical implementation patterns and known issues discovered during recent development. Use this as a reference when implementing new features or fixing bugs.

---

## Critical Patterns

### 1. LLM Client Invocation (MUST FOLLOW)

**Pattern**: Use `asyncio.to_thread()` with message dict format

```python
import asyncio

# ✅ CORRECT
response = await asyncio.to_thread(
    self.llm_client.invoke,
    [
        {"role": "system", "content": "You are an expert..."},
        {"role": "user", "content": prompt_text},
    ]
)

# Extract response
text = response.content if hasattr(response, 'content') else str(response)
```

**Why This Pattern?**
1. **Synchronous Client**: The LLM client (`ChatAnthropic`, `ChatOpenAI`) is synchronous
2. **No ainvoke() Method**: These clients don't have an `ainvoke()` method
3. **Message Format Required**: LLM clients expect list of message dicts with roles
4. **Thread Pool Safety**: `asyncio.to_thread()` safely runs sync code in async context

**Common Errors**:
- ❌ `await self.llm_client.ainvoke(prompt)` → AttributeError: no ainvoke
- ❌ `await asyncio.to_thread(self.llm_client.invoke, "plain string")` → Empty responses
- ❌ Mixing response formats → JSON parsing failures

---

### 2. State Field Naming (MUST USE CORRECT NAMES)

**Parent Workflow State**:
```python
# ✅ CORRECT field name
state = {
    "input_story": "# API Development\n...",  # NOT "story"!
    "story_requirements": {},
    "story_type": "api_development",
    "preprocessor_output": {...},
    "planner_output": {...},
    "registry": registry,  # For child workflow invocation
    ...
}
```

**Why?**
- Original implementation used "story" field
- Refactored to "input_story" for clarity
- Child workflows all expect "input_story" field
- Registry field enables workflow invocation

**Common Errors**:
- ❌ Using `"story"` field → Validation failures in child workflows
- ❌ Missing `"registry"` field → Cannot invoke child workflows
- ❌ Missing child workflow required fields

---

### 3. Child Workflow Response Format (MUST MATCH)

**Standard Response Format** (all child workflows must return):

```python
{
    "status": str,  # "success", "failure", "partial"
    "output": {
        # Workflow-specific outputs
        "phase1_result": {...},
        "phase2_result": {...},
        ...
    },
    "artifacts": list,  # Generated files/code
    "execution_time_seconds": float,  # REQUIRED
    "errors": list,  # Optional
}
```

**Why This Format?**
- Coordinator expects this structure for aggregation
- Execution time is used for metrics and logging
- Artifacts list enables result collection
- Consistent format across all workflows

**Common Errors**:
- ❌ Missing `execution_time_seconds` → Coordinator validation fails
- ❌ Missing `artifacts` list → Results not collected
- ❌ Inconsistent status values → Aggregation errors

---

### 4. Message Dict Structure (CRITICAL FOR LLM)

```python
# ✅ CORRECT structure
message_list = [
    {
        "role": "system",
        "content": "You are an expert API architect..."
    },
    {
        "role": "user",
        "content": prompt_text
    }
]

# Use with asyncio.to_thread
response = await asyncio.to_thread(
    self.llm_client.invoke,
    message_list
)
```

**Roles**:
- `"system"`: Sets the assistant's behavior and expertise
- `"user"`: The actual prompt/request
- `"assistant"`: Previous AI responses (rarely used in single-turn)

**Why This Matters?**
- LLM client expects this specific format
- Other formats result in empty responses
- Causes "Expecting value" JSON parsing errors

---

## Known Issues & Workarounds

### Issue 1: Empty JSON Responses from LLM

**Symptom**:
```
Failed to parse design JSON: Expecting value: line 1 column 1 (char 0)
```

**Root Cause**:
- LLM receiving plain string instead of message dict
- Or LLM receiving async instead of sync invocation

**Workaround**:
```python
# ✅ Always wrap with asyncio.to_thread + message dict
response = await asyncio.to_thread(
    self.llm_client.invoke,
    [
        {"role": "system", "content": "..."},
        {"role": "user", "content": prompt},
    ]
)
```

**Verification**:
```bash
# Check if response is valid
if not response or not response.content:
    print("LLM returned empty response")
    # Fallback logic here
```

---

### Issue 2: Child Workflow Validation Failures

**Symptom**:
```
Child workflow validation failed: input_story not in state
```

**Root Cause**:
- Parent state not properly passed to child workflow
- Child workflow checking for wrong field names
- Missing preprocessor_output field

**Workaround**:
```python
# ✅ Ensure parent state has required fields
if "input_story" not in state:
    return {"status": "failure", "output": {}, "artifacts": []}

if "preprocessor_output" not in state:
    return {"status": "failure", "output": {}, "artifacts": []}
```

---

### Issue 3: Registry Not Available to Coordinator

**Symptom**:
```
No registry available for api_development, using simulated execution
```

**Root Cause**:
- Registry not passed through state to coordinator
- Coordinator can't invoke actual workflows

**Workaround**:
```python
# ✅ Ensure registry is in state before coordinator
state = {
    "input_story": "...",
    ...
    "registry": registry,  # MUST be present
}

# In coordinator, check registry availability
registry = state.get("registry")
if registry:
    # Actually invoke workflows
    result = await invoker.invoke(workflow_name, state, registry)
else:
    # Fall back to simulation
    result = simulate_workflow(workflow_name)
```

---

### Issue 4: Story Type Misclassification

**Symptom**:
```
UI story routed to API development workflow
```

**Root Cause**:
- Substring matching causing false positives
- Binary detection instead of scoring
- Keyword "add" matching in "addressing" (UI) story

**Solution** (already implemented):
```python
# ✅ Use word boundary regex with keyword counting
import re

def _detect_story_type(story: str) -> str:
    # Count keywords with word boundaries
    api_keywords = [r'\bapi\b', r'\brest\b', r'\bend\s*point\b']
    ui_keywords = [r'\bui\b', r'\bdashboard\b', r'\breact\b']

    api_count = sum(1 for kw in api_keywords if re.search(kw, story.lower()))
    ui_count = sum(1 for kw in ui_keywords if re.search(kw, story.lower()))

    if ui_count > api_count:
        return "ui_development"
    elif api_count > ui_count:
        return "api_development"
    else:
        return "api_development"  # Default
```

---

## Testing Patterns

### Test Pattern: LLM Mock Handling

```python
import asyncio
from unittest.mock import MagicMock  # Use MagicMock, NOT AsyncMock

# ✅ CORRECT: Mock for asyncio.to_thread usage
with patch.object(agent, "llm_client") as mock_llm:
    # Use MagicMock for sync invocations
    mock_llm.invoke = MagicMock(
        return_value=MagicMock(content='{"valid": "json"}')
    )

    # This works because asyncio.to_thread handles the sync call
    result = await agent.plan_something()
```

**Why Not AsyncMock?**
- `asyncio.to_thread()` expects synchronous functions
- AsyncMock returns an awaitable, causing type mismatches
- MagicMock provides sync behavior that asyncio.to_thread expects

---

### Test Pattern: Fallback Generation

```python
# ✅ CORRECT: Test fallback when LLM fails
with patch.object(agent, "llm_client") as mock_llm:
    # Simulate LLM failure
    mock_llm.invoke = MagicMock(
        side_effect=Exception("LLM unavailable")
    )

    result = await agent.plan_something()

    # Verify fallback was generated
    assert result["plan"] is not None
    assert "project_name" in result["plan"]
```

---

## Performance Considerations

### 1. LLM Call Timeout

```python
# ✅ Add timeouts for LLM calls
try:
    response = await asyncio.wait_for(
        asyncio.to_thread(
            self.llm_client.invoke,
            [
                {"role": "system", "content": "..."},
                {"role": "user", "content": prompt},
            ]
        ),
        timeout=30.0  # 30 seconds
    )
except asyncio.TimeoutError:
    # Fallback to cached/default response
    response = self._generate_fallback_response()
```

---

### 2. Registry Caching

```python
# ✅ Registry is loaded once and cached
registry = load_registry()  # Loaded once at startup

# Reuse registry for all invocations
for workflow_name in workflow_list:
    metadata = registry.get(workflow_name)
```

---

### 3. Workflow Instance Caching

```python
# ✅ Workflow instances cached to avoid repeated instantiation
class WorkflowInvoker:
    def __init__(self):
        self._workflow_cache = {}

    async def invoke(self, workflow_name, state):
        # Load once, reuse
        if workflow_name not in self._workflow_cache:
            workflow = self._load_workflow(workflow_name)
            self._workflow_cache[workflow_name] = workflow

        workflow = self._workflow_cache[workflow_name]
        return await workflow.execute(state)
```

---

## Debugging Tips

### Enable Verbose Logging

```bash
# Run with debug logging
LOG_LEVEL=DEBUG python main.py examples/stories/api_development.md
```

### Check LLM Client Configuration

```python
from core.llm import get_default_llm_client

client = get_default_llm_client()
print(f"LLM Client Type: {type(client)}")
print(f"LLM Model: {client.model_name}")
print(f"Has invoke: {hasattr(client, 'invoke')}")
print(f"Has ainvoke: {hasattr(client, 'ainvoke')}")
```

### Verify Message Dict Format

```python
# Test LLM with message dict
response = client.invoke([
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hello"}
])

print(f"Response type: {type(response)}")
print(f"Response content: {response.content if hasattr(response, 'content') else response}")
```

---

## Refactoring Notes

### Recent Changes (Phase 8-9)

1. **LLM Invocation Pattern**
   - Changed from hypothetical `ainvoke()` to `asyncio.to_thread()` wrapper
   - Updated all execution planners and workflow nodes
   - Updated test mocks from AsyncMock to MagicMock

2. **State Field Naming**
   - Changed `"story"` to `"input_story"` throughout
   - Updated preprocessor, planner, coordinator
   - Updated all state validation

3. **Child Workflow Standardization**
   - All child workflows (ui_development, api_enhancement, ui_enhancement) updated
   - Consistent response format across all workflows
   - Proper parent state extraction and field validation

4. **Test Count**
   - From 314 to 315 tests
   - Added E2E tests for comprehensive coverage

---

## Future Improvements

1. **Type Checking**: Add mypy for better type safety
2. **Message Format Validation**: Validate message format before sending to LLM
3. **Response Caching**: Cache LLM responses for identical prompts
4. **Rate Limiting**: Implement rate limiting for LLM API calls
5. **Monitoring**: Add OpenTelemetry instrumentation for execution tracing

---

## Related Documentation

- [Architecture Documentation](docs/architecture.md) - System design
- [Configuration Guide](docs/configuration.md) - Workflow configuration
- [API Reference](docs/api_reference.md) - API endpoints and schemas
- [Documentation Audit](DOCUMENTATION_AUDIT.md) - Issues identified and fixed
- [Documentation Changes](DOCUMENTATION_CHANGES.md) - Detailed changelog

---

## Contributing Guidelines

When implementing new features or workflows:

1. **Always use asyncio.to_thread + message dict** for LLM calls
2. **Always pass registry through state** for workflow invocation
3. **Always return standard response format** with status, output, artifacts, execution_time
4. **Always use input_story field** not "story"
5. **Always add tests** using MagicMock for LLM mocking
6. **Always document patterns** in relevant doc files

---

**Version**: 1.0
**Last Updated**: 2025-11-06
**Maintainer**: Framework Team
