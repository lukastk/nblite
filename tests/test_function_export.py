"""
Tests for function notebook export (Milestone 12).
"""

from pathlib import Path

import pytest

from nblite.core.notebook import Notebook
from nblite.export.function_export import (
    export_function_notebook,
    is_function_notebook,
)


@pytest.fixture
def function_notebook(tmp_path: Path) -> Notebook:
    """Create a function notebook."""
    nb_content = """{
        "cells": [
            {"cell_type": "code", "source": "#|default_exp my_workflow\\n#|export_as_func true", "metadata": {}, "outputs": [], "execution_count": null},
            {"cell_type": "code", "source": "#|top_export\\nimport os\\nfrom typing import List", "metadata": {}, "outputs": [], "execution_count": null},
            {"cell_type": "code", "source": "#|set_func_signature\\ndef run_workflow(input_path: str, verbose: bool = False): ...", "metadata": {}, "outputs": [], "execution_count": null},
            {"cell_type": "code", "source": "#|export\\ndata = load_data(input_path)\\nif verbose:\\n    print(f'Loaded {len(data)} items')", "metadata": {}, "outputs": [], "execution_count": null},
            {"cell_type": "code", "source": "#|export\\nresult = process(data)", "metadata": {}, "outputs": [], "execution_count": null},
            {"cell_type": "code", "source": "#|func_return\\nresult", "metadata": {}, "outputs": [], "execution_count": null}
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5
    }"""
    nb_path = tmp_path / "workflow.ipynb"
    nb_path.write_text(nb_content)
    return Notebook.from_file(nb_path)


@pytest.fixture
def simple_function_notebook(tmp_path: Path) -> Notebook:
    """Create a simple function notebook."""
    nb_content = """{
        "cells": [
            {"cell_type": "code", "source": "#|default_exp simple\\n#|export_as_func true", "metadata": {}, "outputs": [], "execution_count": null},
            {"cell_type": "code", "source": "#|set_func_signature\\ndef simple_func(x: int) -> int: ...", "metadata": {}, "outputs": [], "execution_count": null},
            {"cell_type": "code", "source": "#|export\\ny = x * 2", "metadata": {}, "outputs": [], "execution_count": null},
            {"cell_type": "code", "source": "#|func_return\\ny", "metadata": {}, "outputs": [], "execution_count": null}
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5
    }"""
    nb_path = tmp_path / "simple.ipynb"
    nb_path.write_text(nb_content)
    return Notebook.from_file(nb_path)


class TestIsFunctionNotebook:
    def test_is_function_notebook_true(self, function_notebook: Notebook) -> None:
        """Test detection of function notebook."""
        assert is_function_notebook(function_notebook)

    def test_is_function_notebook_false(self, tmp_path: Path) -> None:
        """Test non-function notebook returns false."""
        nb_content = """{
            "cells": [
                {"cell_type": "code", "source": "#|default_exp utils\\n#|export\\ndef foo(): pass", "metadata": {}, "outputs": [], "execution_count": null}
            ],
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
            "nbformat": 4,
            "nbformat_minor": 5
        }"""
        nb_path = tmp_path / "utils.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        assert not is_function_notebook(nb)


