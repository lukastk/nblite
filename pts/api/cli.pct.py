# %% [markdown]
# # cli

# %%
#|default_exp cli

# %%
#|hide
import nblite; from nbdev.showdoc import show_doc; nblite.nbl_export()

# %%
#|export
import typer
from typer import Argument, Option
from typing_extensions import Annotated
from types import FunctionType
from typing import Callable, Union, List
import inspect
import re
from pathlib import Path
import tempfile
import importlib.resources as resources
import sys
import subprocess

from nblite.const import nblite_config_file_name
from nblite.config import get_project_root_and_config, read_config
from nblite.export import convert_nb, generate_readme
from nblite.utils import get_code_location_nbs, is_nb_unclean, get_relative_path
from nblite.git import get_unstaged_nb_twins, get_git_root, is_file_staged

# %%
import nblite.cli

# %% [markdown]
# # Helper functions

# %%
show_doc(nblite.cli.parse_docstring)


# %%
#|exporti
def parse_docstring(docstring: str) -> tuple:
    """Parses a docstring to extract argument descriptions and return value description.

    Args:
        docstring: The docstring to parse.

    Returns:
        A tuple containing three elements: 
        1. The function summary as a string.
        2. A dictionary of argument descriptions.
        3. The return value description as a string.
    """
    _docstring = docstring.split('Args:', 1)
    func_summary, _docstring = _docstring if len(_docstring) == 2 else (docstring, '')
    arg_docstring, return_docstring = _docstring.split('Returns:', 1) if 'Returns:' in _docstring else (_docstring, '')
    
    # Use regex to find argument descriptions
    pattern = r'(\w+): (.+)'
    matches = re.findall(pattern, arg_docstring)
    args = {arg: desc.strip() for arg, desc in matches}
    
    return func_summary.strip(), args, return_docstring.strip()


# %%
func_summary, arg_docs, return_doc = parse_docstring(parse_docstring.__doc__)
print(func_summary)
print(arg_docs)
print(return_doc)

# %%
show_doc(nblite.cli.derive_cli_meta)


# %%
#|export
def derive_cli_meta(source_func: FunctionType) -> Callable:
    """
    A decorator factory that transfers docstring and argument annotations from a source functio and turns
    them into a typer annotations for the target function.

    Args:
        source_func: The function from which to derive the docstring and argument annotations.
    """
    def decorator(target_func: FunctionType) -> FunctionType:
        func_summary, arg_docs, return_doc = parse_docstring(source_func.__doc__)
        target_func.__doc__ = func_summary
        if return_doc.strip():
            target_func.__doc__ += f"\n\nReturns:\n{return_doc}"
        target_func.__doc__ = inspect.cleandoc("\n".join([l.strip() for l in target_func.__doc__.split("\n") if l.strip()]))
        typer_annotations = {
            arg_key: Annotated[arg_type, Argument(help=arg_docs[arg_key] if arg_key in arg_docs else '')]
            for arg_key, arg_type in source_func.__annotations__.items()
        }
        target_func.__annotations__.update(typer_annotations)
        return target_func
    return decorator


# %% [markdown]
# # Define CLIs

# %%
#|export
app = typer.Typer(invoke_without_command=True)

@app.callback()
def entrypoint(ctx: typer.Context):
    # If no subcommand is provided, show the help
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
            
def main():
    app()


# %%
#|export
from nblite.export import export, clean_ipynb, fill_ipynb


# %% [markdown]
# ## `nbl export`

# %%
#|export
@app.command(name='export')
def cli_export(
    root_path: Annotated[Union[str,None], Option(help="Path to the root folder of the nblite project.")] = None,
    config_path: Annotated[Union[str,None], Option(help="Path to the nblite.toml config file. Will be used instead of the config file in the root folder if provided.")] = None,
    export_pipeline: Annotated[Union[str,None], Option(help=" The export pipeline to use. E.g. 'nbs->pts,pts->lib'.")] = None,
    nb_paths: Annotated[Union[List[str],None], Option(help="If provided, only the notebooks specified in the paths will be exported.")] = None,
):
    """
    Export notebooks in an nblite project, as specified in the nblite.toml config file.
    
    If the `root_path` is not provided, nblite will search for a nblite.toml file in the current directory
    and all parent directories, and use the directory containing the nblite.toml file as the root folder.
    """
    export(root_path, config_path, export_pipeline, nb_paths)


