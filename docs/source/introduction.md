# Introduction to DSMS-SDK
## 1.1. Overview

In the dynamic world of Material Science, the introduction of our latest development brings a new way of interaction with our Dataspace Management System (DSMS): The DSMS Python SDK.

**What is the DSMS SDK?**

SDK stands for Software Development Kit. In our case, it is a Python-based package for the interaction with the DSMS. This means that all fundamental functionalities of the DSMS can be accessed through a Python interface now!

**How does the SDK work?**

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

**What is K-type?**

K-type stands for knowledge type and categorizes types of knowledge instances and what kind of details are relevant for them (as shown in the attached image). It basically describes a concept and its schema.

**What is K-item?**

K-item stands for knowledge item and represents an individual instance of a k-type following its property schema and functionalities. Knowledge items also capture the concepts of data containers and digital twin.

**How is it helpful?**

This approach streamlines the schematisation, conceptualization and structurisation of data for various domains and applications. Technically speaking, it builds an ideal base for the integration of data and knowledge into large dataspaces. K-Items classify through K-Types didactically, support the upscaling of information into knowledge graphs by additional semantic annotations - which are usually mapped by ontologists.

K-Items and K-Types embody the concepts of digital twins and data containers by providing a structured and semantic framework for representing real-world materials and processes in the manufacturing industry.

![DSMS](assets/images/DSMS.jpg)

### 1.2.3. Kitem Properties

A Kitem has several properties to enable to handle data effectively. This section briefly describes the properties a Kitem can consist or in simple words the schema of a K-item.

The schema contains complex types and references, indicating an advanced usage scenario where various objects (like KItems and their properties) are interconnected. It also includes customizations like optional and default values, arrays of references, and conditional formats (e.g., UUID formats).

For the DSMS, Pydantic has been used extensively. Pydantic is a Python library that leverages type annotations for data validation and settings management. It ensures that data conforms to predefined schemas by validating or serializing it at runtime and thus facilitates strict type checking and data integrity.

Below given is the details of the schema of a Kitem for better understanding:

### 1.2.3. Kitem Properties

A Kitem has several properties to enable to handle data effectively. This section briefly describes the properties a Kitem can consist or in simple words the schema of a K-item.

The schema contains complex types and references, indicating an advanced usage scenario where various objects (like KItems and their properties) are interconnected. It also includes customizations like optional and default values, arrays of references, and conditional formats (e.g., UUID formats).

For the DSMS, Pydantic has been used extensively. Pydantic is a Python library that leverages type annotations for data validation and settings management. It ensures that data conforms to predefined schemas by validating or serializing it at runtime and thus facilitates strict type checking and data integrity.

Below given is the details of the schema of a Kitem for better understanding:


# DSMS Schema Documentation

**Note:** This documentation covers the various components within the DSMS schema, focusing on the properties, types, and roles of different objects.

## Definitions

### General Definitions

All IDs are typically of the type `UUID` unless specified otherwise. Each entity defined within the system has an associated ID which is automatically generated.

### 1. KItem

**Description:** Represents a Knowledge Item within the DSMS system.

**Required Fields:** `name`, `ktype_id`

#### KItem Properties

1.1. **Name**
- **Description:** Human-readable name of the KItem.
- **Type:** string
- **Default:** -

1.2. **Slug**
- **Description:** A unique slug identifier for the KItem, minimum of 4 characters.
- **Type:** string, MinLength: 4
- **Default:** None

1.3. **Ktype_id**
- **Description:** The type ID of the KItem.
- **Type:** string or enumeration
- **Default:** -

1.4. **Created_at**
- **Description:** Timestamp of when the KItem was created.
- **Type:** string, format: date-time
- **Default:** None

1.5. **Updated_at**
- **Description:** Timestamp of when the KItem was last updated.
- **Type:** string, format: date-time
- **Default:** None

1.6. **Summary**
- **Description:** A brief human-readable summary of the KItem.
- **Type:** string or summary object
- **Default:** None

1.7. **Avatar_exists**
- **Description:** Indicates whether the KItem has an avatar image associated with it.
- **Type:** boolean
- **Default:** False

1.8. **Custom_properties**
- **Description:** A set of custom properties related to the KItem.
- **Type:** object
- **Default:** {}

1.9. **Kitem_apps**
- **Description:** A list of applications associated with the KItem.
- **Type:** array of App objects
- **Default:** []

1.10. **Annotations**
- **Description:** A list of annotations related to the KItem.
- **Type:** array of Annotation objects
- **Default:** []

1.11. **Affiliations**
- **Description:** A list of affiliations associated with the KItem.
- **Type:** array of Affiliation objects
- **Default:** []

1.12. **Authors**
- **Description:** A list of authors related to the KItem.
- **Type:** array of Author objects
- **Default:** []

1.13. **Contacts**
- **Description:** Contact information related to the KItem.
- **Type:** array of ContactInfo objects
- **Default:** []

1.14. **External_links**
- **Description:** A list of external links related to the KItem.
- **Type:** array of ExternalLink objects
- **Default:** []

