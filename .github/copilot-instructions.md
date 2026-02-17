# GitHub Copilot Instructions - VEAF Foothold Checkpoint Tool

Permanent instructions for GitHub Copilot when working on this project.

## 🎯 Project Objective

CLI tool for managing DCS Foothold campaign checkpoints with integrity verification and cross-server restoration. Also includes a DCSServerBot plugin for Discord.

## 📋 OpenSpec Workflow

**IMPORTANT**: This project uses OpenSpec for structured change management.

- **New feature**: Always use `openspec new change` to start
- **Consult**: `CONTRIBUTING.md`, `openspec/changes/`, and existing specs before modification
- **Artifacts**: Follow workflow proposal → design → specs → tasks → implementation
- **Available skills**: see `.github/skills/` for OpenSpec workflows

## 💻 Code Conventions

### Language and Style

- **Code**: English only (functions, variables, classes, comments, docstrings)
- **Documentation**: English
- **Line length**: 100 characters (Black/Ruff)
- **Type hints**: mandatory for all public functions
- **Docstrings**: required for modules, classes, and public functions

### Code Formatting

```powershell
# Format with ruff format (replaces Black since CI update)
poetry run ruff format .

# Check formatting
poetry run ruff format --check .

# Linting
poetry run ruff check .

# Type checking
poetry run mypy src/
```

**Recommended execution order before commit**:
1. `poetry run ruff format .`
2. `poetry run ruff check .`
3. `poetry run mypy src/`
4. `poetry run pytest`

## 🧪 Tests (TDD MANDATORY)

### Imperative TDD Workflow

**CRITICAL**: Tests MUST be written BEFORE implementation.

1. ✅ **Write the test** (it should fail)
2. ✅ **Implement minimal code** to pass the test
3. ✅ **Refactor** if necessary
4. ✅ **Repeat**

### Import Structure in Tests

**Important convention** (see repository memories):

```python
# tests/test_example.py

# ✅ Standard library and third-party imports at module level
import pytest
from pathlib import Path
from datetime import datetime, timezone

# ❌ DO NOT import project code at module level
# from foothold_checkpoint.core.config import Config  # NO!

class TestExample:
    def test_something(self):
        # ✅ Import project code INSIDE test methods
        from foothold_checkpoint.core.config import Config
        
        config = Config.from_file("config.yaml")
        assert config is not None
```

**Reason**: Established convention for test isolation and managing import side effects.

### Test Coverage

- **Core modules**: 100% coverage (`src/foothold_checkpoint/core/`)
- **CLI**: integration tests for major workflows
- **Overall target**: ≥90%

```powershell
# Run all tests
poetry run pytest

# With coverage
poetry run pytest --cov=foothold_checkpoint --cov-report=html

# View report
start htmlcov/index.html
```

## ⚠️ Critical Technical Constraints

### Click Version 8.1.7 (DO NOT UPGRADE)

**BLOCKING**: Click must remain at 8.1.7 in `pyproject.toml`

```toml
[tool.poetry.dependencies]
click = "8.1.7"  # DO NOT upgrade to 8.3.x
```

**Reason**: Typer 0.9.x incompatible with Click 8.3.x
- Click 8.3.x breaks `Parameter.make_metavar()` (requires `ctx` argument)
- Symptoms: `--help` crashes with TypeError
- Solution: Stay at 8.1.7 until new Typer version

**Mandatory test after dependency updates**:
```powershell
poetry run foothold-checkpoint --help  # must work
```

### Configuration Field Names

**API Convention** (see repository memories):

```python
# ✅ Use real Pydantic field names
Config.checkpoints_dir  # Path
ServerConfig.path       # Path

# ❌ Don't invent names
# config.checkpoints_directory  # Doesn't exist!
# server.mission_directory      # Doesn't exist!
```

**Reference files**:
- `src/foothold_checkpoint/core/config.py` lines 83-132

### Datetime Handling

```python
# ✅ Always use UTC with timezone
from datetime import datetime, timezone

now = datetime.now(timezone.utc)

# ❌ Don't use datetime.now() without timezone
```

### Reading JSON from ZIP

```python
# ✅ Established pattern in codebase
import json
import zipfile

with zipfile.ZipFile(checkpoint_path) as zf:
    metadata = json.loads(zf.read("metadata.json").decode("utf-8"))

# Note: although json.loads() accepts bytes in Python 3.6+,
# the project explicitly uses .decode("utf-8") for clarity
```

## 📁 Established Code Patterns

### File Listing

```python
# ✅ Use glob("*") to list files in a directory
files = list(source_dir.glob("*"))

# Convention established in save_checkpoint (storage.py:104)
```

### Standard Library Imports

```python
# Main modules: imports at module level
# core/checkpoint.py pattern - imports at top
import json
import zipfile
import hashlib
from datetime import datetime, timezone

# Acceptable alternative: imports in functions (storage.py)
# Both styles coexist in the project
```

## 🔄 Git Workflow

### GitFlow Model

```
main (production releases)
  └── develop (development)
      ├── feature/descriptive-name
      ├── bugfix/description
      └── hotfix/critical
```

### Conventional Commits

Format: `<type>: <short description>`

**Types**:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `style:` Code style (formatting)
- `refactor:` Code restructuring
- `test:` Adding/modifying tests
- `chore:` Maintenance tasks