# %% [markdown]
# ## `nbl readme`

# %%
#|export
@app.command(name='readme')
@derive_cli_meta(generate_readme)
def cli_readme(root_path=None):
    generate_readme(root_path)


# %% [markdown]
# ## `nbl convert`

# %%
#|export
@app.command(name='convert')
@derive_cli_meta(convert_nb)
def cli_convert(nb_path, dest_path, nb_format=None, dest_format=None):
    convert_nb(nb_path, dest_path, nb_format, dest_format)


# %% [markdown]
# ## `nbl init`

# %%
#|export
@app.command(name='init')
def cli_init(
    module_name: Annotated[Union[str,None], Option(help="The name of the module to create")] = None,
    root_path: Annotated[Union[str,None], Option(help="The root path of the project")] = None,
    use_defaults: Annotated[bool, Option(help="Use default values for module name and root path")] = False,
):
    """
    Initialize a new nblite project.
    """
    if module_name is None:
        default_module_name = Path('.').resolve().name
        if not use_defaults:
            module_name = typer.prompt(f"Enter the name of the module to create", default=default_module_name)
        else:
            module_name = default_module_name
    
    if root_path is None:
        root_path = Path('.').resolve()
    
    nblite_toml_template = (resources.files("nblite") / "defaults" / "default_nblite.toml").read_text()
    nblite_toml_str = nblite_toml_template.format(module_name=module_name)
    
    toml_path = root_path / 'nblite.toml'
    if toml_path.exists():
        typer.echo(f"Error: {toml_path} already exists")
        raise typer.Abort()
    
    with open(toml_path, 'w') as f:
        f.write(nblite_toml_str)
        
    typer.echo(f"Created {toml_path}.")
    typer.echo()
    typer.echo("Run `nbl new {CODE_LOCATION}/{NB_NAME}.{NB_FILE_EXT}` to create a new notebook. E.g. `nbl new nbs/main.ipynb`.")


# %% [markdown]
# ## `nbl new`

# %%
#|export
@app.command(name='new')
def cli_new(
    nb_path: Annotated[str, Argument(help="The notebook to create.")],
    mod_name: Annotated[Union[str,None], Option("-n", "--name", help="The name of the exported module. Defaults to the notebook path relative to the code location root.")] = None,
    nb_title: Annotated[Union[str,None], Option("-t", "--title", help="The display title of the notebook. Defaults to the notebook path stem.")] = None,
    root_path: Annotated[Union[str,None], Option("-r", "--root", help="The root path of the project. If not provided, the project root will be determined by searching for a nblite.toml file.")] = None,
):
    "Create a new notebook in a code location."
    nb_path = Path(nb_path).resolve()
    if root_path is None:
        root_path, config = get_project_root_and_config(nb_path.parent)
    else:
        root_path = Path(root_path)
        config = read_config(root_path / nblite_config_file_name)

    if nb_title is None:
        nb_title = nb_path.stem

    nb_format = None
    for loc in config.code_locations.values():
        cl_path = (root_path / loc.path).resolve()
        if nb_path.is_relative_to(cl_path):
            nb_format = loc.format
            if not nb_path.name.endswith(loc.file_ext):
                nb_path = Path(nb_path.as_posix() + '.' + loc.file_ext)
            if mod_name is None:
                rel_path = str(nb_path.relative_to(cl_path).parent)
                if rel_path == '.':
                    mod_name = nb_path.stem
                else:
                    mod_name = rel_path.replace('/', '.') + '.' + nb_path.stem
            break

    if nb_format is None:
        typer.echo(f"Error: '{nb_path}' is not inside any code location.")
        raise typer.Abort()

    if nb_path.exists():
        typer.echo(f"Error: '{nb_path}' already exists.")
        raise typer.Abort()

    with tempfile.NamedTemporaryFile(suffix='.pct.py') as tmp_nb:
        pct_content = (resources.files("nblite") / "defaults" / "default_nb.pct.py_").read_text().format(nb_title=nb_title, mod_name=mod_name)
        tmp_nb.write(pct_content.encode())
        tmp_nb.flush()
        nb_path.parent.mkdir(parents=True, exist_ok=True)
        convert_nb(tmp_nb.name, nb_path, nb_format="percent", dest_format=nb_format)
        
    typer.echo(f"Created {nb_path}")


