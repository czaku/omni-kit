# wickit

**Wicked utilities for Python.** A versatile library providing data directory management, configuration, profile management, cloud sync, spaced repetition learning, analytics, schema validation, and more.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Modules

| Module | Description |
|--------|-------------|
| **hideaway** | Data directory management |
| **knobs** | Configuration management |
| **alter-egos** | Profile management |
| **dropzone** | Local cloud folder detection |
| **cloudbridge** | Cloud API sync (Dropbox, Google Drive) |
| **autopilot** | Auto-sync file watcher |
| **synapse** | Spaced repetition SM-2 algorithm |
| **pulse** | Progress tracking and analytics |
| **blueprint** | JSON schema validation |
| **humanize** | Human-like mistake injection |
| **landscape** | Platform detection and categorization |

## Installation

```bash
pip install wickit
```

Or from source:

```bash
pip install git+https://github.com/czaku/wickit
```

## Quick Start

```python
from wickit import hideaway, knobs, alter_egos

# Get data directory for your application
data_dir = hideaway.get_data_dir("myapp")  # ~/.myapp/

# Load configuration
config = knobs.get_config("myapp")

# Manage profiles
profiles = alter_egos.list_profiles("myapp")
```

## Module Details

### hideaway - Data Directory Management

Manages application data directories across platforms, following XDG Base Directory Specification conventions.

```python
from wickit import hideaway

# Get data directory for your application
data_dir = hideaway.get_data_dir("myapp")  # ~/.myapp/

# Get config file path
config_path = hideaway.get_config_path("myapp", "settings.json")

# Ensure directory exists
hideaway.ensure_data_dir("myapp")

# List known products
products = hideaway.get_project_names()

# Check if a product is installed
is_installed = hideaway.is_product_installed("myapp")
```

**Key Functions:**
- `get_data_dir(product_name)` - Returns Path to data directory
- `get_config_path(product_name, filename)` - Returns Path to config file
- `ensure_data_dir(product_name)` - Creates directory if missing
- `get_project_names()` - Lists all known product directories
- `is_product_installed(product_name)` - Checks if product is installed

---

### knobs - Configuration Management

Unified configuration system with typed settings, validation, and persistence.

```python
from wickit import knobs

# Load configuration
config = knobs.get_config("myapp")

# Create new config
config = knobs.Config(project="myapp")
config.ai.engine = "ollama"
config.ai.model = "llama3.2"
config.sync.provider = "dropbox"

# Save configuration
knobs.save_config(config)

# Get/set sync provider
provider = knobs.get_sync_provider("myapp")
knobs.set_sync_provider("myapp", "dropbox")

# Get/set AI config
ai_config = knobs.get_ai_config("myapp")
ai_config.engine = "claude"
knobs.set_ai_config("myapp", ai_config)
```

**Key Classes:**
- `Config` - Main configuration container
- `AIConfig` - AI-specific settings (engine, model, timeout, retry)
- `SyncConfig` - Sync settings (provider, auto-sync, debounce)

**Key Functions:**
- `get_config(product_name)` - Load config from file
- `save_config(config)` - Save config to file
- `get_ai_config(product_name)` - Get AI configuration
- `set_ai_config(product_name, config)` - Set AI configuration
- `get_sync_provider(product_name)` - Get sync provider
- `set_sync_provider(product_name, provider)` - Set sync provider

---

### alter-egos - Profile Management

Manage multiple named profiles for your application with defaults and metadata.

```python
from wickit import alter_egos

# List all profiles
profiles = alter_egos.list_profiles("myapp")

# Get default profile
default = alter_egos.get_default_profile("myapp")

# Create new profile
profile = alter_egos.create_profile("myapp", "development", {"env": "dev"})

# Set default profile
alter_egos.set_default_profile("myapp", "development")

# Copy profile
copy = alter_egos.copy_profile("myapp", "development", "development-backup")

# Delete profile
alter_egos.delete_profile("myapp", "temp")

# Check if profile exists
exists = alter_egos.profile_exists("myapp", "production")
```

**Key Classes:**
- `Profile` - Profile with id, name, path, is_default, created, modified

**Key Functions:**
- `list_profiles(product_name)` - List all profiles
- `get_default_profile(product_name)` - Get default or first profile
- `create_profile(product_name, name, data)` - Create new profile
- `delete_profile(product_name, name)` - Delete a profile
- `copy_profile(product_name, source, dest)` - Copy a profile
- `set_default_profile(product_name, name)` - Set default profile
- `profile_exists(product_name, name)` - Check if profile exists

---

### dropzone - Cloud Folder Detection

