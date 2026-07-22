# GitHub Actions integration

This workflow installs PyArchLens, validates architecture rules, generates reports, exports a Mermaid dependency graph, and stores artifacts.

```yaml
name: Architecture

on:
  pull_request:
  push:
    branches:
      - main

jobs:
  pyarchlens:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install project
        run: pip install -e ".[tui,dev]"

      - name: Run tests
        run: pytest -q

      - name: Check architecture
        run: pyarchlens check . --config pyarchlens.yml --out reports/pyarchlens_check.json

      - name: Generate reports
        run: pyarchlens report . --out reports --config pyarchlens.yml

      - name: Export Mermaid graph
        run: pyarchlens mermaid . --out reports/dependencies.mmd

      - name: Create architecture snapshot
        run: pyarchlens snapshot . --config pyarchlens.yml --out snapshots/architecture.json

      - uses: actions/upload-artifact@v4
        with:
          name: pyarchlens-reports
          path: |
            reports
            snapshots
```
