# DSMS-SDK
Python SDK core-package for interacting with the Dataspace Management System (DSMS)

## Installation

### From PyPI

```{python}
pip install dsms-sdk
```

## From source

```{bash}
git clone git@github.com:MI-FraunhoferIWM/dsms-python-sdk.git
cd dsms-python-sdk
pip install -e .
```

## Usage

The SDK provides a general Python interface to a remote DSMS deployment, allowing users to access, store and link data in a DSMS instance easily and safely. The package provides the following main capabilities:

- Managing Knowledge Items (KItems), which are data instances of an explicitly defined semantic class type (KType)
  - Creating, updating and deleting metadata and properties, e.g. date, operator, material response data for a conducted tensile test
  - Contact information and supplementary information upon making changes or adding KItems
  - Semantic annotation of KItems
  - Attaching semantic schema data (ontology-class instance data) to KItems
- Managing Knowledge Types (KTypes), including the v2 semantic-spec subsystem for defining ontology classes, relations, and schema references
- Role-based access control (RBAC) per KItem: assign users and groups to `MEMBER`, `CONTRIBUTOR`, `OWNER`, or `ADMIN` roles
- Conduct free-text searches within the DSMS instance with filters (KType, annotation, context membership, attachment extension) as well as a full SPARQL interface (including context-scoped queries)
- Linking KItems to other KItems, and grouping them via context KItems
- Linking Apps to KItems, triggered, for example, during a file upload
- Performing simple file upload and download using attachments to KItems
- Export of a knowledge (sub)graph as common serializations (.ttl, .json)


## Documentation

Please have a look at our documentation on _readthedocs_:
https://dsms-python-sdk.readthedocs.io

## Compatibility

Please take the compability of the SDK version with the DSMS version into account:

| SDK Version | DSMS Version |
| --- | --- |
| <2.0.0 | <2.0.0 |
| >=2.0.0, <3.0.0 | >=2.0.0, <3.0.0 |
| >=3.0.0, <3.0.4 | >=3.0.0, <3.0.5 |
| >=3.0.4, <3.1.0 | >=3.0.5, <3.1.0 |
| >=3.1.0, <3.2.2 | >=3.1.0, <3.2.1 |
| >=3.2.2 | >=3.2.1, <4.0.0 |
| >=4.0.0, <5.0.0 | >=4.0.0, <5.0.0 |
| >=5.0.0 | >=5.0.0 |


## Tutorials

Please have a look at our tutorials on _readthedocs_:
* [1. Introduction](https://dsms-python-sdk.readthedocs.io/en/latest/dsms_sdk/tutorials/1_introduction.html)
* [2. Creation](https://dsms-python-sdk.readthedocs.io/en/latest/dsms_sdk/tutorials/2_creation.html)
* [3. Updating](https://dsms-python-sdk.readthedocs.io/en/latest/dsms_sdk/tutorials/3_updating.html)
* [4. Deletion](https://dsms-python-sdk.readthedocs.io/en/latest/dsms_sdk/tutorials/4_deletion.html)
* [5. Search](https://dsms-python-sdk.readthedocs.io/en/latest/dsms_sdk/tutorials/5_search.html)
* [6. Apps](https://dsms-python-sdk.readthedocs.io/en/latest/dsms_sdk/tutorials/6_apps.html)

Or try our Jupyter Notebooks:
* [1. Introduction](docs/dsms_sdk/tutorials/1_introduction.ipynb)
* [2. Creation](docs/dsms_sdk/tutorials/2_creation.ipynb)
* [3. Updating](docs/dsms_sdk/tutorials/3_updating.ipynb)
* [4. Deletion](docs/dsms_sdk/tutorials/4_deletion.ipynb)
* [5. Search](docs/dsms_sdk/tutorials/5_search.ipynb)
* [6. Apps](docs/dsms_sdk/tutorials/6_apps.ipynb)
* [7. KTypes](docs/dsms_sdk/tutorials/7_ktypes.ipynb)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All contributors are listed on the [GitHub contributors page](https://github.com/MI-FraunhoferIWM/dsms-python-sdk/graphs/contributors).

## License

This project is licensed under the BSD 3-Clause. See the LICENSE file for more information.


## Disclaimer

Copyright (c) 2014-2026, Fraunhofer-Gesellschaft zur Förderung der angewandten Forschung e.V. acting on behalf of its Fraunhofer IWM.

Contact: [Matthias Büschelberger](mailto:matthias.bueschelberger@iwm.fraunhofer.de)
