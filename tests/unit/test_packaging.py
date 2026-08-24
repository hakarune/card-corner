"""Builds the real .deb via debpkg/build_deb.py and inspects its
contents/metadata -- catches packaging regressions (wrong paths, missing
Depends, bad permissions) without needing a full clean-VM install test,
which is left to CI's dedicated release workflow / Auditor #2's manual
pass. Skips cleanly if dpkg-deb isn't on PATH (e.g. a non-Debian dev box).

Named debpkg/, not packaging/ -- the latter collides with the real PyPI
`packaging` library (a transitive dependency of pip/setuptools), which
would otherwise shadow this directory on sys.path.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

pytestmark = pytest.mark.skipif(shutil.which("dpkg-deb") is None, reason="dpkg-deb not on PATH")


@pytest.fixture(scope="module")
def built_deb(tmp_path_factory):
    import debpkg.build_deb as build_deb

    out_dir = tmp_path_factory.mktemp("deb_out")
    deb_path = build_deb.build(out_dir)
    return deb_path


def test_deb_file_is_created(built_deb):
    assert built_deb.exists()
    assert built_deb.name.startswith("card-corner_")
    assert built_deb.suffix == ".deb"


def test_control_metadata_is_well_formed(built_deb):
    result = subprocess.run(
        ["dpkg-deb", "--info", str(built_deb)], capture_output=True, text=True, check=True
    )
    info = result.stdout
    assert "Package: card-corner" in info
    assert "Architecture: all" in info
    assert "python3-pygame" in info
    assert "Depends:" in info
    assert "Maintainer:" in info
    assert "Description: Kid-friendly card game suite" in info


def test_contents_include_expected_paths(built_deb):
    result = subprocess.run(
        ["dpkg-deb", "--contents", str(built_deb)], capture_output=True, text=True, check=True
    )
    contents = result.stdout
    expected = [
        "./usr/bin/card-corner",
        "./usr/share/applications/card-corner.desktop",
        "./usr/share/icons/hicolor/256x256/apps/card-corner.png",
        "./usr/share/card-corner/main.py",
        "./usr/share/card-corner/version.py",
        "./usr/share/card-corner/core/card.py",
        "./usr/share/card-corner/games/go_fish/screen.py",
        "./usr/share/card-corner/ui/widgets.py",
    ]
    for path in expected:
        assert path in contents, f"missing expected path: {path}"


def test_launcher_script_is_executable(built_deb):
    result = subprocess.run(
        ["dpkg-deb", "--contents", str(built_deb)], capture_output=True, text=True, check=True
    )
    launcher_line = next(line for line in result.stdout.splitlines() if line.endswith("./usr/bin/card-corner"))
    perms = launcher_line.split()[0]
    assert perms.startswith("-rwxr-xr-x"), f"launcher not executable: {perms}"


def test_extracted_source_is_syntactically_valid_and_importable(built_deb, tmp_path):
    import ast

    extract_dir = tmp_path / "extracted"
    subprocess.run(["dpkg-deb", "-x", str(built_deb), str(extract_dir)], check=True)
    app_dir = extract_dir / "usr" / "share" / "card-corner"
    py_files = list(app_dir.rglob("*.py"))
    assert len(py_files) > 10  # sanity: the whole app really got copied in
    for path in py_files:
        ast.parse(path.read_text(), filename=str(path))


def test_version_in_control_matches_version_module():
    from version import __version__

    import debpkg.build_deb as build_deb

    assert build_deb.__version__ == __version__
