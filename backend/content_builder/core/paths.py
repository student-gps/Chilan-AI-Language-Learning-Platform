from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ContentBuilderPaths:
    """Canonical filesystem locations used by content-builder commands."""

    content_builder_dir: Path
    backend_dir: Path
    project_root: Path
    artifacts_dir: Path

    @classmethod
    def from_content_builder_dir(cls, content_builder_dir: Path) -> "ContentBuilderPaths":
        content_builder_dir = content_builder_dir.resolve()
        backend_dir = content_builder_dir.parent
        return cls(
            content_builder_dir=content_builder_dir,
            backend_dir=backend_dir,
            project_root=backend_dir.parent,
            artifacts_dir=content_builder_dir / "artifacts",
        )


def default_paths() -> ContentBuilderPaths:
    return ContentBuilderPaths.from_content_builder_dir(Path(__file__).resolve().parents[1])

