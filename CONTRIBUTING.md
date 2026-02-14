# Contributing to Foothold Checkpoint Tool

Thank you for considering contributing to the Foothold Checkpoint Tool! This document provides guidelines and instructions for developers.

## Table of Contents

- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Git Workflow](#git-workflow)
- [Pull Request Process](#pull-request-process)
- [Development Guidelines](#development-guidelines)

## Development Environment

### Requirements

- **Python**: 3.10 or higher
- **Poetry**: Dependency management and packaging
- **Git**: Version control
- **Windows**: PowerShell environment
- **VS Code**: Recommended IDE

### Install Poetry

```powershell
# Install Poetry (if not already installed)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

### Clone and Setup

```powershell
# Clone the repository
git clone https://github.com/VEAF/VEAF-foothold-checkpoint-tool.git
cd VEAF-foothold-checkpoint-tool

# Install dependencies with Poetry
poetry install

# Activate the virtual environment
poetry shell

# Verify installation
python -c "import foothold_checkpoint; print(foothold_checkpoint.__version__)"
```

### IDE Setup (VS Code)

Recommended extensions:
- Python (Microsoft)
- Pylance
- Ruff
- Black Formatter
- Python Test Explorer

Configure VS Code to use the Poetry virtualenv:
1. Open Command Palette (`Ctrl+Shift+P`)
2. Select "Python: Select Interpreter"
3. Choose the Poetry virtualenv (usually `foothold-checkpoint-xxx-py3.x`)

### Critical Dependencies

**⚠️ Important: Click Version Constraint**

This project uses **Typer 0.9.x** for the CLI, which has a critical compatibility issue with Click 8.3.x. 

**Required:** Click must be pinned to version **8.1.7** in `pyproject.toml`:

```toml
[tool.poetry.dependencies]
click = "8.1.7"  # DO NOT upgrade to 8.3.x
```

**Issue:** Click 8.3.x introduces a breaking change where `Parameter.make_metavar()` requires a `ctx` argument. This causes a `TypeError` when Typer renders help text with `Annotated` type hints:

```
TypeError: Parameter.make_metavar() missing 1 required positional argument: 'ctx'
```

**Symptoms:**
- `--help` flag crashes with TypeError
- CLI commands fail to display usage information
- Help rendering fails when using `typer.Option()` with `Annotated` syntax

**Resolution:** Keep Click at 8.1.7 until Typer releases a version compatible with Click 8.3.x.

**Testing:** Always verify `--help` works after any dependency updates:
```powershell
poetry run foothold-checkpoint --help
```

## Project Structure

```
VEAF-foothold-checkpoint-tool/
├── src/
│   └── foothold_checkpoint/      # Main package
│       ├── __init__.py            # Package metadata
│       ├── cli.py                 # CLI entry point (Typer)
│       └── core/                  # Business logic
│           ├── __init__.py
│           ├── config.py          # Configuration management (Pydantic)
│           ├── campaign.py        # Campaign detection & normalization
│           ├── checkpoint.py      # Checkpoint metadata
│           └── storage.py         # Save/restore/list/delete/import
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_campaign.py
│   ├── test_checkpoint.py
│   ├── test_storage.py
│   ├── test_cli.py
│   └── data/foothold/             # Test data fixtures
├── openspec/                      # Design artifacts
│   └── changes/foothold-checkpoint-tool/
│       ├── proposal.md
│       ├── design.md
│       ├── specs/
│       └── tasks.md
├── pyproject.toml                 # Poetry config & tool settings
├── poetry.lock                    # Locked dependencies
├── config.yaml.example            # Example configuration
├── README.md                      # Project overview
├── USERS.md                       # User guide
├── CONTRIBUTING.md                # This file
└── CHANGELOG.md                   # Change history (Keep a Changelog)
```

## Coding Standards

### Language and Style

- **Code**: English only (functions, variables, classes, comments, docstrings)
- **Communication**: French with team members
- **Documentation**: English
- **Line length**: 100 characters (Black/Ruff enforced)
- **Type hints**: Mandatory for all public functions
- **Docstrings**: Required for public modules, classes, and functions

### Code Quality Tools

All code must pass these checks before commit:

```powershell
# Format code with Black
poetry run black src/ tests/

# Lint with Ruff
poetry run ruff check src/ tests/

# Type checking with mypy
poetry run mypy src/

# Run all checks together
poetry run black src/ tests/ && poetry run ruff check src/ tests/ && poetry run mypy src/
```

### Pre-commit Checklist

Before committing code:

1. ✅ Format with Black
2. ✅ Lint with Ruff (no errors)
3. ✅ Type check with mypy (no errors)
4. ✅ All tests pass
5. ✅ No VS Code errors/warnings
6. ✅ Update CHANGELOG.md

## Testing

### Test-Driven Development (TDD)

**CRITICAL**: Tests MUST be written BEFORE implementation.

#### TDD Workflow

1. **Write the test** (it should fail)
2. **Implement minimal code** to pass the test
3. **Refactor** if needed
4. **Repeat**

#### Example TDD Cycle

```python
# Step 1: Write failing test
# tests/test_campaign.py
def test_normalize_campaign_name_removes_version():
    """Campaign name normalization should remove version suffixes."""
    from foothold_checkpoint.core.campaign import normalize_campaign_name

    assert normalize_campaign_name("FootHold_CA_v0.2") == "CA"
    assert normalize_campaign_name("Germany_Modern_V0.1") == "Germany_Modern"

# Step 2: Run test (should fail)
# poetry run pytest tests/test_campaign.py::test_normalize_campaign_name_removes_version

# Step 3: Implement
# src/foothold_checkpoint/core/campaign.py
def normalize_campaign_name(filename: str) -> str:
    """Remove version suffixes from campaign filenames."""
    import re
    # Remove _v0.2, _V0.1, _0.1 patterns
    return re.sub(r'_[vV]?\d+\.\d+$', '', filename)

# Step 4: Run test (should pass)
# Step 5: Refactor if needed
```

### Running Tests

```powershell
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_campaign.py

# Run specific test
poetry run pytest tests/test_campaign.py::test_normalize_campaign_name_removes_version

# Run with coverage
poetry run pytest --cov=foothold_checkpoint --cov-report=html

# View coverage report
start htmlcov/index.html
```

### Test Structure

```python
# tests/test_example.py
"""Tests for example module."""

import pytest
from foothold_checkpoint.core.example import ExampleClass


class TestExampleClass:
    """Test suite for ExampleClass."""

    def test_basic_functionality(self):
        """Test basic functionality works as expected."""
        instance = ExampleClass()
        assert instance.method() == expected_value

    def test_error_handling(self):
        """Test that errors are handled correctly."""
        instance = ExampleClass()
        with pytest.raises(ValueError, match="expected error message"):
            instance.method_with_error()

    @pytest.fixture
    def sample_data(self):
        """Fixture providing sample test data."""
        return {"key": "value"}

    def test_with_fixture(self, sample_data):
        """Test using a fixture."""
        assert sample_data["key"] == "value"
```

### Coverage Requirements

- **Core modules**: 100% coverage (`src/foothold_checkpoint/core/`)
- **CLI**: Integration tests for major workflows
- **Overall target**: ≥90%

## Git Workflow

### GitFlow Model

We use the GitFlow branching model:

```
main (production releases)
  └── develop (development branch)
      ├── feature/feature-name (feature branches)
      ├── bugfix/bug-description (bug fixes)
      └── hotfix/critical-fix (urgent production fixes)
```

### Branch Naming

- **Feature branches**: `feature/descriptive-name`
- **Bug fixes**: `bugfix/issue-description`
- **Hotfixes**: `hotfix/critical-issue`

### Workflow Steps

1. **Create feature branch from develop**

```powershell
git checkout develop
git pull origin develop
git checkout -b feature/my-feature
```

2. **Make changes with TDD**
   - Write tests first
   - Implement code
   - Ensure all quality checks pass

3. **Commit with conventional commits**

```powershell
git add .
git commit -m "feat: add campaign detection logic

- Implement file pattern matching
- Add version suffix normalization
- Add tests for all scenarios

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

4. **Push and create Pull Request**

```powershell
git push -u origin feature/my-feature
```

Then create a PR on GitHub targeting `develop`.

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <short description>

<detailed description>

<footer>
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `style:` Code style (formatting, no logic change)
- `refactor:` Code restructuring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

**Example:**

```
feat: add checkpoint import functionality

- Implement directory scanning for campaign files
- Add auto-detection of campaigns from file patterns
- Generate metadata with current timestamp
- Compute SHA-256 checksums for integrity

Closes #42

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

## Pull Request Process

### Before Creating PR

1. ✅ All tests pass: `poetry run pytest`
2. ✅ Code formatted: `poetry run black src/ tests/`
3. ✅ Linting clean: `poetry run ruff check src/ tests/`
4. ✅ Type checks pass: `poetry run mypy src/`
5. ✅ CHANGELOG.md updated
6. ✅ Branch rebased on latest `develop`

### PR Checklist

- [ ] Descriptive title (conventional commit format)
- [ ] Description explains what/why/how
- [ ] Tests included (TDD approach documented)
- [ ] Documentation updated if needed
- [ ] CHANGELOG.md entry added
- [ ] No merge conflicts with `develop`
- [ ] CI checks passing (when available)

### PR Review Process

1. **Automated checks** run (linting, tests, type checking)
2. **Code review** by maintainer(s)
3. **Approval** required before merge
4. **Squash and merge** to develop

## Development Guidelines

### Communication Language

- **Code**: Always English
  - Function names, variables, classes
  - Comments, docstrings
  - Test names and messages

- **Team Communication**: French
  - Pull request discussions
  - Issue comments
  - Team meetings

### Code Documentation

All public APIs must be documented:

```python
def save_checkpoint(
    server: str,
    campaign: str,
    name: str | None = None,
    comment: str | None = None,
) -> Path:
    """Save a checkpoint for the specified campaign.

    Creates a timestamped ZIP archive containing all campaign files,
    Foothold_Ranks.lua, and metadata.json with SHA-256 checksums.

    Args:
        server: Server name from configuration
        campaign: Campaign identifier (normalized)
        name: Optional checkpoint name
        comment: Optional checkpoint description

    Returns:
        Path to the created checkpoint ZIP file

    Raises:
        ServerNotFoundError: If server not in configuration
        CampaignNotFoundError: If campaign files not detected
        CheckpointCreationError: If ZIP creation fails

    Example:
        >>> checkpoint = save_checkpoint(
        ...     server="production-1",
        ...     campaign="afghanistan",
        ...     name="Before Mission 5"
        ... )
        >>> print(checkpoint.name)
        afghanistan_2024-02-13_14-30-00.zip
    """
```

### Error Handling

- Use specific exception types
- Provide helpful error messages
- Include context in error messages

```python
# Good
if server not in config.servers:
    raise ServerNotFoundError(
        f"Server '{server}' not found in configuration. "
        f"Available servers: {', '.join(config.servers.keys())}"
    )

# Bad
if server not in config.servers:
    raise ValueError("Invalid server")
```

### Pydantic Models

Use Pydantic for configuration and data validation:

```python
from pydantic import BaseModel, Field
from pathlib import Path


class ServerConfig(BaseModel):
    """Configuration for a DCS server."""

    path: Path = Field(..., description="Path to server Missions/Saves directory")
    description: str = Field(..., description="Human-readable server description")

    class Config:
        frozen = True  # Immutable after creation
```

### Type Hints

Always use type hints:

```python
# Good
def process_files(files: list[Path], output_dir: Path) -> dict[str, str]:
    """Process files and return checksums."""
    checksums: dict[str, str] = {}
    for file in files:
        checksums[file.name] = compute_checksum(file)
    return checksums

# Bad
def process_files(files, output_dir):
    checksums = {}
    for file in files:
        checksums[file.name] = compute_checksum(file)
    return checksums
```

## Questions or Issues?

- **Questions**: Open a [GitHub Discussion](https://github.com/VEAF/VEAF-foothold-checkpoint-tool/discussions)
- **Bugs**: Open a [GitHub Issue](https://github.com/VEAF/VEAF-foothold-checkpoint-tool/issues)
- **Security**: Email contact@veaf.org

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (TBD).
