# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [5.0.0] - 2026-11-25

### Breaking changes

- KType forms are now plain specs: `KType.webform_schema` and `KType.webform_schema_id` are removed in favour of the dict `KType.custom_properties`. The `WebformSchema` model and `DSMS.webform_schemas` are removed, and webform schemas can no longer be committed.
- `KItem.user_groups` is removed (the value is silently ignored when passed) and `UserGroup` is no longer exported from `dsms.knowledge.properties`. Use `KItem.access_properties` instead.
- Python 3.10 or newer is required (3.8 and 3.9 are no longer supported).

### Added

**Access control (RBAC)**
- `KItem.access_properties: Optional[KItemAccessProperties]` with a `visibility` (`"restricted"` (default), `"internal"` or `"public"`) and a list of `grants: List[AccessGrant]`.
- `AccessGrant` model (`id`, `type` = `"user"` or `"group"`, `role`) with an `access_level` property listing the granted operations. Duplicate `(id, type)` grants are rejected.
- `KItemAccessProperties.by_id`, `by_role` and `operation_by_principal` lookups.
- `Role` enum (`MEMBER=1`, `CONTRIBUTOR=2`, `OWNER=3`) and `OperationType` enum (`create`, `read`, `update`, `delete`, `manage`). Roles accept names (`"owner"`) or integers as input and serialize as lowercase strings in JSON (`"member"`, `"contributor"`, `"owner"`).
- `RoleMapping` enum with `get_operations`, `min_access_level` and `max_access_level`. The last two return a `Role` and raise `ValueError` for operations no role grants (e.g. `CREATE`).
- Access properties are sent when a KItem is created, and changes to them are committed on update. Only fields you set are sent, so changing just the `visibility` keeps the existing grants.
- The access models live in `dsms.knowledge.properties.access`; `KItemAccessProperties` is also exported from `dsms.knowledge.properties`.

**Users and groups**
- `dsms.knowledge.groups` module with `User` (`id`, `username`, optional `firstName`, `lastName`, `email`, `user_groups`), `UserList` (`by_id`, `by_username`), `BaseGroup`, `Group` (with nested `subgroups`) and `GroupList` (`flat`, `by_id`, `by_name`).
- `DSMS.users` and `DSMS.user_groups` cached properties with `refresh_users()` / `refresh_user_groups()`.
- `DSMS.get_user(user_id)`, also available as `dsms.knowledge.utils.get_user_by_id(dsms, user_id)`.
- Group management on `DSMS`: `create_group(name, description="", parent_id=None)`, `update_group`, `delete_group`, `get_group_members`, `add_group_member`, `remove_group_member`.
- Nested groups on `DSMS`: `get_group_subgroups`, `add_group_to_group`, `remove_group_from_group`.

**KType semantic specs**
- `KType.custom_properties`: the custom properties spec (sections with inputs, camelCase keys) used to validate and convert KItem custom properties.
- `KTypeSpec` model capturing the full semantic spec of a KType: ontology classes, relations, semantic schema references (own and inherited via `resolved_ontology_classes` / `resolved_semantic_schemas`), inheritance, context settings, tags, versioning and stash state.
- Sub-models: `OntologyClassSpec`, `SemanticSchemaRef`, `RelationSpec`.
- `KTypeV2(KType)` response model with an optional `spec: KTypeSpec` field.
- Request models: `CreateKTypeRequest`, `KTypeSpecPayload`.
- All of these models are exported from `dsms.knowledge`.
- KType spec methods on `DSMS`: `list_ktypes`, `get_ktype`, `get_ktype_spec`, `create_ktype`, `update_ktype_spec`, `delete_ktype`, `restore_ktype_stash`, `export_ktype`. Importing KTypes from git repositories is done through the git sources of knowledge-type-service and isn't wrapped by the SDK yet.
- `DSMS.get_ktypes_by_parent(parent_id)` returns the KTypes that extend the given KType.

**Schema data on KItems**
- `KItemSchemaData` model (`schema_id`, `content`) and `KItemSchemaDataList` helper with `.by_schema_id` lookup.
- `KItem.schema_data: Optional[List[KItemSchemaData]]` field. It also accepts a `{schema_id: input_data}` dict, which is passed through `populate_schema` when the KItem is created.
- `KItem.populate_schema(schema_id, input_data)` looks up the schema in the KType spec, applies the schema's simplified input transform if it has one, and stores the result as form content (`sections` / `entries`) in `schema_data`. KItem IRIs are resolved to KItem references and vocabulary fields to vocabulary terms. Raises `ValueError` if the KType has no spec or does not list the schema.
- `schema_to_webform(schema_url, input_data, dsms=None)` and `schema_to_oold(schema_url, input_data)` in `dsms.knowledge.semantics`.
- `DSMS.get_schema_data(kitem_id)`.
- Committing a KItem whose `schema_data` is not `None` creates, updates and deletes entries via `PUT`/`DELETE` on `api/knowledge/kitems/{kitem_id}/schema-data/{schema_id}`.

**DSMS archives**
- `DSMS.export_kitems(kitem_ids, path=None, include_context_members=False, include_linked=False)` saves the KItems as a `.dsms.zip` archive and returns its path. KItems pulled in by the include options that you cannot read are left out with a warning.
- `DSMS.import_kitems(path, on_conflict="fail", dry_run=False)` imports an archive; `on_conflict` is `"fail"`, `"skip"` or `"replace"`. Returns an `ArchiveImportReport` (`dsms.knowledge.archive`). If any KItem has an error nothing is written, `ok` is `False` and `all_errors` lists the reasons.

**Context SPARQL**
- `SparqlInterface.query_context(context_id, query)`: `POST /api/knowledge/sparql/context`.
- `SparqlInterface.graph_context(context_id, query)`: `POST /api/knowledge/graph/context`.

