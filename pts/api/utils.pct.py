# %% [markdown]
# # utils

# %%
#|default_exp utils

# %%
#|hide
import nblite; from nbdev.showdoc import show_doc; nblite.nbl_export()

# %%
#|export
from pathlib import Path
from typing import Union 
import os

from nblite.config import NBLiteConfig, get_project_root_and_config, CodeLocation, read_config
from nblite.const import file_exts_to_format, nblite_config_file_name

# %%
import nblite.utils as this

# %%
show_doc(this.get_nb_format_from_path)


# %%
#|export
def get_nb_format_from_path(path: str) -> str:
    path = Path(path).as_posix()
    for ext, fmt in file_exts_to_format.items():
        if path.endswith(f".{ext}"): return fmt
    return None


# %%
get_nb_format_from_path('file.pct.py')

# %%
show_doc(this.get_nb_path_info)


# %%
#|export
def get_nb_path_info(nb_path: str, root_path: str, config: NBLiteConfig):
    nb_path = Path(nb_path).resolve()
    root_path = Path(root_path).resolve()
    rel_nb_path = nb_path.relative_to(root_path)
    if not rel_nb_path.parts[0] in [loc.path for loc in config.code_locations.values()]:
        raise ValueError(f"Notebook '{nb_path}' is not in a valid code location.")
        
    for loc in config.code_locations.values():
        if str(rel_nb_path).startswith(loc.path):
            file_ext = loc.file_ext
            if not str(rel_nb_path).endswith(file_ext):
                raise ValueError(f"Notebook '{nb_path}' has an invalid file extension.")
            name = Path(str(rel_nb_path)[:-len(f".{file_ext}")])
            return {
                "name": name,
                "cl_name": Path(*name.parts[1:]),
                "basename": Path(name).stem,
                "format": loc.format,
                "file_ext": file_ext,
                "cl_path": loc.path,
            }


# %%
root_path = '../../test_proj'
root_path, config = get_project_root_and_config(root_path)
get_nb_path_info('../../test_proj/nbs/notebook1.ipynb', '../../test_proj', config)

# %%
show_doc(this.is_code_loc_nb)


# %%
#|export
def is_code_loc_nb(nb_path: str, root_path: str, config: NBLiteConfig):
    """Returns True if the notebook is a notebook associated with a code location."""
    nb_path = Path(nb_path).resolve()
    root_path = Path(root_path).resolve()
    try:
        rel_nb_path = nb_path.relative_to(root_path)
        for loc in config.code_locations.values():
            if str(rel_nb_path).startswith(loc.path):
                in_cl = True
                is_nb = str(rel_nb_path).endswith(loc.file_ext)
                return in_cl and is_nb
        return False
    except ValueError:
        return False


# %%
root_path = '../../test_proj'
print(is_code_loc_nb('../../test_proj/nbs/notebook1.ipynb', root_path, config))
print(is_code_loc_nb('../../test_proj/nbs/notebook1.pct.py', root_path, config))
print(is_code_loc_nb('../../test_proj/test.txt', root_path, config))

# %%
show_doc(this.get_code_location_nbs)


# %%
#|export
def get_code_location_nbs(root_path: str, cl: CodeLocation, ignore_underscores: bool = True):
    """Returns all notebooks in a code location. If ignore_underscores is True,
    notebooks with underscores in their names, or notebooks in folders that start with underscores, are ignored."""
    
    cl_path = Path(root_path) / cl.path
    if not cl_path.exists(): raise ValueError(f"Code location path '{cl_path}' does not exist.")
    
    nbs = []
    for fp in cl_path.glob('**/*'):
        rel_fp = fp.relative_to(cl_path)
        if fp.is_file() and fp.name.endswith(cl.file_ext):
            if ignore_underscores and any(p.startswith('_') for p in rel_fp.parts): continue
            nbs.append(fp)
    return nbs


# %%
get_code_location_nbs('../../test_proj', CodeLocation(path='nbs', format='ipynb'))

# %%
get_code_location_nbs('../../test_proj', CodeLocation(path='nbs', format='ipynb'), ignore_underscores=False)

# %%
show_doc(this.is_nb_unclean)


# %%
#|export
def is_nb_unclean(nb_path:Union[str, None]=None, file_content:Union[str, None]=None):
    import nbformat
    from nbconvert.preprocessors import ExecutePreprocessor

    if nb_path is not None and file_content is not None:
        raise ValueError("Only one of nb_path or file_content can be provided.")
    
    if nb_path is None and file_content is None:
        raise ValueError("Either nb_path or file_content must be provided.")

    if nb_path:
        nb_path = Path(nb_path)
        if not nb_path.as_posix().endswith('.ipynb'):
            raise ValueError(f"Error: '{nb_path}' is not a Jupyter notebook file.")

        with open(nb_path) as f:
            nb = nbformat.read(f, as_version=4)
    else:
        nb = nbformat.reads(file_content, as_version=4)

    if nb.metadata: return True

    for cell in nb.cells:
        if cell['cell_type'] != 'code': continue
        if cell['execution_count'] is not None: return True
        if cell.metadata: return True
        for output in cell.get('outputs', []):
            if 'execution_count' in output and output['execution_count'] is not None: return True
            if 'metadata' in output and output['metadata']: return True

    return False


# %%
is_nb_unclean(file_content='{"cells":[]}')

# %%
is_nb_unclean('../../test_proj/nbs/notebook1.ipynb')

# %%
show_doc(this.get_unclean_nbs)


# %%
#|export
def get_unclean_nbs(root_path: str = None, ignore_underscores: bool = False):
    """
    Get all notebooks that have metadata or execution count.
    
    Returns:
        bool: True if all notebooks are clean, False otherwise.
    """
    if root_path is None:
        root_path, config = get_project_root_and_config()
    else:
        root_path = Path(root_path)
        config = read_config(root_path / nblite_config_file_name)
    
    unclean_nbs = []
    for cl in config.code_locations.values():
        if not cl.format == 'ipynb': continue
        cl_nbs = get_code_location_nbs(root_path, cl, ignore_underscores=ignore_underscores)
        unclean_nbs.extend([nb_path.relative_to(root_path) for nb_path in cl_nbs if is_nb_unclean(nb_path)])
    return unclean_nbs


# %%
get_unclean_nbs('../../test_proj')

# %%
show_doc(this.get_relative_path)


# %%
#|export
def get_relative_path(from_path: str, to_path: str):
    """Returns the relative path to the root path."""
    return Path(os.path.relpath(Path(to_path).resolve(), start=Path(from_path).resolve()))


# %%
get_relative_path('.', '/Users/lukastk/')
