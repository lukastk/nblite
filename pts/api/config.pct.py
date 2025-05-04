# %% [markdown]
# # config

# %%
#|default_exp config

# %%
#|hide
import nblite; from nbdev.showdoc import show_doc; nblite.nbl_export()

# %%
#|export
import toml
from pydantic import BaseModel, field_validator
from typing import List, Dict, Union, Optional
from pathlib import Path

from nblite.const import code_loc_key_to_default_formats, nb_formats, nblite_config_file_name, format_to_file_exts, format_to_jupytext_format

# %%
import nblite.config as this_module

# %%
show_doc(this_module.NBLiteConfig)


# %%
#|export
class ExportRule(BaseModel):
    from_key: str
    to_key: str

class CodeLocation(BaseModel):
    path: str
    format: str
    
    @property
    def file_ext(self) -> str:
        return format_to_file_exts[self.format]
    
    @property
    def jupytext_format(self) -> str:
        return format_to_jupytext_format[self.format]

class NBLiteConfig(BaseModel):
    """
    Configuration for the NBLite export pipeline.
    """
    export_pipeline: List[ExportRule]
    code_locations: Dict[str, CodeLocation]
    
    docs_cl: Optional[str] = None
    docs_title: Optional[str] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__post_process()
           
    @classmethod     
    def _has_cycle(cls, rules: List[ExportRule]) -> bool:
        # Create a graph from the export rules
        graph = {}
        for rule in rules:
            if rule.from_key not in graph:
                graph[rule.from_key] = []
            graph[rule.from_key].append(rule.to_key)

        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            if node not in visited:
                visited.add(node)
                rec_stack.add(node)

                for neighbor in graph.get(node, []):
                    if neighbor not in visited and dfs(neighbor):
                        return True
                    elif neighbor in rec_stack:
                        return True

                rec_stack.remove(node)
            return False

        for node in graph:
            if dfs(node):
                return True

        return False
    
    @classmethod
    def _order_pipeline(cls, pipeline: List[ExportRule]) -> List[ExportRule]:
        ordered_pipeline = []
        _pipeline = list(pipeline)
        while _pipeline:
            next_found = False
            for rule in _pipeline:
                if all([r.to_key != rule.from_key for r in _pipeline]):
                    ordered_pipeline.append(rule)
                    _pipeline.remove(rule)
                    next_found = True
                    break
            if not next_found:
                raise RuntimeError("Cycle in pipeline")
        return ordered_pipeline
    
    def __post_process(self):
        for rule in self.export_pipeline:
            # Verify that all export rules from_keys and to_keys are in code_locations
            if rule.from_key not in self.code_locations:
                raise ValueError(f'"{rule.from_key}" not found in code_locations')
            if rule.to_key not in self.code_locations:
                raise ValueError(f'"{rule.to_key}" not found in code_locations')
            
            # Verify that no export rule is from a module to a notebook
            if self.code_locations[rule.from_key].format == "module":
                raise ValueError(f'Modules can only be exported to, not from.')
            
        for cl in self.code_locations.values():
            if cl.format not in nb_formats:
                raise ValueError(f'"{cl.format}" is not a valid format')
            
        if self._has_cycle(self.export_pipeline):
            raise ValueError("Export pipeline contains a cycle.")
        
        self.export_pipeline = self._order_pipeline(self.export_pipeline)


# %%
conf = NBLiteConfig(
    docs_cl="nbs",
    export_pipeline=[
        ExportRule(from_key="nbs", to_key="pts"),
        ExportRule(from_key="pts", to_key="lib"),
        ExportRule(from_key="test_nbs", to_key="test_pts"),
        ExportRule(from_key="test_pts", to_key="test_lib"),
    ],
    code_locations={
        "nbs": CodeLocation(path="nbs", format="ipynb"),
        "pts": CodeLocation(path="pts", format="percent"),
        "test_nbs": CodeLocation(path="test_nbs", format="ipynb"),
        "test_pts": CodeLocation(path="test_pts", format="percent"),
        "lib": CodeLocation(path="my_module", format="module"),
        "test_lib": CodeLocation(path="test_module", format="module"),
    }
)

# %%
show_doc(this_module.parse_config_dict)


