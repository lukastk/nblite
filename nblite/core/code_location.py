"""
CodeLocation class for nblite.

Represents a code location (directory) in an nblite project.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from nblite.config.schema import CodeLocationFormat, ExportMode

if TYPE_CHECKING:
    from nblite.core.notebook import Notebook
    from nblite.core.pyfile import PyFile

__all__ = ["CodeLocation"]


@dataclass
class CodeLocation:
    """
    Represents a code location in the project.

    A code location is a directory containing related files of a specific format.
    For example, "nbs" for notebooks, "pts" for percent-format files, "lib" for
    Python modules.

    Attributes:
        key: Location key (e.g., "nbs", "pts", "lib")
        path: Directory path (absolute)
        format: Format type (ipynb, percent, module)
        export_mode: How to export to this location (for module format)
        project_root: Root path of the project (for relative calculations)
    """

    key: str
    path: Path
    format: CodeLocationFormat | str
    export_mode: ExportMode = ExportMode.PERCENT
    project_root: Path | None = None

    def __post_init__(self) -> None:
        """Normalize format to enum."""
        self.path = Path(self.path)
        if isinstance(self.format, str):
            try:
                self.format = CodeLocationFormat(self.format)
            except ValueError:
                valid_formats = [f.value for f in CodeLocationFormat]
                raise ValueError(
                    f"Invalid format '{self.format}' for code location '{self.key}'. "
                    f"Valid formats: {valid_formats}"
                ) from None
        if isinstance(self.export_mode, str):
            try:
                self.export_mode = ExportMode(self.export_mode)
            except ValueError:
                valid_modes = [m.value for m in ExportMode]
                raise ValueError(
                    f"Invalid export_mode '{self.export_mode}' for code location '{self.key}'. "
                    f"Valid modes: {valid_modes}"
                ) from None

    @property
    def file_ext(self) -> str:
        """File extension for this format."""
        if self.format == CodeLocationFormat.IPYNB:
            return ".ipynb"
        elif self.format == CodeLocationFormat.PERCENT:
            return ".pct.py"
        elif self.format == CodeLocationFormat.MODULE:
            return ".py"
        return ".py"

    @property
    def is_notebook(self) -> bool:
        """Whether this is a notebook format (not module)."""
        return self.format in (CodeLocationFormat.IPYNB, CodeLocationFormat.PERCENT)

    @property
    def relative_path(self) -> Path:
        """Path relative to project root."""
        if self.project_root is not None:
            try:
                return self.path.relative_to(self.project_root)
            except ValueError:
                pass
        return self.path

    def get_files(
        self,
        ignore_dunders: bool = True,
        ignore_hidden: bool = True,
    ) -> list[Path]:
        """
        Get all files in this code location.

        Args:
            ignore_dunders: Exclude files starting with __
            ignore_hidden: Exclude files starting with .

        Returns:
            List of file paths matching the format
        """
        if not self.path.exists():
            return []

        ext = self.file_ext
        pattern = f"**/*{ext}"

        files: list[Path] = []
        for file_path in self.path.glob(pattern):
            if not file_path.is_file():
                continue

            name = file_path.name

            # Handle .pct.py extension
            if ext == ".pct.py" and not name.endswith(".pct.py"):
                continue

            if ignore_dunders and name.startswith("__"):
                continue
            if ignore_hidden and name.startswith("."):
                continue

            files.append(file_path)

        return sorted(files)

    def get_notebooks(
        self,
        ignore_dunders: bool = True,
        ignore_hidden: bool = True,
    ) -> list[Notebook]:
        """
        Get all notebooks in this code location.

        Only valid for notebook formats (ipynb, percent).

        Args:
            ignore_dunders: Exclude files starting with __
            ignore_hidden: Exclude files starting with .

        Returns:
            List of Notebook instances
        """
        if not self.is_notebook:
            return []

        from nblite.core.notebook import Notebook

        files = self.get_files(ignore_dunders=ignore_dunders, ignore_hidden=ignore_hidden)
        notebooks: list[Notebook] = []

        for file_path in files:
            nb = Notebook.from_file(file_path)
            nb.code_location = self.key
            notebooks.append(nb)

        return notebooks

    def get_pyfiles(
        self,
        ignore_dunders: bool = True,
        ignore_hidden: bool = True,
    ) -> list[PyFile]:
        """
        Get all Python files in this code location.

        Only valid for module format.

        Args:
            ignore_dunders: Exclude files starting with __
            ignore_hidden: Exclude files starting with .

        Returns:
            List of PyFile instances
        """
        if self.format != CodeLocationFormat.MODULE:
            return []

        from nblite.core.pyfile import PyFile

        files = self.get_files(ignore_dunders=ignore_dunders, ignore_hidden=ignore_hidden)
        pyfiles: list[PyFile] = []

        for file_path in files:
            pyfile = PyFile.from_file(file_path, package_root=self.path)
            pyfiles.append(pyfile)

        return pyfiles

    def __repr__(self) -> str:
        return f"CodeLocation(key={self.key!r}, path={self.path!r}, format={self.format.value!r})"
