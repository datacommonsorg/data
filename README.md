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

To see the extent of data we have today, browse the graph using our
[browser](https://browser.datacommons.org/).

## License

Apache 2.0

## Development

Every data import involves some or all of the following: obtaining the source
data, cleaning the data, and converting the data into one of Meta Content
Framework, JSON-LD, or RDFa format. We ask that you check in all scripts used in
this process, so that others can reproduce and continue your work.

Source data must meet the [licensing policy](LICENSING_POLICY.md) requirements.

Scripts should go under the top-level `scripts/` directory, depending on the
provenance and dataset. See
[the example](scripts/example_provenance/example_dataset/README.md) for more
detail.

We provide some utility libraries under the top-level `util/` directory. This
includes maps to and from common geographic identifiers, a sharding writer to
break up large output files, a templating library for writing
[StatisticalPopulation](https://schema.org/StatisticalPopulation)s and
[Observation](https://schema.org/Observation)s, and more to come.

### GitHub Development Process

In https://github.com/datacommonsorg/data, click on "Fork" button to fork the
repo.

Clone your forked repo to your desktop.

Add datacommonsorg/data repo as a remote:

```shell
git remote add dc https://github.com/datacommonsorg/data.git
```

Every time when you want to send a Pull Request, do the following steps:

```shell
git checkout master
git pull dc master
git checkout -b new_branch_name
# Make some code change
git add .
git commit -m "commit message"
git push -u origin new_branch_name
```

Then in your forked repo, you can send a Pull Request. If this is your first
time contributing to a Google Open Source project, you may need to follow the
steps in [contributing.md](contributing.md).

Wait for approval of the Pull Request and merge the change.

### Code quality

Code style guidelines ease understanding and maintaining code. Automated checks
enforce some of the guidelines.

#### Python

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

To run the tools via a command line:

*   [pylint](http://pylint.pycqa.org/en/latest/user_guide/run.html).
*   After [installing yapf](https://github.com/google/yapf#id2), execute using
    `--style google`, e.g.,

```
# Update (--in-place) all files in the util/ directory and its subdirectories.
yapf --recursive --in-place --style google util/

# Produce differences between the current code and reformatted code.  Empty
# output indicates correctly formatted code.
yapf --recursive --diff --style google util/
```

To run a unit test, use a command like

```
python3 -m unittest discover -v -s util/ -p "*_test.py"
```

The `discover` option searches (`-s`) the `util/` directory for files with
filenames ending with `_test.py`. It considers all these files to be unit tests
to be run. Output is verbose (`-v`).

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
page. For all other questions, please send an email to
`support@datacommons.org`.

**Note** - This is not an officially supported Google product. ```
