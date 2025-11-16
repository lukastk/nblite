## [0.6.10] - 2025-11-16

### 🐛 Bug Fixes

- Removed print statement

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update docs
- Update version in pyproject.toml
## [0.6.9] - 2025-11-16

### 🐛 Bug Fixes

- The relative paths of func notebooks are now correct

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update docs
- Update version in pyproject.toml
## [0.6.8] - 2025-11-13

### 🐛 Bug Fixes

- Fixed bug in expost_as_func that removed #|func_return

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update docs
- Update version in pyproject.toml
## [0.6.7] - 2025-11-13

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Fixed typo
- Update docs
- Update version in pyproject.toml
## [0.6.6] - 2025-11-04

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Modified prepare.sh script to always use latest version of nblite
- Update docs
- Update version in pyproject.toml
## [0.6.5] - 2025-10-04

### 🚀 Features

- 'nbl run' can now be run on any notebook without a nblite.toml file
- 'nbl nb-to-script'

### 🐛 Bug Fixes

- Jupyterlab was a dev dependency rather than a dependency
- Bug in get_nb_path_info

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Changed prepare script
- Update docs
- Update version in pyproject.toml
## [0.6.4] - 2025-08-15

### 🚀 Features

- *(cli)* Nbl run

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update docs
- Update version in pyproject.toml
## [0.6.3] - 2025-08-08

### 🐛 Bug Fixes

- Top-level code locations that did not have a export rule would be deleted in 'nbl clear'

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update docs
- Update version in pyproject.toml
## [0.6.2] - 2025-07-05

### 🐛 Bug Fixes

- *(export.base.clear_code_location)* Was using old def of hidden files
- Added dunders to hidden files
- Wrong hiddden file detection

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update docs
- Update version in pyproject.toml
## [0.6.1] - 2025-06-28

### 🚀 Features

- Can now skip 'set_func_signature' in func notebooks. Defaults to 'main()'.

### 🐛 Bug Fixes

- Added warning when trying to export a notebook func without any export directives.

### 🧪 Testing

- Added test notebook for d5ece3534af8a8ccbcc409b86813e00147737339

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update docs
- Update version in pyproject.toml
## [0.6.0] - 2025-06-28

### 🚀 Features

- *(cli)* Breaking change. Now ignores files and folders beginning with dunders, as opposed to underscores.

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update docs
- Update version in pyproject.toml
## [0.5.23] - 2025-06-25

### 🐛 Bug Fixes

- Nbl clean was set to ignore underscored notebooks

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update docs
- Update version in pyproject.toml
## [0.5.22] - 2025-06-20

### 🐛 Bug Fixes

- Filtering out 'pkg_resources' warning.

### 📚 Documentation

- Updated and cleaned up the documentation for 'nblite.docs'

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Ran nbl prepare on 'test_proj' after having filtered out the pkg_resource warning
- Ran 'nbl prepare' with the 'pkg_resources' warning now removed. Also adjusted some of the non-exported cells so that I won't keep getting unstaged changes.
- Updated uv.lock
- Updated prepare script
- Updated publish_new_version.sh script
- Update docs
- Update version in pyproject.toml
## [0.5.21] - 2025-06-20

### 🚀 Features

- *(nblite.docs)* Removed doc rendering of #|exporti cells

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update docs
- Update version in pyproject.toml
## [0.5.20] - 2025-06-10

### 🐛 Bug Fixes

- *(export.export_as_func.export_to_lib_as_func)* Fixed bug for real

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update version in pyproject.toml
## [0.5.19] - 2025-06-10

### 🐛 Bug Fixes

- *(export.export_as_func.export_to_lib_as_func)* Fixed bug

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update version in pyproject.toml
## [0.5.18] - 2025-06-09

### 🚀 Features

- Options for including underscores and periods

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Modified script
- Update version in pyproject.toml
## [0.5.17] - 2025-05-27

### 🚀 Features

- 'nbl to-md'

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update version in pyproject.toml
## [0.5.16] - 2025-05-25

### 🐛 Bug Fixes

- Issues whenever the parent folders of a repo started with a '_' or '.'

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Updated prepare script to install the test module
- Update version in pyproject.toml
## [0.5.15] - 2025-05-24

### 🚀 Features

- 'nbl git-add' autocomplete

### 🐛 Bug Fixes

- Removed requirement that 'curr_folder' exists in 'get_project_root_and_config'

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update version in pyproject.toml
## [0.5.14] - 2025-05-23

### 🐛 Bug Fixes

