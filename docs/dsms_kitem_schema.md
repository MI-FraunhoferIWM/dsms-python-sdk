## 3. DSMS KItem Schema

A Kitem has several properties which enable it to handle data effectively. This section briefly describes the properties a Kitem can consist of, or in simple words, the schema of a KItem.

The schema contains complex types and references, indicating an advanced usage scenario where various objects (like KItems and their properties) are interconnected. It also includes customizations like optional and default values, arrays of references, and conditional formats (e.g., UUID formats).

The KItem object has the following properties

### Kitem Object Properties

![kitem_schema_uml](assets/images/UML_KItem_schema.jpg)

| Field Name        | Description                                                                                              | Type                                              | Default  | Property Namespace | Required / Optional |
|:-----------------:|:--------------------------------------------------------------------------------------------------------:|:-------------------------------------------------:|:--------:|:------------------:|:-----------------:|
| Name              | Human-readable name of the KItem.                                                                       | string                                               | Not Applicable | `name`             | Required          |
| Slug              | A unique slug identifier for the KItem, minimum of 4 characters.                                        | string                                               | `None`   | `slug`             | Optional          |
| Ktype ID          | The type ID of the KItem                                                                                | Union[Enum, string]                                  | Not Applicable | `ktype_id`         | Required          |
| Created At        | Timestamp of when the KItem was created.                                                                | Union[string, datetime]                              | `None`   | `created_at`       | Automatically generated          |
| Updated At        | Timestamp of when the KItem was updated.                                                                | Union[string, datetime]                              | `None`   | `updated_at`       | Automatically generated          |
| Avatar Exists     | Whether the KItem holds an avatar or not.                                                               | boolean                                              | `False`  | `avatar_exists`    | Automatically generated          |
| Custom Properties | A set of custom properties related to the KItem.                                                        | Any                                               | `{}`     | `custom_properties`| Optional          |
| Summary           | A brief human-readable summary of the KItem                                                             | Union[string, [Summary](#summary-properties)]                               | `None`   | `summary`          | Optional          |
| KItem Apps        | A list of applications associated with the KItem                                                        | List[[App](#app-properties)]                                         | `[ ]`    | `kitem_apps`       | Optional          |
| Annotations       | A list of annotations related to the KItem                                                              | List[[Annotation](#annotation-properties)]                                  | `[ ]`    | `annotations`      | Optional          |
| Affiliations      | A list of affiliations associated with the KItem                                                        | List[[Affiliation](#affiliation-properties)]                                 | `[ ]`    | `affiliations`     | Optional          |
| Authors           | A list of authors related to the KItem                                                                  | List[Union[[Author](#author-properties), string]]                          | `[ ]`    | `authors`          | Optional          |
| Contacts          | Contact information related to the KItem                                                                | List[[ContactInfo](#contactinfo-properties)]                                 | `[ ]`    | `contacts`         | Optional          |
| External Links    | A list of external links related to the KItem                                                           | List[[ExternalLink](#externallink-properties)]                                | `[ ]`    | `external_links`   | Optional          |
| Attachments       | A list of file attachments associated with the KItem                                                    | List [ Union [[Attachment ](#attachment-properties)], string]                      | `[ ]`    | `attachments`      | Optional          |
| Hdf5              | HDF5 data structure associated with the KItem                                                           | Union[List[[Column](#column-properties)], pd.DataFrame, Dictionary[string, Union[List, Dictionary]]] | `None`   | `hdf5`             | Optional          |
| Linked KItems     | List of other KItems linked to this KItem                                                               | List[Union[[LinkedKItem](#linkedkitem-properties), "KItem"]]                 | `None`   | `linked_kitems`    | Optional          |
| User Groups       | User groups with access to this KItem                                                                   | List[[UserGroup](#usergroup-properties)]                                   | `[ ]`    | `user_groups`      | Optional          |

#### Example Usage
```python

item = KItem(
    name="Glass Bending machine 01",
    slug="1234",
    ktype_id="Testing Machine",
    custom_properties={"location": "Room01", "max_force": "100Pa"},
    summary={"text": "This is a summary", "author": "John Doe"},
    kitem_apps=[{"executable": "tensile_analysis.py", "description": "analysis the tensile strength from machine data"}],
    annotations=[{"iri": "http://example.org/sample_kitem/annotation"}],
    affiliations=[{"name": "Fraunhofer IWM"}],
    authors=[{"user_id": "Tom Brown"}],
    contacts=[{"name": "John Doe", "email": "john.doe@example.com"}],
    external_links=[{"label": "Project Website", "url": "https://example.com"}],
    attachments=["research_data.csv"],
    linked_kitems=[{"id": "{kitem_id_of_present}", "source_id": "{kitem_id_of_source}"}],
    user_groups=[{"group_id": "{other_kitem_id}", "name": "DigiMaterials"}]
)
```

### Summary Properties

| Sub-Property Name | Description                       | Type     | Default | Property Namespace | Required/Optional |
|:-----------------:|:---------------------------------:|:--------:|:-------:|:------------------:|:-----------------:|
| Text              | Summary                           | string      | `None`  | `text`             | Required          |
| Author            | Author of the summary             | string      | `None`  | `author`           | Required          |

#### Example Usage
```python
sample_kitem.summary = {"text": "This is a summary", "author": "John Doe"}
```

### App Properties

| Sub-Property Name | Description                       | Type     | Default | Property Namespace | Required/Optional |
|:-----------------:|:---------------------------------:|:--------:|:-------:|:------------------:|:-----------------:|
| Executable        | Name of the executable            | string      | `None`  | `executable`       | Required          |
| Description       | Description of the application    | string      | `None`  | `description`     |Required          |

#### Example Usage
```python
sample_kitem.summary = {"executable": "unit_conversion.py", "description": "converting input to different units"}
```

### Annotation Properties

| Sub-Property Name | Description                       | Type     | Default | Property Namespace | Required/Optional |
|:-----------------:|:---------------------------------:|:--------:|:-------:|:------------------:|:-----------------:|
| IRI               | IRI of the annotation             | string      | `None`  | `iri`              | Required          |
| Name              | Name of the annotation            | string      | `None`  | `name`             | Required          |
| Namespace         | Namespace of the annotation       | string      | `None`  | `namespace`        | Required          |

#### Example Usage
```python
sample_kitem.annotation = {"iri": "1238.py", "name": "","namespace":""}
```

### Affiliation Properties

| Sub-Property Name | Description                       | Type     | Default | Property Namespace | Required/Optional |
|:-----------------:|:---------------------------------:|:--------:|:-------:|:------------------:|:-----------------:|
| Name              | Name of the affiliation           | string      | `None`  | `name`             | Required          |

#### Example Usage
```python
sample_kitem.affiliation = {"name": "Research BAC"}
```

### Author Properties

| Sub-Property Name | Description                       | Type          | Default | Property Namespace | Required/Optional |
|:-----------------:|:---------------------------------:|:-------------:|:-------:|:------------------:|:-----------------:|
| User Id           | ID of the DSMS User               | string (UUID)     | `None`  | `user_id`          | Required          |

#### Example Usage
```python
sample_kitem.author = {"user_id": "1238"}
```

### ContactInfo Properties

| Sub-Property Name | Description                       | Type          | Default | Property Namespace | Required/Optional |
|:-----------------:|:---------------------------------:|:-------------:|:-------:|:------------------:|:-----------------:|
| Email             | Email of the contact person       | string           | `None`  | `email`            | Required          |
| Name              | Name of the contact person        | string           | `None`  | `name`             | Required          |
| User Id           | User ID of the contact person     | string (UUID)     | `None`  | `user_id`          | Optional          |

#### Example Usage
```python
sample_kitem.contactinfo = {"email": "research.abc@gmail.com","name": "project01@research.abc.de","user_id":"33f24ee5-2f03-4874-854d-388af782c4c3"}
```

### ExternalLink Properties

| Sub-Property Name | Description                       | Type                       | Default | Property Namespace | Required/Optional |
|:-----------------:|:---------------------------------:|:--------------------------:|:-------:|:------------------:|:-----------------:|
| Label             | Label of the external link        | string                        | `None`  | `label`            | Required          |
| Url               | URL of the external link          | string , format: URI, minLength: 1 | `None`  | `url`              | Required          |

#### Example Usage
```python
sample_kitem.externallink = {"label": "project link","url": "www.projectmachine01.com"}
```


### Attachment Properties

| Sub-Property Name | Description                       | Type     | Default | Property Namespace | Required/Optional |
|:-----------------:|:---------------------------------:|:--------:|:-------:|:------------------:|:-----------------:|
| Name              | File name of the attachment       | string      | `None`  | `name`             | Required          |

#### Example Usage
```python
sample_kitem.attachment = {"strength.csv": "strength test results data"}
```


### Column Properties

| Sub-Property Name | Description                       | Type     | Default | Property Namespace | Required/Optional |
|:-----------------:|:---------------------------------:|:--------:|:-------:|:------------------:|:-----------------:|
| Name              | File name of the attachment       | string      | `None`  | `name`             | Required          |

#### Example Usage
```python
sample_kitem.contactinfo = {"email": "research.abc@gmail.com","name": "project01@research.abc.de","user_id":"33f24ee5-2f03-4874-854d-388af782c4c3"}
```


### LinkedKItem Properties

| Sub-Property Name | Description                       | Type          | Default | Property Namespace | Required/Optional |
|:-----------------:|:---------------------------------:|:-------------:|:-------:|:------------------:|:-----------------:|
| Id                | ID of the KItem to be linked      | string (UUID)     | `None`  | `id`               | Required          |
| Source Id         | Source Id of the KItem which has been linked | string (UUID)     | `None`  | `source_id`        | Required          |

#### Example Usage
```python
sample_kitem.linkedKItem = {"id": "33305","source_id": "22205"}
```

### UserGroup Properties

| Sub-Property Name | Description                       | Type          | Default | Property Namespace | Required/Optional |
|:-----------------:|:---------------------------------:|:-------------:|:-------:|:------------------:|:-----------------:|
| Id                | KItem ID related to the KItem property | string (UUID)     | `None`  | `id`               | Required          |
| Group Id          | ID of the user group              | string           | `None`  | `group_id`         | Required          |
| Name              | Name of the user group            | string           | `None`  | `name`             | Required          |

#### Example Usage
```python
sample_kitem.linkedKItem = {"id": "33305","source_id": "22205"}
```