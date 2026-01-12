# Coverage & CI/CD Testing - Integration Patterns

Coverage measures how much code is tested. CI/CD integration ensures tests run automatically on every commit. Together, they guarantee quality before deployment.

## Coverage Basics

### What is Coverage?

```
Coverage % = (Lines executed by tests / Total lines) × 100

┌─────────────────────────────────┐
│      Coverage Metrics           │
├─────────────────────────────────┤
│ Line Coverage      │ 82%        │
│ Branch Coverage    │ 76%        │
│ Function Coverage  │ 90%        │
└─────────────────────────────────┘

Line: Did tests execute this line?
Branch: Did tests execute both if/else paths?
Function: Did tests call this function?
```

### Coverage Goals by Project Type

```
Unit Tests Only         → 70-80% coverage
Unit + Integration      → 80-90% coverage
Full Stack + E2E        → 90-100% coverage (critical code)
```

---

## pytest-cov Setup

### Installation

```bash
pip install pytest-cov
```

### Basic Coverage Report

```bash
# Run tests with coverage
pytest --cov=src

# Output:
# Name              Stmts   Miss  Cover
# ─────────────────────────────────────
# src/main.py         25      3    88%
# src/models.py       42      4    90%
# src/validators.py   18      2    89%
# ─────────────────────────────────────
# TOTAL              85      9    89%
```

### Coverage Reports

```bash
# Terminal report with missing lines
pytest --cov=src --cov-report=term-missing

# HTML report (browser-friendly)
pytest --cov=src --cov-report=html
# Open htmlcov/index.html

# XML report (for CI/CD)
pytest --cov=src --cov-report=xml

# JSON report
pytest --cov=src --cov-report=json
```

---

## Coverage Configuration

### pyproject.toml Configuration

```toml
[tool.coverage.run]
# What to measure
source = ["src"]
omit = [
    "*/migrations/*",
    "*/tests/*",
    "*/__main__.py",
]

# Branch coverage
branch = true

[tool.coverage.report]
# What to report
precision = 2  # Show 2 decimal places
show_missing = true  # Show missing lines
skip_covered = false  # Include 100% covered files

# Exclude lines from coverage
exclude_lines = [
    "pragma: no cover",  # Explicit marker
    "def __repr__",      # Debug methods
    "if __name__ == .__main__.:",
    "raise AssertionError",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "if 0:",
    "if False:",
]

[tool.coverage.html]
# HTML report directory
directory = "htmlcov"
```

### .coveragerc Configuration (Legacy)

```ini
[run]
source = src
omit = */migrations/*, */tests/*
branch = True

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if __name__ == .__main__.:
    raise AssertionError
    raise NotImplementedError

[html]
directory = htmlcov
```

---

## Minimum Coverage Thresholds

### Enforcing Minimum Coverage

```bash
# Fail if coverage drops below 80%
pytest --cov=src --cov-fail-under=80

# Exit code 1 if threshold not met
echo $?  # Returns 1 if failed
```

### Gradual Coverage Improvement

```bash
# Start with realistic target
pytest --cov=src --cov-fail-under=70  # First pass

# Gradually increase
pytest --cov=src --cov-fail-under=75
pytest --cov=src --cov-fail-under=80
pytest --cov=src --cov-fail-under=85
pytest --cov=src --cov-fail-under=90
```

### Per-Module Coverage

```toml
[tool.coverage.report]
# Require different coverage per module
# Note: Requires custom configuration

# In conftest.py:
def pytest_configure(config):
    # Custom coverage per module
    pass
```

---

## Identifying Coverage Gaps

### Using HTML Reports

```bash
# Generate and open HTML report
pytest --cov=src --cov-report=html
python -m webbrowser htmlcov/index.html
```

**HTML Report Shows:**
- Red: Not covered
- Yellow: Partially covered (branches)
- Green: Fully covered

### Using Term-Missing Report

