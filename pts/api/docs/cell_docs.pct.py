# %% [markdown]
# # docs.cell_docs

# %%
#|default_exp docs.cell_docs

# %%
#|hide
import nblite; from nblite import show_doc; nblite.nbl_export()

# %%
#|export
from IPython.display import Markdown
from pathlib import Path
from docstring_parser import parse as parse_docstring
import inspect
import ast

# %%
#|hide
from nblite.utils import get_project_root_and_config
import nblite.docs.cell_docs as this_module

# %%
#|hide
root_path, config = get_project_root_and_config(Path('../../../test_proj/'))

# %%
#|hide
show_doc(this_module.extract_top_level_definitions)


# %%
#|exporti
def extract_top_level_definitions(code_str: str) -> list:
    """
    Extracts top-level function and class definitions from a given Python code string.
    """
    # Parse the code string into an Abstract Syntax Tree (AST)
    tree = ast.parse(code_str)

    # Initialize a list to store the top-level definitions
    top_level_definitions = []

    # Iterate over the top-level nodes in the AST
    for node in tree.body:
        # Check if the node is a function or class definition
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Get the source code for the node
            start_line = node.lineno - 1
            end_line = node.end_lineno
            lines = code_str.splitlines()
            definition = "\n".join(lines[start_line:end_line])
            top_level_definitions.append({
                'type': 'function' if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class',
                'code': definition,
            })

    return top_level_definitions


# %%
#|hide
code_str = """
def foo(a: int, b: Union[str, None], c, *args, **kwargs) -> str:
    '''
    Processes input.

    Args:
        a (int): The first number.
        b (Union[str, None]): Optional label.
        c: Unannotated parameter.

    Returns:
        bool: True if processed correctly.
    '''
    return "foo"

def bar():
    '''
    A docstring
    '''
    pass

async def baz():
    pass

class MyClass(BaseClass1, BaseClass2):
    def __init__(self, a: int, b: str, c):
        '''
        Constructs a new instance of MyClass.

        Args:
            a (int): The first number.
            b (str): The second number.
            c: Unannotated parameter.
        '''
        pass

    def baz(self, d: float, e: bool):
        pass
        
    async def async_method(self, f: float, g: bool):
        pass
"""

extract_top_level_definitions(code_str)

# %%
#|hide
show_doc(this_module.extract_function_meta)


# %%
#|exporti
def extract_function_meta(code_str):
    """
    Extracts details of functions from a given Python code string.
    """
    import ast
    tree = ast.parse(code_str)
    function_details = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_name = node.name
            is_async = isinstance(node, ast.AsyncFunctionDef)
            args = {}
            # Regular arguments
            for arg in node.args.args:
                args[arg.arg] = ast.get_source_segment(code_str, arg.annotation) if arg.annotation else None
            # *args
            if node.args.vararg:
                vararg = node.args.vararg
                args[f"*{vararg.arg}"] = ast.get_source_segment(code_str, vararg.annotation) if vararg.annotation else None
            # **kwargs
            if node.args.kwarg:
                kwarg = node.args.kwarg
                args[f"**{kwarg.arg}"] = ast.get_source_segment(code_str, kwarg.annotation) if kwarg.annotation else None
            docstring = ast.get_docstring(node)
            # Get return type
            return_type = ast.get_source_segment(code_str, node.returns) if node.returns else None
            # Build signature string
            sig_parts = []
            for k, v in args.items():
                if v is not None:
                    sig_parts.append(f"{k}: {v}")
                else:
                    sig_parts.append(f"{k}")
            full_signature = f"{func_name}({', '.join(sig_parts)})"
            if return_type is not None:
                full_signature += f" -> {return_type}"
            function_details.append({
                'name': func_name,
                'full_signature': full_signature,
                'is_async': is_async,
                'args': args,
                'docstring': docstring,
                'return_annotation': return_type
            })
    if len(function_details) != 1: raise ValueError(f"Expected exactly one function definition in the code string. Got:\n{code_str}")
    return function_details[0]


# %%
#|hide
func_str = extract_top_level_definitions(code_str)[0]['code']
extract_function_meta(func_str)

# %%
#|hide
func_str = extract_top_level_definitions(code_str)[2]['code']
extract_function_meta(func_str)

# %%
#|hide
show_doc(this_module.extract_function_meta_from_obj)