# %%
#|export
def parse_config_dict(config_dict) -> NBLiteConfig:
    if 'export_pipeline' not in config_dict:
        raise ValueError("'export_pipeline' not found in config")

    # Change key name to match the Pydantic model
    if 'cl' in config_dict:
        config_dict['code_locations'] = config_dict.pop('cl')
    elif 'code_locations' not in config_dict:
        config_dict['code_locations'] = {}
        
    # Process the export pipeline
    if isinstance(config_dict['export_pipeline'], str):
        _export_pipeline = [rule.strip() for rule in config_dict['export_pipeline'].replace('\n', ',').split(',') if rule.strip()]
        config_dict['export_pipeline'] = [
            ExportRule(from_key=rule_str.strip().split('->')[0].strip(), to_key=rule_str.strip().split('->')[1].strip())
            for rule_str in _export_pipeline
            if rule_str.strip() and not rule_str.strip().startswith('#')
        ]
    else:
        config_dict['export_pipeline'] = [ExportRule(**rule) for rule in config_dict['export_pipeline']]
    
    # Add default code locations inferred from the export pipeline if they don't exist
    for rule in config_dict['export_pipeline']:
        if rule.from_key not in config_dict['code_locations'] and rule.from_key in code_loc_key_to_default_formats:
            config_dict['code_locations'][rule.from_key] = {}
        if rule.to_key not in config_dict['code_locations'] and rule.to_key in code_loc_key_to_default_formats:
            config_dict['code_locations'][rule.to_key] = {}

    # Fill in path and format of code locations, if possible to infer
    for code_loc_key, code_loc_config in config_dict['code_locations'].items():
        if 'path' not in code_loc_config:
            code_loc_config['path'] = code_loc_key
        if 'format' not in code_loc_config:
            if code_loc_key in code_loc_key_to_default_formats:
                code_loc_config['format'] = code_loc_key_to_default_formats[code_loc_key]
            else:
                raise ValueError(f"No default format for code location '{code_loc_key}'")
    
    config = NBLiteConfig(**config_dict)
    return config


# %%
toml_string = '''
export_pipeline = """
    #nbs->pts
    pts ->lib
    test_nbs-> test_pts, test_pts->test_lib
"""
docs_cl = "nbs"

[cl.lib]
path = "my_module"
format = "module"

[cl.test_lib]
path = "test"

[cl.nbs]
format = "ipynb"

[cl.pts]
format = "percent"

[cl.test]
format = "module"

[cl.test_nbs]
format = "ipynb"

[cl.test_pts]
'''

parse_config_dict(toml.loads(toml_string)).model_dump()

# %%
toml_string = '''
export_pipeline = """
    pts ->lib
"""
docs_cl = "nbs"
'''

parse_config_dict(toml.loads(toml_string)).model_dump()

# %%
show_doc(this_module._find_config_file)


# %%
#|exporti
def _find_config_file(curr_folder: Path) -> str:
    curr_folder = curr_folder.resolve()
    if (curr_folder / nblite_config_file_name).exists():
        return curr_folder / nblite_config_file_name
    else:
        if curr_folder.parent == curr_folder or curr_folder == Path('~').expanduser():
            return None
        else:
            return _find_config_file(curr_folder.parent)



# %%
_find_config_file(Path('../../test_proj'))

# %%
show_doc(this_module.read_config)


# %%
#|export
def read_config(path) -> NBLiteConfig:
    with open(path, 'r') as f:
        return parse_config_dict(toml.loads(f.read()))


# %%
read_config('../../test_proj/nblite.toml')

# %%
show_doc(this_module.get_project_root_and_config)


# %%
#|export
def get_project_root_and_config(curr_folder:Union[Path, None] = None) -> Path:
    curr_folder = Path(curr_folder) if curr_folder is not None else Path('.')
    config_path = _find_config_file(curr_folder)
    if config_path is None:
        raise ValueError("No nblite.toml found in the current or any parent directory")
    else:
        return config_path.parent, read_config(config_path)


# %%
root_path, config = get_project_root_and_config('../../test_proj')
print(root_path)

# %%
show_doc(this_module.get_top_level_code_locations)


# %%
#|export
def get_top_level_code_locations(config: NBLiteConfig) -> List[str]:
    """
    Returns the top level code locations in the export pipeline.
    """
    all_to_keys = set([rule.to_key for rule in config.export_pipeline])
    return [rule.from_key for rule in config.export_pipeline if rule.from_key not in all_to_keys]


# %%
root_path, config = get_project_root_and_config('../../test_proj')
get_top_level_code_locations(config)

# %%
show_doc(this_module.get_downstream_module)


# %%
#|exporti
def get_downstream_module(config: NBLiteConfig, starting_code_loc_key: str) -> str:
    """
    Finds the first downstream code location in the export pipeline that is of format 'module'.

    Args:
        config (NBLiteConfig): The configuration object containing the export pipeline and code locations.
        starting_code_loc_key (str): The key of the starting code location.

    Returns:
        str: The key of the first downstream code location with format 'module', or None if not found.

    Raises:
        ValueError: If the starting code location key is not found in the configuration.
    """
    def get_next_cl(curr_cl: str) -> ExportRule:
        for rule in config.export_pipeline:
            if rule.from_key == curr_cl:
                return rule.to_key
        return None
    
    if not starting_code_loc_key in config.code_locations:
        raise ValueError(f"Starting code location '{starting_code_loc_key}' not found in config.")
    
    curr_cl = starting_code_loc_key
    while curr_cl is not None:
        if config.code_locations[curr_cl].format == "module":
            return curr_cl
        curr_cl = get_next_cl(curr_cl)
    
    return None



# %%
config = read_config('../../test_proj/nblite.toml')
get_downstream_module(config, 'nbs')
