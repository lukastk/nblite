# %% [markdown]
# # export.nb_export
#
# > Contains the logic for exporting notebooks.

# %%
#|default_exp export.nb_export

# %%
#|hide
import nblite; from nblite import show_doc; nblite.nbl_export()

# %%
#|export
from pathlib import Path
from typer import Argument
from typing_extensions import Annotated
from typing import Union, List
import os

from nblite.const import nblite_config_file_name, DISABLE_NBLITE_EXPORT_ENV_VAR
from nblite.config import read_config, parse_config_dict, get_project_root_and_config
from nblite.const import format_to_jupytext_format
from nblite.utils import get_nb_format_from_path, get_code_location_nbs, get_nb_path_info
from nblite.export import convert_nb, get_nb_directives, lookup_directive, export_to_lib_as_func, export_to_lib

# %%
import shutil
import nblite.export.nb_export as this_module

# %%
#|hide
show_doc(this_module.export)


# %%
#|export
def export(root_path:Union[str,None] = None, config_path:Union[str,None] = None, export_pipeline:Union[str,None] = None, nb_paths:Union[List[str],None] = None):
    """
    Export notebooks in an nblite project, as specified in the nblite.toml config file.
    
    If the `root_path` is not provided, nblite will search for a nblite.toml file in the current directory
    and all parent directories, and use the directory containing the nblite.toml file as the root folder.
    
    Args:
        root_path: Path to the root folder of the nblite project.
        config_path: Path to the nblite.toml config file. Will be used instead of the config file in the root folder if provided.
        export_pipeline: The export pipeline to use. E.g. 'nbs->pts,pts->lib'.
    """
    disable_export = os.environ.get(DISABLE_NBLITE_EXPORT_ENV_VAR, False)
    
    if disable_export and disable_export.lower() == 'true':
        print(f"Environment variable {DISABLE_NBLITE_EXPORT_ENV_VAR} is set to True, skipping export.")
        return
    
    if root_path is None:
        root_path, config = get_project_root_and_config()
    else:
        root_path = Path(root_path)
        config = read_config(root_path / nblite_config_file_name)
        
    if config_path: # If config_path is provided, use it instead of the config file in the root folder
        config = read_config(config_path)
    
    if not root_path.is_dir():
        raise NotADirectoryError(f"{root_path} is not a valid directory")
    
    # Replace the export pipeline in the config with the one provided as an argument
    config_dict = config.model_dump()
    if export_pipeline is not None:
        config_dict['export_pipeline'] = export_pipeline
    config = parse_config_dict(config_dict)
    
    if nb_paths is not None:
        nb_paths = [Path(p).resolve() for p in nb_paths]
    
    for rule in config.export_pipeline:
        from_conf = config.code_locations[rule.from_key]
        to_conf = config.code_locations[rule.to_key]
        from_file_ext = from_conf.file_ext
        
        ignore_dunders = to_conf.format == 'module' # Don't export dundered nbs to module code locations
        from_nb_paths = get_code_location_nbs(root_path, from_conf, ignore_dunders=ignore_dunders)
        
        if to_conf.format == 'module':            
            for fp in from_nb_paths:
                nb_directives = get_nb_directives(fp)
                export_as_func_directive = lookup_directive(nb_directives, 'export_as_func')
                export_as_func = export_as_func_directive is not None and export_as_func_directive['args'] == 'true'
                
                if export_as_func:
                    export_to_lib_as_func(fp, root_path / to_conf.path, nb_format=from_conf.format)
                else:
                    export_to_lib(fp, root_path / to_conf.path, nb_format=from_conf.format)
        else:
            to_file_ext = to_conf.file_ext
            for fp in from_nb_paths:
                if nb_paths is not None and fp.resolve() not in nb_paths:
                    continue
                
                sub_path = fp.relative_to(root_path / from_conf.path)
                dest_fname = sub_path.name[:-len(from_file_ext)] + to_file_ext
                dest_path = root_path / to_conf.path / sub_path.parent / dest_fname
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                convert_nb(fp, dest_path, from_conf.format, to_conf.format)


# %%
root_path = Path('../../../test_proj/')
shutil.rmtree(root_path / 'my_module', ignore_errors=True)
shutil.rmtree(root_path / 'pcts', ignore_errors=True)
shutil.rmtree(root_path / 'lgts', ignore_errors=True)

# %%
export(root_path)

# %%
export(root_path, nb_paths=[root_path / 'nbs/notebook1.ipynb'])
