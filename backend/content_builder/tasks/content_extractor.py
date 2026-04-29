try:
    from content_builder.pipelines.integrated_chinese.tasks.content_extractor import *  # noqa: F401,F403
except ImportError:
    from pipelines.integrated_chinese.tasks.content_extractor import *  # noqa: F401,F403

