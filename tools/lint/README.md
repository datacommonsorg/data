# Repo lint checks

Lint checks that run in CI in addition to ruff and yapf. Each check is a
standalone script with no third-party dependencies.

`./run_tests.sh -l` runs these checks along with ruff and yapf. In CI, it runs
in the lint step of [cloudbuild.py.yaml](../../cloudbuild.py.yaml).

| Check | Script |
|---|---|
| absl flags registered on import | [absl_flags_lint.py](absl_flags_lint.py) |

## absl flags registered on import

absl keeps one flag registry per process. If a file defines a flag at module
level, the flag is registered as soon as the file is imported, for example by a
test or by another script. Two files that define a flag with the same name then
can't be imported together: the second import fails with `DuplicateFlagError`.

The check fails if any of these run when a file is imported:

- `flags.DEFINE_*()` calls
- other `absl.flags` functions that need the flag to be defined first, such as
  `flags.mark_flag_as_required()` or `@flags.validator`
- calls to a function that defines flags, such as `_define_flags()`

Code runs on import if it's at module level, including inside module-level
`if`, `try`, `with`, and `for` blocks, and inside class bodies. Code inside
functions or under `if __name__ == '__main__':` doesn't.

### How to fix

Move the flag definitions, and calls like `flags.mark_flag_as_required()`, into
a function. Call it under `if __name__ == '__main__':`, just before `app.run()`.

Before:

```python
from absl import app
from absl import flags

flags.DEFINE_string('input_path', None, 'Input CSV file.')
flags.mark_flag_as_required('input_path')
_FLAGS = flags.FLAGS


def main(_):
    process(_FLAGS.input_path)


if __name__ == '__main__':
    app.run(main)
```

After:

```python
from absl import app
from absl import flags

_FLAGS = flags.FLAGS


def _define_flags():
    flags.DEFINE_string('input_path', None, 'Input CSV file.')
    flags.mark_flag_as_required('input_path')


def main(_):
    process(_FLAGS.input_path)


if __name__ == '__main__':
    _define_flags()
    app.run(main)
```

Running the script works the same as before, and `--help` still lists the
flags. Read flag values only in `main()`, and pass them as arguments to other
functions, so that tests can call those functions without setting flags.

### Files that aren't fixed yet

Files that registered flags on import when this check was added are listed in
`EXCLUDED_FILES` in [absl_flags_lint.py](absl_flags_lint.py), and are skipped.

- When you fix a file, remove it from `EXCLUDED_FILES`. The check fails if a
  listed file no longer registers flags on import, or no longer exists, so the
  list only gets shorter.
- Don't add files to the list. Fix the file instead.

### Running only this check

```bash
# Check the whole repo.
python3 tools/lint/absl_flags_lint.py

# Check specific files or folders.
python3 tools/lint/absl_flags_lint.py path/to/script.py path/to/folder
```