Detect cloud storage folders on the system (Dropbox, Google Drive, OneDrive, iCloud).

```python
from wickit import dropzone

# Detect all cloud folders
folders = dropzone.detect_cloud_folders()

# Get specific cloud folders
dropbox = dropzone.get_dropbox_folder()
gdrive = dropzone.get_google_drive_folder()
onedrive = dropzone.get_onedrive_folder()
icloud = dropzone.get_icloud_folder()

# Get default sync folder
default = dropzone.get_default_sync_folder()

# Create sync folder
sync_folder = dropzone.create_sync_folder(
    local_path="/path/to/sync",
    provider="dropbox",
    remote_path="/remote/path"
)
```

**Key Classes:**
- `CloudProvider` - Enum for cloud providers (DROPBOX, GOOGLE_DRIVE, ONEDRIVE, ICLOUD, LOCAL)
- `SyncFolder` - Sync folder configuration
- `SyncStatus` - Sync status enum (IDLE, SYNCING, ERROR, PENDING)
- `LocalFolderSync` - Local folder sync manager

**Key Functions:**
- `detect_cloud_folders()` - Find all cloud folders on system
- `get_dropbox_folder()` - Get Dropbox folder path
- `get_google_drive_folder()` - Get Google Drive folder path
- `get_onedrive_folder()` - Get OneDrive folder path
- `get_icloud_folder()` - Get iCloud folder path
- `create_sync_folder(**kwargs)` - Create sync folder configuration

---

### cloudbridge - Cloud API Sync

Cloud storage synchronization with Dropbox and Google Drive APIs.

```python
from wickit import cloudbridge

# Create sync provider
dropbox = cloudbridge.DropboxSync(access_token="your-token")
gdrive = cloudbridge.GoogleDriveSync(credentials_path="/path/to/creds")

# Sync to cloud
result = cloudbridge.sync_to_cloud(dropbox, local_file, "/remote/path")

# Restore from cloud
result = cloudbridge.restore_from_cloud(dropbox, "/remote/path", local_file)

# Get sync provider
provider = cloudbridge.get_cloud_sync_provider("dropbox")
```

**Key Classes:**
- `SyncResult` - Result of sync operation (success, path, timestamp, error)
- `CloudSync` - Base cloud sync class
- `DropboxSync` - Dropbox synchronization
- `GoogleDriveSync` - Google Drive synchronization

**Key Functions:**
- `get_cloud_sync_provider(provider_name)` - Get configured sync provider
- `sync_to_cloud(provider, local_path, remote_path)` - Upload to cloud
- `restore_from_cloud(provider, remote_path, local_path)` - Download from cloud

---

### autopilot - Auto-Sync Watcher

Automatic file synchronization with directory watching and change detection.

```python
from wickit import autopilot

# Create auto-sync manager
manager = autopilot.AutoSyncManager()

# Add folder to watch
manager.add_folder(
    local_path="/path/to/watch",
    cloud_provider="dropbox",
    remote_path="/remote/path",
    debounce_seconds=5.0
)

# Start watching
manager.start()

# Stop watching
manager.stop()

# Get sync status
status = manager.get_status()
```

**Key Classes:**
- `AutoSync` - Single folder auto-sync configuration
- `AutoSyncManager` - Manages multiple auto-sync folders
- `AutoSyncConfig` - Auto-sync configuration

**Key Functions:**
- `AutoSyncManager.add_folder()` - Add folder to auto-sync
- `AutoSyncManager.start()` - Start watching
- `AutoSyncManager.stop()` - Stop watching
- `AutoSyncManager.get_status()` - Get sync status

---

### synapse - Spaced Repetition (SM-2)

Implementation of the SM-2 spaced repetition algorithm for learning and memory.

```python
from wickit import synapse

# Create a flashcard
card = synapse.SM2Card(
    front="What is the capital of France?",
    back="Paris",
    deck="geography"
)

# Review card with quality rating (0-5)
# 0-2: fail, 3-5: pass (quality affects interval)
synapse.review_card(card, quality=5)

# Calculate next review interval
interval = synapse.calculate_interval(card)

# Check if card is due
is_due = synapse.is_due(card)

# Get retention score (0-100)
retention = synapse.get_retention_score(card)

# Get grade label
label = synapse.get_grade_label(quality)

# Create a deck of cards
deck = synapse.Deck(name="French Geography", cards=[card1, card2, card3])
```

**Key Classes:**
- `SM2Card` - Flashcard with SM-2 scheduling data
- `Deck` - Collection of cards