1.15. **Attachments**
- **Description:** A list of file attachments associated with the KItem.
- **Type:** array of Attachment objects or strings
- **Default:** []

1.16. **Hdf5**
- **Description:** HDF5 data structure associated with the KItem.
- **Type:** array of Column objects or object
- **Default:** None

1.17. **Linked_kitems**
- **Description:** List of other KItems linked to this KItem.
- **Type:** array of LinkedKItem or KItem objects
- **Default:** []

1.18. **User_groups**
- **Description:** User groups with access to this KItem.
- **Type:** array of UserGroup objects
- **Default:** []

### 2. App

**Description:** Represents an application associated with a KItem.

**Required Fields:** `executable`

#### App Properties

2.1. **Executable**
- **Description:** Name of the executable related to the app.
- **Type:** string
- **Default:** -

2.2. **Description**
- **Description:** Description of the application.
- **Type:** string or null
- **Default:** None

2.3. **KitemAppId**
- **Description:** ID of the KItem App.
- **Type:** integer or null
- **Default:** None

2.4. **Tags**
- **Description:** Tags related to the application.
- **Type:** object or null
- **Default:** None

2.5. **Title**
- **Description:** Title of the application.
- **Type:** string or null
- **Default:** None

2.6. **Additional Properties**
- **Description:** Additional properties related to the application.
- **Type:** Refers to `AdditionalProperties`
- **Default:** None

### 3. Affiliation

**Description:** Represents an affiliation associated with a KItem.

**Required Fields:** `Name`

#### Affiliation Properties

3.1. **Name**
- **Description:** Name of the affiliation.
- **Type:** string
- **Default:** -

### 4. Annotation

**Description:** Represents an annotation within a KItem.

**Required Fields:** `iri`, `name`, `namespace`

#### Annotation Properties

4.1. **Iri**
- **Description:** IRI of the annotation.
- **Type:** string
- **Default:** -

4.2. **Name**
- **Description:** Name of the annotation.
- **Type:** string
- **Default:** -

4.3. **Namespace**
- **Description:** Namespace of the annotation.
- **Type:** string
- **Default:** -

### 5. Attachment

**Description:** Represents a file attachment uploaded by a certain user.

**Required Fields:** `name`

#### Attachment Properties

5.1. **Name**
- **Description:** File name of the attachment.
- **Type:** string
- **Default:** -

### 6. Author

**Description:** Represents an author of a KItem.

**Required Fields:** `UserID`

#### Author Properties

6.1. **UserId**
- **Description:** ID of the DSMS User.
- **Type:** string (UUID)
- **Default:** -

### 7. Column

**Description:** Represents a column of an HDF5 data frame.

**Required Fields:** `ColumnId`, `Name`

#### Column Properties

7.1. **ColumnId**
- **Description:** Column ID in the data frame.
- **Type:** integer
- **Default:** -

7.2. **Name**
- **Description:** Name of the column in the data series.
- **Type:** string
- **Default:** -

### 8. ContactInfo

**Description:** Contact information for a person or entity.

**Required Fields:** `name`, `email`

#### ContactInfo Properties

8.1. **Email**
- **Description:** Email of the contact person.
- **Type:** string
- **Default:** -


8.2. **Name**
- **Description:** Name of the contact person.
- **Type:** string
- **Default:** -

8.3. **UserId**
- **Description:** User ID of the contact person.
- **Type:** string (UUID) or null
- **Default:** None

### 9. ExternalLink

**Description:** Represents an external link of a KItem.

**Required Fields:** `label`, `Url`

#### ExternalLink Properties

9.1. **Label**
- **Description:** Label of the external link.
- **Type:** string
- **Default:** -

9.2. **Url**
- **Description:** URL of the external link.
- **Type:** string, format: uri, minLength: 1
- **Default:** -

### 10. LinkedKItem

**Description:** Data model for a linked KItem.

**Required Fields:** None

#### LinkedKItem Properties

10.1. **Id**
- **Description:** ID of the KItem to be linked.
- **Type:** string (UUID) or null
- **Default:** None

10.2. **SourceId**
- **Description:** Source ID of the KItem.
- **Type:** string (UUID) or null
- **Default:** None

### 11. Summary

**Description:** Model for the custom properties of the KItem.

**Required Fields:** `text`

#### Summary Properties

11.1. **Id**
- **Description:** KItem ID.
- **Type:** string (UUID) or null
- **Default:** None

11.2. **Kitem**
- **Description:** KItem related to the summary.
- **Type:** null or object
- **Default:** None

11.3. **Text**
- **Description:** Summary text of the KItem.
- **Type:** string
- **Default:** -

### 12. UserGroup

**Description:** User groups related to a KItem.

**Required Fields:** `GroupId`, `name`

#### UserGroup Properties

12.1. **GroupId**
- **Description:** ID of the user group.
- **Type:** string
- **Default:** -

12.2. **Id**
- **Description:** KItem ID related to the KPropertyItem.
- **Type:** string (UUID) or null
- **Default:** None

12.3. **Name**
- **Description:** Name of the user group.
- **Type:** string
- **Default:** -
