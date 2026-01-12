---
name: pytest-testing
description: |
  Build comprehensive test suites for FastAPI applications using pytest and pytest-asyncio.
  This skill should be used when users want to write unit tests, integration tests, or end-to-end
  tests for FastAPI endpoints, async functions, database operations, and business logic.
  Covers test organization, fixtures, mocking, async testing, and CI/CD integration.
  Always fetches latest pytest and pytest-asyncio documentation before implementation.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch
---

## Before Implementation

Gather context to ensure successful test implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Code structure, existing tests, testing patterns, Python version |
| **Conversation** | What to test (unit/integration/e2e), coverage targets, CI/CD platform |
| **Skill References** | Testing patterns from `references/` (fixtures, mocking, async, coverage) |
| **Fetch Docs** | Use `fetch-library-docs` skill to get latest pytest/pytest-asyncio documentation |

Ensure all required context is gathered before implementing tests.

---

## Skill Triggers & Use Cases

| Trigger | Skill Action |
|---------|--------------|
| "Write tests for this FastAPI endpoint" | Generate unit + integration tests with proper fixtures |
| "Test async functions" | Setup pytest-asyncio with @pytest.mark.asyncio |
| "Mock external API calls" | Generate mocking patterns with unittest.mock or pytest-mock |
| "Set up test fixtures" | Create reusable fixtures for database, auth, HTTP client |
| "Improve test coverage" | Analyze coverage gaps, add tests for edge cases |
| "Organize test suite" | Structure tests into unit/integration/e2e with conftest.py |
| "Debug failing test" | Use pytest introspection, assertions, verbose output |
| "CI/CD integration" | Configure pytest for GitHub Actions, GitLab CI, etc. |

---

## Required Clarifications

Before implementing, ask the user these questions:

### 1. **Test Scope & Type** ❓
   - What are you testing? (endpoint/function/model/integration?)
   - Test types needed: Unit? Integration? End-to-end?
   - **Affects**: Test organization and fixture complexity

### 2. **Async Requirements** ❓
   - Does your code use async/await (FastAPI does)?
   - Do you need to test async functions?
   - External async calls to mock? (databases, APIs)
   - **Affects**: pytest-asyncio configuration and fixture setup

### 3. **Database & Fixtures** ❓
   - Do tests need database access?
   - Use in-memory (SQLite), test containers, or real database?
   - Need test data fixtures? (users, products, etc.)
   - **Affects**: Fixture complexity and database setup

### 4. **Mocking Strategy** ❓
   - External APIs to mock? (email, payment, etc.)
   - Internal functions to patch?
   - Monkeypatch vs unittest.mock vs pytest-mock?
   - **Affects**: Mock configuration patterns

### 5. **Coverage Targets** ❓
   - Target coverage percentage? (80%, 90%, 100%?)
   - Which modules/packages are critical?
   - CI/CD pipeline needs coverage reporting?
   - **Affects**: Test organization and CI configuration

---

## User Input Not Required For