```bash
pytest --cov=src --cov-report=term-missing

# Output:
# Name                Stmts   Miss  Cover   Missing
# ─────────────────────────────────────────────────
# src/validators.py      30      2    93%   15-16, 28
# src/services.py        45      8    82%   12-15, 34, 56-58

# Lines 15-16 and 28 not covered in validators.py
```

### Analyzing Missing Coverage

```python
# tests/unit/test_validators.py

# Missing coverage in validator.py line 28:
# if email_domain not in whitelist:
#     raise ValueError("Domain not whitelisted")

# Add test to cover it:
def test_email_domain_whitelist_check():
    """Test that non-whitelisted domains are rejected"""
    with pytest.raises(ValueError, match="Domain not whitelisted"):
        validate_email("test@blocked-domain.com")
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml

name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, "3.10", "3.11"]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests with coverage
        run: |
          pytest --cov=src --cov-report=xml --cov-fail-under=80

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          fail_ci_if_error: true
          verbose: true
```

### GitLab CI

```yaml
# .gitlab-ci.yml

test:
  image: python:3.11
  script:
    - pip install -e ".[dev]"
    - pytest --cov=src --cov-report=xml --cov-fail-under=80
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

### Azure Pipelines

```yaml
# azure-pipelines.yml

trigger:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

strategy:
  matrix:
    Python_3_9:
      PYTHON_VERSION: 3.9
    Python_3_10:
      PYTHON_VERSION: 3.10
    Python_3_11:
      PYTHON_VERSION: 3.11

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '$(PYTHON_VERSION)'

  - script: |
      python -m pip install --upgrade pip
      pip install -e ".[dev]"
    displayName: 'Install dependencies'

  - script: |
      pytest --cov=src --cov-report=xml --cov-fail-under=80
    displayName: 'Run tests'

  - task: PublishCodeCoverageResults@1
    inputs:
      codeCoverageTool: Cobertura
      summaryFileLocation: '$(System.DefaultWorkingDirectory)/**/coverage.xml'
```

---

## Coverage Reporting

### Codecov Integration

```bash
# After tests generate coverage.xml
pip install codecov

# Upload to Codecov
codecov -f coverage.xml
```

### Coveralls Integration

```bash
# Install coveralls
pip install coveralls

# Run tests and upload
pytest --cov=src
coveralls
```

### Local Coverage Tracking

```bash
# Generate baseline
pytest --cov=src --cov-report=json

# Store previous coverage
cp .coverage.json .coverage.baseline.json

# After changes, compare
pytest --cov=src --cov-report=json

# Check if coverage improved or degraded
python scripts/check_coverage_trend.py
```

---

## Advanced Coverage Scenarios

### Testing Hard-to-Reach Code Paths

```python
# src/error_handler.py
def handle_critical_error(error):
    """Handle critical system errors"""
    if isinstance(error, DatabaseError):
        log_error(error)
        notify_team("Database down")
        # Very hard to trigger in tests
        raise SystemExit(1)

# tests/integration/test_critical_errors.py
@pytest.mark.integration
def test_critical_database_error_handling(mocker):
    """Test critical error path"""
    # Mock the error
    mocker.patch(
        "src.database.query",
        side_effect=DatabaseError("Connection lost")
    )

    # Mock notification
    mock_notify = mocker.patch("src.error_handler.notify_team")

    with pytest.raises(SystemExit):
        handle_critical_error(DatabaseError("Connection lost"))

    mock_notify.assert_called_with("Database down")
```

### Testing Legacy Code

```python
# For untested legacy code, gradually add coverage

# Step 1: Write integration tests (black-box)
def test_legacy_function_input_output():
    """Test without understanding internals"""
    result = legacy_function(input_data)
    assert result == expected_output

# Step 2: Write unit tests (refactor as you go)
def test_legacy_function_parsing():
    """Test extracted parsing logic"""
    pass

def test_legacy_function_calculation():
    """Test extracted calculation logic"""
    pass

