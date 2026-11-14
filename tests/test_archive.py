"""Pytest for exporting and importing DSMS archives"""

import json
from urllib.parse import urljoin

import pytest
import responses


def _report(ok=True, **overrides):
    report = {
        "dry_run": False,
        "on_conflict": "fail",
        "ok": ok,
        "created": 1 if ok else 0,
        "replaced": 0,
        "skipped": 0,
        "errors": [],
        "warnings": [],
        "kitems": [
            {
                "id": "a00af336-e714-499a-9dbf-298651939e62",
                "name": "foo789",
                "ktype_id": "dataset",
                "action": "create",
                "errors": [] if ok else ["K-type 'dataset' is abstract"],
                "warnings": [],
            }
        ],
    }
    report.update(overrides)
    return report


def _dsms(custom_address):
    from dsms.core.dsms import DSMS

    with pytest.warns(UserWarning, match="No authentication details"):
        return DSMS(host_url=custom_address)


@responses.activate
def test_export_kitems(custom_address, get_mock_kitem_ids, tmp_path):
    """Export streams the archive into the given directory."""
    dsms = _dsms(custom_address)
    responses.add(
        responses.POST,
        urljoin(custom_address, "api/knowledge/kitems/export"),
        body=b"PK\x03\x04archive",
        content_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="My_process.dsms.zip"',
            "X-DSMS-Omitted": "secret-id",
        },
    )

    with pytest.warns(UserWarning, match="secret-id"):
        path = dsms.export_kitems(
            get_mock_kitem_ids[0], path=tmp_path, include_context_members=True
        )

    assert path == tmp_path / "My_process.dsms.zip"
    assert path.read_bytes() == b"PK\x03\x04archive"
    sent = json.loads(responses.calls[-1].request.body)
    assert sent == {
        "kitem_ids": [get_mock_kitem_ids[0]],
        "include_context_members": True,
        "include_linked": False,
    }


@responses.activate
def test_export_kitems_to_file(custom_address, get_mock_kitem_ids, tmp_path):
    """A file path is used as is and its stem becomes the filename hint."""
    dsms = _dsms(custom_address)
    responses.add(
        responses.POST,
        urljoin(custom_address, "api/knowledge/kitems/export"),
        body=b"zip",
    )
    target = tmp_path / "backup.dsms.zip"

    assert dsms.export_kitems(get_mock_kitem_ids[:2], path=target) == target
    sent = json.loads(responses.calls[-1].request.body)
    assert sent["kitem_ids"] == get_mock_kitem_ids[:2]
    assert sent["filename"] == "backup"


@responses.activate
def test_export_kitems_error(custom_address, tmp_path):
    dsms = _dsms(custom_address)
    responses.add(
        responses.POST,
        urljoin(custom_address, "api/knowledge/kitems/export"),
        status=403,
        json={"detail": "Cannot read KItem x"},
    )
    with pytest.raises(ValueError, match="Cannot read KItem x"):
        dsms.export_kitems("x", path=tmp_path)


@responses.activate
def test_import_kitems(custom_address, tmp_path):
    """Import uploads the file with the conflict mode and returns the report."""
    from dsms.knowledge.archive import ArchiveImportReport

    dsms = _dsms(custom_address)
    archive = tmp_path / "in.dsms.zip"
    archive.write_bytes(b"zip-bytes")
    responses.add(
        responses.POST,
        urljoin(custom_address, "api/knowledge/kitems/import"),
        json=_report(),
    )

    report = dsms.import_kitems(archive, on_conflict="replace", dry_run=True)

    assert isinstance(report, ArchiveImportReport)
    assert report.ok and report.created == 1
    request = responses.calls[-1].request
    assert "on_conflict=replace" in request.url
    assert "dry_run=true" in request.url
    assert b"zip-bytes" in request.body


@responses.activate
def test_import_kitems_rejected(custom_address, tmp_path):
    """A rejected archive (422) comes back as a report, not an exception."""
    dsms = _dsms(custom_address)
    archive = tmp_path / "in.dsms.zip"
    archive.write_bytes(b"zip-bytes")
    responses.add(
        responses.POST,
        urljoin(custom_address, "api/knowledge/kitems/import"),
        status=422,
        json=_report(ok=False),
    )

    report = dsms.import_kitems(archive)

    assert not report.ok
    assert report.all_errors == ["foo789: K-type 'dataset' is abstract"]


@responses.activate
def test_import_kitems_unreadable(custom_address, tmp_path):
    dsms = _dsms(custom_address)
    archive = tmp_path / "in.dsms.zip"
    archive.write_bytes(b"not a zip")
    responses.add(
        responses.POST,
        urljoin(custom_address, "api/knowledge/kitems/import"),
        status=400,
        json={"detail": "Not a zip file"},
    )
    with pytest.raises(ValueError, match="Not a zip file"):
        dsms.import_kitems(archive)
