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
        "./usr/share/card-corner/audio/manager.py",
    ]
    for path in expected:
        assert path in contents, f"missing expected path: {path}"


def test_extracted_package_can_actually_import_every_top_level_source_dir(built_deb, tmp_path):
    """A narrower unit test importing e.g. audio.manager in isolation can
    pass even if the .deb build itself forgot to vendor that directory
    (exactly what happened here: audio/ was missing from both
    pyproject.toml's package discovery and SOURCE_DIRS until this test was
    added). Actually run the extracted, installed-layout main.py's imports
    to catch that class of bug directly.
    """
    extract_dir = tmp_path / "import_check"
    subprocess.run(["dpkg-deb", "-x", str(built_deb), str(extract_dir)], check=True)
    app_dir = extract_dir / "usr" / "share" / "card-corner"

    result = subprocess.run(
        [sys.executable, "-c", "import main"],
        cwd=str(app_dir),
        capture_output=True,
        text=True,
        env={"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy", "PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"


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


def test_desktop_entry_exec_and_icon_match_package_name(built_deb, tmp_path):
    import debpkg.build_deb as build_deb

    extract_dir = tmp_path / "desktop_check"
    subprocess.run(["dpkg-deb", "-x", str(built_deb), str(extract_dir)], check=True)
    desktop_file = extract_dir / "usr" / "share" / "applications" / f"{build_deb.PACKAGE_NAME}.desktop"
    content = desktop_file.read_text()
    assert f"Exec={build_deb.PACKAGE_NAME}" in content
    assert f"Icon={build_deb.PACKAGE_NAME}" in content


def test_version_bump_produces_a_differently_named_deb(tmp_path, monkeypatch):
    """Simulates a release: build twice with different versions and confirm
    dpkg-deb names them so apt/dpkg recognize the second as an upgrade
    (same Package:, differing Version: baked into the filename).
    """
    import debpkg.build_deb as build_deb

    monkeypatch.setattr(build_deb, "__version__", "0.1.0-test")
    first = build_deb.build(tmp_path / "out1")
    monkeypatch.setattr(build_deb, "__version__", "0.2.0-test")
    second = build_deb.build(tmp_path / "out2")

    assert first.name != second.name
    assert "0.1.0-test" in first.name
    assert "0.2.0-test" in second.name

    first_info = subprocess.run(
        ["dpkg-deb", "--info", str(first)], capture_output=True, text=True, check=True
    ).stdout
    second_info = subprocess.run(
        ["dpkg-deb", "--info", str(second)], capture_output=True, text=True, check=True
    ).stdout
    # Same package identity, different version -- what makes this an
    # upgrade rather than a conflicting/unrelated package to dpkg.
    assert "Package: card-corner" in first_info and "Package: card-corner" in second_info
    assert "Version: 0.1.0-test" in first_info
    assert "Version: 0.2.0-test" in second_info
