"""
Cell documentation extraction and rendering.

This module provides functions for extracting function and class definitions
from Python code using AST, and rendering them as formatted Markdown documentation.
"""

from __future__ import annotations

import ast
import inspect
from typing import Any

try:
    from docstring_parser import parse as parse_docstring
except ImportError:
    parse_docstring = None

__all__ = [
    "extract_top_level_definitions",
    "extract_function_meta",
    "extract_function_meta_from_obj",
    "extract_class_meta",
    "extract_class_meta_from_obj",
    "render_function_doc",
    "render_class_doc",
    "render_cell_doc",
    "show_doc",
]


def extract_top_level_definitions(code_str: str) -> list[dict[str, Any]]:
    """
    Extract top-level function and class definitions from a Python code string.

    Args:
        code_str: Python source code string

    Returns:
        List of dictionaries with 'type' ('function' or 'class') and 'code' keys
    """
    tree = ast.parse(code_str)
    top_level_definitions = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start_line = node.lineno - 1
            end_line = node.end_lineno
            lines = code_str.splitlines()
            definition = "\n".join(lines[start_line:end_line])
            top_level_definitions.append(
                {
                    "type": "function"
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    else "class",
                    "code": definition,
                }
            )

    return top_level_definitions


def extract_function_meta(code_str: str) -> dict[str, Any]:
    """
    Extract metadata from a function definition in Python code.

    Args:
        code_str: Python source code containing a single function definition

    Returns:
        Dictionary with function metadata (name, signature, args, docstring, etc.)

    Raises:
        ValueError: If code doesn't contain exactly one function definition
    """
    tree = ast.parse(code_str)
    function_details = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_name = node.name
            is_async = isinstance(node, ast.AsyncFunctionDef)
            args = {}

            # Regular arguments
            for arg in node.args.args:
                args[arg.arg] = (
                    ast.get_source_segment(code_str, arg.annotation) if arg.annotation else None
                )

            # *args
            if node.args.vararg:
                vararg = node.args.vararg
                args[f"*{vararg.arg}"] = (
                    ast.get_source_segment(code_str, vararg.annotation)
                    if vararg.annotation
                    else None
                )

            # **kwargs
            if node.args.kwarg:
                kwarg = node.args.kwarg
                args[f"**{kwarg.arg}"] = (
                    ast.get_source_segment(code_str, kwarg.annotation) if kwarg.annotation else None
                )

            docstring = ast.get_docstring(node)
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

            function_details.append(
                {
                    "name": func_name,
                    "full_signature": full_signature,
                    "is_async": is_async,
                    "args": args,
                    "docstring": docstring,
                    "return_annotation": return_type,
                }
            )

    if len(function_details) != 1:
        raise ValueError(
            f"Expected exactly one function definition in the code string. Got {len(function_details)}."
        )

    return function_details[0]


def extract_function_meta_from_obj(func: Any) -> dict[str, Any]:
    """
    Extract metadata from a function object.

    Args:
        func: A function or method object

    Returns:
        Dictionary with function metadata

    Raises:
        TypeError: If obj is not a function or method
    """
    if not inspect.isfunction(func) and not inspect.ismethod(func):
        raise TypeError("Expected a function or method object.")

    func_name = func.__name__
    sig = inspect.signature(func)
    args = {}
    sig_parts = []

    for name, param in sig.parameters.items():
        annotation = param.annotation if param.annotation is not inspect.Parameter.empty else None
        annotation_str = (
            annotation.__name__
            if isinstance(annotation, type)
            else str(annotation)
            if annotation is not None
            else None
        )

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

    return_annotation = (
        sig.return_annotation if sig.return_annotation is not inspect.Signature.empty else None
    )
    return_annotation_str = (
        return_annotation.__name__
        if isinstance(return_annotation, type)
        else str(return_annotation)
        if return_annotation is not None
        else None
    )

    full_signature = f"{func_name}({', '.join(sig_parts)})"
    if return_annotation_str is not None:
        full_signature += f" -> {return_annotation_str}"

    return {
        "name": func_name,
        "full_signature": full_signature,
        "is_async": is_async,
        "args": args,
        "docstring": docstring,
        "return_annotation": return_annotation_str,
    }


def extract_class_meta(code_str: str) -> dict[str, Any]:
    """
    Extract metadata from a class definition in Python code.

    Args:
        code_str: Python source code containing a class definition

    Returns:
        Dictionary with class metadata (name, base classes, methods)
    """
    tree = ast.parse(code_str)
    class_details = {}

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            base_classes = [base.id for base in node.bases if isinstance(base, ast.Name)]
            methods = []

            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_code = ast.get_source_segment(code_str, item)
                    if method_code:
                        method_details = extract_function_meta(method_code)
                        methods.append(method_details)

            class_details = {
                "name": class_name,
                "inherits_from": base_classes,
                "methods": methods,
                "docstring": ast.get_docstring(node),
            }

    return class_details


