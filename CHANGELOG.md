# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [5.0.0] — unreleased

### Added

**User model**
- `User` gains optional `firstName`, `lastName`, and `email` fields populated from the Keycloak user profile.

**Access control (RBAC)**
- `KItemAccessProperties` model with `user_access` and `group_access` lists for per-KItem role assignments.
- `Role` enum (`MEMBER=1`, `CONTRIBUTOR=2`, `OWNER=3`, `ADMIN=4`) and `OperationType` enum (`create`, `read`, `update`, `delete`, `manage`).
- `RoleMapping` enum with `get_operations`, `min_access_level`, and `max_access_level` helpers.
- `UserAccessProperty` and `GroupAccessProperty` sub-models.
- `DSMS.user_groups` and `DSMS.users` cached properties with `refresh_user_groups()` / `refresh_users()` invalidation.
- `DSMS.get_user(user_id)` convenience method.
- `Group`, `User`, `GroupList`, `UserList` models (`dsms.knowledge.groups`).
- `INTERNALLY_PUBLIC_GROUP` / `EXTERNALLY_PUBLIC_GROUP` constants, configurable via environment variables.
- `refresh_public_groups(config)` to avoid import-time staleness when custom group IDs are used.

**KType v2 semantic-spec subsystem**
- `KTypeSpec` model capturing the full `ktype_spec` database record: ontology classes, relations, semantic schema references, inheritance, tags, versioning, stash state.
- Sub-models: `OntologyClassSpec`, `SemanticSchemaRef`, `RelationSpec`.
- `KTypeV2(KType)` response model with optional `spec: KTypeSpec` field.
- Request models: `CreateKTypeRequest`, `ImportFromUrlRequest`, `KTypeSpecPayload`.
- Remote-repository models: `RemoteKTypeSummary`, `RemoteKTypeVersion`, `RemoteSchemaInfo`, `RemoteSchemaVersionInfo`, `SpecDiffField`, `RemoteDiffOut`.
- Full v2 CRUD surface on `DSMS`: `get_v2_ktypes`, `get_v2_ktype`, `create_v2_ktype`, `import_v2_ktype`, `update_v2_ktype`, `delete_v2_ktype`, `restore_v2_ktype_stash`, `refresh_v2_ktype`, `export_v2_ktype`, `list_remote_v2_ktypes`, `list_remote_schemas`, `list_remote_ktype_versions`, `get_v2_ktype_remote_diff`.
- `DSMS.get_ktypes_by_parent(parent_id)` for the `?parent=` filter on the v1 list endpoint.

**Schema data on KItems**
- `KItemSchemaData` model (`schema_id`, `content`) and `KItemSchemaDataList` helper with `.by_schema_id` lookup.
- `KItem.schema_data: Optional[List[KItemSchemaData]]` field.
- Commit flow syncs `schema_data` changes via `PUT`/`DELETE` on `/api/knowledge/{kitem_id}/schema-data/{schema_id}`.

**Context SPARQL**
- `SparqlInterface.query_context(context_id, query)` — `POST /api/knowledge/sparql/context`.
- `SparqlInterface.graph_context(context_id, query)` — `POST /api/knowledge/graph/context`.

**Search and list additions**
- `DSMS.search()` gains `contexts: List[str]` (filter by context KItem IDs) and `attachment_extensions: List[str]` (filter by file extension).
- `DSMS.get_kitems()` gains `name: str` for substring filtering.

**KItemCompactedModel additions**
- `has_contexts: bool` — whether the KItem belongs to at least one context.
- `attachment_extensions: Optional[List[str]]` — unique file extensions in the KItem's attachments.
- `avatar_exists` moved from `KItem` to the shared `KItemCompactedModel` base.

### Changed

- `KItem.contexts` field now properly tracks changes in `_get_kitems_diffs()`.
- `KItem.access_properties` changes are tracked and committed.
- `get_user_by_id` now accepts `dsms` as its first argument (consistent with all util functions) and returns a typed `User` object.
- `Role.min_access_level` / `max_access_level` now return `Role` objects and raise `ValueError` for operations not granted by any role (e.g. `CREATE`).

### Deprecated

- `KItem.authors` — the server no longer populates this field. Use `access_properties` instead.
- `KItem.rdf_exists` — the server no longer populates this field.
- `KItem.user_groups` — legacy field still supported but superseded by `access_properties`.

### Maintenance

- Upgraded pre-commit hooks: `pre-commit-hooks` v4→v6, `black` 23→26, `isort` 5→8, `setup-cfg-fmt` v2→v3, `bandit` 1.9.3→1.9.4.
- Aligned `isort` line length to match `black`'s 79-character limit.
- Relaxed dependency pins: `rdflib>=6,<8`, `pandas>=2,<4`, `segno>=1.6,<2`, `pydantic-settings>=2,<3`, `oyaml>=1`.
- Dropped Python 3.8 and 3.9 support.

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