**Key Functions:**
- `review_card(card, quality)` - Review a card and update scheduling
- `calculate_interval(card)` - Calculate next review interval
- `is_due(card)` - Check if card needs review
- `get_retention_score(card)` - Get calculated retention percentage
- `ease_factor_for_quality(quality)` - Calculate ease factor
- `get_grade_label(quality)` - Get human-readable grade label

**Constants:**
- `DEFAULT_EASE_FACTOR = 2.5`
- `MIN_EASE_FACTOR = 1.3`
- `MAX_EASE_FACTOR = 2.5`

---

### pulse - Progress Tracking and Analytics

Track streaks, retention, and learning progress with analytics.

```python
from wickit import pulse

# Create streak tracker
tracker = pulse.StreakTracker("myapp")
tracker.record_review(quality=4)
tracker.record_review(quality=5)
tracker.record_review(quality=3)

# Get streak count
streak = tracker.get_streak()  # 3 days

# Calculate progress metrics
metrics = pulse.calculate_progress_metrics(tracker)

# Get retention analysis
retention = pulse.get_retention_message(tracker)

# Find weak spots
weak_spots = pulse.get_weak_spots(tracker)

# Get recommendations
recommendations = pulse.get_recommendations(tracker)

# Generate summary
summary = pulse.generate_analytics_summary(tracker)
```

**Key Classes:**
- `StreakData` - Streak tracking data
- `StreakTracker` - Tracks daily streaks
- `RetentionPoint` - Single retention data point
- `RetentionAnalyzer` - Analyzes retention over time
- `ProgressMetrics` - Aggregated progress metrics

**Key Functions:**
- `StreakTracker.record_review(quality)` - Record a review
- `calculate_progress_metrics(tracker)` - Get progress metrics
- `get_retention_message(tracker)` - Get retention summary
- `get_weak_spots(tracker)` - Identify weak areas
- `get_recommendations(tracker)` - Get study recommendations
- `generate_analytics_summary(tracker)` - Generate full summary

---

### blueprint - JSON Schema Validation

Create and validate JSON schemas with error handling.

```python
from wickit import blueprint

# Create a schema
schema = blueprint.make_schema({
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "age": {"type": "number", "minimum": 0},
        "tags": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["name", "email"]
})

# Validate data
try:
    blueprint.validate(data, schema)
    print("Valid!")
except blueprint.SchemaError as e:
    print(f"Invalid: {e}")

# Validate specific required fields
blueprint.validate_required_fields(data, ["name", "email"])

# Validate a file
result = blueprint.validate_json_file("/path/to/file.json", schema)
if result.valid:
    print("File is valid")
else:
    print(f"Errors: {result.errors}")

# Safe validation (returns result instead of raising)
result = blueprint.safe_validate(data, schema)
if result.valid:
    print("Valid!")
```

**Key Classes:**
- `Schema` - JSON schema wrapper
- `FieldSchema` - Individual field schema
- `SchemaError` - Validation error with details

**Key Functions:**
- `make_schema(schema_dict)` - Create schema from dict
- `validate(data, schema)` - Validate, raise on error
- `validate_required_fields(data, fields required fields
-)` - Check `validate_json_file(path, schema)` - Validate file
- `safe_validate(data, schema)` - Validate, return result

**Pre-built Schemas (COMMON_SCHEMAS):**
- `USER_SCHEMA` - Basic user with name, email
- `SETTINGS_SCHEMA` - Application settings
- `DECK_SCHEMA` - Flashcard deck
- `PROFILE_SCHEMA` - User profile

---

### humanize - Human-Like Mistake Injection

Inject realistic mistakes into text for training data augmentation or testing.

```python
from wickit import humanize

# Create mistaker with level
mistaker = humanize.Mistaker(
    level=humanize.MISTAKE_LEVELS["medium"],
    seed=42
)

# Check if should make mistakes
if humanize.should_make_mistakes():
    # Make mistakes in text
    text = "This is correct text"
    result = mistaker.inject_mistakes(text)

# Configure mistake level
humanize.set_mistake_level(humanize.MISTAKE_LEVELS["low"])

# Record an answer (for learning)
recorded = humanize.record_answer("original", "mistaken", "user_answer")

# Calculate actual score with mistakes
score = humanize.calculate_actual_score(raw_score=90, mistakes=3)

# Get mistake warning
warning = humanize.get_mistake_warning()
```

**Key Classes:**
- `Mistaker` - Mistake injection engine
- `MistakeConfig` - Configuration for mistakes

