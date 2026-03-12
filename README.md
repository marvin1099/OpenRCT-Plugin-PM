# OpenRCT Plugin Downloader

A simple OpenRCT2 plugin package manager and downloader written in Python.

- **Codeberg**: https://codeberg.org/marvin1099/OpenRCT-Plugin-PM  
- **GitHub**: https://github.com/marvin1099/OpenRCT-Plugin-PM  

## Description

This script lets you search, install,  
and manage OpenRCT2 plugins from the [OpenRCT2 Plugins](https://openrct2plugins.org/) database.  
It uses the plugin API to find plugins and GitHub API to download them.

## Installation

1. Make sure Python is installed
2. Download `orct-pldl.py` from [Codeberg](https://codeberg.org/marvin1099/OpenRCT-Plugin-PM/releases) or [GitHub](https://github.com/marvin1099/OpenRCT-Plugin-PM/releases)
3. Place the script in your OpenRCT2 plugin folder
4. Run the script from within the plugin folder (this ensures config and downloaded files stay in the right place)
5. On Linux, you use `cd "path/to/plugin/folder"` in you terminal to go to the folder 

**Note:** On Windows, use `cd /d "path/to/plugin/folder"` in Command Prompt.

## Usage

```bash
python orct-pldl.py [options]
```

### Search Options
| Flag | Description |
|------|-------------|
| `-q <name>` | Search for plugins by name |
| `-f <fields>` | Search fields: `n`=name, `d`=description, `a`=author, `s`=stars, `t`=tags |
| `-n <num>` | Filter by number (stars, date) - use `g`/`b` in fields for greater/less than |
| `-s <key>` | Sort results by: `n`=name, `s`=stars, `m`=submitted, `l`=last_updated, `r`=reverse |

### Plugin Management
| Flag | Description |
|------|-------------|
| `-i <name>` | Install a plugin (asks which files to download) |
| `-r <name>` | Remove an installed plugin |
| `-u` | Force update all plugins |
| `-l` | List installed plugins |
| `-o` | List all available plugins |

### Other Options
| Flag | Description |
|------|-------------|
| `-x` | Force refresh plugin index |
| `-t` | Instant timeout (skips interactive prompts) |
| `-d` | Ignore the ignore list |
| `-g <url>` | Set custom ignore list URL |
| `-c <file>` | Use custom config file |

### Examples

```bash
# Search for "park" plugins
orct-pldl.py -q park

# Install a plugin
orct-pldl.py -i ParkFenceManager

# Update all plugins
orct-pldl.py -u

# List installed plugins
orct-pldl.py -l
```