These are inferred or handled flexibly; don't ask unless user mentions them:
- Testing framework (it's pytest—this skill is pytest-specific)
- Assertion style (pytest uses plain assert)
- Test discovery (pytest auto-discovers by convention)
- Parametrization library (pytest has built-in @pytest.mark.parametrize)

---

## Core Workflows

### 1. Unit Test Setup

```
User Request → Identify Code to Test
  ├─ Function/class/method
  ├─ Dependencies/inputs
  ├─ Expected outputs/side effects
  └─ Edge cases/error paths
         ↓
Fetch Official Docs (fetch-library-docs)
  ├─ Assertions and introspection
  ├─ Parametrization techniques
  └─ Fixtures for test isolation
         ↓
Setup Test Structure (see pytest-config.md)
  ├─ Create test file (test_*.py or *_test.py)
  ├─ Import code under test
  ├─ Setup conftest.py if needed
  └─ Configure pytest.ini or pyproject.toml
         ↓
Write Unit Tests (see unit-testing.md)
  ├─ Happy path test
  ├─ Edge case tests
  ├─ Error/exception tests
  ├─ Parametrized tests for variations
  └─ Fixtures for reusable setup
         ↓
Run & Verify
  ├─ pytest test_*.py
  ├─ pytest -v (verbose)
  ├─ pytest --cov (coverage)
  └─ Fix failing tests
```

### 2. Async Testing

```
Identify Async Code
  ├─ async def functions
  ├─ Async database operations
  ├─ Async HTTP calls
  └─ Event loops required
         ↓
Fetch Official Docs (pytest-asyncio)
  └─ @pytest.mark.asyncio patterns
         ↓
Setup Async Testing (see async-testing.md)
  ├─ Install pytest-asyncio
  ├─ Add asyncio_mode in pytest.ini
  ├─ Create async fixtures with @pytest_asyncio.fixture
  └─ Mark tests with @pytest.mark.asyncio
         ↓
Write Async Tests (see async-testing.md)
  ├─ Use await in test functions
  ├─ Test async functions directly
  ├─ Test async context managers
  └─ Test database operations
         ↓
Handle Event Loop
  └─ pytest-asyncio manages automatically
```

### 3. Integration Testing

```
Identify Integration Points
  ├─ Database layer integration
  ├─ External API calls
  ├─ Multiple components together
  └─ End-to-end request flow
         ↓
Setup Integration Fixtures (see fixtures.md)
  ├─ Database fixtures (or in-memory SQLite)
  ├─ HTTP client fixtures (httpx.AsyncClient)
  ├─ Authenticated user fixtures
  └─ Seeded test data
         ↓
Write Integration Tests (see integration-testing.md)
  ├─ Test with real database (or test container)
  ├─ Test HTTP endpoints with TestClient
  ├─ Test with mocked external APIs
  └─ Test request/response flow
         ↓
Database Management
  └─ Rollback after each test (fixture cleanup)
```

### 4. Fixture Setup

```
Identify Fixture Needs
  ├─ Reusable objects (users, tokens, etc.)
  ├─ External service connections
  ├─ Configuration overrides
  └─ Cleanup requirements
         ↓
Fetch Official Docs (pytest fixtures)
  └─ Scope, parametrization, dependency injection
         ↓
Create Fixtures (see fixtures.md)
  ├─ Function-scoped (default, fastest cleanup)
  ├─ Module-scoped (shared across tests)
  ├─ Session-scoped (shared across all tests)
  ├─ Parametrized fixtures (multiple values)
  └─ Composite fixtures (fixtures using other fixtures)
         ↓
Use in Tests
  └─ Pass fixture name as parameter to test function
```

### 5. Mocking & Patching

```
Identify What to Mock
  ├─ External APIs (payment, email, SMS)
  ├─ Internal functions
  ├─ Database calls
  └─ Time/date (freezegun)
         ↓
Fetch Official Docs (unittest.mock)
  └─ Mock, patch, MagicMock patterns
         ↓
Setup Mocks (see mocking.md)
  ├─ unittest.mock.patch decorator
  ├─ pytest-mock fixture
  ├─ monkeypatch fixture
  └─ Mock return values and side effects
         ↓
Write Tests with Mocks (see mocking.md)
  ├─ Mock external service
  ├─ Assert mock was called with correct args
  ├─ Test error handling
  └─ Verify call counts and sequences
```

### 6. Coverage & CI/CD

```
Setup Coverage (see coverage.md)
  ├─ Install pytest-cov
  ├─ Configure .coveragerc
  ├─ Generate coverage reports
  └─ Set minimum coverage threshold
         ↓
Run Coverage Analysis
  ├─ pytest --cov=src --cov-report=html
  ├─ Identify untested code paths
  ├─ Add tests for gaps
  └─ Iteratively improve coverage
         ↓
CI/CD Integration (see coverage.md)
  ├─ GitHub Actions workflow
  ├─ GitLab CI configuration
  ├─ Fail if coverage drops
  └─ Upload coverage reports
         ↓
Pre-deployment Verification
  └─ Ensure all tests pass and coverage meets target
```

---

## Decision Trees

### Test Type Decision

```
What are you testing?
├─ Single function/method → Unit test (see unit-testing.md)
├─ Multiple components working together → Integration test (see integration-testing.md)
└─ Complete request flow through API → End-to-end test (see integration-testing.md)

Is the code async?
├─ YES → Use @pytest.mark.asyncio (see async-testing.md)
└─ NO → Standard pytest pattern
```

### Fixture Scope Decision

```
How often should fixture setup/cleanup run?
├─ Every test → Use function scope (default, fastest)
├─ All tests in module → Use module scope
├─ All tests in session → Use session scope
└─ Different value per test → Use parametrize
```

### Mock vs Real Decision

```
Should test use real or mocked service?
├─ Real database → Use test database or in-memory SQLite
├─ External API → Mock it (prevents flaky tests)
├─ Internal function → Mock for isolation
└─ Time/date → Use freezegun for deterministic tests
```

---

## Key Patterns (Reference in references/)

### Pytest Fundamentals
- **`pytest-config.md`** - pytest.ini, pyproject.toml, conftest.py setup
- **`pytest-basics.md`** - Plain assertions, test discovery, parametrization

### Async Testing
- **`async-testing.md`** - pytest-asyncio, @pytest.mark.asyncio, async fixtures, event loops

### Test Organization
- **`unit-testing.md`** - Unit test patterns, isolation, edge cases
- **`integration-testing.md`** - Integration tests, fixtures, database, end-to-end
- **`fixtures.md`** - Fixture creation, scoping, parametrization, composition

### Advanced Patterns
- **`mocking.md`** - Mock, patch, unittest.mock, pytest-mock, monkeypatch
- **`coverage.md`** - pytest-cov, coverage reports, CI/CD integration
- **`best-practices.md`** - Test organization, naming, clarity, maintenance

### FastAPI-Specific
- **`fastapi-testing.md`** - TestClient, httpx.AsyncClient, endpoint testing, auth mocking

---

## Error Handling in Skill

When implementing tests:
- ✅ Fetch official docs BEFORE writing tests
- ✅ Use established patterns from `references/`
- ✅ Test both happy path and error cases
- ✅ Use fixtures to avoid test interdependencies
- ✅ Mock external services to avoid flaky tests

When uncertain:
- Use `fetch-library-docs` to get latest pytest patterns
- Check `references/pytest-basics.md` for common patterns
- Ask user for specific context (code, requirements)

---

## What This Skill Does

✅ Create unit tests for functions and classes
✅ Create integration tests for endpoints and workflows
✅ Setup async testing with pytest-asyncio
✅ Create and organize fixtures
✅ Setup mocking and patching patterns
✅ Configure coverage reporting
✅ Integrate with CI/CD pipelines
✅ Debug failing tests with pytest introspection
✅ Organize tests into clear, maintainable structure
✅ Parametrize tests for multiple scenarios

## What This Skill Does NOT Do

❌ Run tests in production (tests are development-only)
❌ Replace manual QA testing (units tests are specific)
❌ Modify source code (only creates tests)
❌ Deploy test infrastructure (CI/CD setup only)
❌ Generate test data endlessly (uses focused fixtures)
