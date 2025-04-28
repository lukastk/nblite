# %% [markdown]
# # export.base

# %%
#|default_exp export.base

# %%
#|hide
import nblite; from nbdev.showdoc import show_doc; nblite.nbl_export()

# %%
#|export
import tempfile
import os
from pathlib import Path
from typer import Argument
from typing_extensions import Annotated
from typing import Union, List
import json

from nblite.const import nblite_config_file_name
from nblite.config import read_config, parse_config_dict, get_project_root_and_config
from nblite.const import format_to_jupytext_format
from nblite.utils import get_nb_format_from_path, get_code_location_nbs, get_nb_path_info

# %%
import shutil
import nblite.export.base

# %%
show_doc(nblite.export.base.convert_nb)


# %%
#|export
def convert_nb(nb_path:str, dest_path:str, nb_format:str=None, dest_format:str=None):
    """
    Convert a notebook from one format to another.
    
    Args:
        nb_path: Path to the notebook to convert.
        dest_path: Path to the destination file.
        nb_format: Format of the notebook to convert.
        dest_format: Format of the destination file.
    """
    # Hot reloading, to reduce loading time for CLI
    import jupytext
    from jupytext.config import JupytextConfiguration
    from jupytext.formats import long_form_one_format
    
    if nb_format is None:
        nb_format = get_nb_format_from_path(nb_path)
    if dest_format is None:
        dest_format = get_nb_format_from_path(dest_path)
        
    jpt_src_fmt = format_to_jupytext_format[nb_format]
    jpt_dest_fmt = format_to_jupytext_format[dest_format]
    
    nb_converted = jupytext.read(nb_path, fmt=jpt_src_fmt)
    
    # Exclude all metadata frontmatter from the notebook
    config = JupytextConfiguration()
    config.set_default_format_options(long_form_one_format(jpt_dest_fmt), read=False)
    config.notebook_metadata_filter = '-all'
    
    jupytext.write(nb_converted, dest_path, fmt=jpt_dest_fmt, config=config)


# %%

root_path = Path('../../../test_proj/')

(root_path / 'pcts').mkdir(parents=True, exist_ok=True)
(root_path / 'lgts').mkdir(parents=True, exist_ok=True)

convert_nb(
    nb_path=root_path / 'nbs' / 'notebook1.ipynb',
    dest_path=root_path / 'pcts' / 'notebook1.pct.py',
)

convert_nb(
    nb_path=root_path / 'nbs' / 'notebook2.ipynb',
    dest_path=root_path / 'pcts' / 'notebook2.pct.py',
)

convert_nb(
    nb_path=root_path / 'pcts' / 'notebook1.pct.py',
    dest_path=root_path / 'lgts' / 'notebook1.lgt.py',
)

convert_nb(
    nb_path=root_path / 'pcts' / 'notebook2.pct.py',
    dest_path=root_path / 'lgts' / 'notebook2.lgt.py',
)

# %%
# Test to see if the conversion is reversible
with tempfile.TemporaryDirectory() as tmpdirname:
    tempdir = Path(tmpdirname)
    convert_nb(
        root_path / "pcts" / "notebook1.pct.py",
        tempdir / "nb.ipynb",
    )
    convert_nb(
        tempdir / "nb.ipynb",
        tempdir / "nb.pct.py",
    )
    assert Path(root_path / "pcts" / "notebook1.pct.py").read_text() == Path(tempdir / "nb.pct.py").read_text()

# %%
show_doc(nblite.export.base.get_nb_module_export_name)


# %%
#|export
def get_nb_module_export_name(nb_path: str, lib_path: str) -> str:
    import nbdev.export
    exp = nbdev.export.ExportModuleProc()
    if not Path(nb_path).as_posix().endswith('.ipynb'):
        tmp_nb_path = tempfile.NamedTemporaryFile(suffix='.ipynb', delete=False)
        convert_nb(nb_path, tmp_nb_path.name)
        nb_path = tmp_nb_path.name
    nb = nbdev.export.NBProcessor(nb_path, [exp], debug=False)
    nb.process()
    for mod,cells in exp.modules.items():
        if nbdev.export.first(1 for o in cells if o.cell_type=='code'):
            all_cells = exp.in_all[mod]
            nm = getattr(exp, 'default_exp', None) if mod=='#' else mod
            return nm
    return None


