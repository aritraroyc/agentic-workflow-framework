# End-to-End Integration Tests - Manual Testing Guide

## Overview

This document outlines the manual end-to-end testing procedures for the Agentic Workflow Framework. While automated tests cover unit and integration testing, these manual tests verify complete workflows with realistic scenarios.

## Test Environment Setup

```bash
# Ensure all dependencies are installed
pip install -r requirements.txt

# Run the unit tests first
pytest tests/unit/ -v

# Run the integration tests
pytest tests/integration/ -v

# Then proceed with manual E2E testing
```

## Test Scenarios

### Scenario 1: API Development Workflow

**Story File**: `examples/stories/api_development.md`

**Test Steps**:
1. Run: `python main.py examples/stories/api_development.md`
2. Verify output:
   - [ ] Preprocessor output contains extracted data
   - [ ] Planner creates workflow tasks
   - [ ] Coordinator executes api_development workflow
   - [ ] Results saved to `outputs/`
3. Validate outputs:
   - [ ] `outputs/full_state.json` contains complete state
   - [ ] `outputs/execution_log.json` has execution timeline
   - [ ] `outputs/preprocessor_output.json` has preprocessor results
   - [ ] `outputs/planner_output.json` has plan details
   - [ ] `outputs/workflow_results.json` has workflow results

**Expected Result**: ✅ PASS - All workflow phases execute successfully

---

### Scenario 2: UI Development Workflow

**Story File**: `examples/stories/ui_development.md`

**Test Steps**:
1. Run: `python main.py examples/stories/ui_development.md`
2. Verify the framework:
   - [ ] Recognizes UI development story type
   - [ ] Creates appropriate workflow tasks
   - [ ] Generates execution plan
3. Validate results:
   - [ ] Execution completes without errors
   - [ ] All output files are created
   - [ ] Summary shows successful execution

**Expected Result**: ✅ PASS - Framework handles UI dev stories

---

### Scenario 3: API Enhancement Workflow

**Story File**: `examples/stories/api_enhancement.md`

**Test Steps**:
1. Run: `python main.py examples/stories/api_enhancement.md`
2. Verify the framework:
   - [ ] Detects API enhancement story
   - [ ] Creates targeted workflow tasks
   - [ ] Generates appropriate execution strategy
3. Check outputs:
   - [ ] All results saved correctly
   - [ ] No errors in execution
   - [ ] Valid JSON in output files

**Expected Result**: ✅ PASS - Enhancement workflows work correctly

---

### Scenario 4: Complex Multi-Workflow Story

**Story File**: `examples/stories/complex_ecommerce_platform.md`

**Test Steps**:
1. Run: `python main.py examples/stories/complex_ecommerce_platform.md`
2. Verify orchestration:
   - [ ] Framework handles large, complex story
   - [ ] Correctly identifies multiple workflows needed
   - [ ] Creates comprehensive execution plan
   - [ ] Handles dependencies between tasks
3. Validate execution:
   - [ ] Completes without errors
   - [ ] All workflows execute in proper order
   - [ ] Results include all workflow outputs

**Expected Result**: ✅ PASS - Complex multi-workflow scenarios supported

---

### Scenario 5: stdin Input

**Test Steps**:
1. Create a simple story file:
   ```bash
   cat > /tmp/test_story.md << 'EOF'
   # Simple Test Story

   ## Story
   We need a simple API for managing users.

   ## Requirements
   - Create, read, update, delete users
   - JWT authentication
   - Validation with Pydantic

   ## Endpoints
   - POST /users - Create user
   - GET /users/{id} - Get user
   - PUT /users/{id} - Update user
   - DELETE /users/{id} - Delete user
   EOF
   ```

2. Run: `cat /tmp/test_story.md | python main.py`
3. Verify:
   - [ ] Story read from stdin correctly
   - [ ] Workflow executes
   - [ ] Results saved to outputs/

**Expected Result**: ✅ PASS - stdin input works correctly

---

### Scenario 6: Output Directory Creation

**Test Steps**:
1. Create custom output directory:
   ```bash
   python main.py examples/stories/api_development.md --output-dir /tmp/test_outputs
   ```