# Step 3: Refactor and improve coverage
# Split into smaller, testable functions
```

### Excluding Code from Coverage

```python
def critical_feature():
    return True

# Exclude specific lines
def error_recovery():  # pragma: no cover
    """This code path is nearly impossible to trigger safely"""
    # Recovery code that risks corrupting data
    pass

# Exclude functions
@skip_coverage  # pragma: no cover
def __repr__(self):
    return f"<{self.__class__.__name__}>"

# Exclude conditional blocks
if settings.DEBUG:  # pragma: no cover
    # Development-only debugging code
    pass
```

---

## Performance & Best Practices

### Fast Coverage Measurement

```bash
# Skip branch coverage for speed
pytest --cov=src --cov-branch

# Parallel testing (faster)
pytest -n auto --cov=src

# Skip slow tests during development
pytest -m "not slow" --cov=src
```

### Coverage in Development

```bash
# Watch mode - rerun on file changes
pytest-watch --cov=src

# Only failed tests
pytest --lf --cov=src

# Coverage with pdb on failure
pytest --cov=src --pdb
```

### Coverage Badges

```markdown
# README.md

## Coverage

[![codecov](https://codecov.io/gh/user/repo/branch/main/graph/badge.svg)](https://codecov.io/gh/user/repo)

Or manually:

![Coverage: 85%](https://img.shields.io/badge/coverage-85%25-brightgreen)
```

---

## Coverage Workflow

### Typical Development Workflow

```
1. Write test
   ↓
2. Run test with coverage
   pytest --cov=src
   ↓
3. See coverage % and missing lines
   ↓
4. Add more tests for missing coverage
   ↓
5. Achieve target coverage (80%+)
   ↓
6. Commit with coverage report
   ↓
7. CI/CD verifies coverage minimum
   ↓
8. Merge to main only if threshold met
```

### Pull Request Checklist

```yaml
# .github/pull_request_template.md

## Coverage

- [ ] No coverage regression (same or higher than main)
- [ ] New code has tests
- [ ] Coverage report reviewed
- [ ] All critical paths tested

## Before Merge

- [ ] All tests passing
- [ ] Coverage ≥ 80%
- [ ] No flaky tests
- [ ] No hardcoded test data
```

---

## Coverage Best Practices

### ✅ Do

- **Measure coverage regularly** (on every commit)
- **Set realistic targets** (80% for most projects)
- **Review missing coverage** (understand why code isn't tested)
- **Test error paths** (exception handling is code too)
- **Use branch coverage** (catch untested conditions)
- **Automate enforcement** (fail CI if threshold not met)
- **Improve gradually** (don't jump from 0% to 100%)

### ❌ Don't

- **Aim for 100% blindly** (some code is untestable)
- **Test implementation details** (test behavior, not internals)
- **Write tests just for coverage** (tests must be meaningful)
- **Ignore failing tests for coverage** (fix broken tests, not metrics)
- **Skip coverage on CI/CD** (automate enforcement)
- **Exclude code without reason** (document why when excluded)
- **Chase coverage at expense of test quality** (quality matters more)

---

## Coverage Checklist

Before deployment:

- [ ] Coverage meets minimum threshold (80%)
- [ ] No coverage regression on this PR
- [ ] Missing coverage reviewed and justified
- [ ] Error paths are tested
- [ ] External dependencies are mocked
- [ ] All markers applied (@pytest.mark.*)
- [ ] Coverage report generated and reviewed
- [ ] CI/CD verification passing
- [ ] No flaky tests in coverage report
- [ ] Documentation updated with coverage status

---

## Summary

Coverage & CI/CD Integration:

- ✅ Automate test execution on every commit
- ✅ Measure code coverage with pytest-cov
- ✅ Enforce minimum coverage thresholds
- ✅ Report coverage to dashboard (Codecov, Coveralls)
- ✅ Prevent regression with automated checks
- ✅ Track coverage trends over time
- ✅ Review missing coverage to identify gaps
- ✅ Update coverage as code evolves
