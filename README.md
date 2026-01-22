# omni-kit

Shared utilities for AI products.

## Sub-modules

- `local_stash` - Data directory management
- `config` - Configuration management
- `profiles` - Profile management
- `sync_local` - Local cloud folder detection
- `sync_cloud` - Cloud API sync (Dropbox, Google Drive)
- `sync_auto` - Auto-sync file watcher

## Installation

```bash
pip install omni-kit
```

## Usage

```python
from omni_kit import get_data_dir, Config, list_profiles, detect_cloud_folders

# Get data directory
data_dir = get_data_dir("studya")  # ~/.studya/

# Load config
config = get_config("jobforge")

# List profiles
profiles = list_profiles("jobforge")

# Detect cloud folders
folders = detect_cloud_folders()
```
