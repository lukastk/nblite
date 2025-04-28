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

# %%
import nblite.export.export_as_func as fns

# %%
show_doc(fns.extract_func_signature)


# %% [markdown]
# Used to extract the function signature declared under the `set_func_signature` directive.

# %%
#|exporti
def extract_func_signature(code_str):
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
#|export
def foo():
    pass

# %%
