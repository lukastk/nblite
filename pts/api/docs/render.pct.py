# %% [markdown]
# # docs.render

# %%
#|default_exp docs.render

# %%
#|hide
import nblite; from nblite import show_doc; nblite.nbl_export()

# %%
#|export
from pathlib import Path
from typing import Union
from tempfile import TemporaryDirectory
import yaml
import shutil
import subprocess
import nbformat

from nblite.const import nblite_assets_path, format_to_file_exts
from nblite.utils import get_project_root_and_config, read_config, _root_path_and_config_helper
from nblite.config import CodeLocation, NBLiteConfig
from nblite.export import convert_nb, get_cell_with_directives
from nblite.docs.cell_docs import render_cell_doc

# %%
#|hide
import nblite.docs.render as this_module

# %%
#|hide
root_path, config = get_project_root_and_config(Path('../../../test_proj/'))


# %%
#|exporti
def process_and_remove_nbdev_directives(nb_path: Path) -> dict:
    """Processes and removes nbdev directives from a notebook."""
    nb = nbformat.read(nb_path, as_version=4)

    nb['cells'] = [get_cell_with_directives(c) for c in nb['cells']]
    proc_cells = []
    for cell in nb['cells']:
        directive_keys = [d['directive'] for d in cell['directives']]
        directive_lines = [d['cell_line'] for d in cell['directives']]
        
        if 'export' in directive_keys or 'exporti' in directive_keys: # Add rendered docstring of all function and class definitions in the cell
            doc_cell = nbformat.notebooknode.NotebookNode({
                'cell_type': 'markdown',
                'metadata': {},
                'source': render_cell_doc(cell['source']),
            })
            proc_cells.append(doc_cell)
        if any([d in directive_keys for d in ['hide', 'export', 'exporti']]): continue
        
        lines_to_remove = [i for i,dk in zip(directive_lines, directive_keys) if not dk.endswith(':')] # All quarto directive keys end with ':'
        cell['source'] = '\n'.join([l for i,l in enumerate(cell['source'].split('\n')) if i not in lines_to_remove])
        del cell['source_without_directives']
        del cell['directives']
        proc_cells.append(cell)
        
    nb['cells'] = proc_cells
    _, nb = nbformat.validator.normalize(nb)
    nbformat.write(nb, nb_path)


# %%
#|exporti
def convert_to_ipynb_and_copy_to_folder(dest_folder: Path, root_path: Path, cl: CodeLocation) -> Path:
    nbs_folder = root_path / cl.path
    cl_file_ext = format_to_file_exts[cl.format]
    for f in nbs_folder.glob(f"**/*"):
        if f.is_dir(): continue
        if f.parent.name.startswith('.'): continue
        
        rel_path = f.relative_to(nbs_folder)
        if any(p.startswith('_') for p in rel_path.parts): continue
        
        if f.name.endswith(cl_file_ext):
            if cl.format != "ipynb":
                file_name = f.name[:-len(cl_file_ext)-1] + ".ipynb"
                dest_path = dest_folder / rel_path.parent / file_name
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                convert_nb(f, dest_path, cl.format, "ipynb")
            else:
                (dest_folder / rel_path).parent.mkdir(parents=True, exist_ok=True)
                dest_path = dest_folder / rel_path
                shutil.copy(f, dest_path)
            process_and_remove_nbdev_directives(dest_path)
        elif f.suffix in ['.md', '.qmd']:
            dest_path = dest_folder / rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(f, dest_path)


# %%
#|exporti
def __process_subfolder(folder_path: Path, rel_path: Path) -> dict:
    contents = {}
    contents['section'] = folder_path.name
    rel_folder_path = folder_path.relative_to(rel_path)
    sub_contents = []
    for subfolder_path in folder_path.glob('*'):
        if not subfolder_path.is_dir(): continue
        if any(p.startswith('_') for p in subfolder_path.relative_to(rel_path).parts): continue
        sub_contents.append(__process_subfolder(subfolder_path, rel_path))
    if len(sub_contents) > 0:
        contents['contents'] = [{'auto': f"{rel_folder_path}/*"}, *sub_contents]
    else:
        contents['contents'] = f"{rel_folder_path}/*"
    return contents