class TestFunctionNotebookExport:
    def test_export_function_notebook(self, function_notebook: Notebook, tmp_path: Path) -> None:
        """Test exporting function notebook."""
        module_path = tmp_path / "my_workflow.py"

        export_function_notebook(function_notebook, module_path)

        content = module_path.read_text()

        # Check structure
        assert "import os" in content
        assert "from typing import List" in content
        assert "def run_workflow(input_path: str, verbose: bool = False):" in content
        assert "data = load_data(input_path)" in content
        assert "return result" in content

    def test_top_export_before_function(self, function_notebook: Notebook, tmp_path: Path) -> None:
        """Test top_export code appears before function."""
        module_path = tmp_path / "my_workflow.py"
        export_function_notebook(function_notebook, module_path)

        content = module_path.read_text()
        import_pos = content.find("import os")
        def_pos = content.find("def run_workflow")

        assert import_pos < def_pos

    def test_func_return_prepends_return(self, function_notebook: Notebook, tmp_path: Path) -> None:
        """Test func_return directive prepends return."""
        module_path = tmp_path / "my_workflow.py"
        export_function_notebook(function_notebook, module_path)

        content = module_path.read_text()
        assert "return result" in content

    def test_func_return_line_inline(self, tmp_path: Path) -> None:
        """Test func_return_line works inline."""
        nb_content = """{
            "cells": [
                {"cell_type": "code", "source": "#|default_exp test\\n#|export_as_func true", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|set_func_signature\\ndef compute(): ...", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|export\\nx = calculate()\\nx #|func_return_line", "metadata": {}, "outputs": [], "execution_count": null}
            ],
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
            "nbformat": 4,
            "nbformat_minor": 5
        }"""
        nb_path = tmp_path / "test.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        module_path = tmp_path / "test.py"
        export_function_notebook(nb, module_path)

        content = module_path.read_text()
        assert "return x" in content

    def test_non_exported_cells_excluded(self, function_notebook: Notebook, tmp_path: Path) -> None:
        """Test cells without export are excluded from function body."""
        module_path = tmp_path / "my_workflow.py"
        export_function_notebook(function_notebook, module_path)

        content = module_path.read_text()
        # The function signature cell content should not be in function body
        # Check that ellipsis from signature is not in the function
        func_body = content.split("def run_workflow")[1]
        assert "..." not in func_body

    def test_body_indentation(self, simple_function_notebook: Notebook, tmp_path: Path) -> None:
        """Test function body is properly indented."""
        module_path = tmp_path / "simple.py"
        export_function_notebook(simple_function_notebook, module_path)

        content = module_path.read_text()
        # Body should be indented
        assert "    y = x * 2" in content
        assert "    return y" in content

    def test_autogenerated_warning(
        self, simple_function_notebook: Notebook, tmp_path: Path
    ) -> None:
        """Test autogenerated warning is included."""
        module_path = tmp_path / "simple.py"
        export_function_notebook(simple_function_notebook, module_path, include_warning=True)

        content = module_path.read_text()
        assert "AUTOGENERATED" in content

    def test_no_autogenerated_warning(
        self, simple_function_notebook: Notebook, tmp_path: Path
    ) -> None:
        """Test autogenerated warning can be excluded."""
        module_path = tmp_path / "simple.py"
        export_function_notebook(simple_function_notebook, module_path, include_warning=False)

        content = module_path.read_text()
        assert "AUTOGENERATED" not in content

    def test_creates_parent_dirs(self, simple_function_notebook: Notebook, tmp_path: Path) -> None:
        """Test export creates parent directories."""
        module_path = tmp_path / "subdir" / "nested" / "simple.py"
        export_function_notebook(simple_function_notebook, module_path)

        assert module_path.exists()

    def test_multiple_top_exports(self, tmp_path: Path) -> None:
        """Test multiple top_export cells are combined."""
        nb_content = """{
            "cells": [
                {"cell_type": "code", "source": "#|default_exp multi\\n#|export_as_func true", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|top_export\\nimport os", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|top_export\\nimport sys", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|set_func_signature\\ndef multi(): ...", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|export\\npass", "metadata": {}, "outputs": [], "execution_count": null}
            ],
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
            "nbformat": 4,
            "nbformat_minor": 5
        }"""
        nb_path = tmp_path / "multi.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        module_path = tmp_path / "multi.py"
        export_function_notebook(nb, module_path)

        content = module_path.read_text()
        assert "import os" in content
        assert "import sys" in content

    def test_default_signature_when_missing(self, tmp_path: Path) -> None:
        """Test default signature is used when set_func_signature missing."""
        nb_content = """{
            "cells": [
                {"cell_type": "code", "source": "#|default_exp my_func\\n#|export_as_func true", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|export\\nx = 1", "metadata": {}, "outputs": [], "execution_count": null}
            ],
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
            "nbformat": 4,
            "nbformat_minor": 5
        }"""
        nb_path = tmp_path / "func.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        module_path = tmp_path / "func.py"
        export_function_notebook(nb, module_path)

        content = module_path.read_text()
        assert "def my_func():" in content

    def test_bottom_export(self, tmp_path: Path) -> None:
        """Test bottom_export adds code after function."""
        nb_content = """{
            "cells": [
                {"cell_type": "code", "source": "#|default_exp func\\n#|export_as_func true", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|set_func_signature\\ndef func(): ...", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|export\\nx = 1", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|bottom_export\\nresult = func()", "metadata": {}, "outputs": [], "execution_count": null}
            ],
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
            "nbformat": 4,
            "nbformat_minor": 5
        }"""
        nb_path = tmp_path / "func.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        module_path = tmp_path / "func.py"
        export_function_notebook(nb, module_path)

        content = module_path.read_text()
        assert "def func():" in content
        assert "result = func()" in content
        # bottom_export should appear after the function definition
        func_pos = content.find("def func():")
        bottom_pos = content.find("result = func()")
        assert func_pos < bottom_pos, "bottom_export should appear after function"

    def test_top_export_ordering(self, tmp_path: Path) -> None:
        """Test top_export cells are sorted by order value."""
        nb_content = """{
            "cells": [
                {"cell_type": "code", "source": "#|default_exp func\\n#|export_as_func true", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|top_export 2\\nimport later_import", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|top_export 1\\nimport earlier_import", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|set_func_signature\\ndef func(): ...", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|export\\npass", "metadata": {}, "outputs": [], "execution_count": null}
            ],
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
            "nbformat": 4,
            "nbformat_minor": 5
        }"""
        nb_path = tmp_path / "func.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        module_path = tmp_path / "func.py"
        export_function_notebook(nb, module_path)

        content = module_path.read_text()
        # earlier_import (order 1) should appear before later_import (order 2)
        earlier_pos = content.find("import earlier_import")
        later_pos = content.find("import later_import")
        assert earlier_pos < later_pos, "top_export with lower order should appear first"

    def test_function_body_ordering(self, tmp_path: Path) -> None:
        """Test function body cells are sorted by order value."""
        nb_content = """{
            "cells": [
                {"cell_type": "code", "source": "#|default_exp func\\n#|export_as_func true", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|set_func_signature\\ndef func(): ...", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|export 5\\nlater_code = 2", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|export -5\\nearlier_code = 1", "metadata": {}, "outputs": [], "execution_count": null}
            ],
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
            "nbformat": 4,
            "nbformat_minor": 5
        }"""
        nb_path = tmp_path / "func.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        module_path = tmp_path / "func.py"
        export_function_notebook(nb, module_path)

        content = module_path.read_text()
        # earlier_code (order -5) should appear before later_code (order 5)
        earlier_pos = content.find("earlier_code = 1")
        later_pos = content.find("later_code = 2")
        assert earlier_pos < later_pos, "export with lower order should appear first in body"

    def test_bottom_export_ordering(self, tmp_path: Path) -> None:
        """Test bottom_export cells are sorted by order value."""
        nb_content = """{
            "cells": [
                {"cell_type": "code", "source": "#|default_exp func\\n#|export_as_func true", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|set_func_signature\\ndef func(): ...", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|export\\npass", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|bottom_export 2000\\nlater_bottom = 2", "metadata": {}, "outputs": [], "execution_count": null},
                {"cell_type": "code", "source": "#|bottom_export 500\\nearlier_bottom = 1", "metadata": {}, "outputs": [], "execution_count": null}
            ],
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
            "nbformat": 4,
            "nbformat_minor": 5
        }"""
        nb_path = tmp_path / "func.ipynb"
        nb_path.write_text(nb_content)
        nb = Notebook.from_file(nb_path)

        module_path = tmp_path / "func.py"
        export_function_notebook(nb, module_path)

        content = module_path.read_text()
        # earlier_bottom (order 500) should appear before later_bottom (order 2000)
        earlier_pos = content.find("earlier_bottom = 1")
        later_pos = content.find("later_bottom = 2")
        assert earlier_pos < later_pos, "bottom_export with lower order should appear first"
