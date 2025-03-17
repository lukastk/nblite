# %% [markdown]
# # const

# %%
#|default_exp const

# %%
#|hide
import nblite; from nbdev.showdoc import show_doc; nblite.nbl_export()

# %%
#|export
nblite_config_file_name = "nblite.toml"

format_to_file_exts = {
    'module' : 'py',
    'ipynb' : 'ipynb',
    'percent' : 'pct.py',
    'light' : 'lgt.py',
    'sphinx' : 'spx.py',
    'myst' : 'myst.md',
    'pandoc' : 'pandoc.md',
}

file_exts_to_format = {v: k for k, v in format_to_file_exts.items()}

nb_formats = list(format_to_file_exts.keys()) + ['module']

format_to_jupytext_format = {
    'module' : 'py',
    'ipynb' : 'ipynb',
    'percent' : 'py:percent',
    'light' : 'py:light',
    'sphinx' : 'py:sphinx',
    'myst' : 'md:myst',
    'mpandoc' : 'md:pandoc',
}

code_loc_key_to_default_formats = {
    'nbs': 'ipynb',
    'pts': 'percent',
    'test_nbs': 'ipynb',
    'test_pts': 'percent',
    'lib': 'module',
    'test_lib': 'module',
}
