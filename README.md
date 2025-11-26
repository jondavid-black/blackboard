# Whiteboard

A prototype whiteboard application built with [Flet](https://flet.dev/) (Flutter for Python). This application allows users to draw on a canvas using different tools like a pen and select shapes.

## Features

- **Pen Tool**: Freehand drawing on the canvas.
- **Selection Tool**: Select and manipulate objects (Work in Progress).
- **Pan/Zoom**: Navigate the infinite canvas.
- **Responsive UI**: Works on Desktop and Web.

## Developer Notes

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) for dependency management.

### Setup

1. Clone the repository.
2. Install dependencies:
   ```bash
   uv sync
   ```

### Running the Application

**Desktop Mode:**

```bash
uv run flet run src/main.py
```

**Web Mode:**

```bash
uv run flet run --web src/main.py
```

### Testing

**Unit Tests:**

Run the unit test suite using `pytest`:

```bash
uv run pytest
```

**BDD Tests:**

Run the behavior-driven development tests using `behave` and `playwright`:

```bash
uv run behave
```

### Code Quality

**Linting:**

Check for linting errors using `ruff`:

```bash
uv run ruff check
```

**Formatting:**

Format the code using `ruff`:

```bash
uv run ruff format
```

