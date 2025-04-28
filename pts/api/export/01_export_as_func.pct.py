# %% [markdown]
# # export.export_as_func

# %%
#|default_exp export.export_as_func

# %%
#|hide
import nblite; from nbdev.showdoc import show_doc; nblite.nbl_export()

# %%
#|export
import re
import tempfile
import nbformat
from pathlib import Path

from nblite.export import convert_nb, get_nb_directives, lookup_directive, export_to_lib, get_nb_module_export_path

# %%
import nblite.export.export_as_func as this_module
from nblite.export.export_as_func import extract_directive_string, get_nb_func_signature, get_nb_as_py_file, get_nb_func_header_content

# %%
#|hide
show_doc(extract_directive_string)


# %%
#|exporti
def extract_directive_string(code_str):
    """
    The pattern looks for a directive `#|set_func_signature` and returns the string that follows it.
    """
    # Pattern explanation:
    # 1. Look for #|set_func_signature
    # 2. Followed by any whitespace and newlines
    # 3. Then match either:
    #    - Triple quotes (""" or ''') with content and closing triple quotes
    #    - Single quotes (' or ") with content and matching closing quote
    pattern = r'#\|set_func_signature\s*\n\s*(?:"""(.*?)"""|\'\'\'(.*?)\'\'\'|"([^"]*?)"|\'([^\']*?)\')'
    
    # re.DOTALL makes . match newlines too
    match = re.search(pattern, code_str, re.DOTALL)
    
    if not match:
        return None
        
    # Return the first non-None group (the one that matched)
    return next((group.strip() for group in match.groups() if group is not None), None)


# %%
# Test cases
test_cases = [
    # Triple double quotes, multiline
    '''
    #|export_as_func true
    #|set_func_signature
    """
    def nb_func():
    """
    ''',
    
    # Triple single quotes, multiline
    """
    #|export_as_func true
    #|set_func_signature
    '''
    def another_func():
    '''
    """,
    
    # Single double quotes, single line
    '''
    #|export_as_func true
    #|set_func_signature
    "def single_line_func()"
    ''',
    
    # Single quotes, single line
    '''
    #|export_as_func true
    #|set_func_signature
    'def another_single_line_func(x, y)'
    '''
]

for i, test in enumerate(test_cases, 1):
    print(f"Test case {i}:")
    print(f"Result: {extract_directive_string(test)}\n")

# %%
#|hide
show_doc(get_nb_func_signature)


# %%
#|exporti
def get_nb_func_signature(nb_path: str):
    """
    Extracts the function signature from a notebook,
    by looking for the directive `#|set_func_signature` in the notebook.
    """
    func_sig = None
    
    with tempfile.NamedTemporaryFile(suffix='.ipynb', delete=True) as tmp_nb:
        convert_nb(nb_path, tmp_nb.name)
        nb_path = tmp_nb.name
    
        with open(nb_path, 'r') as f:
            nb = nbformat.read(f, as_version=4)
        

        for cell in nb['cells']:
            if cell['cell_type'] == 'code':
                code = cell['source']
            else: continue
            
            for code_line in code.split('\n'):
                if not code_line.startswith('#|'): continue
                _directive_str = code_line.split('#|', 1)[1]
                directive = _directive_str.split()[0]
                directive_args = _directive_str[len(directive):].strip()
                if directive == 'set_func_signature':
                    func_sig = extract_directive_string(code)
        
    return func_sig

# %%
root_path = Path('../../../test_proj/')
func_sig = get_nb_func_signature(root_path / 'nbs/func_notebook.ipynb')
print(func_sig)

# %%
show_doc(get_nb_as_py_file)


# %%
#|exporti
def get_nb_as_py_file(nb_path: str, lib_name: str, nb_format=None):
    with tempfile.TemporaryDirectory() as tmp_dir:  # Create a temporary directory instead
        temp_lib_path = Path(tmp_dir) / lib_name
        temp_lib_path.mkdir(parents=True, exist_ok=True)
        export_to_lib(nb_path, temp_lib_path, nb_format)
        py_file_path = get_nb_module_export_path(nb_path, temp_lib_path)
        py_file_content = Path(py_file_path).read_text()
        return py_file_content
    raise Exception('Failed to get the content of the notebook as a python file')


# %%
py_content = get_nb_as_py_file(root_path / 'nbs' / 'func_notebook.ipynb', 'my_module')
print(py_content)

# %%
show_doc(get_nb_func_header_content)


# %%
#|exporti
def get_nb_func_header_content(nb_path: str, nb_format=None):
    """
    Get the content of the notebook as a python file
    """
    directives = get_nb_directives(nb_path, nb_format)
    header_codes = [f"# %%\n{d['cell']['source_without_directives']}" for d in directives if d['directive'] == 'func_header_export']
    return "\n\n".join(header_codes)


# %%
py_header_content = get_nb_func_header_content(root_path / 'nbs' / 'func_notebook.ipynb')
print(py_header_content)

# %%
show_doc(this_module.export_to_lib_as_func)


# %%
#|export
def export_to_lib_as_func(nb_path: str, lib_path: str, nb_format: str = None):
    # Get the function signature from the notebook
    
    directives = get_nb_directives(nb_path, nb_format)
    export_as_func_directive = lookup_directive(directives, 'set_func_signature')
    cell_code = export_as_func_directive['cell']['source'] if export_as_func_directive is not None else ''
    func_sig = extract_directive_string(cell_code)
    func_sig = func_sig if func_sig is not None else 'def main():'
    
    # Get the content of the notebook as a python file
    
    lib_name = Path(lib_path).stem
    py_file_content = get_nb_as_py_file(nb_path, lib_name, nb_format)
    
    # Get the function header content
    header_content = get_nb_func_header_content(nb_path, nb_format)
    
    # Construct the function
    
    first_line = py_file_content.split('\n')[0] # The first line contains the 'AUTOGENERATED!...' comment
    # Get the content after the __all__ line
    py_file_content = py_file_content.split('\n# %% auto 0', 1)[1]
    py_file_content = py_file_content.split('\n', 2)[2].strip()
    
    func_body = "\n".join([f"    {l}" for l in py_file_content.split('\n')])
    
    py_func_file_content = f"""
{first_line}

{header_content}

{func_sig}
{func_body}
    """.strip()

    # Export to the library
    py_file_path = get_nb_module_export_path(nb_path, lib_path)
    Path(py_file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(py_file_path, 'w') as f:
        f.write(py_func_file_content)


# %%
export_to_lib_as_func(root_path / 'nbs' / 'func_notebook.ipynb', root_path / 'my_module');