# %%
#|exporti
def extract_function_meta_from_obj(func):
    """
    Extracts details of a function from a given Python function object.
    """
    import inspect

    if not inspect.isfunction(func) and not inspect.ismethod(func):
        raise TypeError("Expected a function or method object.")

    func_name = func.__name__
    sig = inspect.signature(func)
    args = {}
    sig_parts = []
    for name, param in sig.parameters.items():
        annotation = param.annotation if param.annotation is not inspect.Parameter.empty else None
        # Convert annotation to string if present
        annotation_str = (
            annotation.__name__ if isinstance(annotation, type)
            else str(annotation) if annotation is not None
            else None
        )
        # Handle *args and **kwargs
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            display_name = f"*{name}"
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            display_name = f"**{name}"
        else:
            display_name = name
        args[display_name] = annotation_str
        if annotation_str is not None:
            sig_parts.append(f"{display_name}: {annotation_str}")
        else:
            sig_parts.append(f"{display_name}")

    docstring = inspect.getdoc(func)
    is_async = inspect.iscoroutinefunction(func)

    # Get return type
    return_annotation = sig.return_annotation if sig.return_annotation is not inspect.Signature.empty else None
    return_annotation_str = (
        return_annotation.__name__ if isinstance(return_annotation, type)
        else str(return_annotation) if return_annotation is not None
        else None
    )

    full_signature = f"{func_name}({', '.join(sig_parts)})"
    if return_annotation_str is not None:
        full_signature += f" -> {return_annotation_str}"

    return {
        'name': func_name,
        'full_signature': full_signature,
        'is_async': is_async,
        'args': args,
        'docstring': docstring,
        'return_annotation': return_annotation_str
    }


# %%
#|hide
def foo(a, b, c:str, *args, **kwargs) -> str:
    pass

extract_function_meta_from_obj(foo)

# %%
#|hide
show_doc(this_module.extract_class_meta)


# %%
#|exporti
def extract_class_meta(code_str):
    """
    Extracts details of a class from a given Python code string.
    """
    import ast
    tree = ast.parse(code_str)
    class_details = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            base_classes = [base.id for base in node.bases if isinstance(base, ast.Name)]
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_details = extract_function_meta(ast.get_source_segment(code_str, item))
                    methods.append(method_details)
            class_details = {
                'name': class_name,
                'inherits_from': base_classes,
                'methods': methods
            }
    return class_details


# %%
#|hide
class_str = extract_top_level_definitions(code_str)[3]['code']
extract_class_meta(class_str)

# %%
#|hide
show_doc(this_module.extract_class_meta_from_obj)


# %%
#|exporti
def extract_class_meta_from_obj(cls):
    """
    Extracts details of a class from a given Python class object.
    """
    class_name = cls.__name__
    base_classes = [base.__name__ for base in cls.__bases__ if base is not object]
    methods = []
    for name, member in inspect.getmembers(cls, predicate=inspect.isfunction):
        # Only include methods defined in this class, not inherited ones
        if member.__qualname__.startswith(cls.__name__ + "."):
            methods.append(extract_function_meta_from_obj(member))
    class_details = {
        'name': class_name,
        'inherits_from': base_classes,
        'methods': methods
    }
    return class_details


# %%
#|hide
class Foo:
    def __init__(self, a, b, c:str):
        "A docstring"
        pass
    
extract_class_meta_from_obj(Foo)

# %%
#|hide
show_doc(this_module.render_function_doc)


