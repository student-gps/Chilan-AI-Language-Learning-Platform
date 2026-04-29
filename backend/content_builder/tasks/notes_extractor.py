try:
    from content_builder.pipelines.integrated_chinese.tasks.notes_extractor import *  # noqa: F401,F403
except ImportError:
    from pipelines.integrated_chinese.tasks.notes_extractor import *  # noqa: F401,F403

