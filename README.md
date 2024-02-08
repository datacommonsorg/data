# Data Commons Data Imports

This is a collaborative repository for contributing data to Data Commons.

If you are looking to use the data in Data Commons, please visit our
[API documentation](http://docs.datacommons.org/api/).

## About Data Commons

[Data Commons](https://datacommons.org/) is an Open Knowledge Graph that
provides a unified view across multiple public data sets and statistics. We've
bootstrapped the graph with lots of [data](https://datacommons.org/datasets)
from US Census, CDC, NOAA, etc., and through collaborations with the New York
Botanical Garden, Opportunity Insights, and more. However, Data Commons is meant
to be for community, by the community. We're excited to work with you to make
public data accessible to everyone.

To see the extent of data we have today, [browse the graph](https://datacommons.org/browser).

We welcome contributions to the graph! To get started, take a look at the
resources [in the docs directory](docs/) and the [list of pending
imports](https://github.com/orgs/datacommonsorg/projects/10).

## License

Apache 2.0

## Development

Every data import involves some or all of the following: obtaining the source
data, cleaning the data, and converting the data into one of [Meta Content
Framework (MCF)](docs/mcf_format.md), JSON-LD, or RDFa format. We ask that you
check in all scripts used in this process, so that others can reproduce and
continue your work.

Source data must meet the [licensing policy](LICENSING_POLICY.md) requirements.

Scripts should go under the top-level `scripts/` directory, depending on the
provenance and dataset. See
[the example](scripts/example_provenance/example_dataset/README.md) for more
detail.

We provide some utility libraries under the top-level `util/` directory. For
example, this includes maps to and from common geographic identifiers.

### GitHub Development Process

#### One Time Set-up

1. Install [Git LFS](https://git-lfs.github.com/)

1. Fork this repo - follow the [Github guide to forking a repo](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo)
   - In https://github.com/datacommonsorg/data, click on "Fork" button to
   fork the repo.
   - Add upstream: `git remote add upstream https://github.com/datacommonsorg/data.git`
   - Clone your forked repo to your desktop. Please do not directly clone
   this repo, verify by running `git remote -v`, the output should look like
   this:

    ```shell
    shell> git remote -v
    origin  https://github.com/YOUR-GITHUB-USERNAME/data.git (fetch)
    origin  https://github.com/YOUR-GITHUB-USERNAME/data.git (push)
    upstream        https://github.com/datacommonsorg/data.git (fetch)
    upstream        https://github.com/datacommonsorg/data.git (push)
    ```

1. Please ask to join the
[datacommons-developers](https://groups.google.com/g/datacommons-developers)
Google group. For example, membership in this group provides access to debug
logs of pre-submit tests that run for your Pull Request.

#### Creating Pull Requests

Contribute your changes by creating pull requests from your fork of this repo.
Learn more in [this step-by-step guide](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork).

A summary of the steps in the development workflow are:

```shell
git checkout master
git pull upstream master
git checkout -b new_branch_name
# Make some code change
git add .
git commit -m "commit message"
git push -u origin new_branch_name
```

Then in your forked repo, you can send a Pull Request. Wait for approval of
the Pull Request and merge the change.

If this is your first time contributing to a Google Open Source project, you
may need to follow the steps in [contributing.md](contributing.md).

### Code quality

Code style guidelines ease understanding and maintaining code. Automated checks
enforce some of the guidelines.

#### Python

##### Setup

Ensure prerequisites are installed

* [Python3](https://www.python.org/downloads/)
* [Pip](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)

Install requirements and setup a virtual environment to isolate python development in this repo.

```shell
python3 -m venv .env
source .env/bin/activate

pip3 install -r requirements_all.txt
```

##### Testing

Scripts should be accompanied with tests using the [`unittest`
framework](https://docs.python.org/3/library/unittest.html), and named with
an `_test.py` suffix.

A common test pattern is to drive your main processing function through some
sample input files (e.g., with a few rows of the real csv/xls/etc.) and
compare the produced output files (e.g., cleaned csv, mcf, tmcf) against
expected ones.  An example test following this pattern is
[here](https://github.com/datacommonsorg/data/blob/b868f558497783bba7a7f3ced9b918f1c0249290/scripts/us_epa/facility/process_facility_test.py).

> **IMPORTANT:**  Please ensure that there is an `__init__.py` file in the
directory of your import scripts, and every parent directory until
`scripts/`.  This is necessary for the `unittest` framework to automatically
discover and run your tests as part of presubmit.

> **NOTE:** In the presence of `__init__.py`, you will need to adjust the way
you import modules and run tests, as below.

1. You should import modules in your test with a dotted prefix like
   [this](https://github.com/datacommonsorg/data/blob/b868f558497783bba7a7f3ced9b918f1c0249290/scripts/us_epa/facility/process_facility_test.py#L8).

2. Instead of running your test as `python3 foo_test.py`, run as:

    `python3 -m unittest discover -v -s ../ -p "foo_test.py"`

   Consider creating a generic alias like this:

    - `alias dc-data-py-test='python3 -m unittest discover -v -s ../ -p "*_test.py"'`

   Then, you can run your tests as:

    - `dc-data-py-test`

##### Guidelines

*   Any additional package required must be specified in the `requirements_all.txt`
    file in the top-level folder. No other `requirements.txt` files are allowed.
*   Code must be formatted according to the
    [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
    according to the [yapf formatter](https://github.com/google/yapf).
*   Code must not generate lint errors or warnings according to
    [pylint](https://www.pylint.org/) configured for the
    [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
    as specified in
    [.pylintrc](https://github.com/datacommonsorg/data/blob/master/.pylintrc).
*   Tests must succeed.

Consider automating coding to satisfy some of these requirements.

*   [Integrate pylint](http://pylint.pycqa.org/en/latest/user_guide/ide-integration.html)
    with your editor.
*   Integrate yapf with
    [Visual Studio](https://code.visualstudio.com/docs/python/editing#_formatting),
    [Emacs](https://www.emacswiki.org/emacs/PythonProgrammingInEmacs#toc21),
    [vim](https://github.com/mindriot101/vim-yapf#why-you-may-not-need-this-plugin).
    Specify the Google style using `--style google`.

To run the tools via a command line (both installed after setup steps above):

*   [pylint](http://pylint.pycqa.org/en/latest/user_guide/run.html).
*   [yapf](https://github.com/google/yapf#id2), execute using
    `--style google`, e.g.,

```shell
# Update (--in-place) all files
./run_tests.sh -f

# Produce differences between the current code and reformatted code.  Empty
# output indicates correctly formatted code.
./run_tests.sh -l
```

To run a unit test, use a command like

```shell
python3 -m unittest discover -v -s util/ -p "*_test.py"
```

The `discover` option searches (`-s`) the `util/` directory for files with
filenames ending with `_test.py`. It considers all these files to be unit tests
to be run. Output is verbose (`-v`).

We provide a utility to run all unit tests in a folder easily (e.g. util/):
```shell
./run_tests.sh -p util/
```

Or to run all tests and checks:
```shell
./run_tests.sh -a
```

**NOTE: Please ensure that all tests are runnable from the test script, e.g. modules should be relative to the root of the repo.**

#### Disabling style checks

Occasionally, one has to disable style checking or formatting for particular
lines.

To
[disable pylint for a particular line or block](http://pylint.pycqa.org/en/latest/user_guide/message-control.html)
, use syntax like

```
# pylint: disable=line-too-long,unbalanced-tuple-unpacking
```

To disable yapf for some lines,

```
# yapf: disable
... code ...
# yapf: enable
```

#### Go

*   Code must be formatted according to
    [go fmt](https://golang.org/cmd/go/#hdr-Gofmt__reformat__package_sources).
*   Vetting must identify no likely mistakes as revealed by
    [go vet](https://golang.org/cmd/go/#hdr-Report_likely_mistakes_in_packages).
*   Code must not generate lint errors or warnings according to
    [golangcli-lint](https://golangci-lint.run/). To run on `foo.go`, use
    `golangcli-lint run foo.go`.
*   Tests must succeed. Files ending with `_test.go` are considered tests. They
    are executed using [go test](https://golang.org/cmd/go/#hdr-Test_packages).

## Support

For general questions or issues about importing data into Data Commons, please
open an issue on our [issues](https://github.com/datacommonsorg/data/issues)
page. For all other questions, please [share feedback on this form](https://docs.google.com/forms/d/e/1FAIpQLScJTtNlIItT-uSPXI98WT6yNlavF-kf5JS0jMrCvJ9TPLmelg/viewform).

**Note** - This is not an officially supported Google product.
