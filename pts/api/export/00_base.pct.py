# %% [markdown]
# # export.base

# %%
#|default_exp export.base

# %%
#|hide
import nblite; from nblite import show_doc; nblite.nbl_export()

# %%
#|export
import tempfile
import os
from pathlib import Path
from typer import Argument
from typing_extensions import Annotated
from typing import Union, List, Tuple
import json
import nbformat

from nblite.const import nblite_config_file_name, format_to_file_exts
from nblite.config import read_config, get_project_root_and_config, get_top_level_code_locations
from nblite.const import format_to_jupytext_format
from nblite.utils import get_nb_format_from_path, get_nb_path_info

# %%
#|hide
from nblite.export.nb_export import export
import nblite.export.base as this_module

# %%
#|hide
show_doc(this_module.convert_nb)


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
#|hide
show_doc(this_module.get_nb_module_export_name)


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
#|hide
export(root_path)

# %%
get_nb_module_export_name(root_path / 'nbs/submodule/notebook3.ipynb', root_path / 'my_module')

# %%
get_nb_module_export_name(root_path / 'pcts/submodule/notebook3.pct.py', root_path / 'my_module')

# %%
#|hide
show_doc(this_module.get_nb_module_export_path)


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
#|hide
show_doc(this_module.get_nb_twin_paths)


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
#|hide
show_doc(this_module.clean_ipynb)


# %%

#|export
def clean_ipynb(nb_path:str, remove_outputs:bool=False, remove_cell_metadata:bool=True, remove_top_metadata:bool=False):
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
    if remove_cell_metadata:
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
        
    if remove_top_metadata:
        nb_json['metadata'] = {}
        
    with open(nb_path, "w") as f:
        json.dump(nb_json, f, indent=4)


# %%
clean_ipynb(root_path / 'nbs/notebook1.ipynb', remove_outputs=True, remove_cell_metadata=True)

# %%
#|hide
show_doc(this_module.get_nb_source_and_output_hash)


# %%
#|export
def get_nb_source_and_output_hash(nb:Union[str,nbformat.notebooknode.NotebookNode], return_nb:bool=False) -> Tuple[bool, str]:
    """
    Check the source hash of a notebook.
    """
    import hashlib
    if not isinstance(nb, nbformat.notebooknode.NotebookNode):
        nb = nbformat.read(nb, as_version=4)
        
    def get_clean_output(output):
        return { k:v for k,v in output.items() if k not in ['metadata', 'execution_count'] }
    
    def get_clean_cell(cell):
        _cell = { 'source': cell.source }
        if 'outputs' in cell:
            _cell['outputs'] = list(map(get_clean_output, cell.outputs))
        return _cell
        
    nb_src_and_out = list(map(get_clean_cell, nb.cells))
    nb_src_and_out_hash = hashlib.sha256(json.dumps(nb_src_and_out).encode('utf-8')).hexdigest()
    if 'nblite_source_hash' in nb.metadata:
        has_changed = nb.metadata['nblite_source_hash'] != nb_src_and_out_hash
    else:
        has_changed = True
        
    if return_nb:
        return nb_src_and_out_hash, has_changed, nb, nb_src_and_out
    else:
        return nb_src_and_out_hash, has_changed


# %%
nb_src_and_out_hash, has_changed = get_nb_source_and_output_hash(root_path / 'nbs' / 'notebook1.ipynb')
has_changed

# %%
nb_src_and_out_hash, has_changed, nb, nb_src_and_out = get_nb_source_and_output_hash(root_path / 'nbs' / 'notebook1.ipynb', return_nb=True)
has_changed

# %%
#|hide
show_doc(this_module.fill_ipynb)


