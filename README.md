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

- Managing Knowledge-Items (KItems), which are data instances of an explicitly defined semantic class type (KType)
 - Creating, updating and deleting meta data and properties, e.g. date, operator, material response data for a conducted tensile test
 - Administrating authorship, contact information and supplementary information upon making changes or adding KItems
 - Semantic annotation of KItems
- Conduct simple free-text searches within the DSMS instance including filters (e.g. limiting the search for certain materials) as well as a more experts-aware SPARQL interface
- Linking KItems to other KItems
- Linking Apps to KItems, triggererd, for example, during a file upload
- Performing simple file upload and download using attachments to KItems
- Export of a knowledge (sub) graph as common serializations (.ttl, .json)


## Documentation

Please have a look at our documentation on _readthedocs_:
https://dsms-python-sdk.readthedocs.io

## Tutorials

Please have a look at our tutorials on _readthedocs_:
* [1. Introduction](https://dsms-python-sdk.readthedocs.io/en/latest/dsms_sdk/tutorials/1_introduction.html)
* [2. Creation](https://dsms-python-sdk.readthedocs.io/en/latest/dsms_sdk/tutorials/2_creation.html)
* [3. Updation](https://dsms-python-sdk.readthedocs.io/en/latest/dsms_sdk/tutorials/3_updation.html)
* [4. Deletion](https://dsms-python-sdk.readthedocs.io/en/latest/dsms_sdk/tutorials/4_deletion.html)
* [5. Search](https://dsms-python-sdk.readthedocs.io/en/latest/dsms_sdk/tutorials/5_search.html)
* [6. Apps](https://dsms-python-sdk.readthedocs.io/en/latest/dsms_sdk/tutorials/6_apps.html)

Or try our Jupyter Notebooks:
* [1. Introduction](examples/tutorials/1_introduction.ipynb)
* [2. Creation](examples/tutorials/2_creation.ipynb)
* [3. Updation](examples/tutorials/3_updation.ipynb)
* [4. Deletion](examples/tutorials/4_deletion.ipynb)
* [5. Search](examples/tutorials/5_search.ipynb)
* [6. Apps](examples/tutorials/6_apps.ipynb)

## Authors

[Matthias Büschelberger](mailto:matthias.bueschelberger@iwm.fraunhofer.de) (Fraunhofer Institute for Mechanics of Materials IWM)

[Yoav Nahshon](mailto:yoav.nahshon@iwm.fraunhofer.de) (Fraunhofer Institute for Mechanics of Materials IWM)

[Pablo De Andres](mailto:pablo.de.andres@iwm.fraunhofer.de) (Fraunhofer Institute for Mechanics of Materials IWM)

[Priyabrat Mishra](mailto:priyabrat.mishra@iwm.fraunhofer.de) (Fraunhofer Institute for Mechanics of Materials IWM)

## License

This project is licensed under the BSD 3-Clause. See the LICENSE file for more information.


## Disclaimer

Copyright (c) 2014-2024, Fraunhofer-Gesellschaft zur Förderung der angewandten Forschung e.V. acting on behalf of its Fraunhofer IWM.

Contact: [Matthias Büschelberger](mailto:matthias.bueschelberger@iwm.fraunhofer.de)
