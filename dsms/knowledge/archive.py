"""DSMS archives: zip files that carry kitems between DSMS instances.

An archive (``*.dsms.zip``) holds every table that belongs to the exported
kitems: core fields, summary, annotations, contacts, external links,
affiliations, apps, custom properties, schema data, attachments, avatar,
data frame, visibility, grants, links and context memberships. The layout is
documented in the knowledge service (``src/schemas/archive.py``).

Use :meth:`dsms.DSMS.export_kitems` and :meth:`dsms.DSMS.import_kitems`.
"""

from typing import List, Literal

from pydantic import BaseModel, Field

ARCHIVE_EXTENSION = ".dsms.zip"

OnConflict = Literal["fail", "skip", "replace"]


class ArchiveImportItem(BaseModel):
    """Planned or performed action for one kitem of an archive."""

    id: str
    name: str
    ktype_id: str
    action: Literal["create", "replace", "skip"]
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ArchiveImportReport(BaseModel):
    """Result of importing (or checking) an archive.

    When ``ok`` is False nothing was written; the reasons are in ``errors``
    and in the ``errors`` of the individual kitems.
    """

    dry_run: bool
    on_conflict: OnConflict
    ok: bool
    created: int = 0
    replaced: int = 0
    skipped: int = 0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    kitems: List[ArchiveImportItem] = Field(default_factory=list)

    @property
    def all_errors(self) -> List[str]:
        """Archive errors and kitem errors, each kitem error prefixed by its name."""
        return self.errors + [
            f"{item.name}: {error}"
            for item in self.kitems
            for error in item.errors
        ]
