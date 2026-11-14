# Repo lint checks

Lint checks that run in CI for files that ruff and yapf don't cover. Each check
is a standalone script with no third-party dependencies.

`./run_tests.sh -l` runs these checks along with ruff and yapf. In CI, it runs
in the `lint` step of [cloudbuild.py.yaml](../../cloudbuild.py.yaml).

| Check | Script | Run only this check |
|---|---|---|
| JSON validity | [json_lint.py](json_lint.py) | `./run_tests.sh -j` |

## JSON validity

Checks every `.json` and `.geojson` file in the repo. A file fails if it:

- is not valid UTF-8 (a leading BOM is allowed)
- is not valid JSON, for example trailing commas, comments, or leftover
  merge-conflict markers
- repeats a key in the same object (Python silently keeps the last value)
- uses `NaN`, `Infinity`, or `-Infinity`

Formatting (indentation, key order, final newline) is not checked.

Git LFS pointer files and the directories in `EXCLUDED_DIRS` (such as `.env`,
`.git`, and `scratch`) are skipped.

To check specific files or folders:

```bash
python3 tools/lint/json_lint.py path/to/file.json path/to/folder
```

### Excluding a file

If a file can't be fixed right away, add its path (relative to the repo root)
to `EXCLUDED_FILES` in [json_lint.py](json_lint.py), with a comment saying why.
Remove the entry once the file is fixed.

## Adding a new check

1. Add `tools/lint/<name>_lint.py` and `tools/lint/<name>_lint_test.py`.
2. Call it from `run_lint_test` in [run_tests.sh](../../run_tests.sh), so that
   `./run_tests.sh -l` (and CI) runs it. Optionally add a flag to run it alone.
3. If the check covers new file types, make sure the `data-pull-request-py`
   Cloud Build trigger in `datcom-ci` includes them in its included-files
   filter. Otherwise PRs that only change those files won't run CI.
4. Add a row to the table above.