- Use slugified module name for lib path in 'nbl init'

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Render docs
- Nbl prepare
- Update version in pyproject.toml
## [0.5.13] - 2025-05-20

### 🚀 Features

- Updated README.md

### 🐛 Bug Fixes

- *(nbl fill)* Bug in 'get_nb_source_and_output_hash'. Only cells with outputs were hashed. Now source-only cells are also hashed.
- Render-docs was not rendering exported async functions

### 🚜 Refactor

- Removed redundant import statement
- Removed junk line

### 📚 Documentation

- Added some stuff
- Updated readme

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Ran 'nbl prepare'
- Update version in pyproject.toml
## [0.5.12] - 2025-05-10

### 🚀 Features

- Simplified template as nblite cells can both import and execute
- 'nbl fill' can now skip notebooks that do not need running. And 'nbl clean' no longe removes top-level metadata.

### 🐛 Bug Fixes

- Changed the behaviour of 'is_nb_unclean' to ignore top-level metadata by default
- 'get_nb_source_and_output_hash' was including output execution_count and metadata in its hash

### 🚜 Refactor

- Typo

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Nbl prepare
- Ran 'nbl prepare' with new clean
- Prepare script
- Nbl prepare
- New prepare script
- Update version in pyproject.toml
## [0.5.11] - 2025-05-09

### 🚀 Features

- Can now disable exporting by setting DISABLE_NBLITE_EXPORT=true. 'nbl fill' disables export by default. Also added cli options to 'nbl prepare'

### 🐛 Bug Fixes

- 'nbl fill' was listing notebooks prefixed with underscores

### 🧪 Testing

- Added tests to see if cells can import and execute code

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Ran nbl prepare. setup pyproject.toml so to as to install the test module properly
- Update version in pyproject.toml
## [0.5.10] - 2025-05-06

### 🚀 Features

- *(nbl fill)* Alphabetical sorting of notebooks in 'nbl fill'
- *(nbl prepare)* 'nbl prepare' now also generates readme

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update version in pyproject.toml
## [0.5.9] - 2025-05-06

### 🚀 Features

- *(nbl fill)* Executes notebooks in parallel by default now in 'nbl fill'

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update version in pyproject.toml
## [0.5.8] - 2025-05-05

### 🚀 Features

- Func signature doc splits over several lines if its too long
- *(docs)* Now also includes the return annotation
- Nbl fill now ignores notebooks that start with or are in folders that start with '.' or '_'

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update version in pyproject.toml
- Update CHANGELOG.md
- Docs re-render
- Update version in pyproject.toml
## [0.5.7] - 2025-05-05

### 🐛 Bug Fixes

- Show_doc now also works for args and kwargs

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update version in pyproject.toml
## [0.5.6] - 2025-05-05

### 🚀 Features

- Function signature now also includes args and kwargs

### 🐛 Bug Fixes

- Bug in template

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update version in pyproject.toml
## [0.5.5] - 2025-05-04

### 🐛 Bug Fixes

- Missed dependency docstring-parser

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update version in pyproject.toml
## [0.5.4] - 2025-05-04

### 🚀 Features

- *(docs)* Functions and classes in exported cells will now have their docs rendered in the cell prior

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update version in pyproject.toml
## [0.5.3] - 2025-05-04

### 🚀 Features

- *(docs)* Hide '#|export' and '#|exporti' as well

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update version in pyproject.toml
## [0.5.2] - 2025-05-04

### 🐛 Bug Fixes

- Typo in docstring
- No longer including any folders that start with '.' in docs rendering

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update version in pyproject.toml
## [0.5.1] - 2025-05-04

### 🐛 Bug Fixes

- 'docs_title' added to nblite.toml template

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update version in pyproject.toml
## [0.5.0] - 2025-05-04

### 🚀 Features

- *(export)* 'nbl readme' now ignores cells with the #|hide directive
- *(docs)* Added rendering and previewing of docs using quarto

### 🐛 Bug Fixes

- *(cli)* Nbl init error. wrong path to the config template
- Updated assets path in const

### 🚜 Refactor

- Moved nblite/defaults to nblite/assets

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update version in pyproject.toml
## [0.4.2] - 2025-05-03

### 🚀 Features

- Nbl --version

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update version in pyproject.toml
## [0.4.1] - 2025-05-03

### 🚀 Features

- Nbl prepare

### 🐛 Bug Fixes

- No longer includes '.ipynb_checkpoints' in 'utils.get_code_location_nbs'

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- Update version in pyproject.toml
## [0.4.0] - 2025-05-03

### 🚀 Features