**Key Functions:**
- `Mistaker.inject_mistakes(text)` - Add mistakes to text
- `should_make_mistakes()` - Check if mistakes enabled
- `set_mistake_level(level)` - Set mistake frequency
- `record_answer(original, mistaken, user_answer)` - Record answer pair
- `calculate_actual_score(raw_score, mistakes)` - Calculate with penalties
- `get_mistake_warning()` - Get warning message

**Mistake Levels:**
- `NONE` - No mistakes
- `LOW` - Few mistakes
- `MEDIUM` - Moderate mistakes
- `HIGH` - Many mistakes
- `EXTREME` - Lots of mistakes

---

### landscape - Platform Detection and Categorization

Detect and categorize platforms/URLs for routing or classification.

```python
from wickit import landscape

# Detect platform from URL
platform = landscape.detect_platform("https://github.com/user/repo")

# Get platform by name
github = landscape.get_platform("github")

# List platforms by category
code_platforms = landscape.list_platforms_by_category(
    landscape.PlatformCategory.CODE
)
social_platforms = landscape.list_platforms_by_category(
    landscape.PlatformCategory.SOCIAL
)

# Categorize a URL
category = landscape.categorize_url("https://youtube.com/watch?v=123")

# Get all categories
categories = landscape.get_all_categories()

# Register custom platform
landscape.register_platform(landscape.Platform(
    name="myapp",
    domains=["myapp.com", "app.myapp.com"],
    category=landscape.PlatformCategory.PRODUCTIVITY
))
```

**Key Classes:**
- `Platform` - Platform definition with name, domains, category
- `PlatformCategory` - Enum (CODE, SOCIAL, PRODUCTIVITY, MEDIA, NEWS, SHOPPING, OTHER)

**Key Functions:**
- `detect_platform(url)` - Detect platform from URL
- `get_platform(name)` - Get platform by name
- `list_platforms()` - List all platforms
- `list_platforms_by_category(category)` - List platforms in category
- `categorize_url(url)` - Get category for URL
- `register_platform(platform)` - Add custom platform
- `unregister_platform(name)` - Remove platform
- `get_all_categories()` - List all categories

**Predefined Platforms:**
- GitHub, GitLab, Bitbucket (CODE)
- Twitter, LinkedIn, Reddit (SOCIAL)
- Notion, Slack, Trello (PRODUCTIVITY)
- YouTube, Spotify (MEDIA)

---

## Changelog

### v0.1.0 (2026-01-22)

Initial release of wickit - wicked utilities for Python.

**Modules:**
- `hideaway` - Data directory management
- `knobs` - Configuration management with AI and sync settings
- `alter-egos` - Profile management with metadata
- `dropzone` - Cloud folder detection (Dropbox, Google Drive, OneDrive, iCloud)
- `cloudbridge` - Cloud API sync (Dropbox, Google Drive)
- `autopilot` - Auto-sync file watcher with change detection
- `synapse` - Spaced repetition SM-2 algorithm for learning
- `pulse` - Progress tracking, streaks, and analytics
- `blueprint` - JSON schema validation with error handling
- `humanize` - Human-like mistake injection for testing/training
- `landscape` - Platform detection and categorization

## License

MIT License - see LICENSE file for details.
| **shuffle** | Dynamic service discovery and connection management |


## shuffle - Dynamic Service Discovery & Connection Management

The `shuffle` module provides dynamic service discovery and connection management for multi-tool architectures. It's specifically designed to solve port conflicts and enable secure communication between services, with special emphasis on Tauri desktop applications.

### Features

- **Dynamic Port Assignment**: Automatically discover available ports to avoid conflicts
- **Service Identity Verification**: Verify services are legitimate before connecting
- **Health Monitoring**: Monitor service health and handle recovery from restarts
- **Tauri Integration**: Seamless integration with Tauri desktop applications
- **mDNS Discovery**: Optional mDNS service registration for local discovery
- **Secure Connections**: Verification tokens to prevent unauthorized connections

### Usage

```python
from wickit.shuffle import ServiceRegistry, ServiceDiscovery

# Register a service with automatic port assignment
registry = ServiceRegistry(
    service_id="my-api",
    port_range=(7770, 7779),
    project_context={"project": "my-app", "version": "1.0.0"}
)

service_info = registry.start()

# Discover services in your application
discovery = ServiceDiscovery(port_range=(7770, 7779))
service_info = discovery.discover_service(
    expected_service_id="my-api",
    project_context={"project": "my-app"}
)

if service_info:
    print(f"Found service on port {service_info.port}")
```

### Documentation

For complete integration guide, see [docs/SERVICE_DISCOVERY_TAURI_INTEGRATION.md](docs/SERVICE_DISCOVERY_TAURI_INTEGRATION.md)


