"""
Configuration handling for nblite.

This module contains:
- NbliteConfig: Main configuration model
- Config loading and validation utilities
"""

from nblite.config.loader import (
    ConfigError,
    find_config_file,
    load_config,
    parse_export_pipeline,
)
from nblite.config.schema import (
    CellReferenceStyle,
    CleanConfig,
    CodeLocationConfig,
    CodeLocationFormat,
    DocsConfig,
    ExportConfig,
    ExportMode,
    ExportRule,
    ExtensionEntry,
    GitConfig,
    NbliteConfig,
    TemplatesConfig,
)

__all__ = [
    # Schema classes
    "NbliteConfig",
    "CodeLocationConfig",
    "CodeLocationFormat",
    "ExportMode",
    "ExportRule",
    "ExtensionEntry",
    "ExportConfig",
    "GitConfig",
    "CleanConfig",
    "DocsConfig",
    "TemplatesConfig",
    "CellReferenceStyle",
    # Loader functions
    "load_config",
    "find_config_file",
    "parse_export_pipeline",
    "ConfigError",
]