# %%
get_nb_module_export_name(root_path / 'nbs/submodule/notebook3.ipynb', root_path / 'my_module')

# %%
show_doc(nblite.export.base.get_nb_module_export_path)


# %%
#|export
def get_nb_module_export_path(nb_path: str, lib_path: str) -> str:
    nb_mod_export_name = get_nb_module_export_name(nb_path, lib_path)
    if nb_mod_export_name:
        return (Path(lib_path) / nb_mod_export_name.replace('.', '/')).with_suffix('.py').resolve()
    return None


# %%
get_nb_module_export_path(root_path / 'nbs/submodule/notebook3.ipynb', root_path / 'my_module')

# %%
show_doc(nblite.export.base.get_nb_twin_paths)


# %%
#|export
def get_nb_twin_paths(nb_path: str, root_path: str):
    """For a given notebook in a code location, returns the paths to all its 'twins' (the corresponding notebooks in the other code locations).
    The original given notebook path is also returned."""
    if root_path is None:
        root_path, config = get_project_root_and_config()
    else:
        root_path = Path(root_path)
        config = read_config(root_path / nblite_config_file_name)
    nb_path = Path(nb_path).resolve()
    cl_nb_name = get_nb_path_info(nb_path, root_path, config)['cl_name']
    
    nb_twins = []
    for loc in config.code_locations.values():
        if loc.format == 'module':
            twin_path = get_nb_module_export_path(nb_path, root_path / loc.path)
            if twin_path is None: continue # Some notebooks are not exported to a module
        else:
            twin_path = root_path / loc.path / cl_nb_name.with_suffix('.' + loc.file_ext)
        nb_twins.append(Path(twin_path).resolve())
        
    nb_twins = tuple(sorted([fp.as_posix() for fp in nb_twins]))
    return nb_twins


# %%
get_nb_twin_paths(root_path / 'nbs/folder/notebook4.ipynb', root_path)

# %%
show_doc(nblite.export.base.get_nb_as_function)


# %%
#|export
def get_nb_as_function():
    pass


# %%
show_doc(nblite.export.base.export_to_lib)


# %%
#|exporti
def _nbdev_nb_export(nbname:str, # Filename of notebook 
              lib_path:str=None, # Path to destination library.  If not in a nbdev project, defaults to current directory.
              procs=None,        # Processors to use
              name:str=None,     # Name of python script {name}.py to create.
              debug:bool=False,  # Debug mode
              source_nb_path:str=None # Path to source notebook. If not provided, the notebook name will be used.
             ):
    """
    Copied from `nbdev.export.nb_export` and modified, adding the extra argument
    `source_nb_path` to use as the source notebook path in `mod_maker.dest2nb`.
    
    Source: https://github.com/AnswerDotAI/nbdev/blob/main/nbs/api/04_export.ipynb
    """
    import nbdev.export
    if lib_path is None: lib_path = nbdev.export.get_config().lib_path if nbdev.export.is_nbdev() else '.'
    exp = nbdev.export.ExportModuleProc()
    nb = nbdev.export.NBProcessor(nbname, [exp]+nbdev.export.L(procs), debug=debug)
    nb.process()
    for mod,cells in exp.modules.items():
        if nbdev.export.first(1 for o in cells if o.cell_type=='code'):
            all_cells = exp.in_all[mod]
            nm = nbdev.export.ifnone(name, getattr(exp, 'default_exp', None) if mod=='#' else mod)
            if not nm:
                nbdev.export.warn(f"Notebook '{nbname}' uses `#|export` without `#|default_exp` cell.\n"
                     "Note nbdev2 no longer supports nbdev1 syntax. Run `nbdev_migrate` to upgrade.\n"
                     "See https://nbdev.fast.ai/getting_started.html for more information.")
                return
            mm = nbdev.export.ModuleMaker(dest=lib_path, name=nm, nb_path=nbname, is_new=bool(name) or mod=='#')
            if source_nb_path is not None:
                py_file_path = Path(lib_path)/(nm.replace('.','/') + ".py")
                relative_path = os.path.relpath(source_nb_path, start=py_file_path)
                mm.dest2nb = relative_path
                mm.hdr = f"# %% {relative_path}"
            mm.make(cells, all_cells, lib_path=lib_path)


