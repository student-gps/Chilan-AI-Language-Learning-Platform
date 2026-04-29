"""Compatibility wrapper for the legacy Integrated Chinese agent path."""

try:
    from content_builder.pipelines.integrated_chinese.agent import (  # noqa: F401
        ContentCreatorAgent,
        _normalize_dialogues,
    )
except ImportError:
    from pipelines.integrated_chinese.agent import (  # noqa: F401
        ContentCreatorAgent,
        _normalize_dialogues,
    )

__all__ = ["ContentCreatorAgent", "_normalize_dialogues"]
