# pytest-testing Skill - Navigation & Index

Welcome to the comprehensive pytest-testing skill for FastAPI applications. This skill provides everything you need to build production-grade test suites from basic to advanced patterns.

## Quick Start

**Are you new to pytest?** Start here:
1. Read `SKILL.md` (overview and workflows)
2. Check `pytest-config.md` (setup instructions)
3. Look at `fixtures.md` (reusable test patterns)
4. Follow the examples in `unit-testing.md`

**Are you testing async FastAPI code?** Go here:
1. `async-testing.md` (pytest-asyncio setup)
2. `fastapi-testing.md` (endpoint testing)
3. `integration-testing.md` (complete workflows)

**Do you need to mock or test complex scenarios?** Check:
1. `mocking.md` (mocking external services)
2. `coverage.md` (measuring code coverage)
3. `best-practices.md` (professional patterns)

---

## Complete Reference Guide

### Foundational References

| Reference | Purpose | Time | Key Topics |
|-----------|---------|------|------------|
| **[pytest-config.md](pytest-config.md)** | Setup pytest and conftest | 15 min | `pyproject.toml`, `conftest.py`, markers, CLI options |
| **[fixtures.md](fixtures.md)** | Create reusable test setup | 20 min | Scopes, dependencies, parametrization, examples |
| **[unit-testing.md](unit-testing.md)** | Test functions and classes | 25 min | Happy path, edge cases, errors, assertions |

### Testing Patterns

| Reference | Purpose | Time | Key Topics |
|-----------|---------|------|------------|
| **[async-testing.md](async-testing.md)** | Test async/await code | 20 min | `@pytest.mark.asyncio`, async fixtures, event loops |
| **[integration-testing.md](integration-testing.md)** | Test components together | 25 min | Database, endpoints, workflows, authentication |
| **[fastapi-testing.md](fastapi-testing.md)** | FastAPI-specific patterns | 20 min | Endpoints, validation, auth, dependencies |

### Advanced Topics

| Reference | Purpose | Time | Key Topics |
|-----------|---------|------|------------|
| **[mocking.md](mocking.md)** | Mock external dependencies | 20 min | `unittest.mock`, `pytest-mock`, async mocks |
| **[coverage.md](coverage.md)** | Measure and enforce coverage | 20 min | `pytest-cov`, CI/CD, GitHub Actions |
| **[best-practices.md](best-practices.md)** | Professional test organization | 15 min | Structure, naming, patterns, quality checks |

---

## Learning Paths

### Path 1: Hello World to Unit Tests (30 min)

```
1. pytest-config.md (5 min)
   └─ Install pytest, configure pyproject.toml

2. unit-testing.md (20 min)
   └─ Write first unit test
   └─ Test happy path
   └─ Test error cases

3. fixtures.md (5 min)
   └─ Extract common setup to fixture
```

**Outcome**: Write unit tests for business logic functions

---

### Path 2: Testing FastAPI Endpoints (45 min)

```
1. pytest-config.md (5 min)
   └─ Setup pytest for FastAPI project

2. fastapi-testing.md (20 min)
   └─ Test GET/POST/PUT/DELETE endpoints
   └─ Test validation errors
   └─ Test authentication

3. async-testing.md (15 min)
   └─ Use AsyncClient
   └─ Mark tests with @pytest.mark.asyncio

4. integration-testing.md (5 min)
   └─ Test complete workflows
```

**Outcome**: Test all FastAPI endpoints with proper setup

---

### Path 3: Production Test Suite (90 min)

```
1. Complete Paths 1 & 2 (45 min)

2. mocking.md (20 min)
   └─ Mock external APIs
   └─ Mock email, payment services
   └─ Mock time with freezegun

3. coverage.md (15 min)
   └─ Measure coverage with pytest-cov
   └─ Set minimum thresholds
   └─ Setup CI/CD reporting

4. best-practices.md (10 min)
   └─ Organize tests professionally
   └─ Follow naming conventions
   └─ Avoid common pitfalls
```

**Outcome**: Production-grade test suite with 80%+ coverage

---

## Topic-Based Navigation

### By Testing Scope

#### Unit Testing (Isolated)
- **Start**: `unit-testing.md`
- **Setup**: `pytest-config.md`
- **Reuse**: `fixtures.md`
- **Isolate**: `mocking.md`

#### Integration Testing (With Services)
- **Start**: `integration-testing.md`
- **Endpoints**: `fastapi-testing.md`
- **Mock**: `mocking.md`
- **Measure**: `coverage.md`

#### End-to-End Testing (Complete Flows)
- **Plan**: `integration-testing.md` (workflows section)
- **Build**: `fastapi-testing.md`
- **Debug**: `best-practices.md`

### By Technology