# %%
#|export
def export_to_lib(nb_path, lib_path, nb_format=None):
    if nb_format is None:
        nb_format = get_nb_format_from_path(nb_path)
    with tempfile.NamedTemporaryFile(delete=True, suffix='.ipynb') as tmpfile:
        convert_nb(nb_path, tmpfile.name, nb_format=nb_format)
        _nbdev_nb_export(tmpfile.name, lib_path, source_nb_path=nb_path)


# %%
root_path = Path(root_path / '')

export_to_lib(
    root_path / 'nbs' / 'notebook1.ipynb',
    root_path / 'my_module',
)

export_to_lib(
    root_path / 'nbs' / 'notebook2.ipynb',
    root_path / 'my_module',
)

# %%
export_to_lib(
    root_path / 'pcts' / 'notebook1.pct.py',
    root_path / 'my_module',
)

export_to_lib(
    root_path / 'pcts' / 'notebook2.pct.py',
    root_path / 'my_module',
)

# %%
show_doc(nblite.export.base.export)


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
        
        from_nb_paths = get_code_location_nbs(root_path, from_conf, ignore_underscores=True)
        
        if to_conf.format == 'module':
            for fp in from_nb_paths:
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
shutil.rmtree(root_path / 'my_module', ignore_errors=True)
shutil.rmtree(root_path / 'pcts', ignore_errors=True)
shutil.rmtree(root_path / 'lgts', ignore_errors=True)

# %%
export(root_path)

# %%
export(root_path, nb_paths=[root_path / 'nbs/notebook1.ipynb'])

# %%
show_doc(nblite.export.base.clean_ipynb)


# %%

#|export
def clean_ipynb(nb_path:str, remove_outputs:bool=False, remove_metadata:bool=True):
    """
    Clean a notebook by removing all outputs and metadata.
    
    Args:
        nb_path: Path to the notebook to clean.
        remove_outputs: Whether to remove the outputs from the notebook.
        remove_metadata: Whether to remove the metadata from the notebook.
    """
    import nbformat
    from nbconvert.preprocessors import ExecutePreprocessor

    nb_path = Path(nb_path)

    if not nb_path.as_posix().endswith('.ipynb'):
        raise ValueError(f"Error: '{nb_path}' is not a Jupyter notebook file.")

    with open(nb_path) as f:
        nb = nbformat.read(f, as_version=4)
                
    # Remove outputs from each cell
    if remove_outputs:
        for cell in nb.cells:
            if cell['cell_type'] == 'code':
                cell.outputs = []
            
    # Remove metadata from each cell
    if remove_metadata:
        for cell in nb.cells:
            if cell['cell_type'] == 'code':
                cell['execution_count'] = None
            cell.metadata = {} 
            for output in cell.get('outputs', []):
                if 'execution_count' in output: output['execution_count'] = None
                if 'metadata' in output: output['metadata'] = {}
            
    with open(nb_path, "w") as f:
        nbformat.write(nb, f)
        
    with open(nb_path) as f:
        nb_json = json.load(f)
    nb_json['metadata'] = {}
    with open(nb_path, "w") as f:
        json.dump(nb_json, f, indent=4)


# %%
clean_ipynb(root_path / 'nbs/notebook1.ipynb', remove_outputs=True, remove_metadata=True)

# %%
show_doc(nblite.export.base.fill_ipynb)


