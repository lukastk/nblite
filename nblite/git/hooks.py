"""
Git hook management for nblite.

Handles installation and removal of git hooks for nblite projects.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nblite.core.project import NbliteProject

__all__ = ["install_hooks", "uninstall_hooks", "find_git_root"]


HOOK_MARKER_START = "# BEGIN NBLITE HOOK:"
HOOK_MARKER_END = "# END NBLITE HOOK:"


def find_git_root(start_path: Path | None = None) -> Path | None:
    """
    Find the git root directory by searching upward.

    Args:
        start_path: Starting path for search

    Returns:
        Path to .git directory, or None if not found
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()

    current = start_path
    while True:
        git_dir = current / ".git"
        if git_dir.is_dir():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _get_hook_section(project_path: Path) -> str:
    """Generate the hook section content for a project."""
    return f"""{HOOK_MARKER_START} {project_path}
if [ "$NBL_DISABLE_HOOKS" != "true" ]; then
    cd "{project_path}" && nbl hook pre-commit
fi
{HOOK_MARKER_END} {project_path}
"""


def install_hooks(project: NbliteProject, force: bool = False) -> None:
    """
    Install git hooks for an nblite project.

    Features:
    - Works with projects in repo subdirectories
    - Adds to existing hooks instead of overwriting
    - Uses markers for clean uninstall
    - Supports multiple nblite projects per repo

    Args:
        project: NbliteProject instance
        force: Force reinstall even if already installed
    """
    git_root = find_git_root(project.root_path)
    if git_root is None:
        raise RuntimeError("Not a git repository")

    hooks_dir = git_root / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    hook_path = hooks_dir / "pre-commit"
    project_marker = f"{HOOK_MARKER_START} {project.root_path}"

    # Read existing hook content
    if hook_path.exists():
        existing_content = hook_path.read_text()
    else:
        existing_content = "#!/bin/sh\n"

    # Check if already installed
    if project_marker in existing_content:
        if not force:
            return
        # Remove existing section before reinstalling
        existing_content = _remove_hook_section(existing_content, project.root_path)

    # Add shebang if missing
    if not existing_content.startswith("#!"):
        existing_content = "#!/bin/sh\n" + existing_content

    # Ensure there's a newline before our section
    if not existing_content.endswith("\n"):
        existing_content += "\n"

    # Add our hook section
    new_content = existing_content + "\n" + _get_hook_section(project.root_path)

    hook_path.write_text(new_content)
    hook_path.chmod(0o755)


def uninstall_hooks(project: NbliteProject) -> None:
    """
    Remove nblite hooks for a project.

    Args:
        project: NbliteProject instance
    """
    git_root = find_git_root(project.root_path)
    if git_root is None:
        return

    hook_path = git_root / ".git" / "hooks" / "pre-commit"
    if not hook_path.exists():
        return

    content = hook_path.read_text()
    new_content = _remove_hook_section(content, project.root_path)

    if new_content.strip() == "#!/bin/sh":
        # Hook is empty, remove the file
        hook_path.unlink()
    else:
        hook_path.write_text(new_content)


def _remove_hook_section(content: str, project_path: Path) -> str:
    """Remove the hook section for a project from hook content."""
    marker_start = f"{HOOK_MARKER_START} {project_path}"
    marker_end = f"{HOOK_MARKER_END} {project_path}"

    lines = content.split("\n")
    new_lines: list[str] = []
    in_section = False

    for line in lines:
        if marker_start in line:
            in_section = True
            continue
        if marker_end in line:
            in_section = False
            continue
        if not in_section:
            new_lines.append(line)

    # Remove extra blank lines
    result = "\n".join(new_lines)
    while "\n\n\n" in result:
        result = result.replace("\n\n\n", "\n\n")

    return result
