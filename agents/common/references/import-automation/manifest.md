# Import manifest reference

Use this reference after selecting a repository import and before interpreting
its `manifest.json`. It describes the current repository contract for agents;
it is not evidence that repository configuration is deployed or currently
running.

## Location and identity

Repository catalog operations inspect only:

- `statvar_imports/**/manifest.json`
- `scripts/**/manifest.json`

Each manifest contains an `import_specifications` list. Select the object whose
case-sensitive `import_name` equals the canonical name returned by the catalog
helper. An absolute import name has the form
`<repository-relative-import-directory>:<import_name>`.

## Fields

Paths and globs are relative to the directory containing `manifest.json` unless
noted otherwise.

| Field | Type and requirement | Agent interpretation |
|---|---|---|
| `import_specifications` | Required root list | Independently named import specifications in this manifest. |
| `import_name` | Required non-empty string | Canonical, case-sensitive import identity. Do not substitute a display name. |
| `provenance_url` | Required string | Source URL recorded in generated provenance metadata. |
| `provenance_description` | Required string | Human-readable description recorded in generated provenance metadata. |
| `curator_emails` | Required list of strings | Contacts responsible for the import. Do not expose addresses unless the request requires them. |
| `scripts` | List of strings; required by the normal executor path | Import-relative Python or shell script entries, including arguments, run sequentially to generate inputs. |
| `import_inputs` | List of objects; required for normal data import | Mappings from input labels to import-relative paths, globs, or lists of them. Common, non-exhaustive labels include `cleaned_csv`, `template_mcf`, `node_mcf`, and `stat_var_mcf`; read every key present. |
| `source_files` | Optional list of strings | Import-relative files or globs uploaded under the version's `source_files/` artifacts. These are not necessarily import-tool inputs. |
| `cron_schedule` | Optional string | Repository-configured cron intent. It does not prove that a Scheduler job exists or uses this value. |
| `validation_config_file` | Optional string | Import-relative validation override merged with the executor's repository-level base validation configuration. |
| `user_script_timeout` | Optional number | Overall Cloud Run scheduled-job timeout in seconds. It does not override script subprocess timeouts in the default Cloud Batch path. |
| `resource_limits` | Optional object | Requested `cpu`, `memory`, and `disk` overrides. Effective fields depend on the configured executor type. |
| `config_override` | Optional object | Overrides of executor configuration fields for this import specification. Interpret individual keys using `ExecutorConfig`. |

## Specialized or legacy fields

The current manifests also contain `gcs_bucket`, `import_type`, `source_file`,
and top-level `cleanup_gcs_volume_mount` in a small number of specifications.
The current in-repository executor does not read those fields directly from an
import specification. Do not infer runtime behavior from them without tracing
the relevant specialized or external consumer. The supported source-artifact
field is `source_files`; executor settings such as `cleanup_gcs_volume_mount`
are applied through `config_override` when used as per-import overrides.

## Interpretation boundaries

- A manifest describes repository configuration, not deployed infrastructure,
  execution history, current status, or published data.
- Read the exact selected specification; one manifest may contain multiple
  imports.
- Read referenced scripts and inputs only when the question requires their
  behavior. Do not rely on a helper-generated interpretation of their content.
- Verify Scheduler, Workflow, Batch, artifact, or Spanner state with the
  corresponding bounded operational reference before making live claims.

## Implementation evidence

- [Manifest validation](../../../../import-automation/executor/app/executor/validation.py)
  defines the required root and specification identity/provenance fields.
- [Import execution](../../../../import-automation/executor/app/executor/import_executor.py)
  consumes scripts, import inputs, source files, and validation overrides.
- [Scheduler job management](../../../../import-automation/executor/app/executor/scheduler_job_manager.py)
  consumes cron schedules, timeout overrides, and resource limits.
- [Executor startup](../../../../import-automation/executor/main.py) applies
  `config_override` to `ExecutorConfig`.
- [Import target handling](../../../../import-automation/executor/app/executor/import_target.py)
  defines relative and absolute import-name syntax. It does not define manifest
  field semantics.