- Nbl clear
- *(export)* Now exports underscored notebooks to non 'module'-type code locations

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md
- New publish script
- Uv.lock
- Update version in pyproject.toml
## [0.3.4] - 2025-05-01

### 🚀 Features

- *(export.export_as_func)* Added ability to return

### ⚙️ Miscellaneous Tasks

- Update version in pyproject.toml
## [0.3.3] - 2025-04-30

### 🚀 Features

- Modified 'nbl new' template and also now defined them using jinja

### ⚙️ Miscellaneous Tasks

- Updated changelog
- 0.3.3
## [0.3.2] - 2025-04-29

### 🐛 Bug Fixes

- Typo in 'get_top_exports'

### ⚙️ Miscellaneous Tasks

- Updated changelog
- 0.3.2
## [0.3.1] - 2025-04-29

### 🚀 Features

- Changed '#|func_header_export' to '#|top_export'

### ⚙️ Miscellaneous Tasks

- Updated version in pyproject.toml
- Updated CHANGELOG.md
- V0.3.1
## [0.3.0] - 2025-04-28

### 🚀 Features

- *(cli)* 'nbl fill' now has a dry run mode
- *(cli)* Nbl test
- *(export)* Implemented exporting notebooks as functions
- *(export)* Modified how to declare the function signature

### 🚜 Refactor

- *(export)* Modularized 'export'
- Made the show_doc parts of the notebook simpler
- Changed 'this' to 'this_module' as the former already exists

### ⚙️ Miscellaneous Tasks

- Updated changelog
## [0.2.0] - 2025-03-17

### 🚀 Features

- *(cli)* 'nbl git-add'
- *(cli)* Git-add now also exports before adding. Also fixed bug in cleaning

### 🐛 Bug Fixes

- *(cli)* Install-hooks now also makes the pre-commit executable. Otherwise it doesn't work

### 🚜 Refactor

- *(cli)* Changed '_' to '-' in install-hooks and validate-staging

### ⚙️ Miscellaneous Tasks

- Fixed poorly formatted nb
- New version
## [0.1.3] - 2025-03-17

### 🚀 Features

- Added nblite.nbl_export alias
- Changed default notebook template
- 'nbl fill' now has more useful error messages

### 🐛 Bug Fixes

- *(export)* Clean and fill were filling the 'output' field in non-code cells

### 🚜 Refactor

- Removed dud test cell

### ⚙️ Miscellaneous Tasks

- Added rich dependency (for typer)
- Bumped version
## [0.1.2] - 2025-03-16

### 🚀 Features

- Nbl readme

### 🚜 Refactor

- Fixed typos in format_to_jupytertext_formats

### ⚙️ Miscellaneous Tasks

- Generated readme
- New version
## [0.1.1] - 2025-03-16

### ⚙️ Miscellaneous Tasks

- Needed to bump the version since 0.1.0 has already been uploaded to pip
## [0.1.0] - 2025-03-16

### 🚀 Features

- *(utils)* Get_relative_path and is_nb_unclean now also checks top-level metadata

### 🚜 Refactor

- Migrated from nbdev to nblite
- Removed __version__ from __init__.py
- Exported

### ⚙️ Miscellaneous Tasks

- Updated version in pyproject.toml
- Nbdev_clean
- Cleaned test_proj
- Cleaned code with new more agressive cleaning
- Clean notebook1.ipynb
- New version
## [0.0.2] - 2025-03-16

### 🐛 Bug Fixes

- Added nbconvert as dependency
- Nbl clean and nbl fill were trying to clean/fill non-ipynb notebooks
## [0.0.1] - 2025-03-16

### 🚀 Features

- *(export.fill)* Removed execution_count
- *(export.clean_ipynb)* Implement notebook cleaner
- *(config.get_project_root)* Implement
- *(nbl clean)* Implement cli
- *(nbl fill)* Implemented cli
- Get_project_root_and_config
- Added more helper text for nbl init
- Introducing new functions for notebook cleaning, filling and validating staging
- Adjusted validatation error message
- Nbl install_hooks
- Can now export individual notebooks
- Can now disable pre commit hooks by setting environmnent vars
- Nbl convert
- Added extra message in validate_staging

### 🐛 Bug Fixes

- String conversion
- String conversion
- Root_folder argument is now respected
- Pre-commit.sh resource was missing
- Nbl clean/export/fill now ignores underscored notebooks and folders

### 💼 Other

- *(pyproject.toml)* Fixed the build process

### 🚜 Refactor

- *(export)* Added docstrings
- Moved nblite_config_file_name to const

### ⚙️ Miscellaneous Tasks

- Added twine and git-cliff as dev dependencies
