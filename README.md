# BOM Monitor Template Builder

Installed software environments are inspected to identify:

- related Windows services
- related Windows event logs and providers
- monitoring candidates
- BOM for Windows monitoring template candidates

## Development phases

1. Collect software, service, registry and event-log information
2. Analyze relationships between software and monitoring targets
3. Generate review reports
4. Generate BOM monitoring templates
5. Add optional GUI and remote collection support

## Quick start

```bash
./scripts/setup.sh
source .venv/bin/activate
./scripts/run.sh --help
pytest
```

## TemplateData knowledge import

Iteration 1 adds source inspection and generic `AutoTemplate.yml` analysis without CAB extraction.

```bash
./scripts/run.sh knowledge inspect --source import/TemplateData
./scripts/run.sh knowledge import --source import/TemplateData --output knowledge --dry-run
./scripts/run.sh knowledge import --source import/TemplateData --output knowledge
```

Generated artifacts are written under `knowledge/`:

- `source_inventory/`: file inventory JSON and CSV
- `categories/`: detected category folders
- `autotemplate/`: parsed YAML and flattened YAML paths
- `state/`: hash-based import state for later diff runs
- `reports/`: import-plan JSON and CSV
