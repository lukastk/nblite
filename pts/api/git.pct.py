# %% [markdown]
# # git

# %%
#|default_exp git

# %%
#|hide
import nblite; from nblite import show_doc; nblite.nbl_export()

# %%
#|export
import subprocess
from pathlib import Path

from nblite.const import nblite_config_file_name
from nblite.config import get_project_root_and_config, read_config
from nblite.utils import get_code_location_nbs
from nblite.export import get_nb_twin_paths

# %%
import nblite.git as this_module

# %%
#|hide
show_doc(this_module.has_unstaged_changes)


# %%
#|export
def has_unstaged_changes(file_path):
    """Check if the given file has unstaged changes.
    
    Args:
        file_path (str): The path to the file to check.
    
    Returns:
        bool: True if there are unstaged changes, False otherwise.
    """
    result = subprocess.run(['git', 'status', '--porcelain', file_path], capture_output=True, text=True)
    result = [l for l in result.stdout.split('\n') if l.strip()]
    assert len(result) <= 1, "Something went wrong."
    if len(result) == 0: return False
    return result[0][1] != ' '


# %%
fps = [
    '../../test_proj/nbs/notebook1.ipynb',
    '../../test_proj/nbs/notebook2.ipynb',
    '../../test_proj/nbs/submodule/notebook3.ipynb',
]
for fp in fps:
    print(fp, has_unstaged_changes(fp))

# %%
#|hide
show_doc(this_module.get_git_root)


# %%
#|export
def get_git_root():
    """
    Get the root directory of the current git repository.
    
    Returns:
        str: The path to the git root directory.
    """
    result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
    return result.stdout.strip()


# %%
get_git_root()

# %%
#|hide
show_doc(this_module.list_staged_files)


# %%
#|export
def list_staged_files():
    """
    List all currently staged files.
    
    Returns:
        list: A list of staged file paths.
    """
    result = subprocess.run(['git', 'diff', '--name-only', '--cached'], capture_output=True, text=True)
    return result.stdout.strip().split('\n')


# %%
show_doc(this_module.list_unstaged_and_untracked_files)


# %%
#|export
def list_unstaged_and_untracked_files():
    """
    List all currently unstaged and untracked files.

    Returns:
        list: A list of unstaged and untracked file paths.
    """
    result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
    files = []
    for line in result.stdout.strip().split('\n'):
        if line and (line[0] == ' ' or line[0] == '?'):
            files.append(line[3:])
    return files


# %%
list_unstaged_and_untracked_files()

# %%
#|hide
show_doc(this_module.is_file_staged)


# %%
#|export
def is_file_staged(file_path):
    """
    Check if the given file is staged.

    Args:
        file_path (str): The path to the file to check.

    Returns:
        bool: True if the file is staged, False otherwise.
    """
    result = subprocess.run(['git', 'status', '--porcelain', file_path], capture_output=True, text=True)
    result = [l for l in result.stdout.split('\n') if l.strip()]
    assert len(result) <= 1, "Something went wrong."
    if len(result) == 0: return False
    return result[0][0] == 'A' or result[0][0] == 'M'


# %%
fps = [
    '../../test_proj/nbs/notebook1.ipynb',
    '../../test_proj/nbs/notebook2.ipynb',
    '../../test_proj/nbs/submodule/notebook3.ipynb',
]
for fp in fps:
    print(fp, is_file_staged(fp))

# %%
#|hide
show_doc(this_module.get_unstaged_nb_twins)


# %%
#|export
def get_unstaged_nb_twins(root_path: str = None):
    """
    Get all notebook twins for which at least one is unstaged.
    
    Returns:
        list: A list of dictionaries, each containing 'staged' and 'unstaged' lists of twin paths.
    """
    if root_path is None:
        root_path, config = get_project_root_and_config()
    else:
        root_path = Path(root_path)
        config = read_config(root_path / nblite_config_file_name)
    git_root_path = Path(get_git_root())

    # Find all twins for which at least one is staged
    staged_twin_nbs = set()
    for cl in config.code_locations.values():
        cl_nbs = get_code_location_nbs(root_path, cl, ignore_underscores=True)
        for nb_path in cl_nbs:
            if is_file_staged(nb_path):
                staged_twin_nbs.add(get_nb_twin_paths(nb_path, root_path))

    # Check that each notebook in each twin group does not have unstaged changes
    unstaged_twins = []
    for twins in staged_twin_nbs:
        if any(has_unstaged_changes(nb_path) for nb_path in twins):
            unstaged_twins.append({
                'staged': [Path(nb_path).relative_to(git_root_path) for nb_path in twins if is_file_staged(nb_path)],
                'unstaged': [Path(nb_path).relative_to(git_root_path) for nb_path in twins if has_unstaged_changes(nb_path)],
            })
            
    return unstaged_twins


# %%
get_unstaged_nb_twins('../../test_proj')