#### FastAPI
1. `pytest-config.md` - Setup pytest for FastAPI
2. `fastapi-testing.md` - Endpoint testing patterns
3. `async-testing.md` - Async handler testing

#### Async Code
1. `async-testing.md` - Complete async guide
2. `fastapi-testing.md` - Async endpoints
3. `integration-testing.md` - Async workflows

#### Databases
1. `fixtures.md` - Database fixtures
2. `integration-testing.md` - Database operations
3. `pytest-config.md` - conftest.py setup

#### External Services
1. `mocking.md` - Mocking APIs and services
2. `integration-testing.md` - Mocking pattern examples
3. `coverage.md` - Testing with mocks

#### Validation & Errors
1. `unit-testing.md` - Error case testing
2. `fastapi-testing.md` - Response validation
3. `integration-testing.md` - Error workflows

### By Problem Type

#### "How do I set up pytest?"
→ `pytest-config.md`

#### "How do I test my async function?"
→ `async-testing.md`

#### "How do I test my FastAPI endpoint?"
→ `fastapi-testing.md`

#### "How do I test endpoints with database?"
→ `integration-testing.md` + `fixtures.md`

#### "How do I test endpoints with authentication?"
→ `fastapi-testing.md` (authentication section)

#### "How do I mock an external API?"
→ `mocking.md`

#### "How do I measure code coverage?"
→ `coverage.md`

#### "How do I organize my tests professionally?"
→ `best-practices.md`

#### "How do I test background tasks?"
→ `fastapi-testing.md` (background tasks section)

#### "How do I test WebSockets?"
→ `fastapi-testing.md` (WebSocket section)

---

## Common Scenarios

### Scenario 1: Testing CRUD Operations

```
1. fixtures.md
   └─ Create test_database fixture
   └─ Create test_user fixture

2. integration-testing.md
   └─ Test create endpoint (POST)
   └─ Test read endpoint (GET)
   └─ Test update endpoint (PUT)
   └─ Test delete endpoint (DELETE)

3. fastapi-testing.md
   └─ Test validation errors
   └─ Test not found errors
```

### Scenario 2: Testing Authentication Flow

```
1. fixtures.md
   └─ Create test_user fixture
   └─ Create auth_headers fixture

2. fastapi-testing.md
   └─ Test login endpoint
   └─ Test protected endpoints
   └─ Test permission checks

3. integration-testing.md
   └─ Test complete auth workflow
```

### Scenario 3: Testing with External Services

```
1. mocking.md
   └─ Mock email service
   └─ Mock payment API

2. integration-testing.md
   └─ Test endpoint that calls external service
   └─ Verify mock was called

3. coverage.md
   └─ Measure coverage of error handling
```

### Scenario 4: Setting Up CI/CD

```
1. pytest-config.md
   └─ Ensure pytest is configured

2. coverage.md
   └─ Setup pytest-cov
   └─ Configure GitHub Actions

3. best-practices.md
   └─ Organize tests for CI/CD
```

---

## Reference Files at a Glance

### pytest-config.md (270 lines)
Modern pytest configuration using `pyproject.toml`, conftest.py structure for async testing, HTTP clients, fixtures, and CI/CD setup.

### async-testing.md (350 lines)
Complete pytest-asyncio guide covering async test functions, async fixtures, event loop management, common patterns, FastAPI helpers, and error solutions.

### fixtures.md (400 lines)
Comprehensive fixture guide with scopes, dependencies, parametrization, database and authentication examples, mock data, and FastAPI TestClient patterns.

### unit-testing.md (420 lines)
Unit test patterns: anatomy, happy path, edge cases, error testing, parametrization, isolation, mocking, assertions, and professional practices.

### integration-testing.md (450 lines)
Integration patterns: database testing, endpoint testing, authentication, error responses, complete workflows, external service mocking.

### mocking.md (480 lines)
Mocking patterns: unittest.mock, pytest-mock, monkeypatch, async mocks, freezegun, side effects, best practices, and common patterns.

### coverage.md (380 lines)
Coverage measurement and CI/CD integration: pytest-cov, minimum thresholds, GitHub Actions, Codecov/Coveralls, tracking trends.

### best-practices.md (420 lines)
Professional test organization: structure, naming, AAA pattern, fixtures, markers, error handling, avoiding pitfalls, quality checklist.

### fastapi-testing.md (400 lines)
FastAPI-specific testing: endpoint testing, validation, authentication, authorization, dependencies, error handling, middleware, WebSockets.

---

## Code Examples by Topic

### Creating a Simple Test
**File**: `unit-testing.md` → "Simple Function Test"

### Testing Database Operations
**File**: `integration-testing.md` → "Testing with Real Test Database"

### Mocking External APIs
**File**: `mocking.md` → "Mocking External API"

