# Agentic Guidelines for CC3501 Computer Graphics

This repository contains educational material for the CC3501 Computer Graphics and Modeling course at the University of Chile. It uses Python with Pyglet and PyOpenGL for 3D rendering.

## 🛠 Build, Lint, and Test Commands

The project uses [`uv`](https://docs.astral.sh/uv/) for dependency management and environment execution.

### Environment Setup
- **Install dependencies:** `uv sync`
- **Run a command in the environment:** `uv run <command>`

### Running Examples (Manual Testing)
The primary way to verify changes is by running the examples through `caja_de_juguetes.py`.
- **List all examples:** `uv run python caja_de_juguetes.py`
- **Run a specific example:** `uv run python caja_de_juguetes.py <example_name> [args]`
  - Example: `uv run python caja_de_juguetes.py hello_world`
  - Example with assets: `uv run python caja_de_juguetes.py image_texture assets/dice.jpg`

### Testing
There are no automated test suites (like `pytest`) currently established in the core repository. Testing is primarily visual and manual via the examples. If you add new logic to `grafica/`, ensure it works correctly by verifying the relevant example or creating a new script in `examples/`.

### Linting and Formatting
While there is no explicit `lint` command in `pyproject.toml`, the codebase generally follows PEP 8.
- **Check formatting (if installed):** `uv run ruff check .` or `uv run flake8 .`
- **Auto-format (if installed):** `uv run ruff format .` or `uv run black .`

---

## 🎨 Code Style Guidelines

### 📦 Imports
- **Standard libraries first**, then third-party (numpy, pyglet), then local modules.
- Use `import numpy as np`.
- Local imports should be relative within the `grafica` package (e.g., `from . import transformations as tr`).
- In `examples`, use `import grafica.transformations as tr`.

### 🔧 Types and Naming
- **Naming Convention:**
  - Functions and variables: `snake_case` (e.g., `calculate_global_transforms`).
  - Classes: `PascalCase` (e.g., `Scenegraph`).
  - Constants: `UPPER_SNAKE_CASE`.
  - Matrix operations: Often shortened in examples, e.g., `tr` for `transformations`.
- **Types:**
  - Matrices and vectors: Use `numpy.ndarray` with `dtype=np.float32` for OpenGL compatibility.
  - Transformation matrices are 4x4.
- **Type Hinting:** Use Python type hints where they improve clarity, especially in the `grafica` core library.

### 📐 Mathematics and Transformations
- **Column-major order:** When passing matrices to Pyglet/OpenGL, use `.reshape(16, 1, order="F")` or ensure the matrix is transposed if necessary.
- **Identity:** Use `tr.identity()` instead of manual `np.eye(4)`.
- **Rotation:** Angles are generally in **radians**.

### 🏗 Scene Graph Architecture
- The project uses a `networkx`-based `Scenegraph`.
- Nodes store `transform` (local) and `mesh` data.
- Global transforms are calculated via DFS traversal (`calculate_global_transforms`).

### ❌ Error Handling
- Use `try...except pyglet.graphics.shader.ShaderException` when setting uniforms, as some shaders might not contain all parameters (e.g., `view` or `projection`).
- Provide informative error messages when failing to load assets (OFF, OBJ, STL files).

### 📝 Documentation
- Comments should be in Spanish or English (the codebase contains both). Spanish is preferred for educational explanations.
- Use docstrings for classes and public functions in the `grafica` directory.

---

## 🤖 Agent Instructions
- **Asset Paths:** Always assume assets are in the `assets/` directory. Use absolute paths or paths relative to the project root.
- **Pyglet Compatibility:** Ensure you are using `pyglet>=2.0` syntax (e.g., `pyglet.graphics.shader.ShaderProgram`).
- **Numpy 2.0:** The project restricts `numpy<2.4.0`. Avoid using deprecated Numpy features that might break in newer versions.
