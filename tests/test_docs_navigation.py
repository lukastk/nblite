"""Navigation must describe the files actually prepared for each generator."""

import shutil
import subprocess
from pathlib import Path
from typing import Any

import nbformat
import pytest
import yaml

from nblite.config.loader import ConfigError
from nblite.core.project import NbliteProject
from nblite.docs.jupyterbook import JupyterBookGenerator
from nblite.docs.mkdocs import MkDocsGenerator

NOTEBOOKS = [
    "zebra.ipynb",
    "open_fda/device-clearances.ipynb",
    "identity/people.ipynb",
    "identity/index.ipynb",
    "identity/deep-folder/companies.ipynb",
    "identity/companies.ipynb",
    "index.ipynb",
    "alpha.ipynb",
]
EXPECTED_NAV = [
    {"Home": "index.ipynb"},
    {"Alpha": "alpha.ipynb"},
    {
        "Identity": [
            {"Home": "identity/index.ipynb"},
            {"Companies": "identity/companies.ipynb"},
            {"Deep Folder": [{"Companies": "identity/deep-folder/companies.ipynb"}]},
            {"People": "identity/people.ipynb"},
        ]
    },
    {"Open Fda": [{"Device Clearances": "open_fda/device-clearances.ipynb"}]},
    {"Zebra": "zebra.ipynb"},
]
OVERRIDE = """nav = [
    { Welcome = "index.ipynb" },
    { Reference = [{ People = "identity/people.ipynb" }, { Guide = "guide.md" }] },
    { Website = "https://example.com" },
]
"""


def make_project(tmp_path: Path, paths: list[str], docs: str = "") -> NbliteProject:
    """Write real notebooks and load the project's TOML configuration."""
    for name in paths:
        path = tmp_path / "nbs" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        nbformat.write(
            nbformat.v4.new_notebook(cells=[nbformat.v4.new_markdown_cell(f"# {path.stem}")]), path
        )
    (tmp_path / "nbs" / "guide.md").write_text("# Guide\n")
    (tmp_path / "nblite.toml").write_text(
        '[cl.nbs]\npath = "nbs"\nformat = "ipynb"\n[docs]\ncode_location = "nbs"\n' + docs
    )
    return NbliteProject.from_path(tmp_path)


def nav_paths(nav: list[dict[str, Any]]) -> list[str]:
    paths = []
    for entry in nav:
        for value in entry.values():
            paths.extend(nav_paths(value) if isinstance(value, list) else [value])
    return paths


def test_nested_nav_matches_copied_tree(tmp_path: Path) -> None:
    project = make_project(tmp_path, NOTEBOOKS)
    output = tmp_path / "prepared"
    MkDocsGenerator().prepare(project, output)
    config = yaml.safe_load((output / "mkdocs.yml").read_text())
    assert config["nav"] == EXPECTED_NAV
    copied = {
        path.relative_to(output / "docs").as_posix() for path in (output / "docs").rglob("*.ipynb")
    }
    assert set(nav_paths(config["nav"])) == copied == set(NOTEBOOKS)


@pytest.mark.parametrize("index", ["index", "00_index", "00_intro"])
def test_index_first_in_each_folder(tmp_path: Path, index: str) -> None:
    project = make_project(
        tmp_path, [f"{index}.ipynb", "aaa.ipynb", f"nested/{index}.ipynb", "nested/aaa.ipynb"]
    )
    output = tmp_path / "prepared"
    MkDocsGenerator().prepare(project, output)
    nav = yaml.safe_load((output / "mkdocs.yml").read_text())["nav"]
    assert nav == [
        {"Home": f"{index}.ipynb"},
        {"Aaa": "aaa.ipynb"},
        {"Nested": [{"Home": f"nested/{index}.ipynb"}, {"Aaa": "nested/aaa.ipynb"}]},
    ]


def test_multiple_index_aliases_are_not_lost(tmp_path: Path) -> None:
    names = ["index.ipynb", "00_index.ipynb", "00_intro.ipynb"]
    project = make_project(tmp_path, names)
    output = tmp_path / "prepared"
    MkDocsGenerator().prepare(project, output)
    nav = yaml.safe_load((output / "mkdocs.yml").read_text())["nav"]
    assert sorted(nav_paths(nav)) == sorted(names)


