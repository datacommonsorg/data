# Data Commons Data Imports

This is a collaborative repository for contributing data to Data Commons.

If you are looking to use the data in Data Commons, please visit
our [API documentation](http://docs.datacommons.org/api/).

## About Data Commons

[Data Commons](https://datacommons.org/) is an Open Knowledge Graph that
provides a unified view across multiple public data sets and statistics.
We've bootstrapped the graph with lots of
[data](https://datacommons.org/datasets) from US Census, CDC, NOAA, etc.,
and through collaborations with the New York Botanical Garden,
Opportunity Insights, and more. However, Data Commons is
meant to be for community, by the community. We're excited to work with you
to make public data accessible to everyone.

To see the extent of data we have today, browse the graph using our
[browser](https://browser.datacommons.org/).


## License

Apache 2.0

## Development

Every data import involves some or all of the following: obtaining the source
data, cleaning the data, and converting the data into one of Meta Content
Framework, JSON-LD, or RDFa format. We ask that you check in all scripts used
in this process, so that others can reproduce and continue your work.

Scripts should go under the top-level `scripts/` directory, depending on the
provenance and dataset.
See [the example](scripts/example_provenance/example_dataset/README.md)
for more detail.

We provide some utility libraries under the top-level `util/` directory. This
includes maps to and from common geographic identifiers, a sharding writer to
break up large output files, a templating library for writing
[StatisticalPopulation](https://schema.org/StatisticalPopulation)s and
[Observation](https://schema.org/Observation)s, and more to come.

### GitHub Development Process

In https://github.com/datacommonsorg/data, click on "Fork" button to fork the repo.

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

## Support

For general questions or issues about importing data into Data Commons,
please open an issue on our [issues](https://github.com/datacommonsorg/data/issues) page. For all other
questions, please send an email to `support@datacommons.org`.

**Note** - This is not an officially supported Google product.

