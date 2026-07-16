# Architecture

## Processing flow

1. Collector reads installed software, services and event-log information.
2. Analyzer scores relationships between software and monitoring candidates.
3. Generator writes review reports and BOM template candidates.
4. An operator reviews and approves generated monitoring definitions.

## Module responsibilities

- collectors: acquire raw information
- analyzers: determine relevance and monitoring priority
- generators: create reports and BOM monitoring templates
- models: define shared data structures
- utils: logging, configuration and common helpers
