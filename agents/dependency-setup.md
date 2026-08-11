# Agent dependency setup

Repository-owned agent tools share one readiness check:

```bash
./agents/check_dependencies.sh
./agents/check_dependencies.sh --local
./agents/check_dependencies.sh --help
```

The default command runs local dependency checks first, then checks both
Google Cloud CLI authentication and Application Default Credentials (ADC).
`--local` stops after local checks. The command only reports readiness: it does
not install software, log in, print tokens, or query cloud resources.

Run it when setting up the repository or resolving a dependency or
authentication failure. Agent workflows should not run it before every task.

## System tools

The local phase requires `bash`, `curl`, `git`, `gcloud`, `jq`, `python3`,
`realpath`, and `sed` on `PATH`.

The checker uses `command -v` from a non-interactive Bash process. Personal
aliases defined only in `.zshrc`, `.bashrc`, or another interactive-shell
configuration might not be loaded and can therefore be reported as missing.
Agent-executed commands use similarly non-interactive shells, so dependencies
should normally be available through `PATH`; do not rely solely on personal
aliases.

On macOS, install the Xcode Command Line Tools, then use Homebrew or another
trusted package manager for missing utilities. On Debian- or Ubuntu-based Linux,
the corresponding packages are generally `bash`, `coreutils`, `curl`, `git`,
`jq`, `python3`, and `sed`. Use your distribution's package manager for other
Linux systems.

### gcloud CLI

Install or update the Google Cloud CLI using the
[official installation guide](https://cloud.google.com/sdk/docs/install). The
checker records the installed version but does not enforce a minimum. It also
checks that every exact `gcloud` operation registered in
`GCLOUD_COMMANDS` is available.

## Python dependencies

Create or repair the repository Python environment only through:

```bash
./run_tests.sh -r
```

The checker requires executable `.env/bin/python` and imports every module
registered in `agents/common/scripts/check_python_dependencies.py`.
`pyopenssl` is intentionally retained for Google Cloud CLI compatibility on
platforms that require it.

## gcloud CLI authentication

The default check requires an active Google Cloud CLI account and a usable CLI
access token. If this check fails, a human can establish or refresh it with:

```bash
gcloud auth login
```

The checker does not run that command or display the selected account.

## Application Default Credentials

Python Google Cloud libraries use ADC independently of the CLI account token.
If the ADC check fails, a human can establish or refresh it with:

```bash
gcloud auth application-default login
```

CLI and ADC identities are not required to match.

Passing authentication checks establishes only that each credential path can
produce a non-empty token. It does not establish IAM permissions, enabled APIs,
quota-project configuration, or the existence of any target resource.

## Optional sibling import checkout

For additional Workflow and helper source navigation, the checker recognizes
this optional layout:

```text
<workspace>/
├── data/       # current repository
└── import/     # optional Git checkout
    └── pipeline/workflow/import-automation-workflow.yaml
```

The resolved Git root must be exactly `<workspace>/import`. An absent or invalid
sibling is reported as `SUGGESTED` and never makes readiness fail. Live cloud
revisions and metadata remain runtime truth.
