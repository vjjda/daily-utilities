# Path: docs/tools/ctree.md

# Tool Guide: ctree

`ctree` is a smart directory tree generator. It provides advanced filtering options via command-line arguments and configuration files, automatically ignoring clutter like `.venv` and `__pycache__`.

## Quick Start

The easiest way to start is by generating a configuration file in your project:

```sh
# Navigate to the directory you want to document
cd /path/to/your/project

# Run the init command
# This creates a .tree.ini file and opens it for you
ctree --init
```

## Usage

```sh
ctree [start_path] [options]
```

* `start_path`: The directory or file to start the tree from. Defaults to the current directory (`.`).

## CLI Options

These options provide one-time overrides for the configuration.

* `--init`: Creates a sample `.tree.ini` file in the current directory and opens it. If one already exists, it will prompt before overwriting.
* `-L, --level <num>`: Limit the display depth of the tree.
* `-I, --ignore <patterns>`: A comma-separated list of patterns (e.g., `*.log,*.tmp`) to completely hide from the output.
* `-P, --prune <patterns>`: A comma-separated list of directory patterns (e.g., `dist,build`). The directory will be shown, but `ctree` will not traverse into it (marked with `[...]`).
* `-d, --dirs-only [patterns]`:
  * If used with no argument (`-d` or `-d _ALL_`), it shows directories only for the entire tree.
  * If used with a comma-separated list (`-d assets,static`), it will only show sub-directories *within* directories that match those patterns (marked with `[dirs only]`).
* `-s, --show-submodules`: By default, `ctree` detects Git submodules (via `.gitmodules`) and hides their contents. Use this flag to show them.

## Configuration Files

For persistent settings, `ctree` automatically loads configurations from `.ini` files in the target directory.

* `.tree.ini`: The primary configuration file for `ctree`.
* `.project.ini`: A fallback project-wide config file. `ctree` will read this if it exists, but any settings in `.tree.ini` will override it.

### Configuration Priority

`ctree` uses a clear priority system to decide which setting to apply:

1. **CLI Arguments** (Highest priority)
      * e.g., `ctree -L 3`
2. **`.tree.ini` file**
      * e.g., `level = 5` inside this file.
3. **`.project.ini` file** (Fallback)
      * Used only if a setting is not in `.tree.ini`.
4. **Script Defaults** (Lowest priority)
      * e.g., `DEFAULT_IGNORE` set to `{.venv, __pycache__, .git, ...}`

**Example:** If your `.tree.ini` says `level = 5`, but you run `ctree -L 3`, the tree will only go to **level 3** because the CLI argument wins. If you run `ctree` with no arguments, it will use **level 5** from the file.

### Filter Patterns (`ignore`, `prune`, `dirs-only`)

All filter patterns in the `.ini` file support:

* **Simple names:** `node_modules`
* **Wildcards:** `*.log`, `temp_?`
* **Relative paths:** `src/generated`, `docs/drafts`

<!-- end list -->