def build_sidebar_section(parent_path: Path) -> dict:
    """
    Recursively build sidebar YAML structure for Quarto from a directory tree.
    """
    contents = [{'auto': f"/*"}]
    for subfolder_path in parent_path.glob('*'):
        if not subfolder_path.is_dir(): continue
        if any(p.startswith('_') for p in subfolder_path.relative_to(parent_path).parts): continue
        contents.append(__process_subfolder(subfolder_path, parent_path))
    return contents


# %%
build_sidebar_section(root_path / 'nbs')


# %%
#|exporti
def generate_quarto_yml(docs_nbs_path: Path, src_path: Path, config: NBLiteConfig) -> dict:
    with open(nblite_assets_path / 'docs' / '_quarto.yml', 'r') as file:
        quarto_yml = yaml.safe_load(file)
    quarto_yml['website']['title'] = config.docs_title
    quarto_yml['website']['sidebar']['contents'] = build_sidebar_section(src_path)
    with open(docs_nbs_path / '_quarto.yml', 'w') as file:
        yaml.dump(quarto_yml, file)


# %%
with TemporaryDirectory() as tmp_dir:
    tmp_dir = Path(tmp_dir)
    convert_to_ipynb_and_copy_to_folder(tmp_dir, root_path, config.code_locations['nbs'])
    generate_quarto_yml(tmp_dir, root_path / 'nbs', config)


# %%
#|exporti
def prepare_docs(dest_folder:Path, docs_cl:Union[str,None] = None, root_path:Union[str,None] = None, config_path:Union[str,None] = None):
    root_path, config = _root_path_and_config_helper(root_path, config_path)
    docs_cl = docs_cl or config.docs_cl
    if not docs_cl: raise ValueError("No 'docs_cl' provided and no default 'docs_cl' provided in config.")
    cl_path = root_path / config.code_locations[docs_cl].path
    if not cl_path.exists(): raise FileNotFoundError(f"Code location '{docs_cl}' not found.")
    dest_folder = Path(dest_folder)
    convert_to_ipynb_and_copy_to_folder(dest_folder, root_path, config.code_locations[docs_cl])
    generate_quarto_yml(dest_folder, cl_path, config)
    shutil.copy(nblite_assets_path / 'docs' / 'styles.css', dest_folder / 'styles.css')        


# %%
#|hide
show_doc(this_module.preview_docs)


# %%
#|export
def preview_docs(docs_cl:Union[str,None] = None, root_path:Union[str,None] = None, config_path:Union[str,None] = None, verbose:bool=False):
    with TemporaryDirectory() as tmp_dir:
        prepare_docs(Path(tmp_dir), docs_cl, root_path, config_path)
        if verbose:
            subprocess.run(['quarto', 'preview'], cwd=tmp_dir)
        else:
            subprocess.run(['quarto', 'preview'], cwd=tmp_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# %%
#|hide
show_doc(this_module.render_docs)


# %%
#|export
def render_docs(output_folder:Union[str,None], docs_cl:Union[str,None] = None, root_path:Union[str,None] = None, config_path:Union[str,None] = None, verbose:bool=False):
    root_path, _ = _root_path_and_config_helper(root_path, config_path)
    doc_folder_name = Path(output_folder).name # Necessary to get the quarto printouts to be correct
    with TemporaryDirectory() as tmp_dir:
        prepare_docs(Path(tmp_dir), docs_cl, root_path, config_path)
        if verbose:
            subprocess.run(['quarto', 'render', '--output-dir', doc_folder_name], cwd=tmp_dir)
        else:
            subprocess.run(['quarto', 'render', '--output-dir', doc_folder_name], cwd=tmp_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        shutil.copytree(Path(tmp_dir) / doc_folder_name, output_folder, dirs_exist_ok=True)


# %%
render_docs(root_path / '_docs', root_path=root_path, docs_cl='pcts')

# %%
render_docs(root_path / '_docs', root_path=root_path, docs_cl='nbs')
