# DSMS-SDK
Python SDK core-package for interacting with the Dataspace Management System (DSMS)


## Authors

[Matthias Büschelberger](mailto:matthias.bueschelberger@iwm.fraunhofer.de) (Fraunhofer Institute for Mechanics of Materials IWM)

[Yoav Nahshon](mailto:yoav.nahshon@iwm.fraunhofer.de) (Fraunhofer Institute for Mechanics of Materials IWM)

[Pablo De Andres](mailto:pablo.de.andres@iwm.fraunhofer.de) (Fraunhofer Institute for Mechanics of Materials IWM)

## License

This project is licensed under the BSD 3-Clause. See the LICENSE file for more information.

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

For the basic usage, please have a look on the Jupyter Notebook under `examples/basic_usage.ipynb`. This tutorial provides a basic overview of using the dsms package to interact with Knowledge Items.


## Disclaimer

Copyright (c) 2014-2024, Fraunhofer-Gesellschaft zur Förderung der angewandten Forschung e.V. acting on behalf of its Fraunhofer IWM.

Contact: [Matthias Büschelberger](mailto:matthias.bueschelberger@iwm.fraunhofer.de)
