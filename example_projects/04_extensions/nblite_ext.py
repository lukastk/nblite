"""
Example nblite extension demonstrating the hook system.

This extension registers callbacks for various hooks that are triggered
during nblite operations like export and clean.
"""

from nblite.extensions import HookType, hook

# Track statistics
export_stats = {"notebooks": 0, "cells": 0}


@hook(HookType.PRE_EXPORT)
def before_export(project, notebooks, **kwargs):
    """Called before export starts."""
    print(f"[EXT] Starting export for project: {project.root_path.name}")
    if notebooks:
        print(f"[EXT] Exporting {len(notebooks)} specific notebooks")
    else:
        print("[EXT] Exporting all notebooks")


@hook(HookType.PRE_NOTEBOOK_EXPORT)
def before_notebook(notebook, output_path, from_location, to_location, **kwargs):
    """Called before each notebook is exported."""
    print(f"[EXT]   Processing: {notebook.source_path.name}")


@hook(HookType.POST_NOTEBOOK_EXPORT)
def after_notebook(notebook, output_path, success, **kwargs):
    """Called after each notebook is exported."""
    if success:
        export_stats["notebooks"] += 1
        print(f"[EXT]   -> {output_path.name} (success)")
    else:
        print(f"[EXT]   -> {output_path.name} (FAILED)")


@hook(HookType.POST_CELL_EXPORT)
def after_cell(cell, notebook, source, **kwargs):
    """Called after each cell is exported."""
    export_stats["cells"] += 1


@hook(HookType.POST_EXPORT)
def after_export(project, result, **kwargs):
    """Called after export completes."""
    print("[EXT] Export complete!")
    print(
        f"[EXT] Stats: {export_stats['notebooks']} notebooks, {export_stats['cells']} cells exported"
    )
    if result.errors:
        print(f"[EXT] Errors: {len(result.errors)}")


@hook(HookType.PRE_CLEAN)
def before_clean(project, notebooks, **kwargs):
    """Called before clean starts."""
    print("[EXT] Starting clean operation")


@hook(HookType.POST_CLEAN)
def after_clean(project, cleaned_notebooks, **kwargs):
    """Called after clean completes."""
    print(f"[EXT] Cleaned {len(cleaned_notebooks)} notebooks")


@hook(HookType.DIRECTIVE_PARSED)
def on_directive(directive, cell, **kwargs):
    """Called when a directive is parsed."""
    # Example: Log custom directives
    if directive.name.startswith("custom_"):
        print(f"[EXT] Found custom directive: {directive.name} = {directive.value}")
