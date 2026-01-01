"""
Tests for the export pipeline (Milestone 6).
"""

import json
from pathlib import Path

import pytest

from nblite.config.schema import ExportMode
from nblite.core.notebook import Notebook
from nblite.export.pipeline import (
    ExportResult,
    export_notebook_to_module,
    export_notebook_to_notebook,
)


class TestNotebookToNotebook:
    def test_ipynb_to_percent(self, tmp_path: Path) -> None:
        """Test converting ipynb to percent format."""
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|export\ndef foo(): pass",
                        "metadata": {},
                        "outputs": [],
                    }
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        ipynb_path = tmp_path / "test.ipynb"
        ipynb_path.write_text(nb_content)
        pct_path = tmp_path / "test.pct.py"

        nb = Notebook.from_file(ipynb_path)
        export_notebook_to_notebook(nb, pct_path, format="percent")

        assert pct_path.exists()
        content = pct_path.read_text()
        assert "# %%" in content
        assert "def foo():" in content

    def test_percent_to_ipynb(self, tmp_path: Path) -> None:
        """Test converting percent to ipynb format."""
        pct_content = "# %%\n#|export\ndef foo(): pass"
        pct_path = tmp_path / "test.pct.py"
        pct_path.write_text(pct_content)
        ipynb_path = tmp_path / "test.ipynb"

        nb = Notebook.from_file(pct_path)
        export_notebook_to_notebook(nb, ipynb_path, format="ipynb")

        assert ipynb_path.exists()
        data = json.loads(ipynb_path.read_text())
        assert "cells" in data

    def test_auto_detect_format_ipynb(self, tmp_path: Path) -> None:
        """Test auto-detecting ipynb format from extension."""
        nb_content = json.dumps(
            {
                "cells": [{"cell_type": "code", "source": "x = 1", "metadata": {}, "outputs": []}],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        ipynb_path = tmp_path / "test.ipynb"
        ipynb_path.write_text(nb_content)
        output_path = tmp_path / "output.ipynb"

        nb = Notebook.from_file(ipynb_path)
        export_notebook_to_notebook(nb, output_path)  # Format auto-detected

        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert "cells" in data

    def test_auto_detect_format_percent(self, tmp_path: Path) -> None:
        """Test auto-detecting percent format from extension."""
        nb_content = json.dumps(
            {
                "cells": [{"cell_type": "code", "source": "x = 1", "metadata": {}, "outputs": []}],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        ipynb_path = tmp_path / "test.ipynb"
        ipynb_path.write_text(nb_content)
        output_path = tmp_path / "output.pct.py"

        nb = Notebook.from_file(ipynb_path)
        export_notebook_to_notebook(nb, output_path)  # Format auto-detected

        assert output_path.exists()
        content = output_path.read_text()
        assert "# %%" in content

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Test that parent directories are created."""
        nb_content = json.dumps(
            {
                "cells": [{"cell_type": "code", "source": "x = 1", "metadata": {}, "outputs": []}],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        ipynb_path = tmp_path / "test.ipynb"
        ipynb_path.write_text(nb_content)
        output_path = tmp_path / "nested" / "dir" / "output.pct.py"

        nb = Notebook.from_file(ipynb_path)
        export_notebook_to_notebook(nb, output_path, format="percent")

        assert output_path.exists()


class TestNotebookToModule:
    @pytest.fixture
    def notebook_with_exports(self, tmp_path: Path) -> Notebook:
        """Create notebook with export directives."""
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp utils",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "#|export\ndef foo():\n    pass",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "# Not exported\ntest_var = 1",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "#|export\ndef bar():\n    return 42",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        nb_path = tmp_path / "nbs" / "utils.ipynb"
        nb_path.parent.mkdir(parents=True, exist_ok=True)
        nb_path.write_text(nb_content)
        return Notebook.from_file(nb_path)

    def test_export_percent_mode(self, notebook_with_exports: Notebook, tmp_path: Path) -> None:
        """Test export with percent mode."""
        module_path = tmp_path / "utils.py"

        export_notebook_to_module(
            notebook_with_exports,
            module_path,
            project_root=tmp_path,
            export_mode=ExportMode.PERCENT,
        )

        content = module_path.read_text()
        assert "AUTOGENERATED" in content
        assert "# %%" in content
        assert "def foo():" in content
        assert "def bar():" in content
        assert "#|export" not in content
        assert "test_var" not in content

    def test_export_py_mode(self, notebook_with_exports: Notebook, tmp_path: Path) -> None:
        """Test export with py mode (no cell markers)."""
        module_path = tmp_path / "utils.py"

        export_notebook_to_module(
            notebook_with_exports,
            module_path,
            project_root=tmp_path,
            export_mode=ExportMode.PY,
        )

        content = module_path.read_text()
        assert "AUTOGENERATED" in content
        assert "# %%" not in content
        assert "def foo():" in content

    def test_export_generates_all(self, notebook_with_exports: Notebook, tmp_path: Path) -> None:
        """Test that __all__ is generated."""
        module_path = tmp_path / "utils.py"

        export_notebook_to_module(
            notebook_with_exports,
            module_path,
            project_root=tmp_path,
            export_mode=ExportMode.PERCENT,
        )

        content = module_path.read_text()
        assert "__all__" in content
        assert "'foo'" in content or '"foo"' in content
        assert "'bar'" in content or '"bar"' in content

    def test_export_removes_directives(
        self, notebook_with_exports: Notebook, tmp_path: Path
    ) -> None:
        """Test that directive lines are removed."""
        module_path = tmp_path / "utils.py"

        export_notebook_to_module(
            notebook_with_exports,
            module_path,
            project_root=tmp_path,
            export_mode=ExportMode.PERCENT,
        )

        content = module_path.read_text()
        assert "#|export" not in content
        assert "#|default_exp" not in content

    def test_export_without_warning(self, notebook_with_exports: Notebook, tmp_path: Path) -> None:
        """Test export without autogenerated warning."""
        module_path = tmp_path / "utils.py"

        export_notebook_to_module(
            notebook_with_exports,
            module_path,
            project_root=tmp_path,
            export_mode=ExportMode.PERCENT,
            include_warning=False,
        )

        content = module_path.read_text()
        assert "AUTOGENERATED" not in content

    def test_export_with_classes(self, tmp_path: Path) -> None:
        """Test export with class definitions."""
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|export\nclass MyClass:\n    pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        nb_path = tmp_path / "test.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        module_path = tmp_path / "test.py"
        export_notebook_to_module(nb, module_path, project_root=tmp_path)

        content = module_path.read_text()
        assert "'MyClass'" in content
        assert "class MyClass:" in content

    def test_export_with_constants(self, tmp_path: Path) -> None:
        """Test export with constant definitions."""
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|export\nDEFAULT_VALUE = 42",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        nb_path = tmp_path / "test.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        module_path = tmp_path / "test.py"
        export_notebook_to_module(nb, module_path, project_root=tmp_path)

        content = module_path.read_text()
        assert "'DEFAULT_VALUE'" in content
        assert "DEFAULT_VALUE = 42" in content

    def test_export_skips_private_names(self, tmp_path: Path) -> None:
        """Test that private names are not in __all__."""
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|export\ndef _private(): pass\ndef public(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        nb_path = tmp_path / "test.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        module_path = tmp_path / "test.py"
        export_notebook_to_module(nb, module_path, project_root=tmp_path)

        content = module_path.read_text()
        assert "'public'" in content
        assert "'_private'" not in content

    def test_export_with_exporti(self, tmp_path: Path) -> None:
        """Test export with exporti directive."""
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|exporti\ndef internal_func(): pass",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        nb_path = tmp_path / "test.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        module_path = tmp_path / "test.py"
        export_notebook_to_module(nb, module_path, project_root=tmp_path)

        content = module_path.read_text()
        assert "def internal_func():" in content

    def test_export_creates_parent_dirs(
        self, notebook_with_exports: Notebook, tmp_path: Path
    ) -> None:
        """Test that parent directories are created."""
        module_path = tmp_path / "nested" / "dir" / "utils.py"

        export_notebook_to_module(notebook_with_exports, module_path, project_root=tmp_path)

        assert module_path.exists()


class TestImportTransformation:
    """Test absolute to relative import transformation."""

    def test_transform_imports_depth_zero(self, tmp_path: Path) -> None:
        """Test import transformation at package root (depth 0)."""
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp core",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "#|export\nfrom my_pkg.utils import helper",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        nb_path = tmp_path / "test.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        # Create package directory structure
        pkg_dir = tmp_path / "my_pkg"
        pkg_dir.mkdir()
        module_path = pkg_dir / "core.py"

        export_notebook_to_module(nb, module_path, project_root=tmp_path, package_name="my_pkg")

        content = module_path.read_text()
        # At depth 0, should use single dot: from .utils import helper
        assert "from .utils import helper" in content
        assert "from my_pkg.utils" not in content

    def test_transform_imports_depth_one(self, tmp_path: Path) -> None:
        """Test import transformation in subdirectory (depth 1)."""
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp submodule.utils",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "#|export\nfrom my_pkg.core import greet",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        nb_path = tmp_path / "test.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        # Create package directory structure
        pkg_dir = tmp_path / "my_pkg" / "submodule"
        pkg_dir.mkdir(parents=True)
        module_path = pkg_dir / "utils.py"

        export_notebook_to_module(nb, module_path, project_root=tmp_path, package_name="my_pkg")

        content = module_path.read_text()
        # At depth 1, should use two dots: from ..core import greet
        assert "from ..core import greet" in content
        assert "from my_pkg.core" not in content

    def test_transform_imports_preserves_external(self, tmp_path: Path) -> None:
        """Test that external imports are not transformed."""
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp core",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "#|export\nfrom pathlib import Path\nimport os",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        nb_path = tmp_path / "test.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        pkg_dir = tmp_path / "my_pkg"
        pkg_dir.mkdir()
        module_path = pkg_dir / "core.py"

        export_notebook_to_module(nb, module_path, project_root=tmp_path, package_name="my_pkg")

        content = module_path.read_text()
        # External imports should be unchanged
        assert "from pathlib import Path" in content
        assert "import os" in content

    def test_transform_imports_from_package_root(self, tmp_path: Path) -> None:
        """Test 'from package import X' transformation."""
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp utils",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "#|export\nfrom my_pkg import something",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        nb_path = tmp_path / "test.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        pkg_dir = tmp_path / "my_pkg"
        pkg_dir.mkdir()
        module_path = pkg_dir / "utils.py"

        export_notebook_to_module(nb, module_path, project_root=tmp_path, package_name="my_pkg")

        content = module_path.read_text()
        # from my_pkg import X -> from . import X
        assert "from . import something" in content

    def test_transform_imports_from_package_root_depth_one(self, tmp_path: Path) -> None:
        """Test 'from package import X' transformation at depth 1."""
        nb_content = json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "#|default_exp utils._base",
                        "metadata": {},
                        "outputs": [],
                    },
                    {
                        "cell_type": "code",
                        "source": "#|export\nfrom my_pkg import const",
                        "metadata": {},
                        "outputs": [],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
        nb_path = tmp_path / "test.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        # Create package directory structure (depth 1)
        pkg_dir = tmp_path / "my_pkg" / "utils"
        pkg_dir.mkdir(parents=True)
        module_path = pkg_dir / "_base.py"

        export_notebook_to_module(nb, module_path, project_root=tmp_path, package_name="my_pkg")

        content = module_path.read_text()
        # from my_pkg import X -> from .. import X (at depth 1, needs 2 dots)
        assert "from .. import const" in content
        assert "from . import const" not in content
        assert "from my_pkg import" not in content


class TestExportResult:
    def test_export_result_defaults(self) -> None:
        """Test ExportResult default values."""
        result = ExportResult()
        assert result.success is True
        assert result.files_created == []
        assert result.files_updated == []
        assert result.errors == []

    def test_export_result_with_data(self) -> None:
        """Test ExportResult with data."""
        result = ExportResult(
            success=True,
            files_created=[Path("file1.py")],
            files_updated=[Path("file2.py")],
            errors=["Error 1"],
        )
        assert result.success is True
        assert len(result.files_created) == 1
        assert len(result.files_updated) == 1
        assert len(result.errors) == 1