### Testing FastAPI Endpoints
**File**: `fastapi-testing.md` → "Testing GET Endpoints"

### Setting Up Authentication
**File**: `fastapi-testing.md` → "Testing Protected Endpoints"

### Measuring Coverage
**File**: `coverage.md` → "Basic Coverage Report"

### GitHub Actions Integration
**File**: `coverage.md` → "GitHub Actions"

---

## Skill Usage Overview

### When to Use This Skill

Use `pytest-testing` skill when you need to:
- Write unit tests for FastAPI applications
- Build integration tests with database and services
- Create end-to-end test suites
- Setup pytest configuration
- Measure code coverage
- Mock external dependencies
- Test async/await code
- Integrate tests into CI/CD

### What This Skill Provides

- **Complete references** for 9 major testing domains
- **Real code examples** for every pattern
- **Best practices** from production experience
- **Professional patterns** for enterprise testing
- **Official documentation** links for all libraries
- **From hello-world to production** patterns

### What This Skill Does NOT Cover

- Testing other frameworks (Django, Flask, etc.)
- Load/performance testing
- Manual QA processes
- Test automation infrastructure
- Selenium/Playwright UI testing
- Mobile app testing

---

## Quick Reference Checklists

### Before Writing Tests
- [ ] Read `pytest-config.md` (setup)
- [ ] Review `fixtures.md` (understand fixtures)
- [ ] Pick learning path above

### Before Running Tests
- [ ] Reviewed relevant reference file
- [ ] Tests follow AAA pattern (arrange-act-assert)
- [ ] Tests are isolated (no dependencies)
- [ ] External services are mocked

### Before Committing Tests
- [ ] All tests pass (`pytest`)
- [ ] Coverage meets target (`pytest --cov`)
- [ ] No flaky tests (run multiple times)
- [ ] Professional naming and organization
- [ ] Docstrings explain test purpose

### Before Deploying
- [ ] All tests passing in CI/CD
- [ ] Coverage meets minimum threshold
- [ ] No warning or error logs
- [ ] Code review approved

---

## File Organization

```
pytest-testing/
├── SKILL.md                           # Main skill definition
├── INDEX.md (this file)               # Navigation guide
└── references/
    ├── pytest-config.md               # Setup & configuration
    ├── async-testing.md               # Async/await patterns
    ├── fixtures.md                    # Fixture patterns
    ├── unit-testing.md                # Unit test patterns
    ├── integration-testing.md         # Integration patterns
    ├── mocking.md                     # Mocking patterns
    ├── coverage.md                    # Coverage & CI/CD
    ├── best-practices.md              # Professional practices
    └── fastapi-testing.md             # FastAPI-specific
```

---

## Estimated Reading Time

| Task | Files | Time |
|------|-------|------|
| Complete Beginner | SKILL.md + pytest-config.md + unit-testing.md | 1 hour |
| FastAPI Tester | All except mocking.md | 2-3 hours |
| Production Suite | All files | 4-5 hours |
| Reference Lookup | Specific file | 5-15 min |

---

## Support & Resources

### Official Documentation
- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio docs](https://pytest-asyncio.readthedocs.io/)
- [FastAPI testing guide](https://fastapi.tiangolo.com/advanced/testing/)

### Key Libraries
- **pytest** - Core testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage measurement
- **unittest.mock** - Mocking (standard library)
- **pytest-mock** - pytest mocking fixture

---

## Tips for Success

1. **Start with one reference** - Don't try to read everything at once
2. **Follow the learning paths** - They're designed in order of complexity
3. **Run examples** - Copy code examples and modify them for your code
4. **Read error messages** - pytest errors are very helpful and clear
5. **Use markers** - Organize tests with `@pytest.mark.*`
6. **Keep tests simple** - One behavior per test is better than many assertions
7. **Use fixtures** - Extract common setup to fixtures for DRY tests
8. **Mock carefully** - Only mock external dependencies, not code under test
9. **Measure coverage** - Use pytest-cov to find untested code
10. **Iterate** - Tests evolve as your code evolves

---

## Cross-Skill Integration

### Testing SQLModel Databases
For testing async SQLModel database layers with FastAPI, see the **async-sqlmodel skill** documentation and the dedicated `fastapi-sqlmodel-testing.md` reference which covers test database setup, async fixtures, relationship eager loading tests, and endpoint integration with database dependencies.

### FastAPI Routing & Endpoints
For API design, authentication, and routing patterns, see the **fastapi-builder skill** documentation.

---

## Version Information

- **Tested with**: Python 3.9+, FastAPI 0.100+, pytest 7.0+, pytest-asyncio 0.21+
- **Last Updated**: 2026-01-12
- **Status**: Production-ready

---

**Ready to start testing?** Pick your learning path above and dive in!