def extract_class_meta_from_obj(cls: type) -> dict[str, Any]:
    """
    Extract metadata from a class object.

    Args:
        cls: A class object

    Returns:
        Dictionary with class metadata
    """
    class_name = cls.__name__
    base_classes = [base.__name__ for base in cls.__bases__ if base is not object]
    methods = []

    for _name, member in inspect.getmembers(cls, predicate=inspect.isfunction):
        if member.__qualname__.startswith(cls.__name__ + "."):
            methods.append(extract_function_meta_from_obj(member))

    return {
        "name": class_name,
        "inherits_from": base_classes,
        "methods": methods,
        "docstring": inspect.getdoc(cls),
    }


def render_function_doc(func: dict[str, Any], title_level: int = 2) -> str:
    """
    Render function metadata as formatted Markdown documentation.

    Args:
        func: Function metadata dictionary
        title_level: Heading level for the function name

    Returns:
        Formatted Markdown string
    """
    md_lines = []

    # Header
    header = f"{'#' * title_level} {func['name']}"
    if func.get("is_async"):
        header += " *(async)*"
    md_lines.append(header)
    md_lines.append("")

    # Signature
    MAX_SIGNATURE_LENGTH = 80
    full_signature = func["full_signature"]

    if len(full_signature) > MAX_SIGNATURE_LENGTH:
        signature_lines = [f"{func['name']}("]
        for arg, arg_type in func["args"].items():
            if arg_type:
                signature_lines.append(f"    {arg}: {arg_type},")
            else:
                signature_lines.append(f"    {arg},")
        if signature_lines[-1].endswith(","):
            signature_lines[-1] = signature_lines[-1].rstrip(",")
        if func.get("return_annotation"):
            signature_lines.append(f") -> {func['return_annotation']}")
        else:
            signature_lines.append(")")
        md_lines.append("```python\n" + "\n".join(signature_lines) + "\n```")
    else:
        md_lines.append(f"```python\n{full_signature}\n```")

    md_lines.append("")

    # Parse docstring if docstring_parser is available
    docstring = func.get("docstring") or ""

    if parse_docstring and docstring:
        parsed_doc = parse_docstring(docstring)

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
    elif docstring:
        # Fallback: just include the raw docstring
        md_lines.append(docstring)
        md_lines.append("")

    md_lines.append("---")
    md_lines.append("")

    return "\n".join(md_lines)


def render_class_doc(cls: dict[str, Any], title_level: int = 2) -> str:
    """
    Render class metadata as formatted Markdown documentation.

    Args:
        cls: Class metadata dictionary
        title_level: Heading level for the class name

    Returns:
        Formatted Markdown string
    """
    md_lines = []

    # Class header
    header = f"{'#' * title_level} {cls['name']}"
    md_lines.append(header)
    md_lines.append("")

    # Inheritance
    if cls.get("inherits_from"):
        bases = ", ".join(cls["inherits_from"])
        md_lines.append(f"*Inherits from*: `{bases}`")
        md_lines.append("")

    # Class docstring
    if cls.get("docstring"):
        md_lines.append(cls["docstring"])
        md_lines.append("")

    md_lines.append("---")
    md_lines.append("")

    # Methods
    if cls.get("methods"):
        md_lines.append(f"{'#' * (title_level + 1)} Methods")
        md_lines.append("")
        for method in cls["methods"]:
            md_lines.append(render_function_doc(method, title_level=title_level + 2))

    return "\n".join(md_lines)


def render_cell_doc(cell_code: str, title_level: int = 2) -> str:
    """
    Render documentation for all top-level definitions in a code cell.

    Args:
        cell_code: Python source code from a notebook cell
        title_level: Heading level for definitions

    Returns:
        Formatted Markdown string with documentation for all definitions
    """
    top_level_defs = extract_top_level_definitions(cell_code)
    docs = []

    for def_info in top_level_defs:
        try:
            if def_info["type"] == "function":
                docs.append(
                    render_function_doc(extract_function_meta(def_info["code"]), title_level)
                )
            else:
                docs.append(render_class_doc(extract_class_meta(def_info["code"]), title_level))
        except Exception:
            # Skip definitions that fail to parse
            pass

    return "\n\n".join(docs)


def show_doc(obj: Any, title_level: int = 2):
    """
    Display formatted documentation for a function or class in IPython/Jupyter.

    This function extracts metadata from the given object and renders it
    as formatted Markdown that displays nicely in Jupyter notebooks.

    Args:
        obj: A function, method, or class object
        title_level: Heading level for the documentation

    Returns:
        IPython Markdown display object

    Raises:
        ValueError: If obj is not a function or class

    Example:
        >>> def my_func(x: int) -> str:
        ...     '''Convert int to string.'''
        ...     return str(x)
        >>> show_doc(my_func)  # Displays formatted documentation
    """
    try:
        from IPython.display import Markdown
    except ImportError:
        raise ImportError(
            "IPython is required for show_doc. Install with: pip install ipython"
        ) from None

    if inspect.isfunction(obj) or inspect.ismethod(obj):
        meta = extract_function_meta_from_obj(obj)
        return Markdown(render_function_doc(meta, title_level))
    elif inspect.isclass(obj):
        meta = extract_class_meta_from_obj(obj)
        return Markdown(render_class_doc(meta, title_level))
    else:
        raise ValueError("Object must be a function, method, or class.")
