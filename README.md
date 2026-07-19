# PyArchLens

PyArchLens is a Python architecture analysis tool for developers who want to understand, inspect, and improve the internal structure of Python projects.

It scans a codebase, parses Python modules with the built-in `ast` module, builds a dependency graph, detects import cycles, calculates module-level metrics, and presents the result through a command-line interface, terminal UI, and exportable reports.

## Features

- Python project scanning
- AST-based source code parsing
- Internal import graph construction
- Dependency cycle detection
- Orphan module detection
- External dependency counting
- Module complexity scoring
- CLI output with Rich tables
- Interactive terminal UI powered by Textual
- JSON report generation
- Self-contained HTML report generation
- Test suite for scanner, parser, graph, and analyzer logic

## Why PyArchLens exists

Large Python projects can become difficult to understand over time. Imports grow in unexpected directions, modules become too complex, and hidden dependency cycles make refactoring risky.

PyArchLens helps answer questions like:

- Which modules are the most complex?
- Are there circular imports?
- Which files are isolated from the rest of the project?
- What external packages are used most often?
- How is the project connected internally?
- Can this architecture be monitored over time?

## Installation

Clone the repository:

```bash
git clone https://github.com/your-username/py-arch-lens.git
cd py-arch-lens
```

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

Install the project in editable mode with development and TUI dependencies:

```bash
pip install -e ".[tui,dev]"
```

## Quick start

Analyze the current project:

```bash
pyarchlens analyze .
```

Generate reports:

```bash
pyarchlens report . --out reports
```

Open the generated HTML report on macOS:

```bash
open reports/pyarchlens_report.html
```

Run the terminal UI:

```bash
pyarchlens tui .
```

Run tests:

```bash
pytest -q
```

## Commands

### Analyze a project

```bash
pyarchlens analyze PATH
```

Example:

```bash
pyarchlens analyze .
```

This prints a terminal summary with project statistics, module metrics, dependency cycles, and external imports.

### Generate reports

```bash
pyarchlens report PATH --out reports
```

This creates:

```text
reports/pyarchlens_report.json
reports/pyarchlens_report.html
```

The JSON report is useful for automation and future CI integration. The HTML report is a readable visual summary that can be opened in a browser.

### Open the TUI dashboard

```bash
pyarchlens tui PATH
```

TUI controls:

```text
q  Quit
r  Refresh analysis
```

## Example output

PyArchLens analyzes a project and reports:

- total modules
- total dependency edges
- number of cycles
- number of orphan modules
- external imports
- per-module lines of code
- import count
- class count
- function and method count
- complexity score

## Project structure

```text
py-arch-lens/
├── reports/
├── src/
│   ├── __init__.py
│   ├── __main__.py
│   ├── analyzer.py
│   ├── cli.py
│   ├── config.py
│   ├── formatting.py
│   ├── graph.py
│   ├── models.py
│   ├── parser.py
│   ├── scanner.py
│   ├── tui.py
│   └── reports/
│       ├── __init__.py
│       ├── html_report.py
│       └── json_report.py
├── tests/
├── README.md
├── pyproject.toml
└── .gitignore
```

## Core architecture

PyArchLens is built as a small analysis pipeline:

```text
ProjectScanner -> ModuleParser -> DependencyGraph -> ArchitectureAnalyzer -> CLI/TUI/Reports
```

### Scanner

Finds Python files in a target project and ignores common generated or virtual environment directories.

### Parser

Uses Python's built-in `ast` module to extract imports, classes, functions, methods, calls, branch counts, and nesting information.

### Graph

Builds a directed graph of internal module dependencies and detects cycles and orphan modules.

### Analyzer

Combines scanner, parser, and graph logic into a single analysis summary.

### Reports

Exports analysis results as JSON and self-contained HTML.

## Metrics

The first version calculates a simple module complexity score based on:

- code lines
- import count
- class count
- function count
- method count
- async function count
- branch count
- maximum nesting depth

The score is not intended to replace advanced static analysis tools. It is designed to provide a fast architecture-level signal and highlight modules worth reviewing.

## Testing

Run the test suite:

```bash
pytest -q
```

## Architecture rules

PyArchLens can validate a project against architecture rules stored in YAML.

Example `pyarchlens.yml`:

```yaml
layers:
  - name: interface
    modules:
      - "src.cli"
      - "src.tui"
    may_depend_on:
      - application
      - reports

  - name: application
    modules:
      - "src.analyzer"
    may_depend_on:
      - core

  - name: core
    modules:
      - "src.models"
      - "src.parser"
      - "src.scanner"
      - "src.graph"
    may_depend_on: []

forbidden_imports:
  - source: "src.*"
    target: "tests.*"
    reason: "Runtime package must not import test modules"
    severity: error
```

Run architecture validation:

```bash
pyarchlens check . --config pyarchlens.yml
```

Write a machine-readable check report:

```bash
pyarchlens check . --config pyarchlens.yml --out reports/pyarchlens_check.json
```

Generate regular reports with validation results included:

```bash
pyarchlens report . --out reports --config pyarchlens.yml
```

The `check` command exits with code `1` when error-level violations are found, which makes it suitable for CI pipelines.

### Find a dependency path

```bash
pyarchlens path . pyarchlens.cli pyarchlens.analyzer
```

Example output:

```text
pyarchlens.cli -> pyarchlens.analyzer
```

If no path exists, the command exits with code `1`.

### Inspect one module

```bash
pyarchlens module . pyarchlens.cli
```

This prints:

- file path
- line count
- complexity score
- incoming dependency count
- outgoing dependency count
- classes
- functions
- internal imports
- modules that import it
- external imports

### Export a Mermaid graph

```bash
pyarchlens mermaid . --out reports/dependencies.mmd
```

The generated `.mmd` file can be pasted into Mermaid-compatible tools or Markdown renderers.

### Enhanced TUI

The TUI now includes:

- module filtering
- module detail panel
- incoming and outgoing dependency counts
- dependency graph text view
- cycle table
- external import table
- refresh action

Run it with:

```bash
pyarchlens tui .
```

Controls:

```text
q  Quit
r  Refresh analysis
```