# %%
cli_new(
    '../../test_proj/nbs/test.ipynb',
    root_path='../../test_proj'
)


# %%
# !rm ../../test_proj/nbs/test.ipynb

# %% [markdown]
# ## `nbl clean`

# %%
#|export
@app.command(name='clean')
def cli_clean(
    nb_paths: Annotated[Union[List[str], None], Argument(help="Specify the jupyter notebooks to clean. If omitted, all ipynb files in the project's code locations will be cleaned.")] = None,
    remove_outputs: Annotated[bool, Option(help="Remove the outputs from the notebook.")]=False,
    remove_metadata: Annotated[bool, Option(help="Remove the metadata from the notebook.")]=True,
    root_path: Annotated[Union[str,None], Option("-r", "--root", help="The root path of the project. If not provided, the project root will be determined by searching for a nblite.toml file.")] = None,
    ignore_underscores: Annotated[bool, Option("-i", "--ignore-underscores", help="Ignore notebooks that begin with an underscore in their filenames or in their parent folders.")] = False,
):
    """
    Clean notebooks in an nblite project by removing outputs and metadata.
    
    If `nb_path` is not provided, all notebooks in the project will be cleaned.
    """
    if root_path is None:
        if nb_paths is not None: root_path = Path(nb_paths[0]).parent
        root_path, config = get_project_root_and_config(root_path)
    else:
        root_path = Path(root_path)
        config = read_config(root_path / nblite_config_file_name)
    
    if nb_paths is None:
        nb_paths = []
        for cl in config.code_locations.values():
            if cl.format != 'ipynb': continue
            nb_paths.extend(get_code_location_nbs(root_path, cl, ignore_underscores=ignore_underscores))

    for nb_path in nb_paths:
        clean_ipynb(nb_path, remove_outputs, remove_metadata)


# %% [markdown]
# ## `nbl fill`

# %%
#|export
@app.command(name='fill')
def cli_fill(
    nb_paths: Annotated[Union[List[str], None], Argument(help="Specify the jupyter notebooks to fill. If omitted, all ipynb files in the project's code locations will be filled.")] = None,
    remove_prev_outputs: Annotated[bool, Option("-r", "--remove-prev-outputs", help="Remove the pre-existing outputs from the notebooks.")]=False,
    remove_metadata: Annotated[bool, Option("-m", "--remove-metadata", help="Remove the metadata from the notebooks.")]=True,
    root_path: Annotated[Union[str,None], Option("-r", "--root", help="The root path of the project. If not provided, the project root will be determined by searching for a nblite.toml file.")] = None,
    cell_exec_timeout: Annotated[Union[int,None], Option("-t", "--timeout", help="The timeout for the cell execution.")] = None,
    ignore_underscores: Annotated[bool, Option("-i", "--ignore-underscores", help="Ignore notebooks that begin with an underscore in their filenames or in their parent folders.")] = False,
):
    """
    Clean notebooks in an nblite project by removing outputs and metadata.
    
    If `nb_path` is not provided, all notebooks in the project will be cleaned.
    """
    if root_path is None:
        if nb_paths is not None: root_path = Path(nb_paths[0]).parent
        root_path, config = get_project_root_and_config(root_path)
    else:
        root_path = Path(root_path)
        config = read_config(root_path / nblite_config_file_name)
    
    if nb_paths is None:
        nb_paths = []
        for cl in config.code_locations.values():
            if cl.format != 'ipynb': continue
            nb_paths.extend(get_code_location_nbs(root_path, cl, ignore_underscores=ignore_underscores))
        
    for nb_path in nb_paths:
        fill_ipynb(nb_path, cell_exec_timeout, remove_prev_outputs, remove_metadata)