# %%
#|export
def fill_ipynb(
    nb_path:str,
    cell_exec_timeout=None,
    remove_pre_existing_outputs:bool=True,
    remove_metadata:bool=True,
    working_dir:Union[str,None]=None,
    dry_run:bool=False,
):
    """
    Execute a notebook and fill it with the outputs.
    
    Cells can be skipped by adding the following directives to the cell:
    - `#|skip_evals`: Skip current and subsequent cells, until `#|skip_evals_stop` is encountered.
    - `#|skip_evals_stop`: Stop skipping cells.
    - `#|eval: false`: Skip the cell.
    
    Args:
        nb_path: Path to the notebook to fill.
        cell_exec_timeout: Timeout for cell execution.
        remove_pre_existing_outputs: Whether to remove the pre-existing outputs from the notebook.
        remove_metadata: Whether to remove the metadata from the notebook.
    """
    import nbformat
    from nbconvert.preprocessors import ExecutePreprocessor

    nb_path = Path(nb_path)
    if not nb_path.as_posix().endswith('.ipynb'):
        raise ValueError(f"Error: '{nb_path}' is not a Jupyter notebook file.")

    with open(nb_path) as f:
        nb = nbformat.read(f, as_version=4)

    # Remove outputs from each cell
    if remove_pre_existing_outputs:
        for cell in nb.cells:
            if cell['cell_type'] == 'code':
                cell.outputs = []

    # Parse directives for skipping cell evaluations
    skip_evals_mode = False
    skipped_cells = []
    for cell in nb.cells:
        skip_cell = False
        if cell['cell_type'] != 'code': continue
        for line in cell['source'].split('\n'):
            line = line.strip()
            if not line.startswith('#|'): continue
            directive = line.split('#|', 1)[1].strip()
            if directive == 'skip_evals':
                if skip_evals_mode:
                    raise ValueError("Already in skip_evals mode")
                skip_evals_mode = True
            elif directive == 'skip_evals_stop':
                if not skip_evals_mode:
                    raise ValueError("Not in skip_evals mode")
                skip_evals_mode = False
            elif directive.split(':', 1)[0].strip() == "eval":
                if directive.split(':', 1)[1].strip() == 'false':
                    skip_cell = True
            
        if skip_evals_mode or skip_cell:
            cell['cell_type'] = 'skip'
            skipped_cells.append(cell)

    # Create the execute preprocessor
    ep = ExecutePreprocessor(timeout=cell_exec_timeout, kernel_name="python3")
    if working_dir is None:
        working_dir = nb_path.parent
    resources = {"metadata": {"path": working_dir}}
    ep.preprocess(nb, resources)

    # Restore the cell types of skipped code cells
    for cell in skipped_cells:
        cell['cell_type'] = 'code'

    if not dry_run:
        with open(nb_path, "w") as f:
            nbformat.write(nb, f)
            
        # Remove metadata from each cell
        if remove_metadata:
            clean_ipynb(nb_path, remove_outputs=False, remove_metadata=True)


# %%
fill_ipynb(root_path / 'nbs/notebook1.ipynb')

# %%
show_doc(nblite.export.base.generate_readme)


# %%
#|export
def generate_readme(root_path:Union[str,None] = None):
    """
    Generate a README.md file for the project from the index.ipynb file.
    
    Args:
        root_path: The root path of the project. If not provided, the project root will be determined by searching for a nblite.toml file.
    """
    # Hot reloading, to reduce loading time for CLI
    import jupytext
    from jupytext.config import JupytextConfiguration
    from jupytext.formats import long_form_one_format
    
    if root_path is None:
        root_path, config = get_project_root_and_config()
    else:
        root_path = Path(root_path)
        config = read_config(root_path / nblite_config_file_name)
        
    if not config.code_locations: return
        
    # Get the top-level code location
    top_level_cl_key = config.export_pipeline[0].from_key
    top_level_cl = config.code_locations[top_level_cl_key]
    
    index_nb_path = root_path / top_level_cl.path / ('index.' + top_level_cl.file_ext)
    if not index_nb_path.exists(): return

    config = JupytextConfiguration()
    config.set_default_format_options(long_form_one_format(top_level_cl.format), read=False)
    config.notebook_metadata_filter = '-all'
    
    index_nb = jupytext.read(index_nb_path, fmt=top_level_cl.jupytext_format)

    jupytext.write(index_nb, root_path / 'README.md', fmt='md', config=config)