@pytest.mark.parametrize("override", [OVERRIDE, "nav = []\n"])
def test_toml_nav_replaces_generated_nav(tmp_path: Path, override: str) -> None:
    project = make_project(tmp_path, NOTEBOOKS, override)
    output = tmp_path / "prepared"
    MkDocsGenerator().prepare(project, output)
    nav = yaml.safe_load((output / "mkdocs.yml").read_text())["nav"]
    expected = (
        [
            {"Welcome": "index.ipynb"},
            {"Reference": [{"People": "identity/people.ipynb"}, {"Guide": "guide.md"}]},
            {"Website": "https://example.com"},
        ]
        if override == OVERRIDE
        else []
    )
    assert nav == expected
    assert project.config.docs.nav == expected


def test_invalid_nav_type_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="nav"):
        make_project(tmp_path, ["index.ipynb"], 'nav = "not a list"\n')


@pytest.mark.parametrize("override", ["", OVERRIDE])
def test_generated_mkdocs_builds_strictly(tmp_path: Path, override: str) -> None:
    if shutil.which("mkdocs") is None:
        pytest.skip("Install dev dependencies to run MkDocs integration tests")
    project = make_project(tmp_path, NOTEBOOKS, override)
    output = tmp_path / "prepared"
    MkDocsGenerator().prepare(project, output)
    result = subprocess.run(
        ["mkdocs", "build", "--strict", "--config-file", str(output / "mkdocs.yml")],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (output / "site" / "identity" / "companies" / "index.html").is_file()


@pytest.mark.parametrize("root", ["index", "00_intro", "00_index"])
def test_jupyterbook_toc_matches_nested_files(tmp_path: Path, root: str) -> None:
    names = [
        f"{root}.ipynb",
        "nested/index.ipynb",
        "nested/companies.ipynb",
        "other/companies.ipynb",
    ]
    project = make_project(tmp_path, names)
    output = tmp_path / "prepared"
    JupyterBookGenerator().prepare(project, output)
    toc = yaml.safe_load((output / "_toc.yml").read_text())
    assert toc["root"] == root
    assert toc["chapters"] == [
        {"file": "nested/companies"},
        {"file": "nested/index"},
        {"file": "other/companies"},
    ]
    assert {toc["root"], *(entry["file"] for entry in toc["chapters"])} == {
        path.relative_to(output).with_suffix("").as_posix() for path in output.rglob("*.ipynb")
    }


def test_jupyterbook_without_root_index(tmp_path: Path) -> None:
    project = make_project(tmp_path, ["nested/alpha.ipynb", "other/beta.ipynb"])
    output = tmp_path / "prepared"
    JupyterBookGenerator().prepare(project, output)
    toc = yaml.safe_load((output / "_toc.yml").read_text())
    assert toc == {
        "format": "jb-book",
        "root": "nested/alpha",
        "chapters": [{"file": "other/beta"}],
    }


def test_nav_order_is_independent_of_discovery_order() -> None:
    generator = MkDocsGenerator()
    assert generator._generate_nav([Path(name) for name in reversed(NOTEBOOKS)]) == EXPECTED_NAV
    assert generator._generate_nav([]) == []


def test_mkdocs_without_index(tmp_path: Path) -> None:
    project = make_project(tmp_path, ["nested/zebra.ipynb", "nested/alpha.ipynb"])
    output = tmp_path / "prepared"
    MkDocsGenerator().prepare(project, output)
    nav = yaml.safe_load((output / "mkdocs.yml").read_text())["nav"]
    assert nav == [{"Nested": [{"Alpha": "nested/alpha.ipynb"}, {"Zebra": "nested/zebra.ipynb"}]}]


def test_mkdocs_without_docs_code_location(tmp_path: Path) -> None:
    project = make_project(tmp_path, NOTEBOOKS)
    project.config.docs.code_location = None
    output = tmp_path / "prepared"
    MkDocsGenerator().prepare(project, output)
    nav = yaml.safe_load((output / "mkdocs.yml").read_text())["nav"]
    assert list(nav[0]) == ["Nbs"]
    assert set(nav_paths(nav)) == {f"nbs/{name}" for name in NOTEBOOKS}
    assert all((output / "docs" / name).is_file() for name in nav_paths(nav))


def test_percent_nav_uses_converted_notebook_paths(tmp_path: Path) -> None:
    source = tmp_path / "pts" / "nested" / "example.pct.py"
    source.parent.mkdir(parents=True)
    source.write_text("# %% [markdown]\n# # Example\n")
    (tmp_path / "nblite.toml").write_text(
        '[cl.pts]\npath = "pts"\nformat = "percent"\n[docs]\ncode_location = "pts"\n'
    )
    project = NbliteProject.from_path(tmp_path)
    output = tmp_path / "prepared"
    MkDocsGenerator().prepare(project, output)
    nav = yaml.safe_load((output / "mkdocs.yml").read_text())["nav"]
    assert nav_paths(nav) == ["nested/example.pct.ipynb"]
    assert (output / "docs" / "nested" / "example.pct.ipynb").is_file()


def test_nav_override_preserves_order_and_untitled_links(tmp_path: Path) -> None:
    if shutil.which("mkdocs") is None:
        pytest.skip("Install dev dependencies to run MkDocs integration tests")
    project = make_project(
        tmp_path,
        ["index.ipynb", "untitled.ipynb"],
        'nav = [{ Zed = "guide.md" }, { Alpha = "index.ipynb" }, "untitled.ipynb"]\n',
    )
    output = tmp_path / "prepared"
    MkDocsGenerator().prepare(project, output)
    nav = yaml.safe_load((output / "mkdocs.yml").read_text())["nav"]
    assert nav == [{"Zed": "guide.md"}, {"Alpha": "index.ipynb"}, "untitled.ipynb"]
    result = subprocess.run(
        ["mkdocs", "build", "--strict", "--config-file", str(output / "mkdocs.yml")],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (output / "site" / "untitled" / "index.html").is_file()


@pytest.mark.parametrize(
    ("entry", "location", "offending"),
    [
        ("{}", "docs.nav[0]", "{}"),
        ('{ Zed = "guide.md", Alpha = "index.ipynb" }', "docs.nav[0]", "Zed"),
        ("{ Home = 42 }", "docs.nav[0]['Home']", "42"),
        ("{ Section = [42] }", "docs.nav[0]['Section'][0]", "42"),
        ("{ Section = [{}] }", "docs.nav[0]['Section'][0]", "{}"),
        ('{ Section = [{ A = "a.md", B = "b.md" }] }', "docs.nav[0]['Section'][0]", "A"),
        (
            "{ Section = [{ Deep = [{ Home = false }] }] }",
            "docs.nav[0]['Section'][0]['Deep'][0]['Home']",
            "False",
        ),
        ('{ Home = { Page = "index.ipynb" } }', "docs.nav[0]['Home']", "Page"),
        ('["index.ipynb"]', "docs.nav[0]", "index.ipynb"),
        ("42", "docs.nav[0]", "42"),
    ],
    ids=[
        "empty-map",
        "multi-key-map",
        "numeric-leaf",
        "numeric-section-entry",
        "nested-empty-map",
        "nested-multi-key-map",
        "deep-boolean-leaf",
        "mapping-leaf",
        "list-entry",
        "numeric-entry",
    ],
)
def test_invalid_nav_entries_are_rejected_at_load_time(
    tmp_path: Path,
    entry: str,
    location: str,
    offending: str,
) -> None:
    with pytest.raises(ConfigError) as error:
        make_project(tmp_path, ["index.ipynb"], f"nav = [{entry}]\n")
    assert location in str(error.value)
    assert offending in str(error.value)


@pytest.mark.parametrize(
    ("names", "root"),
    [
        (["00_intro", "index", "00_index"], "index"),
        (["00_intro", "00_index"], "00_index"),
    ],
)
def test_jupyterbook_index_precedence_preserves_other_aliases(
    tmp_path: Path,
    names: list[str],
    root: str,
) -> None:
    project = make_project(tmp_path, [f"{name}.ipynb" for name in names])
    output = tmp_path / "prepared"
    JupyterBookGenerator().prepare(project, output)
    toc = yaml.safe_load((output / "_toc.yml").read_text())
    assert toc["root"] == root
    assert toc["chapters"] == [{"file": name} for name in sorted(names) if name != root]
