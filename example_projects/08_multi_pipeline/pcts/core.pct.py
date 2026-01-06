# ---
# jupyter:
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Core Module
#
# This notebook exports to multiple targets via branching pipelines.

# %%
#|default_exp core

# %%
#|export
VERSION = "1.0.0"

# %%
#|export
def hello() -> str:
    """Say hello."""
    return "Hello from core!"

# %%
#|export
def get_version() -> str:
    """Get the version string."""
    return VERSION

# %%
# Test
print(hello())
print(get_version())
