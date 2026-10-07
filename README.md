# Reverse-Engineering-Workflows

Public, minimal CI for harmless fixtures. Contains **no** private source, targets, inputs, outputs or credentials.

- `public-smoke` (manual `workflow_dispatch` only): read-only token, standard `ubuntu-latest`, 10-minute timeout, no caches/artifacts, checkout action pinned to a full commit SHA, credentials not persisted.
- A public smoke run is **not** the private project's full gate.
