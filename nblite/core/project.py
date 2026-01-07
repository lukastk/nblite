"""
NbliteProject class for nblite.

Central project management class that coordinates all nblite functionality.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from nblite.config import NbliteConfig, find_config_file, load_config, parse_export_pipeline
from nblite.config.schema import CodeLocationFormat
from nblite.core.code_location import CodeLocation
from nblite.core.notebook import Format, Notebook
from nblite.core.pyfile import PyFile
from nblite.export.function_export import is_function_notebook
from nblite.export.pipeline import (
    ExportResult,
    export_notebook_to_module,
    export_notebook_to_notebook,
    export_notebooks_to_module,
    get_export_targets,
)
from nblite.extensions import HookRegistry, HookType, load_extension

__all__ = ["NbliteProject", "NotebookLineage"]


def _path_contains_dunder(path: Path) -> bool:
    """Check if any part of the path starts with double underscores."""
    return any(part.startswith("__") for part in path.parts)


@dataclass
class NotebookLineage:
    """
    Tracks the lineage of a notebook through the export pipeline.

    Attributes:
        source: Source notebook path
        code_location: Code location key of the source
        twins: Dictionary mapping code location keys to twin file paths
        module_path: Path to the exported module (if applicable)
    """

    source: Path
    code_location: str
    twins: dict[str, Path] = field(default_factory=dict)
    module_path: Path | None = None


@dataclass
class NbliteProject:
    """
    Central project management class for nblite.

    This class provides access to all project components:
    - Configuration
    - Code locations
    - Notebooks
    - Export pipeline

    Attributes:
        root_path: Project root directory
        config: Project configuration

    Example:
        >>> # Load project from current directory
        >>> project = NbliteProject.from_path()
        >>>
        >>> # Access code locations
        >>> nbs_loc = project.get_code_location("nbs")
        >>> for nb in nbs_loc.get_notebooks():
        ...     print(nb.source_path)
        >>>
        >>> # Export all notebooks
        >>> project.export_all()
        >>>
        >>> # Export with custom pipeline
        >>> project.export_all(pipeline="nbs -> lib")
    """

    root_path: Path
    config: NbliteConfig

    _code_locations: dict[str, CodeLocation] | None = field(default=None, repr=False, init=False)
    _loaded_extensions: list[Any] = field(default_factory=list, repr=False, init=False)

    @classmethod
    def from_path(
        cls,
        path: Path | str | None = None,
        config_override: dict[str, Any] | None = None,
        add_code_locations: list[dict[str, Any]] | None = None,
    ) -> NbliteProject:
        """
        Load project from path.

        If path is None, searches upward for nblite.toml from cwd.

        Args:
            path: Path to project root or nblite.toml
            config_override: Dictionary of config values to override (merges at top level)
            add_code_locations: List of code location dicts to add (each must have 'name' key)

        Returns:
            NbliteProject instance

        Raises:
            FileNotFoundError: If no nblite.toml found
        """
        if path is None:
            config_path = find_config_file()
            if config_path is None:
                raise FileNotFoundError("No nblite.toml found. Run 'nbl init' to create a project.")
            root_path = config_path.parent
        else:
            path = Path(path)
            if path.is_file() and path.name == "nblite.toml":
                root_path = path.parent
            else:
                root_path = path
                config_path = root_path / "nblite.toml"
                if not config_path.exists():
                    raise FileNotFoundError(f"No nblite.toml found in {root_path}")

        config = load_config(
            root_path / "nblite.toml",
            config_override=config_override,
            add_code_locations=add_code_locations,
        )
        project = cls(root_path=root_path.resolve(), config=config)

        # Load extensions from config
        project._load_extensions()

        return project

    def _load_extensions(self) -> None:
        """Load all extensions specified in config."""
        for ext_entry in self.config.extensions:
            try:
                # Convert path to absolute if relative
                ext_path = ext_entry.path
                if ext_path is not None:
                    path = Path(ext_path)
                    if not path.is_absolute():
                        path = self.root_path / path
                    ext_path = str(path)

                loaded = load_extension(path=ext_path, module=ext_entry.module)
                self._loaded_extensions.append(loaded)
            except Exception as e:
                # Log warning but don't fail - extensions are optional
                import warnings

                source = ext_entry.path or ext_entry.module
                warnings.warn(f"Failed to load extension '{source}': {e}", stacklevel=2)

    @classmethod
    def find_project_root(cls, start_path: Path | str | None = None) -> Path | None:
        """
        Find project root by searching for nblite.toml.

        Args:
            start_path: Starting path for search

        Returns:
            Project root path, or None if not found
        """
        if start_path is None:
            start_path = Path.cwd()
        else:
            start_path = Path(start_path)

        config_path = find_config_file(start_path)
        if config_path:
            return config_path.parent
        return None

    @property
    def code_locations(self) -> dict[str, CodeLocation]:
        """
        All code locations in the project.

        Returns:
            Dictionary mapping location keys to CodeLocation objects
        """
        if self._code_locations is None:
            self._build_code_locations()
        return self._code_locations  # type: ignore

    def _build_code_locations(self) -> None:
        """Build CodeLocation objects from config."""
        self._code_locations = {}
        for key, cl_config in self.config.code_locations.items():
            path = self.root_path / cl_config.path
            self._code_locations[key] = CodeLocation(
                key=key,
                path=path,
                format=cl_config.format,
                export_mode=cl_config.export_mode,
                project_root=self.root_path,
            )

    def get_code_location(self, key: str) -> CodeLocation:
        """
        Get a code location by key.

        Args:
            key: Code location key

        Returns:
            CodeLocation object

        Raises:
            KeyError: If code location not found
        """
        if key not in self.code_locations:
            raise KeyError(f"Code location '{key}' not found")
        return self.code_locations[key]

    def get_notebooks(
        self,
        code_location: str | None = None,
        ignore_dunders: bool = True,
        ignore_hidden: bool = True,
    ) -> list[Notebook]:
        """
        Get all notebooks in the project.

        Args:
            code_location: Filter by code location key
            ignore_dunders: Exclude __* files
            ignore_hidden: Exclude .* files

        Returns:
            List of Notebook objects
        """
        notebooks: list[Notebook] = []

        locations = self.code_locations.values()
        if code_location:
            locations = [self.get_code_location(code_location)]

        for cl in locations:
            if cl.is_notebook:
                nbs = cl.get_notebooks(
                    ignore_dunders=ignore_dunders,
                    ignore_hidden=ignore_hidden,
                )
                notebooks.extend(nbs)

        return notebooks

    @property
    def notebooks(self) -> list[Notebook]:
        """All notebooks in the project."""
        return self.get_notebooks()

    @property
    def py_files(self) -> list[PyFile]:
        """All Python module files in the project."""
        pyfiles: list[PyFile] = []
        for cl in self.code_locations.values():
            if cl.format == CodeLocationFormat.MODULE:
                pyfiles.extend(cl.get_pyfiles())
        return pyfiles

    def get_notebook_twins(self, notebook: Notebook | Path) -> list[Path]:
        """
        Get all twin paths for a notebook.

        Twin files are files that correspond to the same notebook
        in different code locations along the export pipeline.

        Args:
            notebook: Source notebook or path

        Returns:
            List of twin file paths
        """
        if isinstance(notebook, Path):
            source_path = notebook
            nb = Notebook.from_file(source_path)
        else:
            if notebook.source_path is None:
                return []
            source_path = notebook.source_path
            nb = notebook

        twins: list[Path] = []

        # Find source code location
        source_cl = None
        for cl in self.code_locations.values():
            try:
                source_path.relative_to(cl.path)
                source_cl = cl
                break
            except ValueError:
                continue

        if source_cl is None:
            return []

        # Get relative path within code location
        rel_path = source_path.relative_to(source_cl.path)
        stem = rel_path.stem
        if stem.endswith(".pct"):
            stem = stem[:-4]

        # Follow the export pipeline chain to find all twins
        # Use BFS to find all reachable locations
        visited = {source_cl.key}
        to_visit = [source_cl.key]

        while to_visit:
            current_key = to_visit.pop(0)

            for rule in self.config.export_pipeline:
                if rule.from_key == current_key and rule.to_key not in visited:
                    target_cl = self.code_locations.get(rule.to_key)
                    if target_cl:
                        if target_cl.format == CodeLocationFormat.MODULE:
                            # Skip notebooks in dunder folders/files for module exports
                            if _path_contains_dunder(rel_path):
                                visited.add(rule.to_key)
                                to_visit.append(rule.to_key)
                                continue
                            # For module exports, use default_exp to determine path
                            default_exp = nb.default_exp
                            if default_exp is None:
                                # No default_exp, skip module twin
                                visited.add(rule.to_key)
                                to_visit.append(rule.to_key)
                                continue
                            module_path = default_exp.replace(".", "/")
                            twin_path = target_cl.path / (module_path + target_cl.file_ext)
                        else:
                            # For notebook exports, preserve directory structure
                            twin_path = (
                                target_cl.path / rel_path.parent / (stem + target_cl.file_ext)
                            )
                        twins.append(twin_path)
                        visited.add(rule.to_key)
                        to_visit.append(rule.to_key)

        return twins

    def get_notebook_lineage(self, notebook: Notebook) -> NotebookLineage:
        """
        Get the full lineage for a notebook.

        Args:
            notebook: Source notebook

        Returns:
            NotebookLineage object
        """
        if notebook.source_path is None:
            return NotebookLineage(
                source=Path("unknown"),
                code_location="unknown",
            )

        # Find source code location
        source_cl_key = notebook.code_location or "unknown"
        for cl in self.code_locations.values():
            if cl.is_notebook:
                try:
                    notebook.source_path.relative_to(cl.path)
                    source_cl_key = cl.key
                    break
                except ValueError:
                    continue

        # Build twins dict
        twins: dict[str, Path] = {}
        module_path: Path | None = None

        for twin_path in self.get_notebook_twins(notebook):
            # Find which code location this twin belongs to
            for cl in self.code_locations.values():
                try:
                    twin_path.relative_to(cl.path)
                    twins[cl.key] = twin_path
                    if cl.format == CodeLocationFormat.MODULE:
                        module_path = twin_path
                    break
                except ValueError:
                    continue

        return NotebookLineage(
            source=notebook.source_path,
            code_location=source_cl_key,
            twins=twins,
            module_path=module_path,
        )

    def get_reversed_pipeline(self) -> str | None:
        """
        Get the reversed export pipeline string, excluding module code locations.

        Reverses the direction of each pipeline rule (from_key <-> to_key) but
        only for rules where neither the source nor destination is a module
        code location.

        Returns:
            Reversed pipeline string (e.g., "pts -> nbs"), or None if no
            reversible rules exist.

        Example:
            If the pipeline is "nbs -> pts, pts -> lib", the reversed pipeline
            would be "pts -> nbs" (the "pts -> lib" rule is excluded because
            'lib' is a module code location).
        """
        reversed_rules: list[str] = []

        for rule in self.config.export_pipeline:
            from_cl = self.code_locations.get(rule.from_key)
            to_cl = self.code_locations.get(rule.to_key)

            if not from_cl or not to_cl:
                continue

            # Skip rules involving module code locations
            if from_cl.format == CodeLocationFormat.MODULE:
                continue
            if to_cl.format == CodeLocationFormat.MODULE:
                continue

            # Reverse the direction: to_key -> from_key
            reversed_rules.append(f"{rule.to_key} -> {rule.from_key}")

        if not reversed_rules:
            return None

        return ", ".join(reversed_rules)

    def export(
        self,
        notebooks: list[Path] | None = None,
        pipeline: str | None = None,
        silence_warnings: bool = False,
    ) -> ExportResult:
        """
        Run the export pipeline.

        Args:
            notebooks: Specific notebooks to export (all if None)
            pipeline: Custom pipeline string (use config if None).
                Format: "from_key -> to_key" or "from1 -> to1, from2 -> to2"
                Can also use newlines to separate rules.
            silence_warnings: If True, suppress warning messages about unrecognized directives.

        Returns:
            ExportResult with success status and file lists

        Hooks triggered:
            PRE_EXPORT: Before export starts (project=self, notebooks=notebooks)
            PRE_NOTEBOOK_EXPORT: Before each notebook (notebook=nb, output_path=path)
            POST_NOTEBOOK_EXPORT: After each notebook (notebook=nb, output_path=path, success=bool)
            POST_EXPORT: After export completes (project=self, result=result)
        """
        from nblite.core.directive import get_unrecognized_directives

        result = ExportResult()

        # Trigger PRE_EXPORT hook
        HookRegistry.trigger(
            HookType.PRE_EXPORT,
            project=self,
            notebooks=notebooks,
        )

        # If specific notebooks provided, convert to Notebook objects
        specific_nbs: list[Notebook] | None = None
        if notebooks:
            specific_nbs = [Notebook.from_file(p) for p in notebooks]

        # Determine which pipeline rules to use
        if pipeline is not None:
            # Parse the custom pipeline string
            # Support both comma-separated and newline-separated formats
            pipeline_str = pipeline.replace(",", "\n")
            export_rules = parse_export_pipeline(pipeline_str)
        else:
            export_rules = self.config.export_pipeline

        # Execute pipeline rules
        for rule in export_rules:
            from_cl = self.code_locations.get(rule.from_key)
            to_cl = self.code_locations.get(rule.to_key)

            if not from_cl or not to_cl:
                continue

            # Get notebooks from source code location for this rule
            if specific_nbs is not None:
                # Filter specific notebooks that are in this source location
                nbs_to_export = []
                for nb in specific_nbs:
                    if nb.source_path is None:
                        continue
                    try:
                        nb.source_path.relative_to(from_cl.path)
                        nbs_to_export.append(nb)
                    except ValueError:
                        continue
            else:
                # Get all notebooks from source code location
                if from_cl.is_notebook:
                    nbs_to_export = from_cl.get_notebooks()
                else:
                    continue

            # Handle module exports with two-phase approach for aggregation
            if to_cl.format == CodeLocationFormat.MODULE:
                # Phase 1: Collect all notebooks and their export targets
                # Maps target_module -> list of (notebook, source_ref) tuples
                module_to_notebooks: dict[str, list[tuple[Notebook, str]]] = {}
                # Track function notebooks separately (they can't aggregate)
                function_notebooks: list[tuple[Notebook, str, str]] = []  # (nb, source_ref, target)
                # Track notebooks that claim each module via #|default_exp
                # Maps module -> notebook source_ref (for error messages)
                default_exp_owners: dict[str, str] = {}

                for nb in nbs_to_export:
                    if nb.source_path is None:
                        continue

                    try:
                        rel_path = nb.source_path.relative_to(from_cl.path)
                    except ValueError:
                        continue

                    # Skip notebooks in dunder folders/files
                    if _path_contains_dunder(rel_path):
                        continue

                    # Compute source reference for cell markers
                    try:
                        source_ref = str(nb.source_path.relative_to(self.root_path))
                    except ValueError:
                        source_ref = str(nb.source_path)

                    # Check for unrecognized directives
                    all_directives = []
                    for cell in nb.cells:
                        for directive_list in cell.directives.values():
                            all_directives.extend(directive_list)
                    unrecognized = get_unrecognized_directives(all_directives)
                    for directive in unrecognized:
                        warning_msg = (
                            f"Unrecognized directive '#|{directive.name}' "
                            f"in '{source_ref}' (line {directive.line_num + 1})"
                        )
                        if warning_msg not in result.warnings:
                            result.warnings.append(warning_msg)

                    # Check for duplicate #|default_exp
                    if nb.default_exp:
                        if nb.default_exp in default_exp_owners:
                            existing_nb = default_exp_owners[nb.default_exp]
                            raise ValueError(
                                f"Multiple notebooks have the same #|default_exp '{nb.default_exp}': "
                                f"'{existing_nb}' and '{source_ref}'. "
                                f"Each module can only have one notebook with #|default_exp. "
                                f"Use #|export_to to export cells to a shared module from multiple notebooks."
                            )
                        default_exp_owners[nb.default_exp] = source_ref

                    export_targets = get_export_targets(nb)
                    if not export_targets:
                        continue

                    # Check for #|export without #|default_exp
                    if "" in export_targets:
                        raise ValueError(
                            f"Notebook '{source_ref}' uses #|export or #|exporti without #|default_exp. "
                            f"Either add #|default_exp to specify the target module, "
                            f"or use #|export_to to explicitly specify the target module for each cell."
                        )

                    # Check if this is a function notebook
                    if is_function_notebook(nb):
                        # Function notebooks are handled separately (no aggregation)
                        for target_module in export_targets:
                            if target_module:
                                function_notebooks.append((nb, source_ref, target_module))
                    else:
                        # Regular notebooks can aggregate
                        for target_module in export_targets:
                            if target_module:
                                if target_module not in module_to_notebooks:
                                    module_to_notebooks[target_module] = []
                                module_to_notebooks[target_module].append((nb, source_ref))

                # Phase 2a: Export function notebooks (one at a time, no aggregation)
                for nb, _source_ref, target_module in function_notebooks:
                    module_path = target_module.replace(".", "/")
                    output_path = to_cl.path / (module_path + to_cl.file_ext)

                    # Trigger PRE_NOTEBOOK_EXPORT hook
                    HookRegistry.trigger(
                        HookType.PRE_NOTEBOOK_EXPORT,
                        notebook=nb,
                        output_path=output_path,
                        from_location=from_cl,
                        to_location=to_cl,
                    )

                    export_success = True
                    try:
                        package_name = to_cl.path.name
                        export_notebook_to_module(
                            nb,
                            output_path,
                            self.root_path,
                            export_mode=to_cl.export_mode,
                            include_warning=self.config.export.include_autogenerated_warning,
                            cell_reference_style=self.config.export.cell_reference_style,
                            package_name=package_name,
                            target_module=target_module,
                        )

                        if output_path.exists():
                            result.files_created.append(output_path)

                    except Exception as e:
                        result.errors.append(
                            f"Failed to export {nb.source_path} to {target_module}: {e}"
                        )
                        result.success = False
                        export_success = False

                    # Trigger POST_NOTEBOOK_EXPORT hook
                    HookRegistry.trigger(
                        HookType.POST_NOTEBOOK_EXPORT,
                        notebook=nb,
                        output_path=output_path,
                        from_location=from_cl,
                        to_location=to_cl,
                        success=export_success,
                    )

                # Phase 2b: Export aggregated regular notebooks
                for target_module, notebooks_list in module_to_notebooks.items():
                    module_path = target_module.replace(".", "/")
                    output_path = to_cl.path / (module_path + to_cl.file_ext)

                    # Trigger PRE_NOTEBOOK_EXPORT hooks for all contributing notebooks
                    for nb, _source_ref in notebooks_list:
                        HookRegistry.trigger(
                            HookType.PRE_NOTEBOOK_EXPORT,
                            notebook=nb,
                            output_path=output_path,
                            from_location=from_cl,
                            to_location=to_cl,
                        )

                    export_success = True
                    try:
                        package_name = to_cl.path.name
                        export_notebooks_to_module(
                            notebooks_list,
                            output_path,
                            self.root_path,
                            export_mode=to_cl.export_mode,
                            include_warning=self.config.export.include_autogenerated_warning,
                            cell_reference_style=self.config.export.cell_reference_style,
                            package_name=package_name,
                            target_module=target_module,
                        )

                        if output_path.exists():
                            result.files_created.append(output_path)

                    except Exception as e:
                        nb_paths = ", ".join(str(nb.source_path) for nb, _ in notebooks_list)
                        result.errors.append(
                            f"Failed to export notebooks ({nb_paths}) to {target_module}: {e}"
                        )
                        result.success = False
                        export_success = False

                    # Trigger POST_NOTEBOOK_EXPORT hooks for all contributing notebooks
                    for nb, _source_ref in notebooks_list:
                        HookRegistry.trigger(
                            HookType.POST_NOTEBOOK_EXPORT,
                            notebook=nb,
                            output_path=output_path,
                            from_location=from_cl,
                            to_location=to_cl,
                            success=export_success,
                        )

            # Handle notebook-to-notebook exports
            for nb in nbs_to_export:
                if nb.source_path is None:
                    continue

                try:
                    rel_path = nb.source_path.relative_to(from_cl.path)
                except ValueError:
                    continue

                if to_cl.format == CodeLocationFormat.MODULE:
                    # Module exports already handled above
                    continue

                # Compute source reference for warnings
                try:
                    source_ref = str(nb.source_path.relative_to(self.root_path))
                except ValueError:
                    source_ref = str(nb.source_path)

                # Check for unrecognized directives (if not already checked in module export)
                all_directives = []
                for cell in nb.cells:
                    for directive_list in cell.directives.values():
                        all_directives.extend(directive_list)
                unrecognized = get_unrecognized_directives(all_directives)
                for directive in unrecognized:
                    warning_msg = (
                        f"Unrecognized directive '#|{directive.name}' "
                        f"in '{source_ref}' (line {directive.line_num + 1})"
                    )
                    if warning_msg not in result.warnings:
                        result.warnings.append(warning_msg)

                # For notebook-to-notebook exports, preserve directory structure
                stem = rel_path.stem
                if stem.endswith(".pct"):
                    stem = stem[:-4]
                output_path = to_cl.path / rel_path.parent / (stem + to_cl.file_ext)

                # Trigger PRE_NOTEBOOK_EXPORT hook
                HookRegistry.trigger(
                    HookType.PRE_NOTEBOOK_EXPORT,
                    notebook=nb,
                    output_path=output_path,
                    from_location=from_cl,
                    to_location=to_cl,
                )

                export_success = True
                try:
                    # Export to notebook format
                    fmt = (
                        Format.PERCENT.value
                        if to_cl.format == CodeLocationFormat.PERCENT
                        else Format.IPYNB.value
                    )
                    export_notebook_to_notebook(nb, output_path, format=fmt)

                    if output_path.exists():
                        result.files_created.append(output_path)

                except Exception as e:
                    result.errors.append(f"Failed to export {nb.source_path}: {e}")
                    result.success = False
                    export_success = False

                # Trigger POST_NOTEBOOK_EXPORT hook
                HookRegistry.trigger(
                    HookType.POST_NOTEBOOK_EXPORT,
                    notebook=nb,
                    output_path=output_path,
                    from_location=from_cl,
                    to_location=to_cl,
                    success=export_success,
                )

        # Trigger POST_EXPORT hook
        HookRegistry.trigger(
            HookType.POST_EXPORT,
            project=self,
            result=result,
        )

        return result

    def clean(
        self,
        notebooks: list[Path] | None = None,
        *,
        remove_outputs: bool | None = None,
        remove_execution_counts: bool | None = None,
        remove_cell_metadata: bool | None = None,
        remove_notebook_metadata: bool | None = None,
        remove_kernel_info: bool | None = None,
        preserve_cell_ids: bool | None = None,
        remove_output_metadata: bool | None = None,
        remove_output_execution_counts: bool | None = None,
        keep_only_metadata: list[str] | None = None,
    ) -> None:
        """
        Clean notebooks by removing outputs and metadata.

        Args:
            notebooks: Specific notebooks to clean (all ipynb if None)
            remove_outputs: Remove all outputs from code cells (None = use config)
            remove_execution_counts: Remove execution counts from code cells (None = use config)
            remove_cell_metadata: Remove cell-level metadata (None = use config)
            remove_notebook_metadata: Remove notebook-level metadata (None = use config)
            remove_kernel_info: Remove kernel specification (None = use config)
            preserve_cell_ids: Preserve cell IDs (None = use config)
            remove_output_metadata: Remove metadata from outputs (None = use config)
            remove_output_execution_counts: Remove execution counts from output results (None = use config)
            keep_only_metadata: Keep only these metadata keys (None = use config)

        Hooks triggered:
            PRE_CLEAN: Before clean starts (project=self, notebooks=notebooks)
            POST_CLEAN: After clean completes (project=self, cleaned_notebooks=list)
        """
        import json

        # Trigger PRE_CLEAN hook
        HookRegistry.trigger(
            HookType.PRE_CLEAN,
            project=self,
            notebooks=notebooks,
        )

        # Use config values as defaults, allow overrides
        clean_config = self.config.clean
        clean_opts = {
            "remove_outputs": remove_outputs
            if remove_outputs is not None
            else clean_config.remove_outputs,
            "remove_execution_counts": remove_execution_counts
            if remove_execution_counts is not None
            else clean_config.remove_execution_counts,
            "remove_cell_metadata": remove_cell_metadata
            if remove_cell_metadata is not None
            else clean_config.remove_cell_metadata,
            "remove_notebook_metadata": remove_notebook_metadata
            if remove_notebook_metadata is not None
            else clean_config.remove_notebook_metadata,
            "remove_kernel_info": remove_kernel_info
            if remove_kernel_info is not None
            else clean_config.remove_kernel_info,
            "preserve_cell_ids": preserve_cell_ids
            if preserve_cell_ids is not None
            else clean_config.preserve_cell_ids,
            "remove_output_metadata": remove_output_metadata
            if remove_output_metadata is not None
            else clean_config.remove_output_metadata,
            "remove_output_execution_counts": remove_output_execution_counts
            if remove_output_execution_counts is not None
            else clean_config.remove_output_execution_counts,
            "keep_only_metadata": keep_only_metadata
            if keep_only_metadata is not None
            else clean_config.keep_only_metadata,
        }

        if notebooks:
            nbs_to_clean = [Notebook.from_file(p) for p in notebooks]
        else:
            # Clean all ipynb notebooks
            nbs_to_clean = []
            for cl in self.code_locations.values():
                if cl.format == CodeLocationFormat.IPYNB:
                    nbs_to_clean.extend(cl.get_notebooks())

        cleaned_notebooks: list[Path] = []
        for nb in nbs_to_clean:
            if nb.source_path is None:
                continue

            cleaned = nb.clean(**clean_opts)
            content = json.dumps(cleaned.to_dict(), indent=2) + "\n"
            nb.source_path.write_text(content)
            cleaned_notebooks.append(nb.source_path)

        # Trigger POST_CLEAN hook
        HookRegistry.trigger(
            HookType.POST_CLEAN,
            project=self,
            cleaned_notebooks=cleaned_notebooks,
        )

    def __repr__(self) -> str:
        return (
            f"NbliteProject(root={self.root_path!r}, locations={list(self.code_locations.keys())})"
        )
