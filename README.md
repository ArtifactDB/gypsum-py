<!-- These are examples of badges you might want to add to your README:
     please update the URLs accordingly

[![Built Status](https://api.cirrus-ci.com/github/<USER>/gypsum-client.svg?branch=main)](https://cirrus-ci.com/github/<USER>/gypsum-client)
[![ReadTheDocs](https://readthedocs.org/projects/gypsum-client/badge/?version=latest)](https://gypsum-client.readthedocs.io/en/stable/)
[![Coveralls](https://img.shields.io/coveralls/github/<USER>/gypsum-client/main.svg)](https://coveralls.io/r/<USER>/gypsum-client)

[![Conda-Forge](https://img.shields.io/conda/vn/conda-forge/gypsum-client.svg)](https://anaconda.org/conda-forge/gypsum-client)

[![Twitter](https://img.shields.io/twitter/url/http/shields.io.svg?style=social&label=Twitter)](https://twitter.com/gypsum-client)
-->

[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)
[![PyPI-Server](https://img.shields.io/pypi/v/gypsum-client.svg)](https://pypi.org/project/gypsum-client/)

# Python client to the gypsum REST API


The `gypsum_client` package provides the Python client to any instance of the [gypsum REST API](https://gypsum.artifactdb.com). This allows client (both in **R** and **Python**) packages to easily store and retrieve resources from the **gypsum** backend.
It also provides mechanisms to allow package maintainers to easily manage upload authorizations and third-party contributions.

Readers are referred to [API's documentation](https://github.com/ArtifactDB/gypsum-worker) for a description of the concepts; this guide will strictly focus on the usage of the `gypsum_client` package.

**Note: check out the R/Bioconductor package for the gypsum REST API [here](https://github.com/ArtifactDB/gypsum-R).**

## Installation

Package is published to [PyPI](https://pypi.org/project/gypsum-client/),

```sh
pip install gypsum_client
```

Check out the [documentation](https://artifactdb.github.io/gypsum-py/) for more information.

<!-- pyscaffold-notes -->

## Note

This project has been set up using PyScaffold 4.5. For details and usage
information on PyScaffold see https://pyscaffold.org/.
