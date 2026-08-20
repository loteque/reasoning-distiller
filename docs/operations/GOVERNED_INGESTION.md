# Explicit Governed Evidence for Distillation

The ingestion adapter supports two explicit evidence source types:

- `--evidence` creates `repository_file` sources;
- `--governed-evidence` creates `governed_artifact` sources.

Example:

```bash
python .reasoning-distiller/runtime/rd_distill.py ingest \
  --governed-evidence docs/design/RIL_CLI_DESIGN_CONTRACT.md \
  --governed-evidence docs/design/RIL_HUMAN_AGENT_DESIGN_CONTRACT.md \
  --evidence docs/status/verification.json \
  --invocation-id reviewed-baseline
```

Source authority is never inferred from a filename, directory, heading, source ID,
or words such as `normative` or `accepted`. A file selected only with
`--evidence` remains a `repository_file` even if its name suggests a contract.

Selecting the same resolved file through both source types is ambiguous and fails
closed with `EVIDENCE_SOURCE_TYPE_CONFLICT`.

Interactive ingestion asks for the source type after each file, directory, or
glob selection and defaults to `repository_file`.

Source IDs are deterministic bookkeeping. Existing `repository_file` IDs retain
the `src:file:<digest-prefix>` form for compatibility. Explicit governed sources
use `src:governed:<digest-prefix>`. The prefix carries no authority semantics;
source standing is determined solely by the `type` field in the invocation source
registry.

`governed_artifact` should be used only when project governance or explicit human
authority has established that the selected artifact is governed. The ingestion
adapter does not make that judgment itself.