# %%
#|exporti
def render_function_doc(func, title_level=2):
    """
    Takes function metadata and returns formatted Markdown documentation
    using `docstring-parser` to structure the docstring content.
    """
    md_lines = []

    # Header
    header = f"{'#'*title_level} {func['name']}"
    if func['is_async']:
        header += " *(async)*"
    md_lines.append(header)
    md_lines.append("")
    
    # Signature
    MAX_SIGNATURE_LENGTH = 80  # Define a constant for maximum signature length
    full_signature = func['full_signature']
    
    if len(full_signature) > MAX_SIGNATURE_LENGTH:
        # Split the signature into multiple lines
        signature_lines = [f"{func['name']}("]
        for arg, arg_type in func['args'].items():
            if arg_type:
                signature_lines.append(f"   {arg}: {arg_type},")
            else:
                signature_lines.append(f"   {arg},")
        signature_lines[-1] = signature_lines[-1].rstrip(',')  # Remove trailing comma from last argument
        if 'return_annotation' in func and func['return_annotation']:
            signature_lines.append(f") -> {func['return_annotation']}")
        else:
            signature_lines.append(")")
        if 'return_type' in func and func['return_type']:
            signature_lines[-1] += f" -> {func['return_type']}"
        md_lines.append("```python\n" + "\n".join(signature_lines) + "\n```")
    else:
        md_lines.append(f"```python\n{full_signature}\n```")
    
    md_lines.append("")

    # Parse docstring
    parsed_doc = parse_docstring(func['docstring'] or "")

    # Summary
    if parsed_doc.short_description:
        md_lines.append(parsed_doc.short_description)
        md_lines.append("")

    # Long description
    if parsed_doc.long_description:
        md_lines.append(parsed_doc.long_description)
        md_lines.append("")

    # Parameters
    if parsed_doc.params:
        md_lines.append("**Arguments:**")
        for param in parsed_doc.params:
            param_line = f"- `{param.arg_name}`"
            if param.type_name:
                param_line += f" (*{param.type_name}*)"
            if param.description:
                param_line += f": {param.description}"
            md_lines.append(param_line)
        md_lines.append("")

    # Returns
    if parsed_doc.returns:
        ret = parsed_doc.returns
        return_line = "**Returns:**"
        if ret.type_name:
            return_line += f" *{ret.type_name}*"
        if ret.description:
            return_line += f": {ret.description}"
        md_lines.append(return_line)
        md_lines.append("")

    # Final spacing
    md_lines.append("---")
    md_lines.append("")

    return "\n".join(md_lines)


# %%
#|hide
function_str = extract_top_level_definitions(code_str)[0]['code']
Markdown(render_function_doc(extract_function_meta(function_str)))

# %%
#|hide
function_str = """
def foo(argument1: int, argument2: str, argument3, argument4, argument5,*args, **kwargs) -> str:
    pass
"""
Markdown(render_function_doc(extract_function_meta(function_str)))


# %%
#|exporti
def render_class_doc(cls, title_level=2):
    """
    Takes class metadata and returns formatted Markdown documentation
    for the class and its methods.
    """
    md_lines = []

    # Class header
    header = f"{'#'*title_level} {cls['name']}"
    md_lines.append(header)
    md_lines.append("")

    # Inheritance
    if cls.get('inherits_from'):
        bases = ', '.join(cls['inherits_from'])
        md_lines.append(f"*Inherits from*: `{bases}`")
        md_lines.append("")

    # Class divider
    md_lines.append("---")
    md_lines.append("")

    # Methods
    if cls.get('methods'):
        md_lines.append(f"<h{title_level+1}>Methods</h{title_level+1}>")
        md_lines.append("")
        for method in cls['methods']:
            md_lines.append(render_function_doc(method, title_level=title_level+2))

    return "\n".join(md_lines)


# %%
#|hide
class_str = extract_top_level_definitions(code_str)[3]['code']
print(render_class_doc(extract_class_meta(class_str)))

# %%
#|hide
show_doc(this_module.render_cell_doc)


# %%
#|export
def render_cell_doc(cell_code, title_level=2):
    """
    Takes a cell code, extracts all top-level function and class definitions,
    and returns formatted Markdown documentation for each.
    """
    top_level_defs = extract_top_level_definitions(cell_code)
    return "\n\n".join([
        render_function_doc(extract_function_meta(func_str['code'])) if func_str['type'] == 'function' else
        render_class_doc(extract_class_meta(func_str['code']))
        for func_str in top_level_defs
    ])


# %%
print(render_cell_doc(code_str))

# %%
#|hide
show_doc(this_module.show_doc)


# %%
#|export
def show_doc(obj, title_level=2):
    if inspect.isfunction(obj) or inspect.ismethod(obj):
        meta = extract_function_meta_from_obj(obj)
        return Markdown(render_function_doc(meta, title_level))
    elif inspect.isclass(obj):
        meta = extract_class_meta_from_obj(obj)
        return Markdown(render_class_doc(meta, title_level))
    else:
        raise ValueError("Object must be a function or class metadata dictionary.")


# %%
def foo(a, b, c:str, *args, **kwargs):
    "A docstring"
    pass

show_doc(foo).data


# %%
class FooClass:
    def __init__(self, a, b, c:str):
        "A docstring"
        pass

show_doc(FooClass).data
