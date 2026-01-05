"""Core functionality module.

This is another example module for conversion.
"""

from dataclasses import dataclass


@dataclass
class Config:
    """Configuration class."""

    debug: bool = False
    verbose: bool = True
    max_retries: int = 3


def process(data: list, config: Config = None) -> list:
    """Process data with optional configuration.

    Args:
        data: Input data to process.
        config: Optional configuration.

    Returns:
        Processed data.
    """
    if config is None:
        config = Config()

    if config.verbose:
        print(f"Processing {len(data)} items...")

    return [x * 2 for x in data]