# %% [markdown]
# ## `nbl validate_staging`

# %%
#|export
@app.command(name='validate_staging')
def cli_validate_staging(
    root_path: Annotated[Union[str,None], Option("-r", "--root", help="The root path of the project. If not provided, the project root will be determined by searching for a nblite.toml file.")] = None
):
    """
    Validate the staging of the project.
    
    The staging is valid if all notebooks are clean and the twins of all notebooks that are staged have no unstaged changes.
    
    The command will exit with code 1 if the staging is invalid.
    """
    
    if root_path is None:
        root_path, config = get_project_root_and_config()
    else:
        root_path = Path(root_path)
        config = read_config(root_path / nblite_config_file_name)
    
    unclean_nbs = []
    for cl in config.code_locations.values():
        if cl.format != 'ipynb': continue
        cl_nbs = get_code_location_nbs(root_path, cl, ignore_underscores=False)
        for nb_path in cl_nbs:
            if not is_file_staged(nb_path): continue
            with tempfile.NamedTemporaryFile(suffix='.ipynb') as tmp_file:
                rel_nb_path = get_relative_path('.', nb_path)
                subprocess.run(['git', 'show', f':{rel_nb_path}'], stdout=tmp_file)
                if is_nb_unclean(tmp_file.name):
                    unclean_nbs.append(nb_path)
            
    if unclean_nbs:
        unclean_nbs_str = "\n".join([f" - {fp}" for fp in unclean_nbs])
        typer.echo(f"Error: The following staged notebooks are not clean:\n{unclean_nbs_str}\n", err=True)
        typer.echo("Please run `nbl clean` and re-stage the notebooks.")
        raise typer.Exit(code=1)
        
    unstaged_nb_twins = get_unstaged_nb_twins()
    if unstaged_nb_twins:
        typer.echo("There are staged notebooks that have unstaged twins.\n", err=True)
        
        for tg in unstaged_nb_twins:
            staged_str = "\n".join([f' - {fp}' for fp in tg['staged']])
            unstaged_str = "\n".join([f' - {fp}' for fp in tg['unstaged']])
            typer.echo(f"The following staged notebooks...\n{staged_str}")
            typer.echo(f"have the corresponding unstaged twins:\n{unstaged_str}")
            typer.echo()
            
        typer.echo("Remember to run `nbl clean` before git adding notebooks.")
            
        raise typer.Exit(code=1)


# %% [markdown]
# ## `nbl install_hooks`

# %%
#|export
@app.command(name='install_hooks')
def cli_install_hooks(
    root_path: Annotated[Union[str,None], Option("-r", "--root", help="The root path of the project. If not provided, the project root will be determined by searching for a nblite.toml file.")] = None
):
    """
    Install the git hooks for the project.
    """
    if root_path is None:
        root_path, _ = get_project_root_and_config()
    root_path = Path(root_path)
    git_root_path = Path(get_git_root())
    
    if root_path.resolve().as_posix() != git_root_path.resolve().as_posix():
        typer.echo("Error: The project root is not the git root.")
        raise typer.Abort()
    
    hooks_path = git_root_path / '.git/hooks'
    pre_commit_hook_path = hooks_path / 'pre-commit'
    
    if pre_commit_hook_path.exists():
        typer.echo(f"Error: A pre-commit hook at {pre_commit_hook_path} already exists.")
        raise typer.Abort()
    
    with open(pre_commit_hook_path, 'w') as f:
        f.write((resources.files("nblite") / "defaults" / "pre-commit.sh").read_text())
