"""
Configuration loading utilities for nblite.

Handles loading and parsing of nblite.toml configuration files.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from nblite.config.schema import (
    CodeLocationConfig,
    CodeLocationFormat,
    ExportMode,
    ExportRule,
    ExtensionEntry,
    NbliteConfig,
)

__all__ = [
    "load_config",
    "find_config_file",
    "parse_export_pipeline",
    "ConfigError",
]


class ConfigError(Exception):
    """Error loading or parsing configuration."""

    pass


def parse_export_pipeline(pipeline_str: str) -> list[ExportRule]:
    """
    Parse an export pipeline string into a list of ExportRules.

    The pipeline string format is:
        from_key -> to_key
        from_key2 -> to_key2
        ...

    Args:
        pipeline_str: Pipeline definition string

    Returns:
        List of ExportRule objects

    Examples:
        >>> rules = parse_export_pipeline("nbs -> pts")
        >>> rules[0].from_key
        'nbs'
        >>> rules[0].to_key
        'pts'
    """
    rules: list[ExportRule] = []

    for line in pipeline_str.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if "->" not in line:
            continue

        parts = line.split("->")
        if len(parts) != 2:
            raise ConfigError(f"Invalid export rule: '{line}'. Expected 'from -> to'")

        from_key = parts[0].strip()
        to_key = parts[1].strip()

        if not from_key or not to_key:
            raise ConfigError(f"Invalid export rule: '{line}'. Keys cannot be empty")

        rules.append(ExportRule(from_key=from_key, to_key=to_key))

    return rules


def find_config_file(start_path: Path | None = None) -> Path | None:
    """
    Find nblite.toml by searching upward from start_path.

    Args:
        start_path: Directory to start searching from. Defaults to cwd.

    Returns:
        Path to nblite.toml if found, None otherwise.
    """
    if start_path is None:
        start_path = Path.cwd()

    start_path = Path(start_path).resolve()

    # If start_path is a file, use its parent
    if start_path.is_file():
        start_path = start_path.parent

    current = start_path
    while True:
        config_path = current / "nblite.toml"
        if config_path.exists():
            return config_path

        # Stop at filesystem root
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _parse_code_location(key: str, data: dict[str, Any]) -> CodeLocationConfig:
    """Parse a code location config from TOML data."""
    # Handle format string to enum
    format_str = data.get("format", "ipynb")
    try:
        format_enum = CodeLocationFormat(format_str)
    except ValueError:
        valid_formats = [f.value for f in CodeLocationFormat]
        raise ConfigError(
            f"Invalid format '{format_str}' for code location '{key}'. "
            f"Valid formats: {valid_formats}"
        )

    # Handle export_mode string to enum
    export_mode_str = data.get("export_mode", "percent")
    try:
        export_mode = ExportMode(export_mode_str)
    except ValueError:
        valid_modes = [m.value for m in ExportMode]
        raise ConfigError(
            f"Invalid export_mode '{export_mode_str}' for code location '{key}'. "
            f"Valid modes: {valid_modes}"
        )

    return CodeLocationConfig(
        path=data.get("path", key),
        format=format_enum,
        export_mode=export_mode,
    )


def _parse_extensions(extensions_data: list[dict[str, Any]]) -> list[ExtensionEntry]:
    """Parse extensions from TOML data."""
    extensions: list[ExtensionEntry] = []
    for ext_data in extensions_data:
        extensions.append(ExtensionEntry(**ext_data))
    return extensions


def load_config(path: Path | str) -> NbliteConfig:
    """
    Load and parse nblite.toml configuration.

    Args:
        path: Path to nblite.toml file

    Returns:
        NbliteConfig object

    Raises:
        ConfigError: If configuration is invalid
        FileNotFoundError: If config file doesn't exist
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    try:
        with open(path, "rb") as f:
            raw_config = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"Invalid TOML in {path}: {e}") from e

    # Parse export pipeline
    pipeline_data = raw_config.get("export_pipeline", "")
    if isinstance(pipeline_data, str):
        export_rules = parse_export_pipeline(pipeline_data)
    elif isinstance(pipeline_data, list):
        # Already a list of rules
        export_rules = [
            ExportRule(from_key=r.get("from", r.get("from_key")), to_key=r.get("to", r.get("to_key")))
            for r in pipeline_data
        ]
    else:
        export_rules = []

    # Parse code locations from cl.* sections
    code_locations: dict[str, CodeLocationConfig] = {}
    cl_section = raw_config.get("cl", {})
    for key, cl_data in cl_section.items():
        if isinstance(cl_data, dict):
            code_locations[key] = _parse_code_location(key, cl_data)

    # Parse extensions
    extensions_data = raw_config.get("extensions", [])
    extensions = _parse_extensions(extensions_data)

    # Build config with nested sections
    config_data = {
        "export_pipeline": export_rules,
        "code_locations": code_locations,
        "docs_cl": raw_config.get("docs_cl"),
        "docs_title": raw_config.get("docs_title"),
        "docs_generator": raw_config.get("docs_generator", "jupyterbook"),
        "extensions": extensions,
    }

    # Parse nested sections if present
    if "templates" in raw_config:
        config_data["templates"] = raw_config["templates"]
    if "export" in raw_config:
        config_data["export"] = raw_config["export"]
    if "git" in raw_config:
        config_data["git"] = raw_config["git"]
    if "clean" in raw_config:
        config_data["clean"] = raw_config["clean"]
    if "docs" in raw_config:
        config_data["docs"] = raw_config["docs"]

    try:
        config = NbliteConfig(**config_data)
    except Exception as e:
        raise ConfigError(f"Invalid configuration: {e}") from e

    # Validate code location references in pipeline
    _validate_pipeline_references(config, path)

    return config


def _validate_pipeline_references(config: NbliteConfig, config_path: Path) -> None:
    """Validate that all code locations referenced in pipeline exist."""
    defined_locations = set(config.code_locations.keys())

    for rule in config.export_pipeline:
        if rule.from_key not in defined_locations:
            raise ConfigError(
                f"Export pipeline references undefined code location '{rule.from_key}'. "
                f"Defined locations: {sorted(defined_locations)}"
            )
        if rule.to_key not in defined_locations:
            raise ConfigError(
                f"Export pipeline references undefined code location '{rule.to_key}'. "
                f"Defined locations: {sorted(defined_locations)}"
            )

    # Validate docs_cl if specified
    if config.docs_cl is not None and config.docs_cl not in defined_locations:
        raise ConfigError(
            f"docs_cl references undefined code location '{config.docs_cl}'. "
            f"Defined locations: {sorted(defined_locations)}"
        )