**Search and list additions**
- `DSMS.search()` gains `contexts: List[str]` (filter by context KItem IDs), `attachment_extensions: List[str]` (filter by file extension) and `visibility` (`"restricted"`, `"internal"` or `"public"`).
- `DSMS.get_kitems()` gains the keyword-only filters `user_id` and `name` (substring match); `limit` and `offset` keep their positions.

**KItemCompactedModel additions**
- `has_contexts: bool`: whether the KItem belongs to at least one context.
- `attachment_extensions: Optional[List[str]]`: unique file extensions in the KItem's attachments.
- `avatar_exists` moved from `KItem` to the shared `KItemCompactedModel` base.

**Custom properties and process schemas**
- `Widget` enum gains `ARRAY_GROUP`, `DATE`, `DATETIME` (`"Date-time"`, `"Datetime"` is accepted too), `KEY_VALUE_PAIRS`, `LATEX`, `STAR_RATING`, `URL` and `VOCABULARY_SELECT`.
- `Date` and `Date-time` entries accept strings or `date` / `datetime` values.
- `Input.vocabulary_url` for vocabulary select inputs. In the semantic mapping, `Vocabulary select` values are mapped as IRIs, like knowledge item references.
- `ProcessSchemaSpec` gains `required` and `cardinality` (`"one"` or `"many"`).

### Changed

- Custom properties are validated against `KType.custom_properties`, and flat custom property dicts are converted using it (previously the webform schema).
- `KItemSearchResult.fuzzy` can be the string `"id"` when a KItem was found by exact UUID match.
- `to_kebab_case` replaces every run of non-alphanumeric characters with `_` (previously spaces with `-`). This changes the property locations in mappings generated by `generate_mapping`.
- `KItem.created_at` and `updated_at` are typed `Optional[datetime]` and parsed by pydantic.

### Deprecated

- `KItem.authors`: the server no longer populates this field. Use `access_properties` instead.
- `KItem.rdf_exists`: the server no longer populates this field.

### Removed

- `KType.webform_schema`, `KType.webform_schema_id`, the `WebformSchema` model (also from the `dsms` and `dsms.knowledge` exports) and `DSMS.webform_schemas`.
- `KItem.user_groups` and the `UserGroup` export from `dsms.knowledge.properties`.

### Fixed

- Username and password login sends base64-encoded Basic credentials.
- KItems whose KType is missing from the locally cached KTypes (e.g. on instances with many KTypes) fetch the KType on demand instead of raising `TypeError`.
- `KItem.avatar.download()` works again.
- KItem timestamps with a trailing `Z` are parsed.
- Unit lookup for dataframe columns and custom properties (`get_unit()`, `convert_to()`) works with the current knowledge graph format and with property names containing spaces or parentheses.
- Select, radio and multi-select custom properties without select options raise a clear `ValueError` instead of an `AttributeError`.
- Custom properties are validated against the KType's form again: select options, default values, ranges and measurement units come from the spec.
- KItems with the newer widgets (`URL`, `LaTeX`, `Star rating`, `Vocabulary select`, `Key-value pairs`, `Array group`) validate instead of raising "Widget type is not mapped to a data type". Without strict validation, unknown widgets are accepted with a warning.
- Updating a KItem sends its grants only when they changed, so contributors can edit KItems they can't manage, and grant changes made meanwhile aren't overwritten. Grants appended to a new `KItemAccessProperties` are sent too.
- Committing a KType no longer fails when refreshing it afterwards, and a fetched KType with a process schema no longer creates that schema again (`process_schema_id` is taken from the nested schema).
- KType IDs and names may be up to 100 characters, as in the backend.

### Maintenance

- New dependency `semantic-schemas>=0.7`. It brings in `jsonata-python`, which `populate_schema` needs for simplified input transforms, as well as `pyshacl` and `pyyaml`.
- Supported Python versions are 3.10 to 3.14.
- Relaxed dependency pins: `pydantic>=2,<3`, `rdflib>=6,<8`, `pandas>=2,<4`, `segno>=1.6,<2`, `pydantic-settings>=2,<3`, `oyaml>=1`.
- Upgraded pre-commit hooks (`pre-commit-hooks` v6, `black` 26, `isort` 8, `setup-cfg-fmt` v3, `bandit` 1.9.4) and `pylint` 3.3.9; aligned `isort` with `black`'s 79-character line length.
- `pytest-nbmake` moved to the `docs` extras; documentation and tutorial notebooks refreshed, with a new semantic schemas tutorial.

---

## [4.0.0]

### Added

- Pydantic v2 migration (`BaseModel`, `field_validator`, `field_serializer`, `model_dump`).
- Service-account authentication via `client_id` / `client_secret` (Keycloak).
- `KItemAccessProperties` groundwork, `UserGroup` model.
- `AppConfig` and `DSMS.apps` for managing application configurations.
- `ProcessSchema` and `WebformSchema` models on `KType`.

### Changed

- Minimum Python version raised to 3.10.
- `KType.id` accepts both `UUID` and `str`.
- `Configuration` uses `pydantic-settings` for environment-variable loading.

---

## [3.x]

- Triplestore / SPARQL interface (`SparqlInterface`, subgraph CRUD).
- `Attachment`, `Avatar`, `ExternalLink`, `LinkedKItems` property models.
- DataFrame integration via `dataframe` field on `KItem`.
- `DSMS.search()` initial implementation.

---

## [2.x]

- Initial Pydantic v1 models for `KItem` and `KType`.
- Basic CRUD operations via `DSMS.add()`, `DSMS.delete()`, `DSMS.commit()`.
- Annotation support.

---

## [< 2.0.0]

- Initial release.
