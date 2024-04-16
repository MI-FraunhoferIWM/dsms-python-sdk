# Introduction to DSMS-SDK
## 1.1. Overview

In the dynamic world of Material Science, the introduction of our latest development brings a new way of interaction with our Dataspace Management System (DSMS): The DSMS Python SDK.

What is the DSMS SDK?

SDK stands for Software Development Kit. In our case, it is a Python-based package for the interaction with the DSMS. This means that all fundamental functionalities of the DSMS can be accessed through a Python interface now!

How does the SDK work?

Just install it on your local system via the pip command line interface:

`pip install dsms-sdk`

... and start connecting to your central DSMS instance remotely, e.g. by integrating it into your own Python scripts and packages

Its functionalities:
1. Managing Knowledge-Items.
2. Creating, updating and deleting meta data and properties, e.g. date, operator, material response data for a conducted tensile test.
3. Administrating authorship, contact information and supplementary information.
4. Semantic annotation of K-Items.
5. Conduct simple free-text searches and SPARQL queries.
6. Linking K-Items to other K-Items.
7. Linking Apps to K-Items, triggered, for example, during a file upload.
8. Performing simple file upload and download of file attachments.
9. Export of a knowledge (sub) graph into TTL/JSON-LD.
[Git repo](https://github.com/MI-FraunhoferIWM/dsms-python-sdk)

![dsms-sdk](assets/images/dsms-sdk.jpg)


## 1.2. DSMS
## 1.3. KItems and KTypes

What is K-type?

K-type stands for knowledge type and categorizes types of knowledge instances and what kind of details are relevant for them (as shown in the attached image). It basically describes a concept and its schema.

What is K-item?

K-item stands for knowledge item and represents an individual instance of a k-type following its property schema and functionalities. Knowledge items also capture the concepts of data containers and digital twin.

How is it helpful?

This approach streamlines the schematisation, conceptualization and structurisation of data for various domains and applications. Technically speaking, it builds an ideal base for the integration of data and knowledge into large dataspaces. K-items classify through k-types didactically, support the upscaling of information into knowledge graphs by additional semantic annotations - which are usually mapped by ontologists. K-items and k-types embody the concepts of digital twins and data containers by providing a structured and semantic framework for representing real-world materials and processes in the manufacturing industry.

![DSMS](assets/images/DSMS.jpg)
