"""wickit presets - Pre-configured AI settings.

Purpose: Common AI configuration presets for different use cases.

Usage:
    from wickit import presets, apply_preset

    # Get a preset config
    preset = presets.get_preset("ollama_default")
    config.ai = preset

    # Or apply directly
    apply_preset("jobforge", "claude_sonnet")

Available Presets:
- ollama_default: Balanced Ollama settings
- ollama_coding: Optimized for code generation
- claude_sonnet: Claude 3.5 Sonnet
- claude_opus: Claude 3 Opus for complex tasks
- gpt4_balanced: GPT-4 balanced performance
- gpt4_fast: GPT-4 for quick responses
- openai_default: Standard OpenAI settings
"""

from dataclasses import dataclass
from typing import Optional

from .knobs import AIConfig


@dataclass
class AIPreset:
    """Pre-configured AI settings."""
    name: str
    description: str
    engine: str
    model: str
    timeout: int = 300
    retry_count: int = 3
    retry_delay: int = 5

    def to_ai_config(self) -> AIConfig:
        """Convert to AIConfig."""
        return AIConfig(
            engine=self.engine,
            model=self.model,
            timeout=self.timeout,
            retry_count=self.retry_count,
            retry_delay=self.retry_delay,
        )


# Preset definitions
OLLAMA_DEFAULT = AIPreset(
    name="ollama_default",
    description="Balanced Ollama settings for general use",
    engine="ollama",
    model="llama3.2",
    timeout=300,
    retry_count=3,
    retry_delay=5,
)

OLLAMA_CODING = AIPreset(
    name="ollama_coding",
    description="Optimized for code generation",
    engine="ollama",
    model="codellama",
    timeout=600,
    retry_count=3,
    retry_delay=10,
)

CLAUDE_SONNET = AIPreset(
    name="claude_sonnet",
    description="Claude 3.5 Sonnet - balanced performance",
    engine="claude",
    model="claude-3-5-sonnet-20241022",
    timeout=600,
    retry_count=3,
    retry_delay=5,
)

CLAUDE_OPUS = AIPreset(
    name="claude_opus",
    description="Claude 3 Opus - for complex reasoning",
    engine="claude",
    model="claude-3-opus-20240229",
    timeout=900,
    retry_count=5,
    retry_delay=10,
)

GPT4_BALANCED = AIPreset(
    name="gpt4_balanced",
    description="GPT-4 balanced performance",
    engine="openai",
    model="gpt-4",
    timeout=600,
    retry_count=3,
    retry_delay=5,
)

GPT4_FAST = AIPreset(
    name="gpt4_fast",
    description="GPT-4 for quick responses",
    engine="openai",
    model="gpt-4-turbo",
    timeout=300,
    retry_count=2,
    retry_delay=3,
)

OPENAI_DEFAULT = AIPreset(
    name="openai_default",
    description="Standard OpenAI settings",
    engine="openai",
    model="gpt-4o",
    timeout=600,
    retry_count=3,
    retry_delay=5,
)

# All presets registry
PRESETS = {
    "ollama_default": OLLAMA_DEFAULT,
    "ollama_coding": OLLAMA_CODING,
    "claude_sonnet": CLAUDE_SONNET,
    "claude_opus": CLAUDE_OPUS,
    "gpt4_balanced": GPT4_BALANCED,
    "gpt4_fast": GPT4_FAST,
    "openai_default": OPENAI_DEFAULT,
}


def get_preset(name: str) -> Optional[AIPreset]:
    """Get a preset by name.

    Args:
        name: Preset name (e.g., "ollama_default", "claude_sonnet")

    Returns:
        AIPreset if found, None otherwise
    """
    return PRESETS.get(name)


def apply_preset(product_name: str, preset_name: str) -> bool:
    """Apply a preset to a product's config.

    Args:
        product_name: Product name (e.g., "jobforge", "studya")
        preset_name: Preset name (e.g., "ollama_default")

    Returns:
        True if applied, False if preset not found
    """
    from .knobs import get_config, save_config

    preset = get_preset(preset_name)
    if not preset:
        return False

    config = get_config(product_name)
    config.ai = preset.to_ai_config()
    save_config(product_name, config)
    return True


def list_presets() -> list:
    """List all available presets.

    Returns:
        List of preset info dicts
    """
    return [
        {
            "name": p.name,
            "description": p.description,
            "engine": p.engine,
            "model": p.model,
        }
        for p in PRESETS.values()
    ]


def list_presets_by_engine(engine: str) -> list:
    """List presets for a specific engine.

    Args:
        engine: Engine name (e.g., "ollama", "claude", "openai")

    Returns:
        List of preset info dicts
    """
    return [
        {
            "name": p.name,
            "description": p.description,
            "model": p.model,
        }
        for p in PRESETS.values()
        if p.engine == engine
    ]