**Example**:
```
feat: add checkpoint import functionality

- Implement directory scanning for campaign files
- Add auto-detection of campaigns from file patterns
- Generate metadata with current timestamp
- Compute SHA-256 checksums for integrity

Closes #42

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Pre-commit Checklist

1. ✅ `poetry run ruff format .`
2. ✅ `poetry run ruff check .`
3. ✅ `poetry run mypy src/`
4. ✅ `poetry run pytest`
5. ✅ Update `CHANGELOG.md`
6. ✅ No conflicts with `develop`

## 📚 Essential Reference Files

### At each new session, consult:

1. **README.md** - Overview, status, quick start
2. **CONTRIBUTING.md** - Complete development conventions
3. **pyproject.toml** - Dependencies, tool configuration
4. **CHANGELOG.md** - Recent changes
5. **openspec/config.yaml** - OpenSpec workflow configuration
6. **config.yaml.example** - Application configuration schema

### Project Structure

```
src/foothold_checkpoint/
├── __init__.py           # Package metadata, version
├── cli.py               # CLI entry point (Typer)
├── py.typed             # PEP 561 marker
└── core/                # Business logic
    ├── config.py        # Configuration (Pydantic)
    ├── campaign.py      # Campaign detection/normalization
    ├── checkpoint.py    # Checkpoint metadata
    └── storage.py       # CRUD operations

tests/                   # Test suite (TDD)
├── test_*.py           # Unit tests
├── conftest.py         # Pytest fixtures
└── data/               # Test fixtures

openspec/               # Design artifacts
├── config.yaml
├── changes/            # Active changes
└── specs/              # Specifications
```

## 🛠️ Quality Tools (CI)

The CI workflow (`.github/workflows/ci.yml`) runs:

```yaml
- ruff check .           # Linting
- ruff format --check .  # Format check
- mypy src              # Type checking
- pytest --cov          # Tests + coverage
```

**Test matrices**:
- OS: Ubuntu, Windows
- Python: 3.10, 3.11, 3.12, 3.13

## 🎨 Error Handling

```python
# ✅ Specific exceptions with helpful messages
from foothold_checkpoint.core.config import ServerNotFoundError

raise ServerNotFoundError(
    f"Server '{server_name}' not found in configuration.\n"
    f"Available servers: {', '.join(available_servers)}"
)

# ✅ Include context in error messages
# ✅ Provide action suggestions to the user
```

## 📝 Function Documentation

**Mandatory template for public functions**:

```python
def function_name(
    arg1: str,
    arg2: int,
    optional_arg: str | None = None,
) -> ReturnType:
    """Short description (one line).

    Detailed description of what the function does,
    including any important behaviors or side effects.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2
        optional_arg: Description of optional argument

    Returns:
        Description of return value

    Raises:
        ExceptionType: When and why this exception is raised

    Example:
        >>> result = function_name("value", 42)
        >>> print(result)
        expected_output
    """
```

## 🔍 Useful Commands

```powershell
# Development
poetry install              # Install dependencies
poetry shell               # Activate virtualenv
poetry run foothold-checkpoint --help

# Quality checks (recommended order)
poetry run ruff format .
poetry run ruff check .
poetry run mypy src/
poetry run pytest

# Specific tests
poetry run pytest tests/test_storage.py
poetry run pytest tests/test_cli.py::test_save_command
poetry run pytest --cov=foothold_checkpoint --cov-report=html

# Build DCSServerBot plugin
poetry run python scripts/build_plugin.py
```

## 🧠 Design Principles

- **Separation of Concerns**: CLI (cli.py) ≠ Business Logic (core/)
- **Configuration as Code**: Pydantic models for validation
- **Type Safety**: Type hints everywhere, mypy in CI
- **Testability**: TDD, fixtures, appropriate mocking
- **User Experience**: Helpful error messages, rich UI (rich library)
- **Integrity**: SHA-256 checksums, verification before restore
- **Automation**: Auto-backup before restore, automatic file renaming

## 🎓 Repository Memories to Preserve

The following facts are validated and should be re-memorized if used:

1. **Import pattern in tests**: Standard lib at top, project code in methods
2. **Config field names**: `checkpoints_dir`, `path` (not `checkpoints_directory`)
3. **Click 8.1.7 pinned**: Typer/Click 8.3.x incompatibility
4. **UTC timezone**: Always `datetime.now(timezone.utc)`
5. **JSON from ZIP**: Explicit `.decode("utf-8")` for clarity
6. **File listing**: `glob("*")` established pattern

## ⚡ Recommended Work Workflow

1. **New feature**:
   - Consult OpenSpec proposal/design/specs if existing
   - Create branch `feature/descriptive-name` from `develop`
   - Write tests first (TDD)
   - Implement minimal code
   - Check quality (ruff, mypy, pytest)
   - Conventional commit
   - PR to `develop`

2. **Bug fix**:
   - Create branch `bugfix/description` from `develop`
   - Write test reproducing the bug (should fail)
   - Fix the bug (test should pass)
   - Check for regressions
   - PR to `develop`

3. **Code review**:
   - Verify TDD applied
   - Verify conventions respected
   - Verify tests pass and coverage maintained
   - Verify documentation updated

---

**Note**: Complete this file with your specific preferences as needed.