2. Verify:
   - [ ] Directory `/tmp/test_outputs` is created
   - [ ] All result files saved there
   - [ ] No files in default `outputs/` directory

**Expected Result**: ✅ PASS - Custom output directory works

---

### Scenario 7: Error Handling - Missing Story File

**Test Steps**:
1. Run: `python main.py nonexistent_file.md`
2. Verify:
   - [ ] Error message: "Story file not found"
   - [ ] Exit code: 1
   - [ ] No output files created

**Expected Result**: ✅ PASS - Error handled gracefully

---

### Scenario 8: Error Handling - Empty Story

**Test Steps**:
1. Create empty story: `echo "" > /tmp/empty.md`
2. Run: `python main.py /tmp/empty.md`
3. Verify:
   - [ ] Error message: "Story is empty"
   - [ ] Exit code: 1

**Expected Result**: ✅ PASS - Empty story rejected

---

### Scenario 9: Registry Validation

**Test Steps**:
1. Verify `config/workflows.yaml`:
   ```bash
   grep -A 5 "api_development:" config/workflows.yaml
   ```
2. Run: `python main.py examples/stories/api_development.md`
3. Check logs:
   - [ ] Registry loading message appears
   - [ ] Workflow count logged
   - [ ] api_development workflow registered

**Expected Result**: ✅ PASS - Registry properly loaded and validated

---

### Scenario 10: Parallel vs Sequential Execution

**Test Steps**:
1. Run: `python main.py examples/stories/complex_ecommerce_platform.md`
2. Check execution logs:
   - [ ] Planner determines execution strategy
   - [ ] Tasks grouped by dependency level (if hybrid)
   - [ ] Execution order makes sense

**Expected Result**: ✅ PASS - Execution strategy correctly determined

---

## Performance Tests

### Test P1: Response Time

**Objective**: Verify API response times

**Test Steps**:
1. Run a simple story: `time python main.py examples/stories/api_development.md`
2. Expected: Completes in < 30 seconds

**Result**: _____ seconds

---

### Test P2: Output Size

**Objective**: Verify output file sizes are reasonable

**Test Steps**:
1. Run workflow and check output sizes:
   ```bash
   du -h outputs/*
   ```
2. Expected: Each file < 5MB (typical case)

**Result**: All files within size limits ✅ / ❌

---

## Regression Tests

These tests should be run after code changes:

- [ ] Run all unit tests: `pytest tests/unit/ -v`
- [ ] Run all integration tests: `pytest tests/integration/ -v`
- [ ] Test main.py with api_development story
- [ ] Verify output files are valid JSON
- [ ] Check error handling tests pass

---

## Test Results Summary

| Scenario | Status | Notes |
|----------|--------|-------|
| 1. API Development | ⬜ | |
| 2. UI Development | ⬜ | |
| 3. API Enhancement | ⬜ | |
| 4. Complex Multi-Workflow | ⬜ | |
| 5. stdin Input | ⬜ | |
| 6. Output Directory | ⬜ | |
| 7. Error: Missing File | ⬜ | |
| 8. Error: Empty Story | ⬜ | |
| 9. Registry Validation | ⬜ | |
| 10. Execution Strategy | ⬜ | |

**Legend**: ⬜ = Not Run, ✅ = PASS, ❌ = FAIL

---

## Debugging Commands

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py examples/stories/api_development.md

# Pretty-print output JSON
python -m json.tool outputs/full_state.json | less

# Validate JSON files
python -c "import json; json.load(open('outputs/full_state.json'))" && echo "Valid JSON"

# Check registry configuration
python -c "from workflows.registry.loader import load_registry; r = load_registry(); print(r.list_all())"

# Test individual components
python -m pytest tests/unit/test_api_development.py -v

# Run integration tests only
python -m pytest tests/integration/ -v
```

---

## Known Issues & Workarounds

None documented at this time. Add any found issues here.

---

## Checklist for Release

Before releasing the framework:
- [ ] All 10 scenario tests pass
- [ ] No Python errors or warnings
- [ ] Documentation is up-to-date
- [ ] Example stories are realistic
- [ ] Output formatting is clean
- [ ] Error messages are helpful
- [ ] Registry validation works
- [ ] All tests passing (235+)
