"""wickit - Wicked utilities for Python.

A wicked library providing data directory management, configuration,
profile management, cloud sync, and more.

Modules (cool names):
- hideaway: Data directory management
- knobs: Configuration management
- alter-egos: Profile management
- dropzone: Local cloud folder detection
- cloudbridge: Cloud API sync
- autopilot: Auto-sync file watcher
- synapse: Spaced repetition SM-2 algorithm
- pulse: Progress tracking and analytics
- blueprint: JSON schema validation
- humanize: Human-like mistake injection
- landscape: Platform detection and categorization

Usage:
    from wickit import hideaway, knobs, alter-egos
    from wickit import synapse, pulse, blueprint
    from wickit import humanize, landscape
"""

from .hideaway import (
    get_data_dir,
    get_config_path,
    ensure_data_dir,
    get_project_names,
    is_product_installed,
    get_all_product_data_dirs,
    VALID_PRODUCTS,
)

from .knobs import (
    Config,
    AIConfig,
    SyncConfig,
    get_config,
    save_config,
    get_sync_provider,
    set_sync_provider,
    get_ai_config,
    set_ai_config,
)

from .alter_egos import (
    Profile,
    list_profiles,
    get_default_profile,
    create_profile,
    delete_profile,
    copy_profile,
    set_default_profile,
    profile_exists,
)

from .dropzone import (
    CloudProvider,
    SyncFolder,
    SyncStatus,
    detect_cloud_folders,
    get_default_sync_folder,
    create_sync_folder,
    get_dropbox_folder,
    get_google_drive_folder,
    get_onedrive_folder,
    get_icloud_folder,
    LocalFolderSync,
)

from .cloudbridge import (
    SyncResult,
    CloudSync,
    DropboxSync,
    GoogleDriveSync,
    get_cloud_sync_provider,
    sync_to_cloud,
    restore_from_cloud,
)

from .autopilot import (
    AutoSync,
    AutoSyncManager,
    AutoSyncConfig,
)

from .synapse import (
    SM2Card,
    Deck,
    calculate_interval,
    review_card,
    ease_factor_for_quality,
    get_grade_label,
    is_due,
    get_retention_score,
    DEFAULT_EASE_FACTOR,
    MIN_EASE_FACTOR,
    MAX_EASE_FACTOR,
)

from .pulse import (
    StreakData,
    StreakTracker,
    RetentionPoint,
    RetentionAnalyzer,
    ProgressMetrics,
    calculate_progress_metrics,
    get_retention_message,
    get_weak_spots,
    get_recommendations,
    generate_analytics_summary,
)

from .blueprint import (
    Schema,
    FieldSchema,
    SchemaError,
    validate,
    validate_required_fields,
    validate_json_file,
    make_schema,
    safe_validate,
    COMMON_SCHEMAS,
)

from .humanize import (
    Mistaker,
    MistakeConfig,
    should_make_mistake,
    get_mistake_info,
    get_mistake_warning,
    set_mistake_level,
    record_answer,
    calculate_actual_score,
    MISTAKE_LEVELS,
    DEFAULT_MISTAKE_LEVEL,
)

from .landscape import (
    Platform,
    PlatformCategory,
    detect_platform,
    get_platform,
    get_platforms_by_category,
    get_platform_info,
    list_platforms,
    list_platforms_by_category,
    register_platform,
    unregister_platform,
    categorize_url,
    get_all_categories,
    PLATFORMS,
)

__version__ = "0.1.0"

__all__ = [
    # hideaway
    "get_data_dir",
    "get_config_path",
    "ensure_data_dir",
    "get_project_names",
    "is_product_installed",
    "get_all_product_data_dirs",
    "VALID_PRODUCTS",
    # knobs
    "Config",
    "AIConfig",
    "SyncConfig",
    "get_config",
    "save_config",
    "get_sync_provider",
    "set_sync_provider",
    "get_ai_config",
    "set_ai_config",
    # alter_egos
    "Profile",
    "list_profiles",
    "get_default_profile",
    "create_profile",
    "delete_profile",
    "copy_profile",
    "set_default_profile",
    "profile_exists",
    # dropzone
    "CloudProvider",
    "SyncFolder",
    "SyncStatus",
    "detect_cloud_folders",
    "get_default_sync_folder",
    "create_sync_folder",
    "get_dropbox_folder",
    "get_google_drive_folder",
    "get_onedrive_folder",
    "get_icloud_folder",
    "LocalFolderSync",
    # cloudbridge
    "SyncResult",
    "CloudSync",
    "DropboxSync",
    "GoogleDriveSync",
    "get_cloud_sync_provider",
    "sync_to_cloud",
    "restore_from_cloud",
    # autopilot
    "AutoSync",
    "AutoSyncManager",
    "AutoSyncConfig",
    # synapse
    "SM2Card",
    "Deck",
    "calculate_interval",
    "review_card",
    "ease_factor_for_quality",
    "get_grade_label",
    "is_due",
    "get_retention_score",
    "DEFAULT_EASE_FACTOR",
    "MIN_EASE_FACTOR",
    "MAX_EASE_FACTOR",
    # pulse
    "StreakData",
    "StreakTracker",
    "RetentionPoint",
    "RetentionAnalyzer",
    "ProgressMetrics",
    "calculate_progress_metrics",
    "get_retention_message",
    "get_weak_spots",
    "get_recommendations",
    "generate_analytics_summary",
    # blueprint
    "Schema",
    "FieldSchema",
    "SchemaError",
    "validate",
    "validate_required_fields",
    "validate_json_file",
    "make_schema",
    "safe_validate",
    "COMMON_SCHEMAS",
    # humanize
    "Mistaker",
    "MistakeConfig",
    "should_make_mistake",
    "get_mistake_info",
    "get_mistake_warning",
    "set_mistake_level",
    "record_answer",
    "calculate_actual_score",
    "MISTAKE_LEVELS",
    "DEFAULT_MISTAKE_LEVEL",
    # landscape
    "Platform",
    "PlatformCategory",
    "detect_platform",
    "get_platform",
    "get_platforms_by_category",
    "get_platform_info",
    "list_platforms",
    "list_platforms_by_category",
    "register_platform",
    "unregister_platform",
    "categorize_url",
    "get_all_categories",
    "PLATFORMS",
]