# %%
#|export
def fill_ipynb(
    nb_path:str,
    cell_exec_timeout=None,
    remove_pre_existing_outputs:bool=True,
    remove_cell_metadata:bool=True,
    working_dir:Union[str,None]=None,
    dry_run:bool=False,
) -> nbformat.notebooknode.NotebookNode:
    """
    Execute a notebook and fills it with the outputs.
    
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
    import hashlib

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
        # Add the source and output hash to the notebook metadata
        with open(nb_path, "w") as f: nbformat.write(nb, f)
        hashed_nb_source, has_changed, nb, _ = get_nb_source_and_output_hash(nb_path, return_nb=True)
        nb.metadata['nblite_source_hash'] = hashed_nb_source
        with open(nb_path, "w") as f: nbformat.write(nb, f)
        
        # Remove metadata from each cell
        if remove_cell_metadata:
            clean_ipynb(nb_path, remove_outputs=False, remove_cell_metadata=remove_cell_metadata)
            
    return nb


# %%
fill_ipynb(root_path / 'nbs' / 'notebook1.ipynb');

# %%
#|hide
show_doc(this_module.get_cell_with_directives)


# %%
#|exporti
def remove_directive_lines(code):
    return "\n".join([ l for l in code.split('\n') if not l.startswith('#|') ])


# %%
#|export
def get_cell_with_directives(cell:dict):
    """
    Get the cell with the directives from a cell as metadata.
    """
    if not 'source' in cell: return cell
    code = cell['source']
    cell['directives'] = []
    cell['source_without_directives'] = remove_directive_lines(code)
    for code_i, code_line in enumerate(code.split('\n')):
        if not code_line.startswith('#|'): continue
        _directive_str = code_line.split('#|', 1)[1].strip()
        directive = _directive_str.split()[0]
        directive_args = _directive_str[len(directive):].strip()
        cell['directives'].append({'directive': directive, 'args': directive_args, 'cell_line': code_i})
    return cell


# %%
#|hide
show_doc(this_module.get_nb_directives)


# %%
#|export
def get_nb_directives(nb_path, nb_format=None, only_code_cells:bool=True):
    """
    Get the directives from a notebook.
    """
    with tempfile.NamedTemporaryFile(suffix='.ipynb', delete=True) as tmp_nb:
        if not nb_path.as_posix().endswith('.ipynb'):
            convert_nb(nb_path, tmp_nb.name, nb_format)
            nb_path = tmp_nb.name
        with open(nb_path) as f:
            nb = nbformat.read(f, as_version=4)
    
    directives = []
    
    def remove_directive_lines(code):
        return "\n".join([ l for l in code.split('\n') if not l.startswith('#|') ])

    for cell in nb['cells']:
        if cell['cell_type'] != 'code' and only_code_cells: continue
        cell = get_cell_with_directives(cell)
        for directive in cell['directives']:
            directives.append({'directive': directive['directive'], 'args': directive['args'], 'cell': cell})
        
    return directives


# %%
directives = get_nb_directives(root_path / 'nbs' / 'func_notebook.ipynb')
for directive in directives:
    print(f"#|{directive['directive']} {directive['args']}")

# %%
#|hide
show_doc(this_module.lookup_directive)


# %%
#|export
def lookup_directive(nb_directives, directive):
    """
    Lookup the latest ocurring directive from the output of `get_nb_directives`.
    """
    for d in reversed(nb_directives):
        if d['directive'] == directive:
            return d
    return None


# %%
lookup_directive(directives, 'set_func_signature')

# %%
#|hide
show_doc(this_module.generate_md_file)


# %%
#|export
def generate_md_file(nb_path:Union[str,None] = None, out_path:Union[str,None] = None, nb_format:Union[str,None] = None):
    """
    Generate a markdown file from a notebook.
    
    Args:
        root_path: The root path of the project. If not provided, the project root will be determined by searching for a nblite.toml file.
    """
    # Hot reloading, to reduce loading time for the CLI
    import jupytext
    from jupytext.config import JupytextConfiguration
    from jupytext.formats import long_form_one_format

    nb_format = nb_format or get_nb_format_from_path(nb_path)
    nb_format_jupytext = format_to_jupytext_format[nb_format]
    config = JupytextConfiguration()
    config.set_default_format_options(long_form_one_format(nb_format), read=False)
    config.notebook_metadata_filter = '-all'
    nb = jupytext.read(nb_path, fmt=nb_format_jupytext)

    # Removed cells with the #|hide directive
    nb_cells_with_directives = list(map(get_cell_with_directives, nb['cells']))
    processed_nb_cells = []
    for cell in nb_cells_with_directives:
        if any([d['directive'] == 'hide' for d in cell['directives']]): continue
        del cell['directives']
        processed_nb_cells.append(cell)
    nb['cells'] = processed_nb_cells

    jupytext.write(nb, out_path, fmt='md', config=config)


# %%
import tempfile

# Create a temporary file path
with tempfile.NamedTemporaryFile(delete=True, suffix='.md') as temp_file:
    generate_md_file(root_path / 'nbs' / 'notebook1.ipynb', temp_file.name)
    md_file_content = Path(temp_file.name).read_text()
    print("\n".join(md_file_content.splitlines()[:10]))

# %%
#|hide
show_doc(this_module.generate_readme)


# %%
#|export
def generate_readme(root_path:Union[str,None] = None):
    """
    Generate a README.md file for the project from the index.ipynb file.
    
    Args:
        root_path: The root path of the project. If not provided, the project root will be determined by searching for a nblite.toml file.
    """
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

    generate_md_file(index_nb_path, root_path / 'README.md', top_level_cl.format)


# %%
generate_readme(root_path)

# %%
#|hide
show_doc(this_module.export_to_lib)


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
root_path = Path('../../../test_proj/')

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
#|hide
show_doc(this_module.clear_code_location)


# %%
#|export
def clear_code_location(cl_key: str, root_path: Union[str,None]=None):
    """
    Clear the code location of a given key.
    """
    if root_path is None:
        root_path, config = get_project_root_and_config()
    else:
        root_path = Path(root_path)
        config = read_config(root_path / nblite_config_file_name)
    
    top_code_locations = get_top_level_code_locations(config)
    if cl_key in top_code_locations:
        raise ValueError(f"Error: '{cl_key}' is a top-level code location and cannot be cleared.")
    
    cl_path = config.code_locations[cl_key].path
    cl_format = config.code_locations[cl_key].format
    file_ext = format_to_file_exts[cl_format]
    
    for file in (root_path / cl_path).glob(f'**/*.{file_ext}'):
        if not file.is_file(): continue
        if cl_format == 'module' and file.name.startswith('__') or file.name.startswith('.'): continue # Skip hidden files in module code locations
        file.unlink()
        
    # Remove empty folders
    for folder in (Path(root_path) / cl_path).glob('**/*'):
        if folder.is_dir() and not any(folder.iterdir()):  # Check if the directory is empty
            folder.rmdir()  # Remove the empty directory


# %%
clear_code_location('pcts', root_path)

# %%
#|hide
show_doc(this_module.clear_downstream_code_locations)


# %%
#|export
def clear_downstream_code_locations(root_path: Union[str,None]=None):
    """"""
    if root_path is None:
        root_path, config = get_project_root_and_config()
    else:
        root_path = Path(root_path)
        config = read_config(root_path / nblite_config_file_name)
    
    top_code_locations = get_top_level_code_locations(config)
    non_top_code_locations = [cl_key for cl_key in config.code_locations if cl_key not in top_code_locations]
    
    for cl_key in non_top_code_locations:
        clear_code_location(cl_key, root_path)


# %%
clear_downstream_code_locations(root_path)

# %%
#|hide
export(root_path) # Export so to not break tests in other notebooks
