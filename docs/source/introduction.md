# Introduction to DSMS-SDK
## 1.1. Overview

In the dynamic world of Material Science, the introduction of our latest development brings a new way of interaction with our Dataspace Management System (DSMS): The DSMS Python SDK.

What is the DSMS SDK?

SDK stands for Software Development Kit. In our case, it is a Python-based package for the interaction with the DSMS. This means that all fundamental functionalities of the DSMS can be accessed through a Python interface now!

How does the SDK work?

Just install it on your local system via the pip command line interface:

`pip install dsms-sdk`

... and start connecting to your central DSMS instance remotely, e.g. by integrating it into your own Python scripts and packages

The SDK functionalities are listed below:
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

DSMS (acronym for Dataspace Management System) by Fraunhofer is a web-based application that manages heterogeneous data and features semantic and analytical capabilities.

### 1.2.1. Introduction

DSMS platform promotes and enables the provenance and catalogization of data through a combintation of classical relational databases and semantic technologies. By enabling the interoperabilty to third party data sources, Fraunhofer IWM demonstrates this though particular use cases in material science and manufacturing in public research projects for industry 4.0.

![DSMS_Intro](assets/images/dsms_picture_01.jpg)


### 1.2.2. KItems and KTypes

What is K-type?

K-type stands for knowledge type and categorizes types of knowledge instances and what kind of details are relevant for them (as shown in the attached image). It basically describes a concept and its schema.

What is K-item?

K-item stands for knowledge item and represents an individual instance of a k-type following its property schema and functionalities. Knowledge items also capture the concepts of data containers and digital twin.

How is it helpful?

This approach streamlines the schematisation, conceptualization and structurisation of data for various domains and applications. Technically speaking, it builds an ideal base for the integration of data and knowledge into large dataspaces. K-Items classify through K-Types didactically, support the upscaling of information into knowledge graphs by additional semantic annotations - which are usually mapped by ontologists. 

K-Items and K-Types embody the concepts of digital twins and data containers by providing a structured and semantic framework for representing real-world materials and processes in the manufacturing industry.

![DSMS](assets/images/DSMS.jpg)

### 1.2.3. Kitem Properties

A Kitem has several properties to enable to handle data effectively. This section briefly describes the properties a Kitem can consist or in simple words the schema of a K-item.  

The schema contains complex types and references, indicating an advanced usage scenario where various objects (like KItems and their properties) are interconnected. It also includes customizations like optional and default values, arrays of references, and conditional formats (e.g., UUID formats).

For the DSMS, Pydantic has been used extensively. Pydantic is a Python library that leverages type annotations for data validation and settings management. It ensures that data conforms to predefined schemas by validating or serializing it at runtime and thus facilitates strict type checking and data integrity.

Below given is the details of the schema of a Kitem for better understanding:

- **AdditionalProperties**: Defines extra, non-standard properties that can be associated with an application. It includes properties like `triggerUponUpload` (a boolean indicating if the app should trigger when a file is uploaded) and `triggerUponUploadFileExtensions` (an array or null defining file extensions for which the upload should be triggered).
- **Affiliation**: Represents the affiliation of a KItem, including identifiers and names. It requires the `name` property.
- **Annotation**: Details annotations related to a KItem, with fields like `iri`, `name`, and `namespace`, all of which are required.
- **App**: Describes an application associated with a KItem, featuring details such as an executable name and additional properties. The `executable` field is mandatory.
- **Attachment**: Defines an attachment, requiring the `name` field and including an identifier.
- **Author**: Specifies an author of a KItem, with a required `userId` indicating the author's user ID.
- **Column**: Represents a column in an HDF5 data frame, requiring both `columnId` and `name`.
- **ContactInfo**: Provides contact information including an email and name, both required.
- **ExternalLink**: Details an external link related to a KItem, requiring `label` and `url`.
- **KItem**: The central model for a Knowledge Item, with comprehensive properties like `affiliations`, `annotations`, `attachments`, and more. Key fields like `name` and `ktype_id` are mandatory.
- **KType**: Describes the type of knowledge contained in a KItem, with necessary fields such as `id`.
- **LinkedKItem**: Models a KItem that is linked to another, requiring identifiers for both the linked item and its source.
- **Summary**: Provides a summary model for KItems, requiring a `text` field.
- **UserGroup**: Specifies user groups related to a KItem, requiring `name` and `groupId`.