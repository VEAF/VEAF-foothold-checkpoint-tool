# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Configuration Management (feature/config-management) - IN PROGRESS
  - Pydantic models (ServerConfig, Config) with frozen/immutable design ✅
  - Field validator for non-empty campaign name lists ✅
  - YAML configuration loading from files with error handling ✅
  - Auto-creation of default configuration files ✅
  - Comprehensive test suite with TDD approach (23/23 tests passing, 100% coverage) ✅
- OpenSpec change artifacts for foothold-checkpoint-tool
  - Proposal: Project vision and capabilities
  - Design: Technical architecture and decisions
  - Specifications: 8 detailed capability specs
    - configuration-management
    - campaign-detection
    - checkpoint-storage
    - checkpoint-restoration
    - checkpoint-listing
    - checkpoint-deletion
    - checkpoint-import
    - cli-interface
  - Tasks: 211 implementation tasks across 21 groups
- Development guidelines and auto-memory documentation
- Conversation history and design rationale documentation
- Project setup (feature/project-setup)
  - `pyproject.toml` with Poetry configuration and project metadata
  - Runtime dependencies: typer, rich, pyyaml, pydantic
  - Dev dependencies: pytest, pytest-cov, ruff, black, mypy, types-PyYAML
  - Package structure (src layout): `src/foothold_checkpoint/` and `src/foothold_checkpoint/core/`
  - Test directory structure: `tests/`
  - Type hints marker: `py.typed`
  - Example configuration: `config.yaml.example`
  - Locked dependencies: `poetry.lock`
- Documentation restructuring
  - `README.md`: Generic project overview
  - `USERS.md`: Complete user guide with installation, configuration, and usage
  - `CONTRIBUTING.md`: Developer guide with TDD workflow, coding standards, and Git workflow
