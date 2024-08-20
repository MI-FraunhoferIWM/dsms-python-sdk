# DSMS Config Schema

The `Configuration` class for the DSMS Python SDK is designed to handle various settings required to connect and interact with a DSMS instance. This documentation provides a detailed overview of the configurable properties, their types, defaults, and descriptions.


This section describes the configuration properties for the DSMS Python SDK.

## Configuration Fields

| Field Name       | Description                                                                                  | Type                 | Default              | Property Namespace | Required/Optional |
|:----------------:|:--------------------------------------------------------------------------------------------:|:--------------------:|:--------------------:|:------------------:|:-----------------:|
| Host URL         | URL of the DSMS instance to connect.                                                         | AnyUrl               | Not Applicable       | `host_url`           | Required          |
| Request timeout  | Timeout in seconds until the request to the DSMS is timed out.                               | int                  | `120`                   | `request_timeout`    | Optional          |
| SSL verify       | Whether the SSL of the DSMS shall be verified during connection.                             | bool                 | `True`                 | `ssl_verify`         | Optional          |
| Username         | User name for connecting to the DSMS instance                                                | Optional[SecretStr]  | `None`                 | `username`           | Optional          |
| Password         | Password for connecting to the DSMS instance                                                 | Optional[SecretStr]  | `None`                 | `password`           | Optional          |
| Token            | JWT bearer token for connecting to the DSMS instance                                         | Optional[SecretStr]  | `None`                 | `token`              | Optional          |
| Ping DSMS        | Check whether the host is a DSMS instance or not.                                            | bool                 | `True`                 | `ping_dsms`          | Optional          |
| Encoding         | General encoding to be used for reading/writing serializations.                              | str                  | “utf-8”              | `encoding`           | Optional          |
| Datetime format  | Datetime format used in the DSMS instance.                                                   | str                  | “%Y-%m-%dT%H:%M:%S.%f” | `datetime_format`    | Optional          |
| KItem repository       | Repository of the triplestore for KItems in the DSMS                                         | str                  | `knowledge`            | `kitem_repo`         | Optional          |
| SPARQL Object for units | Class and Module specification in order to retrieve the units. | str  | `dsms.`<br>`knowledge.`<br>`semantics.`<br>`units.`<br>`sparql:`<br>`UnitSparqlQuery` | `units_sparql_object`| Optional |
| Individual Slugs | When set to `True`, the slugs of the KItems will receive the first few characters of the KItem-id, when the slug is derived automatically from the KItem-name. | bool | `True` | `individual_slugs` | Optional |
| Display units | Whether the custom properties or the dataframe columns shall directly reveal their unit when printed. WARNING: This might lead to performance issues. | bool | `False` | `display_units` | Optional |
| Autocomplete units | When a unit is fetched but does not hold a symbol next to its URI, it shall be fetched from the respective ontology (which is general side effect from the `units_sparq_object`).<br>WARNING: This might lead to performance issues. | bool | `True` | `autocomplete_units` | Optional |
| QUDT units | URI of the QUDT unit ontology | str | `http://qudt.org/2.1/vocab/unit` | `qudt_units` | Optional |
| QUDT Quantity Kinds | URI of the QUDT quantity kind ontology | str | `http://qudt.org/vocab/quantitykind/` | `qudt_quantity_kinds` | Optional |
| Hide properties | Properties to hide while printing, e.g {'external_links'} | Set[str] | `{}` | `hide_properties` | Optional |
| Log level | Logging level | str | None | `log_level` | Optional |

## Example Usage
```python
from dsms import DSMS


config = DSMS(
    host_url="https://dsms.example.com",
    request_timeout=30,
    ssl_verify=True,
    username="****",
    password="****",
    token=None,
    ping_dsms=True,
    individual_slugs=True,
    encoding="utf-8",
    datetime_format="%Y-%m-%dT%H:%M:%S.%f",
    display_units=False,
    autocomplete_units=True,
    kitem_repo="knowledge-items",
    qudt_units="http://qudt.org/2.1/vocab/unit",
    qudt_quantity_kinds="http://qudt.org/vocab/quantitykind/",
    units_sparql_object="dsms.knowledge.semantics.units.sparql:UnitSparqlQuery",
    hide_properties={"external_links"},
    log_level="INFO",
)

print(dsms.config)
```
