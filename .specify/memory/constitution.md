<!--
Sync Impact Report:
- Version change: 0.0.0 -> 1.0.0
- Modified principles: Defined all principles (Toolchain, Testing, Architecture, Documentation)
- Added sections: Technology Stack, Development Workflow
- Templates requiring updates: tasks-template.md (✅ updated)
-->
# Whiteboard Constitution

## Core Principles

### I. Modern Python Toolchain
Use `uv` for all dependency management and execution. Python 3.12+ is required. All dependencies must be explicitly defined in `pyproject.toml` via `uv add` (production) or `uv add --dev` (development). The environment must be kept in sync using `uv sync`.

### II. Comprehensive Testing Strategy
Testing is bifurcated into Unit and Behavior-Driven tests.
- **Unit Tests**: Use `pytest` targeting high coverage for business logic (e.g., shape calculation, state management).
- **BDD**: Use `behave` driven by `playwright` for end-to-end user stories defined in Gherkin `.feature` files. Steps must interact with the Flet web view to verify acceptance criteria.

### III. Architecture & State Separation
State must be managed centrally (Single Source of Truth), distinct from UI controls. UI components should use Flet's `UserControl` (or `flet.Control` subclasses) for reusability. Canvas operations (pan/zoom) must be handled mathematically before rendering or during hit-testing.

### IV. Documentation-Driven
Documentation is maintained in Markdown using `mkdocs` with the `mkdocs-material` theme. It serves as the primary reference for usage and architecture.

## Technology Stack

- **Language**: Python >= 3.12
- **UI Framework**: Flet (Flutter for Python)
- **Package Manager**: uv (managed by astral-sh)
- **Testing**: pytest, behave, playwright
- **Documentation**: mkdocs, mkdocs-material

## Development Workflow

- **Dependency Management**: `uv add <package>` (prod), `uv add --dev <package>` (dev), `uv sync`.
- **Execution**: `uv run python main.py` (or entry point).
- **Testing**: `uv run pytest` (unit), `uv run behave` (BDD).
- **Documentation**: `uv run mkdocs serve`.

## Governance

This Constitution supersedes all other project documentation. Amendments require documentation, approval, and a version bump. All PRs and reviews must verify compliance with these principles.

**Version**: 1.0.0 | **Ratified**: 2025-11-25 | **Last Amended**: 2025-11-25
