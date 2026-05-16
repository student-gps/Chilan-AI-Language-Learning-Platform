"""Compatibility wrapper for the legacy Integrated Chinese agent path."""

from content_builder_zh.integrated_chinese.agent import (  # noqa: F401
    ContentCreatorAgent,
    _normalize_dialogues,
)

__all__ = ["ContentCreatorAgent", "_normalize_dialogues"]
