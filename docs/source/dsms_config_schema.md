## 4. DSMS Config Schema

The `Configuration` class for the DSMS Python SDK is designed to handle various settings required to connect and interact with a DSMS instance. This documentation provides a detailed overview of the configurable properties, their types, defaults, and descriptions.


This section describes the configuration properties for the DSMS Python SDK.

### Configuration Object Properties

| Field Name       | Description                                                                                  | Type                 | Default              | Property Namespace | Required/Optional |
|:----------------:|:--------------------------------------------------------------------------------------------:|:--------------------:|:--------------------:|:------------------:|:-----------------:|
| host_url         | URL of the DSMS instance to connect.                                                         | AnyUrl               | Not Applicable       | `host_url`           | Required          |
| request_timeout  | Timeout in seconds until the request to the DSMS is timed out.                               | int                  | `30`                   | `request_timeout`    | Optional          |
| ssl_verify       | Whether the SSL of the DSMS shall be verified during connection.                             | bool                 | `True`                 | `ssl_verify`         | Optional          |
| username         | User name for connecting to the DSMS instance                                                | Optional[SecretStr]  | `None`                 | `username`           | Optional          |
| password         | Password for connecting to the DSMS instance                                                 | Optional[SecretStr]  | `None`                 | `password`           | Optional          |
| token            | JWT bearer token for connecting to the DSMS instance                                         | Optional[SecretStr]  | `None`                 | `token`              | Optional          |
| ping_dsms        | Check whether the host is a DSMS instance or not.                                            | bool                 | `True`                 | `ping_dsms`          | Optional          |
| encoding         | General encoding to be used for reading/writing serializations.                              | str                  | “utf-8”              | `encoding`           | Optional          |
| datetime_format  | Datetime format used in the DSMS instance.                                                   | str                  | “%Y-%m-%dT%H:%M:%S.%f” | `datetime_format`    | Optional          |
| kitem_repo       | Repository of the triplestore for KItems in the DSMS                                         | str                  | `knowledge`            | `kitem_repo`         | Optional          |

#### Example Usage
```python
from dsms.configuration import Configuration
from pydantic import SecretStr

config = Configuration(
    host_url="https://dsms.example.com",
    request_timeout=30,
    ssl_verify=True,
    username=SecretStr("your_username"),
    password=SecretStr("your_password"),
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
    hide_properties={"external_links"}
)

print(config)
```


> **Reminder Tip**
>
> As discussed in previous section in DSMS SDK section (refer to the [Accessing DSMS Core](dsms_sdk.md#accessing-dsms-core)) for accessing DSMS core, you either need to pass during initialization:
>
> `username` and `password`
>
> OR
>
> `token`